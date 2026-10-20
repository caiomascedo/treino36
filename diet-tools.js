/* Small arithmetic and clipboard controls, local to the open diet draft. */
window.DietTools=(()=>{
  const fields=[['calories','Calorias do dia','kcal'],['protein','Proteína','g'],['carbs','Carboidratos','g'],['fat','Gorduras','g']];
  const format=value=>Number(value).toLocaleString('pt-BR',{useGrouping:false,maximumFractionDigits:10});
  function markup(){return '<div class="diet-values-actions"><button type="button" id="dietCopyValues">Copiar tudo</button><button type="button" id="dietClearValues">Limpar campos</button><button type="button" id="dietCalculateMacros">Calcular macros</button></div>'+
    '<details id="dietMacroTools"><summary>Macros pelo peso · ajustar</summary><p class="diet-hint" id="dietMacroSource"></p><div class="diet-macro-ratios"><label>Peso para o cálculo (kg)<input id="diet-macroWeight" inputmode="decimal" placeholder="Peso da OBS"></label><label>Carbo · manutenção (g/kg)<input id="diet-carbDaily" inputmode="decimal" placeholder="Definir"></label><label>Carbo · emagrecimento (g/kg)<input id="diet-carbDeficit" inputmode="decimal" placeholder="2"></label><label>Carbo · hipertrofia (g/kg)<input id="diet-carbSurplus" inputmode="decimal" placeholder="Definir"></label></div><p class="diet-hint">Proteína: peso × 2. Gordura: peso × 0,8. Calorias: proteína × 4 + carboidratos × 4 + gorduras × 9.</p><label class="diet-macro-auto"><input type="checkbox" id="dietMacroAuto"> Atualizar macros com o peso e o objetivo</label></details><p id="dietMacroNotice" class="diet-hint" role="status"></p>'+
    '<details id="dietMiniCalculator"><summary>🧮 Mini calculadora</summary><div class="diet-mini-input"><input id="dietCalcExpression" type="text" inputmode="text" maxlength="160" aria-label="Conta da calculadora" placeholder="Ex.: 56 × 0,8"><button type="button" id="dietCalcEvaluate">=</button><button type="button" id="dietCalcClear">Limpar</button></div><output id="dietCalcResult" aria-live="polite"></output><div class="diet-mini-keys">'+['7','8','9','÷','4','5','6','×','1','2','3','−','0',',','⌫','+'].map(key=>'<button type="button" data-diet-calc-key="'+key+'">'+key+'</button>').join('')+'</div><div class="diet-mini-apply"><button type="button" id="dietCalcCopy" disabled>Copiar resultado</button><label>Usar em<select id="dietCalcTarget">'+fields.map(([key,label])=>'<option value="'+key+'">'+label+'</option>').join('')+'</select></label><button type="button" id="dietCalcApply" disabled>Aplicar resultado</button></div></details>';}
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
    const expression=q('dietCalcExpression'),output=q('dietCalcResult'),apply=q('dietCalcApply'),copyButton=q('dietCalcCopy');
    function invalidate(){result=null;output.textContent='';apply.disabled=copyButton.disabled=true;}
    function calculate(){try{result=DietCalculations.evaluate(expression.value);output.textContent='= '+format(result);apply.disabled=result<0;copyButton.disabled=false;}catch(error){invalidate();output.textContent=error.message;}}
    expression.oninput=invalidate;expression.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();calculate();}};
    q('dietCalcEvaluate').onclick=calculate;q('dietCalcClear').onclick=()=>{expression.value='';invalidate();expression.focus();};
    dialog.querySelectorAll('[data-diet-calc-key]').forEach(button=>{button.onclick=()=>{const key=button.dataset.dietCalcKey,start=expression.selectionStart??expression.value.length,end=expression.selectionEnd??start;if(key==='⌫'&&start===end){expression.setRangeText('',Math.max(0,start-1),end,'end');}else expression.setRangeText(key==='⌫'?'':key,start,end,'end');invalidate();expression.focus({preventScroll:true});};});
    copyButton.onclick=()=>{if(result!==null)send(format(result),'Resultado');};
    apply.onclick=()=>{if(result!==null&&result>=0){config.apply(q('dietCalcTarget').value,String(result));message('Resultado aplicado.');}};
    return {reset(){expression.value='';invalidate();q('dietMiniCalculator').open=false;}};
  }
  return {markup,mount};
})();
