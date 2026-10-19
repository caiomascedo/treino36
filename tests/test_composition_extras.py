from pathlib import Path
from urllib.parse import urlparse
import re,urllib.request,fitz
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
LIBS=['https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js','https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js']
scripts={url:urllib.request.urlopen(url,timeout=30).read() for url in LIBS}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  if r.request.url in scripts:r.fulfill(body=scripts[r.request.url],content_type='application/javascript');return
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404,body='')
 context.route('**/*',route);context.add_init_script('window.open=()=>null');page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://app.test/treino36/');page.evaluate("""()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino_id:'wa',treino:{A:['Agachamento 3x10']},avaliacaoId:10},{student_id:'b',nome:'Bia',treino_id:'wb',treino:{A:['Supino 3x10']},avaliacaoId:20}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',idade:'30',altura:'1.64',treinoStudentIds:['a'],composicaoExtras:['pesoGordura','massaMuscularPct','musculoEsqueleticoKg','alturaCm','idadeReal'],avaliacaoPreferidaId:12,avaliacoes:[{id:11,data:'01/09/2026',peso:'60'},{id:12,data:'01/10/2026',peso:'56.9',gordura:'34.6',pesoGordura:'19.7',massamuscular:'30',massaMuscularPct:'52.7',musculoEsqueleticoKg:'19.7',ficha:{idade:'30',altura:'1.64'}}]},{id:20,nome:'Bia',sexo:'F',idade:'24',altura:'1.67',treinoStudentIds:['b'],avaliacoes:[{id:21,data:'01/10/2026',peso:'70'}]}]));}""");page.reload()
 def composition():
  page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click()
 def options():
  if not page.locator('.composition-extras-choices').is_visible():page.locator('.composition-extras-add').click()
 def choose(key,enabled=True):
  options();check=page.locator('[data-extra-key="'+key+'"]')
  check.check() if enabled else check.uncheck()
 def done():page.locator('.composition-extras-choices > button').click()
 composition();expect(page.locator('.composition-source')).to_have_count(0)
 expect(page.locator('#obs-av-gordura')).to_have_value('34.6');expect(page.locator('#obs-av-pesoGordura')).to_have_value('19.7')
 # Related values can be selected together, independently, with their original readings.
 choose('gordura',False);done();expect(page.locator('#obs-av-gordura')).not_to_be_visible();expect(page.locator('#obs-av-pesoGordura')).to_have_value('19.7')
 choose('gordura');choose('pesoGordura',False);done();expect(page.locator('#obs-av-gordura')).to_have_value('34.6');expect(page.locator('#obs-av-pesoGordura')).to_have_count(0)
 for key in ['pesoGordura','aguaLitros','pesoAgua','proteinaKg','metabolismoInformado','musculoEsqueleticoPct']:choose(key)
 for key in ['alturaCm','idadeReal']:expect(page.locator('[data-extra-key="'+key+'"]')).to_have_count(0)
 expect(page.locator('[data-unit-group]')).to_have_count(0)
 for key in ['peso','imc','gordura','visceral','massamuscular','proteina','agua','tmb','idadeMetabolica']:expect(page.locator('[data-extra-key="'+key+'"]')).to_be_checked()
 options()
 basic=page.locator('.composition-inbody-options').filter(has=page.locator('summary',has_text='InBody · dados do laudo'));basic.locator('summary').click()
 values={'mineraisKg':'2,84','pontuacaoInbody':'67','pesoIdealInbody':'56,5','controlePesoInbody':'-0,4','controleGorduraInbody':'-6,7','controleMuscularInbody':'+6,3','rcqInformado':'0,86','grauObesidadeInbody':'101','idLaudoInbody':'EX-120','horaLaudoInbody':'11:21'}
 for key in values:page.locator('[data-extra-key="'+key+'"]').check()
 for title,keys in [('InBody · massa magra segmentar',['magra_bracoDireito','adequacaoMagra_bracoDireito']),('InBody · gordura segmentar',['gordura_tronco','adequacaoGordura_tronco']),('InBody · impedância',['impedancia20_bd','impedancia100_bd'])]:
  group=page.locator('.composition-inbody-options').filter(has=page.locator('summary',has_text=title));group.locator('summary').click()
  for key in keys:page.locator('[data-extra-key="'+key+'"]').check()
 done();values.update({'agua':'47,8','pesoAgua':'27,2','proteina':'12,65','musculoEsqueleticoPct':'34,6','aguaLitros':'27,2','proteinaKg':'7,2','metabolismoInformado':'1174','magra_bracoDireito':'1,61','adequacaoMagra_bracoDireito':'91','gordura_tronco':'10','adequacaoGordura_tronco':'187,7','impedancia20_bd':'474,1','impedancia100_bd':'439,5'})
 cdp=context.new_cdp_session(page);cdp.send('Emulation.setCPUThrottlingRate',{'rate':4});page.evaluate("""()=>{window.compressionCalls=0;const old=LZString.compressToUTF16;LZString.compressToUTF16=function(...args){compressionCalls++;return old.apply(this,args);};}""")
 for key,value in values.items():page.locator('#obs-av-'+key).fill(value)
 minerals=page.locator('#obs-av-mineraisKg').locator('..');minerals.locator('.composition-extra-rating').click()
 minerals.locator('[aria-label^="Mínimo do laudo"]').fill('2,66');minerals.locator('[aria-label^="Máximo do laudo"]').fill('3,25')
 expect(minerals.locator('.composition-extra-rating')).to_have_text('Normal')
 assert page.evaluate('compressionCalls')==0
 assert page.locator('#obs-av-controleGorduraInbody').get_attribute('inputmode')=='text'
 expect(page.locator('#obs-av-controleGorduraInbody').locator('..').locator('.composition-extra-rating')).to_have_text('Meta do laudo')
 page.reload();composition()
 for key,value in values.items():expect(page.locator('#obs-av-'+key)).to_have_value(value)
 raw=page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0]");av=raw['avaliacoes'][1]
 assert av['gordura']=='34.6' and av['pesoGordura']=='19.7' and av['massaMuscularPct']=='52.7'
 assert 'pesoGordura' in raw['composicaoExtras'] and 'gordura' in raw['composicaoCampos']
 for group,keys in [('gordura',['gordura','pesoGordura']),('agua',['agua','pesoAgua','aguaLitros']),('massamuscular',['massamuscular','massaMuscularPct']),('musculoEsqueletico',['musculoEsqueleticoKg','musculoEsqueleticoPct'])]:
  container=page.locator('.composition-related-fields[data-metric-group="'+group+'"]')
  ids=container.locator('input[id^="obs-av-"]').evaluate_all('(nodes)=>nodes.map(n=>n.id)')
  assert ids==['obs-av-'+key for key in keys],(group,ids)
  boxes=[page.locator('#obs-av-'+key).bounding_box() for key in keys]
  assert all(boxes[i+1]['y']>boxes[i]['y']+boxes[i]['height'] for i in range(len(boxes)-1)),boxes
 with page.expect_download() as download:page.locator('#obsAssessment-pdf').click()
 text=re.sub(r'\s+',' ',' '.join(pg.get_text() for pg in fitz.open(download.value.path())))
 for expected in ['InBody','Minerais','Pontuação','2,84','-6,7','27,2','7,2','474,1','439,5','187,7']:assert expected in text,(expected,text)
 for label in ['% Gordura','Peso da gordura (kg)','Massa muscular (%)','Massa muscular esquelética (kg)','Massa muscular esquelética (%)','% Proteína','% Água','Peso da água (kg)','TMB (kcal)','Metabolismo da bioimpedância']:assert label in text,(label,text)
 assert text.index('% Gordura')<text.index('Peso da gordura (kg)')<text.index('Massa Muscular (kg)'),text
 assert text.index('Massa Muscular (kg)')<text.index('Massa muscular (%)')<text.index('% Proteína'),text
 assert text.index('% Água')<text.index('Peso da água (kg)')<text.index('Água corporal total'),text
 assert page.locator('#searchName').input_value()=='Ana'
 library=context.new_page();library.on('pageerror',lambda e:errors.append(str(e)));library.goto('http://app.test/treino36/avaliacao.html?embed=treino36&treinoStudentId=a')
 expect(library.locator('#library-extra-10-12-mineraisKg')).to_have_value('2,84');library.locator('#library-extra-10-12-mineraisKg').fill('2,85');library.close()
 page.reload();composition();expect(page.locator('#obs-av-mineraisKg')).to_have_value('2,85');expect(page.locator('#obs-av-mineraisKg').locator('..').locator('.composition-extra-rating')).to_have_text('Normal')
 page.evaluate("localStorage.setItem('treinoAlunoSelecionado','Bia')");page.reload();composition();expect(page.locator('#obs-av-gordura')).to_be_visible();expect(page.locator('#obs-av-mineraisKg')).to_have_count(0)
 assert not errors,errors
 browser.close();print('PASS: no source field; independent related units stacked in UI and PDF, old values preserved, InBody general/segment/impedance fields, signed controls, actual PDF, immediate persistence, native/library sync and per-pupil selections; CPU4 typing without compression')
