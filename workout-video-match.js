/* Local exercise recognition. Exact synonyms may be applied automatically;
   equipment and movement variants remain explicit choices. */
window.WorkoutVideoMatch = (() => {
  const stop = new Set('de do da dos das no na nos nas com para ao a o em e'.split(' '));
  const words = {ag:'agachamento',agach:'agachamento',sup:'supino',elev:'elevacao',elevancao:'elevacao',desenv:'desenvolvimento',rem:'remada',unil:'unilateral',uni:'unilateral',alt:'alternado',alternada:'alternado',alternadas:'alternado',halteres:'halter',pes:'pe',bracos:'braco',joelhos:'joelho',inclinada:'inclinado',sentada:'sentado',deitada:'deitado',cad:'cadeira',maquinas:'maquina',polias:'polia',steps:'step',adutor:'adutora',abdutor:'abdutora'};
  function clean(text) {
    return String(text).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\b(\d+)\s*(graus?|°)/g,'$1').replace(/[^a-z0-9]+/g,' ').trim();
  }
  function canonical(text) {
    let value = clean(text).split(' ').filter(Boolean).map(w=>Object.prototype.hasOwnProperty.call(words,w)?words[w]:w).filter(w=>!stop.has(w)).join(' ');
    const aliases = {
      'extensora':'cadeira extensora','adutora':'cadeira adutora','abdutora':'cadeira abdutora',
      'stepup':'subida step','step up':'subida step','subida step':'subida step',
      'gluteo coice polia':'gluteo polia','elevacao pelvica banco barra':'elevacao pelvica barra',
      'agachamento classico barra':'agachamento livre barra','voador inverso':'crucifixo inverso maquina',
      'crucifixo inverso maquina':'crucifixo inverso maquina'
    };
    return Object.prototype.hasOwnProperty.call(aliases,value)?aliases[value]:value;
  }
  function parts(name) {
    const pieces = String(name).split(/\s*\+\s*/).map(p=>p.trim()).filter(Boolean);
    const qualifier=/^(?:com )?(?:halter(?:es)?|barra(?: w)?|elastico|anilha|caneleira|banco|step|polia|isometria|pausa|curtinhas|unilateral|alternado|carga|peso)$/;
    return pieces.length>1 && pieces.every(p=>/[a-zá-ú]{2}/i.test(p)&&!qualifier.test(clean(p))) ? pieces : [String(name).trim()];
  }
  function driveID(value) {
    try { const url=new URL(value); if(url.hostname==='caio.tail953b6e.ts.net')return driveID(url.searchParams.get('url')||''); return url.hostname==='drive.google.com' ? url.pathname.match(/\/file\/d\/([^/]+)/)?.[1] || url.searchParams.get('id') : null; } catch(error){return null;}
  }
  function names(video) {
    const list=[canonical(video.name),...(video.aliases||[]).map(canonical)];
    // The original CM 172 clip is the verified 45-degree leg press.
    if(video.collection==='cm' && video.id==='1wq8rmGfeoY0pyiq3eXo90SHPx1ePSN1v')list.push('leg press 45');
    return list;
  }
  function incompatible(query, candidate) {
    const q=new Set(query.split(' ')),c=new Set(candidate.split(' '));
    for(const key of ['polia','smith','halter','barra','maquina','inclinado','declinado','sem','unilateral','alternado','inverso','sumo','frontal','semiflexionada'])if(q.has(key)&&!c.has(key))return true;
    if(!q.has('inverso')&&c.has('inverso'))return true;
    for(const key of ['30','45','60','90'])if(q.has(key)&&!c.has(key))return true;
    return false;
  }
  function score(query, candidate) {
    if(query===candidate)return 1;
    if(incompatible(query,candidate))return 0;
    const q=query.split(' '), c=candidate.split(' '), common=q.filter(w=>c.includes(w)).length;
    if(!common || c[0]!==q[0])return 0;
    return 0.75*common/q.length+0.25*common/c.length;
  }
  function rank(name, videos, preferred) {
    const query=canonical(name);
    return videos.map(video=>({video,score:Math.max(...names(video).map(n=>score(query,n)))}))
      .filter(item=>item.score>=0.60)
      .sort((a,b)=>b.score-a.score || Number(b.video.collection===preferred)-Number(a.video.collection===preferred) || Number(b.video.gender==='Feminino')-Number(a.video.gender==='Feminino'));
  }
  function resolve(row, videos, preferred, remembered) {
    const saved=videos.find(v=>v.id===remembered);
    if(saved)return {video:saved,reason:'Sua escolha anterior',suggestions:[]};
    const id=driveID(row.video),linked=videos.find(v=>v.id===id&&v.collection===preferred);
    if(linked)return {video:linked,reason:'Vídeo salvo no treino',suggestions:[]};
    const ranked=rank(row.nome,videos,preferred), exact=ranked.find(item=>item.score===1&&item.video.collection===preferred);
    if(exact)return {video:exact.video,reason:'Reconhecido pelo nome',suggestions:[]};
    const seen=new Set();
    const suggestions=ranked.filter(item=>{const key=item.video.collection+':'+canonical(item.video.name);if(seen.has(key))return false;seen.add(key);return true;}).slice(0,3).map(item=>item.video);
    return {video:null,reason:suggestions.length?'Confira a variação sugerida':'Nenhuma demonstração equivalente encontrada',suggestions};
  }
  return {canonical,parts,rank,resolve,driveID};
})();
