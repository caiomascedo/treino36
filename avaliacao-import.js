/* Importação independente: este módulo só grava o cadastro de avaliações. */
(function () {
  'use strict';
  const KEY = 'avaliacao_fisica_alunos';
  const fields = ['id','nome','nasc','idade','altura','pesoIni','sexo','whatsapp','email','valorPago','renovacaoDias','pagamentoTipo','pagamentoData1','pagamentoData2','pagamentoMinimizado','renovacaoMinimizado'];
  const clone = value => JSON.parse(JSON.stringify(value));
  function read() {
    const data = JSON.parse(localStorage.getItem(KEY) || '[]');
    if (!Array.isArray(data)) throw Error('O cadastro atual de avaliações está inválido.');
    return data;
  }
  function extract(raw) {
    if (Array.isArray(raw)) return raw;
    if (raw && typeof raw === 'object') {
      if (typeof raw.nome === 'string' && Array.isArray(raw.avaliacoes)) return [raw];
      if (Array.isArray(raw.alunos)) return raw.alunos;
      if (Array.isArray(raw.avaliacoes)) return raw.avaliacoes;
    }
    throw Error('Selecione o backup JSON exportado pela Avaliação.');
  }
  function isAssessmentPayload(raw) {
    try { const data = extract(raw); return raw?.tipo === 'avaliacoes' || (data.length > 0 && data.every(a => a && !a.treino && Array.isArray(a.avaliacoes))); }
    catch (e) { return false; }
  }
  function validate(raw) {
    const source = extract(raw), people = new Set(), assessments = new Set();
    return source.map(person => {
      if (!person || typeof person.nome !== 'string' || !person.nome.trim() || !Array.isArray(person.avaliacoes)) throw Error('Cada pessoa deve ter nome e uma lista de avaliações. Nenhum dado foi importado.');
      if (!Number.isSafeInteger(Number(person.id)) || Number(person.id) <= 0) throw Error('O cadastro de ' + person.nome + ' não tem um ID válido.');
      const id = Number(person.id);
      if (people.has(id)) throw Error('Há cadastros com IDs repetidos no arquivo.');
      people.add(id);
      const clean = {};
      fields.forEach(field => {
        if (Object.hasOwn(person, field)) {
          if (!['string','number','boolean'].includes(typeof person[field]) && person[field] !== null) throw Error('Campo inválido no cadastro de ' + person.nome + ': ' + field);
          clean[field] = person[field];
        }
      });
      clean.id = id; clean.nome = person.nome.trim();
      if (clean.sexo && !['M','F'].includes(clean.sexo)) throw Error('Sexo inválido no cadastro de ' + person.nome + '.');
      clean.avaliacoes = person.avaliacoes.map(av => {
        if (!av || typeof av !== 'object' || Array.isArray(av) || !Number.isSafeInteger(Number(av.id)) || Number(av.id) <= 0) throw Error('Uma avaliação de ' + person.nome + ' não tem um ID válido.');
        const copy = clone(av); copy.id = Number(av.id);
        if (assessments.has(copy.id)) throw Error('Há avaliações com IDs repetidos no arquivo.');
        assessments.add(copy.id);
        ['fotoF','fotoL','fotoD'].forEach(field => {
          if (copy[field] && (typeof copy[field] !== 'string' || !/^(data:image\/(?:png|jpeg|jpg|webp);base64,|https?:\/\/)/i.test(copy[field]))) throw Error('Foto inválida na avaliação de ' + person.nome + '.');
        });
        return copy;
      });
      return clean;
    });
  }
  function prepare(raw, current, preferImported) {
    const incoming = validate(raw), records = clone(current);
    const summary = {people:incoming.length, addedPeople:0, addedAssessments:0, existingAssessments:0};
    const owners = new Map();
    records.forEach(p => (p.avaliacoes || []).forEach(av => owners.set(Number(av.id), Number(p.id))));
    incoming.forEach(person => {
      let target = records.find(p => Number(p.id) === person.id);
      if (!target) {
        target = {id:person.id,nome:person.nome,avaliacoes:[]}; records.push(target); summary.addedPeople++;
      }
      target.id = person.id;
      fields.forEach(field => {
        if (!Object.hasOwn(person, field) || field === 'id') return;
        if (preferImported || target[field] === undefined || target[field] === null || target[field] === '') target[field] = person[field];
      });
      if (!Array.isArray(target.avaliacoes)) target.avaliacoes = [];
      person.avaliacoes.forEach(av => {
        if (owners.has(av.id) && owners.get(av.id) !== person.id) throw Error('O ID de uma avaliação está associado a outra pessoa. Confira o arquivo antes de importar.');
        const existing = target.avaliacoes.find(item => Number(item.id) === av.id);
        if (existing) {
          existing.id = av.id;
          summary.existingAssessments++;
          Object.keys(av).forEach(field => {
            if (['__proto__','constructor','prototype'].includes(field)) throw Error('Campo inválido na avaliação.');
            if (preferImported || existing[field] === undefined || existing[field] === null || existing[field] === '') existing[field] = av[field];
          });
        } else { target.avaliacoes.push(clone(av)); summary.addedAssessments++; owners.set(av.id, person.id); }
      });
      function date(value) {
        const parts = String(value || '').match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
        if (!parts) return null;
        const result = new Date(Number(parts[3]),Number(parts[2])-1,Number(parts[1]));
        return result.getDate() === Number(parts[1]) && result.getMonth() === Number(parts[2])-1 ? result.getTime() : null;
      }
      target.avaliacoes.sort((a,b) => {
        const da = date(a.data), db = date(b.data);
        return da !== null && db !== null ? (da - db || Number(a.id) - Number(b.id)) : 0;
      });
    });
    // Os IDs de vínculo vindos de outro arquivo não ligam pessoas a treinos automaticamente.
    // Os vínculos já confirmados neste navegador permanecem nos registros locais.
    return {records, summary, names:incoming.map(p => p.nome)};
  }
  function download() {
    const data = {schema_version:'avaliacoes-1',tipo:'avaliacoes',alunos:read()};
    const url = URL.createObjectURL(new Blob([JSON.stringify(data,null,2)], {type:'application/json'}));
    const a = document.createElement('a'); a.href = url; a.download = 'avaliacoes_' + new Date().toISOString().slice(0,10) + '.json'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function preview(raw, onCommitted) {
    validate(raw);
    const dialog = document.createElement('dialog');
    dialog.className = 'assessment-import-dialog';
    dialog.style.cssText = 'max-width:620px;width:calc(100% - 24px);max-height:85dvh;overflow:auto;padding:20px;border:0;border-radius:14px;color:#243a4d;font:14px system-ui';
    dialog.innerHTML = '<h3>Importar somente avaliações</h3><p>Os treinos e seus nomes serão mantidos. Os cadastros atuais e as avaliações ausentes deste arquivo também serão mantidos.</p><label>Para dados que já existem:<select class="import-preference" style="display:block;width:100%;padding:8px;margin:8px 0"><option value="existing">Manter os dados atuais e completar campos vazios</option><option value="incoming">Usar os dados do arquivo</option></select></label><p class="import-summary"></p><ul class="import-names"></ul><p>Depois da importação, confirme a pessoa correspondente ao treino em “Sincronizar com pessoa cadastrada”. Vínculos já confirmados continuam funcionando.</p><p class="import-status" role="status"></p><button type="button" class="import-confirm">Importar avaliações</button> <button type="button" class="import-cancel">Cancelar</button>';
    let snapshot;
    function update() {
      const plan = prepare(raw, read(), dialog.querySelector('select').value === 'incoming');
      snapshot = localStorage.getItem(KEY);
      const s = plan.summary;
      dialog.querySelector('.import-summary').textContent = s.people + ' pessoa(s) no arquivo · ' + s.addedPeople + ' novo(s) cadastro(s) · ' + s.addedAssessments + ' nova(s) avaliação(ões) · ' + s.existingAssessments + ' avaliação(ões) já salva(s).';
      const list = dialog.querySelector('.import-names'); list.replaceChildren();
      plan.names.forEach(name => { const li = document.createElement('li'); li.textContent = name; list.appendChild(li); });
    }
    dialog.querySelector('select').onchange = () => { try { update(); } catch (e) { dialog.querySelector('.import-status').textContent = e.message; } };
    dialog.querySelector('.import-cancel').onclick = () => dialog.close();
    dialog.querySelector('.import-confirm').onclick = () => {
      try {
        if (localStorage.getItem(KEY) !== snapshot) { update(); dialog.querySelector('.import-status').textContent = 'O cadastro mudou em outra tela. Confira a prévia atualizada e confirme novamente.'; return; }
        const plan = prepare(raw, read(), dialog.querySelector('select').value === 'incoming');
        localStorage.setItem('avaliacao_backup_antes_importacao', JSON.stringify(read()));
        localStorage.setItem(KEY, JSON.stringify(plan.records));
        dialog.close();
        window.dispatchEvent(new CustomEvent('avaliacoes-importadas'));
        if (onCommitted) onCommitted(plan);
      } catch (e) { dialog.querySelector('.import-status').textContent = 'Não foi possível importar: ' + e.message; }
    };
    dialog.addEventListener('close', () => dialog.remove(), {once:true});
    update(); document.body.appendChild(dialog); dialog.showModal();
    return dialog;
  }
  function choose(onCommitted, onError) {
    const input = document.createElement('input'); input.type = 'file'; input.accept = '.json,application/json';
    input.onchange = async () => {
      if (!input.files[0]) return;
      try { preview(JSON.parse(await input.files[0].text()), onCommitted); }
      catch (e) { if (onError) onError(e.message); else alert('Não foi possível importar: ' + e.message); }
    };
    input.click();
  }
  window.AvaliacoesJSON = {read,extract,validate,prepare,isAssessmentPayload,preview,choose,download};
})();
