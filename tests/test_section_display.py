"""Per-pupil section visibility is independent of saved contents and PDF selection."""
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='display.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();page.goto('http://display.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate("localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana',treino:{A:['Agachamento — 3×12']}},{student_id:'bruno',nome:'Bruno',treino:{A:['Supino — 3×12'],B:['Remada — 3×12']}}]))")
 page.reload();page.locator('#moreOptions > summary').click();page.locator('.section-display-options > summary').click();before=page.evaluate("localStorage.getItem('treinoAlunos')")
 page.get_by_role('button',name='Ocultar vazias',exact=True).click();expect(page.locator('.section.sec-a')).to_be_visible()
 for section in 'BCDE':expect(page.locator('.section.sec-'+section.lower())).not_to_be_visible()
 assert page.evaluate("localStorage.getItem('treinoAlunos')")==before
 page.get_by_role('button',name='Mostrar todas',exact=True).click();expect(page.locator('.section.sec-b')).to_be_visible()
 page.get_by_role('checkbox',name='Mostrar seção A na tela',exact=True).uncheck();expect(page.locator('.section.sec-a')).not_to_be_visible()
 # Hiding the main section does not remove it from the optional PDF chooser.
 page.locator('#pdfBtn').click();expect(page.get_by_role('checkbox',name='Incluir seção A no PDF',exact=True)).to_be_checked();expect(page.locator('#pdfBody .pdf-ex-title')).to_contain_text('Agachamento');page.locator('#closePdfViewer').click()
 page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="Bruno"] .aluno-nome').click();expect(page.locator('.section.sec-a')).to_be_visible();expect(page.locator('.section.sec-b')).to_be_visible()
 page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="Ana"] .aluno-nome').click();expect(page.locator('.section.sec-a')).not_to_be_visible()
 page.reload();expect(page.locator('.section.sec-a')).not_to_be_visible();assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].treino.A")==['Agachamento — 3×12']
 browser.close();print('PASS: hide empty/manual sections without deleting data, PDF independence, per-pupil visibility and reload')
