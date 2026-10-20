/* Browser-only document reading. No pupil document is uploaded to a service. */
window.CompositionOCR=(()=>{
  const scripts=new Map();let workerPromise,pdfPromise;
  function script(url){if(!scripts.has(url))scripts.set(url,new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=url;s.onload=resolve;s.onerror=()=>{scripts.delete(url);s.remove();reject(Error('Não foi possível carregar o leitor. Verifique a conexão e tente novamente.'));};document.head.append(s);}));return scripts.get(url);}
  async function worker(progress){
    if(!workerPromise)workerPromise=(async()=>{if(!window.Tesseract)await script('https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js');return Tesseract.createWorker('por+eng',1,{logger:m=>{if(m.status==='recognizing text')currentProgress?.('Lendo imagem: '+Math.round(m.progress*100)+'%');}});})().catch(error=>{workerPromise=null;throw error;});
    return workerPromise;
  }
  let currentProgress=null,busy=false;
  async function recognize(canvas,progress){currentProgress=progress;const w=await worker(progress);await w.setParameters({tessedit_pageseg_mode:'3',preserve_interword_spaces:'1'});const result=await w.recognize(canvas);const data=result.data;const lines=data.lines||data.blocks?.flatMap(b=>b.paragraphs?.flatMap(p=>p.lines||[])||[])||[];return lines.length?lines.map(line=>({text:line.text,confidence:line.confidence,words:(line.words||[]).map(word=>({text:word.text,confidence:word.confidence,...word.bbox}))})):data.text.split('\n').filter(t=>t.trim()).map(text=>({text,confidence:data.confidence||0}));}
  async function imageCanvas(file){
    let bitmap;try{bitmap=await createImageBitmap(file,{imageOrientation:'from-image'});}catch(error){const url=URL.createObjectURL(file);try{bitmap=await new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(Error('Imagem não suportada. Exporte como JPG ou PNG.'));image.src=url;});}finally{URL.revokeObjectURL(url);}}
    const w=bitmap.width||bitmap.naturalWidth,h=bitmap.height||bitmap.naturalHeight;if(!w||!h)throw Error('A imagem está vazia.');
    const scale=Math.min(2400/w,4800/h,Math.max(1,1800/w)),canvas=document.createElement('canvas');canvas.width=Math.round(w*scale);canvas.height=Math.round(h*scale);const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close?.();
    // Trim a large empty bottom area in spreadsheet screenshots, preserving all printed rows.
    const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);let last=canvas.height-1;
    while(last>canvas.height*.25){let ink=0;for(let x=0;x<canvas.width;x+=8){const at=(last*canvas.width+x)*4;if(Math.min(...pixels.data.slice(at,at+3))<235)ink++;}if(ink>2)break;last-=4;}
    if(last<canvas.height*.8){const cropped=document.createElement('canvas');cropped.width=canvas.width;cropped.height=Math.min(canvas.height,last+40);cropped.getContext('2d').drawImage(canvas,0,0);canvas.width=canvas.height=1;return cropped;}return canvas;
  }
  async function pdf(){if(!pdfPromise)pdfPromise=(async()=>{if(!window.pdfjsLib)await script('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js');pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';return pdfjsLib;})().catch(e=>{pdfPromise=null;throw e;});return pdfPromise;}
  async function read(file,progress=()=>{},options={}){
    if(busy)throw Error('Aguarde a leitura atual terminar.');if(file.size>25*1024*1024)throw Error('Use um arquivo de até 25 MB.');busy=true;
    try{
      const signature=new Uint8Array(await file.slice(0,5).arrayBuffer()),isPdf=String.fromCharCode(...signature)==='%PDF-';
      let rows=[];
      if(isPdf){progress('Abrindo PDF…');const lib=await pdf(),document=await lib.getDocument({data:new Uint8Array(await file.arrayBuffer()),isEvalSupported:false}).promise;
        try{if(document.numPages>15)throw Error('Use um PDF de até 15 páginas ou exporte apenas as páginas do laudo.');
          for(let n=1;n<=document.numPages;n++){
            progress('Lendo página '+n+' de '+document.numPages+'…');const page=await document.getPage(n),content=await page.getTextContent();
            const words=content.items.filter(i=>i.str?.trim()).map(i=>({text:i.str,x0:i.transform[4],x1:i.transform[4]+i.width,y0:-i.transform[5],y1:-i.transform[5]+Math.abs(i.height||10),confidence:100}));
            const native=CompositionReader.rowsFromWords(words);if(options.kind==='text'?native.map(r=>r.text).join(' ').replace(/[^a-zA-ZÀ-ÿ]/g,'').length>=40:CompositionReader.parse(native).candidates.length>=3){rows.push(...native);page.cleanup();continue;}
            const viewport=page.getViewport({scale:Math.min(2.5,2100/page.getViewport({scale:1}).width)}),canvas=window.document.createElement('canvas');canvas.width=Math.round(viewport.width);canvas.height=Math.round(viewport.height);try{await page.render({canvasContext:canvas.getContext('2d'),viewport}).promise;rows.push(...await recognize(canvas,progress));}finally{canvas.width=canvas.height=1;page.cleanup();}
          }
        }finally{await document.destroy();}
      }else{
        if(!file.type.startsWith('image/'))throw Error('Selecione uma foto, imagem ou PDF.');progress('Preparando imagem…');const canvas=await imageCanvas(file);try{rows=await recognize(canvas,progress);}finally{canvas.width=canvas.height=1;}
      }
      if(options.kind==='text')return {text:rows.map(row=>row.text).join('\n'),rows,filename:file.name};
      const result=CompositionReader.parse(rows);result.filename=file.name;return result;
    }finally{busy=false;currentProgress=null;}
  }
  return {read,imageCanvas};
})();
