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
      localStorage.setItem('treinoAlunos',JSON.stringify([
        {student_id:'s1',nome:'Ana treino 1',treino:{A:['Agachamento 3x10']},infoGuias:[{id:'f1',nomeCompleto:'Ana Silva',idade:'28 anos',peso:'60 kg',altura:'165',dataNasc:'17/06/1998',whats:'86999999999',email:'ana@example.com'}]},
        {student_id:'s2',nome:'Ana treino 2',treino:{A:['Supino 4x8']}},
        {student_id:'s3',nome:'Sem ficha',treino:{A:['Remada 3x12']}},
        {student_id:'s4',nome:'Ána Silva treino 3',treino:{A:['Leg press 3x10']}}
      ])); localStorage.setItem('avaliacao_fisica_alunos','[]');
    }""")
    page.reload(); page.locator('#assessmentsLibraryBtn').click()
    frame=page.frame_locator('#assessmentLibraryFrame')
    frame.locator('#addTrainingStudentBtn').click()
    expect(frame.locator('.training-student-select option')).to_have_count(4)
    assert frame.locator('.training-student-select option').evaluate_all("options=>options.map(o=>o.value)")==['s4','s1','s2','s3']
    frame.locator('.training-student-order').select_option('za')
    assert frame.locator('.training-student-select option').evaluate_all("options=>options.map(o=>o.value)")==['s3','s2','s1','s4']
    frame.locator('.training-student-order').select_option('az')
    frame.locator('.training-student-search').fill('ANA SILVA')
    expect(frame.locator('.training-student-select option')).to_have_count(2)
    expect(frame.locator('.training-registration-status')).to_contain_text('Sem vínculo')
    frame.locator('.training-student-search').fill('Ana treino 1')
    expect(frame.locator('.training-student-preview')).to_contain_text('60 kg')
    frame.locator('.picker-add').click()
    expect(frame.locator('.aluno-nome')).to_have_text('Ana Silva')
    frame.locator('.aluno-content>.assessment-tabs [data-section="cadastro"]').click()
    expect(frame.locator('[id^="idade-"]')).to_have_value('28')
    expect(frame.locator('[id^="altura-"]')).to_have_value('1.65')
    frame.locator('.aluno-content>.assessment-tabs [data-section="avaliacoes"]').click()
    frame.locator('.btn-add-av').click()
    expect(frame.locator('[id^="peso-input-"]')).to_have_value('60')
    expect(frame.locator('input[id^="imc-"]')).to_have_value('22.0')
    expect(frame.locator('.av-content [data-section="composicao"]')).to_have_attribute('aria-selected','true')
    expect(frame.locator('.av-content input[onchange*="cintura"]')).to_be_hidden()
    frame.locator('.av-content [data-section="medidas"]').click()
    expect(frame.locator('.av-content input[onchange*="cintura"]')).to_be_visible()
    frame.locator('.av-content [data-section="composicao"]').click()
    frame.locator('[id^="peso-input-"]').fill('62'); frame.locator('[id^="peso-input-"]').press('Tab')
    assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].infoGuias[0].peso")=='62'
    # Editing the linked ficha in Obs updates the compact assessment as well.
    workout=context.new_page(); workout.goto('http://app.test/treino36/')
    workout.locator('#searchName').fill('Ana treino 1'); workout.locator('#obsIconBtn').click(); workout.locator('#toggleInfoRelevanteBtn').click()
    workout.locator('#infoIdade').fill('29 anos'); workout.locator('#infoIdade').press('Tab')
    frame.locator('.aluno-content>.assessment-tabs [data-section="cadastro"]').click()
    expect(frame.locator('[id^="idade-"]')).to_have_value('29')
    frame.locator('input[type="email"]').fill('novo@example.com'); frame.locator('input[type="email"]').press('Tab')
    expect(workout.locator('#infoEmail')).to_have_value('novo@example.com')
    workout.close()
    frame.locator('#addTrainingStudentBtn').click()
    frame.locator('.training-student-filter').select_option('cadastrado')
    expect(frame.locator('.training-student-select option')).to_have_count(1)
    expect(frame.locator('.training-student-select')).to_have_value('s1')
    expect(frame.locator('.training-registration-status')).to_contain_text('Já cadastrado')
    expect(frame.locator('.picker-add')).to_have_text('Abrir cadastro')
    frame.locator('.training-student-filter').select_option('confirmar')
    expect(frame.locator('.training-student-select')).to_have_value('s4')
    expect(frame.locator('.training-registration-status')).to_contain_text('Confirme')
    expect(frame.locator('.identity-confirm')).to_be_visible()
    frame.locator('.picker-add').click()
    expect(frame.locator('.picker-status')).to_contain_text('Confirme')
    assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].treinoStudentIds")==['s1']
    frame.locator('.training-student-filter').select_option('novo')
    assert frame.locator('.training-student-select option').evaluate_all("options=>options.map(o=>o.value)")==['s2','s3']
    frame.locator('.training-student-search').fill('Não existe')
    expect(frame.locator('.picker-add')).to_be_disabled()
    frame.locator('.training-student-search').fill('Ana treino 2')
    frame.locator('.training-student-filter').select_option('todos')
    record=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0]")
    frame.locator('.assessment-person-select').select_option(str(record['id']))
    frame.locator('.picker-add').click()
    expect(frame.locator('.picker-status')).to_contain_text('Confirme')
    assert len(page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))"))==1
    frame.locator('.identity-confirm').check(); frame.locator('.picker-add').click()
    record=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0]")
    assert record['treinoStudentIds']==['s1','s2'] and record['idade']=='29' and record['avaliacoes'][0]['peso']=='62'
    frame.locator('#addTrainingStudentBtn').click(); frame.locator('.training-student-search').fill('Sem ficha'); frame.locator('.picker-add').click()
    expect(frame.locator('.aluno-card.active .aluno-nome')).to_have_text('Sem ficha')
    frame.locator('.aluno-content>.assessment-tabs [data-section="cadastro"]').click()
    expect(frame.locator('.aluno-card.active [id^="altura-"]')).to_have_value('')
    students=page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
    assert [s['nome'] for s in students]==['Ana treino 1','Ana treino 2','Sem ficha','Ána Silva treino 3']
    assert students[1]['treino']['A']==['Supino 4x8']
    expect(frame.locator('.btn-export-all')).to_be_hidden()
    frame.locator('.assessment-more-options summary').click(); expect(frame.locator('.btn-export-all')).to_be_visible()
    frame.locator('.assessment-more-options summary').click()
    frame.locator('.aluno-card.active .aluno-header').click()
    folder=frame.locator('.aluno-card').first
    expect(folder.locator('.aluno-acoes')).to_be_hidden()
    widths=frame.locator('.alunos-grid').evaluate("el=>({columns:getComputedStyle(el).gridTemplateColumns.split(' ').length,width:el.clientWidth,scroll:el.scrollWidth})")
    assert widths['columns']==2 and widths['scroll']<=widths['width'], widths
    assert page.locator('#mergeEvaluationBtn').count()==0
    assert page.locator('#importAssessmentsBtn').count()==0
    assert page.locator('#exportAssessmentsBtn').count()==0
    assert not errors,errors
    page.screenshot(path=str(Path(__file__).parent/'compact-mobile.png'))
    browser.close()
    print('PASS: mobile tabs, compact controls, training student import with/without ficha, weight prefilling, identity confirmation, preserved existing values and workouts')
