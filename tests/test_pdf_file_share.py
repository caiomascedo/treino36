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
 window.fileShares=[];Object.defineProperty(navigator,'canShare',{configurable:true,value:data=>!!data.files?.length});Object.defineProperty(navigator,'userActivation',{configurable:true,value:{get isActive(){return !window.forceInactive;}}});Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{if(window.shareError){const error=new Error(window.shareError);error.name=window.shareError;throw error;}fileShares.push(data);}});
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
    def pdf_data(frame,index):
        return frame.evaluate("""async index=>{const file=fileShares[index].files[0];const data=await new Promise(resolve=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.readAsDataURL(file);});return {data,name:file.name,type:file.type,keys:Object.keys(fileShares[index])};}""",index)
    def share_preview(frame):
        expect(frame.locator('.pdf-inline-document')).to_have_attribute('src',__import__('re').compile('^blob:'))
        expect(frame.locator('.pdf-file-send')).to_be_enabled()
        assert frame.locator('.pdf-direct-preview').inner_text().find('Enviar PDF')==-1
        assert frame.locator('.pdf-inline-document').evaluate("async el=>(await (await fetch(el.src)).blob()).type")=='application/pdf'
        frame.locator('.pdf-file-send').click()
        frame.locator('.pdf-file-close').click()
    # Generation shows the document first. Sharing requires only the toolbar icon.
    page.locator('#pdfBtn').click();assert page.locator('#sharePdfBtn').count()==0;page.locator('#downloadPdfBtn').click()
    assert page.evaluate('fileShares.length')==0;share_preview(page)
    page.wait_for_function('fileShares.length===1');expect(page.locator('.pdf-file-share')).to_have_count(0)
    data=pdf_data(page,0);assert data['keys']==['files'] and data['name']=='treino_Ana.pdf' and data['type']=='application/pdf'
    with fitz.open(stream=base64.b64decode(data['data']),filetype='pdf') as doc:
        assert any('youtube' in a.get('uri','') for p in doc for a in p.get_links())
    assert page.evaluate('pdfWindows.length')==0 and page.evaluate('performance.timeOrigin')==origin
    expect(page.locator('#searchName')).to_have_value('Ana');page.locator('#closePdfViewer').click()
    page.locator('#studentEvaluationBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click()
    expect(page.locator('#obs-av-peso')).to_have_value('72')
    engine=next(f for f in page.frames if 'treino36-engine' in f.url)
    for index,kind in enumerate(['pdf','postural'],start=2):
        page.locator('#obsAssessment-'+kind).click();share_preview(page);page.wait_for_function(f'fileShares.length==={index}');expect(page.locator('.pdf-file-share')).to_have_count(0)
        data=pdf_data(page,index-1);assert data['keys']==['files'] and data['type']=='application/pdf'
        with fitz.open(stream=base64.b64decode(data['data']),filetype='pdf') as doc:
            text=' '.join(p.get_text() for p in doc);assert 'Ana' in text and ('Postura observada' if kind=='postural' else '72') in text
        assert engine.evaluate('pdfWindows.length')==0 and engine.locator('.pdf-file-share').count()==0
        expect(page.locator('#searchName')).to_have_value('Ana');expect(page.locator('#obsAssessmentHistory')).to_have_value('11')
    page.locator('#workoutObsDialog [data-close]').click();page.locator('#assessmentsLibraryBtn').click()
    expect(page.frame_locator('#assessmentLibraryFrame').locator('.aluno-nome')).to_have_text('Ana')
    library=next(f for f in page.frames if 'treino36-library' in f.url);library.locator('.aluno-nome').click();library.locator('.btn-pdf-aluno').click();library.locator('.assessment-pdf-generate').click()
    share_preview(library);library.wait_for_function('fileShares.length===1');data=pdf_data(library,0);assert data['keys']==['files'] and data['name']=='Avaliacao_Ana.pdf';assert library.evaluate('pdfWindows.length')==0
    page.locator('#assessmentLibraryDialog [data-close]').click()
    # Sharing cancellation keeps the prepared document visible for retry.
    page.evaluate("window.forceInactive=true;window.shareError='AbortError'")
    page.locator('#pdfBtn').click();page.locator('#downloadPdfBtn').click();expect(page.locator('.pdf-file-send')).to_be_enabled();assert page.evaluate('fileShares.length')==3
    page.locator('.pdf-file-send').click();expect(page.locator('.pdf-inline-document')).to_be_visible();expect(page.locator('.pdf-file-send')).to_be_enabled()
    page.evaluate("window.shareError='NotAllowedError'");page.locator('.pdf-file-send').click();expect(page.locator('.pdf-file-share-status')).to_contain_text('Tente novamente')
    page.evaluate('window.shareError=null');page.locator('.pdf-file-send').click();page.wait_for_function('fileShares.length===4');expect(page.locator('.pdf-inline-document')).to_be_visible()
    with page.expect_download() as downloaded:page.locator('.pdf-file-save').click()
    assert downloaded.value.suggested_filename=='treino_Ana.pdf'
    page.locator('.pdf-file-close').click()
    assert page.evaluate("""()=>{const target=TreinoPDFViewer.reserve();target.close();TreinoPDFViewer.deliver({output(){throw Error('Should ignore canceled result');}},'cancelado.pdf',target);return target.closed;}""")
    assert not errors,errors
    browser.close();print('PASS: PDF preview shown before sharing; training/evaluation/postural/library actual PDF blobs; toolbar shares files only, no URL/text; name/history retained; native sharing cancellation/retry, download and canceled generation handled')
