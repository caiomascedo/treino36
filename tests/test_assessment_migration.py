"""Execute com os repositórios treino36 e avaliacao em diretórios irmãos.
Requer Playwright, Chromium, PyMuPDF e acesso aos CDNs já usados pelos PDFs.
"""
import json
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect
import fitz

ROOT = Path(__file__).resolve().parents[2]
LIBS = [
    'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js',
]
scripts = {url: urllib.request.urlopen(url, timeout=30).read() for url in LIBS}
errors = []
with sync_playwright() as p, tempfile.TemporaryDirectory() as tmp:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1280, 'height':900}, accept_downloads=True)
    external_assessment_reads = []
    def route(request):
        url = request.request.url
        parsed = urlparse(url)
        if url in scripts:
            request.fulfill(body=scripts[url], content_type='application/javascript', headers={'Access-Control-Allow-Origin':'*'})
            return
        if parsed.hostname == 'app.test':
            path = ROOT / parsed.path.strip('/')
            if path.is_dir(): path /= 'index.html'
            if path.is_file():
                request.fulfill(body=path.read_bytes(), content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
                return
            if parsed.path.startswith('/avaliacao'): external_assessment_reads.append(parsed.path)
        request.fulfill(status=404,body='')
    context.route('**/*', route)
    page = context.new_page(); page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://app.test/treino36/')
    page.evaluate("""() => {
      localStorage.setItem('treinoAlunos', JSON.stringify([{student_id:'t1',nome:'Pessoa treino 1',treino:{A:['Agachamento 3x10']},titulos:{A:'A. Pernas'}}]));
      localStorage.setItem('avaliacao_fisica_alunos', '[]');
    }""")
    page.reload()
    before = page.evaluate("localStorage.getItem('treinoAlunos')")
    payload = [{'id':100,'nome':'Pessoa Migrada','sexo':'F','idade':30,'altura':'1.70','whatsapp':'86999999999','avaliacoes':[{'id':101,'data':'01/09/2026','peso':'70','gordura':'20','protocolo':'jp7','resumo':'Avaliação original'},{'id':102,'data':'01/10/2026','peso':'68','gordura':'19','protocolo':'jp7'}]}]
    page.locator('#moreOptions > summary').click()
    with page.expect_file_chooser() as chooser: page.locator('#importBtn').click()
    chooser.value.set_files({'name':'avaliacoes.json','mimeType':'application/json','buffer':json.dumps(payload).encode()})
    expect(page.locator('.assessment-import-dialog')).to_be_visible()
    assert page.evaluate("localStorage.getItem('treinoAlunos')") == before
    assert page.evaluate("localStorage.getItem('avaliacao_fisica_alunos')") == '[]'
    page.locator('.import-confirm').click()
    assert page.evaluate("localStorage.getItem('treinoAlunos')") == before
    page.locator('#assessmentsLibraryBtn').click()
    library = page.frame_locator('#assessmentLibraryFrame')
    expect(library.locator('.aluno-nome')).to_have_text('Pessoa Migrada')
    library.locator('.aluno-header').click()
    expect(library.locator('.av-item')).to_have_count(2)
    # The complete PDF remains downloadable from the migrated application.
    with page.expect_download() as download: library.locator('.btn-pdf-aluno').click()
    pdf = Path(tmp) / 'avaliacao.pdf'; download.value.save_as(pdf)
    with fitz.open(pdf) as document:
        text = ''.join(p.get_text() for p in document)
        assert 'Pessoa Migrada' in text and 'COMPOSI' in text and '70' in text and '68' in text
    with page.expect_download() as download: library.locator('.btn-postural-aluno').click()
    pdf = Path(tmp) / 'postural.pdf'; download.value.save_as(pdf)
    with fitz.open(pdf) as document: assert len(document) == 2
    # Export contains assessments only; reimporting it does not duplicate records.
    library.locator('.assessment-more-options > summary').click()
    with page.expect_download() as download: library.locator('.btn-export-all').click()
    exported = Path(tmp) / 'avaliacoes.json'; download.value.save_as(exported)
    backup = json.loads(exported.read_text())
    assert backup['tipo'] == 'avaliacoes' and 'treino' not in backup['alunos'][0]
    library.locator('#importFile').set_input_files(str(exported))
    expect(library.locator('.assessment-import-dialog')).to_be_visible()
    library.locator('.import-confirm').click()
    expect(library.locator('.av-item')).to_have_count(2)
    page.locator('#assessmentLibraryDialog [data-close]').click()
    # Link the imported person only after explicit confirmation.
    page.locator('#obsIconBtn').click(); page.locator('#toggleInfoRelevanteBtn').click()
    page.locator('#openEvaluationBtn').click(); page.locator('#mergeEvaluationSelect').select_option('100')
    expect(page.locator('#confirmMergeEvaluation')).to_be_disabled()
    page.locator('#confirmMergeEvaluation').click()
    expect(page.locator('#infoPeso')).to_have_value('68')
    assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].nome") == 'Pessoa treino 1'
    # A new standalone import preserves confirmed links and all older evaluations.
    standalone = context.new_page(); standalone.on('pageerror', lambda error: errors.append(str(error)))
    standalone.goto('http://app.test/avaliacao/')
    update = [{'id':100,'nome':'Pessoa Migrada','avaliacoes':[{'id':103,'data':'03/10/2026','peso':'67','protocolo':'jp7'}]}]
    standalone.locator('#importFile').set_input_files({'name':'novas_avaliacoes.json','mimeType':'application/json','buffer':json.dumps(update).encode()})
    expect(standalone.locator('.assessment-import-dialog')).to_be_visible()
    standalone.locator('.import-confirm').click()
    expect(page.locator('#infoPeso')).to_have_value('67')
    record = page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0]")
    assert record['treinoStudentIds'] == ['t1'] and len(record['avaliacoes']) == 3
    assert record['avaliacoes'][0]['resumo'] == 'Avaliação original'
    # Invalid files and canceling a valid preview leave both stores unchanged.
    snapshot = page.evaluate("[localStorage.getItem('treinoAlunos'),localStorage.getItem('avaliacao_fisica_alunos')]")
    assert page.evaluate("""() => { try { AvaliacoesJSON.prepare([{id:200,nome:'Inválido',avaliacoes:[{}]}], AvaliacoesJSON.read(), false); return false; } catch(e) { return true; } }""")
    page.evaluate('payload => AvaliacoesJSON.preview(payload)', payload)
    page.locator('.import-cancel').click()
    assert page.evaluate("[localStorage.getItem('treinoAlunos'),localStorage.getItem('avaliacao_fisica_alunos')]") == snapshot
    # A workload JSON is not accepted by the assessment-only import.
    assert page.evaluate("() => !AvaliacoesJSON.isAssessmentPayload({alunos:[{nome:'Treino',treino:{A:[]}}]})")
    # Importing an older assessment must not turn it into the latest weight.
    assert page.evaluate("""() => {
      const plan = AvaliacoesJSON.prepare([{id:100,nome:'Pessoa Migrada',avaliacoes:[{id:99,data:'01/08/2026',peso:'80'}]}], AvaliacoesJSON.read(), false);
      return plan.records[0].avaliacoes.at(-1).peso === '67' && plan.records[0].avaliacoes[0].id === 99;
    }""")
    # Imported links are not trusted; only a local confirmed link is retained.
    assert page.evaluate("""() => {
      const plan = AvaliacoesJSON.prepare([{id:200,nome:'Outra pessoa',treinoStudentId:'t1',treinoStudentIds:['t1'],avaliacoes:[]}], AvaliacoesJSON.read(), false);
      return !plan.records.find(a => a.id === 200).treinoStudentId && !plan.records.find(a => a.id === 200).treinoStudentIds;
    }""")
    # Both conflict policies preserve fields absent from the imported file.
    assert page.evaluate("""() => {
      const raw = [{id:100,nome:'Pessoa Migrada',avaliacoes:[{id:101,peso:'71'}]}];
      const current = AvaliacoesJSON.prepare(raw,AvaliacoesJSON.read(),false).records[0].avaliacoes.find(a=>a.id===101);
      const incoming = AvaliacoesJSON.prepare(raw,AvaliacoesJSON.read(),true).records[0].avaliacoes.find(a=>a.id===101);
      return current.peso==='70' && incoming.peso==='71' && incoming.resumo==='Avaliação original';
    }""")
    page.locator('#workoutObsDialog').evaluate('(d) => d.close()')
    page.locator('#pdfBtn').click()
    expect(page.locator('#pdfBody')).to_contain_text('Agachamento')
    with page.expect_download(timeout=30000) as download: page.locator('#downloadPdfBtn').click()
    pdf = Path(tmp) / 'treino.pdf'; download.value.save_as(pdf)
    with fitz.open(pdf) as document:
        assert len(document) > 0
        assert any('youtube.com' in link.get('uri','') for p in document for link in p.get_links())
    assert not errors, errors
    print('PASS: avaliação local completa, importação antiga e nova só de avaliações, sem alterar treinos, prévia/cancelamento, histórico, vínculos e JSON inválido')
    print('PASS: PDFs reais de avaliação, postural e treino com links do YouTube')
    browser.close()
