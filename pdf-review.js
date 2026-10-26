/* Optional edits apply to the current PDF draft, preserving the saved workout. */
window.WorkoutPDFReview=(()=>{
  let current=null;
  const node=(tag,attrs={},text)=>{const item=document.createElement(tag);for(const [key,value] of Object.entries(attrs))item.setAttribute(key,value);if(text!==undefined)item.textContent=text;return item;};
  function videoURL(value){if(!value.trim())return '';let parsed;try{parsed=new URL(value.trim());}catch(error){throw Error('Cole o link completo do vídeo, começando com https://.');}if(!['https:','http:'].includes(parsed.protocol)||!parsed.hostname||parsed.username||parsed.password)throw Error('Use um link de vídeo http ou https válido.');return parsed.href;}
  function mount(body,tools,makeURL){
    tools.replaceChildren();let editing=false;const edit=node('button',{type:'button','aria-pressed':'false'},'Editar texto'),hint=node('small',{},'Revisão deste PDF. O treino cadastrado permanece igual.'),videos=node('details'),summary=node('summary',{},'Vídeos · opcional'),help=node('p',{},'Sem alterações, mantém a busca automática do exercício. Para abrir um vídeo específico, busque e cole o link escolhido.'),rows=node('div'),status=node('p',{role:'status'});videos.append(summary,help,rows);tools.append(edit,hint,videos,status);
    const fields=[...body.querySelectorAll('[data-pdf-editable]')],entries=[];
    function finish(){editing=false;edit.textContent='Editar texto';edit.setAttribute('aria-pressed','false');for(const field of fields)field.setAttribute('contenteditable','false');body.classList.remove('pdf-is-editing');}
    edit.onclick=()=>{editing=!editing;edit.textContent=editing?'Concluir edição':'Editar texto';edit.setAttribute('aria-pressed',String(editing));body.classList.toggle('pdf-is-editing',editing);for(const field of fields)field.setAttribute('contenteditable',String(editing));};
    for(const field of fields)field.addEventListener('paste',event=>{event.preventDefault();document.execCommand('insertText',false,event.clipboardData.getData('text/plain'));});
    for(const [index,row] of [...body.querySelectorAll('.pdf-ex-row')].entries()){
      const title=row.querySelector('.pdf-ex-title'),link=row.querySelector('.yt-link'),original=title.textContent,label=node('label'),name=node('span',{},original),input=node('input',{type:'url',placeholder:'Automático · cole um link para trocar','aria-label':'Vídeo de '+original}),search=node('a',{target:'_blank',rel:'noopener'},'Buscar vídeo'),reset=node('button',{type:'button'},'Automático'),item=node('div',{class:'pdf-video-choice'});label.append(name,input);item.append(label,search,reset);rows.append(item);
      const entry={input,link,custom:'',valid:true};entries.push(entry);
      function update(){const exercise=title.textContent.trim()||original;name.textContent=(index+1)+'. '+exercise;search.href='https://www.youtube.com/results?search_query='+encodeURIComponent(exercise+' academia como fazer');try{entry.custom=videoURL(input.value);entry.valid=true;input.setCustomValidity('');link.href=makeURL(exercise,entry.custom,row.dataset.sectionTitle);status.textContent='';}catch(error){entry.valid=false;input.setCustomValidity(error.message);status.textContent=error.message+' Corrija o campo ou toque em Automático.';}}
      input.oninput=update;reset.onclick=()=>{input.value='';update();};title.addEventListener('input',update);update();
    }
    current={finish,validate(){const invalid=entries.find(entry=>!entry.valid);if(invalid){videos.open=true;invalid.input.reportValidity();invalid.input.focus();return false;}finish();return true;}};
  }
  return {mount,videoURL,beforeExport:()=>!current||current.validate()};
})();

window.WhatsAppCopy=(()=>{
  function localNumber(value){let digits=String(value||'').replace(/\D/g,'');if(/^0055\d{10,11}$/.test(digits))return digits.slice(4);if(/^55\d{10,11}$/.test(digits))return digits.slice(2);return digits;}
  async function copy(value,host=document.body){const text=localNumber(value);if(!text)throw Error('Informe o WhatsApp primeiro.');try{await navigator.clipboard.writeText(text);}catch(error){const area=document.createElement('textarea');area.value=text;area.setAttribute('readonly','');area.style.cssText='position:fixed;left:0;top:0;opacity:0';host.append(area);area.select();const copied=document.execCommand('copy');area.remove();if(!copied)throw Error('Não foi possível copiar o número.');}return text;}
  return {localNumber,copy};
})();
