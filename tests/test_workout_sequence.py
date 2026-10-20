from pathlib import Path
from urllib.parse import urlparse
import json
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404,body='')
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://app.test/treino36/')
 page.evaluate('''()=>{const student=(id,nome,division)=>({student_id:id,nome,treino_id:'w-'+id,treino:Object.fromEntries([...division].map(key=>[key,['Agachamento 3x10']])),titulos:Object.fromEntries([...division].map(key=>[key,key+'. TREINO'])),atualizadoEm:'2026-10-01T12:00:00Z',observacoes:'Observações preservadas',historicoTreinos:[]});localStorage.setItem('treinoAlunos',JSON.stringify([student('a','Ana','AB'),student('b','Bruno','ABC'),student('c','Caio','ABCD')]));localStorage.setItem('avaliacao_fisica_alunos','[]');}''');page.reload()
 def students():return page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')")
 def select(name):
  page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="'+name+'"] .aluno-nome').click()
 def complete(letter,next):
  expect(page.locator('#sequenceComplete')).to_have_text('✓ Fiz o treino '+letter);expect(page.locator('#sequenceComplete')).to_be_enabled();page.locator('#sequenceComplete').click();expect(page.locator('#sequenceNext')).to_have_text('Próximo: '+next);expect(page.locator('#sequenceLast')).to_contain_text('Último feito: '+letter)
 expect(page.locator('#workoutSequence')).to_be_visible();expect(page.locator('#sequenceNext')).to_have_text('Próximo: A');expect(page.locator('#sequenceLast')).to_have_text('Nenhum treino marcado ainda')
 before=students();assert all(not s.get('sequenciaTreino') for s in before)
 complete('A','B');complete('B','A');first=students()[0];assert first['sequenciaTreino']['ultima']=='B' and first['atualizadoEm']==before[0]['atualizadoEm'] and first['treino']==before[0]['treino'] and first['observacoes']==before[0]['observacoes'] and first['historicoTreinos']==[]
 page.locator('#sequenceUndo').click();expect(page.locator('#sequenceNext')).to_have_text('Próximo: B');expect(page.locator('#sequenceUndo')).to_be_disabled()
 page.reload();expect(page.locator('#sequenceLast')).to_contain_text('Último feito: A');expect(page.locator('#sequenceNext')).to_have_text('Próximo: B')
 # Manual corrections need not follow the suggested letter.
 page.locator('#sequenceAdjust > summary').click();page.locator('#sequenceLastChoice').select_option('B');page.locator('#sequenceSet').click();expect(page.locator('#sequenceNext')).to_have_text('Próximo: A')
 select('Bruno');expect(page.locator('#sequenceLast')).to_have_text('Nenhum treino marcado ainda');complete('A','B');complete('B','C');complete('C','A')
 page.locator('#sequenceAdjust > summary').click();page.locator('#sequenceLastChoice').select_option('A');page.locator('#sequenceSet').click();expect(page.locator('#sequenceNext')).to_have_text('Próximo: B')
 select('Caio');complete('A','B');complete('B','C');complete('C','D');complete('D','A')
 # List summaries remain specific to each pupil, and browsing never marks one done.
 page.locator('#listBtn').click();expect(page.locator('.aluno-list-item[data-nome="Ana"] .lista-sequencia-treino')).to_have_text('Último feito: B · Próximo: A');expect(page.locator('.aluno-list-item[data-nome="Bruno"] .lista-sequencia-treino')).to_have_text('Último feito: A · Próximo: B');expect(page.locator('.aluno-list-item[data-nome="Caio"] .lista-sequencia-treino')).to_have_text('Último feito: D · Próximo: A');page.locator('.aluno-list-item[data-nome="Ana"] .aluno-nome').click()
 stable=students()[0]['sequenciaTreino'];page.reload();assert students()[0]['sequenciaTreino']==stable
 # Failed durable writes keep the last successful marker both on screen and in storage.
 page.evaluate("()=>{window.realStage=TreinoStorage.stageObs;TreinoStorage.stageObs=()=>{throw Error('Sem espaço para salvar')};}")
 page.locator('#sequenceComplete').click();expect(page.locator('#sequenceStatus')).to_contain_text('Sem espaço');expect(page.locator('#sequenceNext')).to_have_text('Próximo: A');assert students()[0]['sequenciaTreino']==stable
 page.evaluate('()=>{TreinoStorage.stageObs=realStage;}')
 complete('A','B')
 # Updates from another tab refresh the selected pupil without completing anything.
 page.evaluate('''()=>{const records=AvaliacaoTreinoSync.read('treinoAlunos');records[0].sequenciaTreino=WorkoutSequence.mark(records[0],'B');localStorage.setItem('treinoAlunos',JSON.stringify(records));window.dispatchEvent(new StorageEvent('storage',{key:'treinoAlunos'}));}''');expect(page.locator('#sequenceNext')).to_have_text('Próximo: A');expect(page.locator('#sequenceLast')).to_contain_text('Último feito: B')
 page.screenshot(path='/tmp/workout-sequence-mobile.png')
 # Clear only affects the current pupil. A new workout does not inherit old attendance.
 page.locator('#sequenceAdjust > summary').click();page.locator('#sequenceClear').click();expect(page.locator('#sequenceLast')).to_have_text('Nenhum treino marcado ainda');assert students()[0]['sequenciaTreino'] is None;assert students()[1]['sequenciaTreino']['ultima']=='A'
 complete('A','B')
 previous_workout=students()[0]['treino_id'];previous_marker=students()[0]['sequenciaTreino']
 page.locator('.sec-a ol').fill('Supino 4x8');page.locator('#saveBtn').click()
 expect(page.locator('#sequenceLast')).to_have_text('Nenhum treino marcado ainda');expect(page.locator('#sequenceNext')).to_have_text('Próximo: A')
 replaced=students()[0];assert replaced['treino_id']!=previous_workout and replaced['historicoTreinos'][-1]['sequenciaTreino']==previous_marker
 assert not replaced.get('sequenciaTreino')
 # Markers are omitted from prints and included in the existing JSON backup.
 page.emulate_media(media='print');expect(page.locator('#workoutSequence')).not_to_be_visible();page.emulate_media(media='screen')
 page.locator('#moreOptions > summary').click()
 with page.expect_download() as download:page.locator('#exportBtn').click()
 backup=json.loads(Path(download.value.path()).read_text());assert backup['alunos'][1]['sequenciaTreino']['ultima']=='A';assert backup['alunos'][2]['sequenciaTreino']['ultima']=='D'
 # A name that is not a saved pupil must never expose another pupil's controls.
 page.locator('#searchName').fill('Novo nome sem cadastro');expect(page.locator('#workoutSequence')).not_to_be_visible()
 assert not errors,errors
 browser.close();print('PASS: manual AB/ABC/ABCD cycles, undo/correction/clear, reload, pupil and workout isolation, no exercise/history/date changes, failed-write rollback, cross-tab refresh, print omission and real JSON export')
