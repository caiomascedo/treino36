/* Shared YouTube choices by exercise name. Clipboard access requires an explicit paste click. */
window.WorkoutVideoLinks=(()=>{
  const bindings=new Set();let applying=false;
  const key=name=>String(name||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ').trim();
  const youtube=value=>{try{const u=new URL(value.trim());return u.protocol==='https:'&&(/(^|\.)youtube\.com$/.test(u.hostname)&&(u.pathname==='/watch'&&!!u.searchParams.get('v')||/^\/(shorts|embed)\/[^/]+/.test(u.pathname))||u.hostname==='youtu.be'&&u.pathname.length>1);}catch(e){return false;}};
  function read(){try{return JSON.parse(localStorage.getItem('treinoYouTubeLinksV1')||'{}')||{};}catch(e){return {};}}
  function apply(input,value,notify){if(!input.isConnected||input.value===value.trim())return;input.value=value.trim();input.dispatchEvent(new Event('input',{bubbles:true}));notify?.('Link preenchido para este exercício.');}
  function broadcast(name,value){applying=true;try{for(const binding of bindings){if(!binding.input.isConnected){bindings.delete(binding);continue;}if(key(binding.context?.())===name)apply(binding.input,value,binding.notify);}}finally{applying=false;}}
  function attach({input,search,paste,notify,context}){
    for(const binding of bindings)if(!binding.input.isConnected)bindings.delete(binding);
    bindings.add({input,context,notify});
    input.addEventListener('input',()=>{if(applying||!youtube(input.value))return;const name=key(context?.());if(!name)return;const value=input.value.trim(),saved=read();saved[name]=value;try{localStorage.setItem('treinoYouTubeLinksV1',JSON.stringify(saved));}catch(e){}broadcast(name,value);});
    // Run after the PDF has finished creating all part fields and handlers.
    queueMicrotask(()=>{if(!input.isConnected)return;const name=key(context?.());if(!name)return;const saved=read();if(youtube(saved[name]||'')){applying=true;try{apply(input,saved[name],notify);}finally{applying=false;}}else if(youtube(input.value))input.dispatchEvent(new Event('input',{bubbles:true}));});
    paste.onclick=async()=>{try{const text=await navigator.clipboard.readText(),url=new URL(text.trim());if(!['http:','https:'].includes(url.protocol)||url.username||url.password)throw Error();apply(input,url.href,notify);}catch(e){input.focus();notify?.('Copie o link do vídeo e cole neste campo (toque e segure, se necessário).');}};
    // Buscar vídeo is a normal link: never inspect the clipboard on search or return.
  }
  return {attach};
})();
