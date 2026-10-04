import json
import urllib.request
import tempfile
import fitz
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2] if Path(__file__).parent.parent.name == 'treino36' else Path(__file__).resolve().parents[1]
LIBS=['https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js','https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js']
scripts={url:urllib.request.urlopen(url,timeout=30).read() for url in LIBS}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':390, 'height':844})
    def route(request):
        if request.request.url in scripts:
            request.fulfill(body=scripts[request.request.url],content_type='application/javascript');return
        url = urlparse(request.request.url)
        if url.hostname == 'app.test':
            path = ROOT / url.path.strip('/')
            if path.is_dir(): path /= 'index.html'
            if path.is_file():
                request.fulfill(body=path.read_bytes(), content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
                return
        request.fulfill(status=404, body='')
    context.route('**/*', route)
    context.add_init_script('window.open=()=>null')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://app.test/treino36/')
    page.evaluate("""() => {
      localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana Vitória treino 1',treino:{A:['Agachamento 3x10']},avaliacaoId:10,infoGuias:[{id:'f1',peso:'73',altura:'1.63',idade:'24',dataNasc:'26/03/2002'}]}]));
      localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana Vitória',sexo:'F',altura:'1.63',idade:'24',nasc:'26/03/2002',pesoAtual:'73',treinoStudentIds:['ana'],avaliacoes:[{id:11,data:'11/07/2026',peso:'74.50',cintura:'80',protocolo:'jp7'}]}]));
    }""")
    page.reload();page.locator('#searchName').fill('Ana Vitória treino 1');page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click()
    page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click()
    expect(page.locator('#obs-av-peso')).to_have_value('74.50')
    expect(page.locator('#fichaAssessmentDate')).to_have_text('Avaliação: 11/07/2026')
    expect(page.locator('#trainingEvaluationPanel')).not_to_be_visible()
    expect(page.locator('#trainingEvaluationFrame')).not_to_be_visible()
    page.locator('#obsNewAssessment').click();expect(page.locator('#obs-av-peso')).to_have_value('73')
    page.locator('#obsAssessmentDate').fill('2026-10-02')
    page.locator('#obs-av-peso').fill('72')
    expect(page.locator('#obs-av-imc')).to_have_value('27.1')
    page.locator('#obsAssessmentSections [data-assessment-section="medidas"]').click()
    page.locator('#obs-av-biceps').fill('32 31');expect(page.locator('#obs-av-biceps')).to_have_value('32 / 31')
    page.locator('#obs-av-cintura').fill('78');page.locator('#obs-av-quadril').fill('98')
    page.locator('#obsAssessmentSections [data-assessment-section="dobras"]').click()
    for key,value in {'triceps':'10','axilar':'11','torax':'12','abdominal':'13','suprailiaca':'14','subescapular':'15','pregaCoxa':'16'}.items():page.locator('#obs-av-'+key).fill(value)
    expect(page.locator('.obs-skinfold-results')).to_contain_text('91')
    page.locator('#obsAssessmentSections [data-assessment-section="fotos"]').click()
    photo=bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')
    page.locator('#obs-av-fotoF').set_input_files({'name':'foto.png','mimeType':'image/png','buffer':photo})
    expect(page.locator('.obs-assessment-photo img').first).to_be_visible()
    page.locator('#obs-av-resumo').fill('Postura registrada nas Obs')
    page.locator('#obsAssessment-save').click()
    state=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0]")
    assert len(state['avaliacoes'])==2 and state['avaliacoes'][0]['peso']=='74.50' and state['avaliacoes'][0]['data']=='11/07/2026'
    latest=state['avaliacoes'][1];assert latest['data']=='02/10/2026' and latest['peso']=='72' and latest['biceps']=='32 / 31' and latest['_dobras']['soma']==91 and latest['fotoF'].startswith('data:image/')
    # The actual PDF generators download files without opening the assessment screen.
    with tempfile.TemporaryDirectory() as tmp:
        for kind in ['pdf','postural']:
            with page.expect_download() as download:page.locator('#obsAssessment-'+kind).click()
            path=Path(tmp)/(kind+'.pdf');download.value.save_as(path)
            doc=fitz.open(path);text=' '.join(p.get_text() for p in doc)
            assert 'Ana' in text and '02/10/2026' in text,(kind,text)
            if kind=='postural':assert 'Postura registrada nas Obs' in text,text
            else:assert '72' in text and '74.50' in text,text
            assert doc.page_count>=1
    expect(page.locator('#assessmentLibraryDialog')).not_to_be_visible()
    # Selective PDFs omit excluded sections and automatic PDFs omit empty sections.
    with tempfile.TemporaryDirectory() as tmp:
        for mode,expected,excluded in [('medidas-dobras','DOBRAS CUTÂNEAS','COMPOSIÇÃO CORPORAL'),('medidas-composicao','COMPOSIÇÃO CORPORAL','DOBRAS CUTÂNEAS')]:
            page.locator('#obsAssessmentPdfMode').select_option(mode)
            with page.expect_download() as download:page.locator('#obsAssessment-pdf').click()
            path=Path(tmp)/(mode+'.pdf');download.value.save_as(path);doc=fitz.open(path);text=' '.join(p.get_text() for p in doc)
            assert expected in text and excluded not in text and 'MEDIDAS CORPORAIS' in text,text
        with page.expect_download() as download:
            page.evaluate("""async()=>{const w=[...document.querySelectorAll('iframe')].map(f=>f.contentWindow).find(w=>w.TreinoAssessmentEngine);await w.TreinoAssessmentEngine.pdf([{id:20,nome:'Somente medidas',avaliacoes:[{id:21,data:'03/10/2026',peitoral:'95',protocolo:'jp7'}]}],20,'pdf',{mode:'auto'});}""")
        path=Path(tmp)/'auto.pdf';download.value.save_as(path);text=' '.join(p.get_text() for p in fitz.open(path))
        assert 'MEDIDAS CORPORAIS' in text and 'COMPOSIÇÃO CORPORAL' not in text and 'DOBRAS CUTÂNEAS' not in text and 'Cintura' not in text,text
    # Each requested group is a single row and dates no longer occupy a tall field.
    for selector in ['#infoQuickActions','#treinoLevelSelector']:
        rects=page.locator(selector+' button').evaluate_all('(buttons)=>buttons.map(b=>b.getBoundingClientRect().top)')
        assert max(rects)-min(rects)<2,(selector,rects)
    assert page.locator('#obsAssessmentHistory').bounding_box()['height']<=34
    assert page.locator('#obsAssessmentDate').bounding_box()['height']<=34
    page.locator('#expandObsBtn').click()
    box=page.locator('#workoutObsDialog').bounding_box();assert box['width']>=389 and box['height']>=843,box
    expect(page.locator('#infoQuickActions')).not_to_be_visible();expect(page.locator('#obsTextarea')).not_to_be_visible()
    expect(page.locator('#obsNativeAssessment')).to_be_visible();expect(page.locator('#closeObsFocusBtn')).to_be_visible()
    assert page.locator('#obsAssessmentSections').bounding_box()['y']<100
    page.screenshot(path=str(Path(__file__).parent/'obs-focus-mobile.png'),full_page=True)
    page.locator('#expandObsBtn').click();expect(page.locator('#infoQuickActions')).to_be_visible()
    page.locator('#saveObsBtn').click();page.locator('#assessmentsLibraryBtn').click()
    library=page.frame_locator('#assessmentLibraryFrame');library.locator('.aluno-nome').click()
    library.locator('#av-item-'+str(latest['id'])+' .av-header').click()
    expect(library.locator('#peso-input-10-'+str(latest['id']))).to_have_value('72')
    library.locator('#peso-input-10-'+str(latest['id'])).fill('71');library.locator('#peso-input-10-'+str(latest['id'])).press('Tab')
    page.locator('#assessmentLibraryDialog [data-close]').click();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click()
    expect(page.locator('#obs-av-peso')).to_have_value('71')
    page.locator('#obsAssessmentHistory').select_option('11');expect(page.locator('#obs-av-peso')).to_have_value('74.50')
    page.locator('#obsAssessmentSections [data-assessment-section="medidas"]').click()
    expect(page.locator('#obsAssessmentHistory')).to_have_value('11')
    expect(page.locator('#obs-av-cintura')).to_have_value('80')
    page.locator('#obs-av-cintura').fill('79')
    page.locator('#infoPeso').fill('75');page.locator('#infoPeso').press('Tab')
    state=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0]")
    assert state['avaliacoes'][0]['peso']=='74.50' and state['avaliacoes'][1]['peso']=='75',state
    assert state['avaliacoes'][0]['cintura']=='79' and state['avaliacoes'][1]['cintura']=='78'
    assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].treino.A[0]")=='Agachamento 3x10'
    page.locator('#workoutObsDialog [data-close]').click();page.locator('#studentEvaluationBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click()
    expect(page.locator('#obs-av-peso')).to_have_value('75')
    expect(page.locator('#infoPeso')).to_have_value('75')
    expect(page.locator('#fichaAssessmentDate')).to_have_text('Avaliação: 02/10/2026')
    assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].infoGuias.at(-1).avaliacaoOrigemData")=='02/10/2026'
    expect(page.locator('#obsContent')).not_to_be_visible()
    expect(page.locator('#mergeEvaluationDialog')).not_to_be_visible()
    assert not errors,errors
    page.screenshot(path=str(Path(__file__).parent/'obs-native-mobile.png'),full_page=True)
    browser.close();print('PASS: native Obs fields, dated history, D/E formatting, calculations, photos, PDF actions and bidirectional library edits; no visible evaluation iframe')
