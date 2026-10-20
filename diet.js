/* A small paste-to-PDF editor using the pupil already selected in the workout. */
window.DietEditor = (() => {
  const plain = text => text.replace(/\*\*|__|`/g, '').replace(/\p{Extended_Pictographic}|[\uFE0F\u200D]/gu, '').replace(/^\s*#{1,6}\s*/, '').trim();
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const meals = /^(?:cafe da manha|cafe|desjejum|lanche da manha|almoco|lanche da tarde|jantar|ceia|pre[- ]?treino|pos[- ]?treino|lanche(?:\s+\d+)?|refeicao\s*\d+|orientacoes(?: gerais)?|observacoes|recomendacoes|resumo(?: diario)?|total(?: diario| do dia| geral)|totais(?: do dia)?)(?=$|\s*[:(–—-]|\s+\d)/;
  const daily = /^(?:resumo(?: diario)?|total(?: diario| do dia| geral)|totais(?: do dia)?)(?:\s+aproximad[oa]s?)?(?=$|\s*[:(–—-])/;
  const visibleSections = sections => sections.filter(section=>!section.summary);
  function parse(text) {
    const sections = [];
    let current;
    function locate(section,index){Object.defineProperties(section,{startLine:{value:index,writable:true},endLine:{value:index+1,writable:true}});return section;}
    for (const [index,raw] of text.split(/\r?\n/).entries()) {
      const line = plain(raw).replace(/^\s*(?:[-*•▪]+\s*|\d+\)\s*|\d+\.\s+)/, '').trim();
      if (!line || /^[\s\p{P}\p{S}]+$/u.test(line)) continue;
      const normalized=normalize(line);
      if(/^os valores podem variar\b/.test(normalized))continue;
      if(!current&&(/^(?:cardapio\b|dieta\b|plano alimentar\b)/.test(normalized)||/^pesar\b/.test(normalized)))continue;
      const candidate = line.replace(/^\d{1,2}(?::\d{2}|h\d{0,2})\s*[-–—:]?\s*/i, '');
      const summary=normalize(candidate).match(daily);
      const match = summary||normalize(candidate).match(meals);
      if (match) {
        // An inline meal ("Almoço: arroz...") retains the food after the colon.
        const tail = candidate.slice(match[0].length);
        const inline = tail.match(/^\s*:\s*(.+)$/);
        const colon = inline && !/^\d{1,2}(?::\d{2}|h\d{0,2})(?:\s*(?:h|horas?))?$/i.test(inline[1]) ? inline : null;
        const prefix = line.slice(0, line.length - candidate.length);
        current = locate({title: colon ? prefix + candidate.slice(0, match[0].length) : line, items: []},index);
        if(summary)current.summary=true;
        sections.push(current);
        if (colon) current.items.push(colon[1]);
      } else {
        if (!current) { current = locate({title: 'Plano alimentar', items: []},index); sections.push(current); }
        current.items.push(line);
        current.endLine=index+1;
      }
    }
    return sections;
  }
  let pdfLibrary;
  const C = () => window.DietCalculations;
  const settingsKeys = ['goal','calories','protein','carbs','fat'];
  const fmt = value => value === null ? '—' : Number(value.toFixed(1)).toLocaleString('pt-BR');
  function profile(student, config) {
    let current=student,person={},av={};
    if(student&&window.AvaliacaoTreinoSync){try{const sync=AvaliacaoTreinoSync;current=sync.read('treinoAlunos').find(s=>s.student_id===student.student_id)||student;person=sync.resolve(sync.read(sync.key),current)||{};av=person.avaliacoes?.find(a=>a.id===person.avaliacaoPreferidaId)||person.avaliacoes?.at(-1)||{};}catch(error){}}
    const ficha=(current?.infoGuias||[]).find(g=>g.id===current.avaliacaoFichaId)||current?.infoGuias?.at(-1)||current?.infoRelevante||{};
    const weight=ficha.peso||av.peso||person.pesoAtual||'',height=ficha.altura||av.ficha?.altura||person.altura||'',age=ficha.idade||av.ficha?.idade||person.idade||'';
    const calc=config.obsCalories(weight,height,age,ficha.nivelTreino||'moderado');
    return {weight:C().number(weight),tmb:calc?.tmb??C().number(av.tmb),daily:calc?.gastoTotal??null,deficit:calc?.deficit??null,surplus:calc?.superavit??null};
  }
  function mount(config) {
    const dialog = config.createDialog('dietDialog', '🥗 Dieta',
      '<button type="button" id="dietExpandBtn" aria-pressed="false">⛶ Ampliar</button><p id="dietStudentName"></p>' +
      '<details id="dietCalculations"><summary>Meta e calorias</summary><p>TMB da OBS: <strong id="dietTmb">—</strong> kcal/dia</p><p class="diet-hint" id="dietObsStatus"></p><div class="diet-quick-goals">' +
      '<button type="button" data-diet-goal="tmb">TMB</button><button type="button" data-diet-goal="daily">Manutenção</button><button type="button" data-diet-goal="deficit">Emagrecimento</button><button type="button" data-diet-goal="surplus">Hipertrofia</button></div>' +
      '<label for="diet-goal">Meta (kcal/dia)</label><div class="diet-goal-row"><button type="button" id="dietGoalMinus">−100</button><input id="diet-goal" inputmode="decimal" placeholder="Automática"><button type="button" id="dietGoalPlus">+100</button><button type="button" id="dietGoalAuto">Auto</button></div>' +
      '<div class="diet-calc-grid"><label>Calorias do dia<input id="diet-calories" inputmode="decimal" placeholder="Automático"></label><label>Proteína (g)<input id="diet-protein" inputmode="decimal" placeholder="Do texto"></label><label>Carboidratos (g)<input id="diet-carbs" inputmode="decimal" placeholder="Do texto"></label><label>Gorduras (g)<input id="diet-fat" inputmode="decimal" placeholder="Do texto"></label></div>' + DietTools.markup() + '<p class="diet-hint">Os valores da OBS são atualizados automaticamente. Deixe a meta vazia para usar a opção selecionada acima; os totais podem vir do texto ou ser corrigidos aqui.</p></details>' +
      '<div id="dietTotals" aria-live="polite"></div><div class="diet-paste-header"><label for="dietText">🧠 Cola inteligente</label><div><button type="button" id="dietPasteClearBtn">Limpar texto</button><button type="button" id="dietPasteExpandBtn" aria-pressed="false">⛶ Ampliar</button></div></div>' +
      '<textarea id="dietText" placeholder="Cole a dieta completa aqui. As refeições serão organizadas automaticamente.\n\nCafé da manhã\n2 ovos\n1 fruta\n\nAlmoço\nArroz, feijão e frango"></textarea>' +
      '<details id="dietPreview"><summary><span>Refeições · editar</span><button type="button" id="dietMealsExpandBtn" aria-pressed="false">⛶ Ampliar</button></summary><div id="dietPreviewBody"></div></details>' +
      '<label class="diet-export-switch"><input type="checkbox" role="switch" id="dietIncludeCalculations"> Incluir TMB e calorias no PDF/foto</label><p id="dietStatus" role="status"></p><div class="dialog-actions"><button type="button" id="dietPdfBtn" class="primary">📄 PDF</button><button type="button" id="dietPhotoBtn">🖼 Ver foto</button><button type="button" data-close>Fechar</button></div>' +
      '<div class="diet-history"><button type="button" id="dietUndoBtn" aria-label="Desfazer edição da dieta">↶</button><button type="button" id="dietRedoBtn" aria-label="Refazer edição da dieta">↷</button></div>');
    const photoViewer=DietPhotoViewer.mount(config.createDialog);
    const text = dialog.querySelector('#dietText'), status = dialog.querySelector('#dietStatus');
    const preview = dialog.querySelector('#dietPreview'), body = dialog.querySelector('#dietPreviewBody');
    const pdfButton = dialog.querySelector('#dietPdfBtn'), photoButton = dialog.querySelector('#dietPhotoBtn');
    const undo = dialog.querySelector('#dietUndoBtn'), redo = dialog.querySelector('#dietRedoBtn');
    const inputs = Object.fromEntries(settingsKeys.map(key => [key,dialog.querySelector('#diet-'+key)]));
    let draftKey, settingsKey, name = '', timer, history = [], historyIndex = 0, lastGroup = '', lastTime = 0, busy = false, studentForDiet=null, goalMode='daily', macroAuto=false, source={tmb:null,daily:null,deficit:null,surplus:null};
    const inMemory = new Map();
    const includeCalculations=dialog.querySelector('#dietIncludeCalculations');
    const settings = () => ({...Object.fromEntries(settingsKeys.map(key => [key,inputs[key].value])),includeCalculations:includeCalculations.checked,goalMode,macroAuto});
    const calculationSettings=()=>({...settings(),obsTmb:source.tmb??'',obsGoal:source[goalMode]??''});
    const state = () => ({text:text.value,settings:settings()});
    function save() {
      const value = state(); inMemory.set(draftKey,value);
      try {localStorage.setItem(draftKey,value.text);localStorage.setItem(settingsKey,JSON.stringify(value.settings));status.textContent='Rascunho salvo.';}
      catch(error) {status.textContent='Não foi possível guardar o rascunho neste navegador. O conteúdo continua disponível para exportar.';}
    }
    function buttons() {undo.disabled=historyIndex===0;redo.disabled=historyIndex>=history.length-1;dialog.querySelector('#dietPasteClearBtn').disabled=!text.value.length;pdfButton.disabled=photoButton.disabled=busy||!visibleSections(parse(text.value)).some(section=>section.items.length);}
    function record(group) {
      const snapshot=JSON.stringify(state());
      if(snapshot===history[historyIndex])return;
      const now=Date.now(),canGroup=group===lastGroup&&now-lastTime<450&&historyIndex===history.length-1&&historyIndex>0;
      history=history.slice(0,historyIndex+1);
      if(canGroup)history[historyIndex]=snapshot;else{history.push(snapshot);if(history.length>80)history.shift();historyIndex=history.length-1;}
      lastGroup=group;lastTime=now;buttons();
    }
    const macroNotice=dialog.querySelector('#dietMacroNotice');
    function deriveMacros(strict=false){
      try{
        const result=C().objectiveMacros(source.weight,goalMode,inputs.goal.value.trim()?inputs.goal.value:source.daily);
        for(const field of ['calories','protein','carbs','fat'])inputs[field].value=String(result[field]);
        macroNotice.textContent=fmt(result.weight)+' kg · Proteína × 2 · '+(goalMode==='daily'?'Carbo completa a meta de calorias':'Carbo × '+fmt(result.carbRatio))+' · Gordura × 0,8 = '+fmt(result.calories)+' kcal.';
        return result;
      }catch(error){macroNotice.textContent=error.message+' Os campos anteriores foram mantidos.';if(strict)throw error;return null;}
    }
    const tools=DietTools.mount(dialog,{
      values:()=>{const value=totals();return {calories:value.calories,protein:value.macrosFound?value.protein:null,carbs:value.macrosFound?value.carbs:null,fat:value.macrosFound?value.fat:null};},
      clear:keys=>{macroAuto=false;macroNotice.textContent='';for(const key of keys)inputs[key].value='';change('clear-values',false);},
      message:value=>{status.textContent=value;}
    });
    function totals() {
      const value=C().nutrition(parse(text.value),calculationSettings());
      dialog.querySelector('#dietTmb').textContent=fmt(value.tmb);
      dialog.querySelector('#dietObsStatus').textContent=value.tmb===null?'Preencha a ficha nas OBS para obter a TMB.':'Atualizada automaticamente pela ficha/OBS.';
      const labels={tmb:'TMB',daily:'Manutenção',deficit:'Emagrecimento',surplus:'Hipertrofia'};
      dialog.querySelectorAll('[data-diet-goal]').forEach(button=>{const mode=button.dataset.dietGoal;button.disabled=mode==='tmb'&&source[mode]===null;button.textContent=labels[mode]+' · '+fmt(source[mode])+' kcal';button.setAttribute('aria-pressed',String(goalMode===mode&&!inputs.goal.value.trim()));});
      inputs.goal.placeholder=value.goal===null?'Preencha os dados acima':fmt(value.goal);
      inputs.calories.placeholder=value.calories===null?'Não informado':String(value.calories);
      for(const key of ['protein','carbs','fat'])inputs[key].placeholder=value.macrosFound?fmt(value[key]):'Não informado';
      const summary=dialog.querySelector('#dietTotals');summary.replaceChildren();
      const main=document.createElement('strong');main.textContent='Dia: '+fmt(value.calories)+' kcal · Meta: '+fmt(value.goal)+' kcal';summary.append(main);
      const macros=document.createElement('div');macros.textContent='Proteína '+(value.macrosFound?fmt(value.protein):'—')+' g · Carbo '+(value.macrosFound?fmt(value.carbs):'—')+' g · Gordura '+(value.macrosFound?fmt(value.fat):'—')+' g';summary.append(macros);
      const sourceLabel=document.createElement('small');sourceLabel.textContent=value.source+(value.missing?' · '+value.missing+' refeição(ões) com contagem incompleta':'');summary.append(sourceLabel);
      return value;
    }
    function nutrientLine(item) {return /^(?:macros?|carbo|prot|gord|total|calorias|kcal)\b/i.test(normalize(item));}
    let renderedSections=[];
    function render() {
      body.replaceChildren();
      renderedSections=parse(text.value);renderedSections.forEach((section,index)=>{if(section.summary)return;
        const block=document.createElement('section'),heading=document.createElement('h4');heading.textContent=section.title;heading.contentEditable='true';heading.setAttribute('aria-label','Nome da refeição');
        block.dataset.sectionIndex=index;
        const list=document.createElement('ul');for(const item of section.items){const li=document.createElement('li');li.contentEditable='true';li.setAttribute('aria-label','Alimento ou informação da refeição');li.textContent=item;if(nutrientLine(item))li.className='diet-nutrition-line';list.append(li);}
        block.append(heading,list);body.append(block);
      });
    }
    function refresh(renderPreview=true) {totals();buttons();if(renderPreview&&preview.open)render();}
    function change(group,renderPreview=true) {if(macroAuto)deriveMacros();save();record(group);totals();buttons();clearTimeout(timer);if(renderPreview&&preview.open)timer=setTimeout(render,160);}
    text.oninput=()=>change('text');
    dialog.querySelector('#dietPasteClearBtn').onclick=()=>{if(!text.value.length||!confirm('Limpar o texto da cola inteligente? Você poderá desfazer.'))return;text.value='';change('clear-text');refresh();};
    includeCalculations.onchange=()=>change('export-option',false);
    for(const [key,input] of Object.entries(inputs))input.addEventListener(input.tagName==='SELECT'?'change':'input',()=>{if(['calories','protein','carbs','fat'].includes(key)){macroAuto=false;macroNotice.textContent='';}change(key,false);});
    preview.ontoggle=()=>{if(preview.open)render();};
    body.addEventListener('input',()=>{const raw=text.value.split(/\r?\n/),blocks=new Map([...body.children].map(block=>[Number(block.dataset.sectionIndex),block])),output=[];let cursor=0;renderedSections.forEach((section,index)=>{const start=section.startLine,end=section.endLine;output.push(...raw.slice(cursor,start));section.startLine=output.length;const block=blocks.get(index);if(block){section.title=block.querySelector('h4').innerText;section.items=[...block.querySelectorAll('li')].map(li=>li.innerText);output.push(section.title,...section.items);}else output.push(...raw.slice(start,end));section.endLine=output.length;cursor=end;});output.push(...raw.slice(cursor));text.value=output.join('\n');change('meals',false);});
    body.addEventListener('paste',event=>{event.preventDefault();document.execCommand('insertText',false,event.clipboardData.getData('text/plain'));});
    body.addEventListener('drop',event=>{event.preventDefault();});
    function move(direction) {
      const next=historyIndex+direction;if(next<0||next>=history.length)return;
      const active=document.activeElement,position=active?.selectionStart;historyIndex=next;lastGroup='';const snapshot=JSON.parse(history[next]);text.value=snapshot.text;for(const key of settingsKeys)inputs[key].value=snapshot.settings[key]||'';includeCalculations.checked=snapshot.settings.includeCalculations===true;goalMode=snapshot.settings.goalMode||'daily';macroAuto=snapshot.settings.macroAuto===true;macroNotice.textContent='';save();refresh();
      if(active===text){text.focus({preventScroll:true});text.setSelectionRange(Math.min(position||0,text.value.length),Math.min(position||0,text.value.length));}
    }
    for(const button of [undo,redo])button.onpointerdown=event=>event.preventDefault();
    undo.onclick=()=>move(-1);redo.onclick=()=>move(1);
    dialog.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&['z','y'].includes(event.key.toLowerCase())){event.preventDefault();event.stopPropagation();move(event.key.toLowerCase()==='y'||event.shiftKey?1:-1);}});
    dialog.querySelector('#dietExpandBtn').onclick=()=>{const expanded=dialog.classList.toggle('diet-expanded');dialog.querySelector('#dietExpandBtn').setAttribute('aria-pressed',String(expanded));dialog.querySelector('#dietExpandBtn').textContent=expanded?'↙ Minimizar':'⛶ Ampliar';};
    function adjustGoal(delta){const current=C().nutrition(parse(text.value),calculationSettings()).goal;if(current===null){status.textContent='Preencha os dados da TMB ou digite uma meta.';return;}inputs.goal.value=String(Math.max(0,current+delta));change('goal-step',false);}
    dialog.querySelectorAll('[data-diet-goal]').forEach(button=>{button.onclick=()=>{goalMode=button.dataset.dietGoal;inputs.goal.value='';macroAuto=goalMode!=='tmb';macroNotice.textContent='';change('goal-preset',false);};});
    dialog.querySelector('#dietGoalMinus').onclick=()=>adjustGoal(-100);dialog.querySelector('#dietGoalPlus').onclick=()=>adjustGoal(100);dialog.querySelector('#dietGoalAuto').onclick=()=>{inputs.goal.value='';change('goal-auto',false);};
    const pasteExpand=dialog.querySelector('#dietPasteExpandBtn'),mealsExpand=dialog.querySelector('#dietMealsExpandBtn');let pasteScroll=0,mealsScroll=0;
    function expandMeals(expanded){
      if(expanded){mealsScroll=dialog.scrollTop;if(!preview.open)preview.open=true;}
      dialog.classList.toggle('diet-meals-expanded',expanded);mealsExpand.setAttribute('aria-pressed',String(expanded));mealsExpand.textContent=expanded?'↙ Minimizar':'⛶ Ampliar';dialog.scrollTop=expanded?0:mealsScroll;
    }
    mealsExpand.onpointerdown=event=>{if(body.contains(document.activeElement))event.preventDefault();};
    mealsExpand.onclick=event=>{event.preventDefault();event.stopPropagation();expandMeals(!dialog.classList.contains('diet-meals-expanded'));};
    preview.addEventListener('toggle',()=>{if(!preview.open&&dialog.classList.contains('diet-meals-expanded'))expandMeals(false);});
    function expandPaste(expanded){
      if(expanded)pasteScroll=dialog.scrollTop;
      dialog.classList.toggle('diet-paste-expanded',expanded);pasteExpand.setAttribute('aria-pressed',String(expanded));pasteExpand.textContent=expanded?'↙ Minimizar':'⛶ Ampliar';dialog.scrollTop=expanded?0:pasteScroll;
    }
    pasteExpand.onpointerdown=event=>{if(document.activeElement===text)event.preventDefault();};
    pasteExpand.onclick=()=>expandPaste(!dialog.classList.contains('diet-paste-expanded'));
    dialog.addEventListener('cancel',event=>{if(dialog.classList.contains('diet-paste-expanded')){event.preventDefault();expandPaste(false);}else if(dialog.classList.contains('diet-meals-expanded')){event.preventDefault();expandMeals(false);}});
    dialog.addEventListener('close',()=>{clearTimeout(timer);expandPaste(false);expandMeals(false);photoViewer.close();});
    async function getPDF() {
      if(window.jspdf?.jsPDF)return window.jspdf.jsPDF;
      if(!pdfLibrary)pdfLibrary=(async()=>{for(const src of ['https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js','https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js']){try{await config.loadScript(src);if(window.jspdf?.jsPDF)return window.jspdf.jsPDF;}catch(error){}}throw Error('Não foi possível carregar a exportação. Confira sua conexão e tente novamente.');})().catch(error=>{pdfLibrary=null;throw error;});
      return pdfLibrary;
    }
    function report(doc,sections,metrics,pdfName,withCalculations,asPhoto=false) {
      const left=asPhoto?8:16,lineWidth=asPhoto?94:178,bottom=asPhoto?172:278,startY=asPhoto?12:20;
      const pages=[[]];let y=startY;
      const addPage=()=>{pages.push([]);y=startY;};
      function lines(value,size,bold,color) {
        doc.setFont('helvetica',bold?'bold':'normal');doc.setFontSize(size);
        for(const line of doc.splitTextToSize(value,lineWidth)) {if(y>bottom)addPage();pages.at(-1).push({text:line,x:left,y,size,bold,color});y+=size*.43;}
      }
      lines(pdfName?'Dieta — '+pdfName:'Dieta',16,true,[30,111,63]);y+=2;lines(new Date().toLocaleDateString('pt-BR'),9,false,[100,110,120]);y+=5;
      if(withCalculations){
      if(metrics.tmb!==null)lines('TMB estimada: '+fmt(metrics.tmb)+' kcal/dia',10,false,[36,55,70]);
      if(metrics.calories!==null)lines('Calorias do dia: '+fmt(metrics.calories)+' kcal ('+metrics.source+')',10,false,[36,55,70]);
      if(metrics.missing&&metrics.calories!==null)lines('Contagem parcial: '+metrics.missing+' refeição(ões) com contagem incompleta.',9,false,[100,110,120]);
      }
      if(metrics.goal!==null)lines('Meta: '+fmt(metrics.goal)+' kcal/dia',10,true,[30,111,63]);
      if(metrics.macrosFound)lines('Proteína: '+fmt(metrics.protein)+' g | Carbo: '+fmt(metrics.carbs)+' g | Gordura: '+fmt(metrics.fat)+' g',10,false,[36,55,70]);
      y+=5;
      for(const section of sections){if(y>(asPhoto?154:260))addPage();lines(section.title,12,true,[30,111,63]);y+=2;for(const item of section.items)lines((nutrientLine(item)?'':'• ')+item,10.5,false,[36,55,70]);y+=5;}
      if(!asPhoto)pages.forEach((commands,index)=>{commands.push({text:(index+1)+'/'+pages.length,x:194,y:289,size:8,color:[115,125,135],align:'right'});});
      return pages;
    }
    function writePDF(doc,pages) {pages.forEach((commands,index)=>{if(index)doc.addPage();for(const command of commands){doc.setFont('helvetica',command.bold?'bold':'normal');doc.setFontSize(command.size);doc.setTextColor(...command.color);doc.text(command.text,command.x,command.y,{align:command.align||'left'});}});}
    async function photos(pages,safeName,exportKey,photoSession) {
      // Bound image dimensions and memory; normal plans become a single tall PNG.
      const scale=1240/110,chunkSize=3;
      for(let start=0;start<pages.length;start+=chunkSize){
        if(!dialog.open||draftKey!==exportKey||photoSession.closed)return;
        // Join content baselines, without carrying PDF page margins into the image.
        let last=null;
        const commands=pages.slice(start,start+chunkSize).flatMap(page=>{
          const first=page[0],shift=last&&first?last.y+last.size*.43+(first.bold&&first.size===12?5:0)-first.y:0;
          const joined=page.map(command=>({...command,y:command.y+shift}));last=joined.at(-1)||last;return joined;
        });
        const canvas=document.createElement('canvas');canvas.width=1240;canvas.height=Math.ceil(((last?.y||12)+8)*scale);
        const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);
        for(const command of commands){ctx.fillStyle='rgb('+command.color.join(',')+')';ctx.font=(command.bold?'bold ':'')+(command.size*25.4/72*scale)+'px Arial';ctx.textAlign=command.align||'left';ctx.fillText(command.text,command.x*scale,command.y*scale);}
        const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));canvas.width=canvas.height=1;
        if(!blob)throw Error('Não foi possível gerar a foto.');
        if(!dialog.open||draftKey!==exportKey||photoSession.closed)return;
        photoSession.add(blob,'Dieta_'+safeName+(pages.length>chunkSize?'_'+(Math.floor(start/chunkSize)+1):'')+'.png');
      }
    }
    async function exportDiet(asPhoto) {
      const parsed=parse(text.value),sections=visibleSections(parsed);if(!sections.some(section=>section.items.length)){status.textContent='Cole a dieta antes de exportar.';return;}
      const pdfName=name,exportKey=draftKey,metrics=C().nutrition(parsed,calculationSettings()),withCalculations=includeCalculations.checked;
      const photoSession=asPhoto?photoViewer.open(pdfName):null;
      const viewer=asPhoto?null:TreinoPDFViewer.reserve();busy=true;buttons();status.textContent=asPhoto?'Gerando foto…':'Gerando PDF…';
      try {
        const jsPDF=await getPDF(),doc=new jsPDF({unit:'mm',format:'a4',compress:true}),pages=report(doc,sections,metrics,pdfName,withCalculations,asPhoto);
        const safeName=(pdfName||'plano_alimentar').replace(/[\\/:*?"<>|]+/g,'_').replace(/\s+/g,'_').slice(0,80);
        if(asPhoto){await photos(pages,safeName,exportKey,photoSession);photoSession.ready();}else{writePDF(doc,pages);TreinoPDFViewer.deliver(doc,'Dieta_'+safeName+'.pdf',viewer);}
        if(draftKey===exportKey)status.textContent=asPhoto?'Prévia da foto gerada.':'PDF gerado.';
      }catch(error){TreinoPDFViewer.close(viewer);if(photoSession)photoSession.error(error.message);if(draftKey===exportKey)status.textContent=error.message;}
      finally{busy=false;buttons();}
    }
    pdfButton.onclick=()=>exportDiet(false);photoButton.onclick=()=>exportDiet(true);
    const button=document.createElement('button');button.type='button';button.id='dietBtn';button.textContent='🥗 Dieta';
    button.onclick=()=>{
      const student=config.student();studentForDiet=student;name=config.name().trim();const id=encodeURIComponent(student?.student_id||name||'sem_aluno');draftKey='dieta36_rascunho_v1:'+id;settingsKey='dieta36_calculos_v1:'+id;status.textContent='';
      let saved=inMemory.get(draftKey)||{text:'',settings:{}};
      try{saved={...saved,text:localStorage.getItem(draftKey)??saved.text};saved.settings=JSON.parse(localStorage.getItem(settingsKey)||JSON.stringify(saved.settings));}catch(error){status.textContent='Não foi possível ler todos os ajustes do rascunho neste navegador.';}
      text.value=saved.text;source=profile(student,config);macroAuto=saved.settings?.macroAuto===true;macroNotice.textContent='';tools.reset();goalMode=['tmb','daily','deficit','surplus'].includes(saved.settings?.goalMode)?saved.settings.goalMode:'daily';const initial={...saved.settings};for(const key of settingsKeys)inputs[key].value=initial[key]??'';includeCalculations.checked=saved.settings?.includeCalculations===true;if(macroAuto){deriveMacros();save();}
      dialog.querySelector('#dietStudentName').textContent=name;preview.open=false;body.replaceChildren();history=[JSON.stringify(state())];historyIndex=0;lastGroup='';refresh(false);dialog.showModal();dialog.querySelector('#dietExpandBtn').focus({preventScroll:true});
    };
    function refreshSource(){if(dialog.open){source=profile(studentForDiet,config);if(macroAuto){deriveMacros();save();record('macro-obs');}totals();}}
    window.addEventListener('focus',refreshSource);window.addEventListener('storage',event=>{if(['treinoAlunos','avaliacao_fisica_alunos','treino36_assessment_drafts','treino36_obs_drafts'].includes(event.key))refreshSource();});
    return button;
  }
  return {mount,parse};
})();
