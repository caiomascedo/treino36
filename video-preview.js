/* Read-only movement preview. Choosing a video remains a separate action. */
window.WorkoutVideoPreview=(()=>{
  let dialog,video,returnFocus;
  function closeVideo(){video.pause();video.removeAttribute('src');video.load();if(returnFocus?.isConnected)returnFocus.focus();}
  function open(asset,focusTarget){
    if(!dialog){
      dialog=document.createElement('dialog');dialog.id='movementPreview';dialog.setAttribute('aria-labelledby','movementPreviewTitle');
      const title=document.createElement('h3');title.id='movementPreviewTitle';video=document.createElement('video');video.controls=true;video.loop=true;video.muted=true;video.playsInline=true;video.preload='metadata';
      const status=document.createElement('p');status.setAttribute('role','status');
      const close=document.createElement('button');close.type='button';close.textContent='Fechar prévia';close.onclick=()=>dialog.close();
      dialog.append(title,video,status,close);document.body.append(dialog);dialog.addEventListener('close',closeVideo);
      video.onerror=()=>{status.textContent='Não foi possível carregar a prévia. Feche e tente novamente.';};
    }
    returnFocus=focusTarget||document.activeElement;dialog.querySelector('h3').textContent=asset.name+' · '+(asset.collection==='cm'?'CM':'GymFaster')+(asset.gender&&asset.gender!=='CM'?' · '+asset.gender:'');dialog.querySelector('[role=status]').textContent='';
    video.classList.toggle('cm-ink-on-white',asset.collection==='cm');video.src=asset.media||(asset.collection==='cm'?'cmfit-media/':'gymfaster-media/')+asset.id+'.mp4';
    if(!dialog.open)dialog.showModal();video.play().catch(()=>{});
  }
  const eye='<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></svg>';
  return {open,eye};
})();
