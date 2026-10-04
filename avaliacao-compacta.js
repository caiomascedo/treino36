/* Navegação compacta do formulário no Treino36. Os dados e PDFs usam o modelo original. */
const secoesAvaliacao = new Map();
const chaveNotificacoesAvaliacao = 'avaliacao_notificacoes_ativas';
function notificacoesAvaliacaoAtivas() { return localStorage.getItem(chaveNotificacoesAvaliacao)==='1'; }
function atualizarControleNotificacoes() {
  const control=document.getElementById('assessmentNotificationsToggle');
  if(control) { control.checked=notificacoesAvaliacaoAtivas(); control.setAttribute('aria-checked',String(control.checked)); }
  const status=document.getElementById('assessmentNotificationsStatus');
  if(status) status.textContent=notificacoesAvaliacaoAtivas()?'Avisos ligados':'Avisos desligados';
}
async function alternarNotificacoesAvaliacao(enabled) {
  localStorage.setItem(chaveNotificacoesAvaliacao,enabled?'1':'0');
  atualizarControleNotificacoes();
  renderizarBannerRenovacoes(getAlunosComPendencias());
  if(!enabled) { const toast=document.getElementById('notif'); if(toast) toast.style.opacity='0'; return; }
  if('Notification' in window) {
    try {
      const permission=Notification.permission==='default'?await Notification.requestPermission():Notification.permission;
      if(!notificacoesAvaliacaoAtivas()) return;
      if(permission==='granted') verificarRenovacoesEnviarNotificacao(true);
      else document.getElementById('assessmentNotificationsStatus').textContent='Avisos na avaliação ligados';
    } catch(e) { if(notificacoesAvaliacaoAtivas()) document.getElementById('assessmentNotificationsStatus').textContent='Avisos na avaliação ligados'; }
  }
}
function carregarFotosDaAvaliacao(panel) {
  const card=panel.closest('.aluno-card'),item=panel.closest('.av-item');
  const person=alunos.find(a=>String(a.id)===card?.dataset.alunoCard);
  const av=person?.avaliacoes?.find(a=>String(a.id)===item?.id.slice('av-item-'.length));
  if(!av)return;
  panel.querySelectorAll('img[data-assessment-photo]').forEach(image=>{const src=av[image.dataset.assessmentPhoto];if(src&&image.getAttribute('src')!==src)image.src=src;image.style.display=src?'block':'none';});
}
function abasCompactas(host, key, groups, initial) {
  const nav = document.createElement('div'); nav.className = 'assessment-tabs'; nav.setAttribute('role','tablist');
  const current = secoesAvaliacao.get(key) || initial;
  groups.forEach(([id, label, nodes]) => {
    const panel = document.createElement('section'); panel.id = key + '-' + id; panel.className = 'assessment-tab-panel'; panel.setAttribute('role','tabpanel');
    nodes.forEach(node => panel.appendChild(node));
    const button = document.createElement('button'); button.type = 'button'; button.textContent = label; button.dataset.section = id; button.setAttribute('role','tab'); button.setAttribute('aria-controls',panel.id);
    button.id = panel.id + '-tab'; panel.setAttribute('aria-labelledby',button.id);
    button.onclick = () => { secoesAvaliacao.set(key,id); groups.forEach(([other]) => { const p = document.getElementById(key+'-'+other); p.hidden = other !== id; if(other===id&&id==='fotos')carregarFotosDaAvaliacao(p); const b = nav.querySelector('[data-section="'+other+'"]'); b.setAttribute('aria-selected',String(other===id)); }); };
    button.setAttribute('aria-selected',String(id===current)); panel.hidden = id !== current;
    nav.appendChild(button); host.appendChild(panel);
  });
  host.prepend(nav);
}
function compactarAvaliacoes() {
  document.querySelectorAll('.aluno-header>div:first-child>span:first-child').forEach(icon=>{icon.textContent='📁';});
  document.querySelectorAll('.aluno-card.active').forEach(card => {
    const clientId = card.dataset.alunoCard;
    const content = card.querySelector('.aluno-content');
    const cards = Array.from(content.children);
    abasCompactas(content,'cliente-'+clientId,[['cadastro','👤 Cadastro',[cards[0]]],['avaliacoes','📊 Avaliações',[cards[1]]]],'avaliacoes');
    card.querySelectorAll('.av-content').forEach(avContent => {
      const key = avContent.parentElement.id;
      const groups = [['composicao','Composição',[]],['medidas','Medidas (cm)',[]],['dobras','Dobras / resultados',[]],['fotos','Fotos',[]],['observacoes','Observações',[]]];
      let index = 0;
      Array.from(avContent.children).forEach(node => {
        if(node.classList.contains('sec-label')) {
          const text = node.textContent.trim();
          if(text.startsWith('Medidas')) index=1;
          else if(text.startsWith('Protocolo')) index=2;
          else if(text==='Fotos') index=3;
          else if(text==='Observações') index=4;
        }
        groups[index][2].push(node);
      });
      abasCompactas(avContent,key,groups,'composicao');
    });
  });
}
function abrirSecaoAvaliacaoPelasObs(section) {
  if(!['composicao','medidas','dobras','fotos'].includes(section)) return;
  const person=alunos.find(a=>a.id===alunoAtivoId);
  if(!person) return;
  if(!person.avaliacoes.length) adicionarAvaliacao(person.id);
  const latest=person.avaliacoes.slice(-1)[0];
  const item=document.getElementById('av-item-'+latest.id);
  if(!item) return;
  item.closest('.aluno-content').querySelector(':scope > .assessment-tabs [data-section="avaliacoes"]').click();
  item.closest('.avs-list').querySelectorAll('.av-item').forEach(other=>other.classList.toggle('expanded',other===item));
  item.querySelector('.av-content > .assessment-tabs [data-section="'+section+'"]').click();
}
function adicionarAvaliacaoAoTreino(recordId) {
  const initialRecord=AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key).find(a=>a.id===recordId);
  if(!initialRecord) return;
  const dialog=document.createElement('dialog'); dialog.className='training-student-picker';
  dialog.innerHTML='<h3>Adicionar avaliação ao treino</h3><p class="assessment-training-person"></p><label>Buscar aluno do treino<input class="assessment-training-search" type="search" placeholder="Nome do aluno ou treino"></label><label>Aluno do treino<select class="assessment-training-select"></select></label><label class="assessment-training-name-wrap">Nome no treino<input class="assessment-training-name" type="text"></label><label class="assessment-training-confirm-wrap" hidden><input class="assessment-training-confirm" type="checkbox"> Confirmo que é a mesma pessoa</label><p>O cadastro será preenchido com os dados desta avaliação. Os exercícios de um treino existente serão mantidos.</p><p class="picker-status" role="status"></p><div class="picker-actions"><button class="assessment-training-add" type="button">Adicionar ao treino</button><button class="picker-cancel" type="button">Cancelar</button></div>';
  document.body.appendChild(dialog);
  dialog.querySelector('.assessment-training-person').textContent=initialRecord.nome;
  const search=dialog.querySelector('.assessment-training-search'), select=dialog.querySelector('.assessment-training-select'), name=dialog.querySelector('.assessment-training-name'), check=dialog.querySelector('.assessment-training-confirm');
  name.value=initialRecord.nome;
  let students=AvaliacaoTreinoSync.read('treinoAlunos');
  function selection() {
    const student=students.find(s=>s.student_id===select.value), linked=student && AvaliacaoTreinoSync.isLinked(initialRecord,student.student_id);
    dialog.querySelector('.assessment-training-name-wrap').hidden=select.value!=='new';
    const other=student && AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key).find(a=>a.id!==initialRecord.id && AvaliacaoTreinoSync.isLinked(a,student.student_id));
    dialog.querySelector('.assessment-training-confirm-wrap').hidden=select.value==='new' || (!!linked && !other);
    check.parentElement.lastChild.textContent=other?' Confirmo que os dois cadastros são da mesma pessoa e desejo reunir o histórico':' Confirmo que é a mesma pessoa';
    check.checked=false; dialog.querySelector('.picker-status').textContent='';
    dialog.querySelector('.assessment-training-add').textContent=linked?'Atualizar cadastro no treino':'Adicionar ao treino';
  }
  function filter() {
    const previous=select.value;
    students=AvaliacaoTreinoSync.read('treinoAlunos');
    select.replaceChildren(new Option('Criar cadastro no treino','new'));
    students.filter(s=>s.student_id && nomeAlunoNaAvaliacao(s.nome).includes(nomeAlunoNaAvaliacao(search.value))).sort((a,b)=>a.nome.localeCompare(b.nome,'pt-BR',{sensitivity:'base',numeric:true})).forEach(s=>select.add(new Option(s.nome+(AvaliacaoTreinoSync.isLinked(initialRecord,s.student_id)?' · Já vinculado':''),s.student_id)));
    if(Array.from(select.options).some(o=>o.value===previous)) select.value=previous;
    selection();
  }
  search.oninput=filter; select.onchange=selection;
  dialog.querySelector('.picker-cancel').onclick=()=>dialog.close(); dialog.onclose=()=>dialog.remove();
  dialog.querySelector('.assessment-training-add').onclick=()=>{
    try {
      const records=AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key), record=records.find(a=>a.id===recordId);
      if(!record) throw Error('Este cadastro não está mais disponível.');
      students=AvaliacaoTreinoSync.read('treinoAlunos');
      let student=students.find(s=>s.student_id===select.value);
      if(select.value!=='new') {
        if(!student) throw Error('Selecione novamente o aluno do treino.');
        if(!AvaliacaoTreinoSync.isLinked(record,student.student_id) && !check.checked) throw Error('Confirme que é a mesma pessoa antes de adicionar.');
        const other=records.find(a=>a.id!==record.id && AvaliacaoTreinoSync.isLinked(a,student.student_id));
        if(other && !check.checked) throw Error('Confirme que os dois cadastros são da mesma pessoa para reunir as avaliações.');
        if(other) AvaliacaoTreinoSync.join(records,record,other);
      } else {
        if(!name.value.trim()) throw Error('Digite o nome do aluno no treino.');
        if(students.some(s=>nomeAlunoNaAvaliacao(s.nome)===nomeAlunoNaAvaliacao(name.value))) throw Error('Já existe esse nome no treino. Selecione o cadastro existente ou escolha outro nome para o novo treino.');
      }
      try { localStorage.setItem('avaliacao_treino_antes_uniao',JSON.stringify({data:new Date().toISOString(),avaliacoes:records,treinos:students})); }
      catch (backupError) { /* A cópia adicional não deve impedir o vínculo. Os cadastros originais continuam guardados. */ }
      if(!student) {
        const uuid=()=>crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+Math.random().toString(36).slice(2);
        student={student_id:'aluno-'+uuid(),nome:name.value.trim(),treino:{},titulos:{},secaoFAtiva:false,historicoTreinos:[],treino_id:'treino-'+uuid(),treinoNome:'Treino de '+name.value.trim(),criadoEm:new Date().toISOString()};
        ['A','B','C','D','E','F'].forEach(key=>{student.treino[key]=[];student.titulos[key]=key+'. TREINO '+key;});
        students.push(student);
      }
      const selected=record.avaliacaoPreferidaId || record.avaliacoes.slice(-1)[0]?.id;
      if(selected)record.avaliacaoPreferidaId=selected;
      AvaliacaoTreinoSync.link(record,student.student_id); AvaliacaoTreinoSync.toFicha(student,record);
      localStorage.setItem('treinoAlunos',JSON.stringify(students));
      localStorage.setItem(AvaliacaoTreinoSync.key,JSON.stringify(records));
      alunos=records; AvaliacaoTreinoSync.syncTraining(records); filtrarAlunos(); dialog.close();
      notifMsg('Cadastro disponível no treino. Informações sincronizadas.');
    } catch(e) { dialog.querySelector('.picker-status').textContent=e.name==='QuotaExceededError'?'O espaço deste navegador está cheio. Exporte Salvar tudo (JSON) para guardar seus dados antes de liberar espaço. Nenhum cadastro foi apagado.':e.message; }
  };
  filter();
  const linked=students.filter(s=>AvaliacaoTreinoSync.isLinked(initialRecord,s.student_id));
  const matches=students.filter(s=>nomeAlunoNaAvaliacao(s.nome)===nomeAlunoNaAvaliacao(initialRecord.nome));
  if(linked.length) select.value=linked[0].student_id; else if(matches.length===1) select.value=matches[0].student_id;
  selection(); dialog.showModal();
}
function nomeAlunoNaAvaliacao(value) {
  return String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().replace(/\s+/g,' ').toLocaleLowerCase('pt-BR');
}
function cadastroDoAlunoNoTreino(student, records) {
  const ficha=(student.infoGuias||[]).find(g=>g.id===student.avaliacaoFichaId) || student.infoRelevante || student.infoGuias?.[0] || {};
  const linked=records.find(a=>AvaliacaoTreinoSync.isLinked(a,student.student_id));
  const names=[ficha.nomeCompleto,student.nome].filter(Boolean).map(nomeAlunoNaAvaliacao);
  const base=nomeAlunoNaAvaliacao(student.nome).replace(/\s*(?:[-–]\s*)?(?:(?:treino|rotina)\s*)?#?\s*\d+\s*$/i,'').replace(/\s+(?:nova|novo)$/i,'').trim();
  const matches=records.filter(a=>names.includes(nomeAlunoNaAvaliacao(a.nome)) || (base && nomeAlunoNaAvaliacao(a.nome)===base));
  return {ficha,linked,matches,status:linked?'cadastrado':matches.length?'confirmar':'novo'};
}
function adicionarAlunoDoTreino() {
  let students = AvaliacaoTreinoSync.read('treinoAlunos');
  let records = AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key);
  if(!students.length) { notifMsg('Cadastre um aluno no treino para adicioná-lo à avaliação.'); return; }
  const dialog = document.createElement('dialog'); dialog.className='training-student-picker';
  dialog.innerHTML='<h3>Adicionar aluno do treino</h3><label>Buscar no treino<input class="training-student-search" type="search" placeholder="Nome do aluno ou treino"></label><div class="training-picker-controls"><label>Ordenar<select class="training-student-order"><option value="az">Nome A–Z</option><option value="za">Nome Z–A</option></select></label><label>Cadastros<select class="training-student-filter"><option value="todos">Todos</option><option value="cadastrado">Já cadastrados</option><option value="confirmar">Confirmar pessoa</option><option value="novo">Novos / sem vínculo</option></select></label></div><label>Aluno do treino<select class="training-student-select"></select></label><p class="training-registration-status" role="status"></p><p class="training-student-preview"></p><label>Cadastro na avaliação<select class="assessment-person-select"></select></label><label class="identity-confirmation" hidden><input class="identity-confirm" type="checkbox"> Confirmo que é a mesma pessoa</label><p class="picker-status" role="status"></p><div class="picker-actions"><button class="picker-add" type="button">Adicionar / abrir</button><button class="picker-cancel" type="button">Cancelar</button></div>';
  document.body.appendChild(dialog);
  const search=dialog.querySelector('.training-student-search'), select=dialog.querySelector('.training-student-select'), person=dialog.querySelector('.assessment-person-select'), check=dialog.querySelector('.identity-confirm'), order=dialog.querySelector('.training-student-order'), statusFilter=dialog.querySelector('.training-student-filter');
  const labels={cadastrado:'Já cadastrado',confirmar:'Confirmar pessoa',novo:'Novo / sem vínculo'};
  function showStudent() {
    check.checked=false;
    const student=students.find(s=>s.student_id===select.value);
    const info=student ? cadastroDoAlunoNoTreino(student,records) : {ficha:{},matches:[]};
    const {ficha,linked,matches}=info;
    dialog.querySelector('.training-student-preview').textContent=student ? [student.nome, ficha.idade && 'Idade: '+ficha.idade, ficha.peso && 'Peso: '+ficha.peso, ficha.altura && 'Altura: '+ficha.altura, (ficha.whats||student.whatsapp) && 'WhatsApp: '+(ficha.whats||student.whatsapp)].filter(Boolean).join(' · ') : 'Nenhum aluno encontrado';
    const badge=dialog.querySelector('.training-registration-status');
    badge.dataset.status=info.status||'';
    badge.textContent=linked ? 'Já cadastrado: '+linked.nome+'. Ao abrir, será usado o mesmo cadastro.' : matches.length ? 'Existe cadastro com esse nome. Confirme se é a mesma pessoa.' : student ? 'Sem vínculo na avaliação. Crie um cadastro ou selecione uma pessoa existente.' : '';
    person.replaceChildren(new Option('Criar cadastro para este aluno','new'));
    records.slice().sort((a,b)=>a.nome.localeCompare(b.nome,'pt-BR',{sensitivity:'base',numeric:true})*(order.value==='za'?-1:1)).forEach(a=>person.add(new Option(a.nome,String(a.id))));
    if(linked) person.value=String(linked.id);
    else if(matches.length===1) person.value=String(matches[0].id);
    person.disabled=!!linked || !student;
    dialog.querySelector('.identity-confirmation').hidden=!!linked || person.value==='new';
    dialog.querySelector('.picker-add').disabled=!student;
    dialog.querySelector('.picker-add').textContent=linked?'Abrir cadastro':person.value==='new'?'Adicionar aluno':'Confirmar e adicionar';
    dialog.querySelector('.picker-status').textContent='';
  }
  function filter() {
    students=AvaliacaoTreinoSync.read('treinoAlunos'); records=AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key);
    const previous=select.value;
    const query=nomeAlunoNaAvaliacao(search.value);
    const filtered=students.filter(s=>s.student_id && [s.nome,cadastroDoAlunoNoTreino(s,records).ficha.nomeCompleto].some(name=>nomeAlunoNaAvaliacao(name).includes(query)) && (statusFilter.value==='todos' || cadastroDoAlunoNoTreino(s,records).status===statusFilter.value));
    filtered.sort((a,b)=>String(a.nome||'').localeCompare(String(b.nome||''),'pt-BR',{sensitivity:'base',numeric:true})*(order.value==='za'?-1:1));
    select.replaceChildren();
    filtered.forEach(s=>select.add(new Option(s.nome+' · '+labels[cadastroDoAlunoNoTreino(s,records).status],s.student_id)));
    if(Array.from(select.options).some(o=>o.value===previous)) select.value=previous;
    showStudent();
  }
  search.oninput=filter; order.onchange=filter; statusFilter.onchange=filter; select.onchange=showStudent;
  person.onchange=()=>{check.checked=false;dialog.querySelector('.identity-confirmation').hidden=person.value==='new';dialog.querySelector('.picker-add').textContent=person.value==='new'?'Adicionar aluno':'Confirmar e adicionar';};
  dialog.querySelector('.picker-cancel').onclick=()=>dialog.close(); dialog.onclose=()=>dialog.remove();
  dialog.querySelector('.picker-add').onclick=()=>{
    try {
      // Releia o navegador para não sobrescrever edições feitas com a janela aberta.
      const student=AvaliacaoTreinoSync.read('treinoAlunos').find(s=>s.student_id===select.value);
      if(!student) throw Error('Selecione um aluno disponível no treino.');
      alunos=AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key);
      let record=alunos.find(a=>AvaliacaoTreinoSync.isLinked(a,student.student_id));
      if(!record && person.value!=='new') {
        if(!check.checked) throw Error('Confirme que é a mesma pessoa antes de sincronizar.');
        record=alunos.find(a=>String(a.id)===person.value);
        if(!record) throw Error('O cadastro não está mais disponível.');
      }
      backupEstado();
      const ficha=(student.infoGuias||[]).find(g=>g.id===student.avaliacaoFichaId) || student.infoRelevante || student.infoGuias?.[0] || {};
      const seed=Object.assign({},ficha,{whats:ficha.whats||student.whatsapp||''});
      if(!record) {
        record={id:Date.now(),nome:student.nome,sexo:'M',avaliacoes:[]};
        while(alunos.some(a=>a.id===record.id)) record.id++;
        AvaliacaoTreinoSync.fromFicha(student,record,seed); alunos.push(record);
      } else {
        const candidate=JSON.parse(JSON.stringify(record)); AvaliacaoTreinoSync.fromFicha(student,candidate,seed);
        ['nome','nasc','idade','altura','whatsapp','email','pesoIni'].forEach(key=>{if(!record[key] && candidate[key]) record[key]=candidate[key];});
        const last=record.avaliacoes?.slice(-1)[0], incoming=candidate.avaliacoes?.slice(-1)[0];
        if(last && !last.peso && incoming?.peso) last.peso=incoming.peso;
      }
      AvaliacaoTreinoSync.link(record,student.student_id);
      record.avaliacoes.forEach(av=>calcularIMCeDobras(record,av.id));
      alunoAtivoId=record.id;
      document.getElementById('buscaAluno').value='';
      salvarDados(); filtrarAlunos(); dialog.close();
      const latest=record.avaliacoes.slice(-1)[0]; if(latest) document.getElementById('av-item-'+latest.id)?.classList.add('expanded');
      notifMsg('Aluno disponível na avaliação. Informações da ficha sincronizadas.');
    } catch(e) {dialog.querySelector('.picker-status').textContent=e.message;}
  };
  filter(); dialog.showModal();
}
document.addEventListener('DOMContentLoaded',()=>{
  const button=document.createElement('button'); button.id='addTrainingStudentBtn'; button.type='button'; button.textContent='＋ Do treino'; button.title='Adicionar aluno do treino'; button.setAttribute('aria-label','Adicionar aluno do treino'); button.onclick=adicionarAlunoDoTreino;
  document.getElementById('btnNovoAluno').after(button);
  const actions=document.getElementById('btnNovoAluno').parentElement;
  actions.classList.add('compact-actions');
  const menu=document.createElement('details'); menu.className='assessment-more-options';
  menu.innerHTML='<summary>Mais opções</summary><div class="assessment-more-menu"></div>';
  const secondary=menu.querySelector('div');
  actions.querySelector('.btn-notif').remove();
  const notifications=document.createElement('div'); notifications.className='assessment-notification-setting';
  notifications.innerHTML='<label class="assessment-switch"><span>Notificações</span><input type="checkbox" role="switch" id="assessmentNotificationsToggle"><span class="assessment-switch-track" aria-hidden="true"></span></label><small id="assessmentNotificationsStatus"></small>';
  secondary.appendChild(notifications);
  notifications.querySelector('#assessmentNotificationsToggle').onchange=function(){alternarNotificacoesAvaliacao(this.checked).catch(()=>{document.getElementById('assessmentNotificationsStatus').textContent='Não foi possível salvar a preferência';});};
  ['.btn-desfazer','.btn-export-all','.btn-import-json'].forEach(selector=>secondary.appendChild(actions.querySelector(selector)));
  actions.appendChild(menu);
  atualizarControleNotificacoes();
  document.getElementById('bannerRenovacao').classList.add('minimized');
  // Ajuste o ícone após recolher o aviso inicial.
  const bannerToggle=document.querySelector('.minimizar-banner'); if(bannerToggle) bannerToggle.textContent='▼';
  window.addEventListener('storage',event=>{if(event.key===chaveNotificacoesAvaliacao){atualizarControleNotificacoes();renderizarBannerRenovacoes(getAlunosComPendencias());}});
});
function abrirOpcoesPDFAvaliacao(recordId) {
  const dialog=document.createElement('dialog');dialog.className='assessment-pdf-picker';
  dialog.innerHTML='<h3>PDF da avaliação</h3><label>Conteúdo<select class="assessment-pdf-mode" aria-label="Conteúdo do PDF"><option value="auto">Automático · partes preenchidas</option><option value="medidas-dobras">Medidas + dobras cutâneas</option><option value="medidas-composicao">Medidas + composição corporal</option><option value="completo">Avaliação completa</option></select></label><p class="assessment-pdf-status" role="status"></p><div class="picker-actions"><button type="button" class="assessment-pdf-generate">Gerar PDF</button><button type="button" class="assessment-pdf-cancel">Cancelar</button></div>';
  document.body.appendChild(dialog);dialog.onclose=()=>dialog.remove();dialog.querySelector('.assessment-pdf-cancel').onclick=()=>dialog.close();
  const button=dialog.querySelector('.assessment-pdf-generate');
  button.onclick=async()=>{button.disabled=true;try{alunos=AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key);await gerarPDFAluno(recordId,{mode:dialog.querySelector('.assessment-pdf-mode').value});dialog.close();}catch(e){dialog.querySelector('.assessment-pdf-status').textContent=e.message;}finally{button.disabled=false;}};
  dialog.showModal();
}
