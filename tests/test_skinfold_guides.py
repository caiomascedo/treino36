from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844});requests=[];errors=[]
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if '/assets/skinfolds/' in u.path:requests.append(u.path)
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.jpg':'image/jpeg'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404,body='')
 context.route('**/*',route);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://app.test/treino36/');page.evaluate("""()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento']},avaliacaoId:10}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'M',idade:'30',altura:'1.70',treinoStudentIds:['a'],avaliacoes:[{id:11,data:'19/10/2026',protocolo:'yuhasz6',peso:'70',triceps:'10',torax:'11',subescapular:'12',suprailiaca:'13',abdominal:'14',pregaCoxa:'15'}]}]));}""");page.reload()
 page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="dobras"]').click()
 assert not requests,requests
 for protocol,count in [('yuhasz6',6),('jp7',7),('pollock3',3),('dw4',4),('carter6',6),('registro',9)]:
  page.locator('#obsAssessmentProtocol').select_option(protocol)
  grid=page.locator('.obs-assessment-fields');expect(grid.locator('.skinfold-help-toggle')).to_have_count(count)
  expect(grid.locator('.skinfold-help-panel:visible')).to_have_count(0)
  boxes=grid.locator('.skinfold-field-heading').evaluate_all('(nodes)=>nodes.map(n=>({x:n.getBoundingClientRect().x,y:n.getBoundingClientRect().y}))')
  assert boxes[0]['y']==boxes[1]['y'] and boxes[0]['x']<boxes[1]['x'],(protocol,boxes)
  for i in range(count):
   button=grid.locator('.skinfold-help-toggle').nth(i);button.click()
   panel=grid.locator('.skinfold-help-panel:visible');expect(panel).to_have_count(1)
   expect(panel).to_contain_text('Localização');expect(panel).to_contain_text('Sentido da dobra');expect(panel).to_contain_text('Dica')
   image=panel.locator('img');image.evaluate('(img)=>img.decode()')
   assert image.evaluate('(img)=>img.naturalWidth')>=600
   assert image.bounding_box()['width']>240
   assert panel.locator('a').get_attribute('href')=='https://www.sanny.com.br/dobras-cutaneas'
   if i==count-1:
    panel.locator('.skinfold-guide-zoom').click();viewer=page.locator('.skinfold-image-viewer');expect(viewer).to_be_visible();viewer.locator('img').evaluate('(img)=>img.decode()');viewer.get_by_role('button',name='Fechar',exact=True).click();expect(viewer).not_to_be_visible()
   button.click();expect(panel).not_to_be_visible()
 assert page.evaluate("SkinfoldGuides.guide('suprailiaca','dw4','F').location.includes('média')")
 assert page.evaluate("SkinfoldGuides.guide('suprailiaca','jp7','F').location.includes('anterior')")
 page.locator('#obs-av-bicipital').fill('8,5')
 page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click();page.locator('#obsAssessmentSex').select_option('F');page.locator('#obsAssessmentSections [data-assessment-section="dobras"]').click()
 page.get_by_role('button',name='Ver orientação: Tórax · peitoral',exact=True).click()
 assert page.locator('.skinfold-help-panel:visible img').get_attribute('src').endswith('torax-feminino.jpg')
 page.locator('.skinfold-help-panel:visible img').evaluate('(img)=>img.decode()')
 records=page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')")
 assert len(records)==1 and len(records[0]['avaliacoes'])==1
 assert records[0]['avaliacoes'][0]['triceps']=='10' and records[0]['avaliacoes'][0]['bicipital']=='8,5'
 assert len(set(requests))==10,set(requests)
 page.reload();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="dobras"]').click();expect(page.locator('#obs-av-bicipital')).to_have_value('8,5');expect(page.locator('.skinfold-help-panel:visible')).to_have_count(0)
 library=context.new_page();library.on('pageerror',lambda e:errors.append(str(e)));library.goto('http://app.test/treino36/avaliacao.html?embed=treino36&treinoStudentId=a&secao=dobras')
 for protocol,count in [('jp7',7),('pollock3',3),('dw4',4),('carter6',6),('registro',9)]:
  library.locator('select[onchange^="trocarProtocoloDobras"]').select_option(protocol)
  grid=library.locator('[data-skinfold-av="11"]');expect(grid.locator('.skinfold-help-toggle')).to_have_count(count)
  grid.locator('.skinfold-help-toggle').last.click();panel=grid.locator('.skinfold-help-panel:visible');expect(panel).to_have_count(1);panel.locator('img').evaluate('(img)=>img.decode()')
  grid.locator('.skinfold-help-toggle').last.click();expect(grid.locator('.skinfold-help-panel:visible')).to_have_count(0)
 assert not errors,errors
 browser.close();print('PASS: all nine sites/ten original Sanny photos; native and library protocols 3/4/6/7/registration/legacy; lazy images, 2-column layout, individual guidance, full-size dialog, sex variants and unchanged saved measurements')
