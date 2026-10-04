import base64
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import fitz
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[2]
urls=['https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js','https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js','https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js']
scripts={url:urllib.request.urlopen(url,timeout=30).read() for url in urls}
# Observe the browser handoff without delegating PDF rendering to headless Chromium.
# Real generators produce PDFs, which are parsed below; source pages stay open.
spy="""(() => {
 window.pdfWindows=[];window.pdfBlobs=new Map();
 const create=URL.createObjectURL.bind(URL);URL.createObjectURL=blob=>{const url=create(blob);pdfBlobs.set(url,blob);return url;};
 window.open=()=>{const viewer={closed:false,document:{title:'',body:{textContent:''}},location:{replace(url){viewer.url=url;}},close(){this.closed=true;}};pdfWindows.push(viewer);return viewer;};
})()"""
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':390,'height':844},user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1')
    context.add_init_script(spy)
    def route(r):
        if r.request.url in scripts:r.fulfill(body=scripts[r.request.url],content_type='application/javascript');return
        u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
        if path.is_dir():path/='index.html'
        if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
        else:r.fulfill(status=404,body='')
    context.route('**/*',route)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://app.test/treino36/')
    page.evaluate("""() => {localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'b',nome:'Bruno',treino:{A:['Supino 3x10']}},{student_id:'a',nome:'Ana',treino:{A:['Agachamento 3x10']},avaliacaoId:10,infoGuias:[{id:'1',titulo:'Ficha 1',peso:'72',altura:'1.7'}]}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',altura:'1.7',treinoStudentIds:['a'],avaliacoes:[{id:11,data:'04/10/2026',peso:'72',peitoral:'95',resumo:'Postura observada'}]}]));}""")
    page.reload();page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="Ana"] .aluno-nome').click()
    origin=page.evaluate('performance.timeOrigin')
    page.locator('#pdfBtn').click();page.locator('#downloadPdfBtn').click()
    page.wait_for_function('pdfWindows.length===1 && pdfWindows[0].url')
    assert page.evaluate('performance.timeOrigin')==origin
    expect(page.locator('#searchName')).to_have_value('Ana')
    assert page.evaluate("localStorage.getItem('treinoAlunoSelecionado')")=='Ana'
    training=page.evaluate("async()=>{const b=pdfBlobs.get(pdfWindows[0].url);return {type:b.type,data:btoa(String.fromCharCode(...new Uint8Array(await b.arrayBuffer())))};}")
    assert training['type']=='application/pdf'
    with fitz.open(stream=base64.b64decode(training['data']),filetype='pdf') as doc:
        assert doc.page_count>=1 and any('youtube' in a.get('uri','') for p in doc for a in p.get_links())
    page.locator('#closePdfViewer').click();page.locator('#studentEvaluationBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click()
    expect(page.locator('#obs-av-peso')).to_have_value('72')
    engine=next(f for f in page.frames if 'treino36-engine' in f.url)
    for index,kind in enumerate(['pdf','postural'],start=2):
        page.locator('#obsAssessment-'+kind).click()
        page.wait_for_function(f'pdfWindows.length==={index} && pdfWindows[{index-1}].url')
        # Reserved synchronously by the parent, never inside the hidden engine.
        assert engine.evaluate('pdfWindows.length')==0
        expect(page.locator('#searchName')).to_have_value('Ana');expect(page.locator('#obsNativeAssessment')).to_be_visible();expect(page.locator('#obsAssessmentHistory')).to_have_value('11')
        data=engine.evaluate("async()=>{const b=[...pdfBlobs.values()].at(-1);return {type:b.type,data:btoa(String.fromCharCode(...new Uint8Array(await b.arrayBuffer())))};}")
        assert data['type']=='application/pdf'
        with fitz.open(stream=base64.b64decode(data['data']),filetype='pdf') as doc:
            text=' '.join(p.get_text() for p in doc);assert 'Ana' in text and '04/10/2026' in text
            assert ('Postura observada' if kind=='postural' else '72') in text
    page.locator('#workoutObsDialog [data-close]').click();page.locator('#assessmentsLibraryBtn').click()
    expect(page.frame_locator('#assessmentLibraryFrame').locator('.aluno-nome')).to_have_text('Ana')
    library=next(f for f in page.frames if 'treino36-library' in f.url)
    library.locator('.aluno-nome').click();expect(library.locator('[data-aluno-card="10"]')).to_have_class('aluno-card active')
    library.locator('.btn-pdf-aluno').click();library.locator('.assessment-pdf-generate').click()
    library.wait_for_function('pdfWindows.length===1 && pdfWindows[0].url')
    expect(library.locator('[data-aluno-card="10"]')).to_have_class('aluno-card active');expect(page.locator('#searchName')).to_have_value('Ana')
    library.goto(library.url);expect(library.locator('[data-aluno-card="10"]')).to_have_class('aluno-card active')
    page.reload();expect(page.locator('#searchName')).to_have_value('Ana')
    assert not errors,errors
    browser.close();print('PASS: real training/evaluation/postural PDFs handed to inline application/pdf viewer; no source navigation; OBS person/history retained; library and workout selection survive reload; training YouTube links retained')
