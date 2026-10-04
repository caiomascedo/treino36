window.WorkoutValidity = (() => {
  const today=()=>{const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');};
  const parse=value=>{if(!/^\d{4}-\d{2}-\d{2}$/.test(value||''))throw Error('Informe a data de início.');const d=new Date(value+'T00:00:00Z');if(!Number.isFinite(d.getTime())||d.toISOString().slice(0,10)!==value)throw Error('Data inválida.');return d;};
  function calculate(start,period){
    const d=parse(start),n=Number(period.amount);if(!Number.isSafeInteger(n)||n<1||n>36500)throw Error('Informe um prazo em dias maior que zero.');
    if(period.unit==='months'){const day=d.getUTCDate();d.setUTCDate(1);d.setUTCMonth(d.getUTCMonth()+n);const last=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,0)).getUTCDate();d.setUTCDate(Math.min(day,last));}
    else if(period.unit==='days')d.setUTCDate(d.getUTCDate()+n);
    else throw Error('Prazo inválido.');
    return d.toISOString().slice(0,10);
  }
  function get(student){const validity=student&&student.validadeTreino;return validity&&validity.treinoId===student.treino_id?validity:null;}
  const format=value=>value.split('-').reverse().join('/');
  function summary(student){const v=get(student);return v?'Validade: '+format(v.until)+(v.until<today()?' · Vencido':v.until===today()?' · Vence hoje':''):'';}
  const options='<option value="none">Sem validade</option><option value="d7">1 semana</option><option value="d14">2 semanas</option><option value="m1">1 mês</option><option value="d45">45 dias</option><option value="m2">2 meses</option><option value="m3">3 meses</option><option value="custom">Outro prazo (dias)</option>';
  function mount(config){
    const dialog=config.createDialog('workoutValidityDialog','📅 Validade do treino',
      '<p id="validityStudent"></p><label for="validityStart">Data de início</label><input type="date" id="validityStart">'+
      '<label for="validityPeriod">Prazo</label><select id="validityPeriod">'+options+'</select>'+ 
      '<label id="validityCustomLabel" for="validityCustom" hidden>Prazo em dias</label><input id="validityCustom" type="number" inputmode="numeric" min="1" step="1" hidden>'+ 
      '<p id="validityPreview" aria-live="polite"></p>'+ 
      '<label for="validityRenewal">Renovação</label><select id="validityRenewal"><option value="same">Mesmo prazo</option><option value="none">Não renovar</option>'+options.replace('<option value="none">Sem validade</option>','')+'</select>'+ 
      '<label id="renewalCustomLabel" for="renewalCustom" hidden>Renovar por quantos dias?</label><input id="renewalCustom" type="number" inputmode="numeric" min="1" step="1" hidden>'+ 
      '<p id="renewalPreview" aria-live="polite"></p><p>A renovação só acontece ao clicar em Renovar agora.</p><p id="validityStatus" role="status"></p>'+ 
      '<button type="button" id="saveWorkoutValidity" class="primary">Salvar validade</button> <button type="button" id="renewWorkoutValidity">Renovar agora</button> <button type="button" data-close>Fechar</button>');
    let studentId,workoutId;
    const $=id=>dialog.querySelector('#'+id);
    function period(value,input){if(value==='none')return null;return value==='custom'?{unit:'days',amount:Number(input.value)}:{unit:value[0]==='m'?'months':'days',amount:Number(value.slice(1))};}
    function refresh(){const text=summary(config.selected());config.summary.textContent=text;config.summary.hidden=!text;}
    function renewalStart(){const v=get(config.find(studentId));return v&&v.until>today()?v.until:today();}
    function preview(){
      const custom=$('validityPeriod').value==='custom',renewCustom=$('validityRenewal').value==='custom';
      $('validityCustom').hidden=$('validityCustomLabel').hidden=!custom;$('renewalCustom').hidden=$('renewalCustomLabel').hidden=!renewCustom;
      $('renewWorkoutValidity').disabled=$('validityPeriod').value==='none'||$('validityRenewal').value==='none';
      try{const p=period($('validityPeriod').value,$('validityCustom'));$('validityPreview').textContent=p?'Válido até '+format(calculate($('validityStart').value,p)):'Sem validade definida.';}catch(error){$('validityPreview').textContent=error.message;}
      try{const choice=$('validityRenewal').value,p=choice==='same'?period($('validityPeriod').value,$('validityCustom')):choice==='none'?null:period(choice,$('renewalCustom'));$('renewalPreview').textContent=p?'Ao renovar, válido até '+format(calculate(renewalStart(),p)):'';}catch(error){$('renewalPreview').textContent=error.message;}
    }
    function open(){
      const student=config.selected();if(!student){config.message('Selecione um aluno salvo para definir a validade.','#b22222',false);return;}
      studentId=student.student_id;workoutId=student.treino_id;
      const v=get(student);$('validityStudent').textContent=student.nome;$('validityStart').value=v?v.start:today();
      const value=v?(v.period.unit==='months'?'m':'d')+v.period.amount:'none';
      $('validityPeriod').value=[...$('validityPeriod').options].some(o=>o.value===value)?value:'custom';$('validityCustom').value=v?v.period.amount:'';
      $('validityRenewal').value=v?v.renewal||'same':'same';$('renewalCustom').value=v?v.renewalDays||'':'';
      $('validityStatus').textContent='';preview();dialog.showModal();
    }
    function save(renew){
      try{
        const student=config.find(studentId);if(!student||student.treino_id!==workoutId)throw Error('O treino mudou. Feche e abra a validade novamente.');
        let p=period($('validityPeriod').value,$('validityCustom')),start=$('validityStart').value;
        const renewal=$('validityRenewal').value;
        if(renew){if(renewal==='none')return;if(renewal!=='same')p=period(renewal,$('renewalCustom'));if(!p)throw Error('Escolha um prazo para renovar.');start=renewalStart();}
        if(renewal==='custom')calculate(start,{unit:'days',amount:Number($('renewalCustom').value)});
        const before=student.validadeTreino;
        if(p)student.validadeTreino={treinoId:workoutId,start,period:p,until:calculate(start,p),renewal,renewalDays:renewal==='custom'?Number($('renewalCustom').value):null};
        else delete student.validadeTreino;
        if(!config.save()){if(before)student.validadeTreino=before;else delete student.validadeTreino;throw Error('Não foi possível salvar a validade.');}
        refresh();dialog.close();
      }catch(error){$('validityStatus').textContent=error.message;}
    }
    dialog.querySelectorAll('input,select').forEach(input=>input.addEventListener('input',preview));
    $('saveWorkoutValidity').onclick=()=>save(false);$('renewWorkoutValidity').onclick=()=>save(true);
    config.button.onclick=open;return{refresh,open};
  }
  return{today,calculate,get,summary,mount};
})();
