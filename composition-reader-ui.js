/* Review is shared by the workout assessment and the full assessment library. */
window.CompositionImportUI=(()=>{
  const node=(tag,attributes={},text)=>{const el=document.createElement(tag);for(const [k,v] of Object.entries(attributes))el.setAttribute(k,v);if(text!==undefined)el.textContent=text;return el;};
  function value(state,c){const v=c.scope==='ficha'?state.av.ficha?.[c.key]??state.person[c.key]??'':state.av[c.key]??'';if(c.key==='altura'){const n=CompositionReader.number(v);return n!==null?(n<3?n*100:n):v;}return v;}
  function stored(target,fallback){try{const person=JSON.parse(localStorage.getItem('avaliacao_fisica_alunos')||'[]').find(p=>String(p.id)===String(target.personId)),av=person?.avaliacoes?.find(a=>String(a.id)===String(target.avId));return person&&av?{person,av}:fallback;}catch(error){return fallback;}}
  function checkMode(result,mode){
    if(result.source==='InBody'&&mode!=='inbody')throw Error('Este é um laudo InBody. Use o leitor exclusivo InBody logo abaixo.');
    if(result.source==='Fitdays'&&mode!=='fitdays')throw Error('Este é um relatório Fitdays. Use o leitor exclusivo Fitdays logo abaixo.');
    if(mode==='inbody')result.source='InBody';if(mode==='fitdays')result.source='Fitdays';return result;
  }
  function mount(root,config){
    function flow(host,mode){
      const input=node('input',{type:'file',accept:'image/*,application/pdf',hidden:'','data-reader-mode':mode}),button=node('button',{type:'button',class:'composition-reader-open'},mode==='inbody'?'📷 Ler InBody · foto/PDF':mode==='fitdays'?'📷 Ler Fitdays · foto/PDF':'📷 Leitura geral · foto/PDF'),status=node('span',{class:'composition-reader-status',role:'status'});host.append(button,input,status);
      button.onclick=()=>input.click();
      input.onchange=async()=>{const file=input.files[0];input.value='';if(!file)return;const initial=config.getState();if(!initial.av){status.textContent='Selecione uma avaliação.';return;}const target={personId:initial.person.id,avId:initial.av.id},snapshot=JSON.parse(JSON.stringify(initial)),persisted=stored(target,snapshot);button.disabled=true;
        try{const result=await CompositionOCR.read(file,message=>{status.textContent=message;});
          checkMode(result,mode);
          result.file=file;status.textContent=result.candidates.length+' indicadores encontrados.';review(result,snapshot,target,config,persisted,mode);
        }catch(error){status.textContent=error.message;}finally{button.disabled=false;}
      };
    }
    flow(root,'standard');
    const fitdays=node('details',{class:'composition-reader-fitdays'});fitdays.append(node('summary',{},'Fitdays · OCR exclusivo do relatório'));flow(fitdays,'fitdays');
    const inbody=node('details',{class:'composition-reader-inbody'});inbody.append(node('summary',{},'InBody · OCR exclusivo do laudo'));flow(inbody,'inbody');(config.inbodyHost||root).after(fitdays,inbody);
    return {review:(result)=>{const state=config.getState();review(result,JSON.parse(JSON.stringify(state)),{personId:state.person.id,avId:state.av.id},config);}};
  }
  function review(result,snapshot,target,config,persisted=stored(target,snapshot),mode='standard'){
    const dialog=node('dialog',{class:'composition-reader-dialog','aria-label':'Conferir leitura da composição corporal'}),heading=node('h3',{},(mode==='inbody'?'Conferir InBody · ':mode==='fitdays'?'Conferir Fitdays · ':'Conferir leitura geral · ')+snapshot.person.nome),source=node('p',{},result.source+' · '+(result.filename||'Documento')),intro=node('p',{class:'composition-reader-note'},'Confira os valores e unidades. Apenas os campos marcados serão preenchidos nesta avaliação.');
    const status=node('p',{role:'status',class:'composition-reader-status'}),table=node('div',{class:'composition-reader-table'}),raw=node('details'),summary=node('summary',{},'Texto lido · corrigir e reler'),text=node('textarea',{'aria-label':'Texto reconhecido do laudo'}),reparse=node('button',{type:'button'},'Reler texto corrigido');text.value=result.text;raw.append(summary,text,reparse);
    let originalUrl=null;const original=node('details');original.append(node('summary',{},'Ver arquivo original'));
    if(result.file){originalUrl=URL.createObjectURL(result.file);const link=node('a',{href:originalUrl,target:'_blank',rel:'noopener'},'Abrir original em outra aba');original.append(link);if(result.file.type.startsWith('image/'))original.append(node('img',{src:originalUrl,alt:'Arquivo original para conferir a leitura',loading:'lazy',style:'display:block;max-width:100%;height:auto;margin-top:8px'}));}
    const options=node('div',{class:'composition-reader-options'}),dateLabel=node('label'),dateCheck=node('input',{type:'checkbox'});dateLabel.append(dateCheck,document.createTextNode('Usar data do laudo: '+(result.date||'não identificada')));dateCheck.disabled=!result.date;
    const sexLabel=node('label'),sexCheck=node('input',{type:'checkbox'});sexLabel.append(sexCheck,document.createTextNode('Usar sexo do laudo: '+({F:'Feminino',M:'Masculino'}[result.sex]||'não identificado')));sexCheck.disabled=!result.sex;sexCheck.checked=!!result.sex&&!snapshot.person.sexo;options.append(dateLabel,sexLabel);
    const actions=node('div',{class:'composition-reader-actions'}),apply=node('button',{type:'button',class:'composition-reader-apply'},'Preencher selecionados'),cancel=node('button',{type:'button'},'Cancelar');actions.append(cancel,apply);dialog.append(heading,source,intro,options,table,original,raw,status,actions);document.body.append(dialog);let entries=[];
    function render(){table.replaceChildren();entries=[];for(const candidate of result.candidates){const row=node('div',{class:'composition-reader-row'}),check=node('input',{type:'checkbox','aria-label':'Importar '+candidate.label+' ('+candidate.unit+')'}),label=node('div'),title=node('strong',{},candidate.label+' ('+candidate.unit+')'),old=value(snapshot,candidate),note=node('small',{},(old!==''?'Atual: '+old+' · ':'')+(candidate.review||'Confira no documento.')),edit=node('input',{type:'text',inputmode:candidate.unit==='texto'?'text':'decimal','aria-label':'Valor lido de '+candidate.label+' ('+candidate.unit+')'}),evidence=node('details'),evidenceTitle=node('summary',{},'Trecho lido'),excerpt=node('p',{},candidate.evidence);evidence.append(evidenceTitle,excerpt);label.append(title,note,evidence);edit.value=candidate.value;check.checked=candidate.selected;row.append(check,label,edit);table.append(row);const item={candidate,check,edit};entries.push(item);check.onchange=()=>{if(check.checked)for(const other of entries)if(other!==item&&other.candidate.key===candidate.key)other.check.checked=false;updateCount();};edit.oninput=()=>{check.checked=true;check.dispatchEvent(new Event('change'));};}
      if(!entries.length)table.append(node('p',{},'Nenhum indicador confiável encontrado. Use uma imagem mais nítida ou corrija o texto lido.'));
      if(result.unresolved.length)table.append(node('p',{class:'composition-reader-note'},result.unresolved.length+' trechos ficaram sem campo ou unidade. Confira o texto lido para completar o que faltar.'));
      updateCount();
    }
    function updateCount(){const count=entries.filter(e=>e.check.checked).length;apply.textContent='Preencher '+count+' campo'+(count===1?'':'s');apply.disabled=!count;}
    reparse.onclick=()=>{try{const parsed=checkMode({...CompositionReader.parse(text.value),filename:result.filename,file:result.file},mode);result=parsed;source.textContent=result.source+' · '+(result.filename||'Documento');dateCheck.checked=false;dateCheck.disabled=!result.date;dateLabel.lastChild.textContent='Usar data do laudo: '+(result.date||'não identificada');sexCheck.checked=false;sexCheck.disabled=!result.sex;sexLabel.lastChild.textContent='Usar sexo do laudo: '+({F:'Feminino',M:'Masculino'}[result.sex]||'não identificado');render();status.textContent='Texto relido.';}catch(error){status.textContent=error.message;}};
    cancel.onclick=()=>dialog.close();dialog.addEventListener('close',()=>{if(originalUrl)URL.revokeObjectURL(originalUrl);dialog.remove();},{once:true});
    apply.onclick=()=>{
      try{
        const current=config.getState();if(String(current.person.id)!==String(target.personId)||String(current.av?.id)!==String(target.avId))throw Error('A avaliação aberta mudou. Reabra a leitura na avaliação desejada.');
        const selected=entries.filter(e=>e.check.checked).map(e=>({...e.candidate,value:e.edit.value}));
        const records=JSON.parse(localStorage.getItem('avaliacao_fisica_alunos')||'[]'),person=records.find(p=>String(p.id)===String(target.personId)),av=person?.avaliacoes?.find(a=>String(a.id)===String(target.avId));
        if(!av)throw Error('Esta avaliação não está mais disponível.');
        for(const c of selected)if(String(value({person,av},c))!==String(value(persisted,c)))throw Error('O campo '+c.label+' mudou durante a leitura. Reabra a importação para conferir os dados atuais.');
        const change=CompositionReader.prepare(current,result,selected);
        if(dateCheck.checked&&result.date)change.fields.data=result.date;
        if(sexCheck.checked&&result.sex)change.personFields.sexo=result.sex;
        config.importValues(change,target);dialog.close();
      }catch(error){status.textContent=error.message;}
    };
    render();dialog.showModal();
  }
  return {mount};
})();
