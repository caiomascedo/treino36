from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':390,'height':844})
    def route(r):
        u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
        if path.is_dir():path/='index.html'
        if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
        else:r.fulfill(status=404,body='')
    context.route('**/*',route)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://app.test/treino36/')
    page.evaluate("""() => {localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento']},infoGuias:[{id:'1',titulo:'Ficha 1',peso:'60',altura:'1.7'},{id:'2',titulo:'Ficha 2',peso:'72',altura:'1.7'}]},{student_id:'b',nome:'Bruno',treino:{A:['Supino']}}]));localStorage.setItem('avaliacao_fisica_alunos','[]');}""")
    page.reload();page.locator('#searchName').fill('Ana');page.locator('#studentEvaluationBtn').click()
    expect(page.locator('#infoTabsList .info-tab-btn.active')).to_contain_text('Ficha 2')
    expect(page.locator('#infoPeso')).to_have_value('72');expect(page.locator('#obsNativeAssessment')).not_to_be_visible()
    assert page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)")==[]
    page.locator('#expandObsBtn').click();expect(page.locator('#infoPeso')).to_be_visible()
    assert page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)")==[]
    page.locator('#expandObsBtn').click();page.locator('#workoutObsDialog [data-close]').click()
    page.evaluate("""() => {const students=AvaliacaoTreinoSync.read('treinoAlunos');students[0].infoGuias.push({id:'3',titulo:'Ficha 3',peso:'73',altura:'1.7'});localStorage.setItem('treinoAlunos',JSON.stringify(students));}""")
    page.reload();page.locator('#studentEvaluationBtn').click()
    expect(page.locator('#infoTabsList .info-tab-btn.active')).to_contain_text('Ficha 3')
    expect(page.locator('#infoPeso')).to_have_value('73')
    assert page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)")==[]
    page.locator('#openEvaluationBtn').click()
    expect(page.locator('#obs-av-peso')).to_have_value('73')
    expect(page.locator('#openEvaluationBtn')).to_have_text('Minimizar avaliação')
    page.locator('#openEvaluationBtn').click();expect(page.locator('#obsNativeAssessment')).not_to_be_visible()
    page.locator('#openEvaluationBtn').click();expect(page.locator('#obs-av-peso')).to_have_value('73')
    assert page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key).length")==1
    assert page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[0].avaliacoes.length")==1
    page.locator('#obs-av-peso').fill('71');page.locator('#obs-av-peso').press('Tab')
    page.locator('#workoutObsDialog [data-close]').click();page.locator('#studentEvaluationBtn').click()
    expect(page.locator('#obsNativeAssessment')).not_to_be_visible()
    page.locator('#obsAssessmentSections [data-assessment-section="medidas"]').click()
    expect(page.locator('#obs-av-biceps')).to_be_visible()
    assert page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[0].avaliacoes.length")==1
    page.locator('#workoutObsDialog [data-close]').click()
    # A shared person loses the assessment in every linked workout; another person remains intact.
    page.evaluate("""() => {
      let records=AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key),students=AvaliacaoTreinoSync.read('treinoAlunos');
      records[0].treinoStudentIds.push('a2');students.push({student_id:'a2',nome:'Ana treino 2',treino:{A:['Leg press']},avaliacaoId:records[0].id,avaliacaoFichaId:'1'});
      records.push({id:99,nome:'Bruno',treinoStudentIds:['b'],avaliacoes:[{id:100,peso:'80',data:'01/10/2026'}]});
      localStorage.setItem('treinoAlunos',JSON.stringify(students));localStorage.setItem(AvaliacaoTreinoSync.key,JSON.stringify(records));
    }""")
    page.reload();page.locator('#searchName').fill('Ana');page.locator('#searchName').press('Escape')
    page.once('dialog',lambda d:d.dismiss());page.locator('#deleteBtn').click()
    assert page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key).length")==2
    def confirm_delete(d):
        assert 'todas as avaliações' in d.message;d.accept()
    page.once('dialog',confirm_delete);page.locator('#deleteBtn').click();page.wait_for_timeout(1400)
    assert page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key).map(a=>a.id)")==[99]
    assert page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos').length")==2
    assert page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos').find(s=>s.student_id==='a2').avaliacaoId") is None
    page.locator('#assessmentsLibraryBtn').click();library=page.frame_locator('#assessmentLibraryFrame')
    expect(library.locator('.aluno-nome')).to_have_text('Bruno')
    page.locator('#assessmentLibraryDialog [data-close]').click()
    page.locator('#undoDeleteStudentBtn').click()
    assert page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos').length")==3
    records=page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)")
    assert len(records)==2 and next(a for a in records if a['id']!=99)['avaliacoes'][0]['peso']=='71'
    assert page.evaluate("!!AvaliacaoTreinoSync.read('treinoAlunos').find(s=>s.student_id==='a2').avaliacaoId")
    # The list delete path must have the same behavior, including a cached library.
    page.locator('#listBtn').click();item=page.locator('.aluno-list-item[data-nome="Ana"]')
    page.once('dialog',confirm_delete);item.locator('.delete-aluno-btn').click();page.locator('#closeModalBtn').click()
    page.locator('#assessmentsLibraryBtn').click();expect(library.locator('.aluno-nome')).to_have_text('Bruno')
    assert not errors,errors
    browser.close();print('PASS: latest ficha-only opening/maximizing; explicit start; minimize/reopen without new records; cancel/delete/undo shared assessments from both workout paths; cached library refreshed')
