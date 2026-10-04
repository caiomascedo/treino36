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
    context = browser.new_context(viewport={'width':320, 'height':844})
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
      localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento 3x10']},avaliacaoId:10,infoGuias:[{id:'f1',idade:'24',altura:'1.70',peso:'72'}],historicoTreinos:[{workout_id:'old-a',name:'Ana antigo',treino:{A:['Agachamento 2x10']},titulos:{A:'A'}}]},{student_id:'b',nome:'Bruno',treino:{A:['Supino 3x10']}},{student_id:'c',nome:'Caio',treino:{A:['Remada 3x12']},arquivadoNaLista:true}]));
      localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',idade:'24',altura:'1.70',treinoStudentIds:['a'],pagamentoTipo:'2x',pagamentoData1:'11/07/2026',pagamentoData2:'11/08/2026',avaliacoes:[{id:11,data:'11/07/2026',peso:'72',imc:'24.9',peitoral:'95',cintura:'80',quadril:'98',triceps:'10',axilar:'11',torax:'12',abdominal:'13',suprailiaca:'14',subescapular:'15',pregaCoxa:'16',protocolo:'jp7'}]}]));
    }""")
    page.reload();page.locator('#searchName').fill('Ana');page.locator('#studentEvaluationBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click()
    expect(page.locator('#obs-av-peso')).to_have_value('72')
    page.locator('[data-metric="imc"]').click()
    legend=page.locator('.obs-metric-detail:not([hidden]) .gauge-legend-item')
    expect(legend).to_have_count(4)
    bounds=legend.evaluate_all('(els)=>els.map(el=>({height:el.getBoundingClientRect().height,scroll:el.scrollWidth,width:el.clientWidth}))')
    assert all(x['height']<32 and x['scroll']<=x['width']+1 for x in bounds),bounds
    bounds=page.locator('#obsAssessmentDate').bounding_box();parent=page.locator('#obsNativeAssessment').bounding_box();assert bounds['x']+bounds['width']<=parent['x']+parent['width']
    # A background context change must not redirect an open assessment to another pupil.
    page.evaluate("document.getElementById('searchName').value='Bruno'")
    background=context.new_page();background.goto('http://app.test/treino36/')
    background.evaluate("localStorage.setItem('treinoAlunos',localStorage.getItem('treinoAlunos')+' ')")
    page.locator('#obsAssessmentSections [data-assessment-section="medidas"]').click()
    expect(page.locator('#obs-av-peitoral')).to_have_value('95')
    page.locator('#obs-av-peitoral').fill('96')
    records=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")
    assert records[0]['nome']=='Ana' and records[0]['avaliacoes'][0]['peitoral']=='96'
    # File reading can finish after the user has opened a different pupil.
    page.locator('#obsAssessmentSections [data-assessment-section="fotos"]').click()
    page.evaluate("""() => { const read=FileReader.prototype.readAsDataURL; FileReader.prototype.readAsDataURL=function(file){setTimeout(()=>read.call(this,file),800)}; }""")
    page.locator('#obs-av-fotoF').set_input_files({'name':'ana.svg','mimeType':'image/svg+xml','buffer':b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>'})
    page.locator('#workoutObsDialog [data-close]').click()
    page.locator('#searchName').fill('Bruno');page.locator('#studentEvaluationBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click()
    expect(page.locator('#obs-av-peso')).to_be_visible()
    page.wait_for_function("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos')).find(a=>a.id===10).avaliacoes[0].fotoF")
    records=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")
    assert not any(av.get('fotoF') for r in records if r['nome']=='Bruno' for av in r['avaliacoes'])
    page.locator('#workoutObsDialog [data-close]').click();background.close()
    page.evaluate("document.getElementById('searchName').value='Ana'");page.locator('#listBtn').click()

    expect(page.locator('.aluno-list-item')).to_have_count(2)
    page.locator('.aluno-list-item[data-nome="Ana"] .archive-aluno-btn').click()
    expect(page.locator('.aluno-list-item')).to_have_count(1)
    students=page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
    assert len(students)==3 and students[0]['treino']['A']==['Agachamento 3x10'] and students[0]['historicoTreinos'][0]['treino']['A']==['Agachamento 2x10']
    page.locator('#selectAllListStudents').check();expect(page.locator('.lista-select-student:checked')).to_have_count(1)
    page.locator('#includeArchivedListStudents').check();expect(page.locator('.aluno-list-item')).to_have_count(3)
    page.locator('#selectAllListStudents').check();expect(page.locator('.lista-select-student:checked')).to_have_count(3)
    page.locator('#restoreSelectedListStudents').click();assert all(not a.get('arquivadoNaLista') for a in page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))"))
    page.locator('.aluno-list-item[data-nome="Ana"] .archive-aluno-btn').click();page.locator('#includeArchivedListStudents').uncheck();expect(page.locator('.aluno-list-item')).to_have_count(2)
    page.locator('#closeModalBtn').click();page.locator('#historyWorkoutBtn').click()
    page.locator('#historyWorkoutSearchInput').fill('Ana antigo');page.locator('#historyStudentClearBtn').click()
    expect(page.locator('#historyStudentSearch')).to_have_value('');expect(page.locator('#historyWorkoutSearchInput')).to_have_value('')
    page.locator('#historyStudentSearch').fill('Bruno');page.locator('#historyStudentSuggestions .history-suggestion-item').first.click();expect(page.locator('#historyStudentSearch')).to_have_value('Bruno')
    page.locator('#workoutHistoryDialog [data-close]').click();page.locator('#compareWorkoutBtn').click()
    expect(page.locator('#compareSearchClearBtn')).to_be_visible();page.locator('#compareSearchInput').fill('Bruno');page.locator('#compareSearchClearBtn').click();expect(page.locator('#compareSearchInput')).to_have_value('')
    page.locator('#compareWorkoutsDialog [data-close]').click()
    page.locator('#assessmentsLibraryBtn').click();library=page.frame_locator('#assessmentLibraryFrame');library.locator('.aluno-nome',has_text='Ana').click()
    library.locator('.aluno-content > .assessment-tabs [data-section="cadastro"]').click()
    charge=library.locator('#pagamento-content-10');parent=charge.bounding_box()
    for locator in [charge.locator('select'),charge.locator('input[type="date"]').first,charge.locator('.btn-limpar-data').first]:
        bounds=locator.bounding_box();assert bounds['x']+bounds['width']<=parent['x']+parent['width']+1,(bounds,parent)
    library.locator('.aluno-content > .assessment-tabs [data-section="avaliacoes"]').click();library.locator('.av-header').click();library.locator('.av-content > .assessment-tabs [data-section="dobras"]').click()
    library.locator('.preview-item .preview-value',has_text='0.82').click()
    legend=library.locator('.gauge-panel.show .gauge-legend-item');expect(legend).to_have_count(3)
    assert all(x<32 for x in legend.evaluate_all('(els)=>els.map(el=>el.getBoundingClientRect().height)'))
    with tempfile.TemporaryDirectory() as tmp:
        for mode,expected,excluded in [('medidas-dobras','DOBRAS CUTÂNEAS','COMPOSIÇÃO CORPORAL'),('medidas-composicao','COMPOSIÇÃO CORPORAL','DOBRAS CUTÂNEAS')]:
            library.locator('.btn-pdf-aluno').first.click();library.locator('.assessment-pdf-mode').select_option(mode)
            with page.expect_download() as download:library.locator('.assessment-pdf-generate').click()
            path=Path(tmp)/(mode+'.pdf');download.value.save_as(path);text=' '.join(p.get_text() for p in fitz.open(path))
            assert expected in text and excluded not in text and 'MEDIDAS CORPORAIS' in text,text
    page.locator('#expandAssessmentLibraryBtn').click();bounds=page.locator('#assessmentLibraryDialog').bounding_box();assert bounds['width']>=319 and bounds['height']>=843,bounds
    page.screenshot(path=str(Path(__file__).parent/'library-full-mobile.png'),full_page=True)
    assert not errors,errors
    browser.close();print('PASS: archive/restore and select-all scope preserve workouts; fast clear searches; whole legends/dates/payment fields; library selective PDFs and full window')
