from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
import base64
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404,body='')
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('https://app.test/treino36/');page.evaluate("""()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino_id:'w1',treino:{A:['Agachamento 3x10']}},{student_id:'b',nome:'Bruno',treino_id:'w2',treino:{A:['Supino 3x10']},obsGuias:[{id:'old',texto:'Não alterar',exameFotos:[{id:'large',src:'data:image/jpeg;base64,'+'A'.repeat(500000)}]}]}]));localStorage.setItem('avaliacao_fisica_alunos','[]');}""");page.reload()
 baseline=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')");page.locator('#obsIconBtn').click();before=page.evaluate('JSON.stringify(localStorage)');page.locator('#toggleInfoRelevanteBtn').click()
 expect(page.locator('#copyTrainingQuestionnaireBtn')).to_be_visible();assert page.evaluate('JSON.stringify(localStorage)')==before
 page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>window.copiedQuestionnaire=text}})")
 page.locator('#copyTrainingQuestionnaireBtn').click();page.wait_for_function('window.copiedQuestionnaire');copied=page.evaluate('window.copiedQuestionnaire')
 assert copied==page.evaluate('ObsAutoSave.questionnaire') and copied.startswith('Para montar seu treino de acordo com seus objetivos e necessidades, me responda:') and '\n7. Qual músculo' in copied
 assert page.locator('#copyTrainingQuestionnaireBtn').evaluate("el=>el.parentElement.querySelector('label').htmlFor==='infoNomeCompleto'")
 assert page.evaluate('JSON.stringify(localStorage)')==before
 # Zero main-thread compression during typing and autosave, even with unrelated photos present.
 cdp=context.new_cdp_session(page);cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
 page.evaluate("""()=>{window.mainCompressionCalls=0;const original=LZString.compressToUTF16;LZString.compressToUTF16=function(...args){window.mainCompressionCalls++;return original.apply(this,args);};}""")
 page.locator('#infoEmail').press_sequentially('ana@example.com',delay=5);page.locator('#infoPeso').fill('64.5');page.locator('#infoWhats').fill('11999998888');expect(page.locator('#obsAutoSaveStatus')).to_contain_text('Salvo automaticamente')
 assert page.evaluate('window.mainCompressionCalls')==0
 # Immediate reload without clicking Save keeps edits through the durable small journal.
 page.reload();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();expect(page.locator('#infoEmail')).to_have_value('ana@example.com');expect(page.locator('#infoPeso')).to_have_value('64.5');expect(page.locator('#infoWhats')).to_have_value('11999998888')
 assert page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')")==[]
 page.locator('#obsTextarea').fill('Observação salva automaticamente');page.reload();page.locator('#obsIconBtn').click();expect(page.locator('#obsTextarea')).to_have_text('Observação salva automaticamente');expect(page.locator('#obsSavedDate')).to_contain_text('OBS salva em')
 expect(page.locator('#obsTextarea')).not_to_be_focused()
 # A background write of an older snapshot cannot lose a newer edit.
 page.locator('#toggleInfoRelevanteBtn').click()
 page.evaluate("""async()=>{const job=TreinoStorage.writeJSON('treinoAlunos',AvaliacaoTreinoSync.read('treinoAlunos'));const input=document.getElementById('infoEmail');input.value='mais-recente@example.com';input.dispatchEvent(new Event('input',{bubbles:true}));await job;}""")
 page.reload();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();expect(page.locator('#infoEmail')).to_have_value('mais-recente@example.com')
 # New OBS tabs and individual photo changes also save without using a Save button.
 page.locator('#addObsTabBtn').click();page.locator('#obsTextarea').fill('Segunda guia');page.locator('#obsExamToggle').click();page.locator('#obsExamResult').fill('Resultado do exame')
 image=page.evaluate("""()=>{const c=document.createElement('canvas');c.width=100;c.height=100;return c.toDataURL('image/png').split(',')[1]}""")
 page.locator('#obsExamFile').set_input_files({'name':'exame.png','mimeType':'image/png','buffer':base64.b64decode(image)});expect(page.locator('.obs-exam-photo')).to_have_count(1)
 page.reload();page.locator('#obsIconBtn').click();page.locator('#obsTabsList .obs-tab-btn').nth(1).click();expect(page.locator('#obsTextarea')).to_have_text('Segunda guia');page.locator('#obsExamToggle').click();expect(page.locator('#obsExamResult')).to_have_text('Resultado do exame');expect(page.locator('.obs-exam-photo')).to_have_count(1)
 page.once('dialog',lambda d:d.accept());page.locator('.obs-exam-photo-delete').click();page.reload();page.locator('#obsIconBtn').click();page.locator('#obsTabsList .obs-tab-btn').nth(1).click();page.locator('#obsExamToggle').click();expect(page.locator('.obs-exam-photo')).to_have_count(0)
 saved=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')");assert saved[0]['treino']==baseline[0]['treino'] and saved[0]['treino_id']==baseline[0]['treino_id'];assert saved[1]==baseline[1]
 assert page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')")==[]
 # Existing explicit Clear must not be undone by unmerged automatic drafts.
 page.locator('#obsTextarea').fill('Texto para limpar');page.once('dialog',lambda d:d.accept());page.locator('#clearObsBtn').click();page.reload();page.locator('#obsIconBtn').click();expect(page.locator('#obsTextarea')).to_have_text('')
 # A new named pupil is created only on an explicit edit, never on opening/copying.
 page.locator('#workoutObsDialog .dialog-actions [data-close]').click();page.locator('#searchName').fill('Nova paciente');page.locator('#obsIconBtn').click();assert len(page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')"))==2
 page.locator('#obsTextarea').fill('Dados da nova paciente');page.reload();expect(page.locator('#searchName')).to_have_value('Nova paciente');page.locator('#obsIconBtn').click();expect(page.locator('#obsTextarea')).to_have_text('Dados da nova paciente');assert len(page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')"))==3;assert page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')")==[]
 # A concurrent assessment adds a new dated ficha; an older autosave cannot remove it or regress its date.
 merged=page.evaluate("""()=>TreinoObsJournal.merge([{student_id:'test',infoGuias:[{id:'one',avaliacaoOrigemData:'12/10/2026'},{id:'two'},{id:'new'}]}],[{studentId:'test',infoOrder:['one','two'],info:[{id:'one',fields:{peso:'70',avaliacaoOrigemData:'01/10/2026'}}]}])[0]""")
 assert len(merged['infoGuias'])==3 and merged['infoGuias'][0]['avaliacaoOrigemData']=='12/10/2026' and merged['infoGuias'][0]['peso']=='70'
 assert not errors,errors
 browser.close();print('PASS: exact questionnaire copy next to contact fields, no writes on opening/copy, immediate durable OBS/ficha autosave, no main compression under CPU4 with unrelated photos, background-write conflict preservation, tab/photo/result/delete autosave, pupil/workout isolation, no assessment auto-creation')
