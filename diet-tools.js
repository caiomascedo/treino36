/* Small arithmetic and clipboard controls, local to the open diet draft. */
window.DietTools=(()=>{
  const fields=[['calories','Calorias do dia','kcal'],['protein','Proteína','g'],['carbs','Carboidratos','g'],['fat','Gorduras','g']];
  const format=value=>Number(value).toLocaleString('pt-BR',{useGrouping:false,maximumFractionDigits:10});
  function markup(){return '<div class="diet-values-actions"><button type="button" id="dietCopyValues">Copiar tudo</button><button type="button" id="dietClearValues">Limpar campos</button></div>'+
    '<p id="dietMacroNotice" class="diet-hint" role="status"></p>'+
    '<details id="dietMiniCalculator"><summary>🧮 Mini calculadora</summary><div class="diet-iphone-calculator"><input id="dietCalcExpression" type="text" inputmode="none" readonly tabindex="-1" maxlength="160" aria-label="Conta da calculadora" placeholder="0"><div class="diet-calc-result-row"><output id="dietCalcResult" aria-live="polite"></output><button type="button" id="dietCalcCopy" disabled>Copiar resultado</button></div><div class="diet-mini-keys">'+['⌫','AC','%','÷','7','8','9','×','4','5','6','−','1','2','3','+','+/−','0',',','='].map(key=>'<button type="button" '+(key==='AC'?'id="dietCalcClear"':key==='='?'id="dietCalcEvaluate" aria-label="Calcular resultado"':'data-diet-calc-key="'+key+'"')+' class="'+('÷×−+='.includes(key)?'diet-calc-operator':['⌫','AC','%'].includes(key)?'diet-calc-utility':'diet-calc-number')+'">'+key+'</button>').join('')+'</div></div></details>';}
  async function copy(value){
    if(navigator.clipboard?.writeText){try{await navigator.clipboard.writeText(value);return;}catch(error){}}
    const active=document.activeElement,selection=typeof active?.selectionStart==='number'?[active.selectionStart,active.selectionEnd]:null;
    const area=document.createElement('textarea');area.readOnly=true;area.value=value;area.style.cssText='position:fixed;left:0;top:0;opacity:0;width:1px;height:1px';
    (document.querySelector('#dietDialog[open]')||document.body).append(area);area.focus({preventScroll:true});area.select();let success;
    try{success=document.execCommand('copy');}finally{area.remove();active?.focus({preventScroll:true});if(selection)active.setSelectionRange(...selection);}
    if(!success)throw Error('Não foi possível copiar. Selecione o valor e copie pelo aparelho.');
  }
  function mount(dialog,config){
    const q=id=>dialog.querySelector('#'+id);let result=null,finished=false;
    const message=text=>config.message(text);
    async function send(value,label){try{await copy(value);message(label+' copiado.');}catch(error){message(error.message);}}
    for(const [key,label] of fields){
      const input=q('diet-'+key),tools=document.createElement('div');tools.className='diet-field-tools';
      for(const [action,text] of [['copy','Copiar'],['clear','Limpar']]){const button=document.createElement('button');button.type='button';button.textContent=text;button.dataset.dietField=key;button.dataset.dietFieldAction=action;button.setAttribute('aria-label',text+' '+label);button.onclick=event=>{event.preventDefault();if(action==='clear'){config.clear([key]);return;}const value=config.values()[key];if(value===null){message(label+': nenhum valor informado.');return;}send(format(value),label);};tools.append(button);}
      const fieldLabel=input.parentElement,wrapper=document.createElement('div');wrapper.className='diet-metric-field';fieldLabel.replaceWith(wrapper);wrapper.append(fieldLabel,tools);
    }
    q('dietCopyValues').onclick=()=>{const values=config.values();send(fields.map(([key,label,unit])=>label+': '+(values[key]===null?'Não informado':format(values[key])+' '+unit)).join('\n'),'Resumo');};
    q('dietCopyGoal').onclick=()=>{const goal=config.goal();if(goal===null){message('Selecione sexo e atividade para calcular a meta.');return;}send(format(goal),'Meta em kcal');};
    q('dietClearValues').onclick=()=>config.clear(fields.map(([key])=>key));
    const expression=q('dietCalcExpression'),output=q('dietCalcResult'),copyButton=q('dietCalcCopy');
    function invalidate(){result=null;output.textContent='';copyButton.disabled=true;}
    function calculate(){try{result=DietCalculations.evaluate(expression.value);output.textContent='= '+format(result);copyButton.disabled=false;finished=true;}catch(error){invalidate();output.textContent=error.message;}}
    expression.oninput=invalidate;expression.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();calculate();}};
    q('dietCalcEvaluate').onclick=calculate;q('dietCalcClear').onclick=()=>{expression.value='';finished=false;invalidate();document.activeElement?.blur();};
    function keypress(key){
      document.activeElement?.blur();
      const operator='÷×−+'.includes(key);
      if(finished){expression.value=operator||['%','+/−','⌫'].includes(key)?format(result):'';finished=false;}
      let value=expression.value;
      if(key==='⌫')value=value.endsWith(')')?value.replace(/\(-[\d.,]+\)$/,''):value.slice(0,-1);
      else if(key==='%'||key==='+/−'){
        const match=value.match(/(\(-[\d.,]+\)|[\d.,]+)$/);
        if(match){const prefix=value.slice(0,match.index);let operand=DietCalculations.evaluate(match[0]);
          if(key==='+/−')operand=-operand;
          else {operand/=100;if(/[+−]$/.test(prefix)){const base=prefix.slice(0,-1);operand*=DietCalculations.evaluate(base);}}
          value=prefix+(operand<0?'('+format(operand)+')':format(operand));
        }
      }else if(operator){
        if(!value){if(key==='−')value='−';}
        else value=/[÷×−+]$/.test(value)?value.slice(0,-1)+key:value+key;
      }else {
        const operand=value.match(/[\d.,]+$/)?.[0]||'';
        if(key===','&&operand.includes(','))return;
        value+=(key===','&&!operand?'0,':key);
      }
      if(value.length<=160)expression.value=value;invalidate();
    }
    dialog.querySelectorAll('[data-diet-calc-key]').forEach(button=>{button.onclick=()=>{try{keypress(button.dataset.dietCalcKey);}catch(error){invalidate();output.textContent=error.message;}};});
    q('dietMiniCalculator').addEventListener('toggle',()=>{if(q('dietMiniCalculator').open)document.activeElement?.blur();});
    copyButton.onclick=()=>{if(result!==null)send(format(result),'Resultado');};
    return {reset(){expression.value='';finished=false;invalidate();q('dietMiniCalculator').open=false;}};
  }
  return {markup,mount};
})();
