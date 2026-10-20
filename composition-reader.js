/* Local OCR/PDF transcription. Values are candidates, never inferred nutrition. */
window.CompositionReader=(()=>{
  const normalize=v=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/g0rdura/g,'gordura').replace(/[–—−]/g,'-').replace(/\s+/g,' ').trim();
  const number=v=>{let s=String(v??'').trim().replace(/\s/g,'');if(/^[-+]?\d{1,3}(?:\.\d{3})+(?:,\d+)?$/.test(s))s=s.replace(/\./g,'');s=s.replace(',','.');return /^[-+]?\d+(?:\.\d+)?$/.test(s)&&Number.isFinite(Number(s))?Number(s):null;};
  const definitions={
    peso:['Peso','kg',10,350],imc:['IMC','kg/m²',5,100],gordura:['Gordura corporal','%',0,80],pesoGordura:['Peso da gordura','kg',0,250],
    visceral:['Gordura visceral','índice',0,100],massamuscular:['Massa muscular total','kg',0,250],massaMuscularPct:['Taxa / registro de massa muscular','%',0,100],musculoEsqueleticoKg:['Massa muscular esquelética','kg',0,150],musculoEsqueleticoPct:['Massa muscular esquelética','%',0,100],
    proteina:['Proteína','%',0,100],proteinaKg:['Proteína · InBody','kg',0,100],agua:['Água corporal','%',0,100],pesoAgua:['Peso da água','kg',0,150],aguaLitros:['Água corporal total · InBody','L',0,150],
    massaLivreGordura:['Massa livre de gordura','kg',0,300],gorduraSubcutanea:['Gordura subcutânea','%',0,80],massaOssea:['Massa óssea','kg',0,30],mineraisKg:['Minerais · InBody','kg',0,30],
    metabolismoInformado:['TMB / metabolismo informado pela balança','kcal/dia',200,6000],idadeMetabolica:['Idade metabólica','anos',1,125],altura:['Altura','cm',60,260,'ficha'],idade:['Idade real','anos',1,125,'ficha'],
    pontuacaoInbody:['Pontuação InBody','pontos',0,300],pesoIdealInbody:['Peso ideal / alvo · InBody','kg',10,350],controlePesoInbody:['Controle de peso · InBody','kg',-200,200],controleGorduraInbody:['Controle de gordura · InBody','kg',-200,200],controleMuscularInbody:['Controle muscular · InBody','kg',-200,200],rcqInformado:['Relação cintura/quadril · InBody','índice',.2,3],grauObesidadeInbody:['Grau de obesidade · InBody','%',0,500]
  };
  const partNames={bracoDireito:'braço direito',bracoEsquerdo:'braço esquerdo',tronco:'tronco',pernaDireita:'perna direita',pernaEsquerda:'perna esquerda'};
  const rules=[
    ['controlePesoInbody',/controle\s*(?:de\s*)?peso/],['controleGorduraInbody',/controle\s*(?:de\s*)?gordura/],['controleMuscularInbody',/controle\s*(?:de\s*)?muscular/],['pesoIdealInbody',/peso\s*(?:ideal|alvo)/],['pontuacaoInbody',/pontuacao\s*(?:inbody)?/],['grauObesidadeInbody',/grau\s*(?:de\s*)?obesidade/],['rcqInformado',/(?:relacao\s*cintura\s*[-/]?\s*quadril|\brcq\b)/],
    ['massaLivreGordura',/massa\s*(?:livre\s*(?:de\s*)?gordura|magra\s*total)/],['gorduraSubcutanea',/gordura\s*subcutanea/],['visceral',/(?:nivel\s*(?:de\s*)?)?gordura\s*visceral/],['idadeMetabolica',/idade\s*metab[od0]lica/],['metabolismoInformado',/(?:taxa\s*metabolica\s*basal|metabolismo(?:\s*(?:da\s*)?bioimpedancia)?|\btmb\b)/],
    ['muscleSkeletal',/(?:massa\s*)?(?:muscular|musc\.?)\s*esqueletica/],['muscleTotal',/(?:taxa\s*muscular|registro\s*(?:de\s*)?massa\s*muscular|massa\s*muscular(?:\s*total)?)/],
    ['massaOssea',/massa\s*ossea/],['mineraisKg',/\bminerais\b/],['fat',/(?:peso\s*(?:da\s*)?gordura|massa\s*(?:de\s*)?gordura|gordura\s*corporal|percentual\s*(?:de\s*)?gordura|porcentual\s*(?:de\s*)?gordura|\bpgc\b|\bgordura\s*\(%\))/],
    ['water',/(?:peso\s*(?:da\s*)?agua|agua\s*(?:corporal(?:\s*total)?)?)/],['protein',/\bproteina\b/],['imc',/\bimc\b/],['peso',/\bpeso\b/],['altura',/\baltura\b/],['idade',/idade\s*real|\bidade\b(?!\s*[a-z]{3,})/]
  ];
  function identify(text){const s=normalize(text);for(const [key,re] of rules){const m=re.exec(s);if(m)return {key,index:m.index,end:m.index+m[0].length,label:m[0]};}return null;}
  function splitLabels(row){const s=normalize(row.text),hits=[];for(const [,re] of rules){const all=new RegExp(re.source,'g');for(const match of s.matchAll(all)){const start=match.index,end=start+match[0].length;if(!hits.some(h=>start<h.end&&end>h.start))hits.push({start,end});}}hits.sort((a,b)=>a.start-b.start);return hits.length<2?[row]:hits.map((hit,i)=>({...row,text:row.text.slice(hit.start,hits[i+1]?.start),words:undefined}));}
  function unit(text){const s=normalize(text).replace(/(\d)(kg|kcal|cm|l)\b/g,'$1 $2');return /%|percent/.test(s)?'%':/\bkg\b|\bquilogram/.test(s)?'kg':/\b(?:litros?|l)\b/.test(s)?'L':null;}
  function keyFor(id,u){if(id.key==='muscleSkeletal')return u==='%'?'musculoEsqueleticoPct':u==='kg'?'musculoEsqueleticoKg':null;if(id.key==='muscleTotal')return u==='%'||/taxa|registro/.test(id.label)?'massaMuscularPct':u==='kg'?'massamuscular':null;if(id.key==='fat')return u==='kg'||/peso|massa/.test(id.label)?'pesoGordura':u==='%'||id.label==='pgc'?'gordura':null;if(id.key==='water')return u==='%'?'agua':u==='kg'?'pesoAgua':u==='L'?'aguaLitros':null;if(id.key==='protein')return u==='kg'?'proteinaKg':u==='%'?'proteina':null;return id.key;}
  const numericTokens=text=>[...String(text).replace(/[–—−]/g,'-').replace(/([+-])\s+(?=\d)/g,'$1').replace(/kg\s*\/\s*m[²2]/gi,'').replace(/(\d)(kg|kcal|cm|l)\b/gi,'$1 $2').matchAll(/(?<![\p{L}\d])[-+]?\d+(?:[.,]\d+)*(?![\p{L}\d])/gu)].map(m=>({raw:m[0],value:number(m[0]),at:m.index})).filter(x=>x.value!==null);
  function rowsFromWords(words){
    const rows=[];for(const word of words.slice().sort((a,b)=>a.y0-b.y0||a.x0-b.x0)){const cy=(word.y0+word.y1)/2;let row=rows.find(r=>Math.abs(r.cy-cy)<Math.max(4,(word.y1-word.y0)*.55));if(!row){row={cy,words:[]};rows.push(row);}row.words.push(word);}
    return rows.sort((a,b)=>a.cy-b.cy).map(r=>{r.words.sort((a,b)=>a.x0-b.x0);return {text:r.words.map(w=>w.text).join(' '),words:r.words,confidence:r.words.reduce((s,w)=>s+(w.confidence??95),0)/r.words.length};});
  }
  function parse(input){
    const originalRows=typeof input==='string'?input.split(/\r?\n/).filter(s=>s.trim()).map(text=>({text,confidence:100})):input;
    const rows=originalRows.flatMap(splitLabels);
    const full=rows.map(r=>r.text).join('\n'),source=/in\s*body/i.test(full)?'InBody':/fit\s*days/i.test(full)?'Fitdays':/registro\s*corporal|avaliacao\s*de\s*bioimpedancia/i.test(normalize(full))?'Planilha de bioimpedância':'Balança / laudo';
    const candidates=[],unresolved=[];let history=false,segment=null;
    function add(key,value,row,evidence,confidence=100,extras={}){
      const def=definitions[key];if(!def||value===null)return;
      const valid=value>=def[2]&&value<=def[3];candidates.push({key,value:String(value),label:def[0],unit:def[1],scope:def[4]||'av',confidence,valid,evidence,review:!valid?'Valor fora da faixa de leitura; confira o documento.':confidence<85?'Leitura com baixa confiança.':'',...extras});
    }
    for(let i=0;i<rows.length;i++){
      const row=rows[i];let text=row.text;const s=normalize(text),conf=row.confidence??95;
      if(/historico\s*(?:da\s*)?composicao/.test(s))history=true;if(/impedancia/.test(s))history=false;
      if(history)continue;
      if(/massa\s*magra\s*segmentar/.test(s))segment='magra';if(/gordura\s*segmentar/.test(s))segment='gordura';
      const parts=[['bracoDireito',/braco\s*direito/],['bracoEsquerdo',/braco\s*esquerdo/],['tronco',/\btronco\b/],['pernaDireita',/perna\s*direita/],['pernaEsquerda',/perna\s*esquerda/]];
      const part=parts.find(([,re])=>re.test(s));
      if(part&&segment){const nums=numericTokens(text.slice(s.search(part[1])+s.match(part[1])[0].length));if(nums.length){const prefix=segment==='magra'?'magra_':'gordura_',k=prefix+part[0];definitions[k]=[`${segment==='magra'?'Massa magra':'Gordura'} · ${partNames[part[0]]}`,'kg',0,150];add(k,nums[0].value,row,text,conf);if(nums[1]&&/%/.test(text)){const a=(segment==='magra'?'adequacaoMagra_':'adequacaoGordura_')+part[0];definitions[a]=['Adequação · '+partNames[part[0]],'%',0,1000];add(a,nums[1].value,row,text,conf);}continue;}}
      const imp=s.match(/\b(20|100)\s*khz\b/);if(imp&&/impedancia|\bbd\b|\bbe\b|\btr\b/.test(normalize(full))){const tail=text.slice(imp.index+imp[0].length),nums=numericTokens(tail);if(nums.length===5){['bd','be','tr','pd','pe'].forEach((part,j)=>{const key='impedancia'+imp[1]+'_'+part;definitions[key]=['Impedância '+imp[1]+' kHz · '+part,'Ω',0,5000];add(key,nums[j].value,row,text,conf);});continue;}}
      let id=identify(text);if((!id||!numericTokens(text).length)&&i+1<rows.length&&!identify(rows[i+1].text)){const joined=text+' '+rows[i+1].text,wrapped=identify(joined);if(wrapped){text=joined;id=wrapped;}}if(!id)continue;
      let combined=text,tail=text.slice(id.end),tokens=numericTokens(tail);
      if(!tokens.length&&i+1<rows.length&&!identify(rows[i+1].text)){combined+=' '+rows[i+1].text;tail+=' '+rows[i+1].text;tokens=numericTokens(tail);}
      if(!tokens.length&&i+2<rows.length&&!identify(rows[i+1].text)&&!identify(rows[i+2].text)){combined+=' '+rows[i+2].text;tail+=' '+rows[i+2].text;tokens=numericTokens(tail);}
      // Captions can wrap before the numeric row (e.g. Massa Musc. / Esquelética).
      if(!tokens.length){unresolved.push(text);continue;}
      const next=identify(tail);if(next&&next.index>0)tail=tail.slice(0,next.index);
      if(/nao\s*informado|sem\s*(?:valor|dado)/.test(normalize(tail)))continue;
      tokens=numericTokens(tail);if(!tokens.length)continue;
      const ref=tail.match(/\(\s*(\d+(?:[.,]\d+)?)\s*(?:-|~|a|–)\s*(\d+(?:[.,]\d+)?)\s*\)/i);
      if(ref){tokens=tokens.filter(t=>t.at<ref.index||t.at>=ref.index+ref[0].length);if(!tokens.length){unresolved.push(text+' [somente referência]');continue;}}
      if(tokens.length>3&&!ref){unresolved.push(text);continue;} // Graph ticks are not measurements.
      const updated=identify(combined);if(updated&&updated.key!==id.key){id=updated;tail=combined.slice(id.end);tokens=numericTokens(tail);if(!tokens.length)continue;}
      const u=unit(combined),key=keyFor(id,u);
      if(!key){unresolved.push(combined+' [unidade não identificada]');continue;}
      let value=tokens[0].value;
      if(key==='altura'&&value<3)value*=100;
      const classification=(combined.match(/\b(Excelente|Saud[aá]vel|Normal|Bom|Baixo|Abaixo|Acima|Alto|M[eé]dio risco|M[eé]dio|Sobrepeso|Obesidade|Desidratado)\b/i)||[])[0]||'';
      const extras={classification};if(ref){extras.refMin=number(ref[1]);extras.refMax=number(ref[2]);}
      add(key,value,row,combined,conf,extras);
    }
    // Match small profile headers to the value directly below, not to a neighboring column.
    for(let i=0;i<originalRows.length-1;i++)for(const word of originalRows[i].words||[]){const label=normalize(word.text);if(!['altura','idade'].includes(label))continue;const nearby=(originalRows[i+1].words||[]).filter(w=>Math.abs((w.x0+w.x1)/2-(word.x0+word.x1)/2)<Math.max(25,word.x1-word.x0));const token=nearby.map(w=>numericTokens(w.text)[0]).find(Boolean);if(token)add(label,label==='altura'&&token.value<3?token.value*100:token.value,originalRows[i],word.text+' '+nearby.map(w=>w.text).join(' '),Math.min(originalRows[i].confidence??95,originalRows[i+1].confidence??95));}
    // Diagram numbers have no anatomical label on their own. Only offer them for
    // review when both side labels and the expected 2/1/2 layout are present.
    if(source==='InBody'){
      const anchors={};
      for(const row of originalRows){for(const word of row.words||[])for(const group of ['magra','gordura']){const pattern=group==='magra'?/analise\s*(?:da\s*)?massa\s*magra\s*segmentar/:/analise\s*(?:da\s*)?gordura\s*segmentar/,match=normalize(word.text).match(pattern);if(match)anchors[group]={x:word.x0+(word.x1-word.x0)*(match.index/word.text.length),y:word.y1};}const words=row.words||[];for(let j=0;j<words.length;j++){const name=normalize(words[j].text),next=normalize(words[j+1]?.text);if(['magra','gordura'].includes(name)&&next.startsWith('segmentar')){const start=Math.max(0,j-(name==='magra'?3:2));anchors[name]={x:words[start].x0,y:words[j].y1};}}}
      if(anchors.magra&&anchors.gordura&&anchors.gordura.x>anchors.magra.x){
        const width=anchors.gordura.x-anchors.magra.x,all=originalRows.flatMap(r=>r.words||[]),historyRow=originalRows.find(r=>/historico.*composicao/.test(normalize(r.text)));
        for(const group of ['magra','gordura']){
          const anchor=anchors[group],end=historyRow?.words?.[0]?.y0??anchor.y+width*1.5,words=all.filter(w=>w.x0>=anchor.x&&w.x0<anchor.x+width&&w.y0>anchor.y&&w.y0<end);
          const leftWord=words.find(w=>/esquerdo/.test(normalize(w.text))),rightWord=words.find(w=>/direito/.test(normalize(w.text)));if(!leftWord||!rightWord)continue;
          const leftIsEsquerdo=leftWord.x0<rightWord.x0,measurements=[];
          for(const row of originalRows){const rw=(row.words||[]).filter(w=>words.includes(w));for(let j=0;j<rw.length;j++){const word=rw[j],combined=word.text+' '+(rw[j+1]?.text||'');if(!/^[-+]?\d[\d.,]*\s*kg\b/i.test(combined))continue;const n=numericTokens(word.text)[0];if(n)measurements.push({word,value:n.value});}}
          const bands=[];for(const measure of measurements.sort((a,b)=>a.word.y0-b.word.y0)){let band=bands.find(b=>Math.abs(b.y-measure.word.y0)<width*.06);if(!band){band={y:measure.word.y0,values:[]};bands.push(band);}band.values.push(measure);}
          if(bands.length!==3||bands[0].values.length!==2||bands[1].values.length!==1||bands[2].values.length!==2)continue;
          for(let band=0;band<3;band++){const values=bands[band].values.sort((a,b)=>a.word.x0-b.word.x0);for(let j=0;j<values.length;j++){const measure=values[j],side=j===0?(leftIsEsquerdo?'Esquerdo':'Direito'):(leftIsEsquerdo?'Direito':'Esquerdo'),part=band===1?'tronco':band===0?'braco'+side:'perna'+(side==='Direito'?'Direita':'Esquerda'),key=group+'_'+part;
              definitions[key]=[(group==='magra'?'Massa magra':'Gordura')+' · '+partNames[part],'kg',0,150];add(key,measure.value,null,measure.word.text+' · diagrama segmentar',80,{review:'Identificado pela posição no diagrama; confirme região e lado.'});
            }}
        }
      }
    }
    const unique=[];
    for(const candidate of candidates){const existing=unique.find(c=>c.key===candidate.key&&c.value===candidate.value);if(existing){if(candidate.confidence>existing.confidence)Object.assign(existing,candidate);}else unique.push(candidate);}
    for(const candidate of unique){candidate.conflict=unique.some(c=>c.key===candidate.key&&c.value!==candidate.value);candidate.selected=candidate.valid&&!candidate.conflict&&candidate.confidence>=85;if(candidate.conflict)candidate.review='Mais de um valor para este indicador. Selecione o correto.';}
    const datePattern=/\b(\d{2})[/.](\d{2})[/.](\d{2}|\d{4})\b/,dateRow=originalRows.find(row=>datePattern.test(row.text)),date=dateRow?.text.match(datePattern),time=dateRow?.text.match(/\b([012]\d:[0-5]\d)\b/);
    let dateText='';if(date){const year=Number(date[3].length===2?'20'+date[3]:date[3]),month=Number(date[2]),day=Number(date[1]),parsed=new Date(year,month-1,day);if(parsed.getFullYear()===year&&parsed.getMonth()===month-1&&parsed.getDate()===day)dateText=date[1]+'/'+date[2]+'/'+year;}
    const female=/\bfeminino\b|\bmulher\b/i.test(full),male=/\bmasculino\b|\bhomem\b/i.test(full),sex=female&&!male?'F':male&&!female?'M':'';
    if(source==='InBody'){
      for(const [key,label,value] of [['horaLaudoInbody','Horário do exame · InBody',time?.[1]],['idLaudoInbody','ID do exame · InBody',full.match(/\bID\b\s*:?\s*([A-Za-z0-9-]*\d[A-Za-z0-9-]*)/i)?.[1]]])if(value){definitions[key]=[label,'texto',null,null,'av','text'];unique.push({key,label,value,unit:'texto',scope:'av',valid:true,selected:true,confidence:95,evidence:value});}
    }
    return {source,candidates:unique,unresolved:[...new Set(unresolved)],text:full,date:dateText,time:time?.[1]||'',sex};
  }
  function prepare(state,result,selected){
    const fields={},personFields={},ficha={...(state.av.ficha||{})},base=new Set(state.person.composicaoCampos||window.CompositionExtras?.baseFields.composicao.map(f=>f.key)||[]),extras=new Set(state.person.composicaoExtras||[]),protectedValues={...(state.av.laudoValores?.values||{})},guards={...(state.av.laudoValores?.guards||{})},protectedKeys=[];
    for(const candidate of selected){const def=definitions[candidate.key];if(def?.[5]==='text'){const text=String(candidate.value).trim();if(!text||text.length>80)throw Error('Confira '+candidate.label+'.');fields[candidate.key]=text;continue;}const n=number(candidate.value);if(!def||n===null||n<def[2]||n>def[3])throw Error('Confira o valor de '+candidate.label+'.');
      if(candidate.scope==='ficha'){ficha[candidate.key]=String(candidate.key==='altura'?n/100:n);continue;}
      fields[candidate.key]=String(n);if(['imc','idadeMetabolica'].includes(candidate.key)){protectedValues[candidate.key]=String(n);protectedKeys.push(candidate.key);}
      if(window.CompositionExtras?.baseFields.composicao.some(f=>f.key===candidate.key))base.add(candidate.key);else extras.add(candidate.key);
      if(window.CompositionContext)Object.assign(fields,CompositionContext.record(state.av,candidate.key,String(n),result.source));
      const rating=['Baixo','Saudável','Bom','Excelente','Moderado','Elevado','Muito elevado','Abaixo','Normal','Acima'].find(label=>normalize(label)===normalize(candidate.classification));fields[candidate.key+'Classificacao']=rating||'';
      if(candidate.refMin===undefined||candidate.refMax===undefined){if(state.av[candidate.key+'RefMin']!==undefined)fields[candidate.key+'RefMin']='';if(state.av[candidate.key+'RefMax']!==undefined)fields[candidate.key+'RefMax']='';}
      if(candidate.refMin!==undefined&&candidate.refMax!==undefined){fields[candidate.key+'RefMin']=String(candidate.refMin);fields[candidate.key+'RefMax']=String(candidate.refMax);}
    }
    fields.ficha=ficha;fields.origemComposicao=result.source;fields.laudoImportado={source:result.source,at:new Date().toISOString(),text:result.text.slice(0,50000),classifications:Object.fromEntries(selected.filter(c=>c.classification).map(c=>[c.key,c.classification]))};
    for(const key of protectedKeys)guards[key]={peso:String(fields.peso??state.av.peso??''),altura:String(ficha.altura??state.person.altura??'')};
    fields.laudoValores={values:protectedValues,guards};
    personFields.composicaoCampos=[...base];personFields.composicaoExtras=[...extras];
    return {fields,personFields};
  }
  function commit(state,change,calculate){
    const nextAv={...state.av,...change.fields},personFields={...change.personFields};
    if(Object.hasOwn(change.fields,'peso')&&state.person.avaliacoes.at(-1)===state.av){personFields.pesoAtual=nextAv.peso;personFields.pesoAtualAvaliacaoId=nextAv.id;}
    const nextPerson={...state.person,...personFields,avaliacoes:state.person.avaliacoes.map(av=>String(av.id)===String(nextAv.id)?nextAv:av)};
    calculate(nextPerson,nextAv.id);
    const calculated=Object.fromEntries(['imc','tmb','idadeMetabolica','_dobras','_dobrasAviso','_dobrasRegistro','protocolo'].filter(key=>key in nextAv).map(key=>[key,nextAv[key]]));
    TreinoStorage.stageAssessment(state.person.id,state.av.id,{...change.fields,...calculated},personFields);
    Object.assign(state.av,nextAv);Object.assign(state.person,personFields);
  }
  function reportedValue(person,av,key,fallback){const saved=av.laudoValores;if(!saved?.values||saved.values[key]===undefined)return fallback;const height=String(av.ficha?.altura??person.altura??'');const guard=saved.guards?.[key]||saved;return number(guard.peso)===number(av.peso)&&number(guard.altura)===number(height)?saved.values[key]:fallback;}
  return {normalize,number,definitions,parse,prepare,commit,reportedValue,rowsFromWords};
})();
