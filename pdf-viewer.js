/* Open the PDF itself in the browser viewer, preserving the source screen. */
window.TreinoPDFViewer = {
  shareReady(doc, filename) {
    // A second, explicit tap keeps Web Share's user activation on iPhone.
    // Send only a named File: sharing a blob viewer's URL can send the site URL.
    document.getElementById('pdfShareReady')?.remove();
    doc.setProperties({title:filename.replace(/\.pdf$/i,'')});
    const file=new File([doc.output('blob')],filename,{type:'application/pdf'});
    const dialog=document.createElement('dialog');dialog.id='pdfShareReady';
    const title=document.createElement('h3');title.textContent='PDF pronto';
    const name=document.createElement('p');name.textContent=filename;
    const status=document.createElement('p');status.setAttribute('role','status');
    const share=document.createElement('button');share.type='button';share.dataset.shareFile='';share.textContent='Compartilhar PDF';
    const save=document.createElement('button');save.type='button';save.textContent='Salvar arquivo';
    const close=document.createElement('button');close.type='button';close.textContent='Fechar';close.onclick=()=>dialog.close();
    share.onclick=async()=>{
      try {
        const payload={files:[file]};
        if(!navigator.share||(navigator.canShare&&!navigator.canShare(payload))){status.textContent='Este navegador não compartilha arquivos. Salve o PDF e anexe como documento no WhatsApp.';return;}
        await navigator.share(payload);status.textContent='PDF compartilhado.';
      } catch(error) {if(error.name!=='AbortError')status.textContent='Não foi possível compartilhar. Salve o arquivo e anexe como documento no WhatsApp.';}
    };
    save.onclick=()=>{const url=URL.createObjectURL(file),link=document.createElement('a');link.href=url;link.download=filename;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);};
    dialog.append(title,name,share,save,status,close);document.body.append(dialog);dialog.showModal();
  },
  reserve() {
    // Reserve during the tap, before loading libraries or preparing photos.
    const viewer = window.open('', '_blank');
    if (viewer) {
      viewer.opener = null;
      viewer.document.title = 'Preparando PDF';
      viewer.document.body.textContent = 'Preparando PDF…';
    }
    return viewer;
  },
  close(viewer) { if (viewer && !viewer.closed) viewer.close(); },
  deliver(doc, filename, viewer) {
    if(viewer && viewer.closed)return;
    if (!viewer) {
      // Preserve access to the file when the browser blocks a new window.
      doc.save(filename);
      return;
    }
    doc.setProperties({title:filename.replace(/\.pdf$/i, '')});
    const blob = doc.output('blob');
    const url = URL.createObjectURL(new File([blob],filename,{type:'application/pdf'}));
    try { viewer.location.replace(url); }
    catch (error) { URL.revokeObjectURL(url); this.close(viewer); throw error; }
    // Keep the URL usable for sharing while the viewer is open.
    const cleanup = setInterval(() => {
      if (viewer.closed) { clearInterval(cleanup); URL.revokeObjectURL(url); }
    }, 30000);
  }
};
