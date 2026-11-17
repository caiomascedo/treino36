from pathlib import Path
from urllib.parse import urlparse
import os
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if os.getenv('GIF_TEST_BROWSER')=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url);f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='paste.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:(errors.append(str(e)),print(str(e))));page.goto('https://paste.test/');page.evaluate('TreinoStorage.ready')
 seed=[{'student_id':'ana','nome':'Ana','treino_id':'active','treinoNome':'Ciclo atual','treino':{'A':['Supino — 3×12 [Vídeo: https://youtu.be/abcdefghijk]'],'B':['Rosca — 2×10']},'titulos':{'A':'A. Peito','B':'B. Braços'},'obsGuias':[{'id':'note','texto':'Preservar'}],'historicoTreinos':[{'workout_id':'old','name':'Ciclo antigo','treino':{'A':['Remada — 4×10 [Vídeo: https://youtu.be/klmnopqrstu]'],'B':['Flexora — 3×10']},'titulos':{'A':'A. Costas','B':'B. Pernas'}}]}, {'student_id':'bia','nome':'Bia','treino_id':'bia-active','treino':{'A':['Agachamento — 3×10']}}]
 page.evaluate('(s)=>localStorage.setItem("treinoAlunos",JSON.stringify(s))',seed);page.reload();page.evaluate('TreinoStorage.ready');page.wait_for_function('document.querySelector("#searchName").value==="Ana"')
 page.evaluate('Object.defineProperty(navigator,"clipboard",{value:{writeText:async(t)=>{window.copiedText=t}}})')
 def records():return page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))')
 baseline=records();area=page.locator('#pasteTextarea')
 # Both the whole-workout and individual modes use the same real text undo/redo and clipboard tools.
 for opener in ['#fullTreinoBtn','.sec-a .colar-btn']:
  page.locator(opener).click();area.fill('A. Rascunho\n1. Extensora — 3×12');page.locator('#pasteCopyAll').click();assert page.evaluate('copiedText')==area.input_value()
  page.once('dialog',lambda d:d.dismiss());page.locator('#pasteClearAll').click();assert 'Extensora' in area.input_value()
  text=area.input_value();page.once('dialog',lambda d:d.accept());page.locator('#pasteClearAll').click();expect(area).to_have_value('');page.locator('#pasteUndoBtn').click();expect(area).to_have_value(text);expect(page.locator('#pasteRedoBtn')).to_be_enabled();page.locator('#pasteRedoBtn').click();expect(area).to_have_value('');page.locator('#cancelPasteBtn').click();assert records()==baseline
 # Load and autosave the current cover; it is edited in place and reflected on the main screen.
 page.locator('#fullTreinoBtn').click();page.locator('#pasteLoadVersion').click();expect(page.locator('#pasteSavedStatus')).to_contain_text('Capa atual');expect(page.locator('#pasteUndoBtn')).to_be_disabled()
 original=area.input_value();area.fill(original.replace('3×12','5×8'))
 page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A[0].includes("5×8")');expect(page.locator('.sec-a ol')).to_contain_text('5×8');assert records()[0]['historicoTreinos']==baseline[0]['historicoTreinos'];assert 'abcdefghijk' in records()[0]['treino']['A'][0]
 page.locator('#pasteUndoBtn').click();page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A[0].includes("3×12")');page.locator('#pasteRedoBtn').click();page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A[0].includes("5×8")')
 # Individual loading targets one exact previous workout, without touching its other sections or the cover.
 page.locator('#cancelPasteBtn').click();page.locator('.sec-a .colar-btn').click();options=page.locator('#pasteSavedVersion option').evaluate_all('(xs)=>xs.map(x=>x.value)');archive=next(v for v in options if v.startswith('archive:'));page.locator('#pasteSavedVersion').select_option(archive);page.locator('#pasteLoadVersion').click();expect(page.locator('#pasteSavedStatus')).to_contain_text('Anterior 1');assert 'Flexora' not in area.input_value()
 cover=records()[0]['treino'];area.fill(area.input_value().replace('4×10','6×10'));page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].historicoTreinos[0].treino.A[0].includes("6×10")');assert records()[0]['treino']==cover;assert records()[0]['historicoTreinos'][0]['treino']['B']==baseline[0]['historicoTreinos'][0]['treino']['B'];assert 'klmnopqrstu' in records()[0]['historicoTreinos'][0]['treino']['A'][0];assert len(records()[0]['historicoTreinos'][0]['revisoes'])==1
 before_clear=area.input_value();page.once('dialog',lambda d:d.accept());page.locator('#pasteClearAll').click();page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].historicoTreinos[0].treino.A.length===0');page.locator('#pasteUndoBtn').click();expect(area).to_have_value(before_clear);page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].historicoTreinos[0].treino.A.length===1');assert 'klmnopqrstu' in records()[0]['historicoTreinos'][0]['treino']['A'][0]
 # With automatic saving off, Save explicitly persists the loaded version.
 page.locator('#pasteSavedAuto').uncheck();area.fill(area.input_value().replace('6×10','7×10'));page.wait_for_timeout(650);assert '7×10' not in records()[0]['historicoTreinos'][0]['treino']['A'][0];page.locator('#confirmPasteBtn').click();assert '7×10' in records()[0]['historicoTreinos'][0]['treino']['A'][0]
 assert records()[1]==baseline[1] and records()[0]['obsGuias']==baseline[0]['obsGuias']
 # Both comparison columns have a direct route to the same version editor.
 page.locator('#compareWorkoutBtn').click();page.locator('#compareEditPasteprevious').click();expect(page.locator('#pasteSavedStatus')).to_contain_text('Anterior 1')
 page.locator('#cancelPasteBtn').click();page.locator('#compareWorkoutBtn').click();page.locator('#compareEditPastecurrent').click();expect(page.locator('#pasteSavedStatus')).to_contain_text('Capa atual')
 # Failed writes retain the saved cover and the typed draft; manual retry can save it.
 before_failure=records();draft=area.input_value().replace('5×8','9×12')
 page.evaluate("()=>{window.originalSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='treinoAlunos')throw new DOMException('Full','QuotaExceededError');return originalSet.call(this,k,v)}}")
 area.fill(draft);expect(page.locator('#pasteSavedStatus')).to_contain_text('Não foi possível salvar');assert records()==before_failure;expect(area).to_have_value(draft)
 page.evaluate('()=>{Storage.prototype.setItem=originalSet;}');page.locator('#confirmPasteBtn').click();assert '9×12' in records()[0]['treino']['A'][0]
 # A stale editor cannot overwrite a training change made elsewhere.
 page.locator('#fullTreinoBtn').click();page.locator('#pasteLoadVersion').click()
 page.evaluate('()=>{const s=JSON.parse(localStorage.getItem("treinoAlunos"));s[0].treino.A=["Edição externa — 2×10"];localStorage.setItem("treinoAlunos",JSON.stringify(s))}')
 external=records();area.fill('A. Outro texto\n1. Supino — 8×10');expect(page.locator('#pasteSavedStatus')).to_contain_text('mudou fora do editor');assert records()==external
 page.once('dialog',lambda d:d.accept());page.locator('#pasteLoadVersion').click();assert 'Edição externa' in area.input_value()
 for width in [390,320]:
  page.set_viewport_size({'width':width,'height':844});assert page.locator('.paste-modal-card').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
 # A loaded source can become a new cover through the existing confirmed archive flow.
 page.locator('#pasteSavedVersion').select_option(archive);page.locator('#pasteLoadVersion').click();before_new=records()[0];page.locator('#pasteSavedAuto').uncheck();area.fill('A. Novo ciclo\n1. Remada — 10×10');page.locator('#pasteAsNewCover').click();page.locator('#confirmPasteBtn').click();page.locator('#pasteArchiveYes').click()
 assert len(records()[0]['historicoTreinos'])==len(before_new['historicoTreinos'])+1, page.locator('#pasteCoverChoiceStatus').inner_text();assert records()[0]['historicoTreinos'][-1]['treino']==before_new['treino'];assert '10×10' in records()[0]['treino']['A'][0];assert 'klmnopqrstu' in records()[0]['treino']['A'][0]
 assert not errors,errors
 b.close();print('PASS: copy/confirmed clear/undo/redo in full and individual editors; exact cover/archive load, automatic/manual saving, main sync, media after clear/undo, archive revisions and comparison routes; other data untouched')
