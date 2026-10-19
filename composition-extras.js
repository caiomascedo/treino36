/* Optional bioimpedance measurements: choices belong to the pupil, values to each assessment. */
window.CompositionExtras=(()=>{
  const fields=[
    {key:'pesoGordura',label:'Peso da gordura (kg)'},
    {key:'musculoEsqueleticoPct',label:'Massa muscular esquelética (%)'},
    {key:'musculoEsqueleticoKg',label:'Massa muscular esquelética (kg)'},
    {key:'massaMuscularPct',label:'Massa muscular (%)',alias:'Taxa muscular / registro de massa muscular'},
    {key:'massaLivreGordura',label:'Massa livre de gordura (kg)'},
    {key:'gorduraSubcutanea',label:'Gordura subcutânea (%)'},
    {key:'massaOssea',label:'Massa óssea (kg)'},
    {key:'pesoAgua',label:'Peso da água (kg)'},
    {key:'metabolismoInformado',label:'Metabolismo da bioimpedância (kcal/dia)',alias:'TMB da balança'},
    {key:'alturaCm',label:'Altura (cm)',readonly:true,retired:true},
    {key:'idadeReal',label:'Idade real (anos)',readonly:true,retired:true},
    ...(window.InBodyFields?.fields||[])
  ];
  const descriptions={
    pesoGordura:'Quantidade de gordura corporal em quilogramas. É diferente do percentual de gordura.',
    musculoEsqueleticoPct:'Percentual do peso corporal correspondente aos músculos esqueléticos, responsáveis pelos movimentos. É diferente da massa muscular total.',
    musculoEsqueleticoKg:'Quantidade de músculos esqueléticos em quilogramas. É diferente da massa muscular total.',
    massaMuscularPct:'Também chamada de taxa muscular ou registro de massa muscular (%) no laudo: percentual do peso corporal correspondente à massa muscular estimada pelo aparelho. Não equivale ao percentual de músculo esquelético. Massa muscular em kg é a quantidade absoluta; confira a unidade do aparelho.',
    massaLivreGordura:'Peso corporal sem a gordura. Inclui músculos, água, ossos, órgãos e outros tecidos; não é o mesmo que massa muscular.',
    gorduraSubcutanea:'Percentual de gordura localizado sob a pele. É diferente da gordura corporal total e do índice de gordura visceral.',
    massaOssea:'Estimativa da massa óssea em quilogramas informada pela balança. Não é uma medida de densidade mineral óssea.',
    pesoAgua:'Quantidade de água corporal em quilogramas. É diferente do percentual de água.',
    metabolismoInformado:'Estimativa de gasto energético em repouso informada no laudo da bioimpedância, em kcal por dia. Este valor não substitui a TMB calculada pelo aplicativo.',
    alturaCm:'Altura registrada na ficha desta avaliação, apresentada em centímetros.',
    idadeReal:'Idade registrada na ficha desta avaliação, em anos. É diferente da idade metabólica.',
    antebraco:'Circunferência dos antebraços direito e esquerdo, em centímetros, nessa ordem.',
    pescoco:'Circunferência do pescoço em centímetros.',
    panturrilhaMedida:'Circunferência das panturrilhas direita e esquerda, em centímetros, nessa ordem.'
  };
  const ratingLabels=['Baixo','Saudável','Bom','Excelente','Moderado','Elevado','Muito elevado','Abaixo','Normal','Acima'];
  const numeric=value=>{const text=String(value??'').trim().replace(',','.');return text!==''&&Number.isFinite(Number(text))?Number(text):null;};
  function classification(person,av,key){
    const field=fields.find(field=>field.key===key);
    if(field?.kind==='text')return {text:'Dado do laudo',tone:'neutral',note:field.description};
    const n=numeric(av[key]);if(n!==null&&n<0&&['target','score','impedance'].includes(field?.kind)&&!key.startsWith('controle'))return {text:'Valor inválido',tone:'neutral',note:'Confira o sinal e a unidade.'};
    if(n!==null&&['target','score','impedance'].includes(field?.kind))return {text:field.kind==='target'?'Meta do laudo':field.kind==='score'?'Pontuação do laudo':'Dado do laudo',tone:'neutral',note:field.description};
    if(n===null)return {text:'—',tone:'neutral',note:'Preencha o valor para ver a classificação.'};
    if(n<0)return {text:'Valor inválido',tone:'neutral',note:'Confira o valor informado.'};
    const manual=av[key+'Classificacao'];if(ratingLabels.includes(manual))return {text:manual,manual:true,tone:['Saudável','Bom','Excelente','Normal'].includes(manual)?'good':manual==='Moderado'?'moderate':'attention',note:'Classificação informada a partir do laudo.'};
    const refMin=numeric(av[key+'RefMin']),refMax=numeric(av[key+'RefMax']);
    if(String(av[key+'RefMin']??'').trim()!==''||String(av[key+'RefMax']??'').trim()!==''){
      if(refMin===null||refMax===null)return {text:'Completar referência',tone:'neutral',note:'Informe os limites mínimo e máximo do laudo, na mesma unidade do valor.'};
      if(refMin<0||refMax<=refMin)return {text:'Faixa inválida',tone:'neutral',note:'Confira os limites de referência do laudo.'};
      const text=n<refMin?'Abaixo':n>refMax?'Acima':'Normal',end=Math.max(n,refMax)+Math.max(1,refMax-refMin);
      return {text,tone:text==='Normal'?'good':'moderate',percent:n,zones:[{label:'Abaixo',color:'#c93732',min:0,max:refMin},{label:'Normal (laudo)',color:'#23864a',min:refMin,max:refMax},{label:'Acima',color:'#157ab8',min:refMax,max:end}],note:'Referência individual informada no laudo: '+refMin.toLocaleString('pt-BR')+' a '+refMax.toLocaleString('pt-BR')+'. Confira a mesma unidade; não é uma faixa universal.'};
    }
    const supported=['pesoGordura','musculoEsqueleticoPct','musculoEsqueleticoKg'];
    if(!supported.includes(key))return {text:'Consultar laudo',tone:'neutral',note:'Este indicador não tem uma faixa universal de saudável. Você pode registrar a classificação do laudo abaixo.'};
    const age=numeric(av.ficha?.idade??person.idade),sex=person.sexo;
    if(age===null||!['F','M'].includes(sex))return {text:'Completar ficha',tone:'neutral',note:'Informe idade e sexo na ficha para calcular a classificação.'};
    const fat=key==='pesoGordura';
    if(age<18||age>(fat?79:80))return {text:'Consultar laudo',tone:'neutral',note:'A referência automática é para adultos de 18 a '+(fat?79:80)+' anos. Use a classificação do laudo nesta idade.'};
    let percent=n;
    if(key!=='musculoEsqueleticoPct'){
      const weight=numeric(av.peso);if(weight===null||weight<=0)return {text:'Informar peso',tone:'neutral',note:'Preencha o peso desta avaliação para converter quilogramas em percentual.'};
      percent=n/weight*100;
    }
    if(percent>100)return {text:'Valor inválido',tone:'neutral',note:'O valor não pode ultrapassar 100% do peso corporal. Confira a unidade (% ou kg).'};
    const band=age<40?0:age<60?1:2;
    // OMRON HBF-511 adult reference tables; compare percentages, never kg directly.
    const ranges=fat?{F:[[21,33,39],[23,34,40],[24,36,42]],M:[[8,20,25],[11,22,28],[13,25,30]]}:{F:[[24.3,30.4,35.4],[24.1,30.2,35.2],[23.9,30,35]],M:[[33.3,39.4,44.1],[33.1,39.2,43.9],[32.9,39,43.7]]};
    const [low,high,veryHigh]=ranges[sex][band],text=percent<low?'Baixo':percent<high?'Saudável':percent<veryHigh?'Elevado':'Muito elevado';
    const zones=[{label:'Baixo',color:'#c93732',min:0,max:low},{label:'Saudável / referência',color:'#23864a',min:low,max:high},{label:'Elevado',color:fat?'#c77700':'#157ab8',min:high,max:veryHigh},{label:'Muito elevado',color:fat?'#c93732':'#157ab8',min:veryHigh,max:Math.max(60,veryHigh+10)}];
    return {text,zones,percent,tone:text==='Saudável'||(!fat&&percent>=low)?'good':text==='Elevado'?'moderate':'attention',note:'Referência OMRON HBF-511 por idade e sexo. Percentual utilizado: '+percent.toLocaleString('pt-BR',{maximumFractionDigits:1})+'%. '+(fat?'Faixa de referência: ':'Faixa normal de músculo esquelético: ')+low.toLocaleString('pt-BR')+'% a menos de '+high.toLocaleString('pt-BR')+'%.'};
  }
  function addDetails(wrap,input,field,config){
    const detail=document.createElement('details');detail.className='composition-extra-detail';
    const summary=document.createElement('summary');summary.textContent='Ver detalhes';detail.id=input.id+'-details';
    const current=document.createElement('p');current.className='composition-extra-value';
    const explanation=document.createElement('p');explanation.textContent=descriptions[field.key]||field.description||'';
        let badge=null,note=null,select=null;const gauge=document.createElement('div');gauge.className='composition-gauge';const analysis=document.createElement('strong');analysis.textContent='Análise de indicadores';analysis.className='composition-analysis-title';let updateHistory=()=>{};
    const update=()=>{
      current.textContent=field.label+': '+(filled(input.value)?input.value:'Não informado');
      if(badge){const state=config.getState(),result=classification(state.person,{...state.av,[field.key]:input.value},field.key);badge.textContent=result.text;badge.dataset.tone=result.tone;note.textContent=result.note;select.value=state.av[field.key+'Classificacao']||'';if(detail.open)CompositionContext.gauge(gauge,result);}
      if(detail.open)updateHistory();
    };
    if(!field.readonly&&!field.paired&&field.key!=='pescoco'){
      badge=document.createElement('button');badge.type='button';badge.className='composition-extra-rating badge';summary.hidden=true;detail.classList.add('composition-detail-from-rating');badge.setAttribute('aria-controls',detail.id);badge.setAttribute('aria-expanded','false');badge.onclick=()=>{detail.open=!detail.open;};wrap.append(badge);
      note=document.createElement('p');const label=document.createElement('label');label.textContent='Classificação do laudo';if(['target','score','impedance','text'].includes(field.kind))label.hidden=true;select=document.createElement('select');select.setAttribute('aria-label','Classificação do laudo: '+field.label);
      ['',...ratingLabels].forEach(text=>{const option=document.createElement('option');option.value=text;option.textContent=text||'Automática / não informada';select.append(option);});
      select.onchange=()=>{try{config.input(field.key+'Classificacao',select.value);update();}catch(error){if(config.error)config.error(error);}};label.append(select);detail.append(note,label);
      if(!['target','score','impedance','text'].includes(field.kind)){
        const reference=document.createElement('fieldset');reference.className='composition-reference';const legend=document.createElement('legend');legend.textContent='Faixa normal do laudo (opcional)';reference.append(legend);
        [['RefMin','Mínimo'],['RefMax','Máximo']].forEach(([suffix,title])=>{const bound=document.createElement('input');bound.type='text';bound.inputMode='decimal';bound.placeholder=title;bound.setAttribute('aria-label',title+' do laudo: '+field.label);bound.value=config.getState().av[field.key+suffix]??'';bound.oninput=()=>{try{config.input(field.key+suffix,bound.value);update();}catch(error){if(config.error)config.error(error);}};reference.append(bound);});detail.append(reference);
      }
    }
    detail.addEventListener('toggle',()=>{if(badge)badge.setAttribute('aria-expanded',String(detail.open));if(detail.open)update();});input.addEventListener('input',update);input.addEventListener('composition-value-refresh',update);
    detail.prepend(summary,current,gauge,analysis,explanation);wrap.append(detail);if(config.section!=='medidas')updateHistory=CompositionContext.mountHistory(detail,input,field,config);update();
    return update;
  }
  const baseFields={
    composicao:[{key:'peso',label:'Peso (kg)',pdf:'Peso (kg)'},{key:'imc',label:'IMC',pdf:'IMC'},{key:'gordura',label:'Gordura (%)',pdf:'% Gordura'},{key:'visceral',label:'Gordura visceral',pdf:'Gordura Visceral'},{key:'massamuscular',label:'Massa muscular (kg)',pdf:'Massa Muscular (kg)'},{key:'proteina',label:'Proteína (%)',pdf:'% Proteína'},{key:'agua',label:'Água (%)',pdf:'% Água'},{key:'tmb',label:'TMB (kcal)',pdf:'TMB (kcal)'},{key:'idadeMetabolica',label:'Idade metabólica',pdf:'Idade Metabólica'}],
    medidas:[{key:'peitoral',label:'Peitoral',pdf:'Peitoral'},{key:'biceps',label:'Bíceps D / E',pdf:'Bíceps D/E'},{key:'barriga',label:'Barriga',pdf:'Abdômen'},{key:'cintura',label:'Cintura',pdf:'Cintura'},{key:'quadril',label:'Quadril',pdf:'Quadril'},{key:'coxa',label:'Coxa D / E',pdf:'Coxa D/E'}]
  };
  const measureFields=[{key:'antebraco',label:'Antebraço D / E',paired:true},{key:'pescoco',label:'Pescoço'},{key:'panturrilhaMedida',label:'Panturrilha D / E',paired:true}];
  const preferenceKeys=section=>section==='medidas'?{base:'medidasCampos',extra:'medidasExtras'}:{base:'composicaoCampos',extra:'composicaoExtras'};
  const catalog=section=>section==='medidas'?measureFields:fields;
  const unitGroups=[
    {key:'gordura',label:'Gordura corporal',members:[['gordura','%'],['pesoGordura','kg']]},
    {key:'massamuscular',label:'Massa muscular total',members:[['massamuscular','kg'],['massaMuscularPct','% · taxa muscular']]},
    {key:'agua',label:'Água corporal',members:[['agua','%'],['pesoAgua','kg'],['aguaLitros','L · InBody']]},
    {key:'proteina',label:'Proteína',members:[['proteina','%'],['proteinaKg','kg · InBody']]},
    {key:'tmb',label:'TMB (kcal/dia)',members:[['tmb','Calculada'],['metabolismoInformado','Informada · balança/InBody']]},
    {key:'musculoEsqueletico',label:'Massa muscular esquelética',members:[['musculoEsqueleticoKg','kg'],['musculoEsqueleticoPct','%']]}
  ];
  function rawSelection(person,section){
    const prefs=preferenceKeys(section),base=baseFields[section].map(f=>f.key),extra=catalog(section).filter(f=>!f.retired).map(f=>f.key);
    return new Set([...(Array.isArray(person[prefs.base])?person[prefs.base].filter(key=>base.includes(key)):base),...(Array.isArray(person[prefs.extra])?person[prefs.extra].filter(key=>extra.includes(key)):[])]);
  }
  function activeSelection(person,section='composicao'){
    return rawSelection(person,section);
  }
  function orderedKeys(section='composicao'){
    const keys=[...baseFields[section],...catalog(section).filter(field=>!field.retired)].map(field=>field.key),ordered=[];
    for(const key of keys){const group=section==='composicao'&&unitGroups.find(group=>group.members.some(([member])=>member===key));for(const member of group?group.members.map(([member])=>member):[key])if(!ordered.includes(member))ordered.push(member);}
    return ordered;
  }
  const selectedBase=(person,section='composicao')=>baseFields[section].filter(field=>activeSelection(person,section).has(field.key)).map(field=>field.key);
  const instances=new Set();
  const selected=(person,section='composicao')=>catalog(section).filter(field=>!field.retired&&activeSelection(person,section).has(field.key)).map(field=>field.key);
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
    const section=config.section||'composicao',base=baseFields[section],extras=catalog(section).filter(field=>!field.retired);
    const baseNodes=new Map();[...grid.children].filter(node=>!node.classList.contains('composition-extra-field')).slice(-base.length).forEach((node,index)=>baseNodes.set(base[index].key,node));
    const button=document.createElement('button');button.type='button';button.className='composition-extras-add';button.textContent='＋ Adicionar campos';button.setAttribute('aria-expanded','false');
    const choices=document.createElement('div');choices.className='composition-extras-choices';choices.hidden=true;
    const id=config.prefix+section+'-extra-options';choices.id=id;button.setAttribute('aria-controls',id);root.append(button,choices);
    const hint=document.createElement('p');hint.textContent=section==='medidas'?'Marque os campos para este aluno. Os valores ficam salvos mesmo ao desmarcar.':'Padrão identifica seus campos originais. Marque as medidas que deseja juntas na tela e no PDF. Desmarcar não apaga os valores.';choices.append(hint);
    const checkboxes=new Map(),standard=document.createElement('fieldset'),additional=document.createElement('fieldset'),inbodyGroups=new Map();
    [[section==='medidas'?'Medidas padrão':'Composição · padrão e medidas relacionadas',standard],[section==='medidas'?'Medidas adicionais':'Adicionais',additional]].forEach(([text,group])=>{const legend=document.createElement('legend');legend.textContent=text;group.append(legend);choices.append(group);});
    if(section==='composicao')for(const [key,title] of [['inbody','InBody · dados do laudo'],['inbody-lean','InBody · massa magra segmentar'],['inbody-fat','InBody · gordura segmentar'],['inbody-impedance','InBody · impedância 20/100 kHz']]){const group=document.createElement('details'),summary=document.createElement('summary');summary.textContent=title;group.className='composition-inbody-options';group.append(summary);choices.append(group);inbodyGroups.set(key,group);}
    const saveChoice=(key,enabled)=>{
      const state=config.getState(),chosen=activeSelection(state.person,section);
      if(enabled)chosen.add(key);else chosen.delete(key);
      config.select(extras.filter(f=>chosen.has(f.key)).map(f=>f.key),base.filter(f=>chosen.has(f.key)).map(f=>f.key));notify(state.person.id);
    };
    const addChoice=(field,target)=>{
      const label=document.createElement('label'),check=document.createElement('input'),name=document.createElement('span');check.type='checkbox';check.dataset.extraKey=field.key;name.textContent=field.label+(field.alias?' · '+field.alias:'');label.append(check,name);target.append(label);checkboxes.set(field.key,check);
      if(section==='composicao'&&base.some(f=>f.key===field.key)){const tag=document.createElement('small');tag.className='composition-default-tag';tag.textContent='Padrão';name.append(tag);}
      check.onchange=()=>{try{saveChoice(field.key,check.checked);}catch(error){check.checked=!check.checked;if(config.error)config.error(error);}};
    };
    const grouped=new Set(section==='composicao'?unitGroups.flatMap(group=>group.members.map(([key])=>key)):[]);
    const definitions=new Map([...base,...extras].map(field=>[field.key,field])),rendered=new Set();
    for(const key of orderedKeys(section)){
      if(rendered.has(key))continue;
      const group=section==='composicao'&&unitGroups.find(group=>group.members.some(([member])=>member===key));
      if(group){const box=document.createElement('fieldset');box.className='composition-choice-group';box.dataset.metricGroup=group.key;const legend=document.createElement('legend');legend.textContent=group.label;box.append(legend);standard.append(box);for(const [member] of group.members){addChoice(definitions.get(member),box);rendered.add(member);}}
      else if(base.some(field=>field.key===key)){addChoice(definitions.get(key),standard);rendered.add(key);}
    }
    extras.filter(field=>!grouped.has(field.key)).forEach(field=>addChoice(field,inbodyGroups.get(field.group)||additional));
    const done=document.createElement('button');done.type='button';done.textContent='Pronto';done.onclick=()=>{choices.hidden=true;button.setAttribute('aria-expanded','false');button.focus({preventScroll:true});};choices.append(done);
    button.onclick=()=>{choices.hidden=!choices.hidden;button.setAttribute('aria-expanded',String(!choices.hidden));};
    function refresh(){
      const state=config.getState(),chosen=selected(state.person,section),baseChosen=selectedBase(state.person,section);checkboxes.forEach((check,key)=>{check.checked=chosen.includes(key)||baseChosen.includes(key);});baseNodes.forEach((node,key)=>{node.hidden=!baseChosen.includes(key);});grid.querySelectorAll('.composition-related-fields').forEach(node=>node.replaceWith(...node.children));grid.querySelectorAll('.composition-extra-field').forEach(node=>node.remove());
      extras.filter(field=>chosen.includes(field.key)).forEach(field=>{
        const wrap=document.createElement('div');wrap.className=(config.fieldClass||'field')+' composition-extra-field';const label=document.createElement('label'),input=document.createElement('input');input.id=config.prefix+field.key;input.type='text';input.inputMode=field.paired||['target','text'].includes(field.kind)?'text':'decimal';if(field.paired)input.placeholder='Direito / Esquerdo';input.dataset.extraField=field.key;input.readOnly=!!field.readonly;if(field.readonly)input.placeholder='Preencha nas informações da ficha';input.value=value(state.person,state.av,field.key);label.htmlFor=input.id;label.textContent=field.label;wrap.append(label,input);addDetails(wrap,input,field,config);grid.append(wrap);
        if(!field.readonly)input.oninput=()=>{try{if(field.paired)input.value=formatPair(input.value);const state=config.getState();config.input(field.key,input.value,section==='composicao'?CompositionContext.record(state.av,field.key,input.value,''):{});}catch(error){if(config.error)config.error(error);}};
      });
      if(section==='composicao'){
        const nodes=new Map(baseNodes);grid.querySelectorAll('.composition-extra-field').forEach(node=>nodes.set(node.querySelector('[data-extra-field]').dataset.extraField,node));const placed=new Set();
        for(const key of orderedKeys(section)){
          if(placed.has(key))continue;const group=unitGroups.find(group=>group.members.some(([member])=>member===key)),members=(group?group.members.map(([member])=>member):[key]).filter(member=>nodes.has(member));
          const visible=members.filter(member=>!nodes.get(member).hidden),target=visible.length>1?document.createElement('div'):grid;
          if(target!==grid){target.className='composition-related-fields';target.dataset.metricGroup=group.key;grid.append(target);}
          for(const member of members){target.append(nodes.get(member));placed.add(member);}
        }
      }
    }
    const instance={root,getState:config.getState,refresh,refreshValues(){const state=config.getState();grid.querySelectorAll('[data-extra-field]').forEach(input=>{const field=fields.find(field=>field.key===input.dataset.extraField);if(field?.readonly)input.value=value(state.person,state.av,field.key);input.dispatchEvent(new Event('composition-value-refresh'));});}};instances.add(instance);refresh();return instance;
  }
  function pdfRows(person,avs,delta,section='composicao',pairDelta){return catalog(section).filter(field=>selected(person,section).includes(field.key)&&avs.some(av=>filled(value(person,av,field.key)))).map(field=>[field.label,...avs.map((av,index)=>{const current=value(person,av,field.key);return filled(current)?String(current)+(index&&delta&&!field.readonly?(field.paired?(pairDelta&&pairDelta(current,value(person,avs[index-1],field.key)).trim()?'\n'+pairDelta(current,value(person,avs[index-1],field.key)).trim():''):delta(current,value(person,avs[index-1],field.key))):''):'—';})]);}
  function filterBaseRows(person,rows,section='composicao'){const enabled=selectedBase(person,section);return rows.filter(row=>{const field=baseFields[section].find(f=>f.pdf===row[0]);return !field||enabled.includes(field.key);});}
  function orderRows(rows,section='composicao'){
    const labels=new Map([...baseFields[section].map(field=>[field.pdf,field.key]),...catalog(section).map(field=>[field.label,field.key])]),order=orderedKeys(section);
    return [...rows].sort((a,b)=>order.indexOf(labels.get(a[0]))-order.indexOf(labels.get(b[0])));
  }
  function hasValues(person,avs,section='composicao'){return [...selectedBase(person,section),...selected(person,section)].some(key=>avs.some(av=>filled(value(person,av,key))));}
  return {classification,unitGroups,activeSelection,orderedKeys,orderRows,fields,baseFields,measureFields,selected,selectedBase,preferenceKeys,value,filled,mount,notify,refreshValues,pdfRows,filterBaseRows,hasValues,formatPair};
})();
