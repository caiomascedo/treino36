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
    context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://app.test/treino36/')
    page.evaluate("""() => {
      localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',avaliacaoId:10,treino:{A:['Agachamento 3x10']},infoGuias:[{id:'1',titulo:'Ficha 1',peso:'59',avaliacaoOrigemId:11,avaliacaoOrigemData:'11/07/2026'}]},{student_id:'a2',nome:'Ana treino 2',avaliacaoId:10,treino:{A:['Leg press']}}]));
      let records=[{id:10,nome:'Ana',sexo:'F',altura:'1.7',idade:'24',treinoStudentIds:['a','a2'],avaliacoes:[{id:21,data:'03/10/2026',peso:'72',protocolo:'jp7'},{id:11,data:'11/07/2026',peso:'59',protocolo:'jp7',fotoF:'data:image/png;base64,aW1hZ2U='}]}];
      for(let i=0;i<20;i++)records.push({id:100+i,nome:'Outro '+i,avaliacoes:[{id:200+i,data:'01/01/2026',fotoF:'data:image/jpeg;base64,'+'A'.repeat(20000)}]});
      localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify(records));
    }""")
    page.reload();page.locator('#searchName').fill('Ana');page.locator('#studentEvaluationBtn').click()
    expect(page.locator('#infoTabsList .info-tab-btn')).to_have_count(2)
    expect(page.locator('#infoTabsList .active')).to_contain_text('Ficha 2')
    expect(page.locator('#fichaAssessmentDate')).to_have_text('Avaliação: 03/10/2026');expect(page.locator('#infoPeso')).to_have_value('72')
    page.locator('#infoTabsList .info-tab-btn').first.click();expect(page.locator('#infoPeso')).to_have_value('59')
    expect(page.locator('#fichaAssessmentDate')).to_have_text('Avaliação: 11/07/2026')
    session=context.new_cdp_session(page);session.send('Emulation.setCPUThrottlingRate',{'rate':4})
    page.evaluate("""() => {window.mainCompressions=[];const original=LZString.compressToUTF16;LZString.compressToUTF16=value=>{mainCompressions.push(value.length);return original(value);};}""")
    page.locator('#infoPeso').fill('60,5');page.wait_for_timeout(1400)
    assert page.evaluate('mainCompressions')==[], 'Ficha typing must never compress photos/history on the page'
    data=page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[0]")
    assert next(a for a in data['avaliacoes'] if a['id']==11)['peso']=='60.5'
    assert next(a for a in data['avaliacoes'] if a['id']==21)['peso']=='72'
    page.locator('#infoPeso').press('Tab')
    page.wait_for_function("AvaliacaoTreinoSync.read('treinoAlunos').every(s=>s.infoGuias?.find(g=>g.avaliacaoOrigemId===11)?.peso==='60.5')")
    page.locator('#openEvaluationBtn').click();expect(page.locator('#obsAssessmentHistory')).to_have_value('11')
    expect(page.locator('#obs-av-peso')).to_have_value('60.5')
    page.locator('#openEvaluationBtn').click()
    page.locator('#addInfoTabBtn').click();expect(page.locator('#infoTabsList .info-tab-btn')).to_have_count(3)
    expect(page.locator('#infoTabsList .active')).to_contain_text('Ficha 3')
    today=page.evaluate("new Date().toLocaleDateString('pt-BR')")
    expect(page.locator('#fichaAssessmentDate')).to_have_text('Avaliação: '+today)
    new_id=page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[0].avaliacoes.at(-1).id")
    page.locator('#infoPeso').fill('73');page.locator('#infoPeso').press('Tab')
    page.locator('#openEvaluationBtn').click();expect(page.locator('#obsAssessmentHistory')).to_have_value(str(new_id))
    expect(page.locator('#obs-av-peso')).to_have_value('73');page.locator('#obs-av-peso').fill('74');page.locator('#obs-av-peso').press('Tab')
    page.locator('#workoutObsDialog [data-close]').click();page.locator('#studentEvaluationBtn').click()
    expect(page.locator('#infoTabsList .active')).to_contain_text('Ficha 3');expect(page.locator('#infoPeso')).to_have_value('74')
    page.locator('#workoutObsDialog [data-close]').click();page.locator('#assessmentsLibraryBtn').click()
    lib=page.frame_locator('#assessmentLibraryFrame');lib.locator('[data-aluno-card="10"] .aluno-nome').click()
    lib.locator('[data-aluno-card="10"] .aluno-content > .assessment-tabs [data-section="avaliacoes"]').click();lib.locator('[data-aluno-card="10"] .btn-add-av').click()
    page.locator('#assessmentLibraryDialog [data-close]').click();page.locator('#studentEvaluationBtn').click()
    expect(page.locator('#infoTabsList .info-tab-btn')).to_have_count(4);expect(page.locator('#infoTabsList .active')).to_contain_text('Ficha 4')
    # Changing an evaluation date reorders fichas, preserving each evaluation's ID and weight.
    last_id=page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[0].avaliacoes.at(-1).id")
    page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click()
    page.locator('#obsAssessmentDate').fill('2026-06-01');page.locator('#obsAssessmentDate').press('Tab')
    page.locator('#workoutObsDialog [data-close]').click();page.locator('#studentEvaluationBtn').click()
    expect(page.locator('#infoTabsList .active')).to_contain_text('Ficha 4');expect(page.locator('#infoPeso')).to_have_value('74')
    page.locator('#infoTabsList .info-tab-btn').first.click();expect(page.locator('#fichaAssessmentDate')).to_have_text('Avaliação: 01/06/2026')
    data=page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[0]")
    assert len(data['avaliacoes'])==4 and next(a for a in data['avaliacoes'] if a['id']==11)['fotoF']=='data:image/png;base64,aW1hZ2U='
    # Deleting a generated ficha removes its paired assessment without recreating it on reopen.
    page.once('dialog',lambda d:d.accept());page.locator('#infoTabsList .info-tab-btn').first.locator('.info-tab-close').click()
    expect(page.locator('#infoTabsList .info-tab-btn')).to_have_count(3)
    assert page.evaluate(f"!AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[0].avaliacoes.some(a=>a.id==={last_id})")
    page.locator('#workoutObsDialog [data-close]').click();page.reload();page.locator('#studentEvaluationBtn').click()
    expect(page.locator('#infoTabsList .info-tab-btn')).to_have_count(3)
    assert page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].treino.A[0]")=='Agachamento 3x10'
    assert not errors,errors
    browser.close();print('PASS: dated chronological fichas, latest default, old/new edits affect only paired evaluations, new ficha/library assessment synchronize automatically, date reorder preserves IDs/photos, mapped delete durable, CPU4 typing has zero main compression')
