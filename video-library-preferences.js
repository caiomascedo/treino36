/* Personal library labels/removals. Original catalog files and prescriptions
   are kept separately; changes stay in this browser's local storage. */
window.WorkoutVideoLibrary = (() => {
  const key='treinoVideoLibraryV1',eventName='workout-video-library-change';
  function read(){try{const value=JSON.parse(localStorage.getItem(key)||'{}');return {names:value?.names&&typeof value.names==='object'&&!Array.isArray(value.names)?value.names:{},removed:value?.removed&&typeof value.removed==='object'&&!Array.isArray(value.removed)?value.removed:{},purged:value?.purged&&typeof value.purged==='object'&&!Array.isArray(value.purged)?value.purged:{}};}catch(error){return {names:{},removed:{},purged:{}};}}
  function save(state,id,action){try{localStorage.setItem(key,JSON.stringify(state));}catch(error){throw Error('Não foi possível salvar a biblioteca neste navegador.');}window.dispatchEvent(new CustomEvent(eventName,{detail:{id,action}}));}
  function decorate(video,state=read()){
    const originalName=video.originalName||video.name,custom=typeof state.names[video.id]==='string'?state.names[video.id].trim():'';
    return {...video,name:custom||originalName,originalName,removed:state.removed[video.id]===true||state.purged[video.id]===true,purged:state.purged[video.id]===true,aliases:[...new Set([...(video.aliases||[]),originalName])]};
  }
  function apply(videos,includeRemoved=false){const state=read();return videos.map(v=>decorate(v,state)).filter(v=>!v.purged&&(includeRemoved||!v.removed));}
  function rename(id,name){const value=String(name).replace(/\s+/g,' ').trim();if(!value)throw Error('Digite um nome para o exercício.');if(value.length>160)throw Error('Use um nome de até 160 caracteres.');const state=read();if(window.WorkoutCatalog?.current().some(v=>v.id!==id&&!decorate(v,state).purged&&WorkoutCatalog.key(decorate(v,state).name)===WorkoutCatalog.key(value)))throw Error('Já existe um exercício com este nome. Informe a variação para diferenciá-lo.');state.names[id]=value;save(state,id,'rename');}
  function remove(id){const state=read();state.removed[id]=true;save(state,id,'remove');}
  function restore(id){const state=read();if(state.purged[id])throw Error('Este vídeo foi apagado definitivamente desta biblioteca.');delete state.removed[id];save(state,id,'restore');}
  function resetName(id){const state=read();delete state.names[id];save(state,id,'rename');}
  function registerUpload(id){const state=read();if(!state.purged[id])return;delete state.purged[id];delete state.removed[id];save(state,id,'add');}
  async function purge(video){
    const state=read();if(!state.removed[video.id])throw Error('Mova o vídeo para Ver apagados primeiro.');
    const personal=video.url?.startsWith('local-video:');
    if(!window.confirm('Apagar definitivamente “'+video.name+'” desta biblioteca neste navegador? '+(personal?'O arquivo salvo neste aparelho será excluído.':'O arquivo original no Drive permanece.')+' Não será possível restaurar pela lista.'))return false;
    await window.WorkoutCatalog?.deleteLocal(video.id);
    // Re-read after IndexedDB work so concurrent edits keep their labels.
    const updated=read();delete updated.names[video.id];delete updated.removed[video.id];updated.purged[video.id]=true;save(updated,video.id,'purge');return true;
  }
  window.addEventListener('storage',event=>{if(event.key===key)window.dispatchEvent(new CustomEvent(eventName,{detail:{action:'storage'}}));});
  return {apply,decorate,rename,remove,restore,resetName,purge,registerUpload,eventName};
})();
