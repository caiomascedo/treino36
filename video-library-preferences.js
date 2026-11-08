/* Personal library labels/removals. Original catalog files and prescriptions
   are kept separately; changes stay in this browser's local storage. */
window.WorkoutVideoLibrary = (() => {
  const key='treinoVideoLibraryV1',eventName='workout-video-library-change';
  function read(){try{const value=JSON.parse(localStorage.getItem(key)||'{}');return {names:value?.names&&typeof value.names==='object'&&!Array.isArray(value.names)?value.names:{},removed:value?.removed&&typeof value.removed==='object'&&!Array.isArray(value.removed)?value.removed:{},purged:value?.purged&&typeof value.purged==='object'&&!Array.isArray(value.purged)?value.purged:{},review:value?.review&&typeof value.review==='object'&&!Array.isArray(value.review)?value.review:{}};}catch(error){return {names:{},removed:{},purged:{},review:{}};}}
  function save(state,id,action){try{localStorage.setItem(key,JSON.stringify(state));}catch(error){throw Error('Não foi possível salvar a biblioteca neste navegador.');}window.dispatchEvent(new CustomEvent(eventName,{detail:{id,action}}));}
  function favorites(){try{return JSON.parse(localStorage.getItem('treinoFavoriteVideosV1')||'{}')||{};}catch(e){return {};}}
  function isFavorite(id){return favorites()[id]===true;}
  function toggleFavorite(id){const state=favorites();if(state[id])delete state[id];else state[id]=true;try{localStorage.setItem('treinoFavoriteVideosV1',JSON.stringify(state));}catch(e){throw Error('Não foi possível salvar os favoritos.');}window.dispatchEvent(new CustomEvent(eventName,{detail:{id,action:'favorite'}}));}
  function favoriteButton(video,after){const button=document.createElement('button');button.type='button';button.className='video-favorite';const selected=isFavorite(video.id);button.textContent=selected?'★':'☆';button.setAttribute('aria-label',(selected?'Remover dos favoritos: ':'Favoritar vídeo: ')+video.name);button.setAttribute('aria-pressed',String(selected));button.title=selected?'Remover dos favoritos':'Favoritar vídeo';button.onclick=()=>{try{toggleFavorite(video.id);after?.();}catch(e){alert(e.message);}};return button;}
  function decorate(video,state=read()){
    const originalName=video.originalName||video.name,custom=typeof state.names[video.id]==='string'?state.names[video.id].trim():'';
    return {...video,name:custom||originalName,originalName,removed:state.removed[video.id]===true||state.purged[video.id]===true,purged:state.purged[video.id]===true,aliases:[...new Set([...(video.aliases||[]),originalName])]};
  }
  function apply(videos,includeRemoved=false){const state=read();return videos.map(v=>decorate(v,state)).filter(v=>!v.purged&&(includeRemoved||!v.removed));}
  function rename(id,name){const value=String(name).replace(/\s+/g,' ').trim();if(!value)throw Error('Digite um nome para o exercício.');if(value.length>160)throw Error('Use um nome de até 160 caracteres.');const state=read();if(window.WorkoutCatalog?.current().some(v=>v.id!==id&&!decorate(v,state).purged&&WorkoutCatalog.key(decorate(v,state).name)===WorkoutCatalog.key(value)))throw Error('Já existe um exercício com este nome. Informe a variação para diferenciá-lo.');state.names[id]=value;save(state,id,'rename');}
  function deletionRecord(id,state,asset=window.WorkoutCatalog?.lookup(id)){
    const named=asset?decorate(asset,state):null,now=new Date().toISOString(),personal=id.startsWith('user-')||asset?.scope==='private'||asset?.localReplacement||asset?.url?.startsWith('local-video:');
    return {...state.review[id],id,name:named?.name||state.review[id]?.name||id,originalName:named?.originalName||state.review[id]?.originalName||'',collection:asset?.collection||state.review[id]?.collection||'',scope:personal?'private':'catalog',filePath:personal?'':asset?.media?.match(/^(?:gymfaster|cmfit)-media\/[^?#]+/)?.[0]||state.review[id]?.filePath||(asset?.collection?(asset.collection==='cm'?'cmfit-media/':'gymfaster-media/')+id+'.mp4':''),url:asset?.driveUrl||asset?.url||state.review[id]?.url||'',sha256:asset?.sha256||state.review[id]?.sha256||'',sourceIds:asset?.sourceIds||state.review[id]?.sourceIds||[id],deletedAt:state.review[id]?.deletedAt||now,updatedAt:now};
  }
  function review(){const state=read(),ids=[...new Set([...Object.keys(state.removed).filter(id=>state.removed[id]),...Object.keys(state.purged).filter(id=>state.purged[id])])];return ids.map(id=>({...state.review[id]||deletionRecord(id,state),status:state.purged[id]?'purged':'removed'})).sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt));}
  function remove(id){const state=read();state.review[id]=deletionRecord(id,state);state.removed[id]=true;save(state,id,'remove');}
  function restore(id){const state=read();if(state.purged[id])throw Error('Este vídeo foi apagado definitivamente desta biblioteca.');delete state.removed[id];save(state,id,'restore');}
  function resetName(id){const state=read();delete state.names[id];save(state,id,'rename');}
  function registerUpload(id){const state=read();if(!state.purged[id]&&!state.removed[id])return;delete state.purged[id];delete state.removed[id];save(state,id,'add');}
  async function purge(video){
    const state=read();if(!state.removed[video.id])throw Error('Mova o vídeo para Ver apagados primeiro.');
    const personal=video.scope==='private'||video.localReplacement||video.url?.startsWith('local-video:');
    if(!window.confirm('Apagar definitivamente “'+video.name+'” desta biblioteca neste navegador? '+(personal?'O arquivo salvo neste aparelho será excluído.':'O arquivo original no Drive permanece.')+' Não será possível restaurar pela lista.'))return false;
    await window.WorkoutCatalog?.deleteLocal(video.id);
    // Re-read after IndexedDB work so concurrent edits keep their labels.
    const updated=read();updated.review[video.id]=deletionRecord(video.id,updated,video);delete updated.names[video.id];delete updated.removed[video.id];updated.purged[video.id]=true;save(updated,video.id,'purge');return true;
  }
  let reviewDialog,renderReview;
  async function openReview(){
    try{await window.WorkoutCatalog?.load();}catch(error){}
    if(!reviewDialog){
      const make=(tag,text)=>{const el=document.createElement(tag);if(text)el.textContent=text;return el;};
      reviewDialog=make('dialog');reviewDialog.id='videoDeletionReview';reviewDialog.setAttribute('aria-label','Lista de vídeos apagados');
      const title=make('h3','Lista de vídeos apagados'),help=make('p','As exclusões da biblioteca ficam registradas aqui. Envie esta lista quando quiser pedir a revisão dos arquivos no GitHub. Arquivos pessoais são identificados separadamente.'),list=make('div'),actions=make('div'),copy=make('button','Copiar lista'),download=make('button','Baixar lista'),close=make('button','Fechar'),status=make('p');list.className='video-deletion-list';actions.className='video-deletion-actions';status.setAttribute('role','status');
      const content=()=>JSON.stringify({format:'treino36-video-deletion-review-v1',exportedAt:new Date().toISOString(),videos:review()},null,2);
      renderReview=()=>{
        list.replaceChildren();const entries=review();
        if(!entries.length)list.append(make('p','Nenhum vídeo na lista de apagados.'));
        for(const entry of entries){
          const row=make('article'),name=make('strong',entry.name),path=make('small',entry.scope==='private'?'Arquivo pessoal deste aparelho':entry.filePath||'Arquivo do catálogo · '+entry.id),state=make('small',entry.status==='purged'?'Apagado definitivamente da biblioteca':'Em Ver apagados · pode ser restaurado');
          row.dataset.videoId=entry.id;row.append(name,path,state);
          if(entry.status!=='purged'){
            const tools=make('div'),restore=make('button','Restaurar'),remove=make('button','Apagar definitivamente');tools.className='video-deletion-row-actions';remove.className='video-deletion-purge';restore.type=remove.type='button';
            restore.onclick=()=>{try{WorkoutVideoLibrary.restore(entry.id);status.textContent='Vídeo restaurado na biblioteca.';}catch(error){status.textContent=error.message;}};
            remove.onclick=async()=>{restore.disabled=remove.disabled=true;try{if(await purge(entry))status.textContent='Vídeo apagado definitivamente desta biblioteca.';}catch(error){status.textContent=error.message;}finally{restore.disabled=remove.disabled=false;}};
            tools.append(restore,remove);row.append(tools);
          }
          list.append(row);
        }
        copy.disabled=download.disabled=!entries.length;
      };
      copy.onclick=async()=>{try{await navigator.clipboard.writeText(content());status.textContent='Lista copiada. Cole na conversa quando quiser pedir a revisão.';}catch(error){let field=reviewDialog.querySelector('textarea');if(!field){field=make('textarea');field.setAttribute('aria-label','Lista para copiar');reviewDialog.insertBefore(field,actions);}field.value=content();field.focus();field.select();status.textContent='Selecione e copie a lista abaixo.';}};
      download.onclick=()=>{const url=URL.createObjectURL(new Blob([content()],{type:'application/json'})),a=make('a');a.href=url;a.download='videos-apagados-revisar-github.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);};close.onclick=()=>reviewDialog.close();actions.append(copy,download,close);reviewDialog.append(title,help,list,actions,status);document.body.append(reviewDialog);
      window.addEventListener(eventName,()=>{if(reviewDialog.open)renderReview();});
    }
    renderReview();reviewDialog.querySelector('textarea')?.remove();reviewDialog.querySelector('[role=status]').textContent='';if(!reviewDialog.open)reviewDialog.showModal();
  }
  function reviewButton(){const button=document.createElement('button');button.type='button';button.textContent='Lista de apagados';button.onclick=()=>openReview();return button;}
  window.addEventListener('storage',event=>{if(event.key===key||event.key==='treinoFavoriteVideosV1')window.dispatchEvent(new CustomEvent(eventName,{detail:{action:'storage'}}));});
  return {isFavorite,toggleFavorite,favoriteButton,apply,decorate,rename,remove,restore,resetName,purge,registerUpload,review,openReview,reviewButton,eventName};
})();
