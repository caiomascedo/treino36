/* Measurement provenance and related units; never infer an old record's entry date. */
window.CompositionContext=(()=>{
  const stamp=value=>{const date=new Date(value);return value&&Number.isFinite(date.getTime())?date.toLocaleString('pt-BR',{dateStyle:'short',timeStyle:'short'}):'data de inclusão não registrada';};
  const source=av=>String(av.origemComposicao||'').trim()||'Origem não informada';
  function record(av,key,value,origin,now=Date.now()){
    const previous=av[key+'Registro'],old=av[key];
    if(String(old??'')===String(value??'')&&previous?.source===origin)return {};
    const changes=Array.isArray(previous?.changes)?previous.changes.map(entry=>({...entry})):[];
    const hadOld=old!==undefined&&old!==null&&String(old).trim()!=='';
    if(!previous&&hadOld)changes.push({at:null,value:String(old),source:''});
    const last=changes.at(-1),entry={at:now,value:String(value),source:origin||''};
    if(last?.at&&now-last.at<3000&&last.source===entry.source)changes[changes.length-1]=entry;else changes.push(entry);
    return {[key+'Registro']:{createdAt:previous?previous.createdAt:(hadOld?null:now),updatedAt:now,source:origin||'',changes:changes.slice(-8)}};
  }
  function pdfSource(av){const origins=[...new Set(Object.entries(av).filter(([key,record])=>key.endsWith('Registro')&&record&&record.source&&String(av[key.slice(0,-8)]??'').trim()!=='').map(([,record])=>record.source))];return origins.length?origins.join(' / '):String(av.origemComposicao||'').trim();}
  function mountHistory(detail,input,field,config){
    const info=document.createElement('p');info.className='composition-record-info';
    const history=document.createElement('details');history.className='composition-record-history';const title=document.createElement('summary');title.textContent='Histórico e origem';const list=document.createElement('ul');history.append(title,list);detail.append(info,history);
    const update=()=>{
      const state=config.getState(),record=state.av[field.key+'Registro'];
      info.textContent=record?'Incluído: '+stamp(record.createdAt)+' · Atualizado: '+stamp(record.updatedAt)+' · '+(record.source||'Origem não informada'):'Avaliação: '+(state.av.data||'sem data')+' · '+source(state.av)+' · Data de inclusão não registrada.';
      if(!history.open)return;
      list.replaceChildren();
      const add=text=>{const li=document.createElement('li');li.textContent=text;list.append(li);};
      (state.person.avaliacoes||[]).filter(av=>String(av.id)!==String(state.av.id)&&String(av[field.key]??'').trim()!=='').slice(-10).forEach(av=>add((av.data||'Sem data')+' · '+av[field.key]+' · '+(av[field.key+'Registro']?(av[field.key+'Registro'].source||'Origem não informada'):source(av))));
      if(Array.isArray(record?.changes)&&record.changes.length)record.changes.filter(entry=>entry&&typeof entry==='object').forEach(entry=>add(stamp(entry.at)+' · '+(entry.value||'Valor apagado')+' · '+(entry.source||'Origem não informada')));
      else add((state.av.data||'Sem data')+' · '+(input.value||'Não informado')+' · '+source(state.av)+' · inclusão não registrada');
    };
    history.addEventListener('toggle',update);return update;
  }
  function gauge(host,result){
    host.replaceChildren();
    let zones=result.zones,value=result.percent;
    if(!zones&&result.manual){zones=[{label:'Baixo',color:'#c93732',min:0,max:1},{label:'Saudável / Bom / Excelente',color:'#23864a',min:1,max:2},{label:'Moderado',color:'#c77700',min:2,max:3},{label:'Elevado / Muito elevado',color:'#157ab8',min:3,max:4}];value=result.text==='Baixo'?0.5:['Saudável','Bom','Excelente'].includes(result.text)?1.5:result.text==='Moderado'?2.5:3.5;}
    if(!zones){if(result.text==='Consultar laudo'){const text=document.createElement('p');text.textContent='Referência específica da balança / laudo';host.append(text);}return;}
    const bar=document.createElement('div');bar.className='composition-gauge-bar';bar.setAttribute('role','img');bar.setAttribute('aria-label',result.text+' — '+(result.manual?'classificação do laudo':'referência por idade e sexo'));
    zones.forEach(zone=>{const segment=document.createElement('span');segment.style.flex=zone.max-zone.min;segment.style.background=zone.color;bar.append(segment);});
    const marker=document.createElement('i');marker.className='composition-gauge-marker';marker.style.left=Math.max(0,Math.min(100,(value-zones[0].min)/(zones.at(-1).max-zones[0].min)*100))+'%';bar.append(marker);
    const legend=document.createElement('ul');legend.className='composition-gauge-legend';zones.forEach(zone=>{const li=document.createElement('li'),dot=document.createElement('i');dot.style.background=zone.color;li.append(dot,document.createTextNode(zone.label));legend.append(li);});host.append(bar,legend);
  }
  return {record,pdfSource,mountHistory,gauge,source};
})();
