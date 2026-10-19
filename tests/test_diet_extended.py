import base64,re,urllib.request
from pathlib import Path
from urllib.parse import urlparse
import fitz
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
URL='https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'
script=urllib.request.urlopen(URL,timeout=30).read()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 context.add_init_script("""window.shared=[];window.opens=0;window.pdfFiles=new Map();const createPDFURL=URL.createObjectURL.bind(URL);URL.createObjectURL=file=>{const url=createPDFURL(file);pdfFiles.set(url,file);return url;};window.open=()=>{window.opens++;return {closed:false,document:{title:'',body:{textContent:''}},location:{replace:url=>shared.push({files:[pdfFiles.get(url)]})}};};Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{shared.push(data);}});Object.defineProperty(navigator,'userActivation',{configurable:true,value:{isActive:true}});""")
 def route(r):
  if r.request.url==URL:r.fulfill(body=script,content_type='application/javascript');return
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404,body='')
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://app.test/treino36/')
 page.evaluate("""()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',infoRelevante:{idade:'30',altura:'1.65',peso:'60'},treino:{A:['Agachamento 3x10']},avaliacaoId:10},{student_id:'b',nome:'Bruno',treino:{A:['Supino 3x10']}}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',treinoStudentIds:['a'],sexo:'F',idade:'30',altura:'1.65',avaliacoes:[{id:11,peso:'65'}]}]));}""");page.evaluate("value=>localStorage.setItem('dieta36_rascunho_v1:a',value)",'Almoço\nArroz e feijão');page.reload()
 original=page.evaluate("[localStorage.getItem('treinoAlunos'),localStorage.getItem('avaliacao_fisica_alunos')]")
 page.locator('#dietBtn').click();expect(page.locator('#dietText')).to_have_value('Almoço\nArroz e feijão');page.locator('#dietCalculations > summary').click()
 expect(page.locator('#dietTmb')).to_have_text('1.486');expect(page.locator('#dietTotals')).to_contain_text('2.303')
 for key in ['sex','age','height','weight','activity']:assert page.locator('#diet-'+key).count()==0
 for mode,value in [('tmb','1.486'),('deficit','1.903'),('surplus','2.603'),('daily','2.303')]:
  page.locator('[data-diet-goal="'+mode+'"]').click();expect(page.locator('#dietTotals')).to_contain_text('Meta: '+value)

 text='Café da manhã\n2 ovos · 140 kcal\nPão · 100 kcal\nTotal: 240 kcal\nMacros:\nCarbo: 45g | Prot: 12g | Gord: 8g\n;\n• ;\nAlmoço\nMacros:\nCarbo: 50g | Prot: 35g | Gord: 12g'
 page.locator('#dietText').fill(text);expect(page.locator('#dietTotals')).to_contain_text('688 kcal')
 compactHeight=page.locator('#dietText').bounding_box()['height'];assert compactHeight<=150
 page.locator('#dietText').evaluate('el=>{el.focus();el.setSelectionRange(8,12)}')
 page.locator('#dietPasteExpandBtn').click();expect(page.locator('#dietPasteExpandBtn')).to_have_attribute('aria-pressed','true');assert page.locator('#dietText').bounding_box()['height']>compactHeight*2
 assert page.locator('#dietText').evaluate('el=>[el.selectionStart,el.selectionEnd]')==[8,12]
 expect(page.locator('#dietText')).to_have_value(text);expect(page.locator('.diet-history')).to_be_visible();expect(page.locator('#dietPdfBtn')).not_to_be_visible()
 page.locator('#dietPasteExpandBtn').click();expect(page.locator('#dietExpandBtn')).to_be_visible();expect(page.locator('#dietText')).to_have_value(text)
 page.locator('#dietPasteExpandBtn').click();page.keyboard.press('Escape');expect(page.locator('#dietPasteExpandBtn')).to_have_attribute('aria-pressed','false');expect(page.locator('#dietDialog')).to_be_visible()
 page.locator('#dietPreview > summary').click()
 assert not page.locator('#dietPreviewBody li').evaluate_all("nodes=>nodes.some(node=>/^[;\\s]+$/.test(node.textContent))")
 # Expand the meals editor directly while collapsed, edit and undo without leaving it.
 page.locator('#dietPreview > summary').click();expect(page.locator('#dietPreviewBody')).not_to_be_visible()
 page.locator('#dietMealsExpandBtn').click();expect(page.locator('#dietMealsExpandBtn')).to_have_attribute('aria-pressed','true')
 expect(page.locator('#dietPreviewBody')).to_be_visible();expect(page.locator('#dietText')).not_to_be_visible();expect(page.locator('.diet-history')).to_be_visible()
 for width in [320,390]:
  page.set_viewport_size({'width':width,'height':844});assert page.locator('#dietDialog').evaluate('el=>el.scrollWidth<=el.clientWidth+1')
  assert page.locator('#dietPreviewBody').bounding_box()['height']>550
 page.locator('#dietPreviewBody li').filter(has_text='Total: 240 kcal').fill('Total: 280 kcal');assert '280 kcal' in page.locator('#dietText').input_value()
 page.locator('#dietUndoBtn').click();expect(page.locator('#dietPreviewBody')).to_contain_text('Total: 240 kcal')
 page.locator('#dietRedoBtn').click();expect(page.locator('#dietPreviewBody')).to_contain_text('Total: 280 kcal')
 page.screenshot(path='/tmp/treino36-diet-meals-expanded.png')
 page.locator('#dietUndoBtn').click();page.locator('#dietMealsExpandBtn').click();expect(page.locator('#dietText')).to_be_visible();expect(page.locator('#dietPreviewBody')).to_be_visible()
 page.locator('#dietMealsExpandBtn').click();page.keyboard.press('Escape');expect(page.locator('#dietMealsExpandBtn')).to_have_attribute('aria-pressed','false');expect(page.locator('#dietDialog')).to_be_visible()
 page.locator('#dietPreviewBody li').filter(has_text='Total: 240 kcal').fill('Total: 300 kcal');expect(page.locator('#dietTotals')).to_contain_text('748 kcal');assert '300 kcal' in page.locator('#dietText').input_value()
 page.locator('#dietUndoBtn').click();expect(page.locator('#dietTotals')).to_contain_text('688 kcal');page.locator('#dietRedoBtn').click();expect(page.locator('#dietTotals')).to_contain_text('748 kcal')
 page.locator('#diet-goal').fill('2000');page.locator('#dietGoalPlus').click();expect(page.locator('#diet-goal')).to_have_value('2100');page.locator('#dietUndoBtn').click();expect(page.locator('#diet-goal')).to_have_value('2000');page.locator('#dietRedoBtn').click();expect(page.locator('#diet-goal')).to_have_value('2100');page.locator('#dietGoalAuto').click();expect(page.locator('#diet-goal')).to_have_value('')
 for key,value in {'protein':'100','carbs':'200','fat':'50'}.items():page.locator('#diet-'+key).fill(value)
 expect(page.locator('#dietTotals')).to_contain_text('1.650 kcal');page.locator('#diet-calories').fill('1850');expect(page.locator('#dietTotals')).to_contain_text('1.850 kcal')
 saved=page.locator('#dietText').input_value();page.reload();page.locator('#dietBtn').click();expect(page.locator('#dietText')).to_have_value(saved);page.locator('#dietCalculations > summary').click();expect(page.locator('#diet-calories')).to_have_value('1850');expect(page.locator('#diet-protein')).to_have_value('100')
 page.locator('#dietExpandBtn').click();expect(page.locator('#dietExpandBtn')).to_have_attribute('aria-pressed','true');expect(page.locator('#dietDialog')).to_have_class('app-dialog diet-expanded')
 for width in [320,390]:
  page.set_viewport_size({'width':width,'height':844});assert page.locator('#dietDialog').evaluate('el=>el.scrollWidth<=el.clientWidth+1')
 page.screenshot(path='/tmp/treino36-diet-controls.png')
 assert page.locator('.diet-history').evaluate("el=>getComputedStyle(el).position==='sticky'")
 expect(page.locator('#dietIncludeCalculations')).not_to_be_checked()
 page.locator('#dietPdfBtn').click();page.wait_for_function('shared.length===1')
 data=page.evaluate("""async()=>{const file=shared[0].files[0];return await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(file);});}""")
 with fitz.open(stream=base64.b64decode(data),filetype='pdf') as doc:
  pdf=' '.join(p.get_text() for p in doc)
  for value in ['Meta: 2.303 kcal/dia','Proteína: 100','Carbo: 200','Gordura: 50','300 kcal']:assert value in pdf,(value,pdf)
  for value in ['TMB estimada:','Calorias do dia:']:assert value not in pdf,(value,pdf)
  assert '• ;' not in pdf
  assert 'Caio' not in pdf and 'Maced' not in pdf,pdf
 page.locator('#dietText').fill(saved+'\n\nJantar\n'+'\n'.join('Alimento de teste '+str(i) for i in range(24)))
 downloads=[];page.on('download',lambda file:downloads.append(file))
 # Record the actual canvas text: image keeps pupil/goal and omits trainer signature.
 page.evaluate("""()=>{window.photoText=[];window.photoPositions=[];const original=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(value,...args){photoText.push(value);photoPositions.push({text:value,y:args[1]});return original.call(this,value,...args);};}""")
 page.locator('#dietPhotoBtn').click();expect(page.locator('#dietPhotoPreviewDialog')).to_be_visible();expect(page.locator('#dietPhotoSaveBtn')).to_be_enabled(timeout=20000)
 page.wait_for_function("document.querySelector('#dietPhotoImages img')?.naturalWidth===1240")
 expect(page.locator('#dietPhotoImages img')).to_be_visible();assert len(downloads)==0
 drawn=page.evaluate('photoText');assert any('Dieta — Ana' in line for line in drawn),drawn;assert any('Meta: 2.303 kcal/dia' in line for line in drawn),drawn;assert not any('Caio' in line or 'Maced' in line for line in drawn),drawn;assert not any(re.fullmatch(r'\d+/\d+',line) for line in drawn),drawn;assert any('Alimento de teste 23' in line for line in drawn),drawn
 positions=page.evaluate("photoPositions.filter(p=>p.text.includes('Alimento de teste ')).map(p=>p.y)")
 assert len(positions)==24,positions
 gaps=[b-a for a,b in zip(positions,positions[1:])]
 assert max(gaps)-min(gaps)<1,(positions,gaps)
 page.locator('#dietPhotoExpandBtn').click();expect(page.locator('#dietPhotoExpandBtn')).to_have_attribute('aria-pressed','true')
 page.screenshot(path='/tmp/treino36-diet-photo-preview.png')
 page.evaluate("Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>false})")
 with page.expect_download() as downloaded:page.locator('#dietPhotoSaveBtn').click()
 file=downloaded.value;assert file.suggested_filename=='Dieta_Ana.png';file.save_as('/tmp/treino36-diet-expanded.png')
 from PIL import Image
 with Image.open(file.path()) as img:assert img.format=='PNG' and img.width==1240 and 1750<img.height<4500
 assert page.evaluate('shared.length')==1
 page.evaluate("Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true})")
 page.locator('#dietPhotoSaveBtn').click();page.wait_for_function('shared.length===2')
 assert page.evaluate("Object.keys(shared[1]).join(',')==='files'&&shared[1].files[0].type==='image/png'&&shared[1].files[0].name==='Dieta_Ana.png'")
 expect(page.locator('#dietPhotoImages img')).to_be_visible()
 page.evaluate("()=>{window.imageShareOriginal=navigator.share;Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{const error=new Error('Cancelado');error.name='AbortError';throw error;}});}")
 page.locator('#dietPhotoSaveBtn').click();expect(page.locator('#dietPhotoSaveBtn')).to_be_enabled();expect(page.locator('#dietPhotoImages img')).to_be_visible()
 page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:window.imageShareOriginal})")
 photoUrl=page.locator('#dietPhotoImages img').get_attribute('src')
 page.evaluate("()=>{window.photoRevoked=[];const previous=URL.revokeObjectURL.bind(URL);URL.revokeObjectURL=url=>{photoRevoked.push(url);previous(url);};}")
 page.locator('#dietPhotoPreviewDialog [data-close]').click();expect(page.locator('#dietPhotoImages img')).to_have_count(0);assert photoUrl in page.evaluate('photoRevoked')
 page.locator('#dietText').fill(saved)
 page.locator('#dietIncludeCalculations').check();page.locator('#dietUndoBtn').click();expect(page.locator('#dietIncludeCalculations')).not_to_be_checked();page.locator('#dietRedoBtn').click();expect(page.locator('#dietIncludeCalculations')).to_be_checked()
 page.locator('#dietPdfBtn').click();page.wait_for_function('shared.length===3')
 data=page.evaluate("""async()=>{const file=shared[2].files[0];return await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(file);});}""")
 with fitz.open(stream=base64.b64decode(data),filetype='pdf') as doc:
  pdf=' '.join(p.get_text() for p in doc)
  for value in ['TMB estimada: 1.486','Meta: 2.303','Calorias do dia: 1.850','Proteína: 100']:assert value in pdf,(value,pdf)
 page.reload();page.locator('#dietBtn').click();expect(page.locator('#dietIncludeCalculations')).to_be_checked()
 page.locator('#dietDialog [data-close]').click();page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="Bruno"] .aluno-nome').click();page.locator('#dietBtn').click();expect(page.locator('#dietText')).to_have_value('');expect(page.locator('#dietTmb')).to_have_text('—');expect(page.locator('#dietIncludeCalculations')).not_to_be_checked();expect(page.locator('#dietUndoBtn')).to_be_disabled()
 assert page.evaluate("[localStorage.getItem('treinoAlunos'),localStorage.getItem('avaliacao_fisica_alunos')]")==original
 # Source values refresh from OBS, ignoring old diet demographics and preserving manual targets.
 page.locator('#dietDialog [data-close]').click();page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="Ana"] .aluno-nome').click();page.locator('#dietBtn').click()
 if not page.locator('#dietCalculations').evaluate('el=>el.open'):page.locator('#dietCalculations > summary').click()
 page.locator('#diet-goal').fill('2000')
 page.evaluate("""()=>{const students=JSON.parse(localStorage.getItem('treinoAlunos'));students.find(s=>s.student_id==='a').infoRelevante.peso='65';localStorage.setItem('treinoAlunos',JSON.stringify(students));window.dispatchEvent(new Event('focus'));}""")
 expect(page.locator('#dietTmb')).to_have_text('1.536');expect(page.locator('#dietTotals')).to_contain_text('Meta: 2.000')
 page.locator('#dietGoalAuto').click();expect(page.locator('#dietTotals')).to_contain_text('Meta: 2.381');page.locator('[data-diet-goal="tmb"]').click();expect(page.locator('#dietTotals')).to_contain_text('Meta: 1.536')
 page.evaluate("""()=>{const students=JSON.parse(localStorage.getItem('treinoAlunos'));students.find(s=>s.student_id==='a').infoRelevante.peso='70';localStorage.setItem('treinoAlunos',JSON.stringify(students));window.dispatchEvent(new Event('focus'));}""")
 expect(page.locator('#dietTmb')).to_have_text('1.586');expect(page.locator('#dietTotals')).to_contain_text('Meta: 1.586')
 page.reload();page.locator('#dietBtn').click();expect(page.locator('#dietTmb')).to_have_text('1.586');expect(page.locator('#dietIncludeCalculations')).to_be_checked()
 assert not errors,errors
 browser.close();print('PASS: original draft retained, automatic OBS TMB, no duplicate demographics, quick targets, editable kcal/macros, meal editing and floating undo/redo, immediate persistence, expanded layout, PDF with goal/macros by default and optional TMB/calorie summary, real image preview before PNG download, separate paste expansion with cursor retained, independent pupils and unchanged datasets')
