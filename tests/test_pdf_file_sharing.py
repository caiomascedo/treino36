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
 expect(page.locator('.pdf-section-choice')).not_to_have_attribute('open','')
 assert page.locator('.pdf-section-checks input').count()==2
 assert page.locator('.pdf-section-checks input:checked').count()==2
 page.locator('#pdfReviewTools > details:not(.pdf-section-choice) > summary').click()
 page.locator('.pdf-video-section > summary').first.click()
 page.get_by_role('button',name='Colar link',exact=True).first.click()
 expected='https://www.youtube.com/watch?v=chosen12345'
 expect(page.locator('.pdf-video-choice input').first).to_have_value(expected)
 page.locator('#closePdfViewer').click();page.locator('#pdfBtn').click()
 expect(page.locator('.pdf-video-choice input').first).to_have_value(expected)
 for model in ['inline','old']:
  page.get_by_label('Modelo do PDF',exact=True).select_option(model)
  page.locator('#sendPdfBtn').click();expect(page.locator('#pdfShareReady')).to_be_visible(timeout=30000)
  page.get_by_role('button',name='Compartilhar PDF',exact=True).click()
  page.wait_for_function('shared.length===%d'%(['inline','old'].index(model)+1))
  result=page.evaluate('shared.at(-1)');assert result['keys']==['files'],result
  assert result['name']=='treino_Exemplo.pdf' and result['type']=='application/pdf'
  with fitz.open(stream=base64.b64decode(result['data']),filetype='pdf') as doc:
   links=[link.get('uri','') for p in doc for link in p.get_links()]
   assert any(parse_qs(urlparse(link).query).get('url')==[expected] for link in links)
   assert sum('/r/yt?' in link for link in links)==3
  page.locator('#pdfShareReady').get_by_role('button',name='Fechar',exact=True).click()
 assert page.evaluate('pdfWindows.length')==0
 page.locator('#closePdfViewer').click()
 page.evaluate("""()=>{document.querySelector('.sec-a ol').innerHTML='<li><span class="bold">Supino Especial</span> — 3×12 <a href="https://youtu.be/keptlink123">Vídeo</a></li>';document.querySelector('.sec-b ol').innerHTML='<li>⚠️ Seção vazia</li>';}""")
 page.locator('#pdfBtn').click();assert page.locator('.pdf-section-checks input:checked').count()==1
 expect(page.locator('.pdf-video-choice input').first).to_have_value('https://youtu.be/keptlink123')
 assert parse_qs(urlparse(page.locator('#pdfBody .yt-link').first.get_attribute('href')).query)['url']==['https://youtu.be/keptlink123']
 page.locator('#closePdfViewer').click();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click()
 phone=page.locator('#infoWhats');phone.fill('+55 (86) 98825-1657')
 box=phone.bounding_box()
 for button in page.locator('.whatsapp-input-wrap button').all():
  b=button.bounding_box();assert b['y']>=box['y']+box['height']-1,(box,b)
 page.get_by_role('button',name='Copiar WhatsApp sem 55',exact=True).click();page.wait_for_function("copied.at(-1)==='86988251657'")
 page.screenshot(path='/tmp/whatsapp-actions-fixed.png')
 assert not errors,errors
 browser.close();print('PASS: share named PDF File only in both models; monitored custom link persists and quick paste works; collapsed populated sections only; WhatsApp actions do not overlap input')
