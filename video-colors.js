/* Keep original footage intact unless this particular clip has an explicit choice. */
window.WorkoutVideoColors=(()=>{
  const storageKey='treinoVideoColorsV1';
  function choices(){try{return JSON.parse(localStorage.getItem(storageKey)||'{}')||{};}catch(error){return {};}}
  const key=asset=>asset&&(asset.url||asset.localURL||asset.media||asset.collection+':'+asset.id);
  function choice(asset){return choices()[key(asset)]||'original';}
  function invert(asset,theme){const value=choice(asset);return value==='invert'||value==='theme'&&((theme==='cm')!==((asset.inkTheme||asset.collection)==='cm'));}
  function apply(video,asset,theme='gymfaster'){
    video.dataset.videoInvert=String(!!asset&&invert(asset,theme));
    video.style.background=asset&&(asset.inkTheme||asset.collection)==='cm'?'#000':'#fff';
  }
  function editor(onChange){
    let asset;
    const element=document.createElement('label');element.className='video-color-choice';
    element.append(document.createTextNode('Cor deste vídeo '));
    const select=document.createElement('select');select.setAttribute('aria-label','Cor deste vídeo');
    for(const [value,text]of [['original','Cores originais'],['theme','Adaptar ao tema'],['invert','Inverter cores']])select.add(new Option(text,value));
    element.append(select);
    select.onchange=()=>{
      if(!asset)return;
      const values=choices();values[key(asset)]=select.value;
      try{localStorage.setItem(storageKey,JSON.stringify(values));}catch(error){}
      onChange?.();
      window.dispatchEvent(new CustomEvent('workout-video-colors-change',{detail:{key:key(asset)}}));
    };
    return {element,select,setAsset(value){asset=value;element.hidden=!asset;select.value=choice(asset);select.disabled=!asset;}};
  }
  return {key,choice,invert,apply,editor};
})();
