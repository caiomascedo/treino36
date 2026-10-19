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
 def composition():
  page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click();expect(page.locator('#obs-av-peso')).to_be_visible()
 composition();expect(page.locator('.composition-extra-field')).to_have_count(0);expect(page.locator('#obs-av-imc')).to_have_value('25.4');original_tmb=page.locator('#obs-av-tmb').input_value()
 page.locator('#obsNativeAssessment .composition-extras-add').click()
 keys=['pesoGordura','musculoEsqueleticoPct','musculoEsqueleticoKg','massaMuscularPct','pesoAgua','metabolismoInformado','alturaCm','idadeReal']
 for key in keys:page.locator('[data-extra-key="'+key+'"]').check()
 expect(page.locator('.composition-extra-field')).to_have_count(8);expect(page.locator('#obs-av-alturaCm')).to_have_value('152');expect(page.locator('#obs-av-idadeReal')).to_have_value('17')
 page.locator('.composition-extras-choices button').click()
 cdp=context.new_cdp_session(page);cdp.send('Emulation.setCPUThrottlingRate',{'rate':4});page.evaluate("""()=>{window.compressionCalls=0;const original=LZString.compressToUTF16;LZString.compressToUTF16=function(...args){window.compressionCalls++;return original.apply(this,args);};}""")
 values={'pesoGordura':'20,8','musculoEsqueleticoPct':'34,1','musculoEsqueleticoKg':'20,0','massaMuscularPct':'59,8','metabolismoInformado':'1197,8'}
 for key,value in values.items():page.locator('#obs-av-'+key).fill(value)
 detail=page.locator('#obs-av-musculoEsqueleticoPct').locator('..').locator('.composition-extra-detail')
 detail.locator('summary').click();expect(detail.locator('.composition-extra-value')).to_contain_text('34,1');expect(detail).to_contain_text('músculos esqueléticos')
 page.locator('#obs-av-musculoEsqueleticoPct').fill('34,2');expect(detail.locator('.composition-extra-value')).to_contain_text('34,2');assert detail.evaluate('el=>el.open')
 page.locator('#obs-av-musculoEsqueleticoPct').fill('34,1');detail.locator('summary').click();assert not detail.evaluate('el=>el.open')
 page.locator('#obs-av-pesoAgua').locator('..').locator('summary').click();expect(page.locator('#obs-av-pesoAgua').locator('..')).to_contain_text('Não informado')
 assert page.evaluate('window.compressionCalls')==0;expect(page.locator('#obs-av-tmb')).to_have_value(original_tmb)
 # Choices and values survive immediate reload, independently of clicking Save.
 page.reload();composition()
 for key,value in values.items():expect(page.locator('#obs-av-'+key)).to_have_value(value)
 page.locator('.composition-extras-add').click();page.locator('[data-extra-key="musculoEsqueleticoPct"]').uncheck();expect(page.locator('#obs-av-musculoEsqueleticoPct')).to_have_count(0);page.locator('[data-extra-key="musculoEsqueleticoPct"]').check();expect(page.locator('#obs-av-musculoEsqueleticoPct')).to_have_value('34,1');page.locator('.composition-extras-choices button').click()
 with page.expect_download() as download:page.locator('#obsAssessment-pdf').click()
 text=re.sub(r'\s+',' ',' '.join(pg.get_text() for pg in fitz.open(download.value.path())))
 for expected in ['Peso da gordura (kg)','Massa muscular esquelética (%)','Massa muscular esquelética (kg)','Massa muscular (%)','Metabolismo da bioimpedância (kcal/dia)','Altura (cm)','Idade real (anos)','20,8','34,1','20,0','59,8','1197,8','150','152']:
  assert expected in text,(expected,text)
 assert 'Peso da água (kg)' not in text,text
 assert page.locator('#searchName').input_value()=='Danyelle'
 # Per-pupil selection does not leak into another pupil.
 page.evaluate("localStorage.setItem('treinoAlunoSelecionado','Bia')");page.reload();composition();expect(page.locator('.composition-extra-field')).to_have_count(0)
 page.locator('.composition-extras-add').click();page.locator('[data-extra-key="pesoAgua"]').check();page.locator('.composition-extras-choices button').click();page.locator('#obs-av-pesoAgua').fill('30')
 page.evaluate("localStorage.setItem('treinoAlunoSelecionado','Danyelle')");page.reload();composition();expect(page.locator('.composition-extra-field')).to_have_count(8)
 # The library uses the same fields and settings, including all history cards.
 library=context.new_page();library.on('pageerror',lambda e:errors.append(str(e)));library.goto('http://app.test/treino36/avaliacao.html?embed=treino36&treinoStudentId=a')
 libraryDetail=library.locator('#library-extra-10-12-musculoEsqueleticoPct').locator('..').locator('.composition-extra-detail')
 libraryDetail.locator('summary').click();expect(libraryDetail).to_contain_text('34,1');expect(libraryDetail).to_contain_text('músculos esqueléticos')
 expect(library.locator('#library-extra-10-12-pesoGordura')).to_have_value('20,8');library.locator('#library-extra-10-12-musculoEsqueleticoKg').fill('20,5')
 assert library.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0].avaliacoes.find(a=>a.id===12).musculoEsqueleticoKg")=='20,5'
 library.close();page.reload();composition();expect(page.locator('#obs-av-musculoEsqueleticoKg')).to_have_value('20,5')
 # Deselecting a filled metric omits it from PDF without erasing the value.
 page.locator('.composition-extras-add').click();page.locator('[data-extra-key="musculoEsqueleticoPct"]').uncheck();page.locator('.composition-extras-choices button').click()
 with page.expect_download() as download:page.locator('#obsAssessment-pdf').click()
 text=re.sub(r'\s+',' ',' '.join(pg.get_text() for pg in fitz.open(download.value.path())));assert 'Massa muscular esquelética (%)' not in text and '20,5' in text,text
 page.locator('.composition-extras-add').click();page.locator('[data-extra-key="musculoEsqueleticoPct"]').check();page.locator('.composition-extras-choices button').click()
 # Settings are person-level and survive removal of every dated assessment.
 page.on('dialog',lambda d:d.accept());page.locator('#obsDeleteAssessment').click();page.locator('#obsDeleteAssessment').click();assert sorted(page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0].composicaoExtras"))==sorted(keys)
 page.locator('#obsNewAssessment').click();expect(page.locator('.composition-extra-field')).to_have_count(8);expect(page.locator('#obs-av-pesoGordura')).to_have_value('')
 records=page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')");assert records[1]['composicaoExtras']==['pesoAgua'] and records[1]['avaliacoes'][0]['pesoAgua']=='30'
 assert not errors,errors
 browser.close();print('PASS: optional bioimpedance fields, same-grid checkbox selection per pupil, immediate durable values/settings, no main compression under CPU4, native/library synchronization, actual PDF inclusion/omission/history, hidden values retained, preferences survive deleting all assessments, no cross-pupil leakage')
