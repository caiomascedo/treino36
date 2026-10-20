/* Manual attendance markers; viewing or editing a workout never completes it. */
window.WorkoutSequence=(()=>{
  const letters=['A','B','C','D','E','F'];
  function sections(student){return letters.filter(key=>(key!=='F'||student?.secaoFAtiva)&&Array.isArray(student?.treino?.[key])&&student.treino[key].some(line=>typeof line==='string'&&line.trim()&&!/^(?:⚠️\s*)?(?:Sem treino cadastrado|Sem exercícios|Nenhum exercício|Seção vazia|Nenhum aluno)[.!\s]*$/i.test(line.trim())));}
  function sanitize(value,previous=true){
    if(!value||typeof value.treinoId!=='string'||!letters.includes(value.ultima)||typeof value.feitoEm!=='string'||!Number.isFinite(Date.parse(value.feitoEm)))return null;
    return {treinoId:value.treinoId,ultima:value.ultima,feitoEm:value.feitoEm,podeDesfazer:value.podeDesfazer!==false,anterior:previous?sanitize(value.anterior,false):null};
  }
  function get(student){const value=sanitize(student?.sequenciaTreino);return value&&value.treinoId===student?.treino_id?value:null;}
  function describe(student){const order=sections(student),progress=get(student),last=progress?.ultima||null,index=order.indexOf(last);return {order,progress,last,next:order.length?order[(index+1)%order.length]:null,removed:!!last&&index<0};}
  function summary(student){const state=describe(student);return state.next?(state.last?'Último feito: '+state.last+' · ':'Sem marcação · ')+'Próximo: '+state.next:'';}
  function mark(student,key,now=new Date().toISOString()){
    if(!student?.treino_id||!sections(student).includes(key))throw Error('Escolha um treino desta divisão.');
    const value=sanitize({treinoId:student.treino_id,ultima:key,feitoEm:now,anterior:get(student)});
    if(!value)throw Error('Não foi possível registrar a data do treino.');return value;
  }
  const el=(tag,attributes={},text)=>{const node=document.createElement(tag);for(const [key,value] of Object.entries(attributes))node.setAttribute(key,value);if(text!==undefined)node.textContent=text;return node;};
  function mount(root,config){
    root.className='workout-sequence';root.hidden=true;root.setAttribute('data-html2canvas-ignore','true');
    const heading=el('div',{class:'sequence-heading'}),next=el('strong',{id:'sequenceNext'}),last=el('span',{id:'sequenceLast'}),division=el('small',{id:'sequenceDivision'}),actions=el('div',{class:'sequence-actions'}),complete=el('button',{type:'button',id:'sequenceComplete'}),undo=el('button',{type:'button',id:'sequenceUndo'},'Desfazer marcação'),adjust=el('details',{id:'sequenceAdjust'}),select=el('select',{id:'sequenceLastChoice','aria-label':'Treino que foi feito'}),save=el('button',{type:'button',id:'sequenceSet'},'Marcar como feito'),clear=el('button',{type:'button',id:'sequenceClear'},'Limpar marcação'),status=el('p',{id:'sequenceStatus',role:'status'});
    heading.append(next,last);actions.append(complete,undo);adjust.append(el('summary',{},'Marcar outro / corrigir'),el('label',{for:select.id},'Qual treino foi feito?'),select,save,clear);root.append(heading,division,actions,adjust,status);
    let shown=null,lockedUntil=0,timer;
    function current(){const selected=config.selected();return selected?config.read(selected.student_id)||selected:null;}
    function refresh(){
      const student=current(),state=describe(student),identity=student?student.student_id+':'+student.treino_id:null;
      if(identity!==shown?.identity){status.textContent='';adjust.open=false;}
      root.hidden=!student||!state.order.length;
      shown=student?{identity,studentId:student.student_id,workoutId:student.treino_id,next:state.next}:null;
      if(root.hidden)return;
      const matches=config.matches(student);next.textContent='Próximo: '+state.next;
      last.textContent=state.last?'Último feito: '+state.last+' · '+new Date(state.progress.feitoEm).toLocaleDateString('pt-BR'):'Nenhum treino marcado ainda';
      last.title=state.last?new Date(state.progress.feitoEm).toLocaleString('pt-BR'):'';
      division.textContent='Sequência '+state.order.join(' → ')+(state.removed?' · O último marcado não está mais nesta divisão.':'');
      complete.textContent='✓ Fiz o treino '+state.next;complete.disabled=!matches||Date.now()<lockedUntil;
      clear.disabled=!matches||!state.progress;undo.disabled=clear.disabled||state.progress?.podeDesfazer===false;
      select.replaceChildren(...state.order.map(key=>el('option',{value:key},key+(student.titulos?.[key]?' — '+student.titulos[key].replace(/^[A-F][.\s-]+/i,''):''))));
      select.value=state.last&&state.order.includes(state.last)?state.last:state.next;
      save.disabled=select.disabled=!matches;
      if(!matches)status.textContent='Salve o treino exibido para marcar a sequência dele.';
      else if(status.textContent==='Salve o treino exibido para marcar a sequência dele.')status.textContent='';
    }
    function change(action,key){
      const expected=shown&&{...shown};
      try{
        if(!expected)throw Error('Selecione um aluno salvo.');
        config.beforeChange();const student=current();
        if(!student||student.student_id!==expected.studentId||student.treino_id!==expected.workoutId)throw Error('O treino mudou. Confira a sequência antes de marcar.');
        if(!config.matches(student))throw Error('Salve o treino exibido antes de marcar.');
        const progress=get(student),value=action==='mark'?mark(student,key):action==='undo'?sanitize(progress?.anterior):null;
        if(action==='undo'&&value)value.podeDesfazer=false;
        config.save(student,value);
        if(action==='mark'){lockedUntil=Date.now()+700;clearTimeout(timer);timer=setTimeout(()=>{const selected=current();complete.disabled=!selected||!config.matches(selected);},710);}
        refresh();status.textContent=action==='mark'?'Treino '+key+' marcado como feito.':action==='undo'?'Última marcação desfeita.':'Marcação limpa.';
      }catch(error){refresh();status.textContent=error.message||'Não foi possível salvar a marcação.';}
    }
    complete.onclick=()=>{if(!complete.disabled)change('mark',shown?.next);};save.onclick=()=>change('mark',select.value);undo.onclick=()=>change('undo');clear.onclick=()=>change('clear');
    window.addEventListener('storage',event=>{if(['treinoAlunos','treino36_obs_drafts'].includes(event.key)){status.textContent='';refresh();}});
    refresh();return {refresh};
  }
  return {sections,sanitize,get,describe,summary,mark,mount};
})();
