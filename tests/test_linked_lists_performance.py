from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':390,'height':844})
    def route(request):
        url=urlparse(request.request.url)
        path=ROOT/url.path.strip('/')
        if path.is_dir(): path/='index.html'
        if url.hostname=='app.test' and path.is_file():
            request.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
        else: request.fulfill(status=404,body='')
    context.route('**/*',route)
    page=context.new_page()
    page.goto('http://app.test/treino36/')
    page.evaluate('''() => {
      const students=[{student_id:'a',nome:'Ana treino 1'},{student_id:'b',nome:'Ana treino 2'},{student_id:'c',nome:'Ana Silva'}];
      students.forEach(s=>{s.treino={A:['Agachamento 3x10']};s.observacoes='Orientações '.repeat(8000);s.historicoTreinos=Array.from({length:50},(_,i)=>({treino:{A:['Supino '.repeat(100)]},created_at:'2026-01-01',treino_id:s.student_id+i}));});
      localStorage.setItem('treinoAlunos',JSON.stringify(students));
      localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:1,nome:'Ana Silva',sexo:'F',treinoStudentIds:['a','b'],avaliacoes:[{id:11,peso:'60',data:'01/10/2026'}]},{id:2,nome:'Sem treino',avaliacoes:[]}]));
    }''')
    page.reload()
    page.locator('#listBtn').click()
    expect(page.locator('.training-assessment-link',has_text='🔗 Avaliação: Ana Silva')).to_have_count(2)
    expect(page.locator('.training-assessment-link',has_text='Sem vínculo')).to_have_count(1)
    page.locator('#closeModalBtn').click()
    page.locator('#searchName').fill('Ana treino 1')
    page.locator('#obsIconBtn').click()
    expect(page.locator('#obsTextarea')).to_have_value('Orientações '*8000)
    page.evaluate("document.getElementById('workoutObsDialog').close()")
    assessment=context.new_page()
    assessment.goto('http://app.test/treino36/avaliacao.html?embed=treino36-library')
    expect(assessment.locator('[data-aluno-card="1"] .assessment-training-link')).to_have_text('🔗 Treino: Ana treino 1 · Ana treino 2')
    expect(assessment.locator('[data-aluno-card="2"] .assessment-training-link')).to_have_text('Sem vínculo com treino')
    assessment.locator('[data-aluno-card="1"] .aluno-header').click()
    assessment.locator('[data-aluno-card="1"] [data-section="cadastro"]').click()
    results=assessment.evaluate('''() => {
      const before=localStorage.getItem('avaliacao_fisica_alunos'),training=localStorage.getItem('treinoAlunos');
      let writes=0,syncs=0;const original=Storage.prototype.setItem,oldSync=AvaliacaoTreinoSync.syncTraining;
      Storage.prototype.setItem=function(k,v){if(this===localStorage)writes++;return original.call(this,k,v);};
      AvaliacaoTreinoSync.syncTraining=()=>syncs++;
      const btn=document.querySelector('[data-aluno-card="1"] .btn-toggle-secao'),card=btn.closest('.aluno-card');
      for(let i=0;i<20;i++)toggleSecao(1,'pagamento',btn);
      toggleSecao(1,'pagamento',btn);
      const minimized=document.getElementById('pagamento-content-1').style.display==='none';
      filtrarAlunos();
      const retained=document.getElementById('pagamento-content-1').style.display==='none';
      Storage.prototype.setItem=original;AvaliacaoTreinoSync.syncTraining=oldSync;
      const student={infoGuias:[],historicoTreinos:{toJSON(){throw Error('History must not be traversed');}}};
      AvaliacaoTreinoSync.fichaState(student);
      return {writes,syncs,minimized,retained,unchanged:before===localStorage.getItem('avaliacao_fisica_alunos')&&training===localStorage.getItem('treinoAlunos')};
    }''')
    assert results=={'writes':0,'syncs':0,'minimized':True,'retained':True,'unchanged':True},results
    browser.close()
    print('PASS: confirmed links in both lists, long observations, toggles without data writes/sync, retained view state, history-free comparison')
