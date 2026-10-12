window.ObsAutoSave = (()=>{
  const questionnaire=`Para montar seu treino de acordo com seus objetivos e necessidades, me responda:

1. Qual é seu principal objetivo com o treino?
2. Você já praticou musculação?
3. Está treinando atualmente? Se sim, quantos dias por semana?
4. Se estiver sem treinar, há quanto tempo parou e quando foi seu último treino?
5. Tem alguma dificuldade na musculação ou algum exercício que sente dificuldade em fazer?
6. Tem algum problema de saúde, lesão ou dor? Se sim, qual?
7. Qual músculo ou região do corpo você deseja desenvolver ou destacar mais?`;
  function mount(config){
    const label=document.querySelector('label[for="infoNomeCompleto"]'),row=document.createElement('div');row.className='obs-contact-heading';label.before(row);row.append(label);
    const copy=document.createElement('button');copy.type='button';copy.id='copyTrainingQuestionnaireBtn';copy.className='info-tool-btn';copy.textContent='📋 Copiar questionário';row.append(copy);
    const preview=document.createElement('details');preview.className='obs-questionnaire';preview.innerHTML='<summary>Ver questionário</summary><div></div>';preview.querySelector('div').textContent=questionnaire;row.after(preview);
    const status=document.createElement('p');status.id='obsAutoSaveStatus';status.setAttribute('role','status');status.textContent='Salvamento automático ativo';document.querySelector('.obs-header-bar').after(status);
    copy.onclick=async()=>{try{if(navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(questionnaire);else{const area=document.createElement('textarea');area.value=questionnaire;area.readOnly=true;area.style.cssText='position:fixed;left:-9999px';document.body.append(area);area.select();const done=document.execCommand('copy');area.remove();copy.focus({preventScroll:true});if(!done)throw Error('Use o texto em Ver questionário para copiar.');}status.textContent='Questionário copiado.';}catch(error){preview.open=true;status.textContent='Não foi possível copiar automaticamente. Copie o texto em Ver questionário.';}};
    let timer,running=false;
    const fingerprints=new WeakMap();
    function saved(){status.textContent='Salvo automaticamente';clearTimeout(timer);timer=setTimeout(compact,1000);}
    function failed(error){status.textContent='Não foi possível salvar automaticamente. Use Salvar OBS. '+(error.message||'');}
    async function compact(){if(running)return;running=true;try{await TreinoStorage.compactObs();}catch(error){failed(error);}finally{running=false;if(TreinoStorage.hasObsDrafts())timer=setTimeout(compact,1500);}}
    function notesChanged(guide,options={}){
      if(config.opening())return;const student=options.student||config.student()||config.ensureStudent();if(!student||!student.student_id)return;
      try{
        const state=config.state(),sameStudent=student===config.student();
        if(sameStudent)student.obsGuias=state.obs.slice();
        if(!guide)guide=sameStudent?state.obs[state.obsIndex]:null;if(!guide)return;
        const fields={titulo:guide.titulo||'',texto:guide.texto||'',textoHtml:guide.textoHtml||'',exameResultado:guide.exameResultado||'',exameResultadoHtml:guide.exameResultadoHtml||''};
        const signature=JSON.stringify([fields,(student.obsGuias||[]).map(g=>g.id)]);
        if(!options.photos&&fingerprints.get(guide)===signature)return;
        guide.obsSalvaEm=new Date().toISOString();fields.obsSalvaEm=guide.obsSalvaEm;
        TreinoStorage.stageObs(student.student_id,{obsOrder:(student.obsGuias||[]).map(g=>g.id),obs:[{id:guide.id,fields}]});
        if(options.photos){const photoFields=Array.isArray(guide.exameFotos)?{exameFotos:guide.exameFotos}:guide.exameFoto?{exameFoto:guide.exameFoto}:{exameFotos:[]};TreinoStorage.stageObs(student.student_id,{obs:[{id:guide.id,fields:photoFields}]},true);}
        fingerprints.set(guide,signature);
        student.observacoes=(student.obsGuias||[]).map(g=>(g.texto||'').trim()).filter(Boolean).join('\n---\n');
        if(sameStudent){const date=document.getElementById('obsSavedDate');date.textContent='OBS salva em '+new Date(guide.obsSalvaEm).toLocaleString('pt-BR');}
        config.indicator();saved();
      }catch(error){failed(error);}
    }
    function infoChanged(previous){
      const student=config.student()||(!config.opening()&&config.ensureStudent()),state=config.state(),guide=state.info[state.infoIndex];if(!student||!guide||config.opening()||!config.dialog.open)return;
      const fields={};for(const key of Object.keys(guide))if(previous[key]!==guide[key])fields[key]=guide[key];if(!Object.keys(fields).length)return;
      try{student.infoGuias=state.info.slice();student.infoRelevante={...guide};const studentFields={infoRelevante:student.infoRelevante};if(!guide.avaliacaoOrigemId||student.avaliacaoFichaId===guide.id){student.whatsapp=guide.whats||'';studentFields.whatsapp=student.whatsapp;}
        TreinoStorage.stageObs(student.student_id,{infoOrder:state.info.map(g=>g.id),info:[{id:guide.id,fields:{...guide}}],studentFields});saved();
      }catch(error){failed(error);}
    }
    config.dialog.addEventListener('close',()=>{clearTimeout(timer);compact();});
    config.dialog.addEventListener('focusout',()=>{clearTimeout(timer);timer=setTimeout(compact,100);});
    if(TreinoStorage.hasObsDrafts())compact();
    return {notesChanged,infoChanged,compact};
  }
  return {mount,questionnaire};
})();
