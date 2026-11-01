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
 assert page.locator('#pdfBody .pdf-ex-row').evaluate_all("rows=>rows.every(row=>row.querySelector('.pdf-ex-name > .yt-link'))")
 assert not page.locator('#pdfReviewTools > details:not(.pdf-section-choice)').evaluate('el=>el.open')
 first=page.locator('#pdfBody .pdf-ex-row').first
 initial_href=first.locator('.yt-link').get_attribute('href');assert 'youtube.com/results' in parse_qs(urlparse(initial_href).query)['url'][0]
 before=page.evaluate("localStorage.getItem('treinoAlunos')")
 page.get_by_role('button',name='Editar texto',exact=True).click();first.locator('.pdf-ex-title').fill('Agachamento no Smith');first.locator('.pdf-ex-details').fill('— 4×15')
 assert first.locator('.pdf-ex-details').inner_text()=='— 4×15'
 assert 'Agachamento no Smith' in parse_qs(urlparse(first.locator('.yt-link').get_attribute('href')).query)['ex'][0]
 page.locator('#pdfReviewTools > details:not(.pdf-section-choice) > summary').click();page.locator('.pdf-video-section > summary').first.click();choice=page.locator('.pdf-video-choice').first
 choice.locator(':scope > label > input').fill('javascript:alert(1)');page.locator('#downloadPdfBtn').click();assert page.evaluate('pdfWindows.length')==0
 expect(page.locator('#pdfReviewTools [role=status]')).to_contain_text('http ou https')
 choice.get_by_role('button',name='Automático',exact=True).click();expect(choice.locator(':scope > label > input')).to_have_value('')
 custom='https://www.youtube.com/watch?v=12345678901';choice.locator(':scope > label > input').fill(custom)
 assert parse_qs(urlparse(first.locator('.yt-link').get_attribute('href')).query)['url']==[custom]
 page.screenshot(path='/tmp/pdf-review-mobile.png')
 page.locator('#downloadPdfBtn').click();page.wait_for_function('pdfWindows.length===1&&pdfWindows[0].url',timeout=30000)
 assert not page.locator('#pdfBody').evaluate("el=>el.classList.contains('pdf-is-editing')")
 result=page.evaluate("async()=>{const blob=pdfBlobs.get(pdfWindows[0].url),bytes=new Uint8Array(await blob.arrayBuffer());let value='';for(const byte of bytes)value+=String.fromCharCode(byte);return btoa(value);}")
 with fitz.open(stream=base64.b64decode(result),filetype='pdf') as doc:
  links=[link.get('uri','') for pdfpage in doc for link in pdfpage.get_links()]
  assert any(parse_qs(urlparse(link).query).get('url')==[custom] for link in links),links
  assert sum('r/yt?' in link for link in links)>=3
 saved=page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))");assert custom in saved[0]['treino']['A'][0]
 assert 'Agachamento Livre' in saved[0]['treino']['A'][0] and '4×15' not in saved[0]['treino']['A'][0]
 assert saved[0]['treino']['B']==['Remada — 3×12']
 page.locator('#closePdfViewer').click();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click()
 phone=page.locator('#infoWhats');phone.fill('+55 (55) 99999-8888');page.get_by_role('button',name='Copiar WhatsApp sem 55',exact=True).click();page.wait_for_function("copied.at(-1)==='55999998888'");expect(phone).to_have_value('+55 (55) 99999-8888')
 for number,expected in [('+55 (11) 98888-7777','11988887777'),('005511988887777','11988887777'),('(55) 99999-8888','55999998888'),('5533334444','5533334444'),('', '')]:
  assert page.evaluate('(value)=>WhatsAppCopy.localNumber(value)',number)==expected
 # Full A-F groups, both layouts and rasterized multi-section PDF regressions.
 page.locator('#workoutObsDialog [data-close]').click()
 page.evaluate("""()=>{const people=JSON.parse(localStorage.getItem('treinoAlunos'));people[0].secaoFAtiva=true;people[0].treino={};people[0].titulos={};for(const section of 'ABCDEF'){people[0].titulos[section]=section+'. Grupo '+section;people[0].treino[section]=Array.from({length:9},(_,i)=>'Exercício '+section+' '+(i+1)+' — 3×12, mantendo amplitude e execução controlada, com descanso de 60 segundos entre cada série.');}localStorage.setItem('treinoAlunos',JSON.stringify(people));}""")
 page.reload();page.locator('#pdfBtn').click();expect(page.locator('.pdf-video-section')).to_have_count(6)
 assert [text[0] for text in page.locator('.pdf-video-section > summary').all_text_contents()]==list('ABCDEF')
 for section in page.locator('.pdf-video-section').all():assert section.locator('.pdf-video-choice label span').first.text_content().startswith('1. '),section.locator('.pdf-video-choice label span').all_text_contents()
 page.locator('#pdfReviewTools > details:not(.pdf-section-choice) > summary').click();page.get_by_role('button',name='Expandir todos',exact=True).click();expect(page.locator('.pdf-video-section[open]')).to_have_count(6);page.get_by_role('button',name='Recolher todos',exact=True).click();expect(page.locator('.pdf-video-section[open]')).to_have_count(0);page.locator('.pdf-video-section > summary').last.click();expect(page.locator('.pdf-video-section').last.locator('input').first).to_be_visible()
 specific=page.locator('.pdf-video-section').last.locator('input').first;specific.fill(custom)
 def export_and_check(model):
  page.get_by_role('combobox',name='Modelo do PDF').select_option(model)
  assert all(urlparse(href).netloc=='caio.tail953b6e.ts.net' and urlparse(href).path=='/r/yt' for href in page.locator('#pdfBody .yt-link').evaluate_all('links=>links.map(a=>a.href)'))
  if model=='old':expect(page.locator('#pdfBody .pdf-ex-name > .yt-link')).to_have_count(54)
  else:expect(page.locator('#pdfBody .pdf-ex-name > .yt-link')).to_have_count(54)
  count=page.evaluate('pdfWindows.length');page.locator('#downloadPdfBtn').click();page.wait_for_function(f'pdfWindows.length==={count+1}&&pdfWindows.at(-1).url',timeout=30000)
  encoded=page.evaluate("async()=>{const blob=pdfBlobs.get(pdfWindows.at(-1).url),bytes=new Uint8Array(await blob.arrayBuffer());let text='';for(const byte of bytes)text+=String.fromCharCode(byte);return btoa(text);}")
  with fitz.open(stream=base64.b64decode(encoded),filetype='pdf') as doc:
   assert doc.page_count>=1
   destinations=[a['uri'] for p in doc for a in p.get_links() if '/r/yt?' in a.get('uri','')]
   assert len(destinations)>=54
   assert any(parse_qs(urlparse(href).query).get('url')==[custom] for href in destinations)
   for page_index,pdfpage in enumerate(doc):
    pix=pdfpage.get_pixmap(alpha=False);rects=[fitz.Rect(link['from'])+(-4,-4,4,4) for link in pdfpage.get_links() if '/r/yt?' in link.get('uri','')]
    # Long red horizontal strokes must belong to an actual video link, never a blank footer/line.
    pixels=pix.samples
    for y in range(pix.height):
     start=None
     for x in range(pix.width+1):
      red=False
      if x<pix.width:
       pos=(y*pix.width+x)*3;r,g,b=pixels[pos:pos+3];red=r-g>35 and r-b>35
      if red and start is None:start=x
      elif not red and start is not None:
       if x-start>15:assert any(rect.contains(fitz.Point((start+x)/2,y)) for rect in rects),(model,page_index,start,x,y)
       start=None
    if page_index==0:
     pix.save('/tmp/pdf-model-'+model+'.png')
     from PIL import Image
     image=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB');assert sum(1 for r,g,b in image.crop((180,0,420,45)).get_flattened_data() if r-g>35 and r-b>35)>20,(model,'missing PDF title')
 export_and_check('inline');export_and_check('old')
 page.screenshot(path='/tmp/pdf-model-selector-mobile.png')
 page.locator('#closePdfViewer').click();page.locator('#pdfBtn').click();expect(page.get_by_role('combobox',name='Modelo do PDF')).to_have_value('old')
 # Choose a single section for this PDF without changing the student's workout.
 page.locator('.pdf-section-choice > summary').click();page.get_by_role('button',name='Desmarcar todas',exact=True).click();count=page.evaluate('pdfWindows.length');page.locator('#downloadPdfBtn').click();assert page.evaluate('pdfWindows.length')==count
 expect(page.locator('#pdfReviewTools [role=status]')).to_contain_text('pelo menos uma seção')
 page.get_by_role('checkbox',name='Incluir seção F no PDF',exact=True).check();expect(page.locator('#pdfBody .pdf-sec:not([hidden])')).to_have_count(1)
 page.locator('#downloadPdfBtn').click();page.wait_for_function(f'pdfWindows.length==={count+1}&&pdfWindows.at(-1).url')
 encoded=page.evaluate("async()=>{const bytes=new Uint8Array(await pdfBlobs.get(pdfWindows.at(-1).url).arrayBuffer());let text='';for(const byte of bytes)text+=String.fromCharCode(byte);return btoa(text);}")
 with fitz.open(stream=base64.b64decode(encoded),filetype='pdf') as doc:
  links=[link['uri'] for page in doc for link in page.get_links() if '/r/yt?' in link.get('uri','')]
  assert len(links)==9 and all(parse_qs(urlparse(href).query)['treino'][0].startswith('F.') for href in links),links
 assert not errors,errors
 browser.close();print('PASS: automatic inline video labels, optional plain-text PDF draft edits, URL validation/reset, actual clickable PDF annotations, unchanged saved workout and Brazil-only WhatsApp copy')
