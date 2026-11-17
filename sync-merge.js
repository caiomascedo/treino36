/* Three-way merge: do not silently select conflicting edits. */
(function(root) {
  function canonical(value) {
    if(value===undefined)return 'undefined';
    if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
    if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
    return JSON.stringify(value);
  }
  function merge(base,local,remote) {
    const conflicts=[],equal=(a,b)=>canonical(a)===canonical(b);
    function walk(b,l,r,path) {
      if(equal(l,r))return l;
      if(equal(l,b))return r;
      if(equal(r,b))return l;
      if(Array.isArray(b)&&Array.isArray(l)&&Array.isArray(r)) {
        const all=[...b,...l,...r];
        const key=['student_id','id','workout_id'].find(k=>all.length&&all.every(x=>x&&typeof x==='object'&&x[k]!=null)&&[b,l,r].every(a=>new Set(a.map(x=>String(x[k]))).size===a.length));
        if(key) {
          const maps=[b,l,r].map(a=>new Map(a.map(x=>[String(x[key]),x])));
          const ids=[...new Set([...r,...l,...b].map(x=>String(x[key])))];
          const result=ids.map(id=>walk(...maps.map(m=>m.get(id)),path+'/'+id)).filter(x=>x!==undefined);
          const oldIds=b.map(x=>String(x[key])),order=a=>a.map(x=>String(x[key])).filter(id=>oldIds.includes(id));
          if(!equal(order(l),oldIds)&&!equal(order(r),oldIds)&&!equal(order(l),order(r))) {
            if(order(l).length===oldIds.length&&order(r).length===oldIds.length)conflicts.push(path+'/ordem');
          }
          const preferred=equal(order(r),oldIds)?l:r,rank=[...new Set([...preferred,...result].map(x=>String(x[key])))];
          return result.sort((a,c)=>rank.indexOf(String(a[key]))-rank.indexOf(String(c[key])));
        }
      }
      if([b,l,r].every(x=>x&&typeof x==='object'&&!Array.isArray(x))) {
        const result={};for(const key of new Set([...Object.keys(b),...Object.keys(l),...Object.keys(r)])) {
          if(['__proto__','constructor','prototype'].includes(key))throw Error('Campo inválido.');
          const value=walk(b[key],l[key],r[key],path+'/'+key);if(value!==undefined)result[key]=value;
        }return result;
      }
      conflicts.push(path);return l;
    }
    return {data:walk(base,local,remote,''),conflicts};
  }
  root.TreinoSyncMerge={canonical,merge};
})(typeof window==='undefined'?globalThis:window);
