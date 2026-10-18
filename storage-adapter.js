/* Lossless local storage for Treino36. Existing JSON and exports keep their schema. */
(() => {
  const prefix = 'treino36:lz:1:';
  const originalGet = Storage.prototype.getItem;
  const originalSet = Storage.prototype.setItem;
  const journalKey = 'treino36_assessment_drafts';
  const obsKey='treino36_obs_drafts',photoKey='treino36_obs_photo_drafts';
  const owned = key => /^(treino|avaliacao)/.test(key) && ![journalKey,obsKey,photoKey].includes(key);
  const caches = new WeakMap();
  const cacheFor = storage => {
    if (!caches.has(storage)) caches.set(storage, new Map());
    return caches.get(storage);
  };
  const remember = (cache, key, raw, decoded) => {
    if (cache.size >= 12 && !cache.has(key)) cache.delete(cache.keys().next().value);
    cache.set(key, {raw, decoded});
  };
  const unpack = value => {
    if (value === null || !value.startsWith(prefix)) return value;
    const decoded = LZString.decompressFromUTF16(value.slice(prefix.length));
    if (decoded === null) throw Error('Não foi possível ler os dados guardados. Preserve o backup JSON.');
    return decoded;
  };
  const pack = value => {
    if (value.length < 512) return value;
    const compressed = prefix + LZString.compressToUTF16(value);
    return compressed.length < value.length ? compressed : value;
  };
  Storage.prototype.getItem = function(key) {
    key = String(key);
    const value = originalGet.call(this, key);
    if (!owned(key)) return value;
    const cache = cacheFor(this), entry = cache.get(key);
    const draftRaw = key === 'avaliacao_fisica_alunos' && this === localStorage ? originalGet.call(this, journalKey) : null;
    const obsRaw=key==='treinoAlunos'&&this===localStorage?originalGet.call(this,obsKey):null;
    const photoRaw=key==='treinoAlunos'&&this===localStorage?originalGet.call(this,photoKey):null;
    // Check the base and both journals, including updates from another window.
    if (entry && entry.raw === value && entry.draftRaw === draftRaw&&entry.obsRaw===obsRaw&&entry.photoRaw===photoRaw) return entry.decoded;
    const base = entry && entry.raw === value ? (entry.base ?? entry.decoded) : unpack(value);
    let decoded = draftRaw && draftRaw !== '[]' && globalThis.TreinoAssessmentJournal
      ? JSON.stringify(TreinoAssessmentJournal.merge(JSON.parse(base || '[]'), JSON.parse(unpack(draftRaw)))) : base;
    if((obsRaw&&obsRaw!=='[]'||photoRaw&&photoRaw!=='[]')&&globalThis.TreinoObsJournal)decoded=JSON.stringify(TreinoObsJournal.merge(JSON.parse(base||'[]'),JSON.parse(unpack(obsRaw)||'[]'),JSON.parse(unpack(photoRaw)||'[]')));
    remember(cache, key, value, decoded);
    Object.assign(cache.get(key), {base, draftRaw,obsRaw,photoRaw});
    return decoded;
  };
  Storage.prototype.setItem = function(key, value) {
    key = String(key); value = String(value);
    if (!owned(key)) return originalSet.call(this, key, value);
    const cache = cacheFor(this), entry = cache.get(key);
    if (entry && (entry.base ?? entry.decoded) === value && originalGet.call(this, key) === entry.raw&&!(key==='treinoAlunos'&&this===localStorage&&[obsKey,photoKey].some(k=>{const raw=originalGet.call(this,k);return raw&&raw!=='[]';}))) return;
    const packed = pack(value);
    originalSet.call(this, key, packed);
    remember(cache, key, packed, value);
    if(key==='treinoAlunos'&&this===localStorage){originalSet.call(this,obsKey,'[]');originalSet.call(this,photoKey,'[]');}
  };
  let worker, nextJob = 0;
  const jobs = new Map();
  function runWorker(data) {
    if (!worker) {
      worker = new Worker(new URL('storage-worker.js?v=19', location.href));
      worker.onmessage = ({data}) => {
        const job = jobs.get(data.id); if (!job) return;
        jobs.delete(data.id); clearTimeout(job.timer);
        if (data.error) job.reject(Error(data.error)); else job.resolve(data);
      };
      worker.onerror = () => {
        for (const job of jobs.values()) { clearTimeout(job.timer); job.reject(Error('Não foi possível concluir o salvamento. Os rascunhos foram preservados.')); }
        jobs.clear(); worker.terminate(); worker = null;
      };
    }
    return new Promise((resolve,reject) => {
      const id = ++nextJob;
      const timer = setTimeout(() => { jobs.delete(id); reject(Error('O salvamento está demorando. Os rascunhos foram preservados.')); },30000);
      jobs.set(id,{resolve,reject,timer}); worker.postMessage({...data,id});
    });
  }
  let compacting,compactingObs;
  window.TreinoStorage = {
    stageObs(studentId,patch,photos=false){
      const key=photos?photoKey:obsKey,drafts=JSON.parse(unpack(originalGet.call(localStorage,key))||'[]');
      let draft=drafts.find(d=>String(d.studentId)===String(studentId));if(!draft){draft={studentId};drafts.push(draft);}
      for(const [field,order] of [['obs','obsOrder'],['info','infoOrder']]){
        if(patch[order]){draft[order]=patch[order];draft[field]=(draft[field]||[]).filter(g=>patch[order].some(id=>String(id)===String(g.id)));}
        for(const item of patch[field]||[]){if(!draft[field])draft[field]=[];let guide=draft[field].find(g=>String(g.id)===String(item.id));if(!guide){guide={id:item.id,fields:{}};draft[field].push(guide);}Object.assign(guide.fields,item.fields);}
      }
      if(patch.createStudent)draft.createStudent=patch.createStudent;
      draft.studentFields={...draft.studentFields,...patch.studentFields};
      originalSet.call(localStorage,key,JSON.stringify(drafts));
    },
    pruneObsInfo(studentId,ids){
      const raw=originalGet.call(localStorage,obsKey);if(!raw||raw==='[]')return;
      const drafts=JSON.parse(unpack(raw)),draft=drafts.find(d=>String(d.studentId)===String(studentId));if(!draft)return;
      const before=JSON.stringify(draft),keep=id=>ids.some(value=>String(value)===String(id));
      if(draft.info)draft.info=draft.info.filter(g=>keep(g.id));if(draft.infoOrder)draft.infoOrder=draft.infoOrder.filter(keep);
      if(draft.studentFields?.infoRelevante&&!keep(draft.studentFields.infoRelevante.id))delete draft.studentFields.infoRelevante;
      if(before!==JSON.stringify(draft))originalSet.call(localStorage,obsKey,JSON.stringify(drafts));
    },
    hasObsDrafts(){return [obsKey,photoKey].some(key=>{const raw=originalGet.call(localStorage,key);return raw&&raw!=='[]';});},
    compactObs(){
      if(compactingObs)return compactingObs;
      compactingObs=(async()=>{const key='treinoAlunos',raw=originalGet.call(localStorage,key),journal=originalGet.call(localStorage,obsKey),photos=originalGet.call(localStorage,photoKey);if((!journal||journal==='[]')&&(!photos||photos==='[]'))return null;
        const result=await runWorker({task:'compactObs',raw,journal,photos});
        if(originalGet.call(localStorage,key)!==raw||originalGet.call(localStorage,obsKey)!==journal||originalGet.call(localStorage,photoKey)!==photos)return null;
        originalSet.call(localStorage,key,result.packed);originalSet.call(localStorage,obsKey,'[]');originalSet.call(localStorage,photoKey,'[]');remember(cacheFor(localStorage),key,result.packed,result.decoded);return result.records;
      })().finally(()=>{compactingObs=null;});return compactingObs;
    },
    stageAssessment(recordId,avId,fields,personFields={}) {
      const drafts = JSON.parse(unpack(originalGet.call(localStorage,journalKey)) || '[]');
      let draft = drafts.find(item => String(item.recordId) === String(recordId) && String(item.avId) === String(avId));
      if (!draft) { draft = {recordId,avId,fields:{}}; drafts.push(draft); }
      Object.assign(draft.fields,fields);
      draft.personFields = {...draft.personFields,...personFields};
      // This contains only edited text/numbers, never the whole photo/history collection.
      originalSet.call(localStorage,journalKey,JSON.stringify(drafts));
    },
    assessmentOperation(recordId,avId,operation,fields={},personFields={}) {
      const drafts = JSON.parse(unpack(originalGet.call(localStorage,journalKey)) || '[]');
      const kept = drafts.filter(item => String(item.recordId) !== String(recordId) || String(item.avId) !== String(avId));
      const draft = {recordId,avId,operation,fields,personFields}; kept.push(draft);
      originalSet.call(localStorage,journalKey,JSON.stringify(kept));
      return draft;
    },
    clearAssessmentDrafts() { originalSet.call(localStorage,journalKey,'[]'); },
    async writeJSON(key,value) {
      const before = originalGet.call(localStorage,key);
      const result = await runWorker({task:'serialize',value});
      if (originalGet.call(localStorage,key) !== before) return false;
      originalSet.call(localStorage,key,result.packed);
      remember(cacheFor(localStorage),key,result.packed,result.decoded);
      return true;
    },
    compactAssessments() {
      if (compacting) return compacting;
      compacting = (async () => {
        const key = 'avaliacao_fisica_alunos';
        const raw = originalGet.call(localStorage,key), journal = originalGet.call(localStorage,journalKey);
        if (!journal || journal === '[]') return null;
        const result = await runWorker({task:'compact',raw,journal});
        // Never overwrite edits made while the worker was busy.
        if (originalGet.call(localStorage,key) !== raw || originalGet.call(localStorage,journalKey) !== journal) return null;
        originalSet.call(localStorage,key,result.packed);
        originalSet.call(localStorage,journalKey,'[]');
        remember(cacheFor(localStorage),key,result.packed,result.decoded);
        return result.records;
      })().finally(() => { compacting = null; });
      return compacting;
    }
  };
  // Replace one key at a time. A failed migration always leaves that original key intact.
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!owned(key)) continue;
      const value = originalGet.call(localStorage, key);
      if (value && !value.startsWith(prefix)) {
        const compressed = pack(value);
        if (compressed.length < value.length) originalSet.call(localStorage, key, compressed);
      }
    }
  } catch (error) { console.warn('Os dados existentes foram preservados:', error.name); }
})();
