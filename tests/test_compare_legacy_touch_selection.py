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
 page.evaluate("""()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana',treino_id:'shared',treinoNome:'Capa Ana',treino:{A:['Agachamento — 3×12']},historicoTreinos:[{workout_id:'shared',name:'Mesmo ID da capa',treino:{A:['Supino — 4×10']}},{name:'Sem ID antigo',treino:{A:['Remada — 3×15']}},{workout_id:'student-ana',name:'ID com prefixo antigo',treino:{A:['Stiff — 3×12']}}]},{student_id:'bia',nome:'Bia',treino_id:'bia-now',treino:{A:['Flexora — 3×10']},historicoTreinos:[{workout_id:'shared',name:'ID repetido em outro aluno',treino:{A:['Extensora — 4×12']}}]}]))""")
 page.reload();baseline=page.evaluate("localStorage.getItem('treinoAlunos')");page.locator('#compareWorkoutBtn').click()
 previous=page.locator('#comparePreviousPicker');trigger=page.locator('#chooseComparePrevious');chooser=page.locator('#comparePreviousChoice')
 expect(page.locator('#compareBody .comparison-previous-line')).to_have_text('Stiff — 3×12')
 def choose(text):
  trigger.tap();chooser.locator('.compare-version-option').filter(has_text=text).tap()
 choose('Sem ID antigo');expect(page.locator('#compareBody .comparison-previous-line')).to_have_text('Remada — 3×15');expect(trigger).to_contain_text('Sem ID antigo')
 choose('Mesmo ID da capa');expect(page.locator('#compareBody .comparison-previous-line')).to_have_text('Supino — 4×10');expect(page.locator('#compareCurrentPicker')).to_have_value('student-ana')
 choose('ID repetido em outro aluno');expect(page.locator('#compareBody .comparison-previous-line')).to_have_text('Extensora — 4×12');expect(trigger).to_contain_text('ID repetido em outro aluno')
 trigger.click();chooser.get_by_role('searchbox').fill('Sem ID antigo');expect(chooser.locator('.compare-version-option')).to_have_count(1);chooser.get_by_role('button',name='Cancelar',exact=True).click();expect(trigger).to_contain_text('ID repetido em outro aluno')
 choose('ID com prefixo antigo');expect(page.locator('#compareBody .comparison-previous-line')).to_have_text('Stiff — 3×12')
 assert page.evaluate("localStorage.getItem('treinoAlunos')")==baseline
 # Editing a legacy archive with a missing ID saves only its exact slot, preserving the cover and other archives.
 choose('Sem ID antigo');page.locator('#compareBody .comparison-previous-line').fill('Remada — 5×15');page.locator('#applyCompareEdit').click()
 saved=page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
 assert saved[0]['treino']['A']==['Agachamento — 3×12'] and saved[0]['historicoTreinos'][0]['treino']['A']==['Supino — 4×10']
 assert saved[0]['historicoTreinos'][1]['treino']['A']==['Remada — 5×15'] and saved[1]['historicoTreinos'][0]['treino']['A']==['Extensora — 4×12']
 page.locator('#compareWorkoutBtn').click();trigger.click();expect(chooser.locator('h3')).to_be_focused();page.screenshot(path='/tmp/compare-previous-touch-list.png')
 assert not errors,errors
 browser.close();print('PASS: touch list selects archives with duplicate, missing or reserved-prefix legacy IDs; pupil isolation; search/cancel; viewing preserves data; editing saves only selected legacy archive')
