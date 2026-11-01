/* Optional edits apply to the current PDF draft, preserving the saved workout. */
window.WorkoutPDFReview=(()=>{
  let current=null;
  const node=(tag,attrs={},text)=>{const item=document.createElement(tag);for(const [key,value] of Object.entries(attrs))item.setAttribute(key,value);if(text!==undefined)item.textContent=text;return item;};
  function videoURL(value){if(!value.trim())return '';let parsed;try{parsed=new URL(value.trim());}catch(error){throw Error('Cole o link completo do vídeo, começando com https://.');}if(!['https:','http:'].includes(parsed.protocol)||!parsed.hostname||parsed.username||parsed.password)throw Error('Use um link de vídeo http ou https válido.');return parsed.href;}
  function directVideoURL(value){
    let url=videoURL(value);
    for(let depth=0;depth<8;depth++){
      const parsed=new URL(url);
      if(parsed.hostname!=='caio.tail953b6e.ts.net'||parsed.pathname!=='/r/yt')return url;
      const target=parsed.searchParams.get('url');if(!target)break;url=videoURL(target);
    }
    throw Error('Use o link original do vídeo para abrir sem monitoramento.');
  }
  function mount(body,tools,makeURL,icon,onVideoChange,samples){
    tools.replaceChildren();let editing=false;const edit=node('button',{type:'button','aria-pressed':'false'},'Editar texto'),hint=node('small',{},'O texto é editado só neste PDF. Os links escolhidos ficam salvos nos exercícios.'),videos=node('details'),summary=node('summary',{},'Vídeos · opcional'),help=node('p',{},'Sem alterações, mantém a busca automática do exercício. Para abrir um vídeo específico, busque e cole o link escolhido.'),rows=node('div'),status=node('p',{role:'status'});const expand=node('button',{type:'button'},'Expandir todos'),collapse=node('button',{type:'button'},'Recolher todos'),groupTools=node('div',{class:'pdf-video-group-tools'});groupTools.append(expand,collapse);expand.onclick=()=>{videos.open=true;for(const panel of rows.querySelectorAll('.pdf-video-section'))panel.open=true;};collapse.onclick=()=>{for(const panel of rows.querySelectorAll('.pdf-video-section'))panel.open=false;};videos.append(summary,help,groupTools,rows);tools.append(edit,hint,videos,status);
    const fields=[...body.querySelectorAll('[data-pdf-editable]')],entries=[],groups=new Map();
    const sectionBox=node('details',{class:'pdf-section-choice'}),sectionLegend=node('summary',{},'Seções no PDF'),sectionChecks=node('div',{class:'pdf-section-checks'}),allSections=node('button',{type:'button'},'Marcar todas'),noSections=node('button',{type:'button'},'Desmarcar todas'),sectionInputs=[];sectionBox.append(sectionLegend,sectionChecks,allSections,noSections);tools.insertBefore(sectionBox,hint);
    for(const section of body.querySelectorAll('.pdf-sec')){const id=section.dataset.pdfSection||section.querySelector('.pdf-sec-title').textContent.trim()[0],label=node('label'),check=node('input',{type:'checkbox','aria-label':'Incluir seção '+id+' no PDF'});check.checked=true;label.append(check,document.createTextNode(id));sectionChecks.append(label);sectionInputs.push(check);check.onchange=()=>{section.hidden=!check.checked;if(groups.has(section))groups.get(section).panel.hidden=!check.checked;status.textContent='';};}
    allSections.onclick=()=>{for(const check of sectionInputs){check.checked=true;check.onchange();}};noSections.onclick=()=>{for(const check of sectionInputs){check.checked=false;check.onchange();}};

    const modelLabel=node('label',{class:'pdf-model-choice'},'Modelo do PDF '),model=node('select',{'aria-label':'Modelo do PDF'});model.append(node('option',{value:'inline'},'(Vídeo) alinhado à direita'),node('option',{value:'old'},'Antigo · botão YouTube'));modelLabel.append(model);tools.prepend(modelLabel);
    const linkOptions=node('div',{class:'pdf-link-options'}),trackingLabel=node('label',{},'Vídeos '),tracking=node('select',{'aria-label':'Monitoramento dos vídeos'}),startLabel=node('label',{class:'pdf-start-choice'}),includeStart=node('input',{type:'checkbox','aria-label':'Incluir Iniciar treino no PDF'}),linkHint=node('small');
    tracking.append(node('option',{value:'tracked'},'Com monitoramento'),node('option',{value:'direct'},'Direto · sem monitoramento'));trackingLabel.append(tracking);startLabel.append(includeStart,document.createTextNode('Iniciar treino · registra presença'));const videosLabel=node('label',{class:'pdf-videos-choice'}),includeVideos=node('input',{type:'checkbox','aria-label':'Incluir vídeos no PDF'}),startOnly=node('button',{type:'button',id:'pdfStartOnly'},'Só Iniciar treino');videosLabel.append(includeVideos,document.createTextNode('Vídeos no PDF'));linkOptions.append(trackingLabel,videosLabel,startLabel,startOnly,linkHint);modelLabel.after(linkOptions);
    let preferences={};try{preferences=JSON.parse(localStorage.getItem('treinoPdfLinkOptions')||'{}')||{};}catch(error){}
    includeVideos.checked=preferences.videos!==false;
    tracking.value=preferences.tracking==='direct'?'direct':'tracked';includeStart.checked=typeof preferences.start==='boolean'?preferences.start:tracking.value!=='direct';
    const startLink=body.querySelector('.pdf-start-btn'),startSlot=body.querySelector('.pdf-start-slot');
    function saveLinkOptions(){try{localStorage.setItem('treinoPdfLinkOptions',JSON.stringify({tracking:tracking.value,start:includeStart.checked,videos:includeVideos.checked}));}catch(error){}}
    function applyVideoVisibility(){startOnly.setAttribute('aria-pressed',String(!includeVideos.checked&&includeStart.checked));for(const entry of entries){if(!includeVideos.checked||entry.row.dataset.allowVideo==='false')entry.link.remove();for(const gif of entry.row.querySelectorAll('.pdf-gif-link'))gif.hidden=!includeVideos.checked||entry.row.dataset.allowGifs==='false';const slot=entry.row.querySelector('.pdf-media-links');slot.hidden=![...slot.children].some(link=>!link.hidden);}videos.hidden=!includeVideos.checked;if(!includeVideos.checked)status.textContent='';tracking.disabled=!includeVideos.checked;}
    function applyLinkOptions(){
      for(const entry of entries)entry.update();applyVideoVisibility();
      if(startSlot){startSlot.replaceChildren();if(includeStart.checked&&startLink)startSlot.append(document.createTextNode(' · '),startLink);}
      linkHint.textContent=!includeVideos.checked?(includeStart.checked?'Sem vídeos no PDF; Iniciar treino registra presença.':'PDF sem vídeos e sem registro de presença.'):tracking.value==='direct'?(includeStart.checked?'Vídeos diretos; apenas Iniciar treino registra presença.':'Sem registro de cliques ou presença neste PDF.'):'Os cliques nos vídeos passam pelo seu acompanhamento.';
    }
    startOnly.onclick=()=>{includeVideos.checked=false;includeStart.checked=true;tracking.value='direct';applyLinkOptions();saveLinkOptions();};includeVideos.onchange=()=>{applyModel();applyLinkOptions();saveLinkOptions();};
    tracking.onchange=()=>{if(tracking.value==='direct')includeStart.checked=false;applyLinkOptions();saveLinkOptions();};includeStart.onchange=()=>{applyLinkOptions();saveLinkOptions();};
    function applyModel(){const old=model.value==='old';body.classList.toggle('pdf-style-old',old);for(const entry of entries){if(old){entry.row.querySelector('.pdf-media-links').prepend(entry.link);entry.link.innerHTML=(icon||'<span aria-hidden="true">▶</span>')+' YouTube';}else{entry.row.querySelector('.pdf-media-links').prepend(entry.link);entry.link.textContent='(Vídeo)';}}applyVideoVisibility();try{localStorage.setItem('treinoPdfVideoStyle',model.value);}catch(error){}}
    try{model.value=localStorage.getItem('treinoPdfVideoStyle')==='old'?'old':'inline';}catch(error){}model.onchange=applyModel;
    function finish(){editing=false;edit.textContent='Editar texto';edit.setAttribute('aria-pressed','false');for(const field of fields)field.setAttribute('contenteditable','false');body.classList.remove('pdf-is-editing');}
    edit.onclick=()=>{editing=!editing;edit.textContent=editing?'Concluir edição':'Editar texto';edit.setAttribute('aria-pressed',String(editing));body.classList.toggle('pdf-is-editing',editing);for(const field of fields)field.setAttribute('contenteditable',String(editing));};
    for(const field of fields)field.addEventListener('paste',event=>{event.preventDefault();document.execCommand('insertText',false,event.clipboardData.getData('text/plain'));});
    for(const row of body.querySelectorAll('.pdf-ex-row')){
      const section=row.closest('.pdf-sec'),heading=section.querySelector('.pdf-sec-title');let group=groups.get(section);if(!group){const panel=node('details',{class:'pdf-video-section'}),title=node('summary',{},heading.textContent),list=node('div');panel.append(title,list);rows.append(panel);group={panel,list,count:0};groups.set(section,group);heading.addEventListener('input',()=>{title.textContent=heading.textContent;});}const number=++group.count;
      const title=row.querySelector('.pdf-ex-title'),link=row.querySelector('.yt-link'),original=title.textContent,label=node('label'),name=node('span',{},original),input=node('input',{type:'url',placeholder:'Automático · cole um link para trocar','aria-label':'Vídeo de '+original}),search=node('a',{target:'_blank',rel:'noopener'},'Buscar vídeo'),reset=node('button',{type:'button'},'Automático'),paste=node('button',{type:'button'},'Colar link'),item=node('div',{class:'pdf-video-choice'});label.append(name,input);item.append(label,paste,search,reset);group.list.append(item);
      input.value=row.dataset.videoUrl||'';
      const entry={input,link,title,row,custom:'',valid:true};entries.push(entry);
      function update(){const exercise=title.textContent.trim()||original;name.textContent=number+'. '+exercise;search.href='https://www.youtube.com/results?search_query='+encodeURIComponent(exercise+' academia como fazer');try{entry.custom=videoURL(input.value);entry.valid=true;input.setCustomValidity('');const tracked=makeURL(exercise,entry.custom,row.dataset.sectionTitle);link.href=tracking.value==='direct'?directVideoURL(tracked):tracked;status.textContent='';}catch(error){entry.valid=false;input.setCustomValidity(error.message);status.textContent=error.message+' Corrija o campo ou toque em Automático.';}}
      function remember(){update();if(!entry.valid)return;if(onVideoChange)onVideoChange(row,entry.custom);}
      paste.onclick=async()=>{try{input.value=await navigator.clipboard.readText();input.dispatchEvent(new Event('input',{bubbles:true}));}catch(error){videos.open=true;group.panel.open=true;input.focus();status.textContent='Toque e segure no campo para colar o link; o navegador não liberou a colagem rápida.';}};
      entry.update=update;input.oninput=remember;reset.onclick=()=>{input.value='';input.dispatchEvent(new Event('input',{bubbles:true}));};title.addEventListener('input',update);update();
    }
    if(window.GymFasterLibrary){
      for(const entry of entries){
        if(!samples){GymFasterLibrary.addChoice({item:entry.input.closest('.pdf-video-choice'),input:entry.input,title:entry.title});continue;}
        const area=node('div',{class:'pdf-gif-controls'}),choose=node('button',{type:'button',class:'pdf-gif-choice'},'GIFs'),count=node('small',{class:'pdf-gif-count'}),previews=node('div',{class:'pdf-gif-previews'});area.append(choose,count,previews);entry.input.closest('.pdf-video-choice').append(area);
        function refresh(){const urls=samples.read(entry.row),names=WorkoutVideoMatch.parts(entry.title.textContent);count.textContent=urls.filter(Boolean).length+'/'+names.length+' GIFs associados';previews.replaceChildren();urls.forEach((url,index)=>{if(!url)return;const name=names[index]||'Demonstração '+(index+1),view=node('button',{type:'button','aria-label':'Ver GIF de '+name},(names.length>1?name+' ':'')+'(GIFs)');view.onclick=()=>GymFasterWorkout.pick({name,video:url,previewOnly:true});previews.append(view);});}
        choose.onclick=()=>samples.choose(entry.row,entry.title.textContent,refresh);entry.title.addEventListener('input',refresh);refresh();
      }
      const prepare=node("button",{type:"button",class:"gym-prepare-a"},"Preparar treino A · GymFaster");prepare.onclick=()=>GymFasterLibrary.prepareA();tools.prepend(prepare);
    }
    applyModel();applyLinkOptions();
    current={finish,refreshMedia:applyModel,validate(){if(!sectionInputs.some(input=>input.checked)){status.textContent='Selecione pelo menos uma seção para gerar o PDF.';sectionBox.scrollIntoView({block:'nearest'});return false;}const invalid=includeVideos.checked&&entries.find(entry=>!entry.valid&&!entry.row.closest('.pdf-sec').hidden);if(invalid){videos.open=true;invalid.input.closest('.pdf-video-section').open=true;invalid.input.reportValidity();invalid.input.focus();return false;}finish();return true;}};
  }
  return {mount,videoURL,directVideoURL,refreshMedia:()=>current?.refreshMedia(),beforeExport:()=>!current||current.validate()};
})();

window.WhatsAppCopy=(()=>{
  function localNumber(value){let digits=String(value||'').replace(/\D/g,'');if(/^0055\d{10,11}$/.test(digits))return digits.slice(4);if(/^55\d{10,11}$/.test(digits))return digits.slice(2);return digits;}
  async function copy(value,host=document.body){const text=localNumber(value);if(!text)throw Error('Informe o WhatsApp primeiro.');try{await navigator.clipboard.writeText(text);}catch(error){const area=document.createElement('textarea');area.value=text;area.setAttribute('readonly','');area.style.cssText='position:fixed;left:0;top:0;opacity:0';host.append(area);area.select();const copied=document.execCommand('copy');area.remove();if(!copied)throw Error('Não foi possível copiar o número.');}return text;}
  return {localNumber,copy};
})();
