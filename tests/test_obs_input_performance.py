from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':390,'height':844})
    stalled=[]
    def route(request):
        url=urlparse(request.request.url)
        if url.hostname=='i.postimg.cc':
            stalled.append(request) # Never finish the logo request.
            return
        path=ROOT/url.path.strip('/')
        if path.is_dir():path/='index.html'
        if url.hostname=='app.test' and path.is_file():
            request.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
        else:request.fulfill(status=404,body='')
    context.route('**/*',route)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://app.test/treino36/',wait_until='domcontentloaded')
    page.evaluate('''() => {
      const records=Array.from({length:21},(_,i)=>({id:i+1,nome:'Aluno '+i,sexo:'F',altura:'1.60',idade:'30',treinoStudentIds:['s'+i],avaliacoes:[{id:100+i,data:'01/10/2026',peso:'60',protocolo:'jp7',resumo:'Histórico '.repeat(2000)}]}));
      localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify(records));
      localStorage.setItem('treinoAlunos',JSON.stringify(records.map((a,i)=>({student_id:'s'+i,nome:a.nome,avaliacaoId:a.id,treino:{A:['Agachamento 3x10']},historicoTreinos:Array.from({length:30},(_,j)=>({treino_id:'v'+i+j,treino:{A:['Supino '.repeat(100)]}}))}))));
    }''')
    page.reload(wait_until='domcontentloaded');page.locator('#searchName').fill('Aluno 0');page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('[data-assessment-section="composicao"]').click()
    expect(page.locator('#obs-av-peso')).to_have_value('60',timeout=5000)
    assert stalled,'Expected stalled engine logo request'
    page.evaluate('''() => {
      window.assessmentWrites=0;window.assessmentSyncs=0;
      const set=Storage.prototype.setItem,sync=AvaliacaoTreinoSync.syncTraining;
      Storage.prototype.setItem=function(k,v){if(this===localStorage&&k==='avaliacao_fisica_alunos')assessmentWrites++;return set.call(this,k,v);};
      AvaliacaoTreinoSync.syncTraining=function(records){assessmentSyncs++;return sync(records);};
      const input=document.getElementById('obs-av-peso');input.focus();
      for(const value of ['7','72','72,','72,5']){input.value=value;input.dispatchEvent(new Event('input',{bubbles:true}));}
    }''')
    assert page.evaluate('[assessmentWrites,assessmentSyncs]')==[0,0]
    expect(page.locator('#obs-av-imc')).to_have_value('28.3')
    # Another tab's unrelated edit must survive the delayed save.
    other=context.new_page();other.goto('http://app.test/treino36/avaliacao.html?embed=treino36-engine',wait_until='domcontentloaded')
    other.evaluate('''() => {const records=AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key);records[0].email='novo@example.com';records[1].avaliacoes[0].cintura='85';localStorage.setItem(AvaliacaoTreinoSync.key,JSON.stringify(records));}''')
    page.locator('#obs-av-peso').press('Tab')
    expect(page.locator('.obs-assessment-status')).to_have_text('Salvo automaticamente nesta avaliação.')
    state=page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)")
    assert state[0]['avaliacoes'][0]['peso']=='72,5' and state[0]['email']=='novo@example.com'
    assert state[1]['avaliacoes'][0]['cintura']=='85'
    # Closing the modal via script, before blur or debounce, must also save.
    page.evaluate('''() => {const input=document.getElementById('obs-av-peso');input.focus();input.value='73';input.dispatchEvent(new Event('input',{bubbles:true}));document.getElementById('workoutObsDialog').close();}''')
    expect(page.locator('#workoutObsDialog')).not_to_be_visible()
    assert page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[0].avaliacoes[0].peso")=='73'
    library=context.new_page()
    library.add_init_script("""(() => {window.libraryWrites=0;const set=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(this===localStorage&&/^(treino|avaliacao)/.test(k))libraryWrites++;return set.call(this,k,v);};})()""")
    library.goto('http://app.test/treino36/avaliacao.html?embed=treino36-library',wait_until='domcontentloaded')
    assert library.evaluate('libraryWrites')==0,'Loading the library must not rewrite assessments or training'
    library.locator('[data-aluno-card="1"] .aluno-nome').click()
    library.evaluate("""() => {window.librarySyncs=0;const sync=AvaliacaoTreinoSync.syncTraining;AvaliacaoTreinoSync.syncTraining=function(records){librarySyncs++;return sync(records);};libraryWrites=0;syncAvaliacao(1,100,'peso','74');}""")
    library.wait_for_timeout(600)
    assert library.evaluate('[libraryWrites,librarySyncs]')[1]==1,'A library edit must synchronize only once'
    assert library.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[0].avaliacoes[0].peso")=='74'
    library.evaluate("""() => {window.searchRenders=0;const render=filtrarAlunos;window.filtrarAlunos=()=>{searchRenders++;render();};const input=document.getElementById('buscaAluno');for(const value of ['A','Al','Aluno']){input.value=value;input.dispatchEvent(new Event('input',{bubbles:true}));}}""")
    library.wait_for_function('searchRenders===1')
    library.wait_for_timeout(250)
    assert library.evaluate('searchRenders')==1,'Rapid search input must render once'
    assert not errors,errors
    for request in stalled: request.abort()
    browser.close();print('PASS: fields ready despite stalled remote logo; live calculation without per-key saves/syncs; concurrent edits preserved; close flushes pending weight')
