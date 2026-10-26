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
 context.add_init_script('''window.copied=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>copied.push(text)}});window.pdfWindows=[];window.pdfBlobs=new Map();const create=URL.createObjectURL.bind(URL);URL.createObjectURL=blob=>{const url=create(blob);pdfBlobs.set(url,blob);return url;};window.open=()=>{const viewer={closed:false,document:{title:'',body:{textContent:''}},location:{replace(url){viewer.url=url}},close(){this.closed=true}};pdfWindows.push(viewer);return viewer;};''')
 def route(r):
  if r.request.url==url:r.fulfill(body=cache.read_bytes(),content_type='application/javascript');return
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='review.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://review.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate('''()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'one',nome:'Exemplo',whatsapp:'+55 (55) 99999-8888',treino:{A:['Agachamento Livre — 3×12','Leg Press 45° — 3×15'],B:['Remada — 3×12']},titulos:{A:'A. Quadríceps',B:'B. Costas'}}]))''')
 page.reload();page.locator('#pdfBtn').click();expect(page.locator('#pdfBody .yt-link')).to_have_count(3)
 assert page.locator('#pdfBody .yt-link').all_text_contents()==['(Vídeo)']*3
 assert not page.locator('#pdfReviewTools details').evaluate('el=>el.open')
 first=page.locator('#pdfBody .pdf-ex-row').first
 initial_href=first.locator('a').get_attribute('href');assert 'youtube.com/results' in parse_qs(urlparse(initial_href).query)['url'][0]
 before=page.evaluate("localStorage.getItem('treinoAlunos')")
 page.get_by_role('button',name='Editar texto',exact=True).click();first.locator('.pdf-ex-title').fill('Agachamento no Smith');first.locator('.pdf-ex-details').fill('— 4×15')
 assert 'Agachamento no Smith' in parse_qs(urlparse(first.locator('a').get_attribute('href')).query)['ex'][0]
 page.locator('#pdfReviewTools summary').click();choice=page.locator('.pdf-video-choice').first
 choice.locator('input').fill('javascript:alert(1)');page.locator('#downloadPdfBtn').click();assert page.evaluate('pdfWindows.length')==0
 expect(page.locator('#pdfReviewTools [role=status]')).to_contain_text('http ou https')
 choice.get_by_role('button',name='Automático',exact=True).click();expect(choice.locator('input')).to_have_value('')
 custom='https://www.youtube.com/watch?v=12345678901';choice.locator('input').fill(custom)
 assert parse_qs(urlparse(first.locator('a').get_attribute('href')).query)['url']==[custom]
 page.screenshot(path='/tmp/pdf-review-mobile.png')
 page.locator('#downloadPdfBtn').click();page.wait_for_function('pdfWindows.length===1&&pdfWindows[0].url',timeout=30000)
 assert not page.locator('#pdfBody').evaluate("el=>el.classList.contains('pdf-is-editing')")
 result=page.evaluate("async()=>{const blob=pdfBlobs.get(pdfWindows[0].url),bytes=new Uint8Array(await blob.arrayBuffer());let value='';for(const byte of bytes)value+=String.fromCharCode(byte);return btoa(value);}")
 with fitz.open(stream=base64.b64decode(result),filetype='pdf') as doc:
  links=[link.get('uri','') for pdfpage in doc for link in pdfpage.get_links()]
  assert any(parse_qs(urlparse(link).query).get('url')==[custom] for link in links),links
  assert sum('r/yt?' in link for link in links)>=3
 assert page.evaluate("localStorage.getItem('treinoAlunos')")==before
 page.locator('#closePdfViewer').click();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click()
 phone=page.locator('#infoWhats');phone.fill('+55 (55) 99999-8888');page.get_by_role('button',name='Copiar WhatsApp sem 55',exact=True).click();page.wait_for_function("copied.at(-1)==='55999998888'");expect(phone).to_have_value('+55 (55) 99999-8888')
 for number,expected in [('+55 (11) 98888-7777','11988887777'),('005511988887777','11988887777'),('(55) 99999-8888','55999998888'),('5533334444','5533334444'),('', '')]:
  assert page.evaluate('(value)=>WhatsAppCopy.localNumber(value)',number)==expected
 assert not errors,errors
 browser.close();print('PASS: automatic inline video labels, optional plain-text PDF draft edits, URL validation/reset, actual clickable PDF annotations, unchanged saved workout and Brazil-only WhatsApp copy')
