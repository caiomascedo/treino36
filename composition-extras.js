/* Optional bioimpedance measurements: choices belong to the pupil, values to each assessment. */
window.CompositionExtras=(()=>{
  const fields=[
    {key:'pesoGordura',label:'Peso da gordura (kg)'},
    {key:'musculoEsqueleticoPct',label:'Massa muscular esquelética (%)'},
    {key:'musculoEsqueleticoKg',label:'Massa muscular esquelética (kg)'},
    {key:'massaMuscularPct',label:'Massa muscular (%)'},
    {key:'pesoAgua',label:'Peso da água (kg)'},
    {key:'metabolismoInformado',label:'Metabolismo da bioimpedância (kcal/dia)'},
    {key:'alturaCm',label:'Altura (cm)',readonly:true},
    {key:'idadeReal',label:'Idade real (anos)',readonly:true}
  ];
  const descriptions={
    pesoGordura:'Quantidade de gordura corporal em quilogramas. É diferente do percentual de gordura.',
    musculoEsqueleticoPct:'Percentual do peso corporal correspondente aos músculos esqueléticos, responsáveis pelos movimentos. É diferente da massa muscular total.',
    musculoEsqueleticoKg:'Quantidade de músculos esqueléticos em quilogramas. É diferente da massa muscular total.',
    massaMuscularPct:'Percentual do peso corporal correspondente à massa muscular estimada pelo aparelho. Não equivale necessariamente ao percentual de músculo esquelético.',
    pesoAgua:'Quantidade de água corporal em quilogramas. É diferente do percentual de água.',
    metabolismoInformado:'Estimativa de gasto energético em repouso informada no laudo da bioimpedância, em kcal por dia. Este valor não substitui a TMB calculada pelo aplicativo.',
    alturaCm:'Altura registrada na ficha desta avaliação, apresentada em centímetros.',
    idadeReal:'Idade registrada na ficha desta avaliação, em anos. É diferente da idade metabólica.',
    antebraco:'Circunferência dos antebraços direito e esquerdo, em centímetros, nessa ordem.',
    pescoco:'Circunferência do pescoço em centímetros.',
    panturrilhaMedida:'Circunferência das panturrilhas direita e esquerda, em centímetros, nessa ordem.'
  };
  function addDetails(wrap,input,field){
    const detail=document.createElement('details');detail.className='composition-extra-detail';
    const summary=document.createElement('summary');summary.textContent='Ver detalhes';
    const current=document.createElement('p');current.className='composition-extra-value';
    const explanation=document.createElement('p');explanation.textContent=descriptions[field.key];
    const update=()=>{current.textContent=field.label+': '+(filled(input.value)?input.value:'Não informado');};
    detail.addEventListener('toggle',()=>{if(detail.open)update();});input.addEventListener('input',update);
    detail.append(summary,current,explanation);wrap.append(detail);update();
    return update;
  }
  const baseFields={
    composicao:[{key:'peso',label:'Peso (kg)',pdf:'Peso (kg)'},{key:'imc',label:'IMC',pdf:'IMC'},{key:'gordura',label:'Gordura (%)',pdf:'% Gordura'},{key:'visceral',label:'Gordura visceral',pdf:'Gordura Visceral'},{key:'massamuscular',label:'Massa muscular (kg)',pdf:'Massa Muscular (kg)'},{key:'proteina',label:'Proteína (%)',pdf:'% Proteína'},{key:'agua',label:'Água (%)',pdf:'% Água'},{key:'tmb',label:'TMB (kcal)',pdf:'TMB (kcal)'},{key:'idadeMetabolica',label:'Idade metabólica',pdf:'Idade Metabólica'}],
    medidas:[{key:'peitoral',label:'Peitoral',pdf:'Peitoral'},{key:'biceps',label:'Bíceps D / E',pdf:'Bíceps D/E'},{key:'barriga',label:'Barriga',pdf:'Abdômen'},{key:'cintura',label:'Cintura',pdf:'Cintura'},{key:'quadril',label:'Quadril',pdf:'Quadril'},{key:'coxa',label:'Coxa D / E',pdf:'Coxa D/E'}]
  };
  const measureFields=[{key:'antebraco',label:'Antebraço D / E',paired:true},{key:'pescoco',label:'Pescoço'},{key:'panturrilhaMedida',label:'Panturrilha D / E',paired:true}];
  const preferenceKeys=section=>section==='medidas'?{base:'medidasCampos',extra:'medidasExtras'}:{base:'composicaoCampos',extra:'composicaoExtras'};
  const catalog=section=>section==='medidas'?measureFields:fields;
  const selectedBase=(person,section='composicao')=>{const allowed=baseFields[section].map(f=>f.key),saved=person[preferenceKeys(section).base];return Array.isArray(saved)?[...new Set(saved.filter(key=>allowed.includes(key)))]:allowed;};
  const instances=new Set();
  const selected=(person,section='composicao')=>{const saved=person[preferenceKeys(section).extra],allowed=catalog(section).map(f=>f.key);return [...new Set((Array.isArray(saved)?saved:[]).filter(key=>allowed.includes(key)))];};
  const formatPair=value=>{const normalized=value.replace(/\s*\/\s*/g,' / ');return !normalized.includes('/')&&/\d\s+\d/.test(normalized)?normalized.replace(/\s+/, ' / '):normalized;};
  const filled=value=>value!==null&&value!==undefined&&String(value).trim()!==''&&String(value)!=='NaN';
  function value(person,av,key){
    if(key==='alturaCm'){const source=av.ficha?.altura??person.altura;if(!filled(source))return '';const n=Number(String(source).replace(',','.'));return Number.isFinite(n)&&n>0?String(Math.round(n*(n<3.5?100:1)*100)/100):'';}
    if(key==='idadeReal')return av.ficha?.idade??person.idade??'';
    return av[key]??'';
  }
  function notify(personId){for(const instance of instances){if(!instance.root.isConnected){instances.delete(instance);continue;}if(String(instance.getState().person.id)===String(personId))instance.refresh();}}
  function refreshValues(personId,avId){for(const instance of instances){if(!instance.root.isConnected){instances.delete(instance);continue;}const state=instance.getState();if(String(state.person.id)===String(personId)&&String(state.av.id)===String(avId))instance.refreshValues();}}
  function mount(root,grid,config){
    for(const instance of instances)if(!instance.root.isConnected)instances.delete(instance);
    const section=config.section||'composicao',base=baseFields[section],extras=catalog(section);
    const baseNodes=new Map();[...grid.children].filter(node=>!node.classList.contains('composition-extra-field')).slice(-base.length).forEach((node,index)=>baseNodes.set(base[index].key,node));
    const button=document.createElement('button');button.type='button';button.className='composition-extras-add';button.textContent='＋ Adicionar campos';button.setAttribute('aria-expanded','false');
    const choices=document.createElement('div');choices.className='composition-extras-choices';choices.hidden=true;
    const id=config.prefix+section+'-extra-options';choices.id=id;button.setAttribute('aria-controls',id);root.append(button,choices);
    const hint=document.createElement('p');hint.textContent='Marque os campos para este aluno. Os valores ficam salvos mesmo ao desmarcar.';choices.append(hint);
    const checkboxes=new Map();
    [...base,...extras].forEach(field=>{const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.dataset.extraKey=field.key;label.append(check,document.createTextNode(field.label));choices.append(label);checkboxes.set(field.key,check);
      check.onchange=()=>{const state=config.getState(),chosen=new Set([...selectedBase(state.person,section),...selected(state.person,section)]);if(check.checked)chosen.add(field.key);else chosen.delete(field.key);try{config.select(extras.filter(f=>chosen.has(f.key)).map(f=>f.key),base.filter(f=>chosen.has(f.key)).map(f=>f.key));notify(state.person.id);}catch(error){check.checked=!check.checked;if(config.error)config.error(error);}};
    });
    const done=document.createElement('button');done.type='button';done.textContent='Pronto';done.onclick=()=>{choices.hidden=true;button.setAttribute('aria-expanded','false');button.focus({preventScroll:true});};choices.append(done);
    button.onclick=()=>{choices.hidden=!choices.hidden;button.setAttribute('aria-expanded',String(!choices.hidden));};
    function refresh(){
      const state=config.getState(),chosen=selected(state.person,section),baseChosen=selectedBase(state.person,section);checkboxes.forEach((check,key)=>{check.checked=chosen.includes(key)||baseChosen.includes(key);});baseNodes.forEach((node,key)=>{node.hidden=!baseChosen.includes(key);});grid.querySelectorAll('.composition-extra-field').forEach(node=>node.remove());
      extras.filter(field=>chosen.includes(field.key)).forEach(field=>{
        const wrap=document.createElement('div');wrap.className=(config.fieldClass||'field')+' composition-extra-field';const label=document.createElement('label'),input=document.createElement('input');input.id=config.prefix+field.key;input.type='text';input.inputMode=field.paired?'text':'decimal';if(field.paired)input.placeholder='Direito / Esquerdo';input.dataset.extraField=field.key;input.readOnly=!!field.readonly;if(field.readonly)input.placeholder='Preencha nas informações da ficha';input.value=value(state.person,state.av,field.key);label.htmlFor=input.id;label.textContent=field.label;wrap.append(label,input);addDetails(wrap,input,field);grid.append(wrap);
        if(!field.readonly)input.oninput=()=>{try{if(field.paired)input.value=formatPair(input.value);config.input(field.key,input.value);}catch(error){if(config.error)config.error(error);}};
      });
    }
    const instance={root,getState:config.getState,refresh,refreshValues(){const state=config.getState();fields.filter(f=>f.readonly).forEach(field=>{const input=grid.querySelector('[data-extra-field="'+field.key+'"]');if(input){input.value=value(state.person,state.av,field.key);input.dispatchEvent(new Event('input'));}});}};instances.add(instance);refresh();return instance;
  }
  function pdfRows(person,avs,delta,section='composicao',pairDelta){return catalog(section).filter(field=>selected(person,section).includes(field.key)&&avs.some(av=>filled(value(person,av,field.key)))).map(field=>[field.label,...avs.map((av,index)=>{const current=value(person,av,field.key);return filled(current)?String(current)+(index&&delta&&!field.readonly?(field.paired?(pairDelta&&pairDelta(current,value(person,avs[index-1],field.key)).trim()?'\n'+pairDelta(current,value(person,avs[index-1],field.key)).trim():''):delta(current,value(person,avs[index-1],field.key))):''):'—';})]);}
  function filterBaseRows(person,rows,section='composicao'){const enabled=selectedBase(person,section);return rows.filter(row=>{const field=baseFields[section].find(f=>f.pdf===row[0]);return !field||enabled.includes(field.key);});}
  function hasValues(person,avs,section='composicao'){return [...selectedBase(person,section),...selected(person,section)].some(key=>avs.some(av=>filled(value(person,av,key))));}
  return {fields,baseFields,measureFields,selected,selectedBase,preferenceKeys,value,filled,mount,notify,refreshValues,pdfRows,filterBaseRows,hasValues,formatPair};
})();
