"""Deletion is explicit, previewed, scoped and guarded against concurrent changes."""
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':600})
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='history.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();page.goto('http://history.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate('''()=>{const treino={},titulos={};for(const section of 'ABCDEF'){treino[section]=Array.from({length:8},(_,i)=>'Exercício '+section+' '+i+' — 3×12');titulos[section]=section+'. Grupo '+section;}localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana',treino_id:'current',treinoNome:'Atual',treinoProtegido:false,treino,titulos,secaoFAtiva:true,obsGuias:[{id:'obs',texto:'Preservar'}],historicoTreinos:[{workout_id:'duplicate',name:'Cópia igual',status:'archived',treino:JSON.parse(JSON.stringify(treino)),titulos,secaoFAtiva:true},{workout_id:'different',name:'Outro ciclo',status:'archived',treino:{A:['Supino — 4×10']},titulos:{A:'A. Peito'},secaoFAtiva:false}]},{student_id:'other',nome:'Outro',treino_id:'only',treino:{A:['Stiff — 3×10']},obsGuias:[{id:'keep',texto:'Não apagar o aluno'}]}]));}''')
 page.reload();page.locator('#historyWorkoutBtn').click();page.locator('#historyVersion').select_option('student-ana');history=page.locator('#workoutHistoryDialog');expect(page.locator('#historyDuplicateStatus')).to_contain_text('Conteúdo repetido')
 # At a short mobile height, the footer and Close button stay completely visible.
 bounds=history.bounding_box();close=history.locator('.dialog-actions [data-close]').bounding_box()
 assert 0<=close['y'] and close['y']+close['height']<=600 and bounds['y']+bounds['height']<=600
 page.screenshot(path='/tmp/history-footer-mobile.png')
 scroll=history.locator('.history-scroll-body');scroll.evaluate('el=>el.scrollTop=el.scrollHeight');assert scroll.evaluate('el=>el.scrollHeight>el.clientHeight')
 page.locator('#historyVersion').select_option('duplicate');page.locator('#deleteHistoryVersion').click();dialog=page.locator('#historyDeleteDialog')
 page.screenshot(path='/tmp/history-delete-preview-mobile.png')
 expect(page.locator('#historyDeleteIdentity')).to_contain_text('Cópia igual');expect(page.locator('#historyDeletePreview')).to_contain_text('F. Grupo F');expect(page.locator('#historyDeleteDuplicate')).to_contain_text('Capa atual')
 original=page.evaluate("localStorage.getItem('treinoAlunos')");dialog.get_by_role('button',name='Cancelar',exact=True).click();assert page.evaluate("localStorage.getItem('treinoAlunos')")==original
 page.locator('#deleteHistoryVersion').click();page.locator('#confirmDeleteHistoryVersion').click();expect(dialog).not_to_be_visible()
 def records():return page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
 assert [v['workout_id'] for v in records()[0]['historicoTreinos']]==['different'];assert records()[0]['treino']['F'] and records()[1]['treino']['A']==['Stiff — 3×10']
 assert page.evaluate("WorkoutHistoryTools.signature({treino:{A:['SUPINO — 3 × 12']}})===WorkoutHistoryTools.signature({treino:{A:['supino - 3x12']}})")
 # Changed prescriptions must never be labelled duplicates merely for sharing exercises.
 assert page.evaluate("WorkoutHistoryTools.signature({treino:{A:['Supino 3x12']}})!==WorkoutHistoryTools.signature({treino:{A:['Supino 4x12']}})")
 page.locator('#historyVersion').select_option('different');page.locator('#deleteHistoryVersion').click()
 page.evaluate("TreinoStorage.stageObs('ana',{obs:[{id:'obs',fields:{texto:'Edição em outra aba'}}]})")
 page.locator('#confirmDeleteHistoryVersion').click();expect(page.locator('#historyDeleteStatus')).to_contain_text('Os dados mudaram');assert len(records()[0]['historicoTreinos'])==1;dialog.get_by_role('button',name='Cancelar',exact=True).click()
 # A failed deletion write keeps the selected version intact.
 page.locator('#deleteHistoryVersion').click();before=page.evaluate("localStorage.getItem('treinoAlunos')")
 page.evaluate("()=>{window.restoreSet=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(key==='treinoAlunos')throw new DOMException('Full','QuotaExceededError');return restoreSet.call(this,key,value)}}")
 page.locator('#confirmDeleteHistoryVersion').click();expect(page.locator('#historyDeleteStatus')).to_contain_text('O treino foi mantido');assert page.evaluate("localStorage.getItem('treinoAlunos')")==before
 page.evaluate('()=>{Storage.prototype.setItem=restoreSet;}');dialog.get_by_role('button',name='Cancelar',exact=True).click()
 # Deleting a cover requires choosing and previewing a replacement when available.
 page.locator('#historyVersion').select_option('student-ana');page.locator('#deleteHistoryVersion').click();expect(page.locator('#confirmDeleteHistoryVersion')).to_be_disabled();page.locator('#historyReplacementChoice').select_option('different');expect(page.locator('#historyReplacementPreview')).to_contain_text('Supino');page.locator('#confirmDeleteHistoryVersion').click()
 assert records()[0]['treino']['A']==['Supino — 4×10'] and records()[0]['historicoTreinos'][0]['workout_id']=='different'
 assert records()[0]['obsGuias'][0]['texto']=='Edição em outra aba'
 # A lone cover can be cleared while the student and notes remain.
 page.locator('#historyVersion').select_option('student-other');page.locator('#deleteHistoryVersion').click();expect(page.locator('#historyDeleteHint')).to_contain_text('treino vazio');page.locator('#confirmDeleteHistoryVersion').click()
 assert all(not lines for lines in records()[1]['treino'].values()) and records()[1]['obsGuias'][0]['texto']=='Não apagar o aluno'
 assert records()[0]['treino']['A']==['Supino — 4×10']
 browser.close();print('PASS: visible mobile footer, full delete preview/cancel, conservative duplicate indication, exact selected history removal, stale/quota protection and safe cover replacement/clearing')
