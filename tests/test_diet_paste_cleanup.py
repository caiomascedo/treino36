import base64,urllib.request,fitz
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];menu=(Path(__file__).parent/'fixtures/diet-menu.txt').read_text()
URL='https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';library=urllib.request.urlopen(URL,timeout=30).read()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844})
 context.add_init_script("""window.printed=[];const fill=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(text,...args){printed.push(text);return fill.call(this,text,...args);};window.open=()=>null;""")
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if r.request.url==URL:r.fulfill(body=library,content_type='application/javascript');return
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://app.test/treino36/');page.evaluate("localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento']}}]))");page.reload();original=page.evaluate("localStorage.getItem('treinoAlunos')")
 page.locator('#dietBtn').click();page.locator('#dietText').fill(menu);page.locator('#dietPreview > summary').click()
 expect(page.locator('#dietPreviewBody section')).to_have_count(6);expect(page.locator('#dietText')).to_have_value(menu)
 def clean(text):
  for excluded in ['CARDÁPIO DO EXEMPLO','Pesar arroz','Os valores podem variar','TOTAL DIÁRIO APROXIMADO']:assert excluded not in text,(excluded,text)
 clean(page.locator('#dietPreviewBody').inner_text());expect(page.locator('#dietTotals')).to_contain_text('2.000 kcal')
 page.locator('#dietPreviewBody li').first.fill('155 g de cuscuz de milho cozido')
 raw=page.locator('#dietText').input_value()
 for preserved in ['CARDÁPIO DO EXEMPLO','Pesar arroz','TOTAL DIÁRIO APROXIMADO','Os valores podem variar']:assert preserved in raw,preserved
 expect(page.locator('#dietTotals')).to_contain_text('Proteína 134 g');expect(page.locator('#dietTotals')).to_contain_text('Carbo 235 g')
 with page.expect_download() as downloaded:page.locator('#dietPdfBtn').click()
 with fitz.open(downloaded.value.path()) as pdf:content=' '.join(pg.get_text() for pg in pdf)
 clean(content)
 for included in ['Café da manhã','Lanche da manhã','Almoço','Lanche da tarde','Jantar','Ceia','155 g de cuscuz','200 ml de leite','Proteína: 134 g']:assert included in content,(included,content)
 page.locator('#dietPhotoBtn').click();expect(page.locator('#dietPhotoImages img')).to_have_count(1);clean(' '.join(page.evaluate('printed')))
 page.locator('#dietPhotoPreviewDialog [data-close]').click()
 if not page.locator('#dietCalculations').evaluate('(e)=>e.open'):page.locator('#dietCalculations > summary').click()
 page.locator('#diet-goal').fill('1950')
 page.once('dialog',lambda d:d.dismiss());page.locator('#dietPasteClearBtn').click();expect(page.locator('#dietText')).to_have_value(raw)
 page.locator('#dietPasteExpandBtn').click();page.once('dialog',lambda d:d.accept());page.locator('#dietPasteClearBtn').click();expect(page.locator('#dietText')).to_have_value('')
 expect(page.locator('#dietPasteClearBtn')).to_be_disabled();page.locator('#dietUndoBtn').click();expect(page.locator('#dietText')).to_have_value(raw)
 page.locator('#dietPasteExpandBtn').click();expect(page.locator('#diet-goal')).to_have_value('1950')
 page.reload();page.locator('#dietBtn').click();expect(page.locator('#dietText')).to_have_value(raw);expect(page.locator('#diet-goal')).to_have_value('1950')
 assert page.evaluate("localStorage.getItem('treinoAlunos')")==original
 assert not errors,errors
 browser.close();print('PASS: user-style menu gives six meals, correct daily totals, clean preview/PDF/PNG, original pasted extras retained during meal editing, confirmed clear + undo + reload, goal and pupil data unchanged')
