from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':390,'height':844})
    def route(request):
        url=urlparse(request.request.url);path=ROOT/url.path.strip('/')
        if path.is_dir():path/='index.html'
        if url.hostname=='app.test' and path.is_file():request.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
        else:request.fulfill(status=404,body='')
    context.route('**/*',route)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://app.test/treino36/')
    page.evaluate('''() => {
      const canvas=document.createElement('canvas');canvas.width=60;canvas.height=60;const ctx=canvas.getContext('2d'),pixels=ctx.createImageData(60,60);crypto.getRandomValues(pixels.data);ctx.putImageData(pixels,0,0);const photo=canvas.toDataURL();
      const records=Array.from({length:21},(_,i)=>({id:i+1,nome:'Pessoa '+i,sexo:'F',altura:'1.60',idade:'30',treinoStudentIds:['s'+i],avaliacoes:[{id:100+i,data:'01/10/2026',peso:'60',fotoF:photo}]}));
      records.at(-1).treinoStudentIds=[];
      records[0].avaliacoes.push({id:200,data:'03/10/2026',peso:'61'});
      localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify(records));
      localStorage.setItem('treinoAlunos',JSON.stringify(records.map((a,i)=>({student_id:'s'+i,nome:a.nome,treino:{A:['Supino']},historicoTreinos:Array.from({length:30},()=>({treino:{A:['Descrição '.repeat(80)]}}))}))));
    }''')
    page.reload();page.locator('#searchName').fill('Pessoa 0');page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('[data-assessment-section="composicao"]').click();expect(page.locator('#obs-av-peso')).to_have_value('61')
    context.new_cdp_session(page).send('Emulation.setCPUThrottlingRate',{'rate':4})
    page.evaluate('''() => {window.mainCompressions=[];const old=LZString.compressToUTF16;LZString.compressToUTF16=v=>{const start=performance.now(),out=old(v);mainCompressions.push(performance.now()-start);return out;};}''')
    for value in ['7','72','72,5']:
        page.locator('#obs-av-peso').fill(value);page.wait_for_timeout(1300)
    expect(page.locator('#obs-av-imc')).to_have_value('28.3')
    assert page.evaluate('mainCompressions')==[], 'Typing pauses must never compress the whole database on the page'
    assert page.evaluate("JSON.parse(localStorage.getItem('treino36_assessment_drafts')).some(d=>d.fields.peso==='72,5')")
    # A second page reads the edit immediately, before heavy compaction completes.
    other=context.new_page();other.goto('http://app.test/treino36/avaliacao.html?embed=treino36-engine')
    assert other.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[0].avaliacoes[1].peso")=='72,5'
    page.locator('[data-assessment-section="medidas"]').click()
    expect(page.locator('#obs-av-biceps')).to_have_attribute('inputmode','text')
    page.locator('#obs-av-biceps').fill('20 ');expect(page.locator('#obs-av-biceps')).to_have_value('20 ')
    page.locator('#obs-av-biceps').press('End');page.locator('#obs-av-biceps').press_sequentially('21')
    expect(page.locator('#obs-av-biceps')).to_have_value('20 / 21')
    page.locator('#obs-av-coxa').fill('55');page.locator('#obs-av-coxa').locator('..').locator('.obs-pair-separator').click();page.locator('#obs-av-coxa').press_sequentially('54')
    expect(page.locator('#obs-av-coxa')).to_have_value('55 / 54')
    page.locator('[data-assessment-section="fotos"]').click()
    for key in ['motivo','resumo']:
        area=page.locator('#obs-av-'+key)
        assert area.bounding_box()['width']>=page.locator('.obs-assessment-fields').bounding_box()['width']-2 and area.bounding_box()['height']>=150
        area.fill('Texto longo '+key+' '+('Detalhes da avaliação. '*100));page.wait_for_timeout(1300)
    assert page.evaluate('mainCompressions')==[], 'Text fields and tab changes must not trigger synchronous compression'
    library=context.new_page();library.goto('http://app.test/treino36/avaliacao.html?embed=treino36-library')
    expect(library.locator('.aluno-content')).to_have_count(0)
    expect(library.locator('[data-aluno-card="21"] .assessment-training-link')).to_have_text('Sem treino')
    library.locator('[data-aluno-card="2"] .aluno-nome').click()
    expect(library.locator('.aluno-content')).to_have_count(1)
    assert library.locator('#fotobox-2-f-101 img').get_attribute('src') is None
    library.locator('#av-item-101 .av-header').click();library.locator('#av-item-101 [data-section="fotos"]').click()
    assert library.locator('#fotobox-2-f-101 img').get_attribute('src').startswith('data:image/')
    before=page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)")
    page.once('dialog',lambda dialog:dialog.dismiss());page.locator('#obsDeleteAssessment').click()
    expect(page.locator('#obsAssessmentHistory option')).to_have_count(2)
    page.once('dialog',lambda dialog:dialog.accept());page.locator('#obsDeleteAssessment').click()
    expect(page.locator('#obsAssessmentHistory option')).to_have_count(1)
    after=page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)")
    assert after[0]['avaliacoes'][0]==before[0]['avaliacoes'][0] and len(after)==21
    assert all(a['id']!=200 for a in after[0]['avaliacoes'])
    page.once('dialog',lambda dialog:dialog.accept());page.locator('#obsDeleteAssessment').click()
    expect(page.locator('#obs-av-peso')).to_have_count(0)
    expect(page.locator('#obsDeleteAssessment')).to_be_disabled()
    assert page.evaluate("AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[0].avaliacoes")==[]
    # Reload preserves the empty history rather than silently recreating an assessment.
    page.reload();page.locator('#searchName').fill('Pessoa 0');page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('[data-assessment-section="composicao"]').click()
    expect(page.locator('#obsNewAssessment')).to_be_visible();expect(page.locator('#obs-av-peso')).to_have_count(0)
    page.locator('#obsNewAssessment').click();expect(page.locator('#obs-av-peso')).to_be_visible()
    # The compact worker preserves concurrent edits to the base and journal.
    result=other.evaluate('''async() => {TreinoStorage.stageAssessment(2,101,{cintura:'84'});const job=TreinoStorage.compactAssessments();TreinoStorage.stageAssessment(2,101,{cintura:'85'});await job;return AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[1].avaliacoes[0].cintura;}''')
    assert result=='85'
    other.evaluate('''async() => {await TreinoStorage.compactAssessments();}''')
    assert other.evaluate("JSON.parse(localStorage.getItem('treino36_assessment_drafts'))")==[]
    # An unavailable worker leaves the durable edits readable and exportable.
    failed=context.new_page();failed.goto('http://app.test/treino36/avaliacao.html?embed=treino36-engine')
    failed.evaluate("() => {window.Worker=class {constructor(){throw Error('Worker indisponível');}};}")
    result=failed.evaluate('''async() => {TreinoStorage.stageAssessment(3,102,{cintura:'88'});try{await TreinoStorage.compactAssessments();}catch(error){}return AvaliacaoTreinoSync.read(AvaliacaoTreinoSync.key)[2].avaliacoes[0].cintura;}''')
    assert result=='88'
    # Writing a canonical snapshot must commit overlaid edits before clearing the journal.
    result=failed.evaluate('''() => {const key=AvaliacaoTreinoSync.key,value=localStorage.getItem(key);localStorage.setItem(key,value);TreinoStorage.clearAssessmentDrafts();return AvaliacaoTreinoSync.read(key)[2].avaliacoes[0].cintura;}''')
    assert result=='88'
    assert not errors,errors
    browser.close();print('PASS: CPU4 typing/text pauses with zero main-thread compression, durable cross-page edits, D/E keyboard and separator, full-width text, safe delete including last, worker conflict preservation')
