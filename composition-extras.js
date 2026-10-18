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
  const keys=new Set(fields.map(f=>f.key)),instances=new Set();
  const selected=person=>[...new Set((Array.isArray(person.composicaoExtras)?person.composicaoExtras:[]).filter(key=>keys.has(key)))];
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
    const button=document.createElement('button');button.type='button';button.className='composition-extras-add';button.textContent='＋ Adicionar campos';button.setAttribute('aria-expanded','false');
    const choices=document.createElement('div');choices.className='composition-extras-choices';choices.hidden=true;
    const id=config.prefix+'extra-options';choices.id=id;button.setAttribute('aria-controls',id);root.append(button,choices);
    const hint=document.createElement('p');hint.textContent='Marque os campos para este aluno. Os valores ficam salvos mesmo ao desmarcar.';choices.append(hint);
    const checkboxes=new Map();
    fields.forEach(field=>{const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.dataset.extraKey=field.key;label.append(check,document.createTextNode(field.label));choices.append(label);checkboxes.set(field.key,check);
      check.onchange=()=>{const state=config.getState(),chosen=selected(state.person);const next=check.checked?[...chosen,field.key]:chosen.filter(key=>key!==field.key);try{config.select(next);notify(state.person.id);}catch(error){check.checked=!check.checked;if(config.error)config.error(error);}};
    });
    const done=document.createElement('button');done.type='button';done.textContent='Pronto';done.onclick=()=>{choices.hidden=true;button.setAttribute('aria-expanded','false');button.focus({preventScroll:true});};choices.append(done);
    button.onclick=()=>{choices.hidden=!choices.hidden;button.setAttribute('aria-expanded',String(!choices.hidden));};
    function refresh(){
      const state=config.getState(),chosen=selected(state.person);checkboxes.forEach((check,key)=>{check.checked=chosen.includes(key);});grid.querySelectorAll('.composition-extra-field').forEach(node=>node.remove());
      fields.filter(field=>chosen.includes(field.key)).forEach(field=>{
        const wrap=document.createElement('div');wrap.className=(config.fieldClass||'field')+' composition-extra-field';const label=document.createElement('label'),input=document.createElement('input');input.id=config.prefix+field.key;input.type='text';input.inputMode='decimal';input.dataset.extraField=field.key;input.readOnly=!!field.readonly;if(field.readonly)input.placeholder='Preencha nas informações da ficha';input.value=value(state.person,state.av,field.key);label.htmlFor=input.id;label.textContent=field.label;wrap.append(label,input);grid.append(wrap);
        if(!field.readonly)input.oninput=()=>{try{config.input(field.key,input.value);}catch(error){if(config.error)config.error(error);}};
      });
    }
    const instance={root,getState:config.getState,refresh,refreshValues(){const state=config.getState();fields.filter(f=>f.readonly).forEach(field=>{const input=grid.querySelector('[data-extra-field="'+field.key+'"]');if(input)input.value=value(state.person,state.av,field.key);});}};instances.add(instance);refresh();return instance;
  }
  function pdfRows(person,avs,delta){return fields.filter(field=>selected(person).includes(field.key)&&avs.some(av=>filled(value(person,av,field.key)))).map(field=>[field.label,...avs.map((av,index)=>{const current=value(person,av,field.key);return filled(current)?String(current)+(index&&delta&&!field.readonly?delta(current,value(person,avs[index-1],field.key)):''):'—';})]);}
  return {fields,selected,value,filled,mount,notify,refreshValues,pdfRows};
})();
