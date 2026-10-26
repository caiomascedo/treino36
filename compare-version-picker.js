/* A touchable version list avoids rebuilding an iPhone's open native select. */
window.CompareVersionPicker={mount(select){
  const button=document.createElement('button');button.type='button';button.id='chooseComparePrevious';button.className='compare-version-trigger';button.setAttribute('aria-label','Escolher treino anterior');button.setAttribute('aria-haspopup','dialog');button.setAttribute('aria-expanded','false');
  const caption=document.createElement('strong');caption.textContent='Escolher anterior ▾';const selected=document.createElement('span');button.append(caption,selected);select.before(button);
  const dialog=document.createElement('dialog');dialog.id='comparePreviousChoice';dialog.setAttribute('aria-labelledby','comparePreviousChoiceTitle');
  const title=document.createElement('h3');title.id='comparePreviousChoiceTitle';title.textContent='Escolher treino anterior';title.tabIndex=-1;title.setAttribute('autofocus','');
  const search=document.createElement('input');search.type='search';search.placeholder='Pesquisar aluno ou treino';search.setAttribute('aria-label','Pesquisar treino anterior');
  const list=document.createElement('div');list.className='compare-version-list';const cancel=document.createElement('button');cancel.type='button';cancel.className='compare-version-cancel';cancel.textContent='Cancelar';cancel.onclick=()=>dialog.close();
  dialog.append(title,search,list,cancel);document.body.append(dialog);
  function render(){
    list.replaceChildren();const term=search.value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');let count=0;
    for(const group of select.querySelectorAll('optgroup')){
      const section=document.createElement('section'),heading=document.createElement('h4');heading.textContent=group.label;section.append(heading);
      for(const option of group.querySelectorAll('option')){
        const text=(group.label+' '+option.textContent).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');if(term&&!text.includes(term))continue;
        const item=document.createElement('button');item.type='button';item.className='compare-version-option';item.dataset.choice=option.value;item.textContent=option.textContent;item.setAttribute('aria-pressed',String(select.value===option.value));item.disabled=option.disabled;
        item.onclick=()=>{const value=option.value;dialog.close();select.value=value;select.dispatchEvent(new Event('change',{bubbles:true}));sync();};section.append(item);count++;
      }
      if(section.children.length>1)list.append(section);
    }
    if(!count){const empty=document.createElement('p');empty.textContent='Nenhum treino encontrado.';list.append(empty);}
  }
  function sync(){select.hidden=true;selected.textContent=select.selectedOptions[0]?.textContent||'Selecione um treino';button.hidden=!!select.dataset.suggestion;button.disabled=select.options.length===0;}
  dialog.addEventListener('close',()=>{button.setAttribute('aria-expanded','false');button.focus({preventScroll:true});});button.onclick=()=>{search.value='';render();dialog.showModal();button.setAttribute('aria-expanded','true');title.focus({preventScroll:true});};search.oninput=render;sync();return {sync};
}};

window.CompareLayout={mount(dialog){
  const bar=document.createElement('div');bar.className='compare-layout-controls';const title=dialog.querySelector('h3');title.before(bar);bar.append(title);
  const minimize=document.createElement('button');minimize.type='button';minimize.id='compareMinimizeOptions';minimize.setAttribute('aria-controls','compareLabels compareVersionHeader');
  const fullscreen=document.createElement('button');fullscreen.type='button';fullscreen.id='compareFullscreen';fullscreen.setAttribute('aria-pressed','false');fullscreen.textContent='⛶ Tela inteira';
  bar.append(fullscreen);
  const selectionBar=document.createElement('div');selectionBar.className='compare-selection-controls';const selectionLabel=document.createElement('span');selectionLabel.textContent='Treinos da comparação';selectionBar.append(selectionLabel,minimize);
  const header=dialog.querySelector('.compare-header');header.id='compareVersionHeader';header.before(selectionBar);
  const columns=document.createElement('div');columns.className='comparison-columns compare-compact-headings';columns.setAttribute('aria-label','Colunas da comparação');
  for(const label of ['Anterior','Atual']){const heading=document.createElement('strong');heading.textContent=label;columns.append(heading);}
  dialog.querySelector('.compare-header').before(columns);
  let collapsed=false;try{collapsed=localStorage.getItem('treinoCompareOptionsCollapsed')==='1';}catch(error){}
  function sync(){dialog.classList.toggle('compare-options-collapsed',collapsed);minimize.textContent=collapsed?'Selecionar treinos':'Minimizar seleção';minimize.setAttribute('aria-expanded',String(!collapsed));}
  minimize.onclick=()=>{collapsed=!collapsed;sync();try{localStorage.setItem('treinoCompareOptionsCollapsed',collapsed?'1':'0');}catch(error){}};
  fullscreen.onclick=()=>{const full=dialog.classList.toggle('compare-full-screen');fullscreen.textContent=full?'⛶ Reduzir tela':'⛶ Tela inteira';fullscreen.setAttribute('aria-pressed',String(full));};
  dialog.addEventListener('close',()=>{dialog.classList.remove('compare-full-screen');fullscreen.textContent='⛶ Tela inteira';fullscreen.setAttribute('aria-pressed','false');});sync();
}};
