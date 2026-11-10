/* Compact inline player; native mobile video controls stay out of the preview. */
window.WorkoutVideoPreview=(()=>{
  let dialog,player,returnFocus,colorControl,currentAsset;
  const make=(tag,className,text)=>{const e=document.createElement(tag);if(className)e.className=className;if(text)e.textContent=text;return e;};
  function createPlayer(asset,options={}){
    const element=make('div','movement-player'),frame=make('div','movement-frame'),video=make('video'),tools=make('div','movement-controls'),play=make('button'),restart=make('button','','↺ Reiniciar'),sound=make('button','','Som desligado'),expand=make('button','','⤢ Ampliar'),range=make('input','movement-progress'),time=make('span','movement-time','0:00');
    video.controls=false;video.loop=true;video.muted=true;video.playsInline=true;video.setAttribute('webkit-playsinline','');video.preload='metadata';video.disablePictureInPicture=true;video.setAttribute('aria-label',asset.name);
    range.type='range';range.min='0';range.max='1000';range.value='0';range.setAttribute('aria-label','Posição do vídeo');range.disabled=true;
    for(const button of [play,restart,sound,expand])button.type='button';
    play.setAttribute('aria-label','Reproduzir vídeo');restart.setAttribute('aria-label','Reiniciar vídeo');sound.setAttribute('aria-label','Ativar som');sound.setAttribute('aria-pressed','false');expand.setAttribute('aria-label','Ampliar prévia');expand.setAttribute('aria-pressed','false');
    const clock=seconds=>Math.floor((seconds||0)/60)+':'+String(Math.floor((seconds||0)%60)).padStart(2,'0');
    const refresh=()=>{play.textContent=video.paused?'▶ Reproduzir':'Pausar';play.setAttribute('aria-label',video.paused?'Reproduzir vídeo':'Pausar vídeo');};
    const toggle=()=>{if(video.paused)video.play().catch(()=>{});else video.pause();};
    play.onclick=video.onclick=toggle;restart.onclick=()=>{video.currentTime=0;video.play().catch(()=>{});};
    sound.onclick=()=>{video.muted=!video.muted;sound.textContent=video.muted?'Som desligado':'Som ligado';sound.setAttribute('aria-label',video.muted?'Ativar som':'Desativar som');sound.setAttribute('aria-pressed',String(!video.muted));};
    expand.onclick=()=>{if(options.onExpand){const enlarged=options.onExpand();expand.textContent=enlarged?'↙ Reduzir':'⤢ Ampliar';expand.setAttribute('aria-label',enlarged?'Reduzir prévia':'Ampliar prévia');expand.setAttribute('aria-pressed',String(enlarged));}else{video.pause();open(asset,expand);}};
    range.oninput=()=>{if(Number.isFinite(video.duration)&&video.duration>0)video.currentTime=Number(range.value)/1000*video.duration;};
    video.onplay=video.onpause=refresh;
    video.onloadedmetadata=()=>{range.disabled=false;time.textContent=clock(video.currentTime)+' / '+clock(video.duration);};
    video.ontimeupdate=()=>{if(Number.isFinite(video.duration)&&video.duration>0){range.value=String(video.currentTime/video.duration*1000);time.textContent=clock(video.currentTime)+' / '+clock(video.duration);}};
    video.onerror=()=>options.onError?.();
    frame.append(video);tools.append(play,restart,sound,expand);element.append(frame,range,time,tools);refresh();
    WorkoutVideoColors.apply(video,asset);video.src=asset.localURL||asset.media||(asset.collection==='cm'?'cmfit-media/':'gymfaster-media/')+asset.id+'.mp4';
    return {element,video,play(){video.play().catch(()=>{});},dispose(){video.pause();video.removeAttribute('src');video.load();}};
  }
  function closeVideo(){player?.dispose();dialog.classList.remove('movement-expanded');if(returnFocus?.isConnected)returnFocus.focus({preventScroll:true});}
  function open(asset,focusTarget,onSelect){
    if(!dialog){
      dialog=document.createElement('dialog');dialog.id='movementPreview';dialog.setAttribute('aria-labelledby','movementPreviewTitle');
      const header=make('div','movement-heading'),title=make('h3'),close=make('button','movement-close','×'),host=make('div','movement-host'),status=make('p'),options=make('details','movement-options'),summary=make('summary','','Cor do vídeo');
      title.id='movementPreviewTitle';title.tabIndex=-1;title.autofocus=true;close.type='button';close.setAttribute('aria-label','Fechar prévia');close.onclick=()=>dialog.close();status.setAttribute('role','status');
      colorControl=WorkoutVideoColors.editor(()=>WorkoutVideoColors.apply(player.video,currentAsset));
      options.append(summary,colorControl.element);header.append(title,close);dialog.append(header,host,options,status);document.body.append(dialog);dialog.addEventListener('close',closeVideo);
    }

    player?.dispose();returnFocus=focusTarget||document.activeElement;currentAsset=asset;
    dialog.querySelector('h3').textContent=[...new Set([asset.name,asset.source||(asset.collection==='cm'?'CM':'Lyfta + GymFaster'),asset.gender!=='CM'?asset.gender:''].filter(Boolean))].join(' · ');
    dialog.querySelector('[role=status]').textContent='';dialog.classList.remove('movement-expanded');
    player=createPlayer(asset,{onExpand:()=>dialog.classList.toggle('movement-expanded'),onError:()=>{dialog.querySelector('[role=status]').textContent='Não foi possível carregar a prévia. Feche e tente novamente.';}});
    if(onSelect){const use=make('button','movement-use','✓ Usar este vídeo');use.type='button';use.onclick=()=>{dialog.close();onSelect(asset);};player.element.querySelector('.movement-controls').firstElementChild.replaceWith(use);}
    dialog.querySelector('.movement-host').replaceChildren(player.element);colorControl.setAsset(asset);
    if(!dialog.open)dialog.showModal();dialog.querySelector('h3').focus({preventScroll:true});player.play();
  }
  const eye='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>';
  const trash='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/></svg>';
  return {open,createPlayer,eye,trash};
})();
