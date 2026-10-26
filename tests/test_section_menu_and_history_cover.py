"""Section tap actions preserve drag/undo; historical cover promotion preserves data."""
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 context.add_init_script("window.copied=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>copied.push(text)}})")
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='sections.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();page.goto('http://sections.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate('''()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana',treino_id:'current',treinoNome:'Ciclo atual',treinoProtegido:false,treino:{A:['Agachamento — 3×12','Leg Press — 3×15'],B:['Remada — 3×12']},titulos:{A:'A. Quadríceps',B:'B. Costas'},obsGuias:[{id:'obs',texto:'Preservar OBS'}],historicoTreinos:[{workout_id:'old-one',student_id:'ana',name:'Ciclo anterior',status:'archived',archived_at:'2026-09-01T10:00:00Z',treino:{A:['Supino — 4×10'],F:['Abdominal — 3×15']},titulos:{A:'A. Peito',F:'F. Core'},secaoFAtiva:true},{workout_id:'old-two',student_id:'ana',name:'Outro anterior',status:'archived',archived_at:'2026-08-01T10:00:00Z',treino:{A:['Extensora — 3×12']},titulos:{A:'A. Pernas'}}]},{student_id:'other',nome:'Outro',treino_id:'other-current',treino:{A:['Stiff — 3×12']}}]))''')
 page.reload();menu=page.locator('#sectionActionsDialog')
 def open_menu(section):page.locator('#mainContainer .workout-grip[data-section='+section+']').click();expect(menu).to_be_visible()
 def data():return page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
 open_menu('A');menu.locator('[data-copy]').click();page.wait_for_function('copied.length===1');assert 'Agachamento' in page.evaluate('copied[0]');menu.locator('[data-close]').click()
 open_menu('B');menu.locator('[data-paste]').click();expect(menu).not_to_be_visible();assert len(data()[0]['treino']['B'])==3 and len(data()[0]['treino']['A'])==2
 page.locator('#undoBtn').click();page.wait_for_function("JSON.parse(localStorage.getItem('treinoAlunos'))[0].treino.B.length===1");assert len(data()[0]['treino']['B'])==1
 open_menu('A');menu.get_by_role('combobox',name='Destino da seção duplicada').select_option('C');menu.locator('[data-duplicate]').click();assert len(data()[0]['treino']['C'])==2 and data()[0]['titulos']['C'].startswith('C.')
 page.locator('#undoBtn').click();page.wait_for_function("!(JSON.parse(localStorage.getItem('treinoAlunos'))[0].treino.C||[]).some(line=>line.includes('Agachamento'))");assert not data()[0]['treino'].get('C') or 'Nenhum' in ' '.join(data()[0]['treino']['C']) or 'Sem treino' in ' '.join(data()[0]['treino']['C'])
 open_menu('A');menu.get_by_role('combobox',name='Destino da seção duplicada').select_option('F');menu.locator('[data-duplicate]').click();assert data()[0]['secaoFAtiva'] and len(data()[0]['treino']['F'])==2
 page.locator('#undoBtn').click();page.wait_for_function("!JSON.parse(localStorage.getItem('treinoAlunos'))[0].secaoFAtiva");assert not data()[0]['secaoFAtiva']
 # Arrow movement is still separate from opening the menu.
 page.locator('#mainContainer .workout-grip[data-section=A]').press('ArrowDown');expect(menu).not_to_be_visible();assert 'Remada' in ' '.join(data()[0]['treino']['A']);page.locator('#undoBtn').click()
 # A held grip starts drag, never a tap menu.
 grip=page.locator('#mainContainer .workout-grip[data-section=A]');grip.scroll_into_view_if_needed();bounds=grip.bounding_box();page.mouse.move(bounds['x']+10,bounds['y']+10);page.mouse.down();page.wait_for_timeout(330);expect(page.locator('.workout-ghost')).to_have_count(1);page.mouse.up();expect(menu).not_to_be_visible()
 # Empty internal clipboard offers manual section paste, appending to existing exercises.
 page.reload();open_menu('B');menu.locator('[data-paste]').click();menu.get_by_role('textbox',name='Texto da seção para colar').fill('A. Externo\n• Extensora — 3×12\n• Flexora — 3×12');menu.locator('[data-apply]').click();assert len(data()[0]['treino']['B'])==3
 before=data();owner=before[0];other=before[1]
 page.locator('#historyWorkoutBtn').click();page.locator('#historyVersion').select_option('old-one');expect(page.locator('#promoteHistoryVersion')).to_be_enabled();page.locator('#promoteHistoryVersion').click()
 expect(page.locator('#historyPromotionStatus')).to_contain_text('capa anterior ficou guardada')
 after=data();active=after[0];assert active['treino']['A']==['Supino — 4×10'] and active['secaoFAtiva']
 assert active['treinoNome']=='Ciclo anterior' and active['treino_id'] not in [owner['treino_id'],'old-one']
 assert any(v['workout_id']==owner['treino_id'] and v['treino']==owner['treino'] for v in active['historicoTreinos'])
 assert any(v['workout_id']=='old-one' for v in active['historicoTreinos']) and active['obsGuias']==owner['obsGuias'] and after[1]==other
 expect(page.locator('#promoteHistoryVersion')).to_be_disabled();page.reload();page.locator('#historyWorkoutBtn').click();page.locator('#historyVersion').select_option('old-two')
 before_failure=page.evaluate("localStorage.getItem('treinoAlunos')")
 page.evaluate("()=>{const set=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(key==='treinoAlunos')throw new DOMException('Full','QuotaExceededError');return set.call(this,key,value)}}")
 page.locator('#promoteHistoryVersion').click();expect(page.locator('#historyPromotionStatus')).to_contain_text('Não foi possível')
 assert page.evaluate("localStorage.getItem('treinoAlunos')")==before_failure
 browser.close();print('PASS: section copy/paste/duplicate, empty-target safety, F activation/undo, arrow/long-press drag retained, historical cover promotion/archiving/isolation and quota rollback')
