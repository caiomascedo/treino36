import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2] if Path(__file__).parent.parent.name == 'treino36' else Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1280, 'height':900})
    def route(request):
        url = urlparse(request.request.url)
        if url.hostname == 'app.test':
            path = ROOT / url.path.strip('/')
            if path.is_dir(): path /= 'index.html'
            if path.is_file():
                request.fulfill(body=path.read_bytes(), content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
                return
        request.fulfill(status=404, body='')
    context.route('**/*', route)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://app.test/treino36/')
    page.evaluate("""() => {
      localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'obs-1',nome:'Pessoa treino 1',treino:{A:['Agachamento 3x10']},infoGuias:[{id:'f1',titulo:'Ficha 1'}]}]));
      localStorage.setItem('avaliacao_fisica_alunos','[]');
    }""")
    page.reload(); page.locator('#searchName').fill('Pessoa treino 1'); page.locator('#obsIconBtn').click(); page.locator('#toggleInfoRelevanteBtn').click()
    for field,value in {'infoNomeCompleto':'Pessoa Completa','infoIdade':'28 anos','infoPeso':'70','infoAltura':'1.70','infoWhats':'86999999999','infoEmail':'pessoa@example.com'}.items():
        page.locator('#'+field).fill(value)
    page.locator('#saveFichaEvaluationBtn').click()
    expect(page.locator('#workoutObsDialog')).not_to_be_visible()
    record=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0]")
    assert record['nome']=='Pessoa Completa' and record['idade']=='28' and record['pesoIni']=='70' and record['avaliacoes']==[],record
    assert record['treinoStudentIds']==['obs-1']
    page.locator('#assessmentsLibraryBtn').click(); library=page.frame_locator('#assessmentLibraryFrame')
    expect(library.locator('.aluno-nome')).to_have_text('Pessoa Completa')
    library.locator('.aluno-nome').click(); library.locator('.btn-add-av').click()
    expect(library.locator('[id^="peso-input-"]')).to_have_value('70')
    library.locator('[id^="peso-input-"]').fill('72'); library.locator('[id^="peso-input-"]').press('Tab')
    page.locator('#assessmentLibraryDialog [data-close]').click()
    page.locator('#obsIconBtn').click(); page.locator('#toggleInfoRelevanteBtn').click()
    expect(page.locator('#infoPeso')).to_have_value('72')
    page.locator('#openEvaluationBtn').click(); frame=page.frame_locator('#trainingEvaluationFrame')
    expect(frame.locator('[id^="peso-input-"]')).to_have_value('72')
    frame.locator('[id^="peso-input-"]').fill('74')
    page.locator('#saveInlineEvaluationBtn').click()
    expect(page.locator('#workoutObsDialog')).not_to_be_visible()
    records=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")
    assert len(records)==1 and len(records[0]['avaliacoes'])==1 and records[0]['avaliacoes'][0]['peso']=='74',records
    page.locator('#assessmentsLibraryBtn').click(); library.locator('.aluno-nome').click(); library.locator('.av-header').click()
    expect(library.locator('[id^="peso-input-"]')).to_have_value('74')
    page.locator('#assessmentLibraryDialog [data-close]').click()
    # Saving an unlinked ficha asks for identity confirmation, then saves into the existing history.
    page.evaluate("""() => {
      localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'obs-2',nome:'Pessoa treino 2',treino:{A:['Supino 4x8']},infoGuias:[{id:'f2',nomeCompleto:'Pessoa Completa',peso:'76',altura:'1.70',idade:'28'}]}]));
    }""")
    page.reload(); page.locator('#searchName').fill('Pessoa treino 2'); page.locator('#obsIconBtn').click(); page.locator('#toggleInfoRelevanteBtn').click(); page.locator('#saveObsBtn').click()
    expect(page.locator('#mergeEvaluationDialog')).to_be_visible()
    expect(page.locator('#confirmMergeEvaluation')).to_be_disabled()
    assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].peso")=='74'
    page.locator('#confirmSamePerson').check(); page.locator('#confirmMergeEvaluation').click()
    expect(page.locator('#workoutObsDialog')).not_to_be_visible()
    records=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")
    assert len(records)==1 and records[0]['avaliacoes'][0]['peso']=='76' and set(records[0]['treinoStudentIds'])=={'obs-1','obs-2'},records
    assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].treino.A[0]")=='Supino 4x8'
    # A different person can be explicitly registered from Save without opening another form.
    page.evaluate("""() => {localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'obs-3',nome:'Outra pessoa',treino:{A:['Remada 3x12']}}]));}""")
    page.reload(); page.locator('#searchName').fill('Outra pessoa'); page.locator('#obsIconBtn').click(); page.locator('#saveObsBtn').click()
    expect(page.locator('#mergeEvaluationDialog')).to_be_visible(); page.locator('#createSeparateEvaluation').click()
    expect(page.locator('#workoutObsDialog')).not_to_be_visible()
    records=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")
    assert len(records)==2 and records[1]['nome']=='Outra pessoa' and records[0]['avaliacoes'][0]['peso']=='76',records
    page.locator('#obsIconBtn').click(); page.locator('#saveObsBtn').click()
    assert len(page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))"))==2
    assert not errors,errors
    browser.close()
    print('PASS: Save Obs registers the same assessment client, library/inline editing share history, blur saves drafts, identity confirmation, separate new person and no duplicated records or changed workouts')
