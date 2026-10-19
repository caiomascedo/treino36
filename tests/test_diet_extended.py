import base64,urllib.request
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
 context.add_init_script("""window.shared=[];window.opens=0;window.open=()=>{window.opens++;return null;};Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{shared.push(data);}});Object.defineProperty(navigator,'userActivation',{configurable:true,value:{isActive:true}});""")
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
 page.locator('#dietText').fill(text);expect(page.locator('#dietTotals')).to_contain_text('688 kcal');page.locator('#dietPreview > summary').click()
 assert not page.locator('#dietPreviewBody li').evaluate_all("nodes=>nodes.some(node=>/^[;\\s]+$/.test(node.textContent))")
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
  for value in ['Proteína: 100','Carbo: 200','Gordura: 50','300 kcal']:assert value in pdf,(value,pdf)
  for value in ['TMB estimada:','Meta:','Calorias do dia:']:assert value not in pdf,(value,pdf)
  assert '• ;' not in pdf
 with page.expect_download() as downloaded:page.locator('#dietPhotoBtn').click()
 file=downloaded.value;assert file.suggested_filename=='Dieta_Ana.png';file.save_as('/tmp/treino36-diet-expanded.png')
 from PIL import Image
 with Image.open(file.path()) as img:assert img.format=='PNG' and img.width==1240 and 400<=img.height<1750
 assert page.evaluate('shared.length')==1
 page.locator('#dietIncludeCalculations').check();page.locator('#dietUndoBtn').click();expect(page.locator('#dietIncludeCalculations')).not_to_be_checked();page.locator('#dietRedoBtn').click();expect(page.locator('#dietIncludeCalculations')).to_be_checked()
 page.locator('#dietPdfBtn').click();page.wait_for_function('shared.length===2')
 data=page.evaluate("""async()=>{const file=shared[1].files[0];return await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(file);});}""")
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
 browser.close();print('PASS: original draft retained, automatic OBS TMB, no duplicate demographics, quick targets, editable kcal/macros, meal editing and floating undo/redo, immediate persistence, expanded layout, PDF with macros-only default and optional calculation summary, real PNG export, independent pupils and unchanged datasets')
