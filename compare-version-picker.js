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
