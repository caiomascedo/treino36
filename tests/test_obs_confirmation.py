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
      localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana vitoria',treino:{A:['Agachamento']},infoGuias:[{id:'f1',idade:'24 anos',peso:'73',altura:'1.63',dataNasc:'26/03/2002'}]}]));
      localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana Vitória',sexo:'F',nasc:'26/03/2002',altura:'1.75',idade:'24',avaliacoes:[{id:11,data:'11/07/2026',peso:'74.50'}]}]));
    }""")
    page.reload();page.locator('#searchName').fill('Ana vitoria');page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click()
    page.locator('#openEvaluationBtn').click()
    expect(page.locator('#mergeEvaluationDialog')).to_be_visible()
    page.evaluate("""() => { const original=Storage.prototype.setItem; Storage.prototype.setItem=function(key,value){if(key==='avaliacao_treino_antes_uniao') throw new DOMException('Full','QuotaExceededError');return original.call(this,key,value);}; }""")
    page.locator('#confirmMergeEvaluation').click()
    expect(page.locator('#mergeEvaluationDialog')).not_to_be_visible()
    frame=page.frame_locator('#trainingEvaluationFrame')
    expect(frame.locator('#peso-input-10-11')).to_have_value('74.50')
    for section in ['composicao','medidas','dobras','fotos']:
        page.locator('#obsAssessmentSections [data-assessment-section="'+section+'"]').click()
        expect(page.locator('#mergeEvaluationDialog')).not_to_be_visible()
        expect(frame.locator('#av-item-11 .av-content [data-section="'+section+'"]').first).to_have_attribute('aria-selected','true')
    assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos')).length")==1
    assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].data")=='11/07/2026'
    # Same name and birth date can open directly even without a saved link.
    page.evaluate("""() => {let records=JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'));delete records[0].treinoStudentId;delete records[0].treinoStudentIds;localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify(records));let students=JSON.parse(localStorage.getItem('treinoAlunos'));delete students[0].avaliacaoId;localStorage.setItem('treinoAlunos',JSON.stringify(students));}""")
    page.reload();page.locator('#searchName').fill('Ana vitoria');page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click()
    expect(page.locator('#mergeEvaluationDialog')).not_to_be_visible();expect(frame.locator('#peso-input-10-11')).to_have_value('74.50')
    assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos')).length")==1
    assert not errors,errors
    browser.close();print('PASS: confirmation closes despite optional backup quota failure; four Obs tabs open directly, identity and old assessment preserved')
