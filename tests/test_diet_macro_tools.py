from pathlib import Path
from urllib.parse import urlparse
import urllib.request
import fitz
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
PDF_URL='https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'
PDF_SCRIPT=urllib.request.urlopen(PDF_URL,timeout=30).read()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844})
 context.add_init_script("window.open=()=>null;window.copied=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copied.push(text);}}});")
 def route(r):
  if r.request.url==PDF_URL:r.fulfill(body=PDF_SCRIPT,content_type='application/javascript');return
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://app.test/treino36/')
 page.evaluate('''()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',infoRelevante:{peso:'56',altura:'1.65',idade:'30'},treino:{A:['Agachamento 3x10']}},{student_id:'b',nome:'Bia',treino:{A:['Supino 3x10']}}]));localStorage.setItem('avaliacao_fisica_alunos','[]');}''');page.reload()
 original=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')")
 def opened():
  assert page.locator('#dietBtn').count(),errors
  page.locator('#dietBtn').click()
  if page.locator('#dietCalculations').get_attribute('open') is None:page.locator('#dietCalculations > summary').click()
 def expect_macros(p,c,f,k):
  for key,value in [('protein',p),('carbs',c),('fat',f),('calories',k)]:expect(page.locator('#diet-'+key)).to_have_value(str(value))
 opened();page.locator('#dietText').fill('Almoço\nArroz e frango')
 page.locator('[data-diet-goal="deficit"]').click();expect_macros(112,112,44.8,1299)
 assert page.locator('#dietMacroTools, #dietCalculateMacros, #dietMacroAuto').count()==0
 page.locator('[data-diet-goal="daily"]').click();page.locator('#diet-goal').fill('2000');expect_macros(112,287.2,44.8,2000)
 expect(page.locator('#dietMacroNotice')).to_contain_text('Carbo completa a meta')
 page.locator('#diet-goal').fill('800');expect_macros(112,287.2,44.8,2000);expect(page.locator('#dietMacroNotice')).to_contain_text('menor que')
 page.locator('[data-diet-goal="surplus"]').click();expect_macros(112,224,44.8,1747)
 page.locator('[data-diet-goal="deficit"]').click();expect_macros(112,112,44.8,1299)
 # Live OBS updates recalculate and persist automatically, with no guessed weight.
 page.evaluate('''()=>{const records=AvaliacaoTreinoSync.read('treinoAlunos');records[0].infoRelevante.peso='58';for(const guide of records[0].infoGuias||[])guide.peso='58';localStorage.setItem('treinoAlunos',JSON.stringify(records));window.dispatchEvent(new StorageEvent('storage',{key:'treinoAlunos'}));}''');expect_macros(116,116,46.4,1346)
 assert page.evaluate("JSON.parse(localStorage.getItem('dieta36_calculos_v1:a')).protein")=='116'
 page.evaluate('''records=>{localStorage.setItem('treinoAlunos',JSON.stringify(records));window.dispatchEvent(new StorageEvent('storage',{key:'treinoAlunos'}));}''',original);expect_macros(112,112,44.8,1299)
 page.locator('#dietCopyValues').click();assert page.evaluate('copied.at(-1)')=='Calorias do dia: 1299 kcal\nProteína: 112 g\nCarboidratos: 112 g\nGorduras: 44,8 g'
 page.get_by_role('button',name='Copiar Proteína',exact=True).click();assert page.evaluate('copied.at(-1)')=='112'
 # Real clipboard fallback is exercised when the modern API refuses a write.
 page.evaluate('''()=>{navigator.clipboard.writeText=async()=>{throw Error('denied')};window.fallback=[];document.addEventListener('copy',()=>fallback.push(document.activeElement.value));}''')
 page.get_by_role('button',name='Copiar Gorduras',exact=True).click();assert page.evaluate('fallback.at(-1)')=='44,8'
 page.evaluate('''()=>{navigator.clipboard.writeText=async text=>{copied.push(text);};}''')
 page.locator('#dietIncludeCalculations').check()
 with page.expect_download() as pdf_download:page.locator('#dietPdfBtn').click()
 with fitz.open(pdf_download.value.path()) as pdf:
  contents='\n'.join(p.get_text() for p in pdf)
  for expected in ['1.299 kcal','Proteína: 112 g','Carbo: 112 g','Gordura: 44,8 g','macros pelo peso']:assert expected in contents,(expected,contents)
 page.get_by_role('button',name='Limpar Proteína',exact=True).click();expect(page.locator('#diet-protein')).to_have_value('');page.locator('#dietUndoBtn').click();expect_macros(112,112,44.8,1299)
 page.locator('#dietClearValues').click()
 for key in ['calories','protein','carbs','fat']:expect(page.locator('#diet-'+key)).to_have_value('')
 expect(page.locator('#dietText')).to_have_value('Almoço\nArroz e frango');page.locator('#dietUndoBtn').click();expect_macros(112,112,44.8,1299)
 # Manual correction is retained until an explicit objective click.
 page.locator('#diet-protein').fill('120');page.locator('#diet-goal').fill('2100');expect(page.locator('#diet-protein')).to_have_value('120')
 page.locator('[data-diet-goal="surplus"]').click();expect_macros(112,224,44.8,1747)
 # The calculator has its own keypad, cannot summon an editable text keyboard, and never changes macros.
 page.locator('#dietMiniCalculator > summary').click()
 assert page.locator('#dietCalcExpression').evaluate('(el)=>el.readOnly && el.inputMode==="none"')
 assert page.locator('#dietCalcTarget, #dietCalcApply').count()==0
 expect(page.locator('.diet-mini-keys #dietCalcEvaluate')).to_have_text('=')
 def keys(text):
  for key in text:page.locator('[data-diet-calc-key="'+key+'"]').click()
 keys('56×0,8');page.locator('#dietCalcEvaluate').click();expect(page.locator('#dietCalcResult')).to_have_text('= 44,8');page.locator('#dietCalcCopy').click();assert page.evaluate('copied.at(-1)')=='44,8'
 assert page.evaluate('document.activeElement.id')!='dietCalcExpression'
 expect_macros(112,224,44.8,1747)
 page.locator('#dietCalcClear').click();expect(page.locator('#dietCalcExpression')).to_have_value('');expect(page.locator('#dietCalcCopy')).to_be_disabled()
 keys('56×3⌫2');page.locator('#dietCalcEvaluate').click();expect(page.locator('#dietCalcResult')).to_have_text('= 112')
 page.locator('#dietCalcClear').click();keys('1÷0');page.locator('#dietCalcEvaluate').click();expect(page.locator('#dietCalcResult')).to_contain_text('zero');expect(page.locator('#dietCalcCopy')).to_be_disabled()
 page.reload();opened();expect_macros(112,224,44.8,1747)
 page.screenshot(path='/tmp/diet-macro-tools-mobile.png')
 page.locator('#dietDialog [data-close]').click();page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="Bia"] .aluno-nome').click();opened();expect(page.locator('#diet-protein')).to_have_value('');page.locator('[data-diet-goal="deficit"]').click();expect(page.locator('#dietMacroNotice')).to_contain_text('peso válido');expect(page.locator('#diet-protein')).to_have_value('')
 assert page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')")==original
 assert not errors,errors
 browser.close();print('PASS: one-click macros, maintenance remainder/errors, live OBS weight, clipboard/fallback, PDF, clear/undo, manual correction, keypad-only calculator/errors, persistence and pupil isolation; OBS/workouts unchanged')
