/* Duplicate detection is deliberately exact after presentation normalization. */
window.WorkoutHistoryTools=(()=>{
  function plain(value){const holder=document.createElement('div');holder.innerHTML=String(value||'');return holder.textContent.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR').replace(/(\d)\s*[×x]\s*(?=\d)/g,'$1x').replace(/[—–]/g,'-').replace(/\s*([:;,()\-+])\s*/g,'$1').replace(/\s+/g,' ').trim();}
  function signature(workout){return JSON.stringify([!!workout.secaoFAtiva,...'ABCDEF'.split('').map(section=>(workout.treino?.[section]||[]).map(plain).filter(Boolean))]);}
  function duplicates(workout,versions,selected){const key=signature(workout);return versions.filter(version=>version.key!==selected&&signature(version.workout)===key);}
  function dateTime(value){
    if(!value)return '';
    if(/^\d{4}-\d{2}-\d{2}$/.test(String(value))){const parts=String(value).split('-');return parts[2]+'/'+parts[1]+'/'+parts[0]+' (hora não registrada)';}
    const date=new Date(value);if(!Number.isFinite(date.getTime()))return '';
    return date.toLocaleString('pt-BR',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
  }
  function stamp(workout){
    for(const [field,label] of [['edited_at','Alterado em'],['updated_at','Atualizado em'],['atualizadoEm','Atualizado em'],['archived_at','Arquivado em'],['activated_at','Ativado em'],['created_at','Criado em']]){
      const date=dateTime(workout[field]);if(date)return label+' '+date;
    }
    return 'Data e horário não registrados';
  }
  function coverLabel(student){return '⭐ CAPA ATUAL · '+(student.treinoNome||'Treino de '+student.nome)+' · '+stamp(student);}
  function versionLabel(workout,index){return '◷ Anterior '+(index+1)+' (arquivado) · '+(workout.name||workout.treinoNome||workout.original_student_name||workout.student_name||'Treino')+' · '+stamp(workout);}
  return {plain,signature,duplicates,dateTime,stamp,coverLabel,versionLabel};
})();
