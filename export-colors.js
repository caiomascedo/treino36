/* Color controls belong to export previews, never the editable workout sheet. */
window.WorkoutExportColors=(()=>{
  const defaults=['#b91c1c','#15803d','#ca8a04','#111111','#1d4ed8','#9333ea','#c2410c','#0f766e','#be185d','#4338ca'];
  const valid=value=>/^#[0-9a-f]{6}$/i.test(String(value||''));
  function create({label,palette=[],onChange}){
    let values=Array.isArray(palette)?palette.map(v=>valid(v)?v:null):[],count=-1;
    const element=document.createElement('details');element.className='export-color-editor';
    const summary=document.createElement('summary');summary.textContent='Ajustar cores do '+label;
    const list=document.createElement('div');list.className='export-color-swatches';
    const reset=document.createElement('button');reset.type='button';reset.textContent='Cores padrão';
    const color=index=>values[index]||defaults[index%defaults.length];
    reset.onclick=()=>{values=[];list.querySelectorAll('input').forEach((input,i)=>input.value=color(i));onChange?.();};
    element.append(summary,list,reset);
    return {element,color,values:()=>values.slice(),setDisabled(disabled){element.querySelectorAll('input,button').forEach(input=>input.disabled=disabled);},refresh(enabled,size){
      element.hidden=!enabled||!size;
      if(size===count)return;count=size;list.replaceChildren();
      for(let i=0;i<size;i++){const row=document.createElement('label'),name=document.createElement('span'),input=document.createElement('input');name.textContent='Parte '+(i+1);input.type='color';input.value=color(i);input.setAttribute('aria-label','Cor da parte '+(i+1)+' do '+label);input.oninput=()=>{values[i]=input.value;onChange?.();};row.append(name,input);list.append(row);}
    }};
  }
  return {create};
})();
