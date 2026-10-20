/* Durable image payloads live in IndexedDB; small references stay in localStorage. */
window.PhotoVault=(()=>{
  const prefix='treino36:photo:',images=new Map(),references=new Map();let database,available=false,error=null;
  const pattern=/data:image\/(?:jpeg|jpg|png|webp);base64,[a-z0-9+/=]+/gi;
  const tokens=/treino36:photo:[a-z0-9-]+/gi;
  const channel=typeof BroadcastChannel==='function'?new BroadcastChannel('treino36-photo-vault'):null;
  function remember(record){images.set(record.id,record.data);references.set(record.data,record.id);}
  function transaction(mode,action){return new Promise((resolve,reject)=>{const tx=database.transaction('images',mode),store=tx.objectStore('images');let result;tx.oncomplete=()=>resolve(result);tx.onabort=tx.onerror=()=>reject(tx.error||Error('Não foi possível guardar as fotos.'));action(store,value=>{result=value;});});}
  async function refresh(){if(available)await transaction('readonly',(store,done)=>{store.getAll().onsuccess=event=>{for(const record of event.target.result)remember(record);done();};});}
  const ready=(async()=>{
    try{database=await new Promise((resolve,reject)=>{const request=indexedDB.open('treino36_photos',1);request.onupgradeneeded=()=>request.result.createObjectStore('images',{keyPath:'id'});request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);request.onblocked=()=>reject(Error('Feche outras abas antigas do site para abrir o armazenamento das fotos.'));});available=true;await refresh();}
    catch(reason){available=false;error=reason;}
  })();
  async function identifier(data){
    if(crypto.subtle){const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(data));return prefix+Array.from(new Uint8Array(hash),byte=>byte.toString(16).padStart(2,'0')).join('');}
    // HTTP test/legacy contexts: validate the full payload before reusing any identifier.
    let a=2166136261,b=5381;for(let i=0;i<data.length;i++){a=Math.imul(a^data.charCodeAt(i),16777619);b=Math.imul(b,33)^data.charCodeAt(i);}return prefix+(a>>>0).toString(16)+'-'+(b>>>0).toString(16)+'-'+data.length;
  }
  async function prepare(value){
    await ready;if(!available)throw Error('Não foi possível abrir o armazenamento ampliado. Suas fotos anteriores foram mantidas. '+(error?.message||''));
    const text=typeof value==='string'?value:JSON.stringify(value),pending=[];
    for(const data of new Set(text.match(pattern)||[]))if(!references.has(data)){
      let id=await identifier(data);const existing=await transaction('readonly',(store,done)=>{store.get(id).onsuccess=e=>done(e.target.result);});
      if(existing&&existing.data!==data)id+='-'+Date.now()+'-'+Math.random().toString(16).slice(2);
      if(existing?.data===data){remember(existing);continue;}pending.push({id,data});
    }
    if(pending.length){await transaction('readwrite',(store)=>{for(const record of pending)store.put(record);});for(const record of pending)remember(record);channel?.postMessage(pending);}
    return value;
  }
  function dehydrate(text){return available?text.replace(pattern,data=>references.get(data)||data):text;}
  function hydrate(text){return typeof text==='string'?text.replace(tokens,id=>{if(!images.has(id))throw Error('Uma foto ainda não foi carregada. Atualize a página; não apague os dados do site.');return images.get(id);}):text;}
  channel?.addEventListener('message',event=>{if(Array.isArray(event.data))for(const record of event.data)if(record?.id?.startsWith(prefix)&&typeof record.data==='string')remember(record);});
  function bytes(){let size=0;for(const data of images.values())size+=data.length;return size;}
  return {ready,prepare,hydrate,dehydrate,refresh,bytes,get available(){return available;},get error(){return error;}};
})();
