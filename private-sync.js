/* Two-way sync is available only through the private Raspberry origin. */
window.PrivateSync=(()=>{
  const active=location.origin==='https://caio.tail953b6e.ts.net:8443'&&!new URLSearchParams(location.search).has('embed');
  if(!active)return {bootstrap:async()=>{},mount(){}};
  const C=TreinoSyncMerge.canonical;
  const keys={alunos:'treinoAlunos',avaliacoes:'avaliacao_fisica_alunos',mobilidades:'treinoMobilidades',treinos_favoritos:'treinoSectionFavoritesV1'};
  const prefs={notificacoes_avaliacao:'avaliacao_notificacoes_ativas',favoritos_treinos_fixados:'treinoSectionFavoritesPinnedV1',favoritos_treinos_visiveis:'treinoSectionFavoritesVisibleV1'};
  let client=localStorage.getItem('treino36BackupClient');
  if(!client){client=crypto.randomUUID();localStorage.setItem('treino36BackupClient',client);}
  let db,checkpoint,busy=false,status,controls,warning='',conflicts=null,lastInput=0,ready=false;
  const request=(method,key,value)=>new Promise((resolve,reject)=>{
    const tx=db.transaction('state',method==='get'?'readonly':'readwrite'),store=tx.objectStore('state'),req=method==='get'?store.get(key):store.put(value,key);
    tx.oncomplete=()=>resolve(req.result);tx.onerror=tx.onabort=()=>reject(tx.error||Error('Não foi possível preservar os dados locais.'));
  });
  async function openDB(){db=await new Promise((resolve,reject)=>{const req=indexedDB.open('treino36_sync',1);req.onupgradeneeded=()=>req.result.createObjectStore('state');req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);});}
  function capture(){
    const data={schema_version:'3.0',tipo:'treino36-completo'};
    for(const[field,key]of Object.entries(keys))data[field]=JSON.parse(localStorage.getItem(key)||'[]');
    data.preferencias={};for(const[field,key]of Object.entries(prefs))data.preferencias[field]=localStorage.getItem(key)==='1';
    data.padrao_caio=checkpoint?.data?.padrao_caio||JSON.parse(document.getElementById('padraoCaioData')?.textContent||'null');
    return data;
  }
  function normalize(data){
    const copy=structuredClone(data);for(const field of Object.keys(keys))if(!copy[field])copy[field]=[];
    copy.preferencias=copy.preferencias||{};for(const field of Object.keys(prefs))copy.preferencias[field]=!!copy.preferencias[field];copy.padrao_caio=copy.padrao_caio||null;return copy;
  }
  async function remote(){
    const response=await fetch('/api/sync',{cache:'no-store',signal:AbortSignal.timeout(15000)});
    if(!response.ok)throw Error('Raspberry indisponível. Os dados continuam neste navegador.');
    const result=await response.json();if(result.data)result.data=normalize(result.data);return result;
  }
  async function remember(data,revision){if(checkpoint?.revision===revision&&C(checkpoint.data)===C(data))return;checkpoint={data:structuredClone(data),revision};await request('put','checkpoint',checkpoint);}
  async function preserve(data){await request('put','recovery',{data:structuredClone(data),date:Date.now()});}
  async function install(data,expected){
    if(!data||!Array.isArray(data.alunos)||!Array.isArray(data.avaliacoes))throw Error('Dados recebidos inválidos.');
    await PhotoVault.prepare(data);
    if(expected!==undefined&&C(capture())!==expected)throw Error('Você alterou os dados durante a sincronização. Tentarei novamente.');
    const allKeys=[...Object.values(keys),...Object.values(prefs),'treino36_assessment_drafts','treino36_obs_drafts','treino36_obs_photo_drafts'];
    const before=allKeys.map(key=>localStorage.getItem(key));
    try{
      for(const[field,key]of Object.entries(keys))localStorage.setItem(key,JSON.stringify(data[field]||[]));
      for(const[field,key]of Object.entries(prefs))localStorage.setItem(key,data.preferencias?.[field]?'1':'0');
      for(const key of allKeys.slice(-3))localStorage.setItem(key,'[]');
    }catch(error){allKeys.forEach((key,i)=>{if(before[i]===null)localStorage.removeItem(key);else localStorage.setItem(key,before[i]);});throw error;}
  }
  function editing(){const el=document.activeElement;return Date.now()-lastInput<2000||el?.matches('input,textarea,[contenteditable="true"]')||!!document.querySelector('dialog[open],#sectionZoom[style*="visible"],#pasteModal[style*="visible"]');}
  async function send(data,revision){
    const response=await fetch('/api/sync',{method:'POST',headers:{'Content-Type':'application/json','X-Treino36-Client':client,'X-Treino36-Revision':revision},body:JSON.stringify(data),signal:AbortSignal.timeout(15000)});
    const result=await response.json();if(!response.ok)throw Error(response.status===409?'Outro navegador acabou de salvar. Vou tentar sincronizar novamente.':result.error);return result;
  }
  async function bootstrap(){
    await TreinoStorage.ready;await openDB();checkpoint=await request('get','checkpoint');
    try{
      const cloud=await remote(),local=capture();
      if(!checkpoint){
        if(cloud.data){
          if(local.alunos.length)await preserve(local);
          if(cloud.client===client&&local.alunos.length)await remember(cloud.data,cloud.revision);
          else{await install(cloud.data);await remember(cloud.data,cloud.revision);}
        }else{
          await remember(local,cloud.revision);
          if(local.alunos.length){const sent=await send(local,cloud.revision);await remember(local,sent.revision);}
        }
      }else if(cloud.data&&cloud.revision!==checkpoint.revision){
        const merged=TreinoSyncMerge.merge(checkpoint.data,local,cloud.data);
        if(merged.conflicts.length){conflicts=merged.conflicts;warning='Há edições simultâneas. Abra Sincronização para escolher a versão.';}
        else{await preserve(local);await install(merged.data);await remember(cloud.data,cloud.revision);}
      }
    }catch(error){warning=error.message;}
    ready=true;
  }
  async function flush(){
    if(window.TreinoBackup?.snapshot)await window.TreinoBackup.snapshot();
    else if(window.TreinoSyncFlush)window.TreinoSyncFlush();
    await PhotoVault.refresh();
  }
  function message(text){if(status)status.textContent=text;}
  function showConflict(paths){conflicts=paths;message('Edições simultâneas no mesmo dado. Nada foi sobrescrito. Escolha a versão abaixo.');if(controls)controls.hidden=false;}
  async function cycle(force=false){
    if(!ready||busy||(!force&&document.hidden)||conflicts)return;busy=true;
    try{
      await flush();const local=capture();if(!checkpoint)throw Error('Conecte ao Tailscale e recarregue para iniciar a sincronização.');
      const statusResponse=await fetch('/api/backup/status',{cache:'no-store',signal:AbortSignal.timeout(15000)});
      if(!statusResponse.ok)throw Error('Não foi possível consultar o Raspberry.');
      const state=await statusResponse.json();
      const cloud=state.sha256===checkpoint.revision?{data:checkpoint.data,revision:checkpoint.revision}:await remote();let next=local;
      if(cloud.data&&cloud.revision!==checkpoint.revision){
        const merged=TreinoSyncMerge.merge(checkpoint.data,local,cloud.data);
        if(merged.conflicts.length){showConflict(merged.conflicts);return;}next=merged.data;
      }
      if(C(capture())!==C(local))return;
      const changedScreen=C(next)!==C(local);
      if(changedScreen&&editing()){message('Há novidades de outro navegador. Elas aparecerão quando você terminar de editar.');return;}
      if(!cloud.data||C(next)!==C(cloud.data)){
        const sent=await send(next,cloud.revision);
        if(C(capture())!==C(local)){await remember(next,sent.revision);return;}
        if(changedScreen){await preserve(local);await install(next,C(local));}
        await remember(next,sent.revision);
      }else{
        if(changedScreen){await preserve(local);await install(next,C(local));}
        await remember(next,cloud.revision);
      }
      if(changedScreen){location.reload();return;}
      message('Sincronizado entre navegadores. Drive: '+(state.uploaded_at?new Date(state.uploaded_at*1000).toLocaleString('pt-BR'):'aguardando')+'. Backup a cada 15 dias.'+(state.error?' '+state.error:''));
    }catch(error){message('Sincronização pendente: '+error.message);}finally{busy=false;}
  }
  function download(data){const url=URL.createObjectURL(new Blob([JSON.stringify(data)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='treino36-copia-local-'+Date.now()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  async function resolve(useLocal){
    if(busy)return;busy=true;
    try{
      await flush();const local=capture(),cloud=await remote();await preserve(local);
      if(useLocal){await request('put','recovery-remote',{data:cloud.data,date:Date.now()});const sent=await send(local,cloud.revision);await remember(local,sent.revision);}
      else{await install(cloud.data,C(local));await remember(cloud.data,cloud.revision);}
      conflicts=null;location.reload();
    }catch(error){message(error.message);}finally{busy=false;}
  }
  function mount(){
    const panel=document.createElement('details');panel.id='privateSyncPanel';panel.style.cssText='padding:8px;background:#edf2f5;border-radius:8px;font:12px/1.4 Arial';
    const title=document.createElement('summary');title.textContent='☁️ Sincronização e backup';status=document.createElement('p');status.setAttribute('role','status');controls=document.createElement('div');controls.hidden=!conflicts;
    function button(label,handler,parent=panel){const b=document.createElement('button');b.type='button';b.textContent=label;b.onclick=handler;parent.append(b);}
    panel.append(title,status,controls);button('Sincronizar agora',()=>cycle(true));
    button('Usar versão deste navegador',()=>resolve(true),controls);button('Usar versão do Raspberry',()=>resolve(false),controls);
    button('Baixar cópia local preservada',async()=>{const saved=await request('get','recovery');if(saved)download(saved.data);else message('Nenhuma cópia anterior disponível.');});
    button('Baixar versão remota preservada',async()=>{const saved=await request('get','recovery-remote');if(saved)download(saved.data);else message('Nenhuma versão remota preservada.');});
    (document.querySelector('#moreOptions .more-options-menu')||document.body).append(panel);
    message(warning||'Preparando sincronização…');if(conflicts)showConflict(conflicts);
    document.addEventListener('input',()=>{lastInput=Date.now();},true);document.addEventListener('change',()=>{lastInput=Date.now();},true);
    setTimeout(()=>cycle(),1200);setInterval(()=>cycle(),5000);
    window.addEventListener('online',()=>cycle());document.addEventListener('visibilitychange',()=>{if(!document.hidden)cycle();});
  }
  return {bootstrap,mount,capture,cycle};
})();
