/* Shared catalog and private videos saved on this device. */
window.WorkoutCatalog = (() => {
  let pending, base = [], custom = [], urls = [], folderURL='';
  const key = name => String(name).replace(/\.mp4$/i, '').replace(/\s*\(\d+\)$/, '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
  function database() { return new Promise((resolve, reject) => {
    const request = indexedDB.open('treino36-private-videos', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('videos', {keyPath:'id'});
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(Error('Não foi possível abrir os vídeos deste aparelho.'));
  }); }
  async function records(action, value) {
    const db = await database();
    try { return await new Promise((resolve, reject) => {
      const tx = db.transaction('videos', action === 'getAll' ? 'readonly' : 'readwrite');
      const request = tx.objectStore('videos')[action](...(value === undefined ? [] : [value]));
      tx.oncomplete = () => resolve(request.result);
      tx.onerror = tx.onabort = () => {const error=Error('Não foi possível salvar. Verifique o espaço disponível no aparelho.');error.cause=tx.error||request.error;reject(error);};
    }); } finally { db.close(); }
  }
  async function refresh() {
    const saved = await records('getAll');
    urls.forEach(URL.revokeObjectURL); urls = [];
    custom = saved.map(({blob,bytes,mimeType, ...asset}) => { const media = URL.createObjectURL(blob||new Blob([bytes],{type:mimeType||'video/mp4'})); urls.push(media); return {...asset, media}; });
    return custom;
  }
  function current() {
    const seen = new Map(),assets=[...base,...custom],visible=window.WorkoutVideoLibrary?new Set(WorkoutVideoLibrary.apply(assets,true).map(video=>video.id)):null;
    return assets.filter(asset => {
      if(visible&&!visible.has(asset.id))return false;
      const identity = asset.exerciseKey || key(asset.name);
      if (seen.has(identity)) {
        const kept=seen.get(identity);kept.sourceIds=[...new Set([...(kept.sourceIds||[]),asset.id,...(asset.sourceIds||[])])];return false;
      }
      seen.set(identity,asset); return true;
    });
  }
  async function load() {
    if (!pending) pending = Promise.all(['cmfit-catalog.json?v=1','gymfaster-catalog.json?v=unified-1'].map(async url => {
      const response = await fetch(url); if (!response.ok) throw Error('Catálogo indisponível.'); return response.json();
    })).then(async ([cm, gym]) => {
      folderURL=gym.folderUrl||'';
      base = [...gym.videos.map(v => ({...v, collection:'gymfaster'})), ...cm.videos.map(v => ({...v, collection:'cm'}))];
      try { await refresh(); } catch (error) { /* The published catalog also works without private storage. */ }
      return current();
    }).catch(error => { pending = null; throw error; });
    await pending; return current();
  }
  async function add(file, name, group) {
    await load(); name = String(name).replace(/\s+/g,' ').trim(); group = String(group).trim();
    if (!name || name.length > 160 || !group) throw Error('Informe o nome (até 160 caracteres) e a categoria.');
    if (!file || !/^(video\/)/.test(file.type) || !/\.(mp4|m4v|mov|webm)$/i.test(file.name) || !file.size || file.size > 100*1048576) throw Error('Escolha um vídeo MP4, MOV ou WebM de até 100 MB.');
    const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', await file.arrayBuffer())), b => b.toString(16).padStart(2,'0')).join('');
    const identity = key(name);
    const existing = WorkoutVideoLibrary.apply([...base,...custom],true).find(v => v.sha256 === hash || v.id === 'user-'+hash || key(v.name) === identity || (v.exerciseKey || key(v.originalName)) === identity || (v.aliases||[]).some(alias => key(alias) === identity));
    if (existing) throw Error('Este exercício ou arquivo já está na biblioteca: '+existing.name+'. Use a versão existente; para uma variação diferente, informe o aparelho ou a variação no nome.');
    const media = URL.createObjectURL(file), probe = document.createElement('video');
    try { await new Promise((resolve,reject) => { const timer=setTimeout(()=>reject(Error('Não foi possível ler este vídeo.')),15000); probe.onloadedmetadata=()=>{clearTimeout(timer); probe.videoWidth && probe.duration > 0 ? resolve() : reject(Error('Vídeo inválido.'));}; probe.onerror=()=>{clearTimeout(timer);reject(Error('Formato de vídeo não suportado neste navegador.'));};probe.preload='metadata';probe.src=media; }); }
    finally { probe.removeAttribute('src'); probe.load(); URL.revokeObjectURL(media); }
    const id = 'user-'+hash;
    const record={id,name,group,gender:'Pessoal',collection:'gymfaster',source:'Meu vídeo',url:'local-video:'+id,sha256:hash,exerciseKey:identity,aliases:[]};
    try{await records('put',{...record,blob:file});}
    catch(error){
      // Some WebKit stores reject Blob/File serialization; bytes remain durable.
      if(error.cause?.name!=='UnknownError')throw error;
      await records('put',{...record,bytes:await file.arrayBuffer(),mimeType:file.type});
    }
    // Do not revoke existing URLs: an open preview or GIF can still be using them.
    const asset={id,name,group,gender:'Pessoal',collection:'gymfaster',source:'Meu vídeo',url:'local-video:'+id,sha256:hash,exerciseKey:identity,media:URL.createObjectURL(file),aliases:[]};
    urls.push(asset.media);custom.push(asset);
    window.WorkoutVideoLibrary?.registerUpload(id);
    window.dispatchEvent(new CustomEvent('workout-video-library-change',{detail:{action:'add',id}}));
    return asset;
  }
  async function deleteLocal(id) {
    await load();const asset=custom.find(video=>video.id===id);if(!asset)return false;
    await records('delete',id);custom=custom.filter(video=>video.id!==id);
    URL.revokeObjectURL(asset.media);urls=urls.filter(url=>url!==asset.media);return true;
  }
  function openAdd(onAdded,defaults={}) {
    const dialog=document.createElement('dialog');dialog.className='gif-video-add';dialog.setAttribute('aria-label','Adicionar vídeo à biblioteca');
    const make=(tag,text)=>{const e=document.createElement(tag);if(text)e.textContent=text;return e;};
    const title=make('h3','Adicionar vídeo'),hint=make('p','O vídeo fica salvo somente neste navegador e aparelho. Ele não será enviado ao Drive nem ficará disponível para outras pessoas pelo PDF. Você pode usá-lo nas prévias e nos GIFs. Guarde também o arquivo original.'),form=make('form'),name=make('input'),category=make('select'),file=make('input'),status=make('p'),save=make('button','Salvar vídeo'),close=make('button','Cancelar');
    name.value=String(defaults.name||'').slice(0,160);name.required=true;name.maxLength=160;name.placeholder='Ex.: Afundo com Halteres';name.setAttribute('aria-label','Nome do exercício');category.required=true;category.setAttribute('aria-label','Categoria do vídeo');
    const placeholder=make('option','Escolha a categoria');placeholder.value='';category.append(placeholder);
    [...new Set(current().map(v=>v.group))].sort((a,b)=>a.localeCompare(b,'pt-BR')).forEach(g=>{const option=make('option',g);option.value=g;category.append(option);});
    if(defaults.group)category.value=defaults.group;
    file.type='file';file.accept='video/mp4,video/webm,video/quicktime,.mp4,.m4v,.mov,.webm';file.required=true;file.setAttribute('aria-label','Arquivo de vídeo');save.type='submit';close.type='button';status.setAttribute('role','status');close.onclick=()=>dialog.close();
    form.append(name,category,file,save,close,status);dialog.append(title,hint,form);document.body.append(dialog);dialog.onclose=()=>dialog.remove();
    form.onsubmit=async event=>{event.preventDefault();save.disabled=true;close.disabled=true;status.textContent='Verificando vídeo e repetições…';try{const asset=await add(file.files[0],name.value,category.value);onAdded?.(asset);dialog.close();}catch(error){status.textContent=error.message;}finally{save.disabled=false;close.disabled=false;}};
    dialog.showModal();name.focus();return dialog;
  }
  return {load,current,add,openAdd,deleteLocal,key,get folderURL(){return folderURL;}};
})();
