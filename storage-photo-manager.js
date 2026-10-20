/* Catalog photos without counting editable originals as additional photos. */
window.StoragePhotoManager=(()=>{
  const assessmentKey='avaliacao_fisica_alunos',trainingKey='treinoAlunos';
  function list(){
    const result=[];
    function add(key,personId,avId,field,id,label,src,name,date){if(typeof src==='string'&&src.startsWith('data:image/'))result.push({key,personId,avId,field,id,label,src,name,date,token:JSON.stringify([key,personId,avId,field,id])});}
    for(const person of JSON.parse(localStorage.getItem(assessmentKey)||'[]'))for(const av of person.avaliacoes||[]){
      for(const [field,label] of [['fotoF','Frontal'],['fotoL','Lateral'],['fotoD','Dorsal']])add(assessmentKey,person.id,av.id,field,null,label,av[field],person.nome,av.data);
      for(const photo of av.fotosExtras||[])add(assessmentKey,person.id,av.id,'fotosExtras',photo.id,photo.label||'Outra foto',photo.src,person.nome,photo.date||av.data);
    }
    for(const person of JSON.parse(localStorage.getItem(trainingKey)||'[]'))for(const guide of person.obsGuias||[]){
      for(const photo of guide.exameFotos||[])add(trainingKey,person.student_id,guide.id,'exameFotos',photo.id,photo.name||'Foto da OBS',photo.src,person.nome,guide.titulo);
      if(!Array.isArray(guide.exameFotos))add(trainingKey,person.student_id,guide.id,'exameFoto',null,'Foto da OBS',guide.exameFoto,person.nome,guide.titulo);
    }
    return result;
  }
  function remove(items){
    const removed=[],errors=[];
    for(const key of [...new Set(items.map(item=>item.key))]){
      const selected=items.filter(item=>item.key===key);
      try{TreinoStorage.replacePhotoRecords(key,records=>{
        for(const item of selected){
          const person=records.find(p=>String(key===assessmentKey?p.id:p.student_id)===String(item.personId));
          const entry=(key===assessmentKey?person?.avaliacoes:person?.obsGuias)?.find(av=>String(av.id)===String(item.avId));
          if(!entry)throw Error('O cadastro mudou. Atualize a lista.');
          if(['fotosExtras','exameFotos'].includes(item.field)){
            const photo=entry[item.field]?.find(p=>String(p.id)===String(item.id));if(photo?.src!==item.src)throw Error('Uma foto mudou. Atualize a lista antes de apagar.');
            entry[item.field]=entry[item.field].filter(p=>String(p.id)!==String(item.id));
          }else{
            if(entry[item.field]!==item.src)throw Error('Uma foto mudou. Atualize a lista antes de apagar.');
            delete entry[item.field];delete entry[item.field+'Original'];
            if(entry.posturaEdicoes){entry.posturaEdicoes={...entry.posturaEdicoes};delete entry.posturaEdicoes[item.field];}
          }
        }
      });removed.push(...selected);}catch(error){errors.push(error.message);}
    }
    return {removed,errors};
  }
  return {list,remove};
})();
