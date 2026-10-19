/* Manual photographic references. Original images and normalized guide geometry stay separate. */
window.PostureEditor=(()=>{
  const clamp=n=>Math.min(1,Math.max(0,n));
  const defaultLogo='assets/caio-macedo-logo.png',logoKey='treinoPostureLogo',logoImages=new Map();
  const validLogo=src=>typeof src==='string'&&(src===defaultLogo||/^data:image\/png;base64,[a-z0-9+/=]+$/i.test(src));
  function loadLogo(src){if(!validLogo(src))return Promise.reject(Error('Use uma logo em PNG.'));if(!logoImages.has(src)){const img=new Image();img.src=src;logoImages.set(src,img.decode().then(()=>img).catch(error=>{logoImages.delete(src);throw error;}));}return logoImages.get(src);}
  const defaults=()=>({grid:false,spacing:10,gridColor:'#10b981',gridThickness:1,gridTransparency:50,showHandles:true,lines:[],logo:null});
  function normalize(value){
    const state=defaults();if(!value||typeof value!=='object')return state;
    state.grid=value.grid===true;state.spacing=[5,10,15,20,25].includes(Number(value.spacing))?Number(value.spacing):10;
    state.gridColor=/^#[0-9a-f]{6}$/i.test(value.gridColor)?value.gridColor:state.gridColor;state.showHandles=value.showHandles!==false;
    if(Number.isFinite(value.gridThickness))state.gridThickness=Math.min(6,Math.max(1,value.gridThickness));
    if(Number.isFinite(value.gridTransparency))state.gridTransparency=Math.min(100,Math.max(0,value.gridTransparency));
    if(value.logo&&validLogo(value.logo.src)&&[value.logo.x,value.logo.y,value.logo.width].every(Number.isFinite))state.logo={src:value.logo.src,x:clamp(value.logo.x),y:clamp(value.logo.y),width:Math.min(.9,Math.max(.05,value.logo.width))};
    if(Array.isArray(value.lines))state.lines=value.lines.slice(0,20).filter(line=>line&&['vertical','horizontal','ruler','line'].includes(line.kind)&&[line.x1,line.y1,line.x2,line.y2].every(Number.isFinite)).map((line,i)=>({id:String(line.id||i),kind:line.kind,x1:clamp(line.x1),y1:clamp(line.y1),x2:clamp(line.x2),y2:clamp(line.y2),color:/^#[0-9a-f]{6}$/i.test(line.color)?line.color:'#ef4444'}));
    return state;
  }
  function angle(line,w,h){if(!line||Math.hypot((line.x2-line.x1)*w,(line.y2-line.y1)*h)<.001)return null;return Math.atan2((line.y2-line.y1)*h,(line.x2-line.x1)*w)*180/Math.PI;}
  function segments(line,w,h){
    const x1=line.x1*w,y1=line.y1*h,x2=line.x2*w,y2=line.y2*h,result=[[x1,y1,x2,y2]];
    if(line.kind==='ruler'){const length=Math.hypot(x2-x1,y2-y1)||1,dx=-(y2-y1)/length,dy=(x2-x1)/length;for(let i=0;i<=10;i++){const x=x1+(x2-x1)*i/10,y=y1+(y2-y1)*i/10,t=w*(i%5===0?.018:.009);result.push([x-dx*t,y-dy*t,x+dx*t,y+dy*t]);}}
    return result;
  }
  function logoRect(logo,asset,w,h){const width=Math.min(w*logo.width,h*.95*asset.naturalWidth/asset.naturalHeight),height=width*asset.naturalHeight/asset.naturalWidth;return {x:Math.min(logo.x*w,w-width),y:Math.min(logo.y*h,h-height),width,height};}
  function drawOverlay(ctx,state,w,h,logoAsset){
    if(state.grid){ctx.save();ctx.strokeStyle=state.gridColor||'#10b981';ctx.globalAlpha=1-(state.gridTransparency??50)/100;ctx.lineWidth=Math.max(1,w/800)*(state.gridThickness||1);const step=w*state.spacing/100;ctx.beginPath();for(let x=step;x<w;x+=step){ctx.moveTo(x,0);ctx.lineTo(x,h);}for(let y=step;y<h;y+=step){ctx.moveTo(0,y);ctx.lineTo(w,y);}ctx.stroke();ctx.restore();}
    for(const line of state.lines){for(const [stroke,width] of [['rgba(255,255,255,.85)',w/125],[line.color,w/250]]){ctx.strokeStyle=stroke;ctx.lineWidth=width;ctx.beginPath();for(const [a,b,c,d] of segments(line,w,h)){ctx.moveTo(a,b);ctx.lineTo(c,d);}ctx.stroke();}}
    if(state.logo&&logoAsset){const r=logoRect(state.logo,logoAsset,w,h);ctx.drawImage(logoAsset,r.x,r.y,r.width,r.height);}
  }
  const el=(tag,attrs={},text)=>{const node=document.createElement(tag);for(const [key,value] of Object.entries(attrs))node.setAttribute(key,value);if(text!==undefined)node.textContent=text;return node;};
  function mount(){
    const dialog=el('dialog',{class:'posture-editor',id:'postureEditorDialog','aria-labelledby':'postureEditorTitle'});
    dialog.innerHTML='<header><strong id="postureEditorTitle">Editor postural</strong><button type="button" data-action="save-top">Salvar foto</button><button type="button" data-action="close">Fechar</button></header>'+
      '<div class="posture-toolbar"><button type="button" data-action="gallery">Abrir foto</button><button type="button" data-action="camera">📷 Câmera</button><button type="button" data-action="vertical">+ Vertical</button><button type="button" data-action="horizontal">+ Horizontal</button><button type="button" data-action="ruler">+ Régua</button><button type="button" data-action="logo">+ Minha logo</button></div>'+
      '<div class="posture-options"><label><input type="checkbox" id="postureGrid"> Mostrar grade na foto</label><label>Grade <select id="postureSpacing" aria-label="Espaçamento da grade"><option value="5">Fina</option><option value="10">Média</option><option value="15">Ampla</option><option value="20">Grande</option><option value="25">Muito grande</option></select></label><label>Cor da grade <input type="color" id="postureGridColor" value="#10b981"></label><label>Cor da linha <input type="color" id="postureColor" value="#ef4444"></label><label><input type="checkbox" id="postureHandles" checked> Mostrar bolinhas</label></div>'+
      '<div class="posture-grid-style"><label>Espessura <input type="range" id="postureGridThickness" min="1" max="6" step="1" value="1" aria-label="Espessura da grade"><output id="postureGridThicknessValue" for="postureGridThickness">1×</output></label><label>Transparência <input type="range" id="postureGridTransparency" min="0" max="100" step="5" value="50" aria-label="Transparência da grade"><output id="postureGridTransparencyValue" for="postureGridTransparency">50%</output></label></div>'+
      '<div class="posture-logo-options" hidden><label>Tamanho da logo <input type="range" id="postureLogoSize" min="5" max="90" step="1" value="40" aria-label="Tamanho da logo"></label><button type="button" data-action="logo-file">Trocar PNG</button><button type="button" data-action="remove-logo">Retirar logo</button></div>'+
      '<div class="posture-zoom"><button type="button" data-action="zoom-out" aria-label="Diminuir foto">−</button><output id="postureZoomValue" aria-live="off">100%</output><button type="button" data-action="zoom-in" aria-label="Ampliar foto">+</button><button type="button" data-action="zoom-reset">Tamanho padrão</button><span>Zoom com dois dedos</span></div>'+
      '<div class="posture-workspace"><p class="posture-placeholder">Abra uma foto ou use a câmera.</p><div class="posture-stage" hidden><img alt="Foto em edição postural"><svg xmlns="http://www.w3.org/2000/svg" role="group" aria-label="Linhas ajustáveis da foto" tabindex="0"></svg></div></div>'+
      '<div class="posture-selection"><select id="postureLine" aria-label="Linha selecionada"></select><button type="button" data-action="remove">Remover linha</button><button type="button" data-action="undo" aria-label="Desfazer marcação">↶</button><button type="button" data-action="redo" aria-label="Refazer marcação">↷</button><button type="button" data-action="clear">Limpar marcações</button></div>'+
      '<p class="posture-help">Arraste a logo ou a linha para mover; uma bolinha para girar. Use dois dedos para aproximar a edição.</p><div class="posture-footer"><button type="button" data-action="delete-photo">Apagar foto</button><span id="postureStatus" role="status"></span><button type="button" data-action="save">Salvar foto</button></div>'+
      '<input type="file" accept="image/*" id="postureGalleryInput" hidden><input type="file" accept="image/*" capture="environment" id="postureCameraInput" hidden><input type="file" accept="image/png" id="postureLogoInput" hidden>';
    document.body.append(dialog);
    const q=s=>dialog.querySelector(s),workspace=q('.posture-workspace'),stage=q('.posture-stage'),photo=q('.posture-stage img'),svg=q('svg'),status=q('#postureStatus'),picker=q('#postureLine'),grid=q('#postureGrid'),spacing=q('#postureSpacing'),color=q('#postureColor'),save=q('[data-action="save"]');
    let state=defaults(),selected=null,image=null,source='',config=null,version=0,busy=false,history=[],historyIndex=0,drag=null,serial=0,logoAsset=null,selectedLogo=false,zoom=1,panX=0,panY=0,pinch=null;
    const pointers=new Map();
    const names={vertical:'Vertical',horizontal:'Horizontal',ruler:'Régua',line:'Linha'};
    const active=()=>state.lines.find(line=>line.id===selected);
    function controls(){
      grid.checked=state.grid;spacing.value=String(state.spacing);q('#postureGridColor').value=state.gridColor;q('#postureHandles').checked=state.showHandles;picker.replaceChildren();
      for(const [id,key,suffix] of [['postureGridThickness','gridThickness','×'],['postureGridTransparency','gridTransparency','%']]){q('#'+id).value=String(state[key]);q('#'+id).disabled=!state.grid||busy;q('#'+id+'Value').textContent=state[key]+suffix;}
      if(!selected&&state.lines.length){const option=el('option',{value:'',disabled:'disabled'},selectedLogo?'Logo selecionada · arraste na foto':'Selecione uma linha');option.selected=true;picker.append(option);}
      state.lines.forEach((line,index)=>{const a=angle(line,image?.naturalWidth||1,image?.naturalHeight||1),o=el('option',{value:line.id},(index+1)+' · '+names[line.kind]+(a===null?'':' · '+a.toLocaleString('pt-BR',{maximumFractionDigits:1})+'°'));o.selected=line.id===selected;picker.append(o);});
      picker.disabled=!state.lines.length;save.disabled=!image||busy;
      q('[data-action="save-top"]').disabled=save.disabled;q('[data-action="delete-photo"]').disabled=!config?.remove||busy;
      q('[data-action="undo"]').disabled=historyIndex<=0;q('[data-action="redo"]').disabled=historyIndex>=history.length-1;
      for(const action of ['vertical','horizontal','ruler','clear'])q('[data-action="'+action+'"]').disabled=!image||busy;
      q('[data-action="remove"]').disabled=!active()||busy;
      for(const action of ['logo','zoom-in','zoom-out','zoom-reset'])q('[data-action="'+action+'"]').disabled=!image||busy;
      q('.posture-logo-options').hidden=!state.logo;q('#postureLogoSize').value=String(Math.round((state.logo?.width||.4)*100));q('#postureLogoSize').disabled=busy;
      q('[data-action="logo-file"]').disabled=busy;q('[data-action="remove-logo"]').disabled=busy;
      q('#postureZoomValue').textContent=Math.round(zoom*100)+'%';
      if(active())color.value=active().color;
    }
    function record(){const value=JSON.stringify(state);if(value!==history[historyIndex]){history=history.slice(0,historyIndex+1);history.push(value);if(history.length>60)history.shift();historyIndex=history.length-1;}controls();}
    function svgLine(coords,attrs={}){const line=document.createElementNS('http://www.w3.org/2000/svg','line');for(const [key,value] of Object.entries({x1:coords[0],y1:coords[1],x2:coords[2],y2:coords[3],...attrs}))line.setAttribute(key,value);svg.append(line);return line;}
    function draw(){
      svg.replaceChildren();if(!image){controls();return;}const w=image.naturalWidth,h=image.naturalHeight;svg.setAttribute('viewBox','0 0 '+w+' '+h);
      if(state.grid){const step=w*state.spacing/100,style={stroke:state.gridColor,'stroke-opacity':1-state.gridTransparency/100,'stroke-width':Math.max(1,w/800)*state.gridThickness,'pointer-events':'none'};for(let x=step;x<w;x+=step)svgLine([x,0,x,h],style);for(let y=step;y<h;y+=step)svgLine([0,y,w,y],style);}
      const scale=stage.getBoundingClientRect().width/w||1;
      for(const line of state.lines){
        const coords=[line.x1*w,line.y1*h,line.x2*w,line.y2*h];
        for(const part of segments(line,w,h)){svgLine(part,{stroke:'white','stroke-opacity':'.85','stroke-width':w/125,'pointer-events':'none'});svgLine(part,{stroke:line.color,'stroke-width':w/250,'pointer-events':'none'});}
        svgLine(coords,{'data-line':line.id,'data-part':'body',stroke:'transparent','stroke-width':'26','vector-effect':'non-scaling-stroke','pointer-events':'stroke'});
      }
      if(state.logo&&logoAsset){const r=logoRect(state.logo,logoAsset,w,h),logo=document.createElementNS('http://www.w3.org/2000/svg','image');for(const [key,value] of Object.entries({...r,href:state.logo.src,'data-logo':'body','pointer-events':'all'}))logo.setAttribute(key,value);svg.append(logo);
        if(selectedLogo&&state.showHandles){const border=document.createElementNS('http://www.w3.org/2000/svg','rect');for(const [key,value] of Object.entries({...r,fill:'none',stroke:'#10b981','stroke-width':1/scale,'stroke-dasharray':(5/scale)+' '+(3/scale),'pointer-events':'none'}))border.setAttribute(key,value);svg.append(border);}}
      const line=active();
      if(line&&state.showHandles)for(const point of [1,2]){const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');for(const [key,value] of Object.entries({cx:line['x'+point]*w,cy:line['y'+point]*h,r:9/scale,fill:'white',stroke:line.color,'stroke-width':2/scale,'data-line':line.id,'data-part':point}))dot.setAttribute(key,value);svg.append(dot);}
      controls();
    }
    function applyView(){stage.style.transform='translate('+panX+'px,'+panY+'px) scale('+zoom+')';draw();}
    function setZoom(next){zoom=Math.min(4,Math.max(.5,next));applyView();}
    function resetView(){zoom=1;panX=panY=0;pointers.clear();pinch=drag=null;applyView();}
    function fit(){if(!image||!dialog.open)return;const w=workspace.clientWidth-12,h=workspace.clientHeight-12;if(w<=0||h<=0)return;const scale=Math.min(w/image.naturalWidth,h/image.naturalHeight);stage.style.width=(image.naturalWidth*scale)+'px';stage.style.height=(image.naturalHeight*scale)+'px';applyView();}
    const observer=new ResizeObserver(fit);observer.observe(workspace);
    function coordinates(event){const box=stage.getBoundingClientRect();return {x:clamp((event.clientX-box.left)/box.width),y:clamp((event.clientY-box.top)/box.height)};}
    workspace.addEventListener('pointerdown',event=>{
      if(!image||busy||event.button>0)return;event.preventDefault();pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});workspace.setPointerCapture(event.pointerId);
      if(pointers.size===2){if(drag&&drag.kind!=='pan')record();drag=null;const [a,b]=[...pointers.values()];pinch={distance:Math.max(1,Math.hypot(b.x-a.x,b.y-a.y)),x:(a.x+b.x)/2,y:(a.y+b.y)/2,zoom,panX,panY};return;}
      if(pointers.size>2)return;
      const target=event.target.closest('[data-line]'),logo=event.target.closest('[data-logo]');
      if(logo&&state.logo){selectedLogo=true;selected=null;const r=logoRect(state.logo,logoAsset,image.naturalWidth,image.naturalHeight);drag={kind:'logo',pointer:event.pointerId,start:coordinates(event),x:r.x/image.naturalWidth,y:r.y/image.naturalHeight};}
      else if(target){selectedLogo=false;selected=target.dataset.line;drag={kind:'line',pointer:event.pointerId,part:target.dataset.part,start:coordinates(event),line:{...active()}};}
      else drag={kind:'pan',pointer:event.pointerId,start:{x:event.clientX,y:event.clientY},panX,panY};
      draw();
    });
    workspace.addEventListener('pointermove',event=>{
      if(!pointers.has(event.pointerId)||busy)return;event.preventDefault();pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if(pinch&&pointers.size>=2){const [a,b]=[...pointers.values()],box=workspace.getBoundingClientRect(),cx=box.x+box.width/2,cy=box.y+box.height/2;zoom=Math.min(4,Math.max(.5,pinch.zoom*Math.hypot(b.x-a.x,b.y-a.y)/pinch.distance));panX=(a.x+b.x)/2-cx-(pinch.x-cx-pinch.panX)*zoom/pinch.zoom;panY=(a.y+b.y)/2-cy-(pinch.y-cy-pinch.panY)*zoom/pinch.zoom;applyView();return;}
      if(!drag||event.pointerId!==drag.pointer)return;
      if(drag.kind==='pan'){panX=drag.panX+event.clientX-drag.start.x;panY=drag.panY+event.clientY-drag.start.y;applyView();return;}
      const p=coordinates(event);
      if(drag.kind==='logo'&&state.logo&&logoAsset){const r=logoRect(state.logo,logoAsset,image.naturalWidth,image.naturalHeight);state.logo.x=Math.max(0,Math.min(1-r.width/image.naturalWidth,drag.x+p.x-drag.start.x));state.logo.y=Math.max(0,Math.min(1-r.height/image.naturalHeight,drag.y+p.y-drag.start.y));draw();return;}
      const line=active(),old=drag.line;if(!line)return;
      if(drag.part==='body'){const dx=Math.max(-Math.min(old.x1,old.x2),Math.min(1-Math.max(old.x1,old.x2),p.x-drag.start.x)),dy=Math.max(-Math.min(old.y1,old.y2),Math.min(1-Math.max(old.y1,old.y2),p.y-drag.start.y));Object.assign(line,{x1:old.x1+dx,x2:old.x2+dx,y1:old.y1+dy,y2:old.y2+dy});}
      else{line['x'+drag.part]=p.x;line['y'+drag.part]=p.y;if(line.kind==='vertical'||line.kind==='horizontal')line.kind='line';}
      draw();
    });
    function endDrag(event){pointers.delete(event.pointerId);if(pinch){if(pointers.size<2)pinch=null;drag=null;return;}if(!drag||event.pointerId!==drag.pointer)return;const changed=drag.kind!=='pan';drag=null;if(changed)record();}
    workspace.addEventListener('pointerup',endDrag);workspace.addEventListener('pointercancel',endDrag);workspace.addEventListener('lostpointercapture',endDrag);
    svg.addEventListener('keydown',event=>{const line=active();if(!line||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))return;event.preventDefault();const step=event.shiftKey ? .02 : .005,dx=event.key==='ArrowLeft'?-step:event.key==='ArrowRight'?step:0,dy=event.key==='ArrowUp'?-step:event.key==='ArrowDown'?step:0;const x=Math.max(-Math.min(line.x1,line.x2),Math.min(1-Math.max(line.x1,line.x2),dx)),y=Math.max(-Math.min(line.y1,line.y2),Math.min(1-Math.max(line.y1,line.y2),dy));line.x1+=x;line.x2+=x;line.y1+=y;line.y2+=y;record();draw();});
    function add(kind){if(!image||state.lines.length>=20){status.textContent='Use até 20 linhas por foto.';return;}const line={id:'line-'+Date.now()+'-'+(++serial),kind,x1:kind==='vertical'?.5:.2,y1:kind==='vertical'?.05:.45,x2:kind==='vertical'?.5:.8,y2:kind==='vertical'?.95:.45,color:color.value};state.lines.push(line);selected=line.id;selectedLogo=false;record();draw();}
    async function loadSource(src,settings,token){
      const next=new Image();next.src=src;await next.decode();const normalized=normalize(settings),asset=normalized.logo?await loadLogo(normalized.logo.src):null;if(token!==version||!dialog.open)return;
      if(!next.naturalWidth||!next.naturalHeight)throw Error('Foto inválida.');
      image=next;source=src;photo.src=src;state=normalized;logoAsset=asset;selectedLogo=false;selected=state.lines.at(-1)?.id||null;history=[JSON.stringify(state)];historyIndex=0;zoom=1;panX=panY=0;pointers.clear();pinch=drag=null;
      stage.hidden=false;q('.posture-placeholder').hidden=true;busy=false;status.textContent='';fit();
    }
    async function loadFile(file){
      const token=++version;busy=true;controls();status.textContent='Abrindo foto…';
      try{const data=await config.compress(file);if(token!==version||!dialog.open)return;await loadSource(data,null,token);}
      catch(error){if(token===version){busy=false;status.textContent='Não foi possível abrir esta foto. Tente outra imagem.';controls();}}
    }
    for(const [id,action] of [['postureGalleryInput','gallery'],['postureCameraInput','camera']]){q('#'+id).onchange=event=>{const file=event.target.files[0];event.target.value='';if(file)loadFile(file);};q('[data-action="'+action+'"]').onclick=()=>q('#'+id).click();}
    for(const kind of ['vertical','horizontal','ruler'])q('[data-action="'+kind+'"]').onclick=()=>add(kind);
    q('[data-action="close"]').onclick=()=>dialog.close();
    q('[data-action="remove"]').onclick=()=>{state.lines=state.lines.filter(line=>line.id!==selected);selected=state.lines.at(-1)?.id||null;record();draw();};
    q('[data-action="clear"]').onclick=()=>{state={...defaults(),logo:state.logo};selected=null;record();draw();};
    for(const [action,direction] of [['undo',-1],['redo',1]])q('[data-action="'+action+'"]').onclick=async()=>{const next=historyIndex+direction;if(busy||next<0||next>=history.length)return;const token=version,restored=normalize(JSON.parse(history[next]));busy=true;controls();try{const asset=restored.logo?await loadLogo(restored.logo.src):null;if(token!==version)return;historyIndex=next;state=restored;logoAsset=asset;selectedLogo=false;selected=state.lines.at(-1)?.id||null;}catch(error){status.textContent='Não foi possível restaurar a logo.';}finally{if(token===version){busy=false;draw();}}};
    q('[data-action="zoom-in"]').onclick=()=>setZoom(zoom*1.2);q('[data-action="zoom-out"]').onclick=()=>setZoom(zoom/1.2);q('[data-action="zoom-reset"]').onclick=resetView;
    async function insertLogo(src,remember=false){const token=version;if(!image||busy)return;busy=true;controls();try{const asset=await loadLogo(src);if(token!==version)return;if(remember)localStorage.setItem(logoKey,src);logoAsset=asset;state.logo={x:.05,y:.85,width:.4,...(state.logo||{}),src};selected=null;selectedLogo=true;record();}catch(error){if(token===version)status.textContent='Não foi possível carregar ou guardar a logo. Use um PNG menor.';}finally{if(token===version){busy=false;draw();}}}
    q('[data-action="logo"]').onclick=()=>{let src=defaultLogo;try{const stored=localStorage.getItem(logoKey);if(validLogo(stored))src=stored;}catch(error){}insertLogo(src);};
    q('[data-action="logo-file"]').onclick=()=>q('#postureLogoInput').click();
    q('#postureLogoInput').onchange=async event=>{const file=event.target.files[0],token=version;event.target.value='';if(!file)return;if(file.type!=='image/png'||file.size>3*1024*1024){status.textContent='Escolha uma logo PNG de até 3 MB.';return;}try{const src=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file);});if(token===version)await insertLogo(src,true);}catch(error){if(token===version)status.textContent='Não foi possível abrir este PNG.';}};
    q('[data-action="remove-logo"]').onclick=()=>{state.logo=null;logoAsset=null;selectedLogo=false;record();draw();};
    q('#postureLogoSize').oninput=event=>{if(state.logo){state.logo.width=Number(event.target.value)/100;draw();}};q('#postureLogoSize').onchange=()=>record();
    grid.onchange=()=>{state.grid=grid.checked;record();draw();};spacing.onchange=()=>{state.spacing=Number(spacing.value);record();draw();};
    q('#postureHandles').onchange=event=>{state.showHandles=event.target.checked;record();draw();};
    q('#postureGridColor').oninput=event=>{state.gridColor=event.target.value;draw();};q('#postureGridColor').onchange=()=>record();
    for(const [id,key] of [['postureGridThickness','gridThickness'],['postureGridTransparency','gridTransparency']]){q('#'+id).oninput=event=>{state[key]=Number(event.target.value);draw();};q('#'+id).onchange=()=>record();}
    color.oninput=()=>{if(active()){active().color=color.value;draw();}};color.onchange=()=>record();
    picker.onchange=()=>{selected=picker.value;selectedLogo=false;draw();};
    save.onclick=async()=>{
      if(!image||busy)return;const saveVersion=version,commit=config.save;busy=true;controls();status.textContent='Salvando foto…';
      try{
        let output=source;
        if(state.grid||state.lines.length||state.logo){const canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0);drawOverlay(ctx,state,canvas.width,canvas.height,logoAsset);output=canvas.toDataURL('image/jpeg',.85);canvas.width=canvas.height=1;}
        await commit({photo:output,original:source,settings:normalize(state)});if(version===saveVersion)dialog.close();
      }catch(error){if(version===saveVersion){busy=false;status.textContent=error.message||'Não foi possível salvar; sua edição continua aberta.';controls();}}
    };
    q('[data-action="save-top"]').onclick=()=>save.click();
    q('[data-action="delete-photo"]').onclick=async()=>{
      if(busy||!config?.remove||!confirm('Apagar a foto e suas marcações desta avaliação?'))return;
      const deleteVersion=version,remove=config.remove;busy=true;controls();
      try{await remove();if(version===deleteVersion)dialog.close();}
      catch(error){if(version===deleteVersion){busy=false;status.textContent=error.message||'Não foi possível apagar a foto.';controls();}}
    };
    dialog.addEventListener('close',()=>{version++;drag=pinch=null;pointers.clear();busy=false;image=logoAsset=null;source='';photo.removeAttribute('src');svg.replaceChildren();config=null;});
    return {open(options){
      config=options;version++;image=logoAsset=null;source='';state=defaults();selected=null;selectedLogo=false;zoom=1;panX=panY=0;drag=pinch=null;pointers.clear();history=[JSON.stringify(state)];historyIndex=0;stage.hidden=true;q('.posture-placeholder').hidden=false;status.textContent='';photo.removeAttribute('src');svg.replaceChildren();q('#postureEditorTitle').textContent='Postural · '+options.title;dialog.showModal();controls();
      if(options.file)loadFile(options.file);
      else if(options.source){const token=version;busy=true;controls();loadSource(options.source,options.settings,token).catch(()=>{if(token===version){busy=false;status.textContent='Não foi possível abrir a foto.';controls();}});}
      if(options.camera)q('#postureCameraInput').click();
    }};
  }
  return {mount,normalize,angle,segments,drawOverlay};
})();
