/* Reusable section snapshots are separate from pupil favourites and live workouts. */
window.SectionWorkoutFavorites=(()=>{
 const key='treinoSectionFavoritesV1',pinKey='treinoSectionFavoritesPinnedV1',letters='ABCDEF'.split('');
 const uuid=()=>crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+Math.random().toString(36).slice(2);
 const read=()=>{try{const value=JSON.parse(localStorage.getItem(key)||'[]');return Array.isArray(value)?value:[];}catch(error){return [];}};
 const signature=v=>JSON.stringify([v.section,v.title,v.lines]);
 function prepareImport(incoming){
  if(!Array.isArray(incoming))throw Error('Favoritos de treinos inválidos.');
  const result=read();
  for(const raw of incoming){
   if(!raw||!letters.includes(raw.section)||typeof raw.title!=='string'||!Array.isArray(raw.lines)||raw.lines.some(line=>typeof line!=='string'))throw Error('Treino favorito inválido.');
   const item={id:typeof raw.id==='string'?raw.id:uuid(),section:raw.section,title:raw.title,lines:raw.lines.slice(),name:String(raw.name||raw.title),sourceName:String(raw.sourceName||''),pinned:!!raw.pinned,createdAt:raw.createdAt||new Date().toISOString()};
   const existing=result.findIndex(v=>v.id===item.id&&signature(v)===signature(item));
   if(existing>=0)result[existing]=item;else if(!result.some(v=>signature(v)===signature(item))){if(result.some(v=>v.id===item.id))item.id=uuid();result.push(item);}
  }
  return result;
 }
 function mount(config){
  let active='A',scope='A',picker=null;
  const bar=document.createElement('div');bar.id='sectionFavoritesBar';bar.className='section-favorites';
  bar.innerHTML='<strong>⭐ Treinos</strong><select aria-label="Seção dos treinos favoritos" data-scope></select><div class="section-favorite-tabs" data-tabs></div><button type="button" data-add title="Favoritar o treino desta seção">⭐＋</button><button type="button" data-manage title="Organizar favoritos de treinos">⇅</button><button type="button" data-sticky title="Fixar favoritos de treinos no topo">📌</button>';
  config.before.before(bar);const filter=bar.querySelector('[data-scope]');
  for(const letter of [...letters,'all']){const o=document.createElement('option');o.value=letter;o.textContent=letter==='all'?'Todos':letter;filter.append(o);}
  function list(value=scope){return read().filter(v=>value==='all'||v.section===value).sort((a,b)=>Number(b.pinned)-Number(a.pinned));}
  function persist(data){try{localStorage.setItem(key,JSON.stringify(data));render();return true;}catch(error){config.message('Não foi possível salvar os favoritos.','#b22222',false);return false;}}
  function remove(id){const item=read().find(v=>v.id===id);if(!item||!confirm('Retirar “'+item.name+'” dos favoritos de treinos?'))return false;return persist(read().filter(v=>v.id!==id));}
  function pin(id){const data=read(),item=data.find(v=>v.id===id);if(item){item.pinned=!item.pinned;persist(data);}}
  function save(section,snapshot,pinned=false){
   const data=snapshot||config.capture(section);if(!data?.lines?.length){config.message('Esta seção está vazia.','#b22222',false);return;}
   const item={id:uuid(),section,title:data.title,lines:data.lines.slice(),sourceName:data.sourceName||'',name:section+' · '+(data.sourceName||data.title.replace(/^[A-F][.\s:-]*/,'')),pinned,createdAt:new Date().toISOString()},existing=read().find(v=>signature(v)===signature(item));
   if(existing){if(pinned){if(!existing.pinned)pin(existing.id);setScope(section);return;}remove(existing.id);return;}
   const records=read();records.unshift(item);if(persist(records)){setScope(section);config.message('Treino '+section+' salvo nos favoritos.','#1e6f3f',false);}
  }
  function apply(item,destination){return config.apply(item,destination);}
  function tabs(host,value,destination){
   host.replaceChildren();for(const item of list(value)){
    const tab=document.createElement('span');tab.className='section-favorite-tab';tab.dataset.favoriteId=item.id;
    const use=document.createElement('button');use.type='button';use.textContent=(item.pinned?'📌 ':'⭐ ')+item.name;use.title=item.title+' · usar na seção '+destination;use.onclick=()=>apply(item,destination);
    const fixed=document.createElement('button');fixed.type='button';fixed.textContent='📌';fixed.title=item.pinned?'Desafixar este favorito':'Fixar este favorito primeiro';fixed.setAttribute('aria-pressed',String(item.pinned));fixed.onclick=()=>pin(item.id);
    const close=document.createElement('button');close.type='button';close.textContent='×';close.setAttribute('aria-label','Retirar '+item.name+' dos favoritos');close.onclick=()=>remove(item.id);tab.append(use,fixed,close);host.append(tab);
   }
   if(!host.children.length){const empty=document.createElement('small');empty.textContent='Sem favoritos '+(value==='all'?'':value)+'. Use ⭐＋ ou o menu ⋮⋮.';host.append(empty);}
  }
  function render(){filter.value=scope;tabs(bar.querySelector('[data-tabs]'),scope,active);const sticky=localStorage.getItem(pinKey)==='1';bar.classList.toggle('is-sticky',sticky);bar.querySelector('[data-sticky]').setAttribute('aria-pressed',String(sticky));if(picker?.host.isConnected)tabs(picker.host,picker.filter.value,picker.dest);if(manager?.open)renderManager();}
  function setScope(value){scope=value;if(letters.includes(value))active=value;render();}
  filter.onchange=()=>setScope(filter.value);bar.querySelector('[data-add]').onclick=()=>save(active);bar.querySelector('[data-sticky]').onclick=()=>{localStorage.setItem(pinKey,localStorage.getItem(pinKey)==='1'?'0':'1');render();};
  let manager=null;
  function renderManager(){const host=manager.querySelector('[data-records]');host.replaceChildren();for(const item of list('all')){const row=document.createElement('div');row.className='section-favorite-manager-row';const title=document.createElement('span');title.textContent=item.name+' · '+item.title;row.append(title);for(const [label,action] of [['✏️',()=>{const name=prompt('Nome do favorito',item.name);if(name?.trim()){const data=read();data.find(v=>v.id===item.id).name=name.trim();persist(data);}}],['📌',()=>pin(item.id)],['↑',()=>move(item.id,-1)],['↓',()=>move(item.id,1)],['×',()=>remove(item.id)]]){const button=document.createElement('button');button.type='button';button.textContent=label;button.title=({'✏️':'Renomear','📌':'Fixar ou desafixar','↑':'Subir','↓':'Descer','×':'Retirar favorito'}[label]||label)+' '+item.name;button.setAttribute('aria-label',button.title);button.onclick=action;row.append(button);}host.append(row);}}
  function move(id,delta){const data=list('all'),index=data.findIndex(v=>v.id===id),next=index+delta;if(next<0||next>=data.length)return;[data[index],data[next]]=[data[next],data[index]];persist(data);}
  bar.querySelector('[data-manage]').onclick=()=>{if(!manager)manager=config.createDialog('sectionFavoriteManager','Favoritos de treinos','<div data-records></div><div class="dialog-actions"><button data-close>Fechar</button></div>');renderManager();manager.showModal();};
  function attachPicker(host,dest){setScope(dest);const wrap=document.createElement('div');wrap.className='section-favorite-picker';wrap.innerHTML='<label>⭐ Favoritos <select aria-label="Filtrar favoritos por seção"></select></label><div class="section-favorite-tabs"></div>';const select=wrap.querySelector('select');for(const value of [dest,'all',...letters.filter(v=>v!==dest)]){const o=document.createElement('option');o.value=value;o.textContent=value==='all'?'Todas as seções':value;select.append(o);}host.prepend(wrap);picker={host:wrap.querySelector('.section-favorite-tabs'),filter:select,dest};select.onchange=()=>tabs(picker.host,select.value,dest);render();}
  config.root.addEventListener('pointerdown',event=>{const section=event.target.closest('.section');if(section){const letter=letters.find(v=>section.classList.contains('sec-'+v.toLowerCase()));if(letter&&letter!==active)setScope(letter);}});
  window.addEventListener('storage',event=>{if(event.key===key||event.key===pinKey)render();});render();
  function status(section,snapshot){const data=snapshot||config.capture(section);return read().find(v=>signature(v)===signature({section,title:data.title,lines:data.lines}));}
  function pinSection(section,snapshot){const found=status(section,snapshot);if(found)pin(found.id);else save(section,snapshot,true);}
  return {save,remove,pin,pinSection,status,attachPicker,setScope,destination:()=>active,refresh:render,export:read,prepareImport,key};
 }
 return {mount,prepareImport,key,pinKey};
})();
