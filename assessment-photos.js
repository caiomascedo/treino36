/* Additional dated assessment photos and a local before/after image composer. */
window.AssessmentPhotos=(()=>{
  const el=(tag,attrs={},text)=>{const node=document.createElement(tag);for(const [key,value] of Object.entries(attrs))node.setAttribute(key,value);if(text!==undefined)node.textContent=text;return node;};
  const photoList=av=>Array.isArray(av?.fotosExtras)?av.fotosExtras.filter(p=>p&&typeof p.id==='string'&&typeof p.src==='string'):[];
  const id=()=>typeof crypto.randomUUID==='function'?crypto.randomUUID():'photo-'+Date.now()+'-'+Math.random().toString(36).slice(2);
  const filename=value=>String(value||'Foto').replace(/[^\p{L}\p{N}_-]+/gu,'_');
  function download(src,name){const link=el('a',{href:src,download:name});document.body.append(link);link.click();link.remove();}
  function catalog(person){
    const result=[];
    for(const av of person.avaliacoes||[]){
      for(const photo of photoList(av))result.push({value:String(av.id)+':extra:'+photo.id,label:photo.label||'Foto livre',src:photo.src,date:av.data||'',weight:av.peso||'',avId:av.id});
      for(const [key,label] of [['fotoF','Frontal'],['fotoL','Lateral'],['fotoD','Dorsal']])if(av[key])result.push({value:String(av.id)+':'+key,label,src:av[key],date:av.data||'',weight:av.peso||'',avId:av.id});
    }
    const date=value=>{const m=String(value).match(/^(\d{2})\/(\d{2})\/(\d{4})$/);return m?Date.UTC(+m[3],+m[2]-1,+m[1]):Number.MAX_SAFE_INTEGER;};
    return result.sort((a,b)=>date(a.date)-date(b.date));
  }
  async function load(src){const image=new Image();image.crossOrigin='anonymous';image.src=src;await image.decode();return image;}
  function round(ctx,x,y,w,h,r){ctx.beginPath();ctx.roundRect(x,y,w,h,r);}
  async function poster(before,after,settings){
    const [a,b]=await Promise.all([load(before.src),load(after.src)]);let logo=null;
    if(settings.logo){let src='assets/caio-macedo-logo.png';try{const stored=localStorage.getItem('treinoPostureLogo');if(/^data:image\/png;base64,/i.test(stored||''))src=stored;}catch(error){}logo=await load(src);}
    const canvas=document.createElement('canvas');canvas.width=1080;canvas.height=1350;const ctx=canvas.getContext('2d');
    const background=ctx.createLinearGradient(0,0,1080,1350);background.addColorStop(0,'#080b0a');background.addColorStop(.6,'#101c14');background.addColorStop(1,'#073a23');ctx.fillStyle=background;ctx.fillRect(0,0,1080,1350);
    ctx.save();ctx.strokeStyle='rgba(255,255,255,.035)';ctx.lineWidth=35;for(let x=-1200;x<1600;x+=210){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x+1000,1350);ctx.stroke();}ctx.restore();
    const cards=[{item:before,image:a,x:44,title:'ANTES',weight:settings.beforeWeight},{item:after,image:b,x:554,title:'DEPOIS',weight:settings.afterWeight}],w=482,h=900,y=214;
    for(const card of cards){
      ctx.fillStyle='white';ctx.font='italic 900 74px Arial';ctx.textAlign='center';ctx.fillText(card.title,card.x+w/2,145);
      if(settings.dates&&card.item.date){ctx.font='23px Arial';ctx.fillStyle='#b9dac9';ctx.fillText(card.item.date,card.x+w/2,187);}
      ctx.save();round(ctx,card.x,y,w,h,23);ctx.clip();ctx.fillStyle='#16221b';ctx.fillRect(card.x,y,w,h);
      const scale=(settings.fit==='cover'?Math.max:Math.min)(w/card.image.naturalWidth,h/card.image.naturalHeight),iw=card.image.naturalWidth*scale,ih=card.image.naturalHeight*scale;
      ctx.drawImage(card.image,card.x+(w-iw)/2,y+(h-ih)/2,iw,ih);
      if(settings.weights&&card.weight.trim()){const text=card.weight.trim().replace(/\s*kg$/i,'')+' kg';let size=70;ctx.font='italic 900 '+size+'px Arial';while(ctx.measureText(text).width>w-36&&size>24){size-=2;ctx.font='italic 900 '+size+'px Arial';}ctx.shadowColor='rgba(0,0,0,.8)';ctx.shadowBlur=10;ctx.fillStyle='white';ctx.fillText(text,card.x+w/2,y+h-55);}
      ctx.restore();
    }
    if(logo){const scale=Math.min(640/logo.naturalWidth,145/logo.naturalHeight),lw=logo.naturalWidth*scale,lh=logo.naturalHeight*scale;ctx.drawImage(logo,(1080-lw)/2,1170+(145-lh)/2,lw,lh);}
    return canvas;
  }
  let composer;
  function comparison(){
    if(composer)return composer;
    const dialog=el('dialog',{id:'assessmentComparisonDialog',class:'assessment-comparison','aria-labelledby':'assessmentComparisonTitle'});
    dialog.innerHTML='<header><strong id="assessmentComparisonTitle">Antes e Depois</strong><button type="button" data-close>Fechar</button></header><div class="comparison-picks"></div><div class="comparison-options"><label><input type="checkbox" id="comparisonWeights" checked> Mostrar pesos</label><label><input type="checkbox" id="comparisonDates"> Mostrar datas</label><label><input type="checkbox" id="comparisonLogo" checked> Minha logo</label><label>Enquadramento <select id="comparisonFit"><option value="contain">Foto inteira</option><option value="cover">Preencher quadro</option></select></label></div><button type="button" id="comparisonGenerate">Gerar prévia</button><p id="comparisonStatus" role="status"></p><img id="comparisonPreview" alt="Imagem de antes e depois" hidden><div class="comparison-actions"><button type="button" id="comparisonDownload" disabled>Salvar imagem</button><button type="button" id="comparisonKeep" disabled>Guardar na avaliação</button></div>';
    document.body.append(dialog);const q=selector=>dialog.querySelector(selector);let config=null,items=[],token=0,ready=null;
    function release(){if(ready)URL.revokeObjectURL(ready.url);ready=null;q('#comparisonPreview').hidden=true;q('#comparisonPreview').removeAttribute('src');q('#comparisonDownload').disabled=q('#comparisonKeep').disabled=true;}
    const picked=side=>items.find(item=>item.value===q('#comparison'+side).value);
    function settings(){return {before:q('#comparisonBefore').value,after:q('#comparisonAfter').value,beforeWeight:q('#comparisonBeforeWeight').value,afterWeight:q('#comparisonAfterWeight').value,weights:q('#comparisonWeights').checked,dates:q('#comparisonDates').checked,logo:q('#comparisonLogo').checked,fit:q('#comparisonFit').value};}
    function invalidate(){token++;release();q('#comparisonGenerate').disabled=items.length<2;q('#comparisonStatus').textContent=items.length<2?'Adicione pelo menos duas fotos para montar o antes e depois.':'Escolha as fotos e toque em Gerar prévia.';}
    q('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('close',()=>{if(dialog.open)return;token++;release();config=null;});
    q('#comparisonGenerate').onclick=async()=>{
      const before=picked('Before'),after=picked('After');if(!before||!after||before.value===after.value){q('#comparisonStatus').textContent='Escolha duas fotos diferentes.';return;}
      release();const version=++token,options=settings(),session=config;q('#comparisonGenerate').disabled=true;q('#comparisonStatus').textContent='Gerando imagem…';
      try{const canvas=await poster(before,after,options),blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));if(version!==token||!dialog.open)return;if(!blob)throw Error('Não foi possível gerar a imagem.');let note='';try{session.saveSettings(options);}catch(error){note=' Não foi possível guardar as opções, mas você pode salvar a imagem.';}if(version!==token||!dialog.open)return;
        ready={blob,url:URL.createObjectURL(blob),name:'Antes_Depois_'+filename(session.name)+'.png'};q('#comparisonPreview').src=ready.url;q('#comparisonPreview').hidden=false;q('#comparisonDownload').disabled=q('#comparisonKeep').disabled=false;q('#comparisonStatus').textContent='Prévia pronta. Toque na imagem para ampliar.'+note;
      }catch(error){if(version===token)q('#comparisonStatus').textContent=error.message||'Não foi possível gerar a imagem.';}finally{if(version===token)q('#comparisonGenerate').disabled=false;}
    };
    q('#comparisonPreview').onclick=()=>{if(ready)config.editor.preview(ready.url,'Antes e Depois');};
    q('#comparisonDownload').onclick=()=>{if(ready)download(ready.url,ready.name);};
    q('#comparisonKeep').onclick=async()=>{if(!ready)return;const version=token,session=config,item=ready;q('#comparisonKeep').disabled=true;
      try{const src=await session.compress(new File([item.blob],item.name,{type:'image/png'}));if(version!==token||!dialog.open)return;session.keep(src);q('#comparisonStatus').textContent='Imagem guardada nas outras fotos desta avaliação.';}
      catch(error){if(version===token){q('#comparisonStatus').textContent=error.message||'Não foi possível guardar a imagem.';q('#comparisonKeep').disabled=false;}}
    };
    composer={open(options){config=options;items=catalog(options.person);release();const initial=options.saved||{},picks=q('.comparison-picks');picks.replaceChildren();
      for(const [side,title] of [['Before','Antes'],['After','Depois']]){const box=el('div',{class:'comparison-pick'}),select=el('select',{id:'comparison'+side,'aria-label':'Foto '+title}),image=el('img',{alt:'Foto '+title}),weight=el('input',{id:'comparison'+side+'Weight',type:'text',inputmode:'decimal','aria-label':'Peso '+title,placeholder:'Peso opcional (kg)'});box.append(el('label',{for:select.id},title),select,image,weight);picks.append(box);
        items.forEach(item=>select.append(el('option',{value:item.value},(item.date||'Sem data')+' · '+item.label)));
        const fallback=side==='Before'?items[0]:items.find(item=>String(item.avId)===String(options.avId)&&item.value!==q('#comparisonBefore').value)||items.at(-1),saved=side==='Before'?initial.before:initial.after;select.value=items.some(item=>item.value===saved)?saved:fallback?.value||'';
        const sync=()=>{const item=picked(side);image.hidden=!item;if(item)image.src=item.src;weight.value=item?.weight||'';};sync();if(saved===select.value)weight.value=(side==='Before'?initial.beforeWeight:initial.afterWeight)??weight.value;
        select.onchange=()=>{sync();invalidate();};weight.oninput=invalidate;
      }
      q('#comparisonWeights').checked=initial.weights!==false;q('#comparisonDates').checked=initial.dates===true;q('#comparisonLogo').checked=initial.logo!==false;q('#comparisonFit').value=initial.fit==='cover'?'cover':'contain';
      q('.comparison-options').onchange=invalidate;dialog.showModal();invalidate();
    }};return composer;
  }
  function mount(root,config){
    const panel=el('details',{class:'assessment-extra-photos',id:'obsExtraPhotos'}),summary=el('summary',{},'＋ Outras fotos e antes/depois');panel.append(summary);
    const toolbar=el('div',{class:'extra-photo-toolbar'}),upload=el('button',{type:'button',id:'extraPhotoAdd'},'Adicionar fotos'),camera=el('button',{type:'button',id:'extraPhotoCamera'},'Câmera'),compare=el('button',{type:'button',id:'extraPhotoCompare'},'Antes e Depois'),input=el('input',{id:'extraPhotoFiles',type:'file',accept:'image/*',multiple:'',hidden:''}),list=el('div',{class:'extra-photo-grid'}),status=el('p',{role:'status',class:'extra-photo-status'});
    toolbar.append(upload,camera,compare);panel.append(toolbar,input,el('p',{class:'extra-photo-hint'},'Fotos de espelho ou outros ângulos. Use o mesmo nome em outra avaliação para comparar no PDF.'),list,status);root.append(panel);
    const target=config.target,initial=config.getState(target);let adding=false;
    const persist=transform=>config.mutate(target,transform);
    function add(src,label){const photo={id:id(),label:label||'Foto '+(photoList(config.getState(target).av).length+1),src,createdAt:new Date().toISOString()};persist(photos=>[...photos,photo]);render();return photo;}
    function change(photo,patch){persist(photos=>{const old=photos.find(item=>item.id===photo.id);if(!old)throw Error('Esta foto não está mais disponível.');if(old.src!==photo.src)throw Error('A foto mudou em outra janela. Abra novamente.');return photos.map(item=>item.id===photo.id?{...item,...patch,updatedAt:new Date().toISOString()}:item);});render();}
    function remove(photo){persist(photos=>{const old=photos.find(item=>item.id===photo.id);if(!old||old.src!==photo.src)throw Error('A foto mudou. Abra novamente antes de apagar.');return photos.filter(item=>item.id!==photo.id);});render();}
    function edit(photo,options={}){config.editor.open({title:(photo?.label||'Nova foto')+' · '+initial.person.nome,source:photo?.original||photo?.src,settings:photo?.settings,compress:config.compress,remove:photo?()=>remove(photo):null,...options,save:result=>{if(photo)change(photo,{src:result.photo,original:result.original,settings:result.settings});else{const added={id:id(),label:'Foto '+(photoList(config.getState(target).av).length+1),src:result.photo,original:result.original,settings:result.settings,createdAt:new Date().toISOString()};persist(photos=>[...photos,added]);render();}}});}
    function render(){if(!root.isConnected)return;list.replaceChildren();for(const photo of photoList(config.getState(target).av)){
      const box=el('div',{class:'obs-assessment-photo extra-photo-card','data-extra-photo-id':photo.id}),name=el('input',{type:'text','aria-label':'Nome da foto',maxlength:'80'}),image=el('img',{alt:photo.label||'Foto livre',loading:'lazy',tabindex:'0',role:'button','aria-label':'Ampliar '+(photo.label||'foto livre')});name.value=photo.label||'';name.onchange=()=>{try{change(photo,{label:name.value.trim()||'Foto'});}catch(error){status.textContent=error.message;name.value=photo.label||'';}};image.src=photo.src;image.onclick=()=>config.editor.preview(photo.src,photo.label||'Foto livre');image.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();image.click();}};
      const actions=el('div',{class:'posture-photo-actions'});for(const [label,action] of [['Câmera',()=>edit(photo,{camera:true})],['Editar',()=>edit(photo)],['Apagar',()=>{if(confirm('Apagar esta foto livre e suas marcações?'))try{remove(photo);}catch(error){status.textContent=error.message;}}],['Salvar',()=>download(photo.src,filename(initial.person.nome+'_'+(photo.label||'Foto')+'_'+config.getState(target).av.data)+'.'+(photo.src.startsWith('data:image/png')?'png':'jpg'))]]){const button=el('button',{type:'button',class:'info-tool-btn'},label);if(label==='Salvar')button.dataset.postureDownload=photo.id;button.onclick=action;actions.append(button);}box.append(name,image,actions);list.append(box);
    }status.textContent=photoList(config.getState(target).av).length?'':'Nenhuma foto livre adicionada nesta avaliação.';}
    upload.onclick=()=>input.click();input.onchange=async()=>{const files=[...input.files];input.value='';if(!files.length||adding)return;adding=true;upload.disabled=camera.disabled=compare.disabled=true;status.textContent='Abrindo fotos…';const added=[];let failed=0;
      try{for(const file of files){try{const src=await config.compress(file);added.push({id:id(),label:'Foto '+(photoList(config.getState(target).av).length+added.length+1),src,createdAt:new Date().toISOString()});}catch(error){failed++;}}if(added.length){persist(photos=>[...photos,...added]);render();}status.textContent=added.length+' foto(s) adicionada(s).'+(failed?' '+failed+' arquivo(s) não puderam ser abertos.':'');}
      catch(error){status.textContent=error.message||'Não foi possível guardar as fotos. As fotos anteriores foram mantidas.';}finally{adding=false;upload.disabled=camera.disabled=compare.disabled=false;}
    };
    camera.onclick=()=>edit(null,{camera:true});compare.onclick=()=>{const state=config.getState(target);comparison().open({person:state.person,avId:state.av.id,name:state.person.nome,saved:state.av.comparativoFoto,editor:config.editor,compress:config.compress,saveSettings:settings=>config.saveSettings(target,settings),keep:src=>add(src,'Comparativo antes e depois')});};
    render();return {panel,refresh:render};
  }
  return {mount,catalog,photoList};
})();
