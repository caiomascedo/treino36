"""Six requested sites, sourced arithmetic and the actual exported assessment PDF."""
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import fitz
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
LIBS=['https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js','https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js']
scripts={url:urllib.request.urlopen(url,timeout=30).read() for url in LIBS}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844});context.add_init_script('window.open=()=>null')
 def route(r):
  if r.request.url in scripts:r.fulfill(body=scripts[r.request.url],content_type='application/javascript');return
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.jpg':'image/jpeg'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://app.test/treino36/')
 page.evaluate('''()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento']},avaliacaoId:10}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',idade:'30',altura:'1.65',treinoStudentIds:['a'],avaliacoes:[{id:11,data:'20/10/2026',peso:'70',protocolo:'carter6',panturrilha:'99'}]}]));}''');page.reload()
 page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="dobras"]').click();page.locator('#obsAssessmentProtocol').select_option('yuhasz6')
 grid=page.locator('.obs-assessment-fields');expect(grid.locator('.skinfold-help-toggle')).to_have_count(6);expect(page.locator('#obs-av-panturrilha')).to_have_count(0)
 boxes=grid.locator('.skinfold-field-heading').evaluate_all('(nodes)=>nodes.map(n=>({x:n.getBoundingClientRect().x,y:n.getBoundingClientRect().y}))')
 assert boxes[0]['y']==boxes[1]['y'] and boxes[0]['x']<boxes[1]['x'],boxes
 assert grid.locator('[data-av-field]').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.avField)')==['triceps','subescapular','suprailiaca','torax','abdominal','pregaCoxa']
 for key in ['triceps','subescapular','suprailiaca','torax','abdominal','pregaCoxa']:page.locator('#obs-av-'+key).fill('10,0')
 def av():return page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0].avaliacoes[0]")
 result=av();assert result['panturrilha']=='99' and result['_dobras']['soma']==60
 assert abs(result['_dobras']['pctG']-13.14)<1e-10 and abs(result['_dobras']['mG']-9.198)<1e-10 and abs(result['_dobras']['mM']-60.802)<1e-10
 expect(page.locator('.obs-skinfold-results')).to_contain_text('13.14%')
 for key in ['triceps','subescapular','suprailiaca','torax','abdominal','pregaCoxa']:
  page.locator('#obs-av-'+key).fill('');assert av()['_dobras'] is None
  page.locator('#obs-av-'+key).fill('10,0')
 page.locator('#obs-av-torax').fill('10abc');assert av()['_dobras'] is None;page.locator('#obs-av-torax').fill('10')
 page.screenshot(path='/tmp/yuhasz-six-sites-mobile.png')
 with page.expect_download() as download:page.locator('#obsAssessment-pdf').click()
 with fitz.open(download.value.path()) as pdf:
  text='\n'.join(p.get_text() for p in pdf)
  assert 'Panturrilha' not in text,text
  for expected in ['Yuhasz 6','60.00 mm','13.14%','9.20','60.80']:assert expected in text,(expected,text)
 page.reload();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="dobras"]').click();expect(page.locator('#obsAssessmentProtocol')).to_have_value('yuhasz6');expect(page.locator('#obs-av-torax')).to_have_value('10');assert av()['panturrilha']=='99'
 assert not errors,errors
 browser.close();print('PASS: exactly six MFIT-reference fields, comma input, every site required, strict invalid-input rejection, sourced female arithmetic and masses, actual PDF values, saved protocol and preserved calf history')
