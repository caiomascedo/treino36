/* Personal library labels/removals. Original catalog files and prescriptions
   are kept separately; changes stay in this browser's local storage. */
window.WorkoutVideoLibrary = (() => {
  const key='treinoVideoLibraryV1',eventName='workout-video-library-change';
  function read(){try{const value=JSON.parse(localStorage.getItem(key)||'{}');return {names:value?.names&&typeof value.names==='object'&&!Array.isArray(value.names)?value.names:{},removed:value?.removed&&typeof value.removed==='object'&&!Array.isArray(value.removed)?value.removed:{}};}catch(error){return {names:{},removed:{}};}}
  function save(state,id,action){try{localStorage.setItem(key,JSON.stringify(state));}catch(error){throw Error('Não foi possível salvar a biblioteca neste navegador.');}window.dispatchEvent(new CustomEvent(eventName,{detail:{id,action}}));}
  function decorate(video,state=read()){
    const originalName=video.originalName||video.name,custom=typeof state.names[video.id]==='string'?state.names[video.id].trim():'';
    return {...video,name:custom||originalName,originalName,removed:state.removed[video.id]===true,aliases:[...new Set([...(video.aliases||[]),originalName])]};
  }
  function apply(videos,includeRemoved=false){const state=read();return videos.map(v=>decorate(v,state)).filter(v=>includeRemoved||!v.removed);}
  function rename(id,name){const value=String(name).replace(/\s+/g,' ').trim();if(!value)throw Error('Digite um nome para o exercício.');if(value.length>160)throw Error('Use um nome de até 160 caracteres.');const state=read();state.names[id]=value;save(state,id,'rename');}
  function remove(id){const state=read();state.removed[id]=true;save(state,id,'remove');}
  function restore(id){const state=read();delete state.removed[id];save(state,id,'restore');}
  function resetName(id){const state=read();delete state.names[id];save(state,id,'rename');}
  window.addEventListener('storage',event=>{if(event.key===key)window.dispatchEvent(new CustomEvent(eventName,{detail:{action:'storage'}}));});
  return {apply,decorate,rename,remove,restore,resetName,eventName};
})();
