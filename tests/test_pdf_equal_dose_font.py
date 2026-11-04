from pathlib import Path
from urllib.parse import urlparse
import os
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if os.getenv('GIF_TEST_BROWSER')=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url);f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='edit.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('https://edit.test/');page.evaluate('TreinoStorage.ready');page.evaluate('localStorage.setItem("treinoAlunos",JSON.stringify([{nome:"Teste edição",student_id:"edit",treino:{A:["Glúteo Na Polia — 3×12 Cada Perna [Vídeo: https://youtu.be/KeepTEST123] [GIFs: https://drive.google.com/file/d/keepGIF/view]"]},titulos:{A:"A. Glúteos"}}]))');page.reload();page.evaluate('TreinoStorage.ready')
 page.evaluate('localStorage.setItem("treinoAlunos",JSON.stringify([{nome:"Teste",treino:{A:["Agachamento Com Barra + Agachamento Taça Curtinho — 3×12 + 20 Curtas No Taça."]}}]))');page.reload();page.evaluate('TreinoStorage.ready');page.locator('#pdfBtn').click();page.get_by_role('checkbox',name='Vídeos individuais nos conjugados',exact=True).check();page.get_by_role('checkbox',name='Cores nos conjugados do PDF',exact=True).check(); page.get_by_role('combobox',name='Modelo do PDF').select_option('old');dose=page.locator('.pdf-compound-dose');fonts=dose.evaluate('(e)=>[e.firstElementChild,e.querySelector(".pdf-compound-tail>span")].map(x=>getComputedStyle(x).fontSize)');assert fonts[0]==fonts[1];assert dose.locator('.pdf-compound-tail').evaluate('e=>getComputedStyle(e).whiteSpace')=='normal';assert dose.locator('.pdf-compound-tail>span').first.evaluate('e=>getComputedStyle(e).color')=='rgb(21, 128, 61)';assert dose.inner_text().count('20 Curtas No Taça.')==1;assert dose.locator('a').count()==2;b.close();print('PASS: coloured prescriptions have equal font sizes, final dose wraps, colours/text/links preserved')
