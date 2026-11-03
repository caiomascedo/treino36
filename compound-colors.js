/* Optional editor colors: wrappers preserve text and remain editable. */
window.WorkoutCompoundColors=(()=>{
  const key='treinoCompoundColorsV1',palette=['#b91c1c','#15803d','#ca8a04','#111111','#1d4ed8','#9333ea','#c2410c','#0f766e','#be185d','#4338ca'];
  let enabled=false,observer,timer,button;
  try{enabled=JSON.parse(localStorage.getItem(key)||'{}').enabled===true;}catch(e){}
  const color=i=>palette[i%palette.length];
  function unwrap(row){row.querySelectorAll('.compound-ink').forEach(span=>span.replaceWith(...span.childNodes));}
  function paint(nodes){let part=0;for(const text of nodes){const fragment=document.createDocumentFragment();for(const value of text.textContent.split(/(\s*\+\s*)/)){if(!value)continue;if(/^\s*\+\s*$/.test(value)){fragment.append(document.createTextNode(value));part++;}else{const span=document.createElement('span');span.className='compound-ink';span.style.color=color(part);span.textContent=value;fragment.append(span);}}text.replaceWith(fragment);}}
  function textNodes(root,exclude){const walk=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),nodes=[];let text;while((text=walk.nextNode()))if(!exclude(text))nodes.push(text);return nodes;}
  function links(root,active){root.querySelectorAll('a.gif-sample,a.exercise-video').forEach((link,index)=>{link.classList.toggle('compound-ink-link',active);if(active)link.style.setProperty('--compound-ink',color(Number(link.dataset.sampleIndex??link.dataset.videoPart??index)));else link.style.removeProperty('--compound-ink');});}
  function rowColors(row){
    if(row.contains(document.activeElement)&&document.activeElement.isContentEditable)return;
    const title=row.querySelector('.bold');if(!title)return;
    const signature=String(enabled)+':'+row.textContent;
    if(row.dataset.compoundInk===signature)return;
    unwrap(row);const compound=window.WorkoutVideoMatch?.parts(title.textContent).length>1,active=enabled&&compound;
    links(row,active);
    if(active){paint(textNodes(title,()=>false));const detail=textNodes(row,text=>title.contains(text)||text.parentElement.closest('a,button,.exercise-gifs,.exercise-videos,[contenteditable="false"]'));if(detail.map(n=>n.textContent).join('').includes('+'))paint(detail);}
    row.dataset.compoundInk=signature;
  }
  function apply(){
    observer?.disconnect();
    document.querySelectorAll('.section ol>li').forEach(rowColors);
    document.querySelectorAll('#mobilityDialog .exercise-gifs').forEach(holder=>links(holder,enabled&&holder.querySelectorAll('.gif-sample').length>1));
    if(button)button.setAttribute('aria-pressed',String(enabled));
    observer?.observe(document.body,{subtree:true,childList:true,characterData:true});
  }
  function schedule(){clearTimeout(timer);timer=setTimeout(apply,120);}
  document.addEventListener('DOMContentLoaded',()=>{
    button=document.createElement('button');button.type='button';button.className='compound-colors-control';button.textContent='🎨 Cores';button.title='Ativar ou desativar cores nos conjugados da ficha';button.setAttribute('aria-label','Colorir conjugados na ficha');
    const linksMenu=document.querySelector('[data-media-menu="all"]');(linksMenu||document.getElementById('redoBtn'))?.after(button);
    const redo=document.getElementById('redoBtn');if(redo){const css=getComputedStyle(redo);for(const name of ['fontSize','fontFamily','fontWeight','lineHeight','padding','borderRadius'])button.style[name]=css[name];button.style.height=redo.getBoundingClientRect().height+'px';}
    button.onclick=()=>{enabled=!enabled;try{localStorage.setItem(key,JSON.stringify({enabled}));}catch(e){}apply();};
    observer=new MutationObserver(schedule);document.addEventListener('focusout',schedule);apply();
  },{once:true});
  return {refresh:schedule};
})();
