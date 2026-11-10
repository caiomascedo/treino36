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
  function allAssets() {
    const replacements=new Map(custom.map(asset=>[asset.id,asset]));
    return [...base.map(asset=>replacements.has(asset.id)?{...asset,...replacements.get(asset.id)}:asset),...custom.filter(asset=>!base.some(original=>original.id===asset.id))];
  }
  function matchingName(name) {
    const identity=key(name);if(!identity)return [];
    const assets=WorkoutVideoLibrary.apply(allAssets(),true);
    return assets.filter(asset=>[asset.name,asset.originalName,...(asset.aliases||[])].some(value=>value&&key(value)===identity));
  }
  function current() {
    const seen = new Map(),assets=allAssets(),visible=window.WorkoutVideoLibrary?new Set(WorkoutVideoLibrary.apply(assets,true).map(video=>video.id)):null;
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
  async function add(file, name, group, options={}) {
    await load(); if(file&&(!file.type||file.type==='application/octet-stream')&&/\.(mp4|m4v|mov|webm)$/i.test(file.name))file=new File([file],file.name,{type:/\.webm$/i.test(file.name)?'video/webm':/\.mov$/i.test(file.name)?'video/quicktime':'video/mp4'}); name = String(name).replace(/\s+/g,' ').trim(); group = String(group).trim();
    if (!name || name.length > 160 || !group) throw Error('Informe o nome (até 160 caracteres) e a categoria.');
    if (!file || !( /^(video\/)/.test(file.type)||!file.type||file.type==='application/octet-stream') || !/\.(mp4|m4v|mov|webm)$/i.test(file.name) || !file.size || file.size > 100*1048576) throw Error('Escolha um vídeo MP4, MOV ou WebM de até 100 MB.');
    const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', await file.arrayBuffer())), b => b.toString(16).padStart(2,'0')).join('');
    const identity = key(name);
    const target=options.replaceId?lookup(options.replaceId):null;
    if(options.replaceId&&!target)throw Error('O vídeo a substituir não está mais disponível. Reabra o formulário.');
    const duplicate=WorkoutVideoLibrary.apply(allAssets(),true).find(v=>v.id!==target?.id&&(v.sha256===hash||!v.sha256&&v.id==='user-'+hash||!target&&[v.name,v.originalName,...(v.aliases||[])].some(value=>value&&key(value)===identity)));
    if(duplicate&&!target)throw Error('Este exercício ou arquivo já está na biblioteca: '+duplicate.name+'. Escolha o vídeo correspondente para substituir ou informe uma variação diferente.');
    if(target?.sha256===hash)return WorkoutVideoLibrary.decorate(target);
    const media = URL.createObjectURL(file), probe = document.createElement('video');
    try { await new Promise((resolve,reject) => { const timer=setTimeout(()=>reject(Error('Não foi possível ler este vídeo.')),15000); probe.onloadedmetadata=()=>{clearTimeout(timer); probe.videoWidth && probe.duration > 0 ? resolve() : reject(Error('Vídeo inválido.'));}; probe.onerror=()=>{clearTimeout(timer);reject(Error('Formato de vídeo não suportado neste navegador.'));};probe.muted=true;probe.playsInline=true;probe.preload='metadata';probe.src=media; }); }
    finally { probe.removeAttribute('src'); probe.load(); URL.revokeObjectURL(media); }
    const initialId='user-'+hash,collision=allAssets().find(video=>video.id===initialId&&video.sha256!==hash);
    const id=target?.id||(collision?initialId+'-'+crypto.randomUUID():initialId);
    const record={id,name,group,gender:target?.gender||'Pessoal',collection:target?.collection||'gymfaster',source:'Meu vídeo',url:target?.url||'local-video:'+id,sha256:hash,exerciseKey:target?.exerciseKey||identity,aliases:[...new Set([...(target?.aliases||[]),target?.originalName,target?.name].filter(Boolean))],sourceIds:target?.sourceIds||[],driveUrl:target?.driveUrl||'',localReplacement:!!target,kind:target?'replacement':'personal',updatedAt:new Date().toISOString()};
    try{await records('put',{...record,blob:file});}
    catch(error){
      // Some WebKit stores reject Blob/File serialization; bytes remain durable.
      if(!['UnknownError','DataCloneError'].includes(error.cause?.name||error.name))throw error;
      await records('put',{...record,bytes:await file.arrayBuffer(),mimeType:file.type});
    }
    // Do not revoke existing URLs: an open preview or GIF can still be using them.
    const asset={...record,media:URL.createObjectURL(file)};
    urls.push(asset.media);custom=custom.filter(video=>video.id!==id);custom.push(asset);
    window.WorkoutVideoLibrary?.registerUpload(id);
    window.dispatchEvent(new CustomEvent('workout-video-library-change',{detail:{action:target?'replace':'add',id}}));
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
    const title=make('h3','Salvar vídeo na biblioteca'),hint=make('p','Use o nome de um exercício existente para substituir o vídeo, ou outro nome para cadastrar uma variação. O arquivo fica salvo somente neste navegador e aparelho; links externos continuam com o vídeo original.'),form=make('form'),name=make('input'),category=make('select'),file=make('input'),status=make('p'),save=make('button','Salvar vídeo'),close=make('button','Cancelar'),targetChoice=make('select'),targetLabel=make('label','Vídeo a substituir');
    name.value=String(defaults.name||'').slice(0,160);name.required=true;name.maxLength=160;name.placeholder='Ex.: Afundo com Halteres';name.setAttribute('aria-label','Nome do exercício');category.required=true;category.setAttribute('aria-label','Categoria do vídeo');
    const placeholder=make('option','Escolha a categoria');placeholder.value='';category.append(placeholder);
    [...new Set(current().map(v=>v.group))].sort((a,b)=>a.localeCompare(b,'pt-BR')).forEach(g=>{const option=make('option',g);option.value=g;category.append(option);});
    if(defaults.group)category.value=defaults.group;
    targetChoice.setAttribute('aria-label','Vídeo a substituir');targetLabel.append(targetChoice);targetLabel.hidden=true;
    const existing=make('section');existing.className='video-existing-choice';existing.hidden=true;
    const existingTitle=make('strong','Já existe um vídeo com este nome'),existingInfo=make('p'),preview=make('button','Ver vídeo existente'),decision=make('fieldset'),legend=make('legend','Deseja substituir este vídeo?');
    preview.type='button';preview.className='video-existing-preview';decision.append(legend);
    const radios=[];
    for(const [value,text]of [['replace','Sim, substituir pelo novo arquivo'],['keep','Não, manter o vídeo existente']]){
      const label=make('label'),radio=make('input');radio.type='radio';radio.name='videoReplacementDecision';radio.value=value;radio.required=true;label.append(radio,document.createTextNode(text));decision.append(label);radios.push(radio);
    }
    const previewActions=make('div'),newPreview=make('button','Ver novo vídeo');previewActions.className='video-compare-actions';newPreview.type='button';newPreview.disabled=true;previewActions.append(preview,newPreview);existing.append(existingTitle,existingInfo,previewActions,decision);let previewURL=null;const releasePreview=()=>{if(!previewURL)return;const openPreview=document.querySelector('#movementPreview');if(openPreview?.querySelector('video')?.getAttribute('src')===previewURL)openPreview.close();URL.revokeObjectURL(previewURL);previewURL=null;};newPreview.onclick=()=>{if(!file.files[0])return;if(!previewURL)previewURL=URL.createObjectURL(file.files[0].type?file.files[0]:new Blob([file.files[0]],{type:/\.webm$/i.test(file.files[0].name)?'video/webm':/\.mov$/i.test(file.files[0].name)?'video/quicktime':'video/mp4'}));WorkoutVideoPreview.open({name:name.value+' · Novo arquivo',collection:'gymfaster',source:'Arquivo escolhido',localURL:previewURL},newPreview);};file.onchange=()=>{releasePreview();newPreview.disabled=!file.files.length;};
    let candidates=[],targetId='';
    const chosenDecision=()=>radios.find(radio=>radio.checked)?.value;
    function updateTarget(){
      candidates=matchingName(name.value);targetId=candidates.length===1?candidates[0].id:'';radios.forEach(radio=>{radio.checked=false;});
      targetLabel.hidden=candidates.length<2;targetChoice.required=candidates.length>1;targetChoice.disabled=candidates.length<2;
      targetChoice.replaceChildren(new Option('Escolha a versão que será substituída',''));
      candidates.forEach(asset=>targetChoice.add(new Option([asset.name,asset.gender,asset.source].filter(Boolean).join(' · '),asset.id)));
      if(candidates.length>1&&candidates.some(asset=>asset.id===defaults.replaceId)){targetChoice.value=defaults.replaceId;targetId=defaults.replaceId;}
      if(targetId&&!category.value)category.value=candidates.find(asset=>asset.id===targetId).group;
      describeTarget();
    }
    function describeTarget(){
      const target=candidates.find(asset=>asset.id===targetId);
      existing.hidden=!candidates.length;decision.disabled=!target;preview.disabled=!target;
      existingTitle.textContent=candidates.length>1?'Existem '+candidates.length+' versões com este nome':'Já existe um vídeo com este nome';
      existingInfo.textContent=target?[target.name,target.group,target.gender,target.source].filter(Boolean).join(' · '):candidates.map(asset=>[asset.name,asset.gender,asset.source].filter(Boolean).join(' · ')).join('\n');
      const keeping=!!target&&chosenDecision()==='keep';
      if(target&&!category.value)category.value=target.group;
      file.disabled=keeping;file.required=!target||chosenDecision()==='replace';category.disabled=keeping;category.required=!keeping;
      radios.forEach(radio=>{radio.required=!!target;});
      status.textContent=target?(chosenDecision()==='replace'?'Ao salvar, o novo arquivo substituirá “'+target.name+'”. Os vínculos e favoritos serão mantidos.':chosenDecision()==='keep'?'O vídeo existente será mantido, sem substituir o arquivo nem criar uma cópia.':'Confira o vídeo existente e escolha se deseja substituí-lo.') :candidates.length>1?'Escolha qual versão deseja conferir.':'Será cadastrado um novo vídeo.';
    }
    name.oninput=updateTarget;targetChoice.onchange=()=>{targetId=targetChoice.value;radios.forEach(radio=>{radio.checked=false;});describeTarget();};
    radios.forEach(radio=>{radio.onchange=describeTarget;});
    preview.onclick=()=>{const asset=candidates.find(asset=>asset.id===targetId);if(asset)WorkoutVideoPreview.open(asset,preview);};
    file.type='file';file.accept='video/mp4,video/webm,video/quicktime,.mp4,.m4v,.mov,.webm';file.required=true;file.setAttribute('aria-label','Arquivo de vídeo');save.type='submit';save.className='video-save-primary';close.type='button';close.className='video-save-cancel';status.setAttribute('role','status');close.onclick=()=>dialog.close();
    const actions=make('div');actions.className='video-save-actions';actions.append(save,close);
    form.append(name,category,targetLabel,existing,file,status,actions);dialog.append(title,hint,form);document.body.append(dialog);dialog.onclose=()=>{releasePreview();dialog.remove();};updateTarget();
    form.noValidate=true;form.onsubmit=async event=>{event.preventDefault();if(save.disabled)return;if(!form.checkValidity()||candidates.length>1&&!targetId||targetId&&!chosenDecision()){const invalid=form.querySelector(':invalid');status.textContent=targetId&&!chosenDecision()?'Escolha se deseja substituir ou manter o vídeo.':invalid?.validationMessage||'Confira os campos obrigatórios.';status.scrollIntoView({block:'nearest'});return;}save.disabled=true;close.disabled=true;status.textContent=targetId?(chosenDecision()==='keep'?'Mantendo vídeo existente…':'Substituindo vídeo…'):'Verificando vídeo e repetições…';try{const asset=targetId&&chosenDecision()==='keep'?WorkoutVideoLibrary.decorate(lookup(targetId)):await add(file.files[0],name.value,category.value,{replaceId:targetId||undefined});await onAdded?.(asset);dialog.close();}catch(error){status.textContent=error.message;status.scrollIntoView({block:'nearest'});}finally{save.disabled=false;close.disabled=false;}};
    dialog.showModal();name.focus();return dialog;
  }
  function lookup(id){return allAssets().find(video=>video.id===id||(video.sourceIds||[]).includes(id));}
  return {load,current,add,openAdd,deleteLocal,lookup,key,get folderURL(){return folderURL;}};
})();
