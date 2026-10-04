/* Small durable assessment edits. Shared by the page and storage worker. */
globalThis.TreinoAssessmentJournal = {
  key: 'treino36_assessment_drafts',
  merge(records, drafts) {
    for (const draft of drafts) {
      const person = records.find(record => String(record.id) === String(draft.recordId));
      if (!person) continue;
      if (draft.operation === 'delete') {
        person.avaliacoes = (person.avaliacoes || []).filter(item => String(item.id) !== String(draft.avId));
        const latest = person.avaliacoes.at(-1);
        if (String(person.avaliacaoPreferidaId) === String(draft.avId)) person.avaliacaoPreferidaId = latest?.id || null;
        if (String(person.pesoAtualAvaliacaoId) === String(draft.avId)) { person.pesoAtualAvaliacaoId = latest?.id || null; person.pesoAtual = latest?.peso || ''; }
        person.avaliacaoSemRegistros = !person.avaliacoes.length;
        continue;
      }
      if (draft.operation === 'add' && !person.avaliacoes.some(item => String(item.id) === String(draft.avId))) person.avaliacoes.push({id:draft.avId});
      const av = person?.avaliacoes?.find(item => String(item.id) === String(draft.avId));
      if (!av) continue; // A deleted assessment must never be recreated by a draft.
      Object.assign(av, draft.fields);
      Object.assign(person, draft.personFields || {});
      if (Object.hasOwn(draft.fields, 'peso') && person.avaliacoes.at(-1) === av) {
        person.pesoAtual = av.peso;
        person.pesoAtualAvaliacaoId = av.id;
      }
    }
    return records;
  }
};
