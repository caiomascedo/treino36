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
  function mergeVersions(existing,incoming){
    const result=[],slots=new Map();
    for(const version of [...(existing||[]),...(incoming||[])]){
      const key=JSON.stringify([version.workout_id||null,version.treino,version.titulos||{},!!version.secaoFAtiva]);
      if(slots.has(key)){const index=slots.get(key);result[index]={...result[index],...version};}
      else{slots.set(key,result.length);result.push(version);}
    }
    if(result.every(version=>Number.isFinite(Date.parse(version.archived_at))))result.sort((a,b)=>Date.parse(a.archived_at)-Date.parse(b.archived_at));
    return result;
  }
  function position(index,total){return Number.isInteger(total)?total-index:index+1;}
  function versionLabel(workout,index,total){return '◷ Anterior '+position(index,total)+' (arquivado) · '+(workout.name||workout.treinoNome||workout.original_student_name||workout.student_name||'Treino')+' · '+stamp(workout);}
  return {plain,signature,duplicates,dateTime,stamp,coverLabel,position,versionLabel,mergeVersions};
})();
