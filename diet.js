/* A small paste-to-PDF editor using the pupil already selected in the workout. */
window.DietEditor = (() => {
  const plain = text => text.replace(/\*\*|__|`/g, '').replace(/\p{Extended_Pictographic}|[\uFE0F\u200D]/gu, '').replace(/^\s*#{1,6}\s*/, '').trim();
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const meals = /^(?:cafe da manha|cafe|desjejum|lanche da manha|almoco|lanche da tarde|jantar|ceia|pre[- ]?treino|pos[- ]?treino|lanche(?:\s+\d+)?|refeicao\s*\d+|orientacoes(?: gerais)?|observacoes|recomendacoes|resumo(?: diario)?|total(?: diario| do dia| geral)|totais(?: do dia)?)(?=$|\s*[:(–—-]|\s+\d)/;
  function parse(text) {
    const sections = [];
    let current;
    for (const raw of text.split(/\r?\n/)) {
      const line = plain(raw).replace(/^\s*(?:[-*•▪]+\s*|\d+\)\s*|\d+\.\s+)/, '').trim();
      if (!line || /^[\s\p{P}\p{S}]+$/u.test(line)) continue;
      const candidate = line.replace(/^\d{1,2}(?::\d{2}|h\d{0,2})\s*[-–—:]?\s*/i, '');
      const match = normalize(candidate).match(meals);
      if (match) {
        // An inline meal ("Almoço: arroz...") retains the food after the colon.
        const tail = candidate.slice(match[0].length);
        const inline = tail.match(/^\s*:\s*(.+)$/);
        const colon = inline && !/^\d{1,2}(?::\d{2}|h\d{0,2})(?:\s*(?:h|horas?))?$/i.test(inline[1]) ? inline : null;
        const prefix = line.slice(0, line.length - candidate.length);
        current = {title: colon ? prefix + candidate.slice(0, match[0].length) : line, items: []};
        sections.push(current);
        if (colon) current.items.push(colon[1]);
      } else {
        if (!current) { current = {title: 'Plano alimentar', items: []}; sections.push(current); }
        current.items.push(line);
      }
    }
    return sections;
  }
  let pdfLibrary;
  const C = () => window.DietCalculations;
  const settingsKeys = ['sex','age','height','weight','activity','goal','calories','protein','carbs','fat'];
  const fmt = value => value === null ? '—' : Number(value.toFixed(1)).toLocaleString('pt-BR');
  function profile(student) {
    const ficha = (student?.infoGuias || []).find(g => g.id === student.avaliacaoFichaId) || student?.infoGuias?.at(-1) || student?.infoRelevante || {};
    let person = {}, av = {};
    if (student && window.AvaliacaoTreinoSync) {
      try {const sync = AvaliacaoTreinoSync; person = sync.resolve(sync.read(sync.key),student) || {}; av = person.avaliacoes?.find(a => a.id === person.avaliacaoPreferidaId) || person.avaliacoes?.at(-1) || {};} catch(error) {}
    }
    const height = C().number(ficha.altura || av.ficha?.altura || person.altura);
    return {sex:person.sexo || '',age:ficha.idade || av.ficha?.idade || person.idade || '',height:height === null ? '' : String(height < 3.5 ? Math.round(height*100) : height),weight:ficha.peso || av.peso || person.pesoAtual || '',activity:'moderada'};
  }
  function mount(config) {
    const dialog = config.createDialog('dietDialog', '🥗 Dieta',
      '<button type="button" id="dietExpandBtn" aria-pressed="false">⛶ Ampliar</button><p id="dietStudentName"></p>' +
      '<details id="dietCalculations"><summary>TMB, meta e calorias</summary><div class="diet-calc-grid">' +
      '<label>Sexo para cálculo<select id="diet-sex"><option value="">Selecionar</option><option value="F">Feminino</option><option value="M">Masculino</option></select></label>' +
      '<label>Idade<input id="diet-age" inputmode="decimal" placeholder="Anos"></label><label>Altura (cm)<input id="diet-height" inputmode="decimal"></label><label>Peso (kg)<input id="diet-weight" inputmode="decimal"></label>' +
      '<label class="diet-wide">Atividade<select id="diet-activity"><option value="baixa">Baixa · ×1,2</option><option value="moderada">Moderada · ×1,3</option><option value="intensa">Intensa · ×1,4</option></select></label></div>' +
      '<p>TMB estimada: <strong id="dietTmb">—</strong> kcal/dia <small>(Harris–Benedict)</small></p>' +
      '<label for="diet-goal">Meta (kcal/dia)</label><div class="diet-goal-row"><button type="button" id="dietGoalMinus">−100</button><input id="diet-goal" inputmode="decimal" placeholder="Automática"><button type="button" id="dietGoalPlus">+100</button><button type="button" id="dietGoalAuto">Auto</button></div>' +
      '<div class="diet-calc-grid"><label>Calorias do dia<input id="diet-calories" inputmode="decimal" placeholder="Automático"></label><label>Proteína (g)<input id="diet-protein" inputmode="decimal" placeholder="Do texto"></label><label>Carboidratos (g)<input id="diet-carbs" inputmode="decimal" placeholder="Do texto"></label><label>Gorduras (g)<input id="diet-fat" inputmode="decimal" placeholder="Do texto"></label></div><p class="diet-hint">Deixe os campos de meta e totais vazios para calcular automaticamente. Você pode corrigir os valores aqui.</p></details>' +
      '<div id="dietTotals" aria-live="polite"></div><label for="dietText">🧠 Cola inteligente</label>' +
      '<textarea id="dietText" placeholder="Cole a dieta completa aqui. As refeições serão organizadas automaticamente.\n\nCafé da manhã\n2 ovos\n1 fruta\n\nAlmoço\nArroz, feijão e frango"></textarea>' +
      '<details id="dietPreview"><summary>Refeições · editar</summary><div id="dietPreviewBody"></div></details>' +
      '<p id="dietStatus" role="status"></p><div class="dialog-actions"><button type="button" id="dietPdfBtn" class="primary">📄 PDF</button><button type="button" id="dietPhotoBtn">🖼 Baixar foto</button><button type="button" data-close>Fechar</button></div>' +
      '<div class="diet-history"><button type="button" id="dietUndoBtn" aria-label="Desfazer edição da dieta">↶</button><button type="button" id="dietRedoBtn" aria-label="Refazer edição da dieta">↷</button></div>');
    const text = dialog.querySelector('#dietText'), status = dialog.querySelector('#dietStatus');
    const preview = dialog.querySelector('#dietPreview'), body = dialog.querySelector('#dietPreviewBody');
    const pdfButton = dialog.querySelector('#dietPdfBtn'), photoButton = dialog.querySelector('#dietPhotoBtn');
    const undo = dialog.querySelector('#dietUndoBtn'), redo = dialog.querySelector('#dietRedoBtn');
    const inputs = Object.fromEntries(settingsKeys.map(key => [key,dialog.querySelector('#diet-'+key)]));
    let draftKey, settingsKey, name = '', timer, history = [], historyIndex = 0, lastGroup = '', lastTime = 0, busy = false;
    const inMemory = new Map();
    const settings = () => Object.fromEntries(settingsKeys.map(key => [key,inputs[key].value]));
    const state = () => ({text:text.value,settings:settings()});
    function save() {
      const value = state(); inMemory.set(draftKey,value);
      try {localStorage.setItem(draftKey,value.text);localStorage.setItem(settingsKey,JSON.stringify(value.settings));status.textContent='Rascunho salvo.';}
      catch(error) {status.textContent='Não foi possível guardar o rascunho neste navegador. O conteúdo continua disponível para exportar.';}
    }
    function buttons() {undo.disabled=historyIndex===0;redo.disabled=historyIndex>=history.length-1;pdfButton.disabled=photoButton.disabled=busy||!parse(text.value).length;}
    function record(group) {
      const snapshot=JSON.stringify(state());
      if(snapshot===history[historyIndex])return;
      const now=Date.now(),canGroup=group===lastGroup&&now-lastTime<450&&historyIndex===history.length-1&&historyIndex>0;
      history=history.slice(0,historyIndex+1);
      if(canGroup)history[historyIndex]=snapshot;else{history.push(snapshot);if(history.length>80)history.shift();historyIndex=history.length-1;}
      lastGroup=group;lastTime=now;buttons();
    }
    function totals() {
      const value=C().nutrition(parse(text.value),settings());
      dialog.querySelector('#dietTmb').textContent=fmt(value.tmb);
      inputs.goal.placeholder=value.goal===null?'Preencha os dados acima':fmt(value.goal);
      inputs.calories.placeholder=value.calories===null?'Não informado':String(value.calories);
      for(const key of ['protein','carbs','fat'])inputs[key].placeholder=value.macrosFound?fmt(value[key]):'Não informado';
      const summary=dialog.querySelector('#dietTotals');summary.replaceChildren();
      const main=document.createElement('strong');main.textContent='Dia: '+fmt(value.calories)+' kcal · Meta: '+fmt(value.goal)+' kcal';summary.append(main);
      const macros=document.createElement('div');macros.textContent='Proteína '+(value.macrosFound?fmt(value.protein):'—')+' g · Carbo '+(value.macrosFound?fmt(value.carbs):'—')+' g · Gordura '+(value.macrosFound?fmt(value.fat):'—')+' g';summary.append(macros);
      const source=document.createElement('small');source.textContent=value.source+(value.missing?' · '+value.missing+' refeição(ões) com contagem incompleta':'');summary.append(source);
      return value;
    }
    function nutrientLine(item) {return /^(?:macros?|carbo|prot|gord|total|calorias|kcal)\b/i.test(normalize(item));}
    function render() {
      body.replaceChildren();
      for(const section of parse(text.value)) {
        const block=document.createElement('section'),heading=document.createElement('h4');heading.textContent=section.title;heading.contentEditable='true';heading.setAttribute('aria-label','Nome da refeição');
        const list=document.createElement('ul');for(const item of section.items){const li=document.createElement('li');li.contentEditable='true';li.setAttribute('aria-label','Alimento ou informação da refeição');li.textContent=item;if(nutrientLine(item))li.className='diet-nutrition-line';list.append(li);}
        block.append(heading,list);body.append(block);
      }
    }
    function refresh(renderPreview=true) {totals();buttons();if(renderPreview&&preview.open)render();}
    function change(group,renderPreview=true) {save();record(group);totals();buttons();clearTimeout(timer);if(renderPreview&&preview.open)timer=setTimeout(render,160);}
    text.oninput=()=>change('text');
    for(const [key,input] of Object.entries(inputs))input.addEventListener(input.tagName==='SELECT'?'change':'input',()=>change(key,false));
    preview.ontoggle=()=>{if(preview.open)render();};
    body.addEventListener('input',()=>{text.value=[...body.children].map(block=>[block.querySelector('h4').innerText,...[...block.querySelectorAll('li')].map(li=>li.innerText)].join('\n')).join('\n\n');change('meals',false);});
    body.addEventListener('paste',event=>{event.preventDefault();document.execCommand('insertText',false,event.clipboardData.getData('text/plain'));});
    body.addEventListener('drop',event=>{event.preventDefault();});
    function move(direction) {
      const next=historyIndex+direction;if(next<0||next>=history.length)return;
      const active=document.activeElement,position=active?.selectionStart;historyIndex=next;lastGroup='';const snapshot=JSON.parse(history[next]);text.value=snapshot.text;for(const key of settingsKeys)inputs[key].value=snapshot.settings[key]||'';save();refresh();
      if(active===text){text.focus({preventScroll:true});text.setSelectionRange(Math.min(position||0,text.value.length),Math.min(position||0,text.value.length));}
    }
    for(const button of [undo,redo])button.onpointerdown=event=>event.preventDefault();
    undo.onclick=()=>move(-1);redo.onclick=()=>move(1);
    dialog.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&['z','y'].includes(event.key.toLowerCase())){event.preventDefault();event.stopPropagation();move(event.key.toLowerCase()==='y'||event.shiftKey?1:-1);}});
    dialog.querySelector('#dietExpandBtn').onclick=()=>{const expanded=dialog.classList.toggle('diet-expanded');dialog.querySelector('#dietExpandBtn').setAttribute('aria-pressed',String(expanded));dialog.querySelector('#dietExpandBtn').textContent=expanded?'↙ Minimizar':'⛶ Ampliar';};
    function adjustGoal(delta){const current=C().nutrition(parse(text.value),settings()).goal;if(current===null){status.textContent='Preencha os dados da TMB ou digite uma meta.';return;}inputs.goal.value=String(Math.max(0,current+delta));change('goal-step',false);}
    dialog.querySelector('#dietGoalMinus').onclick=()=>adjustGoal(-100);dialog.querySelector('#dietGoalPlus').onclick=()=>adjustGoal(100);dialog.querySelector('#dietGoalAuto').onclick=()=>{inputs.goal.value='';change('goal-auto',false);};
    dialog.addEventListener('close',()=>clearTimeout(timer));
    async function getPDF() {
      if(window.jspdf?.jsPDF)return window.jspdf.jsPDF;
      if(!pdfLibrary)pdfLibrary=(async()=>{for(const src of ['https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js','https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js']){try{await config.loadScript(src);if(window.jspdf?.jsPDF)return window.jspdf.jsPDF;}catch(error){}}throw Error('Não foi possível carregar a exportação. Confira sua conexão e tente novamente.');})().catch(error=>{pdfLibrary=null;throw error;});
      return pdfLibrary;
    }
    function report(doc,sections,metrics,pdfName,footer) {
      const pages=[[]];let y=20;
      const addPage=()=>{pages.push([]);y=20;};
      function lines(value,size,bold,color) {
        doc.setFont('helvetica',bold?'bold':'normal');doc.setFontSize(size);
        for(const line of doc.splitTextToSize(value,178)) {if(y>278)addPage();pages.at(-1).push({text:line,x:16,y,size,bold,color});y+=size*.43;}
      }
      lines(pdfName?'Dieta — '+pdfName:'Dieta',16,true,[30,111,63]);y+=2;lines(new Date().toLocaleDateString('pt-BR'),9,false,[100,110,120]);y+=5;
      if(metrics.tmb!==null)lines('TMB estimada: '+fmt(metrics.tmb)+' kcal/dia',10,false,[36,55,70]);
      if(metrics.goal!==null)lines('Meta: '+fmt(metrics.goal)+' kcal/dia',10,true,[30,111,63]);
      if(metrics.calories!==null)lines('Calorias do dia: '+fmt(metrics.calories)+' kcal ('+metrics.source+')',10,false,[36,55,70]);
      if(metrics.macrosFound)lines('Proteína: '+fmt(metrics.protein)+' g | Carbo: '+fmt(metrics.carbs)+' g | Gordura: '+fmt(metrics.fat)+' g',10,false,[36,55,70]);
      if(metrics.missing&&metrics.calories!==null)lines('Contagem parcial: '+metrics.missing+' refeição(ões) com contagem incompleta.',9,false,[100,110,120]);
      y+=5;
      for(const section of sections){if(y>260)addPage();lines(section.title,12,true,[30,111,63]);y+=2;for(const item of section.items)lines((nutrientLine(item)?'':'• ')+item,10.5,false,[36,55,70]);y+=5;}
      pages.forEach((commands,index)=>{commands.push({text:doc.splitTextToSize(footer,160)[0]||'',x:16,y:289,size:8,color:[115,125,135]},{text:(index+1)+'/'+pages.length,x:194,y:289,size:8,color:[115,125,135],align:'right'});});
      return pages;
    }
    function writePDF(doc,pages) {pages.forEach((commands,index)=>{if(index)doc.addPage();for(const command of commands){doc.setFont('helvetica',command.bold?'bold':'normal');doc.setFontSize(command.size);doc.setTextColor(...command.color);doc.text(command.text,command.x,command.y,{align:command.align||'left'});}});}
    async function photos(pages,safeName,exportKey) {
      // Bound image dimensions and memory; normal plans become a single tall PNG.
      const scale=1240/210,chunkSize=4;
      for(let start=0;start<pages.length;start+=chunkSize){
        if(!dialog.open||draftKey!==exportKey)return;
        const chunk=pages.slice(start,start+chunkSize).map(commands=>{const footerY=Math.min(289,Math.max(20,...commands.slice(0,-2).map(command=>command.y))+14);return {commands,footerY,height:Math.ceil((footerY+8)*scale)};});
        const canvas=document.createElement('canvas');canvas.width=1240;canvas.height=chunk.reduce((sum,page)=>sum+page.height,0);
        const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);
        let offset=0;for(const page of chunk){page.commands.forEach((command,index)=>{ctx.fillStyle='rgb('+command.color.join(',')+')';ctx.font=(command.bold?'bold ':'')+(command.size*25.4/72*scale)+'px Arial';ctx.textAlign=command.align||'left';ctx.fillText(command.text,command.x*scale,(index>=page.commands.length-2?page.footerY:command.y)*scale+offset);});offset+=page.height;}
        const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));canvas.width=canvas.height=1;
        if(!blob)throw Error('Não foi possível gerar a foto.');
        if(!dialog.open||draftKey!==exportKey)return;
        const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='Dieta_'+safeName+(pages.length>chunkSize?'_'+(Math.floor(start/chunkSize)+1):'')+'.png';link.hidden=true;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
      }
    }
    async function exportDiet(asPhoto) {
      const sections=parse(text.value);if(!sections.length){status.textContent='Cole a dieta antes de exportar.';return;}
      const pdfName=name,footer=config.footer(),exportKey=draftKey,metrics=C().nutrition(sections,settings());
      const viewer=asPhoto?null:TreinoPDFViewer.reserve();busy=true;buttons();status.textContent=asPhoto?'Gerando foto…':'Gerando PDF…';
      try {
        const jsPDF=await getPDF(),doc=new jsPDF({unit:'mm',format:'a4',compress:true}),pages=report(doc,sections,metrics,pdfName,footer);
        const safeName=(pdfName||'plano_alimentar').replace(/[\\/:*?"<>|]+/g,'_').replace(/\s+/g,'_').slice(0,80);
        if(asPhoto)await photos(pages,safeName,exportKey);else{writePDF(doc,pages);TreinoPDFViewer.deliver(doc,'Dieta_'+safeName+'.pdf',viewer);}
        if(draftKey===exportKey)status.textContent=asPhoto?'Foto gerada.':'PDF gerado.';
      }catch(error){TreinoPDFViewer.close(viewer);if(draftKey===exportKey)status.textContent=error.message;}
      finally{busy=false;buttons();}
    }
    pdfButton.onclick=()=>exportDiet(false);photoButton.onclick=()=>exportDiet(true);
    const button=document.createElement('button');button.type='button';button.id='dietBtn';button.textContent='🥗 Dieta';
    button.onclick=()=>{
      const student=config.student();name=config.name().trim();const id=encodeURIComponent(student?.student_id||name||'sem_aluno');draftKey='dieta36_rascunho_v1:'+id;settingsKey='dieta36_calculos_v1:'+id;status.textContent='';
      let saved=inMemory.get(draftKey)||{text:'',settings:{}};
      try{saved={...saved,text:localStorage.getItem(draftKey)??saved.text};saved.settings=JSON.parse(localStorage.getItem(settingsKey)||JSON.stringify(saved.settings));}catch(error){status.textContent='Não foi possível ler todos os ajustes do rascunho neste navegador.';}
      text.value=saved.text;const initial={...profile(student),...saved.settings};for(const key of settingsKeys)inputs[key].value=initial[key]??'';
      dialog.querySelector('#dietStudentName').textContent=name;preview.open=false;body.replaceChildren();history=[JSON.stringify(state())];historyIndex=0;lastGroup='';refresh(false);dialog.showModal();dialog.querySelector('#dietExpandBtn').focus({preventScroll:true});
    };
    return button;
  }
  return {mount,parse};
})();
