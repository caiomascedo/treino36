window.GymFasterWorkout = (() => {
  'use strict';
  const WIDTH=800,CARD=270,HEADER=175,FRAMES=100,SLOT_W=350,SLOT_H=242;
  const themes={cm:{name:'CM',bg:'#050906',card:'#0a110d',ink:'#f3faf5',green:'#3aeb91'},gymfaster:{name:'GymFaster',bg:'#eff5f1',card:'#fff',ink:'#1b3428',green:'#176b43'}};
  let integration,dialog,controls,videos=[],catalogPromise,workout,selected,cards=[],mode='gymfaster',file,blobURL,observer,job=null,sequence=0,layoutHeader=HEADER,focusReturn;
  const match=()=>window.WorkoutVideoMatch;
  const node=(tag,attrs={},text)=>{const item=document.createElement(tag);Object.entries(attrs).forEach(([key,value])=>item.setAttribute(key,value));if(text!==undefined)item.textContent=text;return item;};
  const prefKey='treinoGifChoicesV1';
  function preferences(){try{return JSON.parse(localStorage.getItem(prefKey)||'{}')||{};}catch(error){return {};}}
  function choiceKey(name){return mode+':'+match().canonical(name);}
  function remember(name,asset){try{const prefs=preferences();prefs[choiceKey(name)]=asset.id;localStorage.setItem(prefKey,JSON.stringify(prefs));}catch(error){}}
  function configure(options){integration=options;}
  function clearResult(){file=null;if(blobURL)URL.revokeObjectURL(blobURL);blobURL=null;controls.result.replaceChildren();controls.result.hidden=true;controls.share.hidden=true;controls.download.hidden=true;}
  function cancel(){if(!job)return;job.cancelled=true;job.abort.abort();job.worker?.terminate();if(job.decoder){job.decoder.pause();job.decoder.removeAttribute('src');job.decoder.load();}}
  function disposeCards(){observer?.disconnect();cards.forEach(card=>{card.video.pause();card.video.removeAttribute('src');card.video.load();if(card.localURL)URL.revokeObjectURL(card.localURL);});cards=[];}
  function create(){
    dialog=node('dialog',{id:'workoutGifDialog','aria-labelledby':'workoutGifTitle'});
    const heading=node('h3',{id:'workoutGifTitle'}),help=node('p',{},'Monte a ficha com movimentos do corpo inteiro. O GIF repete por 5 segundos e pode ser baixado ou compartilhado.'),student=node('strong',{class:'gif-student'});
    const library=node('select',{'aria-label':'Biblioteca dos GIFs'});library.append(node('option',{value:'cm'},'CM · fundo branco, traços pretos'),node('option',{value:'gymfaster'},'GymFaster · modelo anatômico'));
    const section=node('select',{'aria-label':'Treino para o GIF'}),status=node('p',{role:'status','aria-live':'polite'}),list=node('div',{class:'gif-cards'}),result=node('div',{class:'gif-result',hidden:''});
    const accept=node('button',{type:'button',class:'gif-accept-suggestions',hidden:''},'Usar sugestões mostradas');
    const actions=node('div',{class:'gif-actions'}),generate=node('button',{type:'button',class:'gif-primary'}),share=node('button',{type:'button',hidden:''},'Compartilhar GIF'),download=node('button',{type:'button',hidden:''},'Baixar GIF'),stop=node('button',{type:'button',hidden:''},'Cancelar geração'),close=node('button',{type:'button'},'Fechar');
    actions.append(generate,share,download,stop,close);dialog.append(heading,help,student,library,section,status,accept,list,result,actions);document.body.append(dialog);
    controls={heading,student,library,section,status,list,result,accept,generate,share,download,stop};
    library.onchange=()=>{mode=library.value;render();};section.onchange=()=>{selected=workout.sections.find(s=>s.id===section.value);render();};
    accept.onclick=()=>{cards.filter(c=>!c.asset&&c.suggestions.length).forEach(c=>selectAsset(c,c.suggestions[0]));readiness();};
    generate.onclick=generateGIF;stop.onclick=cancel;close.onclick=()=>dialog.close();
    dialog.addEventListener('close',()=>{sequence++;cancel();disposeCards();clearResult();if(focusReturn?.isConnected)focusReturn.focus();});
    download.onclick=()=>{if(!file||!blobURL)return;const link=node('a',{href:blobURL,download:file.name});document.body.append(link);link.click();link.remove();};
    share.onclick=async()=>{if(!file)return;try{if(navigator.canShare?.({files:[file]}))await navigator.share({files:[file],title:'Treino '+selected.id+' · '+themes[mode].name});else{controls.status.textContent='Baixe o GIF e anexe a imagem na conversa do aluno.';download.click();}}catch(error){if(error.name!=='AbortError')controls.status.textContent='Não foi possível compartilhar. Use Baixar GIF e anexe a imagem na conversa.';}};
  }
  function setBusy(busy){controls.library.disabled=busy;controls.section.disabled=busy;controls.generate.disabled=busy||!cards.length;controls.accept.disabled=busy;controls.stop.hidden=!busy;cards.forEach(c=>{c.choose.disabled=busy;c.upload.disabled=busy;c.suggestionBox.querySelectorAll('button').forEach(b=>b.disabled=busy);});}
  function readiness(){
    if(job)return;
    const missing=cards.filter(c=>!c.asset),ready=cards.length-missing.length,suggested=missing.filter(c=>c.suggestions.length).length;
    controls.generate.disabled=!cards.length;
    controls.generate.textContent=missing.length?'Revisar '+missing.length+' exercício'+(missing.length>1?'s':''):'Gerar GIF '+themes[mode].name;
    controls.accept.hidden=!suggested;controls.accept.textContent='Usar sugestões mostradas ('+suggested+')';
    controls.status.textContent=cards.length?ready+'/'+cards.length+' demonstrações prontas. '+(missing.length?'Confira as sugestões destacadas; combinações foram separadas mantendo os blocos do treino.':'Confira os movimentos e gere o GIF.'): 'Este treino está vazio. Adicione os exercícios na ficha.';
  }
  function cmWhiteInk(asset){return asset.collection==='cm'&&!asset.localURL;}
  function assetURL(asset){return asset.localURL||asset.media||(asset.collection==='cm'?'cmfit-media/':'gymfaster-media/')+asset.id+'.mp4';}
  function playVisible(card){if(card.visible&&card.asset&&!job){if(!card.video.getAttribute('src'))card.video.src=assetURL(card.asset);card.video.play().catch(()=>{});}else card.video.pause();}
  function setVideo(card,asset,reason){
    if(card.localURL&&card.localURL!==asset?.localURL)URL.revokeObjectURL(card.localURL);
    card.localURL=asset?.localURL||null;card.asset=asset;card.video.classList.toggle('cm-ink-on-white',!!asset&&cmWhiteInk(asset));
    card.video.pause();card.video.removeAttribute('src');card.video.load();card.video.hidden=!asset;
    card.article.classList.toggle('gif-missing',!asset);
    card.caption.textContent=asset?asset.name+' · '+(asset.localURL?'Arquivo local · reenvie ao reabrir a ficha':asset.kind==='created-example'?'Exemplo criado':themes[asset.collection].name)+(asset.collection==='gymfaster'&&asset.gender&&!asset.kind?' · '+asset.gender:'')+(reason?' · '+reason:''):'Escolha a demonstração deste exercício.';
    card.suggestionBox.hidden=!!asset;playVisible(card);clearResult();
  }
  function selectAsset(card,asset){
    remember(card.row.nome,asset);
    if(!card.row.compound){integration.save(card.row.source,asset.url,workout.student);card.row.video=asset.url;}
    setVideo(card,asset,'Escolhido por você');readiness();
  }
  function expandedRows(){return selected.rows.flatMap((row,index)=>{const parts=match().parts(row.nome),reps=row.detalhes.replace(/^[\s—–-]+/,'').match(/^(\s*\d+\s*[x×])\s*([\d\s–-]+)\+([\d\s–-]+)$/i);return parts.map((name,part)=>({...row,nome:name,video:parts.length===1?row.video:'',compound:parts.length>1?row.nome:null,label:String(index+1)+(parts.length>1?String.fromCharCode(97+part):''),detalhes:parts.length===2&&reps?reps[1]+' '+reps[part+2].trim():row.detalhes}));});}
  function render(){
    if(job)return;
    clearResult();disposeCards();controls.list.replaceChildren();dialog.dataset.library=mode;controls.library.value=mode;controls.heading.textContent='Treino em GIF · '+themes[mode].name;controls.student.textContent=workout.student+' · '+(selected?.title||'Treino');
    if(!selected){readiness();return;}
    observer=new IntersectionObserver(entries=>entries.forEach(entry=>{const card=cards.find(c=>c.article===entry.target);if(card){card.visible=entry.isIntersecting;playVisible(card);}}),{root:dialog,rootMargin:'30px'});
    const prefs=preferences();
    expandedRows().forEach(row=>{
      const article=node('article',{class:'gif-card'}),text=node('div',{class:'gif-card-text'}),name=node('strong',{},row.label+'. '+row.nome),details=node('p',{},row.detalhes),caption=node('small'),suggestionBox=node('div',{class:'gif-suggestions'}),choose=node('button',{type:'button'},'Escolher outro vídeo'),upload=node('button',{type:'button'},'Vídeo do aparelho'),input=node('input',{type:'file',accept:'video/*',hidden:'','aria-label':'Arquivo de vídeo de '+row.nome});
      const video=node('video',{muted:'',playsinline:'',loop:'',preload:'none','aria-label':'Demonstração de '+row.nome});video.muted=true;
      const resolution=match().resolve(row,videos,mode,prefs[choiceKey(row.nome)]),card={row,article,video,caption,choose,upload,suggestionBox,suggestions:resolution.suggestions,asset:null,localURL:null,visible:false};
      if(row.compound)text.append(node('small',{class:'gif-block'},'Bloco '+row.label.replace(/[a-z]$/,'')+' · '+row.compound));
      resolution.suggestions.forEach(asset=>{const button=node('button',{type:'button'},'Usar '+themes[asset.collection].name+': '+asset.name);button.onclick=()=>selectAsset(card,asset);suggestionBox.append(button);});
      choose.onclick=()=>openPicker(card);
      upload.onclick=()=>input.click();input.onchange=()=>{const chosen=input.files?.[0];if(!chosen||job)return;if((!chosen.type.startsWith('video/')&&!/\.(mp4|m4v|mov|webm)$/i.test(chosen.name))||chosen.size>100*1048576){controls.status.textContent='Escolha um vídeo de até 100 MB.';return;}setVideo(card,{name:chosen.name,collection:mode,localURL:URL.createObjectURL(chosen)},'Usado somente neste GIF');readiness();};
      video.onerror=()=>{if(card.asset&&!job)card.caption.textContent='A prévia não carregou. Você pode tentar Gerar GIF para carregar a demonstração novamente.';};
      text.append(name,details,caption,suggestionBox,choose,upload,input);article.append(text,video);controls.list.append(article);cards.push(card);setVideo(card,resolution.video,resolution.reason);observer.observe(article);
    });readiness();
  }
  function openPicker(card){
    const picker=node('dialog',{class:'gif-video-picker','aria-label':'Escolher vídeo para '+card.row.nome});
    const title=node('h3',{},card.row.nome),search=node('input',{type:'search','aria-label':'Buscar demonstração',placeholder:'Nome, aparelho ou abreviação'});
    const library=node('select',{'aria-label':'Biblioteca da demonstração'}),group=node('select',{'aria-label':'Grupo muscular da demonstração'}),gender=node('select',{'aria-label':'Versão da demonstração'});
    const filters=node('div',{class:'gif-picker-filters'}),status=node('p',{class:'gif-picker-count',role:'status'}),all=node('button',{type:'button'},'Ver todos os vídeos'),list=node('div',{class:'gif-picker-results'}),close=node('button',{type:'button'},'Fechar');
    library.append(node('option',{value:mode},themes[mode].name),node('option',{value:mode==='cm'?'gymfaster':'cm'},themes[mode==='cm'?'gymfaster':'cm'].name));search.value=card.row.nome;
    function refreshFilters(){
      const pool=videos.filter(v=>v.collection===library.value);group.replaceChildren(node('option',{value:''},'Todos os grupos'));gender.replaceChildren(node('option',{value:''},'Todas as versões'));
      [...new Set(pool.map(v=>v.group))].sort((a,b)=>a.localeCompare(b,'pt-BR')).forEach(value=>group.append(node('option',{value},value)));
      [...new Set(pool.map(v=>v.gender))].sort().forEach(value=>gender.append(node('option',{value},value)));gender.hidden=library.value==='cm';update();
    }
    function update(){
      list.replaceChildren();const libraryPool=videos.filter(v=>v.collection===library.value),pool=libraryPool.filter(v=>(!group.value||v.group===group.value)&&(!gender.value||v.gender===gender.value));
      const query=search.value.trim(),ranked=query?match().rank(query,pool,library.value).map(r=>r.video):pool;
      const tokens=match().canonical(query).split(' ').filter(Boolean),remaining=query?pool.filter(v=>tokens.every(word=>match().canonical(v.name).includes(word))):[];
      const seen=new Set(),found=[...ranked,...remaining].filter(v=>{if(seen.has(v.id))return false;seen.add(v.id);return true;});
      status.textContent=found.length+' resultados · '+libraryPool.length+' vídeos na biblioteca';
      if(!found.length)list.append(node('p',{},'Tente menos palavras, escolha outro grupo ou toque em Ver todos os vídeos.'));
      found.forEach(asset=>{const button=node('button',{type:'button','data-video-id':asset.id},asset.name+' · '+(asset.gender==='CM'?'CM':asset.gender));button.onclick=()=>{selectAsset(card,asset);picker.close();};list.append(button);});
    }
    all.onclick=()=>{search.value='';group.value='';gender.value='';update();};search.oninput=update;library.onchange=refreshFilters;group.onchange=update;gender.onchange=update;close.onclick=()=>picker.close();
    filters.append(group,gender);picker.append(title,search,library,filters,status,all,list,close);document.body.append(picker);picker.onclose=()=>picker.remove();refreshFilters();picker.showModal();
  }
  async function loadCatalogs(){if(!catalogPromise)catalogPromise=Promise.all(['cmfit-catalog.json?v=1','gymfaster-catalog.json?v=2'].map(async url=>{const response=await fetch(url);if(!response.ok)throw Error('Catálogo indisponível');return response.json();})).then(([cm,gym])=>videos=[...cm.videos.map(v=>({...v,collection:'cm'})),...gym.videos.map(v=>({...v,collection:'gymfaster'}))]).catch(error=>{catalogPromise=null;throw error;});return catalogPromise;}
  async function open(library=mode){
    if(!integration||job)return;if(!dialog)create();const token=++sequence;focusReturn=document.activeElement;mode=themes[library]?library:'gymfaster';workout=integration.read();controls.section.replaceChildren();workout.sections.forEach(s=>controls.section.append(node('option',{value:s.id},s.title)));selected=workout.sections.find(s=>s.id==='A')||workout.sections[0];controls.section.value=selected?.id||'';controls.generate.disabled=true;if(!dialog.open)dialog.showModal();controls.status.textContent='Carregando as bibliotecas CM e GymFaster…';
    try{await loadCatalogs();if(dialog.open&&token===sequence)render();}catch(error){controls.status.textContent='Não foi possível carregar as bibliotecas. Feche e tente novamente.';}
  }
  function check(active){if(active.cancelled||active!==job||!dialog.open)throw Error('Geração cancelada.');}
  function mediaEvent(video,event,active,action){return new Promise((resolve,reject)=>{let settled=false;const timeout=setTimeout(()=>finish(Error('Não foi possível ler o vídeo. Confira a conexão e tente novamente.')),15000),poll=setInterval(()=>{try{check(active);}catch(error){finish(error);}},100);const done=()=>finish(),failed=()=>{console.warn('GIF decoder',active.currentName,video.error?.code,video.error?.message);finish(Error('Não foi possível ler '+(active.currentName||'esta demonstração')+'. Escolha outro vídeo ou um arquivo MP4.'));};function finish(error){if(settled)return;settled=true;clearTimeout(timeout);clearInterval(poll);video.removeEventListener(event,done);video.removeEventListener('error',failed);error?reject(error):resolve();}video.addEventListener(event,done,{once:true});video.addEventListener('error',failed,{once:true});try{action();}catch(error){finish(error);}});}
  async function loadDecoder(url,active){const video=active.decoder;await mediaEvent(video,'loadeddata',active,()=>{video.src=url;video.preload='auto';video.load();});if(!Number.isFinite(video.duration)||video.duration<=0)throw Error('A duração de um vídeo não foi reconhecida. Escolha outro arquivo.');return video;}
  async function seek(video,time,active){check(active);if(Math.abs(video.currentTime-time)>0.0001||video.readyState<2)await mediaEvent(video,'seeked',active,()=>{video.currentTime=time;});check(active);if(Math.abs(video.currentTime-time)>0.08)throw Error('Não foi possível avançar o movimento. Tente novamente.');await new Promise(resolve=>requestAnimationFrame(resolve));check(active);}
  function send(active,data,transfers=[]){return new Promise((resolve,reject)=>{let settled=false;const target=active.worker,timeout=setTimeout(()=>finish(Error('A geração demorou demais. Tente um treino menor.')),120000),poll=setInterval(()=>{try{check(active);}catch(error){finish(error);}},100);const response=event=>{if(event.data.type==='progress'){controls.status.textContent='Finalizando GIF: '+event.data.percent+'%';return;}event.data.type==='error'?finish(Error(event.data.message)):finish(null,event.data);},failed=()=>finish(Error('Não foi possível iniciar o gerador. Recarregue o treino36 e tente novamente.'));function finish(error,value){if(settled)return;settled=true;clearTimeout(timeout);clearInterval(poll);target.removeEventListener('message',response);target.removeEventListener('error',failed);error?reject(error):resolve(value);}target.addEventListener('message',response);target.addEventListener('error',failed);target.postMessage(data,transfers);});}
  function wrap(ctx,text,x,y,width,step){let line='';for(const word of text.split(/\s+/)){const next=line?line+' '+word:word;if(ctx.measureText(next).width>width&&line){ctx.fillText(line,x,y);y+=step;line=word;}else line=next;}if(line)ctx.fillText(line,x,y);return y+step;}
  function lineCount(ctx,text,width){let n=1,line='';for(const word of text.split(/\s+/)){const next=line?line+' '+word:word;if(ctx.measureText(next).width>width&&line){n++;line=word;}else line=next;}return n;}
  function layout(ctx){ctx.font='bold 29px Arial';layoutHeader=Math.max(HEADER,88+lineCount(ctx,selected.title,744)*32+55);let top=layoutHeader;cards.forEach(c=>{ctx.font='bold 23px Arial';const names=lineCount(ctx,c.row.label+'. '+c.row.nome,358);ctx.font='20px Arial';c.top=top;c.height=Math.max(CARD,Math.max(38+names*28+13,120)+lineCount(ctx,c.row.detalhes,358)*26+25);top+=c.height;});return top+50;}
  function paint(ctx,canvas){const t=themes[mode];ctx.fillStyle=t.bg;ctx.fillRect(0,0,WIDTH,canvas.height);ctx.fillStyle=t.green;ctx.fillRect(0,0,WIDTH,7);ctx.font='bold 23px Arial';ctx.fillText('CAIO MACÊDO · PERSONAL TRAINER',28,43);ctx.fillStyle=t.ink;ctx.font='bold 29px Arial';wrap(ctx,selected.title,28,88,744,32);ctx.font='19px Arial';ctx.fillText(workout.student.slice(0,65),28,layoutHeader-29);cards.forEach(c=>{ctx.fillStyle=t.card;ctx.fillRect(20,c.top,760,c.height-12);ctx.fillStyle=t.ink;ctx.font='bold 23px Arial';const y=wrap(ctx,c.row.label+'. '+c.row.nome,36,c.top+38,358,28);ctx.fillStyle=t.green;ctx.font='20px Arial';wrap(ctx,c.row.detalhes,36,Math.max(y+13,c.top+120),358,26);});ctx.fillStyle=t.green;ctx.font='17px Arial';const sources=new Set(cards.map(c=>c.asset.localURL?'arquivo local':c.asset.kind==='created-example'?'exemplo criado':themes[c.asset.collection].name));ctx.fillText('Demonstrações '+[...sources].join(' + ')+' · Treino '+selected.id,28,canvas.height-20);}
  function drawSlot(ctx,video,asset){
    ctx.fillStyle=asset.collection==='cm'?'#000':'#fff';ctx.fillRect(0,0,SLOT_W,SLOT_H);
    const scale=Math.min(SLOT_W/video.videoWidth,SLOT_H/video.videoHeight),w=video.videoWidth*scale,h=video.videoHeight*scale;ctx.drawImage(video,(SLOT_W-w)/2,(SLOT_H-h)/2,w,h);
    if(cmWhiteInk(asset)){
      const frame=ctx.getImageData(0,0,SLOT_W,SLOT_H),pixels=frame.data;
      // Same sRGB transform as the preview's invert(1) hue-rotate(180deg).
      // Black/white swap while the muscle highlight retains its green hue.
      for(let i=0;i<pixels.length;i+=4){const r=pixels[i],g=pixels[i+1],b=pixels[i+2],shift=255-2*(.213*r+.715*g+.072*b);pixels[i]=r+shift;pixels[i+1]=g+shift;pixels[i+2]=b+shift;}
      ctx.putImageData(frame,0,0);return frame;
    }
  }
  async function generateGIF(){
    if(job||!cards.length)return;const missing=cards.filter(c=>!c.asset);if(missing.length){controls.status.textContent='Falta confirmar: '+missing.map(c=>c.row.nome).join(', ')+'. Toque numa sugestão ou escolha um vídeo.';missing[0].article.scrollIntoView({block:'center'});return;}if(cards.length>20){controls.status.textContent='Use até 20 demonstrações por GIF. Divida esta seção.';return;}
    clearResult();const active={cancelled:false,abort:new AbortController(),worker:null,decoder:node('video',{muted:'',playsinline:'',preload:'auto','aria-hidden':'true',class:'gif-decoder'}),urls:[]};active.decoder.muted=true;job=active;dialog.append(active.decoder);setBusy(true);cards.forEach(c=>{c.video.pause();c.video.removeAttribute('src');c.video.load();});
    try{
      const canvas=document.createElement('canvas');canvas.width=WIDTH;const ctx=canvas.getContext('2d',{willReadFrequently:true}),height=layout(ctx);if(height>12000)throw Error('A ficha ficou muito longa. Divida o treino para gerar o GIF.');canvas.height=height;paint(ctx,canvas);const base=ctx.getImageData(0,0,WIDTH,height).data.buffer;
      const slot=document.createElement('canvas');slot.width=SLOT_W;slot.height=SLOT_H;const sc=slot.getContext('2d',{willReadFrequently:true});const unique=new Map();cards.forEach(c=>{c.key=assetURL(c.asset);if(!unique.has(c.key))unique.set(c.key,{asset:c.asset,key:c.key,url:null});});
      let index=0;
      for(const item of unique.values()){
        check(active);controls.status.textContent='Carregando movimento '+(++index)+'/'+unique.size+'…';
        const timer=setTimeout(()=>active.abort.abort(),60000);let response;try{response=await fetch(item.key,{signal:active.abort.signal,cache:'force-cache'});if(!response.ok)throw Error('Não foi possível carregar '+item.asset.name+'. Tente novamente.');const blob=await response.blob();item.url=URL.createObjectURL(blob);active.urls.push(item.url);}finally{clearTimeout(timer);}
        active.currentName=item.asset.name;const video=await loadDecoder(item.url,active);await seek(video,0.001,active);drawSlot(sc,video,item.asset);cards.filter(c=>c.key===item.key).forEach(c=>ctx.drawImage(slot,410,c.top+5));
      }
      check(active);const sample=ctx.getImageData(0,0,WIDTH,height).data.buffer;active.worker=new Worker('workout-gif-worker.js?v=2');await send(active,{type:'init',width:WIDTH,height,count:FRAMES,base,sample,slots:cards.map(c=>({key:c.key,x:410,y:c.top+5,width:SLOT_W,height:SLOT_H}))},[base,sample]);
      index=0;
      for(const item of unique.values()){
        active.currentName=item.asset.name;const video=await loadDecoder(item.url,active);
        for(let frame=0;frame<FRAMES;frame++){
          await seek(video,Math.max(0.001,frame/FRAMES*video.duration),active);const converted=drawSlot(sc,video,item.asset);const pixels=(converted||sc.getImageData(0,0,SLOT_W,SLOT_H)).data.buffer;await send(active,{type:'cache',key:item.key,frame,pixels},[pixels]);controls.status.textContent='Preparando movimento '+(index+1)+'/'+unique.size+' · '+Math.round((index*FRAMES+frame+1)/(unique.size*FRAMES)*85)+'%';
        }index++;
      }
      controls.status.textContent='Finalizando GIF…';const result=await send(active,{type:'finish'});check(active);
      file=new File([result.bytes],'treino_'+selected.id+'_'+mode+'_'+workout.student.slice(0,80).replace(/[^a-z0-9áéíóúâêôãõç_-]+/gi,'_')+'.gif',{type:'image/gif'});blobURL=URL.createObjectURL(file);controls.result.replaceChildren(node('img',{src:blobURL,alt:'Treino '+selected.id+' · '+themes[mode].name+' em movimento'}));controls.result.hidden=false;controls.share.hidden=false;controls.download.hidden=false;controls.status.textContent='GIF pronto · '+themes[mode].name+' · 5 segundos · '+(file.size/1048576).toFixed(1)+' MB. Confira e compartilhe.';controls.result.scrollIntoView({block:'start'});
    }catch(error){if(dialog.open&&job===active)controls.status.textContent=active.cancelled?'Geração cancelada. Você pode tentar novamente.':error.name==='AbortError'?'O carregamento demorou demais. Verifique a conexão e tente novamente.':error.message||'Não foi possível gerar o GIF. Tente novamente.';}
    finally{active.worker?.terminate();active.decoder.pause();active.decoder.removeAttribute('src');active.decoder.load();active.decoder.remove();active.urls.forEach(url=>URL.revokeObjectURL(url));if(job===active){job=null;setBusy(false);if(dialog.open)cards.forEach(playVisible);}}
  }
  return {configure,open};
})();
