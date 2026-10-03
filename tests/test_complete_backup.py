import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2] if Path(__file__).parent.parent.name == 'treino36' else Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1280, 'height':900}, accept_downloads=True)
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
      localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'t1',nome:'Cliente treino 1',whatsapp:'86999999999',treino:{A:['Agachamento 3x10']},titulos:{A:'A. Pernas'},avaliacaoId:10,avaliacaoFichaId:'f1',infoGuias:[{id:'f1',idade:'30',peso:'70',altura:'1.70',whats:'86999999999'}],obsGuias:[{id:'o1',texto:'Cuidados com joelho'}],historicoTreinos:[{workout_id:'old1',name:'Treino anterior',treino:{A:['Supino 4x8']},titulos:{A:'A. Superior'}}]}]));
      localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Cliente completo',whatsapp:'86999999999',idade:'30',altura:'1.70',sexo:'M',treinoStudentId:'t1',treinoStudentIds:['t1'],avaliacoes:[{id:11,data:'03/10/2026',peso:'70',protocolo:'jp7',triceps:'10',axilar:'11',torax:'12',abdominal:'13',suprailiaca:'14',subescapular:'15',pregaCoxa:'16',cintura:'80',quadril:'100',fotoF:'data:image/png;base64,aGVsbG8=',motivo:'Objetivo salvo',resumo:'Postura salva'}]}]));
      localStorage.setItem('treinoMobilidades',JSON.stringify([{id:'m1',nome:'Mobilidade',texto:'Mobilidade de quadril'}]));localStorage.setItem('avaliacao_notificacoes_ativas','1');
    }""")
    page.reload(); page.locator('#moreOptions > summary').click()
    with page.expect_download() as result:page.locator('#exportBtn').click()
    backup=json.loads(Path(result.value.path()).read_text())
    assert backup['tipo']=='treino36-completo' and backup['schema_version']=='3.0'
    assert backup['avaliacoes'][0]['avaliacoes'][0]['fotoF']=='data:image/png;base64,aGVsbG8='
    assert backup['avaliacoes'][0]['avaliacoes'][0]['pregaCoxa']=='16'
    assert backup['alunos'][0]['obsGuias'][0]['texto']=='Cuidados com joelho'
    assert backup['alunos'][0]['historicoTreinos'][0]['treino']['A']==['Supino 4x8']
    assert backup['preferencias']['notificacoes_avaliacao'] is True
    # Restore into an empty browser and confirm the paired records in the preview.
    page.close();page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)));page.goto('http://app.test/treino36/')
    page.evaluate("""() => {localStorage.setItem('treinoAlunos','[]');localStorage.setItem('avaliacao_fisica_alunos','[]');localStorage.setItem('treinoMobilidades','[]');localStorage.setItem('avaliacao_notificacoes_ativas','0');}""")
    page.reload();page.locator('#moreOptions > summary').click()
    with page.expect_file_chooser() as chooser:page.locator('#importBtn').click()
    chooser.value.set_files({'name':'backup.json','mimeType':'application/json','buffer':json.dumps(backup).encode()})
    expect(page.locator('#completeBackupImportDialog')).to_be_visible()
    assert page.evaluate("localStorage.getItem('avaliacao_fisica_alunos')")=='[]'
    page.locator('#confirmCompleteBackupImport').click()
    records=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")
    students=page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
    assert records[0]['treinoStudentIds']==['t1'] and students[0]['avaliacaoId']==10
    assert records[0]['avaliacoes'][0]['fotoF']=='data:image/png;base64,aGVsbG8='
    assert students[0]['treino']['A']==['Agachamento 3x10'] and students[0]['historicoTreinos'][0]['treino']['A']==['Supino 4x8']
    assert page.evaluate("localStorage.getItem('avaliacao_notificacoes_ativas')")=='1'
    assert page.evaluate("JSON.parse(localStorage.getItem('treinoMobilidades')).some(item=>item.id==='m1')")
    # Assessment-only JSON remains independent of workouts.
    before=page.evaluate("localStorage.getItem('treinoAlunos')")
    if not page.locator('#moreOptions').evaluate('el=>el.open'):page.locator('#moreOptions > summary').click()
    with page.expect_file_chooser() as chooser:page.locator('#importBtn').click()
    chooser.value.set_files({'name':'avaliacoes.json','mimeType':'application/json','buffer':json.dumps({'tipo':'avaliacoes','alunos':backup['avaliacoes']}).encode()})
    expect(page.locator('.assessment-import-dialog')).to_be_visible();page.locator('.import-cancel').click()
    assert page.evaluate("localStorage.getItem('treinoAlunos')")==before
    # A foreign link is rejected before any dataset is changed.
    invalid=json.loads(json.dumps(backup));invalid['avaliacoes'][0]['treinoStudentIds']=['not-in-backup'];invalid['avaliacoes'][0]['treinoStudentId']='not-in-backup'
    with page.expect_file_chooser() as chooser:page.locator('#importBtn').click()
    chooser.value.set_files({'name':'invalid.json','mimeType':'application/json','buffer':json.dumps(invalid).encode()})
    expect(page.locator('#completeBackupImportDialog')).not_to_be_visible()
    assert page.evaluate("localStorage.getItem('treinoAlunos')")==before
    assert not errors,errors
    browser.close()
    print('PASS: complete JSON backup/restore with workouts, observations, assessment fields/photos/history, confirmed links and preferences; assessment-only import and invalid-link rejection')
