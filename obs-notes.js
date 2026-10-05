window.ObsNotes = (() => {
  function clean(html){const source=document.createElement('div');source.innerHTML=html||'';const out=document.createElement('div');function walk(node,parent){if(node.nodeType===3){parent.append(document.createTextNode(node.textContent));return;}if(node.nodeType!==1)return;if(['SCRIPT','STYLE','IFRAME','OBJECT'].includes(node.tagName))return;const tag=['H1','H2','H3','H4','H5','H6'].includes(node.tagName)?'DIV':node.tagName==='SPAN'&&(/bold|[7-9]00/.test(node.style.fontWeight))?'STRONG':node.tagName;const allowed=['B','STRONG','BR','DIV','P','UL','OL','LI'].includes(tag),dest=allowed?document.createElement(tag.toLowerCase()):parent;if(allowed)parent.append(dest);for(const child of node.childNodes)walk(child,dest);}for(const child of source.childNodes)walk(child,out);return out.innerHTML;}
  function mount(config){
    const dialog=config.dialog,area=document.getElementById('obsTextarea'),container=document.getElementById('obsContent');
    const extras=document.createElement('section');extras.className='obs-exam';extras.innerHTML='<p id="obsSavedDate" class="obs-note-date"></p><button type="button" id="obsExamToggle" class="toggle-info-btn" aria-expanded="false" aria-controls="obsExamBody"><span><span id="obsExamArrow" class="info-arrow">▶</span> Exame do aluno <span id="obsExamBadge" class="obs-exam-badge" hidden aria-label="Exame preenchido"></span></span><span id="obsExamToggleAction" class="panel-toggle-action">Abrir</span></button><div id="obsExamBody" hidden><label for="obsExamFile">Adicionar fotos do exame</label><input id="obsExamFile" type="file" accept="image/*" multiple><div id="obsExamGallery" class="obs-exam-gallery"></div><label for="obsExamResult">Resultado do exame</label><div id="obsExamResult" class="obs-rich-text" contenteditable="true" role="textbox" aria-multiline="true" aria-label="Resultado do exame"></div></div><p id="obsNotesStatus" role="status"></p>';
    container.append(extras);
    const toolbar=document.createElement('div');toolbar.className='obs-notes-toolbar';toolbar.setAttribute('aria-label','Editar observações');toolbar.innerHTML='<button type="button" id="obsBoldBtn" title="Negrito"><b>B</b> (Negrito)</button><button type="button" id="obsUndoBtn" aria-label="Desfazer observação">↶</button><button type="button" id="obsRedoBtn" aria-label="Refazer observação">↷</button><button type="button" id="obsCopyPrescriptionBtn">📋 Copiar prescrição para OBS</button>';
    container.prepend(toolbar);
    const examHeader=document.createElement('div');examHeader.className='obs-exam-header';
    const examHeading=document.getElementById('obsExamToggle'),copyPrescription=document.getElementById('obsCopyPrescriptionBtn');
    examHeading.before(examHeader);examHeader.append(examHeading);document.getElementById('obsExamBody').prepend(copyPrescription);
    copyPrescription.textContent='📋 Copiar prescrição';copyPrescription.title='Copiar prescrição para OBS';copyPrescription.setAttribute('aria-label','Copiar prescrição para OBS');
    const result=document.getElementById('obsExamResult'),status=document.getElementById('obsNotesStatus'),date=document.getElementById('obsSavedDate'),file=document.getElementById('obsExamFile');
    area.before(date);
    const examBody=document.getElementById('obsExamBody'),examToggle=document.getElementById('obsExamToggle'),badge=document.getElementById('obsExamBadge');
    let displayedGuide=null;
    function examIndicator(){const g=config.guide()||{};badge.hidden=!(photosFor(g).length||String(g.exameResultado||'').trim());}
    function setExamExpanded(expanded){examBody.hidden=!expanded;examToggle.setAttribute('aria-expanded',String(expanded));document.getElementById('obsExamArrow').textContent=expanded?'▼':'▶';document.getElementById('obsExamToggleAction').textContent=expanded?'Minimizar':'Abrir';}
    examToggle.onclick=()=>{if(!examBody.hidden)capture();setExamExpanded(examBody.hidden);};
    dialog.addEventListener('close',()=>setExamExpanded(false));
    const histories=new WeakMap();let editing=area,range=null,pending=0;
    function text(editor){return editor.innerText.replace(/\r/g,'');}
    function capture(){const g=config.guide();if(!g)return;g.texto=text(area);g.textoHtml=clean(area.innerHTML);if(!examBody.hidden){g.exameResultado=text(result);g.exameResultadoHtml=clean(result.innerHTML);}examIndicator();}
    Object.defineProperty(area,'value',{get(){return text(area);},set(value){const g=config.guide();area.innerHTML=g&&g.texto===value&&g.textoHtml?clean(g.textoHtml):'';if(!area.innerHTML)area.textContent=value||'';}});
    function snapshot(){return [area.innerHTML,result.innerHTML];}
    function history(){const g=config.guide();if(!g)return null;let h=histories.get(g);if(!h){h={items:[snapshot()],at:0};histories.set(g,h);}return h;}
    function record(){const h=history();if(!h)return;const s=snapshot();if(JSON.stringify(h.items[h.at])!==JSON.stringify(s)){h.items.splice(h.at+1);h.items.push(s);if(h.items.length>80)h.items.shift();h.at=h.items.length-1;}capture();buttons();}
    function buttons(){const h=history();document.getElementById('obsUndoBtn').disabled=!h||h.at===0;document.getElementById('obsRedoBtn').disabled=!h||h.at===h.items.length-1;}
    function refresh(){const g=config.guide()||{};if(displayedGuide!==g){setExamExpanded(false);displayedGuide=g;}examIndicator();area.value=g.texto||'';result.innerHTML=clean(g.exameResultadoHtml||'');if(!result.innerHTML)result.textContent=g.exameResultado||'';date.textContent=g.obsSalvaEm?'OBS salva em '+new Date(g.obsSalvaEm).toLocaleString('pt-BR'):'';renderPhotos();file.value='';range=null;editing=area;buttons();}
    [area,result].forEach(editor=>{editor.addEventListener('focus',()=>{editing=editor;history();});editor.addEventListener('input',record);editor.addEventListener('paste',event=>{event.preventDefault();const html=event.clipboardData.getData('text/html'),plain=event.clipboardData.getData('text/plain');if(html)document.execCommand('insertHTML',false,clean(html));else if(/\*\*[^*]+\*\*/.test(plain)){const escaped=document.createElement('div');escaped.textContent=plain;document.execCommand('insertHTML',false,escaped.innerHTML.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\n/g,'<br>'));}else document.execCommand('insertText',false,plain);record();});editor.addEventListener('keydown',event=>{if(!(event.ctrlKey||event.metaKey))return;const key=event.key.toLowerCase();if(key==='b'){event.preventDefault();bold();}if(key==='z'||key==='y'){event.preventDefault();move(key==='y'||event.shiftKey?1:-1);}});});
    document.addEventListener('selectionchange',()=>{if(!dialog.open)return;const sel=getSelection();if(!sel.rangeCount)return;const r=sel.getRangeAt(0);if(editing.contains(r.commonAncestorContainer))range=r.cloneRange();});
    function restore(){editing.focus({preventScroll:true});if(range&&editing.contains(range.commonAncestorContainer)){const sel=getSelection();sel.removeAllRanges();sel.addRange(range);}}
    function bold(){restore();document.execCommand('bold',false,null);record();}
    function move(step){const h=history();if(!h||!h.items[h.at+step])return;h.at+=step;if(result.innerHTML!==h.items[h.at][1])setExamExpanded(true);[area.innerHTML,result.innerHTML]=h.items[h.at];range=null;capture();buttons();editing.focus({preventScroll:true});}
    [['obsBoldBtn',bold],['obsUndoBtn',()=>move(-1)],['obsRedoBtn',()=>move(1)]].forEach(([id,fn])=>{const b=document.getElementById(id);b.addEventListener('pointerdown',e=>e.preventDefault());b.onclick=fn;});
    document.getElementById('obsCopyPrescriptionBtn').onclick=()=>{history();const prescription=config.prescription();if(!prescription){status.textContent='Não há prescrição neste treino.';return;}const separator=document.createTextNode(text(area).trim()?'\n\n':'');area.append(separator,document.createTextNode(prescription));editing=area;record();status.textContent='Prescrição adicionada à OBS. Toque em Salvar somente OBS para guardar.';};
    const gallery=document.getElementById('obsExamGallery');
    const viewer=document.createElement('dialog');viewer.className='app-dialog obs-exam-viewer';viewer.innerHTML='<button type="button">Fechar foto</button><img alt="Exame ampliado">';document.body.append(viewer);viewer.querySelector('button').onclick=()=>viewer.close();
    function photosFor(g){return Array.isArray(g.exameFotos)?g.exameFotos.filter(p=>p&&p.src):g.exameFoto?[{id:'legacy',src:g.exameFoto,name:'exame.jpg'}]:[];}
    function storePhotos(g,photos){g.exameFotos=photos;delete g.exameFoto;}
    function photoFile(photo,index){const parts=photo.src.split(','),bytes=atob(parts[1]),buffer=new Uint8Array(bytes.length);for(let i=0;i<bytes.length;i++)buffer[i]=bytes.charCodeAt(i);const mime=(parts[0].match(/data:([^;]+)/)||[])[1]||'image/jpeg';return new File([buffer],'exame-'+(index+1)+(mime==='image/png'?'.png':'.jpg'),{type:mime});}
    async function savePhoto(photo,index){
      try{const imageFile=photoFile(photo,index);
        if(navigator.canShare&&navigator.canShare({files:[imageFile]})&&navigator.share){try{await navigator.share({files:[imageFile],title:'Foto do exame'});return;}catch(error){if(error.name==='AbortError')return;}}
        const url=URL.createObjectURL(imageFile),link=document.createElement('a');link.href=url;link.download=imageFile.name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
        status.textContent='Foto enviada para salvar no dispositivo.';
      }catch(error){status.textContent='Não foi possível salvar a foto: '+error.message;}
    }
    function renderPhotos(){
      gallery.replaceChildren();const g=config.guide();if(!g)return;
      photosFor(g).forEach((photo,index)=>{
        const card=document.createElement('div');card.className='obs-exam-photo';
        const open=document.createElement('button');open.type='button';open.className='obs-exam-photo-view';open.setAttribute('aria-label','Ampliar foto '+(index+1)+' do exame');
        const image=document.createElement('img');image.src=photo.src;image.alt='Foto '+(index+1)+' do exame';image.loading='lazy';image.decoding='async';open.append(image);open.onclick=()=>{viewer.querySelector('img').src=photo.src;viewer.showModal();};
        const actions=document.createElement('div');actions.className='obs-exam-photo-actions';
        const save=document.createElement('button');save.type='button';save.className='obs-exam-photo-save';save.textContent='Salvar foto';save.onclick=()=>savePhoto(photo,index);
        const remove=document.createElement('button');remove.type='button';remove.className='obs-exam-photo-delete';remove.textContent='Apagar foto';remove.onclick=()=>{if(config.guide()!==g)return;storePhotos(g,photosFor(g).filter(item=>item.id!==photo.id));renderPhotos();examIndicator();status.textContent='Foto removida. Salve a OBS para guardar.';};
        actions.append(save,remove);card.append(open,actions);gallery.append(card);
      });
    }
    async function compressPhoto(selected){
      if(!selected.type.startsWith('image/'))throw Error('Escolha uma imagem do exame.');
      const bitmap=await createImageBitmap(selected,{imageOrientation:'from-image'}),scale=Math.min(1,1400/Math.max(bitmap.width,bitmap.height)),canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(bitmap.width*scale));canvas.height=Math.max(1,Math.round(bitmap.height*scale));const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close();
      const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',0.72));if(!blob)throw Error('Imagem inválida.');
      const src=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(blob);});
      return {id:crypto.randomUUID?crypto.randomUUID():Date.now()+'-'+Math.random(),src,name:selected.name};
    }
    file.onchange=async()=>{
      const selected=[...file.files],g=config.guide();if(!selected.length||!g)return;pending++;file.disabled=true;let added=0;
      try{for(const image of selected){if(config.guide()===g)status.textContent='Preparando foto '+(added+1)+' de '+selected.length+'…';const photo=await compressPhoto(image);storePhotos(g,[...photosFor(g),photo]);added++;if(config.guide()===g){renderPhotos();examIndicator();}}
        if(config.guide()===g)status.textContent=added+' foto(s) adicionada(s). Salve a OBS para guardar.';
      }catch(error){status.textContent='Não foi possível carregar todas as fotos: '+error.message;}
      finally{pending--;file.disabled=false;file.value='';}
    };
    const save=document.createElement('button');save.type='button';save.id='saveOnlyObsBtn';save.className='primary';save.textContent='Salvar OBS';save.title='Salvar somente OBS';save.setAttribute('aria-label','Salvar somente OBS');document.getElementById('saveObsBtn').before(save);save.onclick=()=>{if(pending){status.textContent='Aguarde a foto terminar de carregar.';return;}capture();config.save();};
    return {refresh,capture,pending:()=>pending,clean};
  }
  return {mount,clean};
})();
