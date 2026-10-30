"""Loading an archive into the normal editor always saves to that archive, not the cover."""
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='mainarchive.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://mainarchive.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate("""()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana',treino_id:'cover',treinoNome:'Capa Ana',atualizadoEm:'2026-10-26T15:00:00Z',treino:{A:['Agachamento — 3×12']},titulos:{A:'A. Pernas'},historicoTreinos:[{workout_id:'old',student_id:'ana',name:'Ciclo antigo',status:'archived',archived_at:'2026-10-20T15:00:00Z',treino:{A:['Supino — 4×10 [Vídeo: https://youtu.be/KeepCASE123]'],B:['Remada — 3×12']},titulos:{A:'A. Peito',B:'B. Costas'},secaoFAtiva:false},{workout_id:'second',name:'Outro anterior',treino:{A:['Flexora — 3×10']}}]},{student_id:'bia',nome:'Bia',treino_id:'bia-cover',treino:{A:['Stiff — 3×12']}}]))""")
 page.reload()
 def records():return page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
 before=records();badge=page.locator('.cover-badge')
 # The Carregar action in name suggestions opens an archive in the normal screen.
 page.locator('#searchName').focus();page.locator('.name-suggestion-subitem[data-type=history][data-history-index="0"] .sub-load-btn').tap()
 expect(badge).to_contain_text('EDITANDO ANTERIOR 1');expect(page.locator('#alunoAtualTitulo')).to_have_text('Anterior 1 · Ana');expect(page.locator('.sec-a ol')).to_contain_text('Supino');expect(page.locator('#saveBtn')).to_have_text('💾 Salvar anterior');expect(page.locator('#searchName')).to_have_attribute('readonly','')
 assert records()==before
 # Regular Cola Inteligente and normal undo/save apply to the archive only.
 page.locator('.sec-a .colar-btn').tap();page.locator('#pasteTextarea').fill('A. Peito alterado\n1. Supino — 5×10 [Vídeo: https://youtu.be/KeepCASE123]\n2. Crucifixo — 3×12');page.locator('#confirmPasteBtn').tap();page.wait_for_function("JSON.parse(localStorage.getItem('treinoAlunos'))[0].historicoTreinos[0].treino.A.length===2");page.locator('#saveBtn').tap()
 saved=records();assert saved[0]['treino']==before[0]['treino'] and saved[0]['titulos']==before[0]['titulos'] and saved[0]['treino_id']=='cover' and saved[0]['atualizadoEm']==before[0]['atualizadoEm']
 assert len(saved[0]['historicoTreinos'][0]['treino']['A'])==2 and 'KeepCASE123' in saved[0]['historicoTreinos'][0]['treino']['A'][0] and saved[0]['historicoTreinos'][0]['treino']['B']==['Remada — 3×12'] and saved[0]['historicoTreinos'][1]==before[0]['historicoTreinos'][1] and saved[1]==before[1]
 page.locator('#undoBtn').tap();page.locator('#saveBtn').tap();assert len(records()[0]['historicoTreinos'][0]['treino']['A'])==1
 page.locator('#redoBtn').tap();page.locator('#saveBtn').tap();assert len(records()[0]['historicoTreinos'][0]['treino']['A'])==2;assert len(records()[0]['historicoTreinos'][0]['revisoes'])==1
 page.screenshot(path='/tmp/main-archive-edit-badge.png')
 page.reload();expect(badge).to_contain_text('EDITANDO ANTERIOR 1');expect(page.locator('.sec-a ol')).to_contain_text('Crucifixo');assert records()[0]['treino']==before[0]['treino']
 # PDF preview is the archive currently shown, and closing retains editing mode.
 page.locator('#pdfBtn').tap();expect(page.locator('#pdfBody')).to_contain_text('Supino');expect(page.locator('#pdfBody')).not_to_contain_text('Agachamento');page.locator('#closePdfViewer').tap();expect(badge).to_contain_text('EDITANDO ANTERIOR 1')
 page.locator('#backToWorkoutCover').tap();expect(badge).to_have_text('Capa · Treino principal');expect(page.locator('.sec-a ol')).to_contain_text('Agachamento');assert page.evaluate("sessionStorage.getItem('treinoMainArchiveEdit')") is None
 # Editing via History loads the main screen; the separate text/section editor is still available.
 page.locator('#historyWorkoutBtn').tap();page.locator('#historyVersion').select_option('old');page.locator('#editHistoryVersion').tap();expect(page.locator('#workoutHistoryDialog')).not_to_be_visible();expect(badge).to_contain_text('EDITANDO ANTERIOR 1')
 # Switching via the pupil list flushes archived work and restores normal cover mode.
 page.locator('#listBtn').tap();page.locator('.aluno-list-item[data-nome="Bia"] .aluno-nome').tap();expect(badge).to_have_text('Capa · Treino principal');expect(page.locator('.sec-a ol')).to_contain_text('Stiff');assert records()[0]['treino']==before[0]['treino']
 page.locator('#listBtn').tap();page.locator('.aluno-list-item[data-nome="Ana"] .aluno-nome').tap();page.locator('#compareWorkoutBtn').tap();page.locator('#chooseComparePrevious').tap();page.locator('#comparePreviousChoice .compare-version-option').filter(has_text='Anterior 1 (arquivado)').tap();page.locator('#editComparedPreviousOnMain').tap();expect(page.locator('#compareWorkoutsDialog')).not_to_be_visible();expect(badge).to_contain_text('EDITANDO ANTERIOR 1')
 # A failed save blocks leaving and keeps the visible archive draft.
 page.locator('.sec-a .colar-btn').tap();page.locator('#pasteTextarea').fill('A. Peito\nSupino — 6×12');page.locator('#confirmPasteBtn').tap();failed_before=records()
 page.evaluate("()=>{window.originalSet=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(key==='treinoAlunos')throw new DOMException('Full','QuotaExceededError');return originalSet.call(this,key,value);}}")
 page.locator('#saveBtn').tap();expect(badge).to_contain_text('EDITANDO ANTERIOR 1');page.locator('#backToWorkoutCover').tap();expect(badge).to_contain_text('EDITANDO ANTERIOR 1');expect(page.locator('.sec-a ol')).to_contain_text('6×12');assert records()==failed_before
 page.evaluate('()=>{Storage.prototype.setItem=originalSet;}')
 page.evaluate("()=>{const people=JSON.parse(localStorage.getItem('treinoAlunos'));people[0].historicoTreinos[0].treino.A=['Edição externa — 2×10'];localStorage.setItem('treinoAlunos',JSON.stringify(people));}")
 external=records();page.locator('#saveBtn').tap();assert records()==external;expect(page.locator('.sec-a ol')).to_contain_text('6×12');expect(badge).to_contain_text('EDITANDO ANTERIOR 1')
 page.reload();expect(page.locator('.sec-a ol')).to_contain_text('Edição Externa');expect(badge).to_contain_text('EDITANDO ANTERIOR 1');page.locator('#backToWorkoutCover').tap();page.locator('#clearNameBtn').tap();expect(page.locator('#searchName')).to_have_value('');expect(badge).to_have_text('Capa · Treino principal')
 # Missing/repeated legacy IDs retain the exact selected archive slot on load/save/reload.
 page.evaluate("""()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'legacy',nome:'Antigo',treino_id:'shared',treino:{A:['Capa — 3×12']},historicoTreinos:[{workout_id:'shared',treino:{A:['Primeiro — 3×10']}},{treino:{A:['Segundo — 4×10']}}]}]))""")
 page.reload();page.locator('#historyWorkoutBtn').tap();select=page.locator('#historyVersion');slot=select.locator('option[data-history-index="1"]').evaluate('el=>el.index');select.select_option(index=slot);page.locator('#editHistoryVersion').tap();expect(badge).to_contain_text('EDITANDO ANTERIOR 2');expect(page.locator('.sec-a ol')).to_contain_text('Segundo')
 page.locator('.sec-a .clear-btn').tap();page.locator('#saveBtn').tap();legacy=records()[0];assert legacy['treino']['A']==['Capa — 3×12'] and legacy['historicoTreinos'][0]['treino']['A']==['Primeiro — 3×10'] and legacy['historicoTreinos'][1]['treino']['A']==[]
 page.reload();expect(badge).to_contain_text('EDITANDO ANTERIOR 2');expect(page.locator('.sec-a ol')).to_contain_text('Sem exercícios')
 assert not errors,errors
 browser.close();print('PASS: suggestions/history/comparison load exact archive on main editor; warning/save target; normal paste/undo/redo/PDF; archive-only persistence; reload and cover return; pupil switch; failed save blocks leaving and retains draft')
