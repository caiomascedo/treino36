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
      localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'s1',nome:'Cliente treino 1',treino:{A:['Agachamento 3x10']},avaliacaoId:10,avaliacaoFichaId:'f1',infoGuias:[{id:'f1',peso:'70',altura:'1.70',idade:'30'}]}]));
      localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Cliente completo',sexo:'M',altura:'1.70',idade:'30',treinoStudentId:'s1',treinoStudentIds:['s1'],avaliacoes:[{id:11,data:'01/09/2026',peso:'68',cintura:'78',protocolo:'jp7'},{id:12,data:'03/10/2026',peso:'70',cintura:'80',protocolo:'jp7'}]}]));
    }""")
    page.reload();page.locator('#searchName').fill('Cliente treino 1');page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click()
    frame=page.frame_locator('#trainingEvaluationFrame')
    page.locator('#obsAssessmentSections [data-assessment-section="medidas"]').click()
    expect(frame.locator('#av-item-12 .av-content [data-section="medidas"]')).to_have_attribute('aria-selected','true')
    field=frame.locator('#av-item-12 input[onchange*="cintura"]');expect(field).to_have_value('80');field.fill('82');field.press('Tab')
    records=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")
    assert records[0]['avaliacoes'][0]['cintura']=='78' and records[0]['avaliacoes'][1]['cintura']=='82'
    page.locator('#obsAssessmentSections [data-assessment-section="dobras"]').click()
    expect(frame.locator('#av-item-12 .av-content [data-section="dobras"]')).to_have_attribute('aria-selected','true')
    for key,value in {'triceps':'10','axilar':'11','torax':'12','abdominal':'13','suprailiaca':'14','subescapular':'15','pregaCoxa':'16'}.items():
        field=frame.locator('#av-item-12 input[onchange*=\"\''+key+'\'\"]');field.fill(value);field.press('Tab')
    assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[1]._dobras.soma")==91
    page.locator('#obsAssessmentSections [data-assessment-section="fotos"]').click()
    expect(frame.locator('#av-item-12 .av-content [data-section="fotos"]')).to_have_attribute('aria-selected','true')
    photo=bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')
    frame.locator('#file-10-f-12').set_input_files({'name':'foto.png','mimeType':'image/png','buffer':photo})
    expect(frame.locator('#fotobox-10-f-12 img')).to_be_visible()
    page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click()
    expect(frame.locator('#av-item-12 .av-content [data-section="composicao"]')).to_have_attribute('aria-selected','true')
    frame.locator('#peso-input-10-12').fill('72');page.locator('#saveInlineEvaluationBtn').click()
    page.locator('#assessmentsLibraryBtn').click();library=page.frame_locator('#assessmentLibraryFrame');library.locator('.aluno-nome').click();library.locator('#av-item-12 .av-header').click()
    expect(library.locator('#peso-input-10-12')).to_have_value('72')
    library.locator('#av-item-12 .av-content [data-section="medidas"]').click();expect(library.locator('#av-item-12 input[onchange*="cintura"]')).to_have_value('82')
    library.locator('#av-item-12 .av-content [data-section="fotos"]').click();expect(library.locator('#fotobox-10-f-12 img')).to_be_visible()
    assert len(page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes"))==2
    assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].treino.A[0]")=='Agachamento 3x10'
    assert not errors,errors
    browser.close();print('PASS: direct Obs tabs edit latest composition, measurements, skinfolds and photos; shared library results and preserved older history/workout')
