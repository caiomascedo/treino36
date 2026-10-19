/* Share named PDF files without page URLs; preserve inline viewing where file sharing is unavailable. */
window.TreinoPDFViewer = {
  reserve() {
    // The direct preview's share action sends only the file, without a page URL.
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
    // Show the prepared PDF immediately; sharing is a single toolbar action.
    const dialog=document.createElement('dialog');dialog.className='pdf-file-share pdf-direct-preview';
    dialog.style.cssText='width:100%;max-width:none;height:100dvh;max-height:100dvh;box-sizing:border-box;border:0;border-radius:0;padding:0;margin:0;color:#243746;background:white;font:16px system-ui;';
    const toolbar=document.createElement('div');toolbar.style.cssText='display:flex;align-items:center;gap:8px;padding:8px;background:#f1f5f8;';
    const status=document.createElement('span');status.className='pdf-file-share-status';status.setAttribute('role','status');status.textContent='Preparando PDF…';status.style.cssText='flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px';
    const button=(label,kind,description)=>{const node=document.createElement('button');node.type='button';node.textContent=label;node.className='pdf-file-'+kind;node.setAttribute('aria-label',description);node.title=description;node.style.cssText='border:0;border-radius:8px;padding:8px 12px;font:20px system-ui;background:white;color:#243746;';return node;};
    const send=button('↥','send','Compartilhar PDF'),save=button('↓','save','Salvar PDF'),close=button('×','close','Fechar PDF');send.disabled=save.disabled=true;
    const frame=document.createElement('iframe');frame.className='pdf-inline-document';frame.title='Visualização do PDF';frame.style.cssText='display:block;width:100%;height:calc(100% - 58px);border:0;background:#555;';
    toolbar.append(status,send,save,close);dialog.append(toolbar,frame);document.body.append(dialog);
    let file=null,url=null;
    const target={closed:false,close(){if(dialog.open)dialog.close();else dialog.remove();target.closed=true;},shareFile(value){if(target.closed)return;file=value;status.textContent=file.name;save.disabled=false;let supported=false;try{supported=!!navigator.share&&(!navigator.canShare||navigator.canShare({files:[file]}));}catch(error){}send.hidden=!supported;send.disabled=!supported;url=URL.createObjectURL(file);frame.src=url;}};
    dialog.addEventListener('close',()=>{target.closed=true;file=null;frame.removeAttribute('src');if(url)URL.revokeObjectURL(url);dialog.remove();});close.onclick=()=>target.close();
    send.onclick=async()=>{if(!file)return;send.disabled=true;try{
      await navigator.share({files:[file]});
    }catch(error){if(error.name!=='AbortError'&&!target.closed)status.textContent='Não foi possível compartilhar. Tente novamente ou salve o PDF.';}
    finally{if(!target.closed)send.disabled=false;}};
    save.onclick=()=>{if(!file||!url)return;const link=document.createElement('a');link.href=url;link.download=file.name;link.click();};
    dialog.showModal();close.focus({preventScroll:true});return target;
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
