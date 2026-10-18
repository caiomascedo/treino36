/* Share named PDF files without page URLs; preserve inline viewing where file sharing is unavailable. */
window.TreinoPDFViewer = {
  reserve() {
    // Prefer sharing only the file; the browser's page share can add its blob URL.
    try {if(navigator.share&&(!navigator.canShare||navigator.canShare({files:[new File(['%PDF-1.4\n%%EOF'], 'treino.pdf', {type:'application/pdf'})]})))return this.reserveShare();}catch(error){}
    // Reserve during the tap, before loading libraries or preparing photos.
    const viewer = window.open('', '_blank');
    if (viewer) {
      viewer.opener = null;
      viewer.document.title = 'Preparando PDF';
      viewer.document.body.textContent = 'Preparando PDF…';
    }
    return viewer;
  },
  reserveShare() {
    // Keep a fresh user tap for navigator.share after asynchronous PDF generation.
    const dialog=document.createElement('dialog');dialog.className='pdf-file-share';
    dialog.style.cssText='max-width:360px;width:calc(100% - 32px);box-sizing:border-box;border:0;border-radius:14px;padding:20px;color:#243746;background:white;font:16px system-ui;';
    const heading=document.createElement('h3');heading.textContent='Enviar PDF';heading.style.margin='0 0 12px';
    const status=document.createElement('p');status.className='pdf-file-share-status';status.setAttribute('role','status');status.textContent='Preparando PDF…';status.style.cssText='overflow-wrap:anywhere;font-size:14px;';
    const actions=document.createElement('div');actions.style.cssText='display:flex;flex-wrap:wrap;gap:8px';
    const button=(label,kind)=>{const node=document.createElement('button');node.type='button';node.textContent=label;node.className='pdf-file-'+kind;node.style.cssText='border:0;border-radius:8px;padding:10px 12px;font:inherit;background:#eaf0f3;color:#243746;';return node;};
    const send=button('Enviar PDF','send'),save=button('Salvar arquivo','save'),close=button('Fechar','close');send.disabled=true;save.disabled=true;send.style.background='#1e6f3f';send.style.color='white';
    actions.append(send,save,close);dialog.append(heading,status,actions);document.body.append(dialog);
    let file=null;
    const target={closed:false,close(){if(dialog.open)dialog.close();else dialog.remove();target.closed=true;file=null;},shareFile(value){if(target.closed)return;file=value;status.textContent=file.name;save.disabled=false;let supported=false;try{supported=!!navigator.share&&(!navigator.canShare||navigator.canShare({files:[file]}));}catch(error){}send.hidden=!supported;send.disabled=!supported;if(!supported)status.textContent+=' — Salve o arquivo para anexar na conversa.';else if(navigator.userActivation?.isActive!==false)send.click();}};
    dialog.addEventListener('close',()=>{target.closed=true;file=null;dialog.remove();});close.onclick=()=>target.close();
    send.onclick=async()=>{if(!file)return;send.disabled=true;try{
      // Files only: adding text or url here puts the site address in the message.
      await navigator.share({files:[file]});
      target.close();
    }catch(error){if(error.name==='AbortError')target.close();else if(!target.closed)status.textContent='Não foi possível abrir o compartilhamento. Tente novamente ou salve o arquivo.';}
    finally{if(!target.closed)send.disabled=false;}};
    save.onclick=()=>{if(!file)return;const url=URL.createObjectURL(file),link=document.createElement('a');link.href=url;link.download=file.name;link.click();setTimeout(()=>URL.revokeObjectURL(url),30000);};
    dialog.showModal();return target;
  },
  close(viewer) { if (viewer && !viewer.closed) viewer.close(); },
  deliver(doc, filename, viewer) {
    if(viewer && typeof viewer.shareFile==='function'){
      if(!viewer.closed){doc.setProperties({title:filename.replace(/\.pdf$/i,'')});viewer.shareFile(new File([doc.output('blob')],filename,{type:'application/pdf'}));}
      return;
    }
    if (!viewer || viewer.closed) {
      // Preserve access to the file when the browser blocks a new window.
      doc.save(filename);
      return;
    }
    doc.setProperties({title:filename.replace(/\.pdf$/i, '')});
    const blob = doc.output('blob');
    const url = URL.createObjectURL(blob.type === 'application/pdf' ? blob : new Blob([blob], {type:'application/pdf'}));
    try { viewer.location.replace(url); }
    catch (error) { URL.revokeObjectURL(url); this.close(viewer); throw error; }
    // Keep the URL usable for sharing while the viewer is open.
    const cleanup = setInterval(() => {
      if (viewer.closed) { clearInterval(cleanup); URL.revokeObjectURL(url); }
    }, 30000);
  }
};
