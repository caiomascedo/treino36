/* Calculations use entered values, never guessed nutrition for food names. */
window.DietCalculations = (() => {
  const normalize = text => String(text).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  function number(value) {
    let text = String(value ?? '').trim().replace(/\s/g, '');
    if (!text) return null;
    if (/^\d{1,3}(?:\.\d{3})+(?:,\d+)?$/.test(text)) text = text.replace(/\./g, '');
    text = text.replace(',', '.');
    if (!/^\d+(?:\.\d+)?$/.test(text)) return null;
    const n = Number(text); return Number.isFinite(n) ? n : null;
  }
  function basal(settings) {
    return calorieEstimate(settings.weight,settings.height,settings.age,settings.sex,settings.activity)?.tmb??null;
  }
  // Reference: https://unimed.coop.br/portalunimed/aplicativos/tmb/ (classic calculator).
  // Its female height coefficient is 1.7; activity factors also differ by sex.
  function measurement(value){return number(String(value??'').trim().replace(/\s*(?:kg|cm|m|anos?)$/i,'').trim());}
  function calorieContext(student,ficha={}){
    let record={};
    if(student&&window.AvaliacaoTreinoSync){try{const sync=window.AvaliacaoTreinoSync,records=sync.read(sync.key);record=records.find(r=>String(r.id)===String(ficha.avaliacaoCadastroId)&&sync.isLinked(r,student.student_id))||sync.resolve(records,student)||{};}catch(error){}}
    return {sex:ficha.sexoCalorico??record.sexo??'',activity:ficha.atividadeCalorica??''};
  }
  function calorieEstimate(weight,height,age,sex,activity){
    const kg=measurement(weight),rawHeight=measurement(height),years=measurement(age),cm=rawHeight!==null&&rawHeight<3.5?rawHeight*100:rawHeight;
    if(!['F','M'].includes(sex)||kg===null||kg<=10||kg>350||cm===null||cm<60||cm>260||years===null||years<=0||years>125)return null;
    const round=value=>Math.round((value+Number.EPSILON)*100)/100;
    const raw=sex==='F'?655+9.6*kg+1.7*cm-4.7*years:66+13.7*kg+5*cm-6.8*years;
    if(raw<=0)return null;
    const factor=(sex==='F'?{nenhuma:1.2,moderada:1.3,intensa:1.4}:{nenhuma:1.25,moderada:1.35,intensa:1.45})[activity];
    const daily=factor?round(raw*factor):null;
    return {tmb:round(raw),gastoTotal:daily,deficit:daily===null?null:round(daily-400),superavit:daily===null?null:round(daily+300),nivel:activity,fator:factor??null,sexo:sex};
  }
  const macroPatterns = {
    protein: /\b(?:proteinas?|prot|p)\s*[:=]?\s*(\d+(?:[.,]\d+)*)\s*g\b/gi,
    carbs: /\b(?:carboidratos?|carbo|carbs?|c)\s*[:=]?\s*(\d+(?:[.,]\d+)*)\s*g\b/gi,
    fat: /\b(?:gorduras?|gord|lipidios?|g)\s*[:=]?\s*(\d+(?:[.,]\d+)*)\s*g\b/gi
  };
  const sum = values => values.reduce((a,b) => a + b, 0);
  const energy = macros => (macros.protein || 0)*4 + (macros.carbs || 0)*4 + (macros.fat || 0)*9;
  const isDaily = text => /\b(?:resumo|total\s+(?:diario|do dia|geral)|totais(?:\s+do dia)?|calorias\s+(?:do dia|totais))\b/.test(normalize(text));
  function nutrition(sections, settings = {}) {
    const totals = {protein:0, carbs:0, fat:0}, daily = {}, energies = [];
    let explicit = false, missing = 0, count = 0, macrosFound = false;
    for (const section of sections) {
      const summary = isDaily(section.title), raw = section.items.map(normalize), macroStart = raw.findIndex(line => /^macros\s*:?$/.test(line));
      const macroLines = macroStart < 0 ? raw : raw.slice(macroStart+1);
      const values = {};
      for (const [key,pattern] of Object.entries(macroPatterns)) {
        const matches = macroLines.flatMap(line => [...line.matchAll(pattern)].map(m => number(m[1])).filter(value => value !== null));
        if (matches.length) { values[key] = sum(matches); macrosFound = true; if (summary) daily[key] = values[key]; else totals[key] += values[key]; }
      }
      let calorie = null, declared = null;
      const entries = [];
      for (const line of raw) {
        const matches = [...line.matchAll(/(\d+(?:[.,]\d+)*)\s*(?:kcal|calorias)\b/gi)].map(m => number(m[1])).filter(value => value !== null);
        if (!matches.length) continue;
        if (isDaily(line)) { daily.calories = matches.at(-1); continue; }
        if (/\btotal\b/.test(line)) declared = matches.at(-1); else entries.push(...matches);
      }
      if (declared !== null) calorie = declared;
      else if (entries.length) calorie = sum(entries);
      if (summary) { if (calorie !== null) daily.calories = calorie; continue; }
      if (!section.items.length || /^(?:observacoes|orientacoes|recomendacoes)/.test(normalize(section.title))) continue;
      count++;
      if (calorie !== null) { energies.push(calorie); explicit = true; }
      else if (Object.keys(values).length) { energies.push(energy(values)); if(Object.keys(values).length<3)missing++; }
      else missing++;
    }
    const manualMacros = ['protein','carbs','fat'].some(key => number(settings[key]) !== null);
    for (const key of ['protein','carbs','fat']) totals[key] = number(settings[key]) ?? daily[key] ?? totals[key];
    let calories = number(settings.calories), source = 'manual';
    if (calories === null) {
      if (manualMacros) { calories = energy(totals); source = 'macros editados'; if(['protein','carbs','fat'].every(key=>number(settings[key])!==null))missing=0; }
      else if (daily.calories !== undefined) { calories = daily.calories; source = 'total do texto'; missing = 0; }
      else if (Object.keys(daily).some(key => key !== 'calories')) { calories = energy(totals); source = 'macros do dia'; missing = ['protein','carbs','fat'].every(key=>daily[key]!==undefined)?0:Math.max(1,missing); }
      else if (energies.length) { calories = sum(energies); source = explicit ? 'valores do texto' : 'macros (4/4/9)'; }
      else { calories = null; source = 'sem valores informados'; }
    } else missing = 0;
    const estimate=calorieEstimate(settings.weight,settings.height,settings.age,settings.sex,settings.activity);
    const tmb = Object.hasOwn(settings,'obsTmb')?number(settings.obsTmb):estimate?.tmb??null;
    const automaticGoal=Object.hasOwn(settings,'obsGoal')?number(settings.obsGoal):estimate?.gastoTotal??null;
    const goal = number(settings.goal) ?? automaticGoal;
    if(settings.macroAuto&&['protein','carbs','fat','calories'].every(key=>number(settings[key])!==null))source='macros pelo peso';
    return {...totals,calories:calories === null ? null : Math.round(calories),source,missing,count,macrosFound:macrosFound||manualMacros,tmb,goal};
  }
  function weightMacros(weight,carbRatio) {
    const kg=number(weight),ratio=number(carbRatio);
    if(kg===null||kg<=0)throw Error('Informe um peso válido para calcular os macros.');
    if(ratio===null||ratio<0)throw Error('Informe os carboidratos em g/kg para este objetivo.');
    const round=value=>Math.round((value+Number.EPSILON)*10)/10;
    const macros={protein:round(kg*2),carbs:round(kg*ratio),fat:round(kg*.8)};
    if(!Object.values(macros).every(Number.isFinite))throw Error('Valores muito grandes para calcular.');
    const calories=Math.round(energy(macros));if(!Number.isFinite(calories))throw Error('Valores muito grandes para calcular.');
    return {...macros,calories,weight:kg,carbRatio:ratio};
  }
  function objectiveMacros(weight,mode,goal) {
    if(!['daily','deficit','surplus'].includes(mode))throw Error('Escolha Manutenção, Emagrecimento ou Hipertrofia para calcular os macros.');
    const result=weightMacros(weight,mode==='surplus'?4:2);
    if(mode==='daily'){
      const target=number(goal);
      if(target===null||target<=0)throw Error('Preencha os dados na OBS ou informe uma meta de calorias para calcular a manutenção.');
      const remaining=target-result.protein*4-result.fat*9;
      if(remaining<0)throw Error('A meta de calorias é menor que a energia da proteína e da gordura. Ajuste a meta para calcular a manutenção.');
      result.carbs=Math.round((remaining/4+Number.EPSILON)*10)/10;
      result.calories=Math.round(energy(result));result.carbRatio=null;
    }
    return result;
  }
  function evaluate(expression) {
    const source=String(expression).replace(/\s/g,'').replace(/[×x]/g,'*').replace(/÷/g,'/').replace(/[−–]/g,'-');
    if(!source||source.length>160)throw Error('Digite uma conta de até 160 caracteres.');
    const tokens=source.match(/(?:\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?|[.,]\d+)|[()+*/-]/g)||[];
    if(tokens.join('')!==source)throw Error('Use números, parênteses e + − × ÷.');
    let at=0;
    function atom(){
      const token=tokens[at++];
      if(token==='+'||token==='-')return (token==='-'?-1:1)*atom();
      if(token==='('){const result=add();if(tokens[at++]!==')')throw Error('Confira os parênteses.');return result;}
      const result=number(/^[.,]/.test(token||'')?'0'+token:token);if(result===null)throw Error('Confira a conta digitada.');return result;
    }
    function multiply(){let value=atom();while(['*','/'].includes(tokens[at])){const operator=tokens[at++],right=atom();if(operator==='/'&&right===0)throw Error('Não é possível dividir por zero.');value=operator==='*'?value*right:value/right;}return value;}
    function add(){let value=multiply();while(['+','-'].includes(tokens[at])){const operator=tokens[at++],right=multiply();value=operator==='+'?value+right:value-right;}return value;}
    const result=add();if(at!==tokens.length||!Number.isFinite(result))throw Error('Confira a conta digitada.');
    return Number(result.toPrecision(12));
  }
  return {number,basal,nutrition,weightMacros,objectiveMacros,evaluate,calorieEstimate,calorieContext,measurement};
})();
