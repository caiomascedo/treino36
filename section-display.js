/* Screen visibility is a view preference; it never changes workout contents. */
window.SectionDisplay={mount(root,config){
  const key='treinoSectionViews',panel=document.createElement('details'),summary=document.createElement('summary'),choices=document.createElement('div'),all=document.createElement('button'),empty=document.createElement('button');let preferences={};
  try{preferences=JSON.parse(localStorage.getItem(key)||'{}');if(!preferences||typeof preferences!=='object'||Array.isArray(preferences))preferences={};}catch(error){}
  panel.className='section-display-options';summary.textContent='Seções na tela';panel.append(summary);all.type=empty.type='button';all.textContent='Mostrar todas';empty.textContent='Ocultar vazias';panel.append(all,empty,choices);root.append(panel);panel.style.cssText='font:12px Arial;color:#29465a;padding:8px;border:1px solid #dce4ea;border-radius:7px';choices.style.cssText='display:flex;flex-wrap:wrap;gap:12px;margin-top:8px';const inputs=new Map();
  function selected(){const saved=preferences[config.identity()];return Array.isArray(saved)?saved:config.ids();}
  function persist(value){preferences[config.identity()]=value;try{localStorage.setItem(key,JSON.stringify(preferences));}catch(error){}refresh();}
  for(const id of 'ABCDEF'){const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.setAttribute('aria-label','Mostrar seção '+id+' na tela');check.style.cssText='width:17px;height:17px;accent-color:#1e6f3f';label.style.cssText='display:flex;align-items:center;gap:4px';label.append(check,document.createTextNode(id));choices.append(label);inputs.set(id,check);check.onchange=()=>{const value=new Set(selected());if(check.checked)value.add(id);else value.delete(id);persist([...value]);};}
  function refresh(){const active=config.ids(),visible=selected();for(const [id,input] of inputs){input.parentElement.hidden=!active.includes(id);input.checked=visible.includes(id);config.group(id).classList.toggle('section-display-hidden',active.includes(id)&&!visible.includes(id));}}
  all.onclick=()=>persist(config.ids());empty.onclick=()=>persist(config.ids().filter(id=>config.filled(id)));
  const observer=new MutationObserver(refresh);for(const id of 'ABCDEF')observer.observe(config.list(id),{childList:true,subtree:true,characterData:true});
  refresh();return {refresh,reveal(id){persist([...new Set([...selected(),id])]);}};
}};
