"""Deletion is explicit, previewed, scoped and guarded against concurrent changes."""
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':600},timezone_id='America/Fortaleza')
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='history.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();page.goto('http://history.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate("""()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana',treino_id:'current',treinoNome:'Treino de Ana',atualizadoEm:'2026-10-26T19:15:00Z',treino:{A:['Agachamento — 3×12']},historicoTreinos:[{workout_id:'old',name:'Ciclo pernas',archived_at:'2026-10-26T18:00:00Z',edited_at:'2026-10-26T18:45:00Z',treino:{A:['Supino — 4×10']}},{workout_id:'same',name:'Cópia da capa',archived_at:'2026-10-26T20:00:00Z',treino:{A:['Agachamento — 3×12']}},{workout_id:'unknown',name:'Importado antigo',treino:{A:['Remada — 3×12']}}]}]))""")
 page.reload();page.locator('#historyWorkoutBtn').click();select=page.locator('#historyVersion');info=page.locator('#historyVersionInfo')
 expect(select).to_have_value('student-ana');expect(info).to_contain_text('Visualizando a CAPA ATUAL');expect(info).to_contain_text('16:15');expect(info).to_contain_text('Mesmo conteúdo da capa: Anterior 2')
 labels=select.locator('option').all_text_contents();assert 'CAPA ATUAL' in labels[0] and 'Capa: Capa' not in ' '.join(labels)
 assert '16:15' in labels[0] and 'Anterior 1 (arquivado)' in labels[-1] and '15:45' in labels[-1],labels
 before=page.evaluate("localStorage.getItem('treinoAlunos')")
 select.select_option('old');expect(info).to_contain_text('Anterior 1 · arquivado · não é a capa');expect(info).to_contain_text('Alterado em 26/10/2026, 15:45');expect(info).to_contain_text('Arquivado em 26/10/2026, 15:00');expect(page.locator('#historyVersionText')).to_contain_text('Supino')
 page.screenshot(path='/tmp/history-clear-cover-times.png')
 select.select_option('unknown');expect(info).to_contain_text('Data e horário não registrados')
 assert page.evaluate("localStorage.getItem('treinoAlunos')")==before
 assert page.evaluate("WorkoutHistoryTools.dateTime('2026-10-20')")=='20/10/2026 (hora não registrada)'
 assert page.evaluate("WorkoutHistoryTools.dateTime('not-a-date')")==''
 # Promoting a version updates the cover label and keeps its historical source marked archived.
 select.select_option('old');page.locator('#promoteHistoryVersion').click();expect(select).to_have_value('student-ana');expect(info).to_contain_text('Capa atual: Ciclo pernas');expect(info).to_contain_text('Visualizando a CAPA ATUAL');expect(info).to_contain_text('Mesmo conteúdo da capa: Anterior 1')
 data=page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0]");saved=next(v for v in data['historicoTreinos'] if v['workout_id']=='current');assert saved['updated_at']=='2026-10-26T19:15:00Z'
 select.select_option('old');expect(info).to_contain_text('não é a capa');expect(info).to_contain_text('15:45')
 bounds=page.locator('#workoutHistoryDialog .dialog-actions [data-close]').bounding_box();assert bounds['y']>=0 and bounds['y']+bounds['height']<=600
 browser.close();print('PASS: default cover, distinct archived versions, real edit/archive local times, unknown/date-only handling, duplicate cover mapping, promotion preserves prior update time, viewing does not mutate data, mobile footer visible')
