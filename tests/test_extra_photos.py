import base64,json,io,urllib.request
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
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
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.png':'image/png'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://app.test/treino36/')
 photos=page.evaluate("""()=>{const draw=(w,h,color)=>{const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.fillStyle=color;x.fillRect(0,0,w,h);return c.toDataURL('image/png');};const old=draw(600,1000,'#b32f28'),current=draw(800,1200,'#2749bd'),wide=draw(1000,400,'#327548');localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento']},avaliacaoId:10},{student_id:'b',nome:'Bia',treino:{A:['Supino']},avaliacaoId:20}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',idade:'30',altura:'1.65',treinoStudentIds:['a'],avaliacaoPreferidaId:12,avaliacoes:[{id:11,data:'01/09/2026',peso:'65',fotosExtras:[{id:'oldmirror',label:'Espelho',src:old,createdAt:'2026-09-01T12:00:00Z'}]},{id:12,data:'01/10/2026',peso:'58'}]},{id:20,nome:'Bia',avaliacoes:[{id:21,data:'01/10/2026'}]}]));return {old,current,wide};}""");page.reload()
 def av():return page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0].avaliacoes.find(av=>av.id===12)")
 def opened():
  page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="fotos"]').click()
 def expand():
  if page.locator('#obsExtraPhotos').get_attribute('open') is None:page.locator('#obsExtraPhotos > summary').click()
 def file(src,name='foto.png'):return {'name':name,'mimeType':'image/png','buffer':base64.b64decode(src.split(',')[1])}
 def card(photo_id):return page.locator('[data-extra-photo-id="'+photo_id+'"]')
 opened();expect(page.locator('#obsExtraPhotos')).to_have_count(1);assert page.locator('#obsExtraPhotos').get_attribute('open') is None;expand()
 assert page.locator('#extraPhotoFiles').get_attribute('multiple') is not None
 with page.expect_file_chooser() as chooser:page.locator('#extraPhotoAdd').click()
 chooser.value.set_files([file(photos['current'],'espelho%d.png'%i) for i in range(8)])
 expect(page.locator('.extra-photo-card')).to_have_count(8);assert len(av()['fotosExtras'])==8 and len({photo['id'] for photo in av()['fotosExtras']})==8
 assert all(photo['createdAt'] for photo in av()['fotosExtras']);first=av()['fotosExtras'][0];first_id=first['id']
 card(first_id).get_by_role('textbox',name='Nome da foto').fill('Espelho');card(first_id).get_by_role('textbox',name='Nome da foto').press('Tab');assert av()['fotosExtras'][0]['label']=='Espelho'
 card(first_id).get_by_role('button',name='Ampliar Foto 1').click() if card(first_id).get_by_role('button',name='Ampliar Foto 1').count() else card(first_id).locator('img').click()
 expect(page.locator('#posturePhotoPreviewDialog')).to_be_visible();expect(page.locator('#postureEditorDialog')).not_to_be_visible();page.keyboard.press('Escape')
 # Every additional photo uses the full editor, including original retention and guide copying.
 card(first_id).get_by_role('button',name='Editar',exact=True).click();editor=page.locator('#postureEditorDialog');expect(editor.locator('[data-action="save"]')).to_be_enabled()
 editor.locator('[data-action="horizontal"]').click();editor.locator('[data-action="copy-line"]').click();editor.locator('[data-action="paste-line"]').click();editor.locator('[data-action="save"]').click();expect(editor).not_to_be_visible()
 edited=av()['fotosExtras'][0];assert edited['original']==first['src'] and len(edited['settings']['lines'])==2
 with page.expect_download() as saved:card(first_id).get_by_role('button',name='Salvar',exact=True).click()
 assert saved.value.suggested_filename=='Ana_Espelho_01_10_2026.jpg';assert Path(saved.value.path()).read_bytes()==base64.b64decode(edited['src'].split(',')[1])
 # Native camera supports cancellation, adding a new photo and existing-photo replacement cancellation.
 with page.expect_file_chooser() as chooser:page.locator('#extraPhotoCamera').click()
 chooser.value.set_files(file(photos['wide']));expect(editor.locator('[data-action="save"]')).to_be_enabled();editor.locator('[data-action="close"]').click();assert len(av()['fotosExtras'])==8
 with page.expect_file_chooser() as chooser:page.locator('#extraPhotoCamera').click()
 chooser.value.set_files(file(photos['wide']));expect(editor.locator('[data-action="save"]')).to_be_enabled();editor.locator('[data-action="logo"]').click();expect(editor.locator('svg image')).to_have_count(1)
 editor.locator('[data-action="save"]').click();expect(editor).not_to_be_visible();expect(page.locator('.extra-photo-card')).to_have_count(9);camera_id=av()['fotosExtras'][-1]['id'];assert av()['fotosExtras'][-1]['settings']['logo']
 with page.expect_file_chooser() as chooser:card(first_id).get_by_role('button',name='Câmera',exact=True).click()
 chooser.value.set_files(file(photos['wide']));expect(editor.locator('[data-action="save"]')).to_be_enabled();editor.locator('[data-action="close"]').click();assert av()['fotosExtras'][0]['src']==edited['src']
 # Dates own their own galleries; no extra photos leak between assessment records.
 page.locator('#obsAssessmentHistory').select_option('11');expand();expect(page.locator('.extra-photo-card')).to_have_count(1);assert card('oldmirror').locator('img').get_attribute('src')==photos['old']
 page.locator('#obsAssessmentHistory').select_option('12');expand();expect(page.locator('.extra-photo-card')).to_have_count(9)
 # Generate the actual shareable PNG: selected photos, actual weights, independent optional settings and original logo.
 page.locator('#extraPhotoCompare').click();composer=page.locator('#assessmentComparisonDialog');expect(composer).to_be_visible()
 expect(page.locator('#comparisonBefore')).to_have_value('11:extra:oldmirror');expect(page.locator('#comparisonAfter')).to_have_value('12:extra:'+first_id)
 expect(page.locator('#comparisonBeforeWeight')).to_have_value('65');expect(page.locator('#comparisonAfterWeight')).to_have_value('58')
 page.locator('#comparisonBeforeWeight').fill('66');page.locator('#comparisonDates').check()
 page.evaluate("()=>{window.beforePreferencesWrite=TreinoStorage.stageAssessment;TreinoStorage.stageAssessment=()=>{throw Error('quota simulada')};}")
 page.locator('#comparisonGenerate').click();expect(page.locator('#comparisonPreview')).to_be_visible();expect(page.locator('#comparisonStatus')).to_contain_text('você pode salvar a imagem');expect(page.locator('#comparisonDownload')).to_be_enabled()
 page.evaluate('()=>{TreinoStorage.stageAssessment=beforePreferencesWrite;}')
 page.locator('#comparisonGenerate').click();expect(page.locator('#comparisonPreview')).to_be_visible()
 with page.expect_download() as generated:page.locator('#comparisonDownload').click()
 assert generated.value.suggested_filename=='Antes_Depois_Ana.png'
 png=Path(generated.value.path()).read_bytes();im=Image.open(io.BytesIO(png));assert im.size==(1080,1350)
 left=im.getpixel((285,600));right=im.getpixel((795,600));assert left[0]-left[2]>80 and right[2]-right[0]>80,(left,right)
 logo_pixels=list(im.crop((210,1170,870,1320)).get_flattened_data());assert sum(1 for r,g,b,a in logo_pixels if g-r>80 and g-b>60)>100
 assert av()['peso']=='58' and av()['comparativoFoto']['beforeWeight']=='66' and av()['comparativoFoto']['dates'] is True
 page.locator('#comparisonPreview').click();expect(page.locator('#posturePhotoPreviewDialog')).to_be_visible();page.keyboard.press('Escape')
 page.locator('#comparisonFit').select_option('cover');expect(page.locator('#comparisonPreview')).not_to_be_visible();expect(page.locator('#comparisonDownload')).to_be_disabled();page.locator('#comparisonGenerate').click();expect(page.locator('#comparisonPreview')).to_be_visible()
 page.screenshot(path='/tmp/extra-photo-comparison-mobile.png');Path('/tmp/extra-photo-before-after.png').write_bytes(png)
 page.locator('#comparisonKeep').click();expect(page.locator('#comparisonStatus')).to_contain_text('guardada');composer.get_by_role('button',name='Fechar',exact=True).click();expect(page.locator('.extra-photo-card')).to_have_count(10)
 assert av()['fotosExtras'][-1]['label']=='Comparativo antes e depois' and av()['comparativoFoto']['fit']=='cover'
 # Confirmed deletion and failed writes preserve all other images and original data.
 deleted_id=av()['fotosExtras'][6]['id'];page.once('dialog',lambda d:d.dismiss());card(deleted_id).get_by_role('button',name='Apagar',exact=True).click();assert len(av()['fotosExtras'])==10
 page.once('dialog',lambda d:d.accept());card(deleted_id).get_by_role('button',name='Apagar',exact=True).click();expect(page.locator('.extra-photo-card')).to_have_count(9)
 card(first_id).get_by_role('button',name='Editar',exact=True).click();editor.locator('[data-action="clear"]').click();page.evaluate("()=>{window.stageBefore=TreinoStorage.stageAssessment;TreinoStorage.stageAssessment=()=>{throw Error('quota simulada')};}")
 editor.locator('[data-action="save"]').click();expect(editor).to_be_visible();expect(page.locator('#postureStatus')).to_contain_text('Não foi possível guardar');assert av()['fotosExtras'][0]['src']==edited['src']
 page.evaluate('()=>{TreinoStorage.stageAssessment=stageBefore;}');editor.locator('[data-action="close"]').click()
 # Real postural PDF includes all named custom images and compares matching labels by date.
 with page.expect_download() as pdf_download:page.locator('#obsAssessment-postural').click()
 with fitz.open(pdf_download.value.path()) as pdf:
  text='\n'.join(p.get_text() for p in pdf);assert pdf.page_count>=3 and 'OUTRAS FOTOS - COMPARATIVO' in text and 'ANTES - 01/09/2026' in text and 'ATUAL - 01/10/2026' in text,text
  for photo in av()['fotosExtras']:assert photo['label'] in text,(photo['label'],text)
  for p in pdf:
   for image in p.get_images():
    for rect in p.get_image_rects(image[0]):assert rect.y1<281*72/25.4
 # JSON export and assessment validation preserve custom photos, originals, guides and comparison settings.
 before=av();page.reload();opened();expand();expect(page.locator('.extra-photo-card')).to_have_count(9);assert av()['fotosExtras']==before['fotosExtras']
 page.keyboard.press('Escape');expect(page.locator('#workoutObsDialog')).not_to_be_visible()
 page.locator('#moreOptions > summary').click()
 with page.expect_download() as exported:page.locator('#exportBtn').click()
 backup=json.loads(Path(exported.value.path()).read_text());exported_av=next(record for record in backup['avaliacoes'][0]['avaliacoes'] if record['id']==12)
 assert exported_av['fotosExtras']==before['fotosExtras'] and exported_av['comparativoFoto']==before['comparativoFoto']
 # Read validation uses the same assessment import path without applying changes to any pupil.
 validated=page.evaluate("AvaliacoesJSON.validate(AvaliacaoTreinoSync.read('avaliacao_fisica_alunos'))")
 assert validated[0]['avaliacoes'][1]['fotosExtras']==before['fotosExtras'];assert validated[0]['avaliacoes'][1]['comparativoFoto']==before['comparativoFoto']
 records=page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')");assert records[0]['avaliacoes'][0]['fotosExtras'][0]['src']==photos['old'];assert 'fotosExtras' not in records[1]['avaliacoes'][0]
 assert not errors,errors
 browser.close();print('PASS: unlimited-style bulk gallery, dated names and isolation, full shared editor and original metadata, native camera add/cancel, direct downloads, actual branded PNG pixels and weight settings, optional fit/dates, save poster into assessment, confirmed delete/quota rollback, custom before/after PDF pages, reload and JSON export/validation')
