window.GymFasterWorkout = (() => {
  'use strict';
  const WIDTH=800,CARD=270,HEADER=175,FRAMES=100,SLOT_W=350,SLOT_H=242;
  const themes={cm:{name:'CM',bg:'#050906',card:'#0a110d',ink:'#f3faf5',green:'#3aeb91'},gymfaster:{name:'GymFaster',bg:'#eff5f1',card:'#fff',ink:'#1b3428',green:'#176b43'}};
  let integration,dialog,controls,videos=[],catalogPromise,workout,selected,cards=[],mode='gymfaster',file,blobURL,observer,job=null,sequence=0,layoutHeader=HEADER,layoutBlocks=[],focusReturn,libraryDirty=false;
  let batchState=null,files=[],resultURLs=[];
  const workingCards=()=>batchState?.cards||cards;
  let presentation={style:'detailed',colors:false};try{presentation={...presentation,...JSON.parse(localStorage.getItem('treinoGifPresentationV1')||'{}')};}catch(e){}
  const colors=['#b91c1c','#15803d','#ca8a04','#111111','#1d4ed8','#9333ea','#c2410c','#0f766e','#be185d','#4338ca'];
  const colorFor=index=>colors[index]||'hsl('+Math.round(index*137.5%360)+' 70% 32%)';
  const match=()=>window.WorkoutVideoMatch;
  const library=()=>window.WorkoutVideoLibrary;
  const availableVideos=()=>library().apply(videos);
  const node=(tag,attrs={},text)=>{const item=document.createElement(tag);Object.entries(attrs).forEach(([key,value])=>item.setAttribute(key,value));if(text!==undefined)item.textContent=text;return item;};
  const prefKey='treinoGifChoicesV1';
  function preferences(){try{return JSON.parse(localStorage.getItem(prefKey)||'{}')||{};}catch(error){return {};}}
  function choiceKey(name){return mode+':'+match().canonical(name);}
  function remember(name,asset){try{const prefs=preferences();prefs[choiceKey(name)]=asset.id;localStorage.setItem(prefKey,JSON.stringify(prefs));}catch(error){}}
  function configure(options){integration=options;}
  function clearResult(){files=[];resultURLs.forEach(url=>URL.revokeObjectURL(url));resultURLs=[];file=null;if(blobURL)URL.revokeObjectURL(blobURL);blobURL=null;controls.result.replaceChildren();controls.result.hidden=true;controls.share.hidden=true;controls.download.hidden=true;controls.share.textContent='Compartilhar GIF';controls.download.textContent='Baixar GIF';}
  function cancel(){if(batchState)batchState.cancelled=true;if(!job)return;job.cancelled=true;job.abort.abort();job.worker?.terminate();if(job.decoder){job.decoder.pause();job.decoder.removeAttribute('src');job.decoder.load();}}
  function disposeCards(){observer?.disconnect();workingCards().forEach(card=>{card.video.pause();card.video.removeAttribute('src');card.video.load();if(card.localURL)URL.revokeObjectURL(card.localURL);});cards=[];}
  function create(){
    dialog=node('dialog',{id:'workoutGifDialog','aria-labelledby':'workoutGifTitle'});
    const heading=node('h3',{id:'workoutGifTitle'}),help=node('p',{},'Monte a ficha com movimentos do corpo inteiro. O GIF repete por 5 segundos e pode ser baixado ou compartilhado.'),student=node('strong',{class:'gif-student'});
    const library=node('select',{'aria-label':'Biblioteca dos GIFs'});library.append(node('option',{value:'cm'},'CM · fundo preto, traços claros'),node('option',{value:'gymfaster'},'GymFaster · modelo anatômico'));
    const section=node('select',{'aria-label':'Treino para o GIF'}),status=node('p',{role:'status','aria-live':'polite'}),list=node('div',{class:'gif-cards'}),result=node('div',{class:'gif-result',hidden:''});
    const accept=node('button',{type:'button',class:'gif-accept-suggestions',hidden:''},'Usar sugestões mostradas');
    const actions=node('div',{class:'gif-actions'}),generate=node('button',{type:'button',class:'gif-primary'}),share=node('button',{type:'button',hidden:''},'Compartilhar GIF'),download=node('button',{type:'button',hidden:''},'Baixar GIF'),stop=node('button',{type:'button',hidden:''},'Cancelar geração'),close=node('button',{type:'button'},'Fechar');
    const presentationBox=node('div',{class:'gif-presentation'}),style=node('select',{'aria-label':'Prescrição dos conjugados'}),colorLabel=node('label'),colorCheck=node('input',{type:'checkbox','aria-label':'Cores nos conjugados'});style.append(node('option',{value:'detailed'},'Prescrição em cada exercício'),node('option',{value:'simplified'},'Nomes + prescrição única'));style.value=presentation.style;colorCheck.checked=presentation.colors;colorLabel.append(colorCheck,document.createTextNode(' Cores nos conjugados'));presentationBox.append(style,colorLabel);style.onchange=colorCheck.onchange=()=>{presentation={style:style.value,colors:colorCheck.checked};try{localStorage.setItem('treinoGifPresentationV1',JSON.stringify(presentation));}catch(e){}clearResult();updatePresentation();};actions.append(generate,share,download,stop,close);dialog.append(heading,help,student,library,section,status,accept,presentationBox,list,result,actions);document.body.append(dialog);
    controls={heading,student,library,section,status,list,result,accept,generate,share,download,stop,presentationFields:[style,colorCheck]};
    library.onchange=()=>{mode=library.value;render();};section.onchange=()=>{selected=section.value==='ALL'?completeWorkout():workout.sections.find(s=>s.id===section.value);render();};
    accept.onclick=()=>{cards.filter(c=>!c.asset&&c.suggestions.length).forEach(c=>selectAsset(c,c.suggestions[0]));readiness();};
    generate.onclick=()=>selected?.id==='ALL'?generateCompleteWorkout():generateGIF();stop.onclick=cancel;close.onclick=()=>dialog.close();
    dialog.addEventListener('close',()=>{sequence++;cancel();disposeCards();clearResult();if(focusReturn?.isConnected)focusReturn.focus();});
    download.onclick=()=>{for(const item of files){const url=URL.createObjectURL(item),link=node('a',{href:url,download:item.name});document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);}};
    share.onclick=async()=>{if(!files.length)return;try{if(navigator.canShare?.({files}))await navigator.share({files,title:(selected.id==='ALL'?'Treino completo A–F':'Treino '+selected.id)+' · '+themes[mode].name});else{controls.status.textContent=files.length>1?'Este navegador não permite enviar os GIFs juntos. Baixe os arquivos e anexe na conversa do aluno.':'Baixe o GIF e anexe a imagem na conversa do aluno.';download.click();}}catch(error){if(error.name!=='AbortError')controls.status.textContent='Não foi possível compartilhar. Use Baixar GIF e anexe a imagem na conversa.';}};
  }
  function setBusy(busy){busy=busy||!!batchState;controls.presentationFields.forEach(e=>e.disabled=busy);controls.library.disabled=busy;controls.section.disabled=busy;controls.generate.disabled=busy||!cards.length;controls.accept.disabled=busy;controls.stop.hidden=!busy;workingCards().forEach(c=>{c.choose.disabled=busy;c.upload.disabled=busy;c.suggestionBox.querySelectorAll('button').forEach(b=>b.disabled=busy);});}
  function readiness(){
    if(job||batchState)return;
    const missing=cards.filter(c=>!c.asset),ready=cards.length-missing.length,suggested=missing.filter(c=>c.suggestions.length).length;
    controls.generate.disabled=!cards.length;
    controls.generate.textContent=missing.length?'Revisar '+missing.length+' exercício'+(missing.length>1?'s':''):selected?.id==='ALL'?'Gerar GIFs do treino completo para enviar':'Gerar GIF '+themes[mode].name;
    controls.accept.hidden=!suggested;controls.accept.textContent='Usar sugestões mostradas ('+suggested+')';
    controls.status.textContent=cards.length?ready+'/'+cards.length+' demonstrações prontas. '+(missing.length?'Confira as sugestões destacadas; conjugados aparecem lado a lado no mesmo bloco.':'Confira os movimentos e gere o GIF.'): 'Este treino está vazio. Adicione os exercícios na ficha.';
  }
  function invertInk(asset){return !asset.localURL&&((mode==='cm')!==(asset.collection==='cm'));}
  function assetURL(asset){return asset.localURL||asset.media||(asset.collection==='cm'?'cmfit-media/':'gymfaster-media/')+asset.id+'.mp4';}
  function playVisible(card){if(card.visible&&card.asset&&!job&&!batchState){if(!card.video.getAttribute('src'))card.video.src=assetURL(card.asset);card.video.play().catch(()=>{});}else card.video.pause();}
  function videoCaption(asset,reason){return asset.name+' · '+(asset.localURL?'Arquivo local · reenvie ao reabrir a ficha':asset.kind==='created-example'?'Exemplo criado':themes[asset.collection].name)+(asset.collection==='gymfaster'&&asset.gender&&!asset.kind?' · '+asset.gender:'')+(reason?' · '+reason:'');}
  function setVideo(card,asset,reason){
    if(card.localURL&&card.localURL!==asset?.localURL)URL.revokeObjectURL(card.localURL);
    card.localURL=asset?.localURL||null;card.asset=asset;card.video.classList.toggle('cm-ink-on-white',!!asset&&invertInk(asset)&&asset.collection==='cm');card.video.classList.toggle('gym-ink-on-black',!!asset&&invertInk(asset)&&asset.collection==='gymfaster');
    card.video.pause();card.video.removeAttribute('src');card.video.load();card.video.hidden=!asset;if(card.options)card.options.open=!asset;
    card.article.classList.toggle('gif-missing',!asset);
    card.caption.textContent=asset?videoCaption(asset,reason):'Escolha a demonstração deste exercício.';
    card.suggestionBox.hidden=!!asset;playVisible(card);clearResult();
  }
  function selectAsset(card,asset){
    remember(card.row.nome,asset);
    integration.save(card.row.source,asset.url,workout.student,card.row.partIndex);card.row.video=asset.url;card.row.gifURL=asset.url;
    setVideo(card,asset,'Escolhido por você');readiness();
  }
  function doses(text,count){const parts=text.replace(/^[\s—–-]+/,'').split(/\s*\+\s*/);if(parts.length!==count||!parts.every(p=>/^(?:\d+\s*[x×]\s*)?\d+(?:\s*[-–]\s*\d+)?(?:\s*(?:s|seg|segundos))?$/i.test(p.trim())))return null;const prefix=parts[0].match(/^(\d+\s*[x×]\s*)/);return parts.map(p=>/^\d+\s*[x×]/.test(p)||!prefix?p:prefix[1]+p);}
  function expandedRows(){return selected.rows.flatMap((row,index)=>{const parts=match().parts(row.nome),reps=row.detalhes.replace(/^[\s—–-]+/,'').match(/^(\s*\d+\s*[x×])\s*([\d\s–-]+)\+([\d\s–-]+)$/i);const split=doses(row.detalhes,parts.length);return parts.map((name,part)=>({...row,nome:name,fullDetails:row.detalhes,gifURL:row.gifs?.[part]||'',video:row.gifs?.[part]||(parts.length===1?row.video:''),compound:parts.length>1?row.nome:null,sourceIndex:index,partIndex:part,partCount:parts.length,label:String((row.sectionIndex??index)+1)+(parts.length>1?String.fromCharCode(97+part):''),detalhes:split?split[part]:parts.length===2&&reps?reps[1]+' '+reps[part+2].trim():row.detalhes}));});}
  function render(){
    if(job||batchState)return;
    clearResult();disposeCards();controls.list.replaceChildren();dialog.dataset.library=mode;controls.library.value=mode;controls.heading.textContent='Treino em GIF · '+themes[mode].name;controls.student.textContent=workout.student+' · '+(selected?.title||'Treino');
    if(!selected){readiness();return;}
    observer=new IntersectionObserver(entries=>entries.forEach(entry=>{const card=cards.find(c=>c.observeTarget===entry.target);if(card){card.visible=entry.isIntersecting;playVisible(card);}}),{root:dialog,rootMargin:'30px'});
    const prefs=preferences(),compoundHosts=new Map();let currentSection='';
    expandedRows().forEach(row=>{if(selected.id==='ALL'&&row.sectionID!==currentSection){currentSection=row.sectionID;controls.list.append(node('h4',{class:'gif-section-heading'},row.sectionTitle));}
      const article=node('article',{class:'gif-card'}),text=node('div',{class:'gif-card-text'}),name=node('strong',{},row.label+'. '+row.nome),details=node('p',{},row.detalhes),caption=node('small'),suggestionBox=node('div',{class:'gif-suggestions'}),choose=node('button',{type:'button'},'Escolher outro vídeo'),upload=node('button',{type:'button'},'Vídeo do aparelho'),input=node('input',{type:'file',accept:'video/*',hidden:'','aria-label':'Arquivo de vídeo de '+row.nome});
      const video=node('video',{muted:'',playsinline:'',loop:'',preload:'none','aria-label':'Demonstração de '+row.nome});video.muted=true;
      const resolution=match().resolve(row,availableVideos(),mode,match().driveID(row.gifURL)||prefs[choiceKey(row.nome)]),card={row,article,video,caption,choose,upload,suggestionBox,suggestions:resolution.suggestions,asset:null,localURL:null,visible:false};
      let host=controls.list;
      if(row.compound){
        if(!compoundHosts.has(row.sourceIndex)){
          const block=node('section',{class:'gif-compound','aria-label':'Conjugado '+((row.sectionIndex??row.sourceIndex)+1)+': '+row.compound});
          const heading=node('h4',{},((row.sectionIndex??row.sourceIndex)+1)+'. Conjugado'),grid=node('div',{class:'gif-compound-grid','data-size':String(row.partCount)});
          block.append(heading,grid);controls.list.append(block);compoundHosts.set(row.sourceIndex,grid);
        }
        host=compoundHosts.get(row.sourceIndex);article.classList.add('gif-compound-card');
      }
      resolution.suggestions.forEach(asset=>{const button=node('button',{type:'button'},'Usar '+themes[asset.collection].name+': '+asset.name);button.onclick=()=>selectAsset(card,asset);suggestionBox.append(button);});
      choose.onclick=()=>openPicker(card);
      upload.onclick=()=>input.click();input.onchange=()=>{const chosen=input.files?.[0];if(!chosen||job)return;if((!chosen.type.startsWith('video/')&&!/\.(mp4|m4v|mov|webm)$/i.test(chosen.name))||chosen.size>100*1048576){controls.status.textContent='Escolha um vídeo de até 100 MB.';return;}setVideo(card,{name:chosen.name,collection:mode,localURL:URL.createObjectURL(chosen)},'Usado somente neste GIF');readiness();};
      video.onerror=()=>{if(card.asset&&!job&&!batchState)card.caption.textContent='A prévia não carregou. Você pode tentar Gerar GIF para carregar a demonstração novamente.';};
      if(row.compound){
        const options=node('details',{class:'gif-card-options'}),summary=node('summary',{},'Vídeo / editar');options.append(summary,caption,choose,upload,input);card.options=options;
        text.append(name,details,suggestionBox,options);text.style.gridColumn='1';text.style.gridRow=String(row.partIndex+1);
        video.style.gridColumn=String(row.partIndex%2+2);video.style.gridRow=(Math.floor(row.partIndex/2)*2+1)+' / span '+Math.min(2,row.partCount-Math.floor(row.partIndex/2)*2);
      }else text.append(name,details,caption,suggestionBox,choose,upload,input);
      article.append(text,video);host.append(article);cards.push(card);card.observeTarget=row.compound?video:article;setVideo(card,resolution.video,resolution.reason);observer.observe(card.observeTarget);
    });updatePresentation();readiness();
  }
  function updatePresentation(){
    controls.list.querySelectorAll('.gif-compound-summary').forEach(n=>n.remove());
    for(const card of cards){if(!card.row.compound)continue;const text=card.article.querySelector('.gif-card-text'),title=text.querySelector('strong'),details=text.querySelector('p');title.querySelector('.gif-color-dot')?.remove();details.hidden=presentation.style==='simplified';card.video.style.borderTop=presentation.colors?'4px solid '+colorFor(card.row.partIndex):'';if(presentation.colors){const dot=node('span',{class:'gif-color-dot','aria-hidden':'true'},'• ');dot.style.color=colorFor(card.row.partIndex);title.prepend(dot);}if(card.row.partIndex===card.row.partCount-1&&presentation.style==='simplified'){const summary=node('p',{class:'gif-compound-summary'}),split=doses(card.row.fullDetails,card.row.partCount);if(presentation.colors&&split){split.forEach((dose,i)=>{if(i)summary.append(document.createTextNode(' + '));const badge=node('span',{},'• '+dose);badge.style.color=colorFor(i);badge.style.background='#fff';summary.append(badge);});}else summary.textContent=gifText(card.row.fullDetails);text.append(summary);}}
  }
  function refreshLibraryState(){
    if(job||batchState||!controls||!dialog?.open)return;
    const active=availableVideos(),prefs=preferences();
    for(const card of cards){
      if(card.asset?.localURL)continue;
      if(card.asset){
        const updated=library().decorate(card.asset);
        if(!updated.removed){
          if(updated.name!==card.asset.name){card.asset=updated;card.caption.textContent=videoCaption(updated,'Nome da sua biblioteca');}
          continue;
        }
        setVideo(card,null,'');
      }
      const resolution=match().resolve(card.row,active,mode,prefs[choiceKey(card.row.nome)]);
      card.suggestions=resolution.suggestions;card.suggestionBox.replaceChildren();
      resolution.suggestions.forEach(asset=>{const button=node('button',{type:'button'},'Usar '+themes[asset.collection].name+': '+asset.name);button.onclick=()=>selectAsset(card,asset);card.suggestionBox.append(button);});
      if(resolution.video)setVideo(card,resolution.video,resolution.reason);
    }
    if(!file)readiness();
  }
  function openPicker(card,onSelect,initialSource=mode,previewIcon=false){
    const picker=node('dialog',{class:'gif-video-picker','aria-label':'Escolher vídeo para '+card.row.nome});
    const title=node('h3',{},card.row.nome),top=node('div',{class:'gif-picker-top'}),search=node('input',{type:'search','aria-label':'Buscar demonstração',placeholder:'Nome, aparelho ou abreviação'});
    const source=node('select',{'aria-label':'Biblioteca da demonstração'}),group=node('select',{'aria-label':'Grupo muscular da demonstração'}),gender=node('select',{'aria-label':'Versão da demonstração'});
    const filters=node('div',{class:'gif-picker-filters'}),status=node('p',{class:'gif-picker-count',role:'status'}),all=node('button',{type:'button'},'Ver todos os vídeos'),list=node('div',{class:'gif-picker-results'}),close=node('button',{type:'button'},'Fechar');
    const manage=node('button',{type:'button','aria-pressed':'false'},'Editar biblioteca'),tools=node('div',{class:'gif-library-tools',hidden:''}),help=node('small',{},'As alterações ficam salvas neste navegador. Apagar remove o vídeo da sua lista, com opção de restaurar.'),removed=node('button',{type:'button'},'Ver apagados'),undo=node('button',{type:'button',hidden:''},'Desfazer exclusão');
    let editing=false,showRemoved=false,lastRemoved=null,notice='';
    source.append(node('option',{value:'both'},'CM + GymFaster'),node('option',{value:'gymfaster'},'GymFaster'),node('option',{value:'cm'},'CM'));source.value=initialSource;search.value=card.row.nome;
    function refreshFilters(){
      const pool=videos.filter(v=>source.value==='both'||v.collection===source.value);group.replaceChildren(node('option',{value:''},'Todos os grupos'));gender.replaceChildren(node('option',{value:''},'Todas as versões'));
      [...new Set(pool.map(v=>v.group))].sort((a,b)=>a.localeCompare(b,'pt-BR')).forEach(value=>group.append(node('option',{value},value)));
      [...new Set(pool.map(v=>v.gender))].sort().forEach(value=>gender.append(node('option',{value},value)));gender.hidden=source.value==='cm';showRemoved=false;update();
    }
    function act(action){try{action();}catch(error){notice=error.message;}update();}
    function renameForm(row,asset){
      row.querySelector('.gif-library-row-tools').hidden=true;
      const form=node('form',{class:'gif-library-rename'}),input=node('input',{type:'text',value:asset.name,maxlength:'160','aria-label':'Novo nome do vídeo'}),save=node('button',{type:'submit'},'Salvar nome'),cancel=node('button',{type:'button'},'Cancelar');
      form.append(input,save,cancel);row.append(form);input.focus();input.select();
      form.onsubmit=event=>{event.preventDefault();act(()=>{library().rename(asset.id,input.value);notice='Nome atualizado na sua biblioteca.';});};
      cancel.onclick=()=>update();input.onkeydown=event=>{if(event.key==='Escape'){event.preventDefault();event.stopPropagation();update();}};
    }
    function update(){
      const scroll=list.scrollTop;list.replaceChildren();
      const raw=videos.filter(v=>source.value==='both'||v.collection===source.value),decorated=library().apply(raw,true),deleted=decorated.filter(v=>v.removed).length,available=decorated.length-deleted;
      const pool=decorated.filter(v=>v.removed===showRemoved&&(!group.value||v.group===group.value)&&(!gender.value||v.gender===gender.value));
      const query=search.value.trim(),ranked=query?match().rank(query,pool,source.value).map(r=>r.video):pool;
      const tokens=match().canonical(query).split(' ').filter(Boolean),remaining=query?pool.filter(v=>tokens.every(word=>match().canonical([v.name,...v.aliases].join(' ')).includes(word))):[];
      const seen=new Set(),found=[...ranked,...remaining].filter(v=>{if(seen.has(v.id))return false;seen.add(v.id);return true;});
      status.textContent=(notice?notice+' ':'')+found.length+(showRemoved?' apagados encontrados':' resultados')+' · '+available+' disponíveis de '+raw.length+' vídeos';notice='';
      removed.textContent=showRemoved?'Voltar aos disponíveis':'Ver apagados ('+deleted+')';removed.disabled=!deleted&&!showRemoved;undo.hidden=!lastRemoved;
      if(!found.length)list.append(node('p',{},showRemoved?'Nenhum vídeo apagado nesta biblioteca.':'Tente menos palavras, outro grupo ou Ver todos os vídeos.'));
      found.forEach(asset=>{
        const row=node('article',{class:'gif-library-row'}),choose=node('button',{type:'button','data-video-id':asset.id},asset.name+' · '+themes[asset.collection].name+(asset.gender&&asset.gender!=='CM'?' · '+asset.gender:''));choose.disabled=asset.removed;choose.onclick=()=>{if(onSelect)onSelect(asset,card.row.nome);else selectAsset(card,asset);picker.close();};const eye=node('button',{type:'button',class:'gif-preview-eye','aria-label':'Ver movimento: '+asset.name+' · '+themes[asset.collection].name+(asset.gender?' · '+asset.gender:''),title:'Ver movimento antes de escolher'},'◉');if(previewIcon)eye.innerHTML=WorkoutVideoPreview.eye;else eye.textContent='(GIFs)';eye.onclick=()=>WorkoutVideoPreview.open(asset);row.append(choose,eye);
        if(asset.name!==asset.originalName)row.append(node('small',{},'Nome original: '+asset.originalName));
        const actions=node('div',{class:'gif-library-row-tools'});actions.hidden=!editing;
        if(asset.removed){const restore=node('button',{type:'button'},'Restaurar');restore.onclick=()=>act(()=>{library().restore(asset.id);notice='Vídeo restaurado.';});actions.append(restore);}
        else{
          const rename=node('button',{type:'button'},'Renomear'),erase=node('button',{type:'button',class:'gif-library-remove'},'Apagar');rename.onclick=()=>renameForm(row,asset);erase.onclick=()=>act(()=>{library().remove(asset.id);lastRemoved=asset.id;notice='Vídeo apagado da sua lista.';});actions.append(rename,erase);
          if(asset.name!==asset.originalName){const reset=node('button',{type:'button'},'Restaurar nome');reset.onclick=()=>act(()=>{library().resetName(asset.id);notice='Nome original restaurado.';});actions.append(reset);}
        }
        row.append(actions);list.append(row);
      });list.scrollTop=scroll;
    }
    manage.onclick=()=>{editing=!editing;tools.hidden=!editing;manage.textContent=editing?'Concluir edição':'Editar biblioteca';manage.setAttribute('aria-pressed',String(editing));if(!editing)showRemoved=false;update();};
    removed.onclick=()=>{showRemoved=!showRemoved;search.value='';group.value='';gender.value='';update();};
    undo.onclick=()=>act(()=>{if(lastRemoved){library().restore(lastRemoved);lastRemoved=null;notice='Exclusão desfeita.';}});
    all.onclick=()=>{showRemoved=false;search.value='';group.value='';gender.value='';update();};search.oninput=update;source.onchange=refreshFilters;group.onchange=update;gender.onchange=update;close.onclick=()=>picker.close();
    tools.append(help,removed,undo);filters.append(group,gender);top.append(title,manage);picker.append(top,search,source,filters,status,all,tools,list,close);document.body.append(picker);picker.onclose=()=>{picker.remove();refreshLibraryState();};refreshFilters();picker.showModal();return picker;
  }

  async function loadCatalogs(){if(!catalogPromise)catalogPromise=Promise.all(['cmfit-catalog.json?v=1','gymfaster-catalog.json?v=3'].map(async url=>{const response=await fetch(url);if(!response.ok)throw Error('Catálogo indisponível');return response.json();})).then(([cm,gym])=>videos=[...cm.videos.map(v=>({...v,collection:'cm'})),...gym.videos.map(v=>({...v,collection:'gymfaster'}))]).catch(error=>{catalogPromise=null;throw error;});return catalogPromise;}
  async function open(library=mode){
    if(!integration||job||batchState)return;if(!dialog)create();const token=++sequence;focusReturn=document.activeElement;mode=themes[library]?library:'gymfaster';workout=integration.read();controls.section.replaceChildren();workout.sections.forEach(s=>controls.section.append(node('option',{value:s.id},s.title)));controls.section.append(node('option',{value:'ALL'},'Treino completo A–F · um GIF por seção'));selected=workout.sections.find(s=>s.id==='A')||workout.sections[0];controls.section.value=selected?.id||'';controls.generate.disabled=true;if(!dialog.open)dialog.showModal();controls.status.textContent='Carregando as bibliotecas CM e GymFaster…';
    try{await loadCatalogs();if(dialog.open&&token===sequence)render();}catch(error){controls.status.textContent='Não foi possível carregar as bibliotecas. Feche e tente novamente.';}
  }
  function check(active){if(active.cancelled||active!==job||!dialog.open)throw Error('Geração cancelada.');}
  function mediaEvent(video,event,active,action){return new Promise((resolve,reject)=>{let settled=false;const timeout=setTimeout(()=>finish(Error('Não foi possível ler o vídeo. Confira a conexão e tente novamente.')),15000),poll=setInterval(()=>{try{check(active);}catch(error){finish(error);}},100);const done=()=>finish(),failed=()=>{console.warn('GIF decoder',active.currentName,video.error?.code,video.error?.message);finish(Error('Não foi possível ler '+(active.currentName||'esta demonstração')+'. Escolha outro vídeo ou um arquivo MP4.'));};function finish(error){if(settled)return;settled=true;clearTimeout(timeout);clearInterval(poll);video.removeEventListener(event,done);video.removeEventListener('error',failed);error?reject(error):resolve();}video.addEventListener(event,done,{once:true});video.addEventListener('error',failed,{once:true});try{action();}catch(error){finish(error);}});}
  async function loadDecoder(url,active){const video=active.decoder;await mediaEvent(video,'loadeddata',active,()=>{video.src=url;video.preload='auto';video.load();});if(!Number.isFinite(video.duration)||video.duration<=0)throw Error('A duração de um vídeo não foi reconhecida. Escolha outro arquivo.');return video;}
  async function seek(video,time,active){check(active);if(Math.abs(video.currentTime-time)>0.0001||video.readyState<2)await mediaEvent(video,'seeked',active,()=>{video.currentTime=time;});check(active);if(Math.abs(video.currentTime-time)>0.08)throw Error('Não foi possível avançar o movimento. Tente novamente.');await new Promise(resolve=>requestAnimationFrame(resolve));check(active);}
  function send(active,data,transfers=[]){return new Promise((resolve,reject)=>{let settled=false;const target=active.worker,timeout=setTimeout(()=>finish(Error('A geração demorou demais. Tente um treino menor.')),120000),poll=setInterval(()=>{try{check(active);}catch(error){finish(error);}},100);const response=event=>{if(event.data.type==='progress'){controls.status.textContent=(batchState?'Treino '+selected.id+' · ':'')+'Finalizando GIF: '+event.data.percent+'%';return;}event.data.type==='error'?finish(Error(event.data.message)):finish(null,event.data);},failed=()=>finish(Error('Não foi possível iniciar o gerador. Recarregue o treino36 e tente novamente.'));function finish(error,value){if(settled)return;settled=true;clearTimeout(timeout);clearInterval(poll);target.removeEventListener('message',response);target.removeEventListener('error',failed);error?reject(error):resolve(value);}target.addEventListener('message',response);target.addEventListener('error',failed);target.postMessage(data,transfers);});}
  function gifText(text){return String(text).replace(/(\d)\s*—\s*(?=\d)/g,'$1-').replace(/—/g,' ').replace(/\s+/g,' ').trim();}
  function wrap(ctx,text,x,y,width,step){text=gifText(text);let line='';for(const word of text.split(/\s+/)){const next=line?line+' '+word:word;if(ctx.measureText(next).width>width&&line){ctx.fillText(line,x,y);y+=step;line=word;}else line=next;}if(line)ctx.fillText(line,x,y);return y+step;}
  function lineCount(ctx,text,width){text=gifText(text);let n=1,line='';for(const word of text.split(/\s+/)){const next=line?line+' '+word:word;if(ctx.measureText(next).width>width&&line){n++;line=word;}else line=next;}return n;}
  function layout(ctx){
    ctx.font='bold 29px Arial';layoutHeader=Math.max(HEADER,88+lineCount(ctx,selected.title,744)*32+55);
    let top=layoutHeader;layoutBlocks=[];
    for(const card of cards){
      let block=layoutBlocks[layoutBlocks.length-1];
      if(!block||block.sourceIndex!==card.row.sourceIndex){block={sourceIndex:card.row.sourceIndex,compound:!!card.row.compound,members:[],pairs:[]};layoutBlocks.push(block);}
      block.members.push(card);
    }
    for(const block of layoutBlocks){
      block.top=top;
      if(!block.compound){
        const c=block.members[0];ctx.font='bold 23px Arial';const names=lineCount(ctx,c.row.label+'. '+c.row.nome,358);ctx.font='20px Arial';
        c.top=top;c.height=Math.max(CARD,Math.max(38+names*28+13,120)+lineCount(ctx,c.row.detalhes,358)*26+25);c.slotX=410;c.slotY=top+5;c.slotWidth=SLOT_W;c.slotHeight=SLOT_H;block.height=c.height;
      }else if(presentation.style==='simplified'){
        let cursor=top+36;for(const c of block.members){ctx.font='bold 23px Arial';c.top=top;c.nameX=presentation.colors?56:36;c.nameY=cursor+22;cursor=c.nameY+lineCount(ctx,c.row.label+'. '+c.row.nome,presentation.colors?338:358)*26+10;}
        block.summaryY=cursor+16;ctx.font='20px Arial';cursor=block.summaryY+lineCount(ctx,block.members[0].row.fullDetails,358)*24+24;
        for(let i=0;i<block.members.length;i+=2){const pair=block.members.slice(i,i+2);pair.forEach((c,column)=>{c.slotX=column?594:410;c.slotY=top+48+Math.floor(i/2)*230;c.slotWidth=166;c.slotHeight=212;});block.pairs.push(pair);}
        block.height=Math.max(CARD,cursor-top,48+block.pairs.length*230+10);
      }else{
        let cursor=top+36;
        for(let index=0;index<block.members.length;index+=2){
          const pair=block.members.slice(index,index+2),pairTop=cursor;
          for(const c of pair){
            ctx.font='bold 23px Arial';const names=lineCount(ctx,c.row.label+'. '+c.row.nome,presentation.colors?338:358)*26;
            ctx.font='20px Arial';const details=lineCount(ctx,c.row.detalhes,358)*24;
            c.top=top;c.nameX=presentation.colors?56:36;c.nameY=cursor+22;c.detailsY=c.nameY+names+6;cursor=c.detailsY+details+12;
          }
          const pairHeight=Math.max(212,cursor-pairTop),slotY=pairTop+(pairHeight-212)/2;
          pair.forEach((c,column)=>{c.slotX=column?594:410;c.slotY=Math.round(slotY);c.slotWidth=166;c.slotHeight=212;});
          block.pairs.push(pair);cursor=pairTop+pairHeight+12;
        }
        block.height=Math.max(CARD,cursor-top+10);
      }
      top+=block.height;
    }
    cards.forEach(c=>{c.article.dataset.gifSlot=JSON.stringify({x:c.slotX,y:c.slotY,width:c.slotWidth,height:c.slotHeight,block:c.row.sourceIndex});});
    return top+8;
  }
  function paint(ctx,canvas){
    const t=themes[mode];ctx.fillStyle=t.bg;ctx.fillRect(0,0,WIDTH,canvas.height);ctx.fillStyle=t.green;ctx.fillRect(0,0,WIDTH,7);
    ctx.font='bold 23px Arial';ctx.fillText('CAIO MACÊDO · PERSONAL TRAINER',28,43);ctx.fillStyle=t.ink;ctx.font='bold 29px Arial';wrap(ctx,selected.title,28,88,744,32);ctx.font='19px Arial';ctx.fillText(gifText(workout.student).slice(0,65),28,layoutHeader-29);
    for(const block of layoutBlocks){
      ctx.fillStyle=t.card;ctx.fillRect(20,block.top,760,block.height-12);
      if(block.compound){
        ctx.fillStyle=t.green;ctx.font='bold 18px Arial';ctx.fillText((block.members[0].row.sectionIndex??block.sourceIndex)+1+'. CONJUGADO',36,block.top+28);
        if(presentation.style==='simplified'){const text=block.members[0].row.fullDetails,split=doses(text,block.members.length);ctx.font='20px Arial';ctx.fillStyle=t.green;if(presentation.colors&&split)paintDoses(ctx,split,36,block.summaryY,0);else wrap(ctx,text,36,block.summaryY,358,24);}
        for(const pair of block.pairs){
          pair.forEach(c=>{ctx.fillStyle=t.ink;ctx.font='bold 23px Arial';wrap(ctx,c.row.label+'. '+c.row.nome,c.nameX,c.nameY,presentation.colors?338:358,26);if(presentation.colors){dot(ctx,43,c.nameY-8,c.row.partIndex);dot(ctx,c.slotX+8,c.slotY-8,c.row.partIndex);}if(presentation.style!=='simplified'){ctx.fillStyle=t.green;ctx.font='20px Arial';if(presentation.colors)paintDoses(ctx,[c.row.detalhes],c.nameX,c.detailsY,c.row.partIndex);else wrap(ctx,c.row.detalhes,c.nameX,c.detailsY,358,24);}});
          if(pair.length===2){ctx.fillStyle=t.green;ctx.font='bold 28px Arial';ctx.textAlign='center';ctx.fillText('+',585,pair[0].slotY+pair[0].slotHeight/2+8);ctx.textAlign='start';}
        }
      }else{
        const c=block.members[0];ctx.fillStyle=t.ink;ctx.font='bold 23px Arial';const y=wrap(ctx,c.row.label+'. '+c.row.nome,36,c.top+38,358,28);ctx.fillStyle=t.green;ctx.font='20px Arial';wrap(ctx,c.row.detalhes,36,Math.max(y+13,c.top+120),358,26);
      }
    }
  }
  function dot(ctx,x,y,index){ctx.beginPath();ctx.arc(x,y,5,0,Math.PI*2);ctx.fillStyle=colorFor(index);ctx.fill();ctx.strokeStyle='#fff';ctx.lineWidth=1;ctx.stroke();}
  function paintDoses(ctx,values,x,y,start){const origin=x;values.forEach((text,i)=>{const label='• '+gifText(text),width=ctx.measureText(label).width+12;if(x+width>origin+358){x=origin;y+=28;}ctx.fillStyle='#fff';ctx.fillRect(x-2,y-19,width,24);ctx.fillStyle=colorFor(start+i);ctx.fillText(label,x+3,y);x+=width;if(i<values.length-1){ctx.fillStyle=themes[mode].green;ctx.fillText('+',x,y);x+=18;}});}
  function drawSlot(ctx,video,asset){
    const width=ctx.canvas.width,height=ctx.canvas.height;
    ctx.fillStyle=asset.collection==='cm'?'#000':'#fff';ctx.fillRect(0,0,width,height);
    const scale=Math.min(width/video.videoWidth,height/video.videoHeight),w=video.videoWidth*scale,h=video.videoHeight*scale;ctx.drawImage(video,(width-w)/2,(height-h)/2,w,h);
    if(invertInk(asset)){
      const frame=ctx.getImageData(0,0,width,height),pixels=frame.data;
      // Same sRGB transform as the preview's invert(1) hue-rotate(180deg).
      // Black/white swap while the muscle highlight retains its green hue.
      for(let i=0;i<pixels.length;i+=4){const r=pixels[i],g=pixels[i+1],b=pixels[i+2],shift=255-2*(.213*r+.715*g+.072*b);pixels[i]=r+shift;pixels[i+1]=g+shift;pixels[i+2]=b+shift;}
      ctx.putImageData(frame,0,0);return frame;
    }
  }
  function completeWorkout(){return {id:'ALL',title:'Treino completo · A–F',rows:workout.sections.flatMap(section=>section.rows.map((row,index)=>({...row,sectionID:section.id,sectionTitle:section.title,sectionIndex:index}))) };}
  async function generateCompleteWorkout(){
    if(job||batchState||!cards.length)return;
    const sections=workout.sections.filter(section=>cards.some(card=>card.row.sectionID===section.id));
    const missing=cards.filter(card=>!card.asset);if(missing.length){controls.status.textContent='Falta confirmar '+missing.length+' demonstrações antes de gerar o treino completo.';missing[0].article.scrollIntoView({block:'center'});return;}
    const oversized=sections.find(section=>cards.filter(card=>card.row.sectionID===section.id).length>20);if(oversized){controls.status.textContent='O treino '+oversized.id+' ultrapassa 20 demonstrações. Divida essa seção antes de gerar.';return;}
    if(!window.confirm('Gerar '+sections.length+' GIFs do treino completo ('+sections.map(s=>s.id).join(', ')+') para enviar? Será um GIF de 5 segundos por seção. Pode levar vários minutos e consumir bastante internet. Tem certeza que deseja continuar?'))return;
    const allCards=cards,selection=selected,generated=[];clearResult();batchState={cards:allCards,cancelled:false};setBusy(true);allCards.forEach(card=>card.video.pause());
    try{
      for(const section of sections){
        if(batchState.cancelled||!dialog.open)break;
        selected=section;cards=allCards.filter(card=>card.row.sectionID===section.id);
        const result=await generateGIF(true);if(!result)break;generated.push({file:result,section});
      }
    }finally{
      const cancelled=batchState.cancelled,reason=controls.status.textContent;batchState=null;selected=selection;cards=dialog.open?allCards:[];setBusy(false);
      if(dialog.open){
        files=generated.map(item=>item.file);file=files[0]||null;controls.result.replaceChildren();
        generated.forEach(item=>{const url=URL.createObjectURL(item.file);resultURLs.push(url);const result=node('section',{class:'gif-batch-result'});result.append(node('strong',{},item.section.title),node('img',{src:url,alt:'Treino '+item.section.id+' em movimento'}),node('a',{href:url,download:item.file.name},'Baixar GIF '+item.section.id));controls.result.append(result);});
        controls.result.hidden=!files.length;controls.share.hidden=!files.length;controls.download.hidden=!files.length;controls.share.textContent=files.length>1?'Enviar GIFs do treino completo':'Compartilhar GIF';controls.download.textContent=files.length>1?'Baixar GIFs':'Baixar GIF';
        controls.status.textContent=generated.length===sections.length?generated.length+' GIFs prontos · 5 segundos cada. Confira e toque em Enviar GIFs do treino completo.':(cancelled?'Geração cancelada. ':reason+' ')+generated.length+'/'+sections.length+' GIFs prontos. Você pode baixar ou compartilhar os que foram concluídos.';
        cards.forEach(playVisible);if(files.length)controls.result.scrollIntoView({block:'start'});if(libraryDirty){libraryDirty=false;refreshLibraryState();}
      }
    }
  }
  async function generateGIF(batch=false){
    if(job||!cards.length)return;const missing=cards.filter(c=>!c.asset);if(missing.length){controls.status.textContent='Falta confirmar: '+missing.map(c=>c.row.nome).join(', ')+'. Toque numa sugestão ou escolha um vídeo.';missing[0].article.scrollIntoView({block:'center'});return;}if(cards.length>20){controls.status.textContent='Use até 20 demonstrações por GIF. Divida esta seção.';return;}
    if(!batch)clearResult();const active={cancelled:false,abort:new AbortController(),worker:null,decoder:node('video',{muted:'',playsinline:'',preload:'auto','aria-hidden':'true',class:'gif-decoder'}),urls:[]};active.decoder.muted=true;job=active;dialog.append(active.decoder);setBusy(true);cards.forEach(c=>{c.video.pause();c.video.removeAttribute('src');c.video.load();});
    try{
      const canvas=document.createElement('canvas');canvas.width=WIDTH;const ctx=canvas.getContext('2d',{willReadFrequently:true}),height=layout(ctx);if(height>12000)throw Error('A ficha ficou muito longa. Divida o treino para gerar o GIF.');canvas.height=height;paint(ctx,canvas);const base=ctx.getImageData(0,0,WIDTH,height).data.buffer;
      const slot=document.createElement('canvas');slot.width=SLOT_W;slot.height=SLOT_H;const sc=slot.getContext('2d',{willReadFrequently:true});const unique=new Map();cards.forEach(c=>{const source=assetURL(c.asset);c.key=source+'|'+c.slotWidth+'x'+c.slotHeight;if(!unique.has(c.key))unique.set(c.key,{asset:c.asset,key:c.key,source,width:c.slotWidth,height:c.slotHeight,url:null});});
      let index=0;
      for(const item of unique.values()){
        check(active);controls.status.textContent=(batchState?'Treino '+selected.id+' · ':'')+'Carregando movimento '+(++index)+'/'+unique.size+'…';
        const timer=setTimeout(()=>active.abort.abort(),60000);let response;try{response=await fetch(item.source,{signal:active.abort.signal,cache:'force-cache'});if(!response.ok)throw Error('Não foi possível carregar '+item.asset.name+'. Tente novamente.');const blob=await response.blob();item.url=URL.createObjectURL(blob);active.urls.push(item.url);}finally{clearTimeout(timer);}
        slot.width=item.width;slot.height=item.height;active.currentName=item.asset.name;const video=await loadDecoder(item.url,active);await seek(video,0.001,active);drawSlot(sc,video,item.asset);cards.filter(c=>c.key===item.key).forEach(c=>ctx.drawImage(slot,c.slotX,c.slotY));
      }
      check(active);const sample=ctx.getImageData(0,0,WIDTH,height).data.buffer;active.worker=new Worker('workout-gif-worker.js?v=2');await send(active,{type:'init',width:WIDTH,height,count:FRAMES,base,sample,slots:cards.map(c=>({key:c.key,x:c.slotX,y:c.slotY,width:c.slotWidth,height:c.slotHeight}))},[base,sample]);
      index=0;
      for(const item of unique.values()){
        slot.width=item.width;slot.height=item.height;active.currentName=item.asset.name;const video=await loadDecoder(item.url,active);
        for(let frame=0;frame<FRAMES;frame++){
          await seek(video,Math.max(0.001,frame/FRAMES*video.duration),active);const converted=drawSlot(sc,video,item.asset);const pixels=(converted||sc.getImageData(0,0,item.width,item.height)).data.buffer;await send(active,{type:'cache',key:item.key,frame,pixels},[pixels]);controls.status.textContent=(batchState?'Treino '+selected.id+' · ':'')+'Preparando movimento '+(index+1)+'/'+unique.size+' · '+Math.round((index*FRAMES+frame+1)/(unique.size*FRAMES)*85)+'%';
        }index++;
      }
      controls.status.textContent=(batchState?'Treino '+selected.id+' · ':'')+'Finalizando GIF…';const result=await send(active,{type:'finish'});check(active);
      const generated=new File([result.bytes],'treino_'+selected.id+'_'+mode+'_'+workout.student.slice(0,80).replace(/[^a-z0-9áéíóúâêôãõç_-]+/gi,'_')+'.gif',{type:'image/gif'});if(batch)return generated;file=generated;files=[file];blobURL=URL.createObjectURL(file);controls.result.replaceChildren(node('img',{src:blobURL,alt:'Treino '+selected.id+' · '+themes[mode].name+' em movimento'}));controls.result.hidden=false;controls.share.hidden=false;controls.download.hidden=false;controls.status.textContent='GIF pronto · '+themes[mode].name+' · 5 segundos · '+(file.size/1048576).toFixed(1)+' MB. Confira e compartilhe.';controls.result.scrollIntoView({block:'start'});
    }catch(error){if(dialog.open&&job===active)controls.status.textContent=active.cancelled?'Geração cancelada. Você pode tentar novamente.':error.name==='AbortError'?'O carregamento demorou demais. Verifique a conexão e tente novamente.':error.message||'Não foi possível gerar o GIF. Tente novamente.';}
    finally{active.worker?.terminate();active.decoder.pause();active.decoder.removeAttribute('src');active.decoder.load();active.decoder.remove();active.urls.forEach(url=>URL.revokeObjectURL(url));if(job===active){job=null;setBusy(false);if(dialog.open&&!batchState){cards.forEach(playVisible);if(libraryDirty){libraryDirty=false;refreshLibraryState();}}}}
  }
  window.addEventListener('workout-video-library-change',()=>{if(dialog?.open){if(job||batchState)libraryDirty=true;else if(!document.querySelector('.gif-video-picker[open]'))refreshLibraryState();}});
  async function pick(options){
    const button=options.trigger||document.activeElement;
    try{
      await loadCatalogs();
      const text=String(options.name||''),linked=match().driveID(options.video||text.match(/\[v[ií]deo:\s*([^\]]+)\]/i)?.[1]||''),saved=videos.find(v=>v.id===linked);
      if(options.previewOnly&&saved){WorkoutVideoPreview.open(library().decorate(saved));return;}
      const parts=text.split(/\r?\n/).flatMap(line=>match().parts(line.replace(/\[v[ií]deo:[^\]]+\]/gi,'').split(/\s+[—–]\s+|\s+\d+\s*[x×]\s*\d/i)[0].trim())).filter(Boolean),card={row:{nome:parts[0]||''}};
      const picker=openPicker(card,(asset,name)=>{if(options.persistChoice!==false){try{const prefs=preferences();prefs[asset.collection+':'+match().canonical(name)]=asset.id;localStorage.setItem(prefKey,JSON.stringify(prefs));}catch(error){}}options.onSelect?.(asset,name);WorkoutVideoPreview.open(asset,button);},'both',!!options.previewIcon);
      if(parts.length>1){const group=node('div',{class:'gif-picker-parts','aria-label':'Exercícios do conjugado'});parts.forEach(name=>{const b=node('button',{type:'button'},name);b.onclick=()=>{card.row.nome=name;picker.querySelector('h3').textContent=name;const search=picker.querySelector('input[type=search]');search.value=name;search.dispatchEvent(new Event('input'));};group.append(b);});picker.querySelector('.gif-picker-top').after(group);}
      picker.addEventListener('close',()=>{if(button?.isConnected)button.focus();},{once:true});
    }catch(error){window.alert('Não foi possível abrir a biblioteca de vídeos. Tente novamente.');}
  }
  async function downloadVideo(url,name){
    await loadCatalogs();const id=match().driveID(url),asset=videos.find(v=>v.id===id);
    if(!asset)throw Error('Este vídeo é de um link externo. Abra o link original para baixar, se disponível.');
    const response=await fetch(assetURL(asset),{cache:'force-cache'});if(!response.ok)throw Error('Não foi possível baixar o vídeo. Tente novamente.');
    const blob=await response.blob(),objectURL=URL.createObjectURL(blob),link=node('a',{href:objectURL,download:String(name||asset.name).replace(/[\\/:*?"<>|]/g,'_').slice(0,140)+'.mp4'});document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(objectURL),60000);
  }
  async function findSamples(name,urls=[]){await loadCatalogs();const available=availableVideos(),prefs=preferences();return match().parts(name).map((part,index)=>{if(urls[index]!==undefined)return urls[index];const remembered=available.find(v=>v.id===(prefs['cm:'+match().canonical(part)]||prefs['gymfaster:'+match().canonical(part)]));if(remembered)return remembered.url;const exact=match().rank(part,available,mode).find(item=>item.score===1);return exact?.video.url||'';});}
  return {configure,open,pick,downloadVideo,findSamples};
})();
