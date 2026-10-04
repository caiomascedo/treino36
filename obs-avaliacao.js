/* Editor nativo do Treino36. Cadastro e avaliações datadas usam o mesmo modelo. */
window.ObsAssessmentEditor = (() => {
  const sections={composicao:[['peso','Peso (kg)'],['imc','IMC',true],['gordura','Gordura (%)'],['visceral','Gordura visceral'],['massamuscular','Massa muscular (kg)'],['proteina','Proteína (%)'],['agua','Água (%)'],['tmb','TMB (kcal)',true],['idadeMetabolica','Idade metabólica',true]],medidas:[['peitoral','Peitoral'],['biceps','Bíceps D / E'],['barriga','Barriga'],['cintura','Cintura'],['quadril','Quadril'],['coxa','Coxa D / E']]};
  let enginePromise;
  function engine() {
    if(!enginePromise) enginePromise=new Promise((resolve,reject)=>{
      const frame=document.createElement('iframe');frame.hidden=true;frame.title='Cálculos e geração de PDF';frame.src=new URL('avaliacao.html?embed=treino36-engine&v=22',location.href).href;
      let settled=false;
      function cleanup(){clearTimeout(timer);window.removeEventListener('message',ready);}
      function finish(){if(settled)return;const api=frame.contentWindow.TreinoAssessmentEngine;if(!api)return;settled=true;cleanup();resolve(api);}
      function fail(){if(settled)return;settled=true;cleanup();enginePromise=null;frame.remove();reject(Error('Não foi possível carregar os cálculos. Toque na seção para tentar novamente.'));}
      function ready(event){if(event.source===frame.contentWindow&&event.origin===location.origin&&event.data?.type==='treino36-engine-ready')finish();}
      const timer=setTimeout(fail,12000);
      window.addEventListener('message',ready);
      // Calculations are ready before remote images finish loading.
      frame.onload=()=>{finish();if(!settled)fail();};frame.onerror=fail;document.body.appendChild(frame);
    });
    return enginePromise;
  }
  function mount(host,config) {
    let studentId,recordId,avId,section='composicao',api,opening=0,pdfChoice='auto',cachedRecords=null,saveTimer,compacting=false,changedRecords=null;
    const el=(tag,attrs={},text)=>{const node=document.createElement(tag);Object.entries(attrs).forEach(([key,value])=>node.setAttribute(key,value));if(text!==undefined)node.textContent=text;return node;};
    const status=el('p',{class:'obs-assessment-status',role:'status'});
    function current(target) {const wantedRecord=target?target.recordId:recordId,wantedAv=target?target.avId:avId;const records=cachedRecords||(cachedRecords=AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key));const person=records.find(a=>String(a.id)===String(wantedRecord));if(!person)throw Error('O cadastro deste aluno não está disponível.');const av=person.avaliacoes.find(a=>String(a.id)===String(wantedAv));return{records,person,av};}
    const calculatedFields = state => Object.fromEntries(['imc','tmb','agua','idadeMetabolica','_dobras'].filter(key=>key in state.av).map(key=>[key,state.av[key]]));
    function notifyChanges(force=false) {
      if(changedRecords&&(force||!host.contains(document.activeElement))) { const records=changedRecords;changedRecords=null;config.changed(records); }
    }
    async function compact(force=false) {
      if(compacting || (!force&&host.contains(document.activeElement)))return;
      compacting=true;
      try {
        const records=await TreinoStorage.compactAssessments();
        if(records) { changedRecords=records;notifyChanges(force); }
      } catch(error) {status.textContent='A edição está guardada. O salvamento final será tentado novamente ao sair dos campos.';}
      finally {compacting=false;}
    }
    function flush() {
      clearTimeout(saveTimer);saveTimer=null;
      // Edits are already durable. The heavy work never runs on the page's keyboard thread.
      notifyChanges();compact();return true;
    }
    function stage(state,fields,personFields={}) {
      TreinoStorage.stageAssessment(state.person.id,state.av.id,{...fields,...calculatedFields(state)},personFields);
      status.textContent='Salvo automaticamente nesta avaliação.';
      clearTimeout(saveTimer);saveTimer=setTimeout(compact,1200);
    }
    function update(key,value,target) {
      try {
        const state=current(target);if(!state.av)return;
        state.av[key]=value;
        api.calculate(state.person,state.av.id);
        stage(state,{[key]:value});
        if(key==='peso'&&state.person.avaliacoes.at(-1)===state.av){state.person.pesoAtual=value;state.person.pesoAtualAvaliacaoId=state.av.id;}
        if(String(state.person.id)===String(recordId)&&String(state.av.id)===String(avId))updateResults(state);
      } catch(error){status.textContent='Não foi possível salvar: '+error.message;}
    }
    host.addEventListener('focusout',()=>{clearTimeout(saveTimer);saveTimer=setTimeout(flush,50);});
    window.addEventListener('pagehide',flush);
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')flush();});
    function updateResults(state) {
      sections.composicao.filter(f=>f[2]).forEach(([key])=>{const input=host.querySelector('[data-av-field="'+key+'"]');if(input)input.value=state.av[key]??'';});
      host.querySelectorAll('[data-metric]').forEach(button=>{const key=button.dataset.metric;const label=button.dataset.label;const c=api.classify(label,state.av[key],state.person.sexo);button.textContent=c.texto;button.className='obs-metric '+c.classe;});
      const result=host.querySelector('.obs-skinfold-results');if(result)result.innerHTML=api.skinfoldResults(state.av,state.person);
    }
    function field(key,label,readonly=false,renderState) {
      const state=renderState||current(),wrap=el('div',{class:'info-field'}),id='obs-av-'+key;const input=el('input',{id,'data-av-field':key,type:'text',inputmode:(key==='biceps'||key==='coxa')?'text':'decimal'});input.value=state.av[key]??'';if(readonly)input.readOnly=true;
      wrap.append(el('label',{for:id},label),input);
      input.oninput=()=>{
        if(key==='biceps'||key==='coxa') {const v=input.value.replace(/\s*\/\s*/g,' / ');if(!v.includes('/')&&/\d\s+\d/.test(v))input.value=v.replace(/\s+/, ' / ');}
        update(key,input.value);
      };
      if(key==='biceps'||key==='coxa'){input.placeholder='Direito / Esquerdo';}
      if(section==='composicao') {
        const metrics={peso:['peso','Peso'],imc:['imc','IMC'],gordura:['gordura','% Gordura'],visceral:['visceral','Gordura Visceral'],massamuscular:['massamuscular','Massa Muscular'],proteina:['proteina','% Proteína'],agua:['agua','% Água'],tmb:['tmb','TMB'],idadeMetabolica:['idademetabolica','Idade Metabólica']};
        const [metric,name]=metrics[key];const button=el('button',{type:'button','data-metric':key,'data-label':name,'aria-expanded':'false'});const detail=el('div',{class:'obs-metric-detail',hidden:''});
        button.onclick=()=>{const opening=detail.hidden;host.querySelectorAll('.obs-metric-detail').forEach(d=>{d.hidden=true;d.previousElementSibling.setAttribute('aria-expanded','false');});if(opening){const state=current();detail.innerHTML=api.gauge(metric,state.av[key],state.person.sexo,state.person.idade,label);detail.hidden=false;button.setAttribute('aria-expanded','true');}};
        wrap.append(button,detail);
      }
      return wrap;
    }
    function newAssessment() {
      if(!flush())return;
      const state=current();let id=Date.now();while(state.person.avaliacoes.some(a=>a.id===id))id++;
      const av={id,data:new Date().toLocaleDateString('pt-BR'),protocolo:'jp7',ficha:{idade:state.person.idade||'',altura:state.person.altura||'',dataNasc:state.person.nasc||'',nomeCompleto:state.person.nome||'',whats:state.person.whatsapp||'',email:state.person.email||''},peso:state.person.pesoAtual||state.person.pesoIni||'',fotoF:null,fotoL:null,fotoD:null};
      const draft=TreinoStorage.assessmentOperation(state.person.id,id,'add',av,{avaliacaoPreferidaId:id,avaliacaoSemRegistros:false});TreinoAssessmentJournal.merge(state.records,[draft]);avId=id;render();compact();
    }
    function deleteAssessment() {
      try {
        const state=current();if(!state.av)return;
        if(!confirm('Apagar a avaliação de '+(state.av.data||'sem data')+'? As medidas, textos e fotos desta avaliação serão excluídos.'))return;
        const draft=TreinoStorage.assessmentOperation(state.person.id,state.av.id,'delete');
        TreinoAssessmentJournal.merge(state.records,[draft]);
        avId=state.person.avaliacoes.at(-1)?.id||null;
        render();status.textContent='Avaliação apagada.';compact();
      }catch(error){status.textContent='Não foi possível apagar: '+error.message;}
    }
    function render() {
      const state=current();if(state.av)api.calculate(state.person,state.av.id);host.replaceChildren();host.hidden=false;host.className='obs-native-assessment';if(config.visibilityChanged)config.visibilityChanged(true);
      document.querySelectorAll('#obsAssessmentSections button').forEach(b=>{const active=b.dataset.assessmentSection===section;b.setAttribute('aria-pressed',String(active));b.classList.toggle('primary',active);});
      const head=el('div',{class:'obs-assessment-head'});head.append(el('strong',{},'Avaliação de '+state.person.nome));const close=el('button',{type:'button',class:'info-tool-btn'},'Minimizar');close.onclick=()=>{if(!flush())return;host.hidden=true;if(config.visibilityChanged)config.visibilityChanged(false);if(config.minimized)config.minimized();};head.append(close);host.append(head);
      const toolbar=el('div',{class:'obs-assessment-history'});const picker=el('select',{'aria-label':'Escolher avaliação',id:'obsAssessmentHistory'});
      state.person.avaliacoes.forEach((av,index)=>{const option=el('option',{value:av.id},(index+1)+' · '+(av.data||'Sem data'));option.selected=String(av.id)===String(avId);picker.append(option);});
      picker.onchange=()=>{if(!flush())return;avId=picker.value;const chosen=current();chosen.person.avaliacaoPreferidaId=chosen.av.id;stage(chosen,{}, {avaliacaoPreferidaId:chosen.av.id});render();};toolbar.append(picker);const add=el('button',{type:'button',class:'info-tool-btn',id:'obsNewAssessment'},'＋ Nova');add.onclick=newAssessment;toolbar.append(add);const remove=el('button',{type:'button',class:'info-tool-btn obs-delete-assessment',id:'obsDeleteAssessment',disabled:!state.av?'':''},'🗑 Apagar');if(state.av)remove.removeAttribute('disabled');remove.onclick=deleteAssessment;toolbar.append(remove);host.append(toolbar);
      if(!state.av){host.append(el('p',{},'Sem avaliações. Toque em Nova para adicionar.'),status);return;}
      const dateWrap=el('div',{class:'obs-assessment-date info-field'}),date=el('input',{type:'date',id:'obsAssessmentDate','aria-label':'Data desta avaliação'});const parts=(state.av.data||'').split('/');date.value=parts.length===3?parts.reverse().join('-'):state.av.data||'';date.onchange=()=>{update('data',date.value.split('-').reverse().join('/'));const option=picker.selectedOptions[0];if(option)option.textContent=(picker.selectedIndex+1)+' · '+current().av.data;};dateWrap.append(el('label',{for:'obsAssessmentDate'},'Data'),date);host.append(dateWrap);
      const content=el('div',{class:'obs-assessment-fields info-grid','data-section':section});host.append(content);
      if(section==='composicao') {
        const sexWrap=el('div',{class:'info-field'}),sex=el('select',{id:'obsAssessmentSex','aria-label':'Sexo para cálculo'});
        [['F','Feminino'],['M','Masculino']].forEach(([id,label])=>{const option=el('option',{value:id},label);option.selected=id===state.person.sexo;sex.append(option);});
        sex.onchange=()=>{if(!flush())return;const state=current();state.person.sexo=sex.value;api.calculate(state.person,state.av.id);stage(state,{}, {sexo:sex.value});updateResults(state);};sexWrap.append(el('label',{for:sex.id},'Sexo para cálculo'),sex);content.append(sexWrap);
      }
      if(sections[section])sections[section].forEach(f=>content.append(field(f[0],f[1],f[2],state)));
      if(section==='dobras') {
        const select=el('select',{id:'obsAssessmentProtocol','aria-label':'Protocolo de dobras'});[['jp7','Jackson-Pollock · 7 dobras'],['pollock3','Jackson-Pollock · 3 dobras'],['yuhasz6','Yuhasz · 6 dobras']].forEach(([id,label])=>{const option=el('option',{value:id},label);option.selected=id===(state.av.protocolo||'jp7');select.append(option);});select.onchange=()=>{update('protocolo',select.value);render();};content.append(select);
        api.protocol(state.av.protocolo).campos(state.person.sexo).forEach(key=>content.append(field(key,api.skinfoldLabel(key)+' (mm)',false,state)));
        content.append(el('div',{class:'obs-skinfold-results'}));
      }
      if(section==='fotos') {
        [['fotoF','Frontal'],['fotoL','Lateral'],['fotoD','Dorsal']].forEach(([key,label])=>{
          const box=el('div',{class:'obs-assessment-photo'}),input=el('input',{type:'file',accept:'image/*',id:'obs-av-'+key,'aria-label':'Foto '+label}),image=el('img',{alt:'Foto '+label});image.hidden=!state.av[key];if(state.av[key])image.src=state.av[key];
          input.onchange=async()=>{const file=input.files[0];if(!file)return;const target={recordId,avId};try{const data=await api.compressImage(file,800,800,0.7);update(key,data,target);flush();if(String(recordId)===String(target.recordId)&&String(avId)===String(target.avId)){const currentInput=host.querySelector('#obs-av-'+key),currentImage=currentInput&&currentInput.parentElement.querySelector('img');if(currentImage){currentImage.src=data;currentImage.hidden=false;}}}catch(e){status.textContent='Não foi possível carregar a foto.';}};
          const remove=el('button',{type:'button',class:'info-tool-btn'},'Apagar foto');remove.onclick=()=>{update(key,null);image.removeAttribute('src');image.hidden=true;input.value='';};box.append(el('label',{for:input.id},label),image,input,remove);content.append(box);
        });
        [['motivo','Objetivo'],['resumo','Análise postural']].forEach(([key,label])=>{const wrap=el('div',{class:'info-field obs-long-text'}),input=el('textarea',{'data-av-field':key,id:'obs-av-'+key});input.value=state.av[key]||'';input.oninput=()=>update(key,input.value);wrap.append(el('label',{for:input.id},label),input);content.append(wrap);});
      }
      const pdfMode=el('select',{id:'obsAssessmentPdfMode','aria-label':'Conteúdo do PDF'});
      [['auto','PDF automático · partes preenchidas'],['medidas-dobras','Medidas + dobras cutâneas'],['medidas-composicao','Medidas + composição corporal'],['completo','Avaliação completa']].forEach(([id,label])=>{const option=el('option',{value:id},label);option.selected=id===pdfChoice;pdfMode.append(option);});pdfMode.onchange=()=>{pdfChoice=pdfMode.value;};
      const pdfWrap=el('div',{class:'obs-assessment-pdf-options'});pdfWrap.append(el('label',{for:pdfMode.id},'Conteúdo do PDF'),pdfMode);host.append(pdfWrap);
      const actions=el('div',{class:'info-tools-bar obs-assessment-actions'});[['save','💾 Salvar'],['pdf','📄 PDF'],['postural','📸 Postural']].forEach(([kind,label])=>{const b=el('button',{type:'button',class:'info-tool-btn'+(kind==='save'?' primary':''),id:'obsAssessment-'+kind},label);b.onclick=async()=>{let viewer=null;try{if(!flush())return;if(kind!=='save')viewer=TreinoPDFViewer.reserve();const state=current();api.calculate(state.person,state.av.id);stage(state,{});await compact(true);if(kind!=='save'){b.disabled=true;status.textContent='Gerando PDF…';await api.pdf(AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key),state.person.id,kind,{mode:pdfMode.value,viewer});status.textContent='PDF gerado.';}else status.textContent='Avaliação salva.';}catch(e){TreinoPDFViewer.close(viewer);status.textContent='Não foi possível concluir: '+e.message;}finally{b.disabled=false;}};actions.append(b);});host.append(actions,status);updateResults(state);
    }
    return {flush,async open(student,nextSection,preferredRecord,preferredAvId){if(!flush())return;cachedRecords=null;const token=++opening;const sameStudent=studentId===student.student_id;const previousAv=preferredAvId||(sameStudent?avId:null);studentId=student.student_id;section=nextSection||'composicao';host.hidden=false;host.replaceChildren(el('p',{},'Carregando campos…'));try{api=await engine();if(token!==opening)return;const record=preferredRecord||(sameStudent&&AvaliacaoTreinoSync.resolve(AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key),student))||config.ensure(student);recordId=record.id;avId=record.avaliacoes.some(a=>String(a.id)===String(previousAv))?previousAv:(record.avaliacoes.find(a=>String(a.id)===String(record.avaliacaoPreferidaId))?.id||record.avaliacoes.slice(-1)[0]?.id);if(!avId&&!record.avaliacaoSemRegistros)newAssessment();else render();document.querySelectorAll('#obsAssessmentSections button').forEach(b=>{const active=b.dataset.assessmentSection===section;b.setAttribute('aria-pressed',String(active));b.classList.toggle('primary',active);});}catch(e){host.replaceChildren(el('p',{role:'status'},e.message));}},reset(){flush();cachedRecords=null;opening++;studentId=null;avId=null;host.hidden=true;if(config.visibilityChanged)config.visibilityChanged(false);},minimize(){if(!flush())return;opening++;host.hidden=true;if(config.visibilityChanged)config.visibilityChanged(false);if(config.minimized)config.minimized();},refresh(){if(!host.hidden&&recordId&&!host.contains(document.activeElement)){try{if(!flush())return;cachedRecords=null;const records=AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key),student=AvaliacaoTreinoSync.read('treinoAlunos').find(s=>s.student_id===studentId),person=student&&AvaliacaoTreinoSync.resolve(records,student);if(person&&String(person.id)!==String(recordId)){recordId=person.id;avId=person.avaliacaoPreferidaId||person.avaliacoes.slice(-1)[0]?.id;}render();}catch(e){status.textContent=e.message;}}}};
  }
  return {mount};
})();
