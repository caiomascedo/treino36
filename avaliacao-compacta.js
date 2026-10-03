/* Navegação compacta do formulário no Treino36. Os dados e PDFs usam o modelo original. */
const secoesAvaliacao = new Map();
function abasCompactas(host, key, groups, initial) {
  const nav = document.createElement('div'); nav.className = 'assessment-tabs'; nav.setAttribute('role','tablist');
  const current = secoesAvaliacao.get(key) || initial;
  groups.forEach(([id, label, nodes]) => {
    const panel = document.createElement('section'); panel.id = key + '-' + id; panel.className = 'assessment-tab-panel'; panel.setAttribute('role','tabpanel');
    nodes.forEach(node => panel.appendChild(node));
    const button = document.createElement('button'); button.type = 'button'; button.textContent = label; button.dataset.section = id; button.setAttribute('role','tab'); button.setAttribute('aria-controls',panel.id);
    button.id = panel.id + '-tab'; panel.setAttribute('aria-labelledby',button.id);
    button.onclick = () => { secoesAvaliacao.set(key,id); groups.forEach(([other]) => { const p = document.getElementById(key+'-'+other); p.hidden = other !== id; const b = nav.querySelector('[data-section="'+other+'"]'); b.setAttribute('aria-selected',String(other===id)); }); };
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
function adicionarAlunoDoTreino() {
  const students = AvaliacaoTreinoSync.read('treinoAlunos');
  if(!students.length) { notifMsg('Cadastre um aluno no treino para adicioná-lo à avaliação.'); return; }
  const dialog = document.createElement('dialog'); dialog.className='training-student-picker';
  dialog.innerHTML='<h3>Adicionar aluno do treino</h3><label>Buscar no treino<input class="training-student-search" type="search" placeholder="Nome do aluno ou treino"></label><label>Aluno do treino<select class="training-student-select"></select></label><p class="training-student-preview"></p><label>Cadastro na avaliação<select class="assessment-person-select"></select></label><label class="identity-confirmation" hidden><input class="identity-confirm" type="checkbox"> Confirmo que é a mesma pessoa</label><p class="picker-status" role="status"></p><div class="picker-actions"><button class="picker-add" type="button">Adicionar / abrir</button><button class="picker-cancel" type="button">Cancelar</button></div>';
  document.body.appendChild(dialog);
  const search=dialog.querySelector('.training-student-search'), select=dialog.querySelector('.training-student-select'), person=dialog.querySelector('.assessment-person-select'), check=dialog.querySelector('.identity-confirm');
  function showStudent() {
    check.checked=false;
    const student=students.find(s=>s.student_id===select.value);
    const linked=student && alunos.find(a=>AvaliacaoTreinoSync.isLinked(a,student.student_id));
    const ficha=student && (student.infoGuias || []).find(g=>g.id===student.avaliacaoFichaId) || student?.infoRelevante || student?.infoGuias?.[0] || {};
    dialog.querySelector('.training-student-preview').textContent=student ? [student.nome, ficha.idade && 'Idade: '+ficha.idade, ficha.peso && 'Peso: '+ficha.peso, ficha.altura && 'Altura: '+ficha.altura, (ficha.whats||student.whatsapp) && 'WhatsApp: '+(ficha.whats||student.whatsapp)].filter(Boolean).join(' · ') : 'Nenhum aluno encontrado';
    person.replaceChildren(new Option('Criar cadastro para este aluno','new'));
    alunos.forEach(a=>person.add(new Option(a.nome,String(a.id))));
    if(linked) person.value=String(linked.id);
    person.disabled=!!linked;
    dialog.querySelector('.identity-confirmation').hidden=!!linked || person.value==='new';
    dialog.querySelector('.picker-add').disabled=!student;
    dialog.querySelector('.picker-status').textContent='';
  }
  function filter() { const previous=select.value; select.replaceChildren(); students.filter(s=>s.student_id && String(s.nome||'').toLocaleLowerCase().includes(search.value.toLocaleLowerCase())).forEach(s=>select.add(new Option(s.nome,s.student_id))); if(Array.from(select.options).some(o=>o.value===previous)) select.value=previous; showStudent(); }
  search.oninput=filter; select.onchange=showStudent;
  person.onchange=()=>{check.checked=false;dialog.querySelector('.identity-confirmation').hidden=person.value==='new';};
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
  const button=document.createElement('button'); button.id='addTrainingStudentBtn'; button.type='button'; button.textContent='＋ Adicionar aluno do treino'; button.onclick=adicionarAlunoDoTreino;
  document.getElementById('btnNovoAluno').after(button);
  const actions=document.getElementById('btnNovoAluno').parentElement;
  actions.classList.add('compact-actions');
  const menu=document.createElement('details'); menu.className='assessment-more-options';
  menu.innerHTML='<summary>Mais opções</summary><div class="assessment-more-menu"></div>';
  const secondary=menu.querySelector('div');
  ['.btn-notif','.btn-desfazer','.btn-export-all','.btn-import-json'].forEach(selector=>secondary.appendChild(actions.querySelector(selector)));
  actions.appendChild(menu);
  document.getElementById('bannerRenovacao').classList.add('minimized');
  // Ajuste o ícone após recolher o aviso inicial.
  const bannerToggle=document.querySelector('.minimizar-banner'); if(bannerToggle) bannerToggle.textContent='▼';
});
