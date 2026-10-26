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
 page.evaluate("""()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana',treino_id:'now',treinoNome:'Capa Ana',treino:{A:['Agachamento — 3×12']},historicoTreinos:[{workout_id:'old-one',student_id:'ana',name:'Anterior um',status:'archived',archived_at:'2026-10-20T15:00:00Z',treino:{A:['Supino — 4×10']}},{workout_id:'old-two',student_id:'ana',name:'Anterior dois',status:'archived',archived_at:'2026-10-21T15:00:00Z',treino:{A:['Remada — 3×15']}}]},{student_id:'bia',nome:'Bia',treino_id:'bia-now',treinoNome:'Capa Bia',treino:{A:['Flexora — 3×10']},historicoTreinos:[{workout_id:'bia-old',student_id:'bia',name:'Anterior Bia',status:'archived',treino:{A:['Extensora — 4×12']}}]}]))""")
 page.reload();baseline=page.evaluate("localStorage.getItem('treinoAlunos')");page.locator('#compareWorkoutBtn').click()
 previous=page.locator('#comparePreviousPicker');current=page.locator('#compareCurrentPicker')
 keys=page.evaluate("({one:'archive:'+encodeURIComponent(JSON.stringify(['ana',0])),two:'archive:'+encodeURIComponent(JSON.stringify(['ana',1])),bia:'archive:'+encodeURIComponent(JSON.stringify(['bia',0]))})")
 def choose(value):
  page.locator('#chooseComparePrevious').tap();page.locator('#comparePreviousChoice [data-choice=\"'+value+'\"]').tap()
 assert previous.input_value()==keys['two'], 'Opening comparison incorrectly selects the owner cover for an archived workout'
 expect(current).to_have_value('student-ana')
 choose(keys['one']);expect(previous).to_have_value(keys['one']);expect(page.locator('#compareBody .comparison-previous-line')).to_have_text('Supino — 4×10')
 choose(keys['two']);expect(previous).to_have_value(keys['two']);expect(page.locator('#compareBody .comparison-previous-line')).to_have_text('Remada — 3×15')
 # An edited version stays selected on undo/redo redraw, with the unsaved-edit guard retained.
 line=page.locator('#compareBody .comparison-previous-line');line.fill('Remada — 4×15');choose(keys['one']);expect(previous).to_have_value(keys['two']);expect(page.locator('#compareEditStatus')).to_contain_text('Aplique as edições')
 page.locator('#compareUndo').click();expect(previous).to_have_value(keys['two']);expect(page.locator('#compareBody .comparison-previous-line')).to_have_text('Remada — 3×15')
 page.locator('#compareRedo').click();expect(previous).to_have_value(keys['two']);page.locator('#compareUndo').click()
 choose(keys['bia']);expect(previous).to_have_value(keys['bia']);expect(page.locator('#compareBody .comparison-previous-line')).to_have_text('Extensora — 4×12');expect(current).to_have_value('student-ana')
 choose('student-bia');expect(previous).to_have_value('student-bia');expect(page.locator('#compareBody .comparison-previous-line')).to_have_text('Flexora — 3×10')
 choose(keys['one']);current.select_option(keys['bia']);page.locator('#compareChoiceViewOnly').click();expect(current).to_have_value(keys['bia']);expect(previous).to_have_value(keys['one'])
 expect(page.locator('#compareBody .comparison-current-line')).to_have_text('Extensora — 4×12');expect(page.locator('#compareBody .comparison-previous-line')).to_have_text('Supino — 4×10')
 assert page.evaluate("localStorage.getItem('treinoAlunos')")==baseline
 assert not errors,errors
 browser.close();print('PASS: exact archived selection on opening and switching; owner covers remain distinct; edit guard and undo/redo keep selection; other pupils/preview-only current side work; no saved workout changes')
