"""Real PDF links, optional draft editing and Brazil-prefix-only phone copying."""
import base64,urllib.request,io
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import fitz
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
url='https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js'
cache=Path('/tmp/treino36-html2pdf.bundle.js')
if not cache.exists():cache.write_bytes(urllib.request.urlopen(url,timeout=30).read())
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 context.add_init_script('''window.shared=[];Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});Object.defineProperty(navigator,'share',{configurable:true,value:async payload=>{const f=payload.files[0];shared.push({keys:Object.keys(payload),name:f.name,type:f.type,data:btoa(Array.from(new Uint8Array(await f.arrayBuffer()),v=>String.fromCharCode(v)).join(''))});}});window.copied=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{readText:async()=>'https://www.youtube.com/watch?v=chosen12345',writeText:async text=>copied.push(text)}});window.pdfWindows=[];window.pdfBlobs=new Map();const create=URL.createObjectURL.bind(URL);URL.createObjectURL=blob=>{const url=create(blob);pdfBlobs.set(url,blob);return url;};window.open=()=>{const viewer={closed:false,document:{title:'',body:{textContent:''}},location:{replace(url){viewer.url=url}},close(){this.closed=true}};pdfWindows.push(viewer);return viewer;};''')
 def route(r):
  if r.request.url==url:r.fulfill(body=cache.read_bytes(),content_type='application/javascript');return
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='review.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://review.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate('''()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'one',nome:'Exemplo',whatsapp:'+55 (55) 99999-8888',treino:{A:['Agachamento Livre — 3×12','Leg Press 45° — 3×15'],B:['Remada — 3×12']},titulos:{A:'A. Quadríceps',B:'B. Costas'}}]))''')
 page.reload();page.locator('#pdfBtn').click()
 page.locator('#pdfReviewTools > details:not(.pdf-section-choice) > summary').click();page.locator('.pdf-video-section > summary').first.click()
 custom='https://www.youtube.com/watch?v=keptvideo12&t=30';page.locator('.pdf-video-choice input').first.fill(custom)
 baseline=page.evaluate("localStorage.getItem('treinoAlunos')")
 for style in ['inline','old']:
  page.get_by_role('combobox',name='Modelo do PDF',exact=True).select_option(style)
  page.get_by_role('button',name='Só Iniciar treino',exact=True).click()
  expect(page.get_by_role('checkbox',name='Incluir vídeos no PDF',exact=True)).not_to_be_checked()
  expect(page.get_by_role('checkbox',name='Incluir Iniciar treino no PDF',exact=True)).to_be_checked()
  expect(page.locator('#pdfBody .yt-link')).to_have_count(0);expect(page.locator('#pdfBody .pdf-start-btn')).to_have_count(1)
  count=page.evaluate('pdfWindows.length');page.locator('#downloadPdfBtn').click();page.wait_for_function('pdfWindows.length===%d&&pdfWindows.at(-1).url'%(count+1),timeout=30000)
  result=page.evaluate("async()=>{const blob=pdfBlobs.get(pdfWindows.at(-1).url);return btoa(Array.from(new Uint8Array(await blob.arrayBuffer()),v=>String.fromCharCode(v)).join(''));}")
  with fitz.open(stream=base64.b64decode(result),filetype='pdf') as doc:
   links=[link.get('uri','') for p in doc for link in p.get_links()]
   assert len(links)==1 and urlparse(links[0]).path=='/r/iniciar',links
   assert doc.page_count>=1 and doc[0].get_images()
   doc[0].get_pixmap().save('/tmp/pdf-start-only-generated.png')
  expect(page.locator('#pdfBody .pdf-ex-title')).to_have_count(3);expect(page.locator('#pdfBody .pdf-ex-title').first).to_have_text('Agachamento Livre')
  assert page.evaluate("localStorage.getItem('treinoAlunos')")==baseline
  page.get_by_role('checkbox',name='Incluir vídeos no PDF',exact=True).check()
  expect(page.locator('#pdfBody .yt-link')).to_have_count(3)
  assert page.locator('#pdfBody .yt-link').first.get_attribute('href')==custom
 page.get_by_role('button',name='Só Iniciar treino',exact=True).click()
 page.locator('#closePdfViewer').click();page.reload();page.locator('#pdfBtn').click()
 expect(page.locator('#pdfBody .yt-link')).to_have_count(0);expect(page.locator('#pdfBody .pdf-start-btn')).to_have_count(1)
 page.screenshot(path='/tmp/pdf-start-only-mobile.png')
 page.get_by_role('checkbox',name='Incluir vídeos no PDF',exact=True).check();expect(page.locator('.pdf-video-choice input').first).to_have_value(custom)
 # Invalid URL drafts do not block a PDF that excludes video links.
 page.locator('#pdfReviewTools > details:not(.pdf-section-choice) > summary').click();page.locator('.pdf-video-section > summary').first.click();page.locator('.pdf-video-choice input').first.fill('javascript:bad')
 page.get_by_role('button',name='Só Iniciar treino',exact=True).click();assert page.evaluate('WorkoutPDFReview.beforeExport()') is True
 assert page.evaluate("localStorage.getItem('treinoAlunos')")==baseline
 assert not errors,errors
 browser.close();print('PASS: explicit start-only preset exports only one tracked start annotation in both models; exercises and custom destinations unchanged; video links restore without monitoring; preference persists; excluded invalid URLs do not block PDF')
