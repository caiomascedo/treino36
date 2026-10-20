import math
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404,body='')
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://app.test/treino36/');page.evaluate("""()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento']},avaliacaoId:10}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',idade:'65',altura:'1.60',treinoStudentIds:['a'],avaliacoes:[{id:11,data:'19/10/2026',peso:'60',protocolo:'dw4'}]}]));}""");page.reload()
 page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="dobras"]').click()
 expect(page.locator('.skinfold-protocol-guide')).to_contain_text('16–72')
 expect(page.locator('.skinfold-protocol-guide')).to_contain_text('idosos')
 for key,value in {'bicipital':'5','triceps':'10','subescapular':'12','suprailiaca':'13'}.items():page.locator('#obs-av-'+key).fill(value)
 actual=page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0].avaliacoes[0]._dobras")
 expected=495/(1.1339-.0645*math.log10(40))-450
 assert actual['soma']==40 and abs(actual['pctG']-expected)<1e-8,actual
 assert page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0].avaliacoes[0].agua??''")==''
 page.locator('#obsAssessmentProtocol').select_option('jp7');expect(page.locator('.skinfold-protocol-guide')).to_contain_text('fora da faixa')
 assert page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0].avaliacoes[0]._dobras") is None
 page.locator('#obsAssessmentProtocol').select_option('registro');expect(page.locator('#obs-av-panturrilha')).to_be_visible();expect(page.locator('.obs-skinfold-results')).to_contain_text('sem estimativa')
 raw=page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0].avaliacoes[0]")
 assert raw['bicipital']=='5' and raw['triceps']=='10' and raw['_dobrasRegistro']['soma']==40 and raw['_dobras'] is None
 page.reload();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="dobras"]').click()
 expect(page.locator('#obsAssessmentProtocol')).to_have_value('registro');expect(page.locator('#obs-av-bicipital')).to_have_value('5')
 engine=next(f for f in page.frames if 'treino36-engine' in f.url)
 legacy=engine.evaluate("""()=>{const person={id:1,sexo:'M',idade:'30',altura:'1.8',avaliacoes:[{id:2,peso:'80',protocolo:'yuhasz6',triceps:'10',torax:'12',subescapular:'15',suprailiaca:'14',abdominal:'13',pregaCoxa:'16'}]};TreinoAssessmentEngine.calculate(person,2);return person.avaliacoes[0]}""")
 assert legacy['protocolo']=='yuhasz6' and legacy['_dobras']['soma']==80 and legacy['torax']=='12',legacy
 checks=engine.evaluate('''()=>{const person={id:1,sexo:'M',idade:'30',altura:'1.8',avaliacoes:[{id:2,peso:'80',protocolo:'carter6',triceps:'10',torax:'12',subescapular:'15',suprailiaca:'14',abdominal:'13',pregaCoxa:'16',panturrilha:'9'}]};TreinoAssessmentEngine.calculate(person,2);const initial={...person.avaliacoes[0]._dobras};person.avaliacoes[0].torax='90';TreinoAssessmentEngine.calculate(person,2);const changed={...person.avaliacoes[0]._dobras};person.avaliacoes[0].panturrilha='';TreinoAssessmentEngine.calculate(person,2);return {initial,changed,missing:person.avaliacoes[0]._dobras};}''')
 assert checks['initial']==checks['changed'] and checks['initial']['soma']==77 and checks['missing'] is None,checks
 library=context.new_page();library.goto('http://app.test/treino36/avaliacao.html?embed=treino36&treinoStudentId=a')
 expect(library.locator('select[onchange^="trocarProtocoloDobras"]')).to_have_value('registro');expect(library.locator('.skinfold-protocol-guide')).to_contain_text('adipômetro')
 assert not errors,errors
 browser.close();print('PASS: DW elderly reference and actual result, out-of-range rejection, manual registration with no invented fat/water, saved sites and protocol, legacy six-site values retained, both interfaces show guidance')
