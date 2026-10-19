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
 page.evaluate("""()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento 3x10']},avaliacaoId:10},{student_id:'b',nome:'Bruno',treino:{A:['Supino 3x10']}}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',avaliacoes:[{id:11,peso:'65'}]}]));}""");page.reload()
 # All six tool buttons remain in view, including when validity has a visible summary.
 ids=['createWorkoutBtn','historyWorkoutBtn','compareWorkoutBtn','workoutValidityBtn','assessmentsLibraryBtn','dietBtn']
 for width in [320,390,768]:
  page.set_viewport_size({'width':width,'height':844});page.evaluate("const s=document.getElementById('workoutValiditySummary');s.hidden=false;s.textContent='Treino válido até 30/12/2026';")
  boxes=[page.locator('#'+id).bounding_box() for id in ids]
  assert all(b and b['x']>=0 and b['x']+b['width']<=width for b in boxes),boxes
  assert page.locator('.workout-tools').evaluate('el=>el.scrollWidth<=el.clientWidth+1')
  assert len(set(round(b['y']) for b in boxes))==(2 if width<521 else 1),boxes
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/tmp/treino36-tools-diet.png',full_page=False)
 original=page.evaluate("[localStorage.getItem('treinoAlunos'),localStorage.getItem('avaliacao_fisica_alunos')]")
 page.locator('#dietBtn').click();expect(page.locator('#dietStudentName')).to_have_text('Ana');expect(page.locator('#dietPdfBtn')).to_be_disabled()
 text='''**1. Café da manhã — 07:00**
- 2 ovos
- 1.5 bananas
- Café sem açúcar

Almoço: 150 g de arroz, feijão e frango
- 30 g de proteína
- Total: 500 kcal

16:00 - Lanche da tarde
- Iogurte natural

Jantar: 19:30
- Sopa

Observações:
- Água: 2 litros
- <img src=x onerror=alert(1)>
'''
 page.locator('#dietText').fill(text);page.locator('#dietPreview > summary').click();expect(page.locator('#dietPreviewBody')).to_contain_text('1.5 bananas');expect(page.locator('#dietPreviewBody')).to_contain_text('30 g de proteína');expect(page.locator('#dietPreviewBody')).to_contain_text('500 kcal');expect(page.locator('#dietPreviewBody')).to_contain_text('16:00 - Lanche da tarde');assert page.locator('#dietPreviewBody img').count()==0
 page.locator('#dietPdfBtn').click();page.wait_for_function('shared.length===1');assert page.evaluate("Object.keys(shared[0]).join(',')==='files'&&shared[0].files[0].name==='Dieta_Ana.pdf'")
 data=page.evaluate("""async()=>{const file=shared[0].files[0];return await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(file);});}""")
 with fitz.open(stream=base64.b64decode(data),filetype='pdf') as doc:
  pdf=' '.join(p.get_text() for p in doc)
  for value in ['Dieta — Ana','2 ovos','1.5 bananas','150 g de arroz','30 g de proteína','500 kcal','16:00','19:30','Água: 2 litros']:assert value in pdf,(value,pdf)
 assert page.evaluate('opens')==0;expect(page.locator('#searchName')).to_have_value('Ana')
 page.locator('#dietDialog [data-close]').click();page.reload();page.locator('#dietBtn').click();expect(page.locator('#dietText')).to_have_value(text);page.locator('#dietDialog [data-close]').click()
 page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="Bruno"] .aluno-nome').click();page.locator('#dietBtn').click();expect(page.locator('#dietText')).to_have_value('');page.locator('#dietText').fill('Jantar\nSopa de legumes');page.locator('#dietDialog [data-close]').click()
 page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="Ana"] .aluno-nome').click();page.locator('#dietBtn').click();expect(page.locator('#dietText')).to_have_value(text)
 assert page.evaluate("[localStorage.getItem('treinoAlunos'),localStorage.getItem('avaliacao_fisica_alunos')]")==original
 # A long pasted plan paginates without omitting the final item or changing student data.
 long='Almoço\n'+'\n'.join(f'{i} g de alimento de teste' for i in range(1,181))
 cdp=context.new_cdp_session(page);cdp.send('Emulation.setCPUThrottlingRate',{'rate':4});page.evaluate("()=>{window.compressCalls=0;window.compressStacks=[];const oldCompress=LZString.compressToUTF16;LZString.compressToUTF16=function(...args){compressCalls++;compressStacks.push(new Error().stack);return oldCompress.apply(this,args);};}")
 page.locator('#dietText').fill(long);assert page.evaluate('compressCalls')==0,page.evaluate('compressStacks')
 page.locator('#dietPdfBtn').click();page.wait_for_function('shared.length===1')
 data=page.evaluate("""async()=>{const file=shared[0].files[0];return await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(file);});}""")
 with fitz.open(stream=base64.b64decode(data),filetype='pdf') as doc:
  assert doc.page_count>1
  assert '180 g de alimento de teste' in ' '.join(p.get_text() for p in doc)
 assert not errors,errors
 browser.close();print('PASS: six compact tools without side scrolling at 320/390/768px; meal parsing preserves quantities/protein/kcal/times; real named diet PDF and pagination; existing file-only share; independent persistent drafts; zero dataset writes and no typing compression at CPU4')
