/* Display generated photos before offering an image-only save/share action. */
window.DietPhotoViewer = {
  mount(createDialog) {
    const dialog=createDialog('dietPhotoPreviewDialog','Foto da dieta',
      '<div class="diet-photo-toolbar"><button type="button" id="dietPhotoExpandBtn" aria-pressed="false">⛶ Ampliar foto</button><button type="button" data-close>Fechar</button></div>'+
      '<div id="dietPhotoImages"></div><p id="dietPhotoPreviewStatus" role="status"></p>'+
      '<div class="dialog-actions"><button type="button" id="dietPhotoSaveBtn" class="primary" disabled>Salvar / enviar foto</button><button type="button" id="dietPhotoDownloadBtn" hidden>Baixar imagem</button></div>');
    const images=dialog.querySelector('#dietPhotoImages'),status=dialog.querySelector('#dietPhotoPreviewStatus');
    const save=dialog.querySelector('#dietPhotoSaveBtn'),download=dialog.querySelector('#dietPhotoDownloadBtn'),expand=dialog.querySelector('#dietPhotoExpandBtn');
    let generation=0,items=[];
    function release(){for(const item of items)URL.revokeObjectURL(item.url);items=[];images.replaceChildren();}
    dialog.addEventListener('close',()=>{generation++;release();save.disabled=true;});
    expand.onclick=()=>{const expanded=dialog.classList.toggle('diet-photo-expanded');expand.setAttribute('aria-pressed',String(expanded));expand.textContent=expanded?'↙ Minimizar foto':'⛶ Ampliar foto';};
    function downloadImages(){for(const item of items){const link=document.createElement('a');link.href=item.url;link.download=item.name;link.hidden=true;document.body.append(link);link.click();link.remove();}}
    download.onclick=downloadImages;
    save.onclick=async()=>{
      if(!items.length)return;
      const token=generation,files=items.map(item=>new File([item.blob],item.name,{type:'image/png'}));
      let supported=false;
      try{supported=!!navigator.share&&(!navigator.canShare||navigator.canShare({files}));}catch(error){}
      if(!supported){downloadImages();return;}
      save.disabled=true;
      try{await navigator.share({files});}
      catch(error){if(token===generation&&error.name!=='AbortError'){status.textContent='Não foi possível abrir o compartilhamento. Você pode baixar a imagem ou tocar e segurar a foto para salvar.';download.hidden=false;}}
      finally{if(token===generation)save.disabled=false;}
    };
    return {
      open(name){
        release();const token=++generation;save.disabled=true;download.hidden=true;status.textContent='Gerando foto…';
        dialog.querySelector('h3').textContent=name?'Foto da dieta — '+name:'Foto da dieta';dialog.showModal();
        const session={
          get closed(){return token!==generation||!dialog.open;},
          add(blob,filename){
            if(session.closed)return;
            const url=URL.createObjectURL(blob),img=document.createElement('img');
            img.src=url;img.alt='Foto da dieta'+(items.length?' · parte '+(items.length+1):'');img.loading='lazy';img.decoding='async';
            items.push({blob,name:filename,url});images.append(img);
          },
          ready(){if(!session.closed&&items.length){save.disabled=false;status.textContent='Toque e segure a foto para salvar, ou use o botão abaixo.';}},
          error(message){if(!session.closed)status.textContent=message;}
        };
        return session;
      },
      close(){if(dialog.open)dialog.close();}
    };
  }
};
