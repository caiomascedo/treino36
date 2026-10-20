from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://app.test/treino36/')
 page.evaluate('''()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'d',nome:'Dany',treino_id:'w-d',acompanharSequencia:true,treino:{A:['**1. Agachamento livre —   3 x 10**','• Ponte de glúteo – 3x12'],B:['2. Remada baixa   3x12'],C:['⚠️ Sem treino cadastrado'],D:['Seção vazia']},titulos:{A:'A. INFERIORES + CORE',B:'B. SUPERIORES'},atualizadoEm:'2026-10-01T12:00:00Z',historicoTreinos:[]} ]));localStorage.setItem('avaliacao_fisica_alunos','[]');}''');page.reload()
 def student():return page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0]")
 original=student()
 def menu():
  if page.locator('#sequenceMenu').get_attribute('open') is None:page.locator('#sequenceMenu > summary').click()
 menu()
 assert page.locator('#sequenceComplete').is_enabled(),page.locator('#sequenceStatus').text_content()
 page.locator('#sequenceAdjust > summary').click();expect(page.locator('#sequenceLastChoice')).to_be_enabled();page.locator('#sequenceLastChoice').select_option('B');page.locator('#sequenceSet').click();expect(page.locator('#sequenceNext')).to_have_text('Próximo: A')
 saved=student();assert saved['sequenciaTreino']['ultima']=='B' and saved['treino']==original['treino'] and saved['atualizadoEm']==original['atualizadoEm'] and saved['historicoTreinos']==[]
 # The tracker shares the formatting toolbar at standard mobile widths; its panel fits the viewport.
 assert page.locator('#workoutSequence').evaluate("node=>node.parentElement.classList.contains('format-bar')")
 for width in [390,360,320]:
  page.set_viewport_size({'width':width,'height':844});menu()
  panel=page.locator('.sequence-content').bounding_box();assert panel['x']>=0 and panel['x']+panel['width']<=width,(width,panel)
  page.locator('#sequenceMenu > summary').click()
 page.set_viewport_size({'width':390,'height':844})
 seq=page.locator('#workoutSequence').bounding_box();bold=page.locator('#boldBtn').bounding_box();assert abs(seq['y']-bold['y'])<12,(seq,bold)
 menu();page.screenshot(path='/tmp/workout-sequence-toolbar-open.png');page.keyboard.press('Escape');expect(page.locator('.sequence-content')).not_to_be_visible();page.screenshot(path='/tmp/workout-sequence-toolbar.png')
 # A real different displayed prescription still cannot mark the saved program.
 page.locator('.sec-a ol').evaluate("node=>{node.querySelector('li').textContent='Agachamento 9x99';}")
 page.locator('#sequenceMenu > summary').click();expect(page.locator('#sequenceComplete')).to_be_disabled();expect(page.locator('#sequenceLastChoice')).to_be_disabled();assert student()['sequenciaTreino']==saved['sequenciaTreino']
 page.reload();menu();expect(page.locator('#sequenceComplete')).to_be_enabled();page.locator('#sequenceComplete').click();expect(page.locator('#sequenceNext')).to_have_text('Próximo: B');assert student()['treino']==original['treino']
 assert not errors,errors
 browser.close();print('PASS: numbered/markdown/spacing display allows marking and manual selection without rewriting data; inline toolbar and viewport-safe panel; Escape; actual differing prescription blocked; reload and quick mark')
