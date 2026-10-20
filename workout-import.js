/* Strip video badges from pasted/exported workouts without rewriting prescriptions. */
window.WorkoutImport=(()=>{
  const normalized=s=>String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z]/g,'');
  function distance(a,b){const row=Array.from({length:b.length+1},(_,i)=>i);for(let i=1;i<=a.length;i++){let diagonal=row[0];row[0]=i;for(let j=1;j<=b.length;j++){const previous=row[j];row[j]=Math.min(row[j]+1,row[j-1]+1,diagonal+(a[i-1]===b[j-1]?0:1));diagonal=previous;}}return row[b.length];}
  function badge(s){const letters=normalized(s);return letters.length>=5&&letters.length<=10&&distance(letters,'youtube')<=2;}
  function clean(text){
    const lines=String(text??'').replace(/\r\n?/g,'\n').replace(/\s*⠿\s*/g,'\n').split('\n'),out=[];
    for(let line of lines){
      line=line.replace(/https?:\/\/(?:www\.)?(?:youtube\.com|youtu\.be)\/\S*/gi,'').trim();
      if(!line||badge(line))continue;
      const last=line.match(/(?:[\s•·▶►|]+)([A-Za-z][A-Za-z ]{4,11})[\s.]*$/);if(last&&badge(last[1]))line=line.slice(0,last.index).trim();
      if(!line||/^(?:gerado\s+em\b|personal\b|treino\s*[—–-]\s*|unknown$)/i.test(line))continue;
      if(out.length&&/^(?:conforme\b|peso\s*\d|carga\s*(?:citada|de)|confirmar\b|cada\s*(?:lado|perna)|retirando\b)/i.test(line)&&/\d\s*[x×]\s*\d/.test(out.at(-1)))out[out.length-1]+=' '+line;
      else out.push(line);
    }
    const title=out.findIndex(line=>/^(?:treino\s*)?[A-F]\s*[:.\-–—]\s*\S/i.test(line));return (title>0?out.slice(title):out).join('\n');
  }
  return {clean,badge};
})();
