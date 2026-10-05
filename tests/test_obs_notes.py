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
 page.goto('http://app.test/treino36/')
 page.evaluate("""()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino_id:'w1',treino:{A:['Agachamento 3x10']},observacoes:'Orientação antiga'},{student_id:'b',nome:'Bruno',treino_id:'w2',treino:{A:['Supino 3x10']}}]));localStorage.setItem('avaliacao_fisica_alunos','[]');}""")
 page.reload();baseline=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].treino");page.locator('#obsIconBtn').click();expect(page.locator('#obsTextarea')).to_have_text('Orientação antiga')
 page.locator('#obsTextarea').fill('Cuidados especiais')
 page.evaluate("""()=>{const el=document.getElementById('obsTextarea'),r=document.createRange();r.selectNodeContents(el);getSelection().removeAllRanges();getSelection().addRange(r);}""");page.wait_for_timeout(100)
 page.locator('#obsBoldBtn').click();assert page.locator('#obsTextarea b, #obsTextarea strong').count()==1
 page.locator('#obsUndoBtn').click();assert page.locator('#obsTextarea b, #obsTextarea strong').count()==0
 page.locator('#obsRedoBtn').click();assert page.locator('#obsTextarea b, #obsTextarea strong').count()==1
 expect(page.locator('#obsExamBody')).not_to_be_visible();expect(page.locator('#obsExamBadge')).not_to_be_visible()
 footer_buttons=page.locator('#workoutObsDialog .dialog-actions>button')
 boxes=[footer_buttons.nth(i).bounding_box() for i in range(footer_buttons.count())]
 assert len(boxes)==4 and max(b['y'] for b in boxes)-min(b['y'] for b in boxes)<2
 assert boxes[-1]['x']+boxes[-1]['width']<=page.locator('#workoutObsDialog').bounding_box()['x']+page.locator('#workoutObsDialog').bounding_box()['width']
 stored_before=page.evaluate('JSON.stringify(localStorage)')
 assert page.locator('#obsCopyPrescriptionBtn').evaluate("el=>el.parentElement.id==='obsExamBody'");expect(page.locator('#obsCopyPrescriptionBtn')).not_to_be_visible()
 page.locator('#obsExamToggle').click();expect(page.locator('#obsExamToggle')).to_have_attribute('aria-expanded','true')
 assert page.evaluate('JSON.stringify(localStorage)')==stored_before
 page.locator('#obsCopyPrescriptionBtn').click();expect(page.locator('#obsTextarea')).to_contain_text('Cuidados especiais');expect(page.locator('#obsTextarea')).to_contain_text('Agachamento 3x10')
 # Clipboard rich HTML and plain ChatGPT markdown both preserve bold safely.
 page.locator('#obsExamResult').focus()
 page.evaluate("""()=>{const data=new DataTransfer();data.setData('text/html','<p>Resultado <strong>importante</strong><img src=x onerror=alert(1)></p>');data.setData('text/plain','Resultado importante');document.getElementById('obsExamResult').dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}));}""")
 expect(page.locator('#obsExamResult strong')).to_have_text('importante');assert page.locator('#obsExamResult img').count()==0
 page.locator('#obsExamResult').fill('')
 page.evaluate("""()=>{const data=new DataTransfer();data.setData('text/plain','Resultado **importante**');document.getElementById('obsExamResult').dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}));}""")
 expect(page.locator('#obsExamResult strong')).to_have_text('importante')
 page.locator('#obsExamResult').fill('Resultado digitado\ndo exame')
 # Browser-generated image avoids dependencies on image codecs in fixtures.
 image=page.evaluate("""()=>{const c=document.createElement('canvas');c.width=1800;c.height=2400;const ctx=c.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='black';ctx.font='80px Arial';ctx.fillText('Exame',100,100);return c.toDataURL('image/png').split(',')[1];}""")
 page.locator('#obsExamFile').set_input_files({'name':'exame.png','mimeType':'image/png','buffer':base64.b64decode(image)})
 expected_result=page.locator('#obsExamResult').inner_text()
 expect(page.locator('.obs-exam-photo img').first).to_be_visible();page.locator('#saveOnlyObsBtn').click()
 expect(page.locator('#obsExamBadge')).to_be_visible()
 page.locator('#obsExamToggle').click();expect(page.locator('#obsExamBody')).not_to_be_visible();expect(page.locator('#obsExamBadge')).to_be_visible();page.locator('#saveOnlyObsBtn').click()
 page.locator('#obsExamToggle').click()
 expect(page.locator('#workoutObsDialog')).to_be_visible();expect(page.locator('#obsSavedDate')).to_contain_text('OBS salva em')
 data=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')");g=data[0]['obsGuias'][0]
 assert '<b>' in g['textoHtml'] or '<strong>' in g['textoHtml'];assert g['exameResultado']==expected_result and len(g['exameFotos'])==1 and g['exameFotos'][0]['src'].startswith('data:image/jpeg') and g['obsSalvaEm'],repr(g['exameResultado'])
 assert not page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')");assert data[0]['treino']==baseline and data[0]['treino_id']=='w1';assert not data[1].get('obsGuias')
 # Multiple selection appends photos rather than replacing the first one.
 photo_payload={'name':'exame-2.png','mimeType':'image/png','buffer':base64.b64decode(image)}
 page.locator('#obsExamFile').set_input_files([photo_payload,dict(photo_payload,name='exame-3.png')]);expect(page.locator('.obs-exam-photo')).to_have_count(3)
 page.locator('#saveOnlyObsBtn').click();saved_photos=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].obsGuias[0].exameFotos");assert len(saved_photos)==3 and len(set(p['id'] for p in saved_photos))==3
 assert page.locator('.obs-exam-photo img').first.bounding_box()['width']<=96
 # File sharing on mobile offers the photo to the device's native save/share sheet.
 page.evaluate("""()=>{Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{window.sharedPhoto={name:data.files[0].name,type:data.files[0].type,size:data.files[0].size};}});}""")
 page.locator('.obs-exam-photo-save').first.click();page.wait_for_function('window.sharedPhoto');assert page.evaluate('window.sharedPhoto.type')=='image/jpeg' and page.evaluate('window.sharedPhoto.size')>0
 page.evaluate("Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>false})")
 with page.expect_download() as downloaded:page.locator('.obs-exam-photo-save').nth(1).click()
 assert downloaded.value.suggested_filename=='exame-2.jpg'
 assert Path(downloaded.value.path()).read_bytes().startswith(b'\xff\xd8')
 page.locator('.obs-exam-photo-view').first.click();expect(page.locator('.obs-exam-viewer')).to_be_visible();page.locator('.obs-exam-viewer button').click()
 page.reload();page.locator('#obsIconBtn').click();expect(page.locator('#obsExamBody')).not_to_be_visible();expect(page.locator('#obsExamBadge')).to_be_visible();page.locator('#obsExamToggle').click();expect(page.locator('.obs-exam-photo img').first).to_be_visible();expect(page.locator('#obsExamResult')).to_have_text(expected_result,use_inner_text=True);assert page.locator('#obsTextarea b, #obsTextarea strong').count()==1
 page.locator('#addObsTabBtn').click();expect(page.locator('#obsExamBadge')).not_to_be_visible();expect(page.locator('.obs-exam-photo img')).not_to_be_visible();page.locator('#obsTextarea').fill('Outra guia');page.locator('#saveOnlyObsBtn').click()
 page.locator('#obsTabsList .obs-tab-btn').first.click();expect(page.locator('#obsExamBody')).not_to_be_visible();expect(page.locator('#obsExamBadge')).to_be_visible();page.locator('#obsExamToggle').click();expect(page.locator('.obs-exam-photo img').first).to_be_visible();expect(page.locator('#obsExamResult')).to_have_text(expected_result,use_inner_text=True)
 page.locator('.obs-exam-photo-delete').nth(1).click();page.locator('#saveOnlyObsBtn').click();remaining=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].obsGuias[0].exameFotos");assert [p['id'] for p in remaining]==[saved_photos[0]['id'],saved_photos[2]['id']]
 page.locator('.obs-exam-photo-delete').first.click();page.locator('.obs-exam-photo-delete').first.click();page.locator('#saveOnlyObsBtn').click();assert not page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].obsGuias[0].exameFotos");expect(page.locator('#obsExamBadge')).to_be_visible()
 page.locator('#obsExamResult').fill('');expect(page.locator('#obsExamBadge')).not_to_be_visible();page.locator('#saveOnlyObsBtn').click()
 # Existing single-photo backups remain readable and migrate when another photo is added.
 page.reload();page.evaluate("""()=>{const records=AvaliacaoTreinoSync.read('treinoAlunos'),canvas=document.createElement('canvas');canvas.width=10;canvas.height=10;records[0].obsGuias=[{id:'legacy',texto:'OBS antiga',exameFoto:canvas.toDataURL('image/png')}];localStorage.setItem('treinoAlunos',JSON.stringify(records));}""");page.reload();page.locator('#obsIconBtn').click();expect(page.locator('#obsExamBadge')).to_be_visible();page.locator('#obsExamToggle').click();expect(page.locator('.obs-exam-photo')).to_have_count(1)
 page.locator('#obsExamFile').set_input_files(photo_payload);expect(page.locator('.obs-exam-photo')).to_have_count(2);page.locator('#saveOnlyObsBtn').click();migrated=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].obsGuias[0]");assert len(migrated['exameFotos'])==2 and migrated['exameFotos'][0]['src'].startswith('data:image/png') and not migrated.get('exameFoto')
 # Sanitization preserves only text and supported formatting.
 assert page.evaluate("ObsNotes.clean('<img src=x onerror=alert(1)><b onclick=alert(1)>Seguro</b><script>alert(1)</script>')")=='<b>Seguro</b>'
 assert not errors,errors
 browser.close();print('PASS: legacy notes, bold/undo/redo, optional prescription append, compressed thumbnail/view/delete, typed result, guide isolation, independent dated save, durable reload, no evaluation/workout side effects, HTML sanitization')
