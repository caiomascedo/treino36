/* Small arithmetic and clipboard controls, local to the open diet draft. */
window.DietTools=(()=>{
  const fields=[['calories','Calorias do dia','kcal'],['protein','Proteína','g'],['carbs','Carboidratos','g'],['fat','Gorduras','g']];
  const format=value=>Number(value).toLocaleString('pt-BR',{useGrouping:false,maximumFractionDigits:10});
  function markup(){return '<div class="diet-values-actions"><button type="button" id="dietCopyValues">Copiar tudo</button><button type="button" id="dietClearValues">Limpar campos</button></div>'+
    '<p id="dietMacroNotice" class="diet-hint" role="status"></p>'+
    '<details id="dietMiniCalculator"><summary>🧮 Mini calculadora</summary><div class="diet-mini-input"><input id="dietCalcExpression" type="text" inputmode="none" readonly tabindex="-1" maxlength="160" aria-label="Conta da calculadora" placeholder="Ex.: 56 × 0,8"><button type="button" id="dietCalcClear">Limpar</button></div><output id="dietCalcResult" aria-live="polite"></output><div class="diet-mini-keys">'+['7','8','9','÷','4','5','6','×','1','2','3','−','0',',','⌫','+'].map(key=>'<button type="button" data-diet-calc-key="'+key+'">'+key+'</button>').join('')+'<button type="button" id="dietCalcEvaluate" aria-label="Calcular resultado">=</button></div><div class="diet-mini-apply"><button type="button" id="dietCalcCopy" disabled>Copiar resultado</button></div></details>';}
  async function copy(value){
    if(navigator.clipboard?.writeText){try{await navigator.clipboard.writeText(value);return;}catch(error){}}
    const active=document.activeElement,selection=typeof active?.selectionStart==='number'?[active.selectionStart,active.selectionEnd]:null;
    const area=document.createElement('textarea');area.value=value;area.style.cssText='position:fixed;left:0;top:0;opacity:0;width:1px;height:1px';
    (document.querySelector('#dietDialog[open]')||document.body).append(area);area.focus({preventScroll:true});area.select();let success;
    try{success=document.execCommand('copy');}finally{area.remove();active?.focus({preventScroll:true});if(selection)active.setSelectionRange(...selection);}
    if(!success)throw Error('Não foi possível copiar. Selecione o valor e copie pelo aparelho.');
  }
  function mount(dialog,config){
    const q=id=>dialog.querySelector('#'+id);let result=null;
    const message=text=>config.message(text);
    async function send(value,label){try{await copy(value);message(label+' copiado.');}catch(error){message(error.message);}}
    for(const [key,label] of fields){
      const input=q('diet-'+key),tools=document.createElement('div');tools.className='diet-field-tools';
      for(const [action,text] of [['copy','Copiar'],['clear','Limpar']]){const button=document.createElement('button');button.type='button';button.textContent=text;button.dataset.dietField=key;button.dataset.dietFieldAction=action;button.setAttribute('aria-label',text+' '+label);button.onclick=event=>{event.preventDefault();if(action==='clear'){config.clear([key]);return;}const value=config.values()[key];if(value===null){message(label+': nenhum valor informado.');return;}send(format(value),label);};tools.append(button);}
      const fieldLabel=input.parentElement,wrapper=document.createElement('div');wrapper.className='diet-metric-field';fieldLabel.replaceWith(wrapper);wrapper.append(fieldLabel,tools);
    }
    q('dietCopyValues').onclick=()=>{const values=config.values();send(fields.map(([key,label,unit])=>label+': '+(values[key]===null?'Não informado':format(values[key])+' '+unit)).join('\n'),'Resumo');};
    q('dietClearValues').onclick=()=>config.clear(fields.map(([key])=>key));
    const expression=q('dietCalcExpression'),output=q('dietCalcResult'),copyButton=q('dietCalcCopy');
    function invalidate(){result=null;output.textContent='';copyButton.disabled=true;}
    function calculate(){try{result=DietCalculations.evaluate(expression.value);output.textContent='= '+format(result);copyButton.disabled=false;}catch(error){invalidate();output.textContent=error.message;}}
    expression.oninput=invalidate;expression.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();calculate();}};
    q('dietCalcEvaluate').onclick=calculate;q('dietCalcClear').onclick=()=>{expression.value='';invalidate();document.activeElement?.blur();};
    dialog.querySelectorAll('[data-diet-calc-key]').forEach(button=>{button.onclick=()=>{document.activeElement?.blur();const key=button.dataset.dietCalcKey;if(key==='⌫')expression.value=expression.value.slice(0,-1);else if(expression.value.length<160)expression.value+=key;invalidate();};});
    q('dietMiniCalculator').addEventListener('toggle',()=>{if(q('dietMiniCalculator').open)document.activeElement?.blur();});
    copyButton.onclick=()=>{if(result!==null)send(format(result),'Resultado');};
    return {reset(){expression.value='';invalidate();q('dietMiniCalculator').open=false;}};
  }
  return {markup,mount};
})();
