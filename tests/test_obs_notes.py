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
 page.locator('#obsCopyPrescriptionBtn').click();expect(page.locator('#obsTextarea')).to_contain_text('Cuidados especiais');expect(page.locator('#obsTextarea')).to_contain_text('Agachamento 3x10')
 expect(page.locator('#obsExamBody')).not_to_be_visible();expect(page.locator('#obsExamBadge')).not_to_be_visible()
 stored_before=page.evaluate('JSON.stringify(localStorage)')
 assert page.locator('#obsCopyPrescriptionBtn').evaluate("el=>el.parentElement.classList.contains('obs-exam-header')")
 page.locator('#obsExamToggle').click();expect(page.locator('#obsExamToggle')).to_have_attribute('aria-expanded','true')
 assert page.evaluate('JSON.stringify(localStorage)')==stored_before
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
 expect(page.locator('#obsExamImage')).to_be_visible();page.locator('#saveOnlyObsBtn').click()
 expect(page.locator('#obsExamBadge')).to_be_visible()
 page.locator('#obsExamToggle').click();expect(page.locator('#obsExamBody')).not_to_be_visible();expect(page.locator('#obsExamBadge')).to_be_visible();page.locator('#saveOnlyObsBtn').click()
 page.locator('#obsExamToggle').click()
 expect(page.locator('#workoutObsDialog')).to_be_visible();expect(page.locator('#obsSavedDate')).to_contain_text('OBS salva em')
 data=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')");g=data[0]['obsGuias'][0]
 assert '<b>' in g['textoHtml'] or '<strong>' in g['textoHtml'];assert g['exameResultado']==expected_result and g['exameFoto'].startswith('data:image/jpeg') and g['obsSalvaEm'],repr(g['exameResultado'])
 assert not page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')");assert data[0]['treino']==baseline and data[0]['treino_id']=='w1';assert not data[1].get('obsGuias')
 assert page.locator('#obsExamImage').bounding_box()['width']<=96
 page.locator('#obsExamView').click();expect(page.locator('.obs-exam-viewer')).to_be_visible();page.locator('.obs-exam-viewer button').click()
 page.reload();page.locator('#obsIconBtn').click();expect(page.locator('#obsExamBody')).not_to_be_visible();expect(page.locator('#obsExamBadge')).to_be_visible();page.locator('#obsExamToggle').click();expect(page.locator('#obsExamImage')).to_be_visible();expect(page.locator('#obsExamResult')).to_have_text(expected_result,use_inner_text=True);assert page.locator('#obsTextarea b, #obsTextarea strong').count()==1
 page.locator('#addObsTabBtn').click();expect(page.locator('#obsExamBadge')).not_to_be_visible();expect(page.locator('#obsExamImage')).not_to_be_visible();page.locator('#obsTextarea').fill('Outra guia');page.locator('#saveOnlyObsBtn').click()
 page.locator('#obsTabsList .obs-tab-btn').first.click();expect(page.locator('#obsExamBody')).not_to_be_visible();expect(page.locator('#obsExamBadge')).to_be_visible();page.locator('#obsExamToggle').click();expect(page.locator('#obsExamImage')).to_be_visible();expect(page.locator('#obsExamResult')).to_have_text(expected_result,use_inner_text=True)
 page.locator('#obsExamDelete').click();page.locator('#saveOnlyObsBtn').click();assert not page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].obsGuias[0].exameFoto");expect(page.locator('#obsExamBadge')).to_be_visible()
 page.locator('#obsExamResult').fill('');expect(page.locator('#obsExamBadge')).not_to_be_visible();page.locator('#saveOnlyObsBtn').click()
 # Sanitization preserves only text and supported formatting.
 assert page.evaluate("ObsNotes.clean('<img src=x onerror=alert(1)><b onclick=alert(1)>Seguro</b><script>alert(1)</script>')")=='<b>Seguro</b>'
 assert not errors,errors
 browser.close();print('PASS: legacy notes, bold/undo/redo, optional prescription append, compressed thumbnail/view/delete, typed result, guide isolation, independent dated save, durable reload, no evaluation/workout side effects, HTML sanitization')
