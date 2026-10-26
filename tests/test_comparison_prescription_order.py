"""Select exact workout versions before falling back to their owner's active cover."""
import os
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.webkit.launch() if os.environ.get('TEST_BROWSER')=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='compare.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://compare.test/');page.evaluate('TreinoStorage.ready')
 old={'A':['Leg Press 45° — 3×12','Agachamento no Smith — 3×12','Step-up — 3×10'],'B':['Remada — 3×12','Remada — 2×15']}
 current={'A':['Agachamento Sumô no Smith — 4×12','Leg Press 45° — 3×12'],'B':['Remada — 3×12'],'C':['Abdominal — 3×15']}
 page.evaluate("data=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana',treino_id:'now',treinoNome:'Capa Ana',treino:data.current,historicoTreinos:[{workout_id:'old',student_id:'ana',name:'Anterior',status:'archived',treino:data.old}]}]))",{'old':old,'current':current})
 page.reload();baseline=page.evaluate("localStorage.getItem('treinoAlunos')");page.locator('#compareWorkoutBtn').click()
 def lines(side,section):return page.locator('.comparison-'+side+'-line[data-section="'+section+'"]').all_text_contents()
 assert lines('previous','A')==old['A'] and lines('current','A')==current['A']
 assert lines('previous','B')==old['B'] and lines('current','B')==current['B']
 assert lines('current','C')==current['C']
 titles=page.locator('.comparison-row > h4').all_text_contents();assert titles==['Exercício 1 · Exercícios diferentes','Exercício 2 · Exercícios diferentes','Exercício 3 · Só no anterior','Exercício 1 · Mantido','Exercício 2 · Só no anterior','Exercício 1 · Só no atual'],titles
 assert page.evaluate("localStorage.getItem('treinoAlunos')")==baseline
 page.locator('#compareMinimizeOptions').tap();page.locator('#compareFullscreen').tap()
 line=page.locator('.comparison-previous-line[data-section="A"][data-index="1"]');line.fill('Agachamento no Smith — 5×12')
 expect(page.locator('.comparison-row > h4').nth(1)).to_have_text('Exercício 2 · Editado (Anterior)')
 page.locator('#compareUndo').tap();assert lines('previous','A')==old['A'];page.locator('#compareRedo').tap();assert lines('previous','A')==[old['A'][0],'Agachamento no Smith — 5×12',old['A'][2]]
 page.screenshot(path='/tmp/compare-order-compact-mobile.png')
 page.locator('#applyCompareEdit').tap();saved=page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0]")
 assert all(saved['treino'].get(section,[])==current.get(section,[]) for section in 'ABCDEF') and saved['historicoTreinos'][0]['treino']['A']==[old['A'][0],'Agachamento no Smith — 5×12',old['A'][2]] and saved['historicoTreinos'][0]['treino']['B']==old['B']
 assert not errors,errors
 browser.close();print('PASS: exact order on both sides by section/position; duplicate exercises and unequal lengths preserved; numbered rows; edit/undo/redo/apply target original index; compact/fullscreen retained')
