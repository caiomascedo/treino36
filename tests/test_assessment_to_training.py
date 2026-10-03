import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2] if Path(__file__).parent.parent.name == 'treino36' else Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':390, 'height':844})
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
      localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'t1',nome:'Ana treino 1',whatsapp:'200',treino:{A:['Agachamento 3x10']},titulos:{A:'A. Pernas'}}]));
      localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana Silva',idade:'32',altura:'1.72',whatsapp:'86911111111',email:'ana@example.com',sexo:'F',avaliacoes:[{id:11,peso:'65',data:'03/10/2026',protocolo:'jp7'}]}]));
    }""")
    page.reload();page.locator('#assessmentsLibraryBtn').click()
    library=page.frame_locator('#assessmentLibraryFrame');library.locator('.aluno-nome').click()
    library.locator('.btn-add-to-training').click();library.locator('.assessment-training-add').click()
    expect(library.locator('.assessment-training-select')).not_to_be_attached()
    students=page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
    assert len(students)==2 and students[0]['treino']['A']==['Agachamento 3x10'],students
    created=next(s for s in students if s['nome']=='Ana Silva')
    assert created['whatsapp']=='86911111111' and created['infoRelevante']['idade']=='32'
    assert created['infoRelevante']['peso']=='65' and created['infoRelevante']['email']=='ana@example.com'
    page.locator('#assessmentLibraryDialog [data-close]').click()
    page.locator('#searchName').fill('Ana Silva');page.locator('#studentEvaluationBtn').click()
    frame=page.frame_locator('#trainingEvaluationFrame');expect(frame.locator('[id^="peso-input-"]')).to_have_value('65')
    page.locator('#workoutObsDialog [data-close]').click()
    page.once('dialog',lambda dialog:dialog.accept('86922222222'))
    page.locator('#wppIconBtn').click()
    assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].whatsapp")=='86922222222'
    assessment=context.new_page();assessment.goto('http://app.test/treino36/avaliacao.html?embed=treino36-library')
    assessment.locator('.aluno-nome').click();assessment.locator('.aluno-content>.assessment-tabs [data-section="cadastro"]').click()
    expect(assessment.locator('input[type="tel"]')).to_have_value('86922222222')
    assessment.locator('input[type="tel"]').fill('86933333333');assessment.locator('input[type="tel"]').press('Tab')
    def update_whatsapp(dialog):
        assert dialog.default_value=='86933333333',dialog.default_value
        dialog.accept('86944444444')
    page.once('dialog',update_whatsapp);page.locator('#wppIconBtn').click()
    expect(assessment.locator('input[type="tel"]')).to_have_value('86944444444')
    # Link another existing workout only after confirming identity, preserving exercises.
    assessment.locator('.btn-add-to-training').click();assessment.locator('.assessment-training-select').select_option('t1')
    assessment.locator('.assessment-training-add').click();expect(assessment.locator('.picker-status')).to_contain_text('Confirme')
    assessment.locator('.assessment-training-confirm').check();assessment.locator('.assessment-training-add').click()
    students=page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
    assert len(students)==2 and students[0]['nome']=='Ana treino 1' and students[0]['treino']['A']==['Agachamento 3x10'],students
    assert all(s['whatsapp']=='86944444444' for s in students)
    record=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0]")
    assert len(record['treinoStudentIds'])==2 and len(record['avaliacoes'])==1
    assessment.locator('.btn-add-to-training').click();assessment.locator('.assessment-training-select').select_option('new');assessment.locator('.assessment-training-add').click()
    expect(assessment.locator('.picker-status')).to_contain_text('Já existe esse nome')
    assert len(page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))"))==2
    assert not errors,errors
    browser.close()
    print('PASS: create training client from evaluation, open same evaluation from student shortcut, WhatsApp both ways, confirmed existing workouts, preserved names/exercises/history and duplicate-name protection')
