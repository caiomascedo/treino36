/* Explicit paste is always available. Return-paste runs only for a changed YouTube clipboard. */
window.WorkoutVideoLinks=(()=>{
  let pending=null;
  const youtube=value=>{try{const u=new URL(value.trim());return u.protocol==='https:'&&(/(^|\.)youtube\.com$/.test(u.hostname)&&(u.pathname==='/watch'&&!!u.searchParams.get('v')||/^\/(shorts|embed)\/[^/]+/.test(u.pathname))||u.hostname==='youtu.be'&&u.pathname.length>1);}catch(e){return false;}};
  function apply(input,value,notify){if(!input.isConnected)return;input.value=value.trim();input.dispatchEvent(new Event('input',{bubbles:true}));notify?.('Link colado.');}
  async function resume(){
    const request=pending;if(!request||request.before===null||Date.now()-request.at>600000||!request.input.isConnected||!request.input.getClientRects().length||request.input.value!==request.value||request.context?.()!==request.contextValue)return;
    try{const value=await navigator.clipboard.readText();if(pending===request&&value!==request.before&&youtube(value)){pending=null;apply(request.input,value,request.notify);}}catch(e){}
  }
  window.addEventListener('focus',resume);document.addEventListener('visibilitychange',()=>{if(!document.hidden)resume();});
  function attach({input,search,paste,notify,context}){
    paste.onclick=async()=>{try{const text=await navigator.clipboard.readText(),url=new URL(text.trim());if(!['http:','https:'].includes(url.protocol)||url.username||url.password)throw Error();pending=null;apply(input,url.href,notify);}catch(e){input.focus();notify?.('Copie o link do vídeo e cole neste campo (toque e segure, se necessário).');}};
    search.addEventListener('click',()=>{const request={input,value:input.value,before:null,at:Date.now(),notify,context,contextValue:context?.()};pending=request;try{navigator.clipboard.readText().then(text=>{if(pending===request)request.before=text;}).catch(()=>{});}catch(e){}});
  }
  return {attach};
})();
