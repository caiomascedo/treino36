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
 page.goto('http://app.test/treino36/');page.evaluate("""()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Danyelle',treino_id:'wa',treino:{A:['Agachamento 3x10']},avaliacaoId:10},{student_id:'b',nome:'Bia',treino_id:'wb',treino:{A:['Supino 3x10']},avaliacaoId:20}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Danyelle',sexo:'F',idade:'17',altura:'1.52',treinoStudentIds:['a'],avaliacaoPreferidaId:12,avaliacoes:[{id:11,data:'23/09/2025',peso:'57',pesoGordura:'21.1',ficha:{idade:'16',altura:'1.50'}},{id:12,data:'23/09/2026',peso:'58.7',gordura:'35.4',massamuscular:'35',ficha:{idade:'17',altura:'1.52'}}]},{id:20,nome:'Bia',sexo:'F',idade:'24',altura:'1.67',treinoStudentIds:['b'],avaliacoes:[{id:21,data:'01/10/2026',peso:'70'}]}]));}""");page.reload()
 def section(name):
  page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="'+name+'"]').click()
 section('composicao');expect(page.locator('#obs-av-peso')).to_be_visible()
 page.locator('.composition-extras-add').click()
 for key in ['peso','imc','gordura','visceral','massamuscular','proteina','agua','tmb','idadeMetabolica']:expect(page.locator('[data-extra-key="'+key+'"]').first).to_be_checked()
 # Default fields can be hidden with no lost values and restored on immediate reload.
 page.locator('[data-extra-key="peso"]').uncheck();page.locator('[data-extra-key="gordura"]').uncheck()
 expect(page.locator('#obs-av-peso')).not_to_be_visible();expect(page.locator('#obs-av-gordura')).not_to_be_visible()
 expect(page.locator('#obs-av-imc')).to_have_value('25.4')
 page.reload();section('composicao');expect(page.locator('#obs-av-peso')).not_to_be_visible()
 page.locator('.composition-extras-add').click();page.locator('[data-extra-key="peso"]').check();expect(page.locator('#obs-av-peso')).to_have_value('58.7');page.locator('.composition-extras-choices button').click()
 page.locator('#obsAssessmentSections [data-assessment-section="medidas"]').click();page.locator('.composition-extras-add').click()
 for key in ['peitoral','biceps','barriga','cintura','quadril','coxa']:expect(page.locator('[data-extra-key="'+key+'"]').first).to_be_checked()
 expect(page.locator('[data-extra-key="pescoco"]')).not_to_be_checked();expect(page.locator('[data-extra-key="panturrilhaMedida"]')).not_to_be_checked()
 page.locator('[data-extra-key="pescoco"]').check();page.locator('[data-extra-key="panturrilhaMedida"]').check();page.locator('[data-extra-key="peitoral"]').uncheck();page.locator('.composition-extras-choices button').click()
 expect(page.locator('#obs-av-peitoral')).not_to_be_visible();assert page.locator('#obs-av-panturrilhaMedida').get_attribute('inputmode')=='text'
 cdp=context.new_cdp_session(page);cdp.send('Emulation.setCPUThrottlingRate',{'rate':4});page.evaluate("""()=>{window.compressionCalls=0;const original=LZString.compressToUTF16;LZString.compressToUTF16=function(...args){window.compressionCalls++;return original.apply(this,args);};}""")
 page.locator('#obs-av-pescoco').fill('34,5');page.locator('#obs-av-panturrilhaMedida').press_sequentially('36 35',delay=20);expect(page.locator('#obs-av-panturrilhaMedida')).to_have_value('36 / 35')
 assert page.evaluate('window.compressionCalls')==0
 page.reload();section('medidas');expect(page.locator('#obs-av-pescoco')).to_have_value('34,5');expect(page.locator('#obs-av-panturrilhaMedida')).to_have_value('36 / 35');expect(page.locator('#obs-av-peitoral')).not_to_be_visible()
 # Hiding a populated measure omits its PDF row but retains its underlying value.
 page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click();page.locator('.composition-extras-add').click();page.locator('[data-extra-key="massamuscular"]').uncheck();page.locator('.composition-extras-choices button').click()
 with page.expect_download() as download:page.locator('#obsAssessment-pdf').click()
 text=re.sub(r'\s+',' ',' '.join(pg.get_text() for pg in fitz.open(download.value.path())))
 assert '% Gordura' not in text and 'Massa Muscular (kg)' not in text,text
 for expected in ['Pescoço','Panturrilha D / E','34,5','36 / 35','Peso (kg)']:assert expected in text,(expected,text)
 # Existing pupil preference is local to that pupil; default choices remain for the other.
 page.evaluate("localStorage.setItem('treinoAlunoSelecionado','Bia')");page.reload();section('composicao');expect(page.locator('#obs-av-gordura')).to_be_visible();expect(page.locator('#obs-av-massamuscular')).to_be_visible()
 page.locator('#obsAssessmentSections [data-assessment-section="medidas"]').click();expect(page.locator('#obs-av-peitoral')).to_be_visible();expect(page.locator('#obs-av-pescoco')).to_have_count(0)
 # Library has the same preferences in every historical assessment card and can change them.
 library=context.new_page();library.on('pageerror',lambda e:errors.append(str(e)));library.goto('http://app.test/treino36/avaliacao.html?embed=treino36&treinoStudentId=a')
 root=library.locator('[data-extra-section="composicao"][data-extra-av="12"]');root.locator('.composition-extras-add').click();expect(root.locator('[data-extra-key="gordura"]')).not_to_be_checked();root.locator('[data-extra-key="gordura"]').check();expect(root.locator('[data-extra-key="gordura"]')).to_be_checked()
 # Use DOM to check synchronization of historical cards even when collapsed.
 assert library.locator('[data-extra-section="composicao"] [data-extra-key="gordura"]').evaluate_all('(nodes)=>nodes.every(node=>node.checked)')
 library.locator('#av-item-12 .av-content > .assessment-tabs [data-section="medidas"]').click()
 expect(library.locator('#library-extra-10-12-pescoco')).to_have_value('34,5');expect(library.locator('#library-extra-10-12-panturrilhaMedida')).to_have_value('36 / 35')
 library.locator('#library-extra-10-12-panturrilhaMedida').fill('37 36');expect(library.locator('#library-extra-10-12-panturrilhaMedida')).to_have_value('37 / 36')
 library.close();page.evaluate("localStorage.setItem('treinoAlunoSelecionado','Danyelle')");page.reload();section('medidas');expect(page.locator('#obs-av-panturrilhaMedida')).to_have_value('37 / 36')
 page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click();expect(page.locator('#obs-av-gordura')).to_have_value('35.4')
 # Two immediate section preference operations must combine before any worker compaction.
 page.evaluate("""()=>{TreinoStorage.assessmentOperation(10,null,'person',{}, {composicaoCampos:['imc']});TreinoStorage.assessmentOperation(10,null,'person',{}, {medidasCampos:['coxa']});}""")
 page.reload();section('composicao');expect(page.locator('#obs-av-peso')).not_to_be_visible();expect(page.locator('#obs-av-imc')).to_be_visible();expect(page.locator('#obs-av-gordura')).not_to_be_visible()
 page.locator('#obsAssessmentSections [data-assessment-section="medidas"]').click();expect(page.locator('#obs-av-biceps')).not_to_be_visible();expect(page.locator('#obs-av-coxa')).to_be_visible();expect(page.locator('#obs-av-pescoco')).to_have_value('34,5')
 assert not errors,errors
 browser.close();print('PASS: original fields selected by default, per-pupil durable visibility and PDF filtering, neck and paired calf values, CPU4 typing without compression, no cross-pupil leakage, synchronized library/history, hidden values retained')
