/* Editor nativo do Treino36. Cadastro e avaliações datadas usam o mesmo modelo. */
window.ObsAssessmentEditor = (() => {
  const sections={composicao:[['peso','Peso (kg)'],['imc','IMC',true],['gordura','Gordura (%)'],['visceral','Gordura visceral'],['massamuscular','Massa muscular (kg)'],['proteina','Proteína (%)'],['agua','Água (%)'],['tmb','TMB (kcal)',true],['idadeMetabolica','Idade metabólica',true]],medidas:[['peitoral','Peitoral'],['biceps','Bíceps D / E'],['barriga','Barriga'],['cintura','Cintura'],['quadril','Quadril'],['coxa','Coxa D / E']]};
  let enginePromise;
  function engine() {
    if(!enginePromise) enginePromise=new Promise((resolve,reject)=>{
      const frame=document.createElement('iframe');frame.hidden=true;frame.title='Cálculos e geração de PDF';frame.src=new URL('avaliacao.html?embed=treino36-engine&v=14',location.href).href;
      const timer=setTimeout(()=>{enginePromise=null;frame.remove();reject(Error('Não foi possível carregar os campos. Toque em Composição para tentar novamente.'));},12000);
      frame.onload=()=>{clearTimeout(timer);const api=frame.contentWindow.TreinoAssessmentEngine;if(api)resolve(api);else{enginePromise=null;frame.remove();reject(Error('Não foi possível carregar os cálculos.'));}};
      frame.onerror=()=>{clearTimeout(timer);enginePromise=null;frame.remove();reject(Error('Não foi possível carregar os cálculos.'));};document.body.appendChild(frame);
    });
    return enginePromise;
  }
  function mount(host,config) {
    let studentId,recordId,avId,section='composicao',api,opening=0,pdfChoice='auto';
    const el=(tag,attrs={},text)=>{const node=document.createElement(tag);Object.entries(attrs).forEach(([key,value])=>node.setAttribute(key,value));if(text!==undefined)node.textContent=text;return node;};
    const status=el('p',{class:'obs-assessment-status',role:'status'});
    function current(target) {const wantedRecord=target?target.recordId:recordId,wantedAv=target?target.avId:avId;const records=AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key);const person=records.find(a=>String(a.id)===String(wantedRecord));if(!person)throw Error('O cadastro deste aluno não está disponível.');const av=person.avaliacoes.find(a=>String(a.id)===String(wantedAv));return{records,person,av};}
    function persist(state) {localStorage.setItem(AvaliacaoTreinoSync.key,JSON.stringify(state.records));AvaliacaoTreinoSync.syncTraining(state.records);config.changed();status.textContent='Salvo automaticamente nesta avaliação.';}
    function update(key,value,target) {
      try {const state=current(target);if(!state.av)return;state.av[key]=value;if(key==='peso'&&state.person.avaliacoes.slice(-1)[0]===state.av){state.person.pesoAtual=value;state.person.pesoAtualAvaliacaoId=state.av.id;}api.calculate(state.person,state.av.id);persist(state);if(String(state.person.id)===String(recordId)&&String(state.av.id)===String(avId))updateResults(state);}
      catch(error){status.textContent='Não foi possível salvar: '+error.message;}
    }
    function updateResults(state) {
      sections.composicao.filter(f=>f[2]).forEach(([key])=>{const input=host.querySelector('[data-av-field="'+key+'"]');if(input)input.value=state.av[key]??'';});
      host.querySelectorAll('[data-metric]').forEach(button=>{const key=button.dataset.metric;const label=button.dataset.label;const c=api.classify(label,state.av[key],state.person.sexo);button.textContent=c.texto;button.className='obs-metric '+c.classe;});
      const result=host.querySelector('.obs-skinfold-results');if(result)result.innerHTML=api.skinfoldResults(state.av,state.person);
    }
    function field(key,label,readonly=false,renderState) {
      const state=renderState||current(),wrap=el('div',{class:'info-field'}),id='obs-av-'+key;const input=el('input',{id,'data-av-field':key,type:'text',inputmode:'decimal'});input.value=state.av[key]??'';if(readonly)input.readOnly=true;
      wrap.append(el('label',{for:id},label),input);
      input.oninput=()=>{
        if(key==='biceps'||key==='coxa') {const v=input.value.replace(/\s*\/\s*/g,' / ');if(!v.includes('/')&&/\d\s+/.test(v))input.value=v.replace(/\s+/, ' / ');}
        update(key,input.value);
      };
      if(section==='composicao') {
        const metrics={peso:['peso','Peso'],imc:['imc','IMC'],gordura:['gordura','% Gordura'],visceral:['visceral','Gordura Visceral'],massamuscular:['massamuscular','Massa Muscular'],proteina:['proteina','% Proteína'],agua:['agua','% Água'],tmb:['tmb','TMB'],idadeMetabolica:['idademetabolica','Idade Metabólica']};
        const [metric,name]=metrics[key];const button=el('button',{type:'button','data-metric':key,'data-label':name,'aria-expanded':'false'});const detail=el('div',{class:'obs-metric-detail',hidden:''});
        button.onclick=()=>{const opening=detail.hidden;host.querySelectorAll('.obs-metric-detail').forEach(d=>{d.hidden=true;d.previousElementSibling.setAttribute('aria-expanded','false');});if(opening){const state=current();detail.innerHTML=api.gauge(metric,state.av[key],state.person.sexo,state.person.idade,label);detail.hidden=false;button.setAttribute('aria-expanded','true');}};
        wrap.append(button,detail);
      }
      return wrap;
    }
    function newAssessment() {
      const state=current();let id=Date.now();while(state.person.avaliacoes.some(a=>a.id===id))id++;
      const av={id,data:new Date().toLocaleDateString('pt-BR'),protocolo:'jp7',peso:state.person.pesoAtual||state.person.pesoIni||'',fotoF:null,fotoL:null,fotoD:null};
      state.person.avaliacoes.push(av);avId=id;api.calculate(state.person,id);persist(state);render();
    }
    function render() {
      const state=current();host.replaceChildren();host.hidden=false;host.className='obs-native-assessment';
      document.querySelectorAll('#obsAssessmentSections button').forEach(b=>{const active=b.dataset.assessmentSection===section;b.setAttribute('aria-pressed',String(active));b.classList.toggle('primary',active);});
      const head=el('div',{class:'obs-assessment-head'});head.append(el('strong',{},'Avaliação de '+state.person.nome));const close=el('button',{type:'button',class:'info-tool-btn'},'Minimizar');close.onclick=()=>{host.hidden=true;if(config.minimized)config.minimized();};head.append(close);host.append(head);
      const toolbar=el('div',{class:'obs-assessment-history'});const picker=el('select',{'aria-label':'Escolher avaliação',id:'obsAssessmentHistory'});
      state.person.avaliacoes.forEach((av,index)=>{const option=el('option',{value:av.id},(index+1)+' · '+(av.data||'Sem data'));option.selected=String(av.id)===String(avId);picker.append(option);});
      picker.onchange=()=>{avId=picker.value;render();};toolbar.append(picker);const add=el('button',{type:'button',class:'info-tool-btn',id:'obsNewAssessment'},'＋ Nova');add.onclick=newAssessment;toolbar.append(add);host.append(toolbar);
      if(!state.av){host.append(el('p',{},'Crie uma avaliação para registrar a data e as medidas.'),status);return;}
      const dateWrap=el('div',{class:'obs-assessment-date info-field'}),date=el('input',{type:'date',id:'obsAssessmentDate','aria-label':'Data desta avaliação'});const parts=(state.av.data||'').split('/');date.value=parts.length===3?parts.reverse().join('-'):state.av.data||'';date.onchange=()=>{update('data',date.value.split('-').reverse().join('/'));const option=picker.selectedOptions[0];if(option)option.textContent=(picker.selectedIndex+1)+' · '+current().av.data;};dateWrap.append(el('label',{for:'obsAssessmentDate'},'Data'),date);host.append(dateWrap);
      const content=el('div',{class:'obs-assessment-fields info-grid','data-section':section});host.append(content);
      if(section==='composicao') {
        const sexWrap=el('div',{class:'info-field'}),sex=el('select',{id:'obsAssessmentSex','aria-label':'Sexo para cálculo'});
        [['F','Feminino'],['M','Masculino']].forEach(([id,label])=>{const option=el('option',{value:id},label);option.selected=id===state.person.sexo;sex.append(option);});
        sex.onchange=()=>{const state=current();state.person.sexo=sex.value;api.calculate(state.person,state.av.id);persist(state);updateResults(state);};sexWrap.append(el('label',{for:sex.id},'Sexo para cálculo'),sex);content.append(sexWrap);
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
          input.onchange=async()=>{const file=input.files[0];if(!file)return;const target={recordId,avId};try{const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file);});update(key,data,target);image.src=data;image.hidden=false;}catch(e){status.textContent='Não foi possível carregar a foto.';}};
          const remove=el('button',{type:'button',class:'info-tool-btn'},'Apagar foto');remove.onclick=()=>{update(key,null);image.removeAttribute('src');image.hidden=true;input.value='';};box.append(el('label',{for:input.id},label),image,input,remove);content.append(box);
        });
        [['motivo','Objetivo'],['resumo','Análise postural']].forEach(([key,label])=>{const wrap=el('div',{class:'info-field'}),input=el('textarea',{'data-av-field':key,id:'obs-av-'+key});input.value=state.av[key]||'';input.oninput=()=>update(key,input.value);wrap.append(el('label',{for:input.id},label),input);content.append(wrap);});
      }
      const pdfMode=el('select',{id:'obsAssessmentPdfMode','aria-label':'Conteúdo do PDF'});
      [['auto','PDF automático · partes preenchidas'],['medidas-dobras','Medidas + dobras cutâneas'],['medidas-composicao','Medidas + composição corporal'],['completo','Avaliação completa']].forEach(([id,label])=>{const option=el('option',{value:id},label);option.selected=id===pdfChoice;pdfMode.append(option);});pdfMode.onchange=()=>{pdfChoice=pdfMode.value;};
      const pdfWrap=el('div',{class:'obs-assessment-pdf-options'});pdfWrap.append(el('label',{for:pdfMode.id},'Conteúdo do PDF'),pdfMode);host.append(pdfWrap);
      const actions=el('div',{class:'info-tools-bar obs-assessment-actions'});[['save','💾 Salvar'],['pdf','📄 PDF'],['postural','📸 Postural']].forEach(([kind,label])=>{const b=el('button',{type:'button',class:'info-tool-btn'+(kind==='save'?' primary':''),id:'obsAssessment-'+kind},label);b.onclick=async()=>{try{const state=current();api.calculate(state.person,state.av.id);persist(state);if(kind!=='save'){b.disabled=true;status.textContent='Gerando PDF…';await api.pdf(state.records,state.person.id,kind,{mode:pdfMode.value});status.textContent='PDF gerado.';}else status.textContent='Avaliação salva e sincronizada.';}catch(e){status.textContent='Não foi possível concluir: '+e.message;}finally{b.disabled=false;}};actions.append(b);});host.append(actions,status);updateResults(state);
    }
    return {async open(student,nextSection,preferredRecord){const token=++opening;const previousAv=studentId===student.student_id?avId:null;studentId=student.student_id;section=nextSection||'composicao';host.hidden=false;host.replaceChildren(el('p',{},'Carregando campos…'));try{api=await engine();if(token!==opening)return;const record=preferredRecord||config.ensure(student);recordId=record.id;avId=record.avaliacoes.some(a=>String(a.id)===String(previousAv))?previousAv:record.avaliacoes.slice(-1)[0]?.id;if(!avId)newAssessment();else render();document.querySelectorAll('#obsAssessmentSections button').forEach(b=>{const active=b.dataset.assessmentSection===section;b.setAttribute('aria-pressed',String(active));b.classList.toggle('primary',active);});}catch(e){host.replaceChildren(el('p',{role:'status'},e.message));}},reset(){opening++;studentId=null;avId=null;host.hidden=true;},refresh(){if(!host.hidden&&recordId&&!host.contains(document.activeElement)){try{render();}catch(e){status.textContent=e.message;}}}};
  }
  return {mount};
})();
