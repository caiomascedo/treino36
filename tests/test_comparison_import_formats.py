import base64,io,os,urllib.request
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844});context.add_init_script('window.open=()=>null')
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.png':'image/png'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://app.test/treino36/')
 photos=page.evaluate("""()=>{const photo=color=>{const c=document.createElement('canvas');c.width=600;c.height=1000;const ctx=c.getContext('2d');ctx.fillStyle=color;ctx.fillRect(0,0,600,1000);return c.toDataURL('image/png');};const before=photo('#b32f28'),after=photo('#2749bd'),green=photo('#327548');localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento']},avaliacaoId:10},{student_id:'b',nome:'Bia',treino:{A:['Supino']},avaliacaoId:20}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',idade:'30',altura:'1.65',treinoStudentIds:['a'],avaliacaoPreferidaId:12,avaliacoes:[{id:12,data:'23/09/2026',peso:'58.7',fotoF:before}]},{id:20,nome:'Bia',avaliacoes:[{id:21,data:'01/10/2026'}]}]));return {before,after,green};}""");page.reload()
 def opened():
  page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="fotos"]').click();page.locator('#obsExtraPhotos > summary').click();page.locator('#extraPhotoCompare').click()
 def av():return page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0].avaliacoes[0]")
 def file(src):return {'name':'mesma_foto.png','mimeType':'image/png','buffer':base64.b64decode(src.split(',')[1])}
 def choose(side,kind,content):
  with page.expect_file_chooser() as chooser:page.locator('[data-import-photo="'+side+kind+'"]').click()
  chooser.value.set_files(content)
 def generate(format):
  page.locator('#comparisonFormat').select_option(format);page.locator('#comparisonGenerate').click();expect(page.locator('#comparisonPreview')).to_be_visible()
  with page.expect_download() as saved:page.locator('#comparisonDownload').click()
  return saved.value,Image.open(io.BytesIO(Path(saved.value.path()).read_bytes()))
 opened();dialog=page.locator('#assessmentComparisonDialog');expect(dialog).to_be_visible();expect(page.locator('#comparisonBefore')).to_have_value('12:fotoF');expect(page.locator('#comparisonAfter')).to_have_value('');expect(page.locator('#comparisonGenerate')).to_be_disabled()
 choose('After','Upload',file(photos['after']));expect(page.locator('#comparisonStatus')).to_contain_text('Foto adicionada em Depois');assert len(av()['fotosExtras'])==1
 after_id=av()['fotosExtras'][0]['id'];expect(page.locator('#comparisonAfter')).to_have_value('12:extra:'+after_id);expect(page.locator('#comparisonBefore')).to_have_value('12:fotoF')
 today=page.evaluate("new Date().toLocaleDateString('pt-BR')");today_iso=page.evaluate("new Date().toLocaleDateString('sv-SE')");assert av()['fotosExtras'][0]['date']==today and av()['data']=='23/09/2026';expect(page.locator('#comparisonAfterDate')).to_have_value(today_iso)
 # A file modified years ago is accepted; importing it appends rather than replacing today's photo.
 old_file=Path('/tmp/comparison-old-synthetic.png');old_file.write_bytes(base64.b64decode(photos['before'].split(',')[1]));os.utime(old_file,(1577836800,1577836800))
 choose('Before','Upload',str(old_file));expect(page.locator('#comparisonStatus')).to_contain_text('Foto adicionada em Antes');assert len(av()['fotosExtras'])==2
 before_id=av()['fotosExtras'][-1]['id'];expect(page.locator('#comparisonBefore')).to_have_value('12:extra:'+before_id);expect(page.locator('#comparisonAfter')).to_have_value('12:extra:'+after_id)
 assert av()['fotoF']==photos['before']
 # Reusing a filename and taking a new camera image still appends separate entries.
 with page.expect_file_chooser() as chooser:page.locator('[data-import-photo="AfterCamera"]').click()
 assert page.locator('#comparisonAfterCamera').get_attribute('capture')=='environment';chooser.value.set_files(file(photos['green']));expect(page.locator('#comparisonStatus')).to_contain_text('Foto adicionada em Depois');assert len(av()['fotosExtras'])==3
 third_id=av()['fotosExtras'][-1]['id'];expect(page.locator('#comparisonAfter')).to_have_value('12:extra:'+third_id);expect(page.locator('#comparisonBefore')).to_have_value('12:extra:'+before_id)
 choose('Before','Upload',str(old_file));expect(page.locator('#comparisonStatus')).to_contain_text('Foto adicionada em Antes');assert len(av()['fotosExtras'])==4 and len({photo['id'] for photo in av()['fotosExtras']})==4
 fourth_id=av()['fotosExtras'][-1]['id'];selection_before=page.locator('#comparisonBefore').input_value();selection_after=page.locator('#comparisonAfter').input_value()
 # Decode failure retains both selections and all stored photos and re-enables retry.
 choose('After','Upload',{'name':'invalida.jpg','mimeType':'image/jpeg','buffer':b'not an image'})
 expect(page.locator('#comparisonStatus')).to_contain_text('Erro ao carregar imagem');assert len(av()['fotosExtras'])==4;expect(page.locator('#comparisonBefore')).to_have_value(selection_before);expect(page.locator('#comparisonAfter')).to_have_value(selection_after);expect(page.locator('[data-import-photo="AfterUpload"]')).to_be_enabled()
 page.locator('#comparisonBeforeDate').fill('2020-01-01');page.locator('#comparisonDates').check();page.locator('#comparisonBeforeWeight').fill('66');page.locator('#comparisonAfterWeight').fill('58')
 saved,im=generate('feed');assert saved.suggested_filename=='Antes_Depois_Ana.png' and im.size==(1080,1350)
 assert av()['comparativoFoto']['beforeDate']=='01/01/2020' and av()['comparativoFoto']['afterDate']==today and av()['data']=='23/09/2026'
 saved,im=generate('story');assert saved.suggested_filename.endswith('_Stories.png') and im.size==(1080,1920)
 pixels=list(im.crop((200,1620,880,1765)).get_flattened_data());assert sum(1 for r,g,b,a in pixels if g-r>80 and g-b>60)>100
 saved,im=generate('reels');assert saved.suggested_filename.endswith('_Reels.png') and im.size==(1080,1920)
 pixels=list(im.crop((200,1480,880,1625)).get_flattened_data());assert sum(1 for r,g,b,a in pixels if g-r>80 and g-b>60)>100
 assert sum(1 for r,g,b,a in im.crop((0,1720,1080,1920)).get_flattened_data() if r>220 and g>220 and b>220)==0
 Path('/tmp/comparison-reels-preview.png').write_bytes(Path(saved.path()).read_bytes());page.screenshot(path='/tmp/comparison-direct-import-mobile.png')
 page.locator('#comparisonKeep').click();expect(page.locator('#comparisonStatus')).to_contain_text('guardada');assert len(av()['fotosExtras'])==5
 saved_image=Image.open(io.BytesIO(base64.b64decode(av()['fotosExtras'][-1]['src'].split(',')[1])));assert saved_image.size==(1080,1920)
 dialog.get_by_role('button',name='Fechar',exact=True).click();expect(page.locator('.extra-photo-card')).to_have_count(5)
 # Independent photo dates are editable without changing the assessment date.
 card=page.locator('[data-extra-photo-id="'+after_id+'"]');card.get_by_label('Data da foto').fill('2024-05-20');assert next(photo for photo in av()['fotosExtras'] if photo['id']==after_id)['date']=='20/05/2024' and av()['data']=='23/09/2026'
 page.reload();opened();expect(page.locator('#comparisonFormat')).to_have_value('reels');expect(page.locator('#comparisonBefore')).to_have_value('12:extra:'+fourth_id);expect(page.locator('#comparisonAfter')).to_have_value('12:extra:'+third_id);expect(page.locator('#comparisonBeforeDate')).to_have_value('2020-01-01');assert len(av()['fotosExtras'])==5
 assert 'fotosExtras' not in page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[1].avaliacoes[0]")
 assert not errors,errors
 browser.close();print('PASS: single legacy photo, repeated direct upload and camera imports, old-file acceptance, independent photo dates, append/selection preservation on success and error, actual Feed/Stories/Reels PNG dimensions and safe bottom area, retained full-resolution saved poster, reload and pupil isolation')
