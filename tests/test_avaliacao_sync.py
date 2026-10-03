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
                request.fulfill(body=path.read_bytes(), content_type='application/javascript' if path.suffix == '.js' else 'text/html')
                return
        request.fulfill(status=404, body='')
    context.route('**/*', route)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://app.test/treino36/')
    page.evaluate("""() => {
      localStorage.setItem('treinoAlunos', JSON.stringify([{student_id:'student-1',nome:'Aluno Teste',treino:{A:['Agachamento 3x10']},titulos:{A:'A. Pernas'},infoGuias:[{id:'ficha1',titulo:'Ficha 1',nomeCompleto:'Aluno Teste',peso:'75 kg',altura:'1,80',idade:'30 anos',whats:'123456789'}]}]));
      localStorage.setItem('avaliacao_fisica_alunos', '[]');
    }""")
    page.reload()
    page.locator('#searchName').fill('Aluno Teste')
    page.locator('#obsIconBtn').click()
    page.locator('#toggleInfoRelevanteBtn').click()
    page.locator('#openEvaluationBtn').click()
    frame = page.frame_locator('#trainingEvaluationFrame')
    expect(frame.locator('.btn-add-av')).to_be_visible()
    frame.locator('.btn-add-av').click()
    weight = frame.locator('[id^="peso-input-"]')
    expect(weight).to_be_visible()
    weight.fill('80')
    weight.press('Tab')
    expect(page.locator('#infoPeso')).to_have_value('80')
    data = page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")
    assert len(data) == 1 and data[0]['treinoStudentId'] == 'student-1'
    assert data[0]['avaliacoes'][0]['imc'] == '24.7', data
    # The standalone app reads the same complete assessment.
    standalone = context.new_page()
    standalone.on('pageerror', lambda error: errors.append(str(error)))
    standalone.goto('http://app.test/avaliacao/')
    standalone.locator('.aluno-header').click()
    standalone.locator('.av-header').click()
    expect(standalone.locator('[id^="peso-input-"]')).to_have_value('80')
    standalone.locator('[id^="gordura-input-"]').fill('18')
    standalone.locator('[id^="gordura-input-"]').press('Tab')
    expect(frame.locator('[id^="gordura-input-"]')).to_have_value('18')
    # Close embedded assessment, then edit the linked workout ficha.
    page.locator('#trainingEvaluationDialog [data-close]').click()
    page.locator('#infoPeso').fill('82')
    page.locator('#infoPeso').press('Tab')
    expect(standalone.locator('[id^="peso-input-"]')).to_have_value('82')
    assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].treino.A[0]") == 'Agachamento 3x10'
    # Reopening reuses the record and keeps the existing assessments.
    page.locator('#openEvaluationBtn').click()
    expect(frame.locator('.av-item')).to_have_count(1)
    assert len(page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")) == 1
    page.screenshot(path=str(Path(__file__).parent / 'evaluation.png'), full_page=True)
    # Ambiguous names are rejected, without silently choosing another person.
    assert standalone.evaluate("""() => {
      try { AvaliacaoTreinoSync.find([{nome:'Duplicado'},{nome:'Duplicado'}], {student_id:'new',nome:'Duplicado'}); return false; }
      catch(e) { return e.message.includes('mesmo nome'); }
    }""")
    assert not errors, errors
    print('PASS: embedded form, new student, bidirectional complete records, ficha edits, IMC, deduplication, workout preservation and ambiguous names')
    standalone.close()
    page.evaluate("""() => {
      localStorage.setItem('treinoAlunos', JSON.stringify([{student_id:'student-merge',nome:'Maria do treino',whatsapp:'111111111',treino:{A:['Supino 4x8']},titulos:{A:'A. Superior'},infoGuias:[{id:'f1',titulo:'Ficha 1',nomeCompleto:'Maria do treino',peso:'60 kg',altura:'1,65',idade:'28',email:'maria@example.com',whats:'111111111'}]}]));
      localStorage.setItem('avaliacao_fisica_alunos', JSON.stringify([{id:100,nome:'Maria Completa',whatsapp:'999999999',altura:'1.70',idade:'29',sexo:'F',avaliacoes:[{id:101,peso:'65',gordura:'20',protocolo:'jp7',fotoF:'data:image/png;base64,aGVsbG8=',resumo:'Histórico preservado'}]}]));
    }""")
    page.reload()
    page.locator('#searchName').fill('Maria do treino')
    page.locator('#obsIconBtn').click()
    page.locator('#toggleInfoRelevanteBtn').click()
    page.locator('#mergeEvaluationBtn').click()
    page.locator('#mergeEvaluationSelect').select_option('100')
    expect(page.locator('#mergeEvaluationPreview')).to_contain_text('Maria Completa')
    expect(page.locator('#confirmMergeEvaluation')).to_be_disabled()
    page.locator('#confirmSamePerson').check()
    page.locator('#confirmMergeEvaluation').click()
    expect(page.locator('#infoWhats')).to_have_value('999999999')
    expect(page.locator('#infoPeso')).to_have_value('65')
    expect(page.locator('#infoEmail')).to_have_value('maria@example.com')
    merged = page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")
    assert len(merged) == 1 and merged[0]['treinoStudentId'] == 'student-merge'
    assert merged[0]['avaliacoes'][0]['fotoF'] == 'data:image/png;base64,aGVsbG8='
    assert merged[0]['avaliacoes'][0]['resumo'] == 'Histórico preservado'
    assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].treino.A[0]") == 'Supino 4x8'
    page.locator('#openEvaluationBtn').click()
    expect(frame.locator('[id^="peso-input-"]')).to_have_value('65')
    frame.locator('[id^="peso-input-"]').fill('66')
    frame.locator('[id^="peso-input-"]').press('Tab')
    expect(page.locator('#infoPeso')).to_have_value('66')
    page.locator('#trainingEvaluationDialog [data-close]').click()
    # Prefer workout values on a second merge without deleting the assessment.
    page.locator('#infoPeso').fill('63')
    page.locator('#infoPeso').press('Tab')
    page.locator('#mergeEvaluationBtn').click()
    page.locator('#confirmSamePerson').check()
    page.locator('#mergeEvaluationSource').select_option('training')
    page.locator('#confirmMergeEvaluation').click()
    assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].peso") == '63'
    assert page.evaluate("Boolean(localStorage.getItem('avaliacao_treino_antes_uniao'))")
    assert not errors, errors
    print('PASS: explicit merge with different names, conflicts, missing fields, WhatsApp, preserved photos/history, source choice and post-merge sync')
    # A second separate workout may refer to the same confirmed person.
    page.evaluate("""() => {
      const students = JSON.parse(localStorage.getItem('treinoAlunos'));
      const second = JSON.parse(JSON.stringify(students[0]));
      second.student_id = 'student-merge-2'; second.nome = 'Maria treino 2';
      second.treino = {A:['Remada 3x12']};
      delete second.avaliacaoId; delete second.avaliacaoFichaId;
      students.push(second); localStorage.setItem('treinoAlunos', JSON.stringify(students));
    }""")
    page.reload()
    page.locator('#searchName').fill('Maria treino 2')
    page.locator('#obsIconBtn').click()
    page.locator('#toggleInfoRelevanteBtn').click()
    page.locator('#openEvaluationBtn').click()
    expect(page.locator('#mergeEvaluationDialog')).to_be_visible()
    page.locator('#mergeEvaluationSelect').select_option('100')
    expect(page.locator('#confirmMergeEvaluation')).to_be_disabled()
    record_before = page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0]")
    assert 'student-merge-2' not in record_before['treinoStudentIds']
    page.locator('#confirmSamePerson').check()
    page.locator('#confirmMergeEvaluation').click()
    expect(frame.locator('[id^="peso-input-"]')).to_have_value('63')
    frame.locator('[id^="peso-input-"]').fill('64')
    frame.locator('[id^="peso-input-"]').press('Tab')
    expect(page.locator('#infoPeso')).to_have_value('64')
    students = page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
    assert [s['nome'] for s in students] == ['Maria do treino','Maria treino 2']
    assert students[0]['treino']['A'] == ['Supino 4x8']
    assert students[1]['treino']['A'] == ['Remada 3x12']
    assert all(s['infoRelevante']['peso'] == '64' for s in students)
    record = page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0]")
    assert set(record['treinoStudentIds']) == {'student-merge','student-merge-2'}
    assert len(page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")) == 1
    assert not errors, errors
    print('PASS: explicit identity confirmation, no automatic link, two workouts for one person, separate names and exercises, shared assessment and ficha')
    browser.close()
