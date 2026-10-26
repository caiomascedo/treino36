"""Select exact workout versions before falling back to their owner's active cover."""
import os
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.webkit.launch() if os.environ.get('TEST_BROWSER')=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':600},is_mobile=True,has_touch=True)
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='compare.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://compare.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate("""()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana Luísa',treino_id:'now',treinoNome:'Treino de Ana Luísa',treino:{A:Array.from({length:8},(_,i)=>'Agachamento '+i+' — 3×12')},historicoTreinos:[{workout_id:'old-one',student_id:'ana',name:'Treino de Ana Luísa',status:'archived',archived_at:'2026-10-26T19:24:00Z',treino:{A:Array.from({length:8},(_,i)=>'Supino '+i+' — 4×10')}},{workout_id:'old-two',student_id:'ana',name:'Treino de Ana Luísa',status:'archived',archived_at:'2026-10-26T19:25:00Z',treino:{A:Array.from({length:8},(_,i)=>'Remada '+i+' — 3×15')}}]}]))""")
 page.reload();baseline=page.evaluate("localStorage.getItem('treinoAlunos')");page.locator('#compareWorkoutBtn').click()
 dialog=page.locator('#compareWorkoutsDialog');body=page.locator('#compareBody');header=page.locator('.compare-header');minimize=page.locator('#compareMinimizeOptions');full=page.locator('#compareFullscreen')
 expect(dialog.locator('.compare-selection-controls')).to_be_visible();expect(minimize).to_have_text('Minimizar seleção');before=body.bounding_box()['height'];selected=page.locator('#comparePreviousPicker').input_value()
 minimize.tap();expect(header).not_to_be_visible();expect(page.locator('#compareLabels')).not_to_be_visible();expect(minimize).to_have_text('Selecionar treinos')
 assert body.bounding_box()['height']>before+140
 expect(page.locator('.compare-compact-headings')).to_be_visible();expect(page.locator('#comparePreviousPicker')).to_have_value(selected)
 # Editing/undo remain intact as controls and layout change.
 line=page.locator('.comparison-previous-line').first;line.fill('Remada editada — 5×15');full.tap();bounds=dialog.bounding_box();assert bounds['x']==0 and bounds['y']==0 and bounds['width']==390 and bounds['height']==600,bounds
 expect(full).to_have_text('⛶ Reduzir tela');expect(line).to_have_text('Remada editada — 5×15')
 page.locator('#compareUndo').tap();expect(line).to_have_text('Remada 0 — 3×15');expect(header).not_to_be_visible();page.locator('#compareRedo').tap();expect(line).to_have_text('Remada editada — 5×15');page.locator('#compareUndo').tap()
 minimize.tap();expect(header).to_be_visible();expect(page.locator('#chooseComparePrevious')).to_be_visible()
 page.locator('#chooseComparePrevious').tap();page.locator('#comparePreviousChoice .compare-version-option').filter(has_text='Anterior 1 (arquivado)').tap();expect(page.locator('.comparison-previous-line').first).to_have_text('Supino 0 — 4×10')
 minimize.tap();footer=dialog.locator('.dialog-actions [data-close]').bounding_box();assert footer['y']>=0 and footer['y']+footer['height']<=600
 page.screenshot(path='/tmp/compare-fullscreen-minimized-mobile.png')
 full.tap();assert dialog.bounding_box()['height']<600;expect(minimize).to_have_text('Selecionar treinos')
 dialog.locator('.dialog-actions [data-close]').tap();page.locator('#compareWorkoutBtn').tap();expect(header).not_to_be_visible();expect(full).to_have_text('⛶ Tela inteira');dialog.locator('.dialog-actions [data-close]').tap()
 page.reload();page.locator('#compareWorkoutBtn').tap();expect(header).not_to_be_visible();expect(minimize).to_have_text('Selecionar treinos')
 assert page.evaluate("localStorage.getItem('treinoAlunos')")==baseline
 assert not errors,errors
 browser.close();print('PASS: collapse frees exercise space; fullscreen fills mobile viewport; footer visible; selection/edit/undo survive layout toggles; previous selection works after expanding options; collapse preference persists; saved workouts unchanged')
