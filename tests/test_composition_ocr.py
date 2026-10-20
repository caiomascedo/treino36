"""Real local OCR + PDF extraction, review/apply in both assessment editors."""
import hashlib,json,urllib.request,fitz
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
CACHE=Path('/tmp/treino36-ocr-cache');CACHE.mkdir(exist_ok=True)
# Synthetic, anonymous documents reproducing the supplied labels and units.
def image_fixture():
 lines=(ROOT/'tests/fixtures/composition/fitdays.txt').read_text().splitlines();im=Image.new('RGB',(1200,80+len(lines)*52),'white');draw=ImageDraw.Draw(im);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',30)
 for i,line in enumerate(lines):draw.text((35,25+i*52),line,font=font,fill='black')
 path=CACHE/'fitdays.png';im.save(path);return path

def pdf_fixture(name):
 lines=(ROOT/f'tests/fixtures/composition/{name}.txt').read_text().splitlines();doc=fitz.open();page=doc.new_page(width=700,height=1200)
 for i,line in enumerate(lines):page.insert_text((30,30+i*20),line,fontsize=11)
 path=CACHE/(name+'.pdf');doc.save(path);doc.close();return path
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  u=urlparse(r.request.url)
  if u.hostname=='app.test':
   path=ROOT/u.path.removeprefix('/treino36/').lstrip('/')
   if path.is_dir():path/='index.html'
   if path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'));return
  if u.hostname in ['cdn.jsdelivr.net','cdnjs.cloudflare.com','tessdata.projectnaptha.com']:
   cached=CACHE/hashlib.sha256(r.request.url.encode()).hexdigest()
   if not cached.exists():
    try:cached.write_bytes(urllib.request.urlopen(r.request.url,timeout=30).read())
    except Exception as error:print('ASSET FAILED',r.request.url,error,flush=True);r.fulfill(status=404);return
   mime='application/wasm' if u.path.endswith('.wasm') else 'application/javascript' if '.js' in u.path else 'application/octet-stream'
   r.fulfill(body=cached.read_bytes(),content_type=mime,headers={'Access-Control-Allow-Origin':'*'});return
  r.fulfill(status=404)
 context.route('**/*',route)
 page.goto('http://app.test/treino36/')
 page.evaluate('''()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ocr',nome:'Exemplo',avaliacaoId:10,treino:{A:['Agachamento 3x10']},infoRelevante:{idade:'24',altura:'1.63',peso:'72'}}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Exemplo',sexo:'F',idade:'24',altura:'1.63',treinoStudentIds:['ocr'],avaliacoes:[{id:11,data:'20/10/2026',peso:'72',agua:'50',protocolo:'jp7',resumo:'Preservar observação'}]},{id:20,nome:'Outro',sexo:'M',avaliacoes:[{id:21,peso:'80'}]}]));}''');page.reload();page.locator('#searchName').fill('Exemplo');page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('[data-assessment-section="composicao"]').click();expect(page.locator('#obs-av-peso')).to_have_value('72')
 original_other=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[1]")
 def upload(path):
  if path.stem in ['inbody','fitdays']:
   panel=page.locator('#obsNativeAssessment .composition-reader-'+path.stem)
   if not panel.evaluate('el=>el.open'):panel.locator('summary').click()
   panel.locator('input[type=file]').set_input_files(path)
  else:page.locator('#obsNativeAssessment .composition-extras-tools input[type=file]').set_input_files(path)
  expect(page.locator('.composition-reader-dialog')).to_be_visible(timeout=120000)
  expect(page.get_by_role('textbox',name='Valor lido de Peso (kg)',exact=True)).to_have_value('77.6' if path.suffix=='.png' else '58.7' if path.stem=='planilha' else '56.9')
 def apply():
  page.locator('.composition-reader-apply').click()
  if page.locator('.composition-reader-dialog').count():print('IMPORT STATUS:',page.locator('.composition-reader-dialog [role=status]').inner_text(),flush=True)
  expect(page.locator('.composition-reader-dialog')).to_have_count(0)
 upload(pdf_fixture('planilha'))
 # Cancel leaves the assessment untouched. A second import applies only reviewed fields.
 page.locator('.composition-reader-dialog').get_by_role('button',name='Cancelar',exact=True).click();expect(page.locator('#obs-av-peso')).to_have_value('72')
 upload(pdf_fixture('planilha'));apply();expect(page.locator('#obs-av-peso')).to_have_value('58.7');expect(page.locator('#obs-av-imc')).to_have_value('25.4');expect(page.locator('#obs-av-musculoEsqueleticoKg')).to_have_value('20');expect(page.locator('#obs-av-massaMuscularPct')).to_have_value('59.8');expect(page.locator('#obs-av-metabolismoInformado')).to_have_value('1197.8');expect(page.locator('#obs-av-agua')).to_have_value('50')
 assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].data")=='20/10/2026'
 print('PASS: native PDF text extraction, review/cancel, separate muscle units, preserved missing fields and reported IMC',flush=True)
 page.locator('#obsNativeAssessment .composition-extras-tools input[type=file]').set_input_files(pdf_fixture('fitdays'));expect(page.locator('#obsNativeAssessment .composition-extras-tools .composition-reader-status')).to_contain_text('leitor exclusivo Fitdays');expect(page.locator('.composition-reader-dialog')).to_have_count(0);expect(page.locator('#obs-av-peso')).to_have_value('58.7')
 upload(image_fixture());expect(page.get_by_role('textbox',name='Valor lido de Massa muscular total (kg)',exact=True)).to_have_value('52.5');expect(page.get_by_role('textbox',name='Valor lido de Massa muscular esquelética',exact=False).first).to_have_value('49.5')
 # Real OCR can flag low-confidence candidates; explicitly review all valid values in the fixture.
 for checkbox in page.locator('.composition-reader-row input[type=checkbox]').all():checkbox.check()
 page.locator('.composition-reader-dialog').screenshot(path='/tmp/treino36-composition-ocr-review.png');apply();expect(page.locator('#obs-av-massamuscular')).to_have_value('52.5');expect(page.locator('#obs-av-musculoEsqueleticoPct')).to_have_value('49.5');expect(page.locator('#obs-av-idadeMetabolica')).to_have_value('32');expect(page.locator('#obs-av-imc')).to_have_value('27.8')
 page.reload();page.locator('#searchName').fill('Exemplo');page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('[data-assessment-section="composicao"]').click();expect(page.locator('#obs-av-idadeMetabolica')).to_have_value('32');expect(page.locator('#obs-av-imc')).to_have_value('27.8')
 print('PASS: real image OCR (Tesseract por+eng), numeric field matching, review/application and persistence of reported values',flush=True)
 scanned=CACHE/'fitdays-scanned.pdf';doc=fitz.open();pdoc=doc.new_page(width=600,height=850);pdoc.insert_image(pdoc.rect,filename=str(image_fixture()));doc.save(scanned);doc.close()
 panel=page.locator('#obsNativeAssessment .composition-reader-fitdays')
 if not panel.evaluate('el=>el.open'):panel.locator('summary').click()
 panel.locator('input[type=file]').set_input_files(scanned);expect(page.locator('.composition-reader-dialog')).to_be_visible(timeout=120000);expect(page.get_by_role('textbox',name='Valor lido de Peso (kg)',exact=True)).to_have_value('77.6');page.locator('.composition-reader-dialog').get_by_role('button',name='Cancelar',exact=True).click()
 print('PASS: image-only PDF rasterization and real OCR fallback',flush=True)
 upload(pdf_fixture('inbody'));apply();expect(page.locator('#obs-av-aguaLitros')).to_have_value('27.2');expect(page.locator('#obs-av-proteinaKg')).to_have_value('7.2');expect(page.locator('#obs-av-mineraisKg')).to_have_value('2.84');expect(page.locator('#obs-av-metabolismoInformado')).to_have_value('1174');expect(page.locator('#obs-av-controleGorduraInbody')).to_have_value('-6.7');expect(page.locator('#obs-av-impedancia100_pe')).to_have_value('319.1')
 page.screenshot(path='/tmp/treino36-composition-ocr-applied.png')
 records=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))");assert records[1]==original_other;assert records[0]['avaliacoes'][0]['resumo']=='Preservar observação'
 print('PASS: InBody units, reference ranges, controls, segments and impedance; unrelated pupil and observations unchanged',flush=True)
 # The existing TMB selectors remain independent: calculated or reported or both.
 page.locator('.composition-extras-add').first.click()
 page.locator('input[data-extra-key="tmb"]').uncheck();expect(page.locator('#obs-av-tmb')).to_be_hidden();expect(page.locator('#obs-av-metabolismoInformado')).to_be_visible();page.locator('input[data-extra-key="tmb"]').check();expect(page.locator('#obs-av-tmb')).to_be_visible()
 page.locator('#workoutObsDialog [data-close]').click()
 library=context.new_page();library.on('pageerror',lambda e:errors.append(str(e)));library.goto('http://app.test/treino36/avaliacao.html?treinoStudentId=ocr&embed=treino36&secao=composicao')
 scope=library.locator('[data-extra-record="10"][data-extra-av="11"][data-extra-section="composicao"]');scope.locator('input[type=file]').set_input_files(pdf_fixture('planilha'));expect(library.locator('.composition-reader-dialog')).to_be_visible();library.locator('.composition-reader-apply').click();expect(library.locator('.composition-reader-dialog')).to_have_count(0);expect(library.locator('#imc-10-11')).to_have_value('25.4')
 print('PASS: independent general/Fitdays/InBody readers and full assessment library import',flush=True)
 # Workout reader stays inside Mais opções and native PDFs are reviewed before applying.
 assert page.locator('#moreOptions #ocrImageBtn').count()==1
 page.locator('#moreOptions > summary').click()
 source=(ROOT/'tests/fixtures/workout-youtube.txt').read_text();doc=fitz.open();wp=doc.new_page(width=1100,height=1800);wp.insert_font(fontname='DejaVu',fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
 for i,line in enumerate(source.splitlines()):wp.insert_text((30,30+i*22),line,fontsize=12,fontname='DejaVu')
 workout=CACHE/'workout.pdf';doc.save(workout);doc.close()
 with page.expect_file_chooser() as chooser:page.locator('#ocrImageBtn').click()
 chooser.value.set_files(workout);expect(page.locator('#pasteTextarea')).to_be_visible(timeout=20000)
 cleaned=page.locator('#pasteTextarea').input_value();assert 'YouTube' not in cleaned and 'ENouTube' not in cleaned
 assert '50%' in cleaned and '100kg' in cleaned and 'Conforme A Execução Dela.' in cleaned
 page.locator('#confirmPasteBtn').click()
 for section,count in [('a',6),('b',7),('c',7),('d',7),('e',7)]:expect(page.locator('.sec-'+section+' ol li')).to_have_count(count)
 assert 'youtube' not in page.locator('.sec-a ol').inner_text().lower()
 print('PASS: workout PDF native text, video badges stripped, review before applying, 34 exercises and A–E sections preserved, reader retained in Mais opções',flush=True)
 assert not errors,errors
 browser.close()
