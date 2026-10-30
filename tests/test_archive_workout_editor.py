"""Editing an archive uses an isolated text/section draft and never replaces the cover."""
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':600},is_mobile=True,has_touch=True)
 context.add_init_script("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{readText:async()=>window.pasteText||''}})")
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='archive.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://archive.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate("""()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana',treino_id:'cover',treinoNome:'Capa atual',atualizadoEm:'2026-10-26T15:00:00Z',treino:{A:['Agachamento — 3×12']},titulos:{A:'A. Pernas'},infoRelevante:{email:'preservar@exemplo.test'},historicoTreinos:[{workout_id:'old',name:'Ciclo antigo',student_id:'ana',status:'archived',archived_at:'2026-10-20T15:00:00Z',treino:{A:['Supino — 4×10 [Vídeo: https://youtu.be/AbC123?list=KeepCASE]'],B:['Remada — 3×12']},titulos:{A:'A. Peito',B:'B. Costas'},secaoFAtiva:false},{workout_id:'other',name:'Outro anterior',treino:{A:['Flexora — 3×10']}}]},{student_id:'bia',nome:'Bia',treino_id:'bia-cover',treino:{A:['Stiff — 3×12']}}]))""")
 page.reload();page.locator('#historyWorkoutBtn').tap();page.locator('#historyVersion').select_option('old');page.locator('#editHistoryTextVersion').tap()
 dialog=page.locator('#archiveWorkoutEditor');source=dialog.get_by_role('textbox',name='Texto completo do treino anterior',exact=True)
 def records():return page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
 before=records();expect(dialog).to_be_visible();expect(dialog.locator('.archive-edit-warning')).to_contain_text('EDITANDO ANTERIOR 1 · Ana');expect(dialog.locator('.archive-edit-warning')).to_contain_text('Capa atual: Capa atual')
 assert 'KeepCASE' in source.input_value() and 'Remada' in source.input_value()
 dialog.get_by_role('button',name='Salvar anterior',exact=True).tap();expect(dialog.get_by_role('status')).to_contain_text('Nenhuma alteração');assert records()==before
 source.fill(source.input_value().replace('4×10','5×10'));dialog.get_by_role('button',name='Cancelar',exact=True).tap();assert records()==before
 page.locator('#editHistoryTextVersion').tap();source.fill(source.input_value().replace('4×10','5×10'));source.press('Control+z');assert '4×10' in source.input_value();source.press('Control+Shift+z');assert '5×10' in source.input_value();dialog.get_by_role('button',name='Ver seções',exact=True).tap();expect(dialog.get_by_role('textbox',name='Editar seção B do anterior',exact=True)).to_be_visible()
 section=dialog.get_by_role('textbox',name='Editar seção B do anterior',exact=True);section.fill('B. Costas\n1. Remada — 4×12\n2. Puxador — 3×10')
 dialog.get_by_role('button',name='Desfazer no anterior',exact=True).tap();dialog.get_by_role('button',name='Refazer no anterior',exact=True).tap()
 dialog.get_by_role('button',name='⛶ Tela inteira',exact=True).tap();bounds=dialog.bounding_box();assert bounds['height']==600 and bounds['width']==390
 footer=dialog.get_by_role('button',name='Salvar anterior',exact=True).bounding_box();assert footer['y']+footer['height']<=600
 page.screenshot(path='/tmp/archive-editor-sections-mobile.png')
 dialog.get_by_role('button',name='Salvar anterior',exact=True).tap();expect(dialog).not_to_be_visible();after=records();old=after[0]['historicoTreinos'][0]
 assert old['treino']['A']==['Supino — 5×10 [Vídeo: https://youtu.be/AbC123?list=KeepCASE]'] and old['treino']['B']==['Remada — 4×12','Puxador — 3×10']
 assert old['archived_at']==before[0]['historicoTreinos'][0]['archived_at'] and old['edited_at'] and old['revisoes'][0]['treino']==before[0]['historicoTreinos'][0]['treino']
 assert after[0]['treino']==before[0]['treino'] and after[0]['treino_id']=='cover' and after[0]['titulos']==before[0]['titulos'] and after[0]['atualizadoEm']==before[0]['atualizadoEm'] and after[0]['infoRelevante']==before[0]['infoRelevante'] and after[0]['historicoTreinos'][1]==before[0]['historicoTreinos'][1] and after[1]==before[1]
 expect(page.locator('#historyVersion')).to_have_value('old');expect(page.locator('#historyPromotionStatus')).to_contain_text('A capa atual foi mantida')
 # Clipboard updates mentioned sections only and allows F to be explicitly enabled.
 page.locator('#editHistoryTextVersion').tap();page.evaluate("window.pasteText='A. Peito novo\\n1. Supino inclinado — 3×12\\nF. Mobilidade\\n1. Alongamento — 3×20'");dialog.get_by_role('button',name='Colar',exact=True).tap();dialog.get_by_role('checkbox').check();page.evaluate("()=>{const people=JSON.parse(localStorage.getItem('treinoAlunos'));people[1].observacoes='Atualização paralela';localStorage.setItem('treinoAlunos',JSON.stringify(people));}");dialog.get_by_role('button',name='Salvar anterior',exact=True).tap();saved=records();assert saved[1]['observacoes']=='Atualização paralela';assert saved[0]['historicoTreinos'][0]['treino']['B']==old['treino']['B'] and saved[0]['historicoTreinos'][0]['secaoFAtiva'] is True and saved[0]['secaoFAtiva'] is False
 # A stale version and a quota failure retain the editable draft and all saved data.
 page.locator('#editHistoryTextVersion').tap();source.fill(source.input_value().replace('3×12','6×12'))
 page.evaluate("()=>{const people=JSON.parse(localStorage.getItem('treinoAlunos'));people[0].historicoTreinos[0].treino.A=['Edição externa — 2×10'];localStorage.setItem('treinoAlunos',JSON.stringify(people));}")
 dialog.get_by_role('button',name='Salvar anterior',exact=True).tap();expect(dialog.get_by_role('status')).to_contain_text('mudou em outra janela');expect(dialog).to_be_visible();assert '6×12' in source.input_value();dialog.get_by_role('button',name='Cancelar',exact=True).tap()
 page.locator('#workoutHistoryDialog .dialog-actions [data-close]').tap();page.reload();page.locator('#historyWorkoutBtn').tap();page.locator('#historyVersion').select_option('old');page.locator('#editHistoryTextVersion').tap();source.fill(source.input_value()+'\n2. Novo — 3×10');before_failure=records()
 page.evaluate("()=>{window.originalSet=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(key==='treinoAlunos')throw new DOMException('Full','QuotaExceededError');return originalSet.call(this,key,value);}}")
 dialog.get_by_role('button',name='Salvar anterior',exact=True).tap();expect(dialog.get_by_role('status')).to_contain_text('rascunho foi mantido');assert records()==before_failure
 page.evaluate('()=>{Storage.prototype.setItem=originalSet;}');dialog.get_by_role('button',name='Cancelar',exact=True).tap();page.locator('#workoutHistoryDialog .dialog-actions [data-close]').tap()
 page.evaluate("""()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'legacy',nome:'Antigo',treino_id:'cover',treino:{A:['Capa — 3×12']},historicoTreinos:[{workout_id:'cover',treino:{A:['Anterior um — 3×10']}},{treino:{A:['Anterior dois — 4×10']}}]}]))""")
 page.reload();page.locator('#historyWorkoutBtn').tap();selection=page.locator('#historyVersion');slot=selection.locator('option[data-history-index="1"]').evaluate('el=>el.index');selection.select_option(index=slot);page.locator('#editHistoryTextVersion').tap();expect(dialog.locator('.archive-edit-warning')).to_contain_text('EDITANDO ANTERIOR 2')
 source.fill('A. Treino antigo\n1. Supino — 5×12');dialog.get_by_role('button',name='Salvar anterior',exact=True).tap();legacy=records()[0]
 assert legacy['treino']['A']==['Capa — 3×12'] and legacy['historicoTreinos'][0]['treino']['A']==['Anterior um — 3×10'] and legacy['historicoTreinos'][1]['treino']['A']==['Supino — 5×12'] and 'workout_id' not in legacy['historicoTreinos'][1]
 assert not errors,errors
 browser.close();print('PASS: explicit archived-edit banner; full text/section edits; cancel and no-op; links, order and omitted sections retained; isolated save and revision; F flag isolated; fullscreen footer; stale/quota protection retains draft')
