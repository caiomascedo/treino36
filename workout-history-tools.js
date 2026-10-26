/* Duplicate detection is deliberately exact after presentation normalization. */
window.WorkoutHistoryTools=(()=>{
  function plain(value){const holder=document.createElement('div');holder.innerHTML=String(value||'');return holder.textContent.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR').replace(/(\d)\s*[×x]\s*(?=\d)/g,'$1x').replace(/[—–]/g,'-').replace(/\s*([:;,()\-+])\s*/g,'$1').replace(/\s+/g,' ').trim();}
  function signature(workout){return JSON.stringify([!!workout.secaoFAtiva,...'ABCDEF'.split('').map(section=>(workout.treino?.[section]||[]).map(plain).filter(Boolean))]);}
  function duplicates(workout,versions,selected){const key=signature(workout);return versions.filter(version=>version.key!==selected&&signature(version.workout)===key);}
  return {plain,signature,duplicates};
})();
