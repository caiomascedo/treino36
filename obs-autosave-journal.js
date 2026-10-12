/* Durable, small OBS edits. Text and photos are stored separately. */
globalThis.TreinoObsJournal = {
  key:'treino36_obs_drafts', photoKey:'treino36_obs_photo_drafts',
  merge(records,drafts,photos=[]) {
    for(const draft of drafts){
      let student=records.find(s=>String(s.student_id)===String(draft.studentId));if(!student&&draft.createStudent){student={...draft.createStudent};records.push(student);}if(!student)continue;
      for(const [field,order,patches] of [['obsGuias',draft.obsOrder,draft.obs],['infoGuias',draft.infoOrder,draft.info]]){
        let guides=student[field]||[];
        if(order){if(field==='obsGuias')guides=order.map(id=>guides.find(g=>String(g.id)===String(id))||{id});else{guides=guides.slice();for(const id of order)if(!guides.some(g=>String(g.id)===String(id)))guides.push({id});}student[field]=guides;}
        for(const patch of patches||[]){const guide=guides.find(g=>String(g.id)===String(patch.id));if(guide)for(const [key,value] of Object.entries(patch.fields)){if(field==='infoGuias'&&['titulo','avaliacaoOrigemData','avaliacaoOrigemId','avaliacaoCadastroId'].includes(key)&&guide[key]!==undefined)continue;guide[key]=value;}}
      }
      Object.assign(student,draft.studentFields||{});
      if(draft.studentFields?.infoRelevante){const current=(student.infoGuias||[]).find(g=>String(g.id)===String(draft.studentFields.infoRelevante.id));if(current)student.infoRelevante={...current};}
      if(draft.obsOrder||draft.obs)student.observacoes=(student.obsGuias||[]).map(g=>(g.texto||'').trim()).filter(Boolean).join('\n---\n');
    }
    for(const draft of photos){
      const student=records.find(s=>String(s.student_id)===String(draft.studentId));if(!student)continue;
      for(const patch of draft.obs||[]){const guide=(student.obsGuias||[]).find(g=>String(g.id)===String(patch.id));if(!guide)continue;Object.assign(guide,patch.fields);if(Object.hasOwn(patch.fields,'exameFotos'))delete guide.exameFoto;}
    }
    return records;
  }
};
