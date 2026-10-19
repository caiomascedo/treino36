import base64,urllib.request,fitz
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
URLS=['https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js','https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js']
scripts={url:urllib.request.urlopen(url,timeout=30).read() for url in URLS}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844});context.add_init_script('window.open=()=>null')
 def route(r):
  if r.request.url in scripts:r.fulfill(body=scripts[r.request.url],content_type='application/javascript');return
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://app.test/treino36/')
 photos=page.evaluate("""()=>{const draw=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.fillStyle='rgb(245,245,245)';x.fillRect(0,0,w,h);x.fillStyle='#94a3b8';x.fillRect(w*.3,h*.2,w*.4,h*.6);return c.toDataURL('image/png');};const portrait=draw(600,1000),landscape=draw(1000,400),old=draw(200,200);localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento']},avaliacaoId:10},{student_id:'b',nome:'Bia',treino:{A:['Supino']},avaliacaoId:20}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',idade:'30',treinoStudentIds:['a'],avaliacaoPreferidaId:12,avaliacoes:[{id:11,data:'01/09/2026',fotoF:old},{id:12,data:'01/10/2026',fotoF:portrait}]},{id:20,nome:'Bia',avaliacoes:[{id:21,data:'01/10/2026'}]}]));return {portrait,landscape,old};}""");page.reload()
 def open_photos():
  page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="fotos"]').click()
 def av():return page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0].avaliacoes[1]")
 def pixels(src):return page.evaluate("""async src=>{const image=new Image();image.src=src;await image.decode();const c=document.createElement('canvas');c.width=image.width;c.height=image.height;const x=c.getContext('2d');x.drawImage(image,0,0);return [...x.getImageData(90,100,1,1).data];}""",src)
 open_photos();page.locator('[data-posture-edit="fotoF"]').click();dialog=page.locator('#postureEditorDialog');expect(dialog).to_be_visible();dialog.locator('.posture-stage img').evaluate('(e)=>e.decode()')
 expect(page.locator('#postureGrid')).not_to_be_checked()
 box=dialog.locator('.posture-stage').bounding_box();work=dialog.locator('.posture-workspace').bounding_box()
 assert box['width']<=work['width'] and box['height']<=work['height'] and abs(box['width']/box['height']-.6)<.01,(box,work)
 for kind in ['vertical','horizontal','ruler']:dialog.locator('[data-action="'+kind+'"]').click()
 expect(page.locator('#postureLine option')).to_have_count(3)
 svg=dialog.locator('svg');end=svg.locator('circle').nth(1).bounding_box();stage=dialog.locator('.posture-stage').bounding_box()
 page.mouse.move(end['x']+end['width']/2,end['y']+end['height']/2);page.mouse.down();page.mouse.move(stage['x']+stage['width']*.7,stage['y']+stage['height']*.68,steps=10);page.mouse.up()
 after=svg.locator('circle').nth(1).get_attribute('cy');assert float(after)>600,after
 dialog.locator('[data-action="undo"]').click();assert abs(float(svg.locator('circle').nth(1).get_attribute('cy'))-450)<1
 dialog.locator('[data-action="redo"]').click();assert svg.locator('circle').nth(1).get_attribute('cy')==after
 page.locator('#postureGrid').check();page.locator('#postureSpacing').select_option('15')
 dialog.locator('[data-action="save"]').click();expect(dialog).not_to_be_visible()
 marked=av();assert marked['fotoFOriginal']==photos['portrait'];assert marked['posturaEdicoes']['fotoF']['grid'] is True;assert len(marked['posturaEdicoes']['fotoF']['lines'])==3
 pixel=pixels(marked['fotoF']);assert pixel[1]-pixel[0]>20,pixel
 page.reload();open_photos();page.locator('[data-posture-edit="fotoF"]').click();expect(page.locator('#postureGrid')).to_be_checked();expect(page.locator('#postureLine option')).to_have_count(3)
 assert dialog.locator('.posture-stage img').get_attribute('src')==photos['portrait']
 dialog.locator('[data-action="save"]').click();expect(dialog).not_to_be_visible();assert av()['fotoF']==marked['fotoF'],'Repeated save must not bake the existing guides a second time'
 page.locator('[data-posture-edit="fotoF"]').click();page.locator('#postureGrid').uncheck();dialog.locator('[data-action="save"]').click();expect(dialog).not_to_be_visible();without=av()
 pixel=pixels(without['fotoF']);assert abs(pixel[1]-pixel[0])<5,pixel
 assert without['fotoFOriginal']==photos['portrait'] and len(without['posturaEdicoes']['fotoF']['lines'])==3
 # Rotate a constrained horizontal line, hide the handles and independently recolor the grid.
 page.locator('[data-posture-edit="fotoF"]').click();page.locator('#postureLine').select_option(index=1)
 def set_angle(degrees):
  page.locator('#postureAngle').evaluate('(e,value)=>{e.value=value;e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}));}',str(degrees))
 set_angle(35);expect(page.locator('#postureAngleValue')).to_have_text('35°')
 dialog.locator('[data-action="rotate-right"]').click();expect(page.locator('#postureAngleValue')).to_have_text('40°')
 page.locator('#postureHandles').uncheck();expect(svg.locator('circle')).to_have_count(0);assert svg.locator('[data-part="body"]').count()==3
 page.locator('#postureGrid').check()
 page.locator('#postureGridColor').evaluate('(e)=>{e.value="#2563eb";e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}));}')
 assert page.locator('#postureColor').input_value()=='#ef4444'
 dialog.locator('[data-action="save-top"]').click();expect(dialog).not_to_be_visible();without=av()
 settings=without['posturaEdicoes']['fotoF'];assert settings['showHandles'] is False and settings['gridColor']=='#2563eb'
 rotated=settings['lines'][1];assert rotated['kind']=='line'
 assert abs(page.evaluate('(line)=>PostureEditor.angle(line,600,1000)',rotated)-40)<.01
 pixel=pixels(without['fotoF']);assert pixel[2]-pixel[0]>20,pixel
 page.locator('[data-posture-edit="fotoF"]').click();expect(page.locator('#postureHandles')).not_to_be_checked();expect(svg.locator('circle')).to_have_count(0)
 assert page.locator('#postureGridColor').input_value()=='#2563eb';page.locator('#postureLine').select_option(index=1);expect(page.locator('#postureAngleValue')).to_have_text('40°')
 page.locator('#postureHandles').check();expect(svg.locator('circle')).to_have_count(2)
 dialog.locator('[data-action="close"]').click();assert av()['posturaEdicoes']['fotoF']['showHandles'] is False
 # The native camera picker opens within the editor, and cancelling preserves the old photo.
 frontal=page.locator('#obs-av-fotoF').locator('..')
 with page.expect_file_chooser() as chooser:frontal.get_by_role('button',name='📷 Câmera',exact=True).click()
 assert page.locator('#postureCameraInput').get_attribute('capture')=='environment'
 chooser.value.set_files({'name':'landscape.png','mimeType':'image/png','buffer':base64.b64decode(photos['landscape'].split(',')[1])})
 dialog.locator('.posture-stage img').evaluate('(e)=>e.decode()')
 dialog.locator('[data-action="close"]').click();assert av()['fotoF']==without['fotoF']
 # Save a landscape lateral photo and verify both photos fit the actual exported PDF.
 lateral=page.locator('#obs-av-fotoL').locator('..')
 lateral.locator('input[type=file]').set_input_files({'name':'landscape.png','mimeType':'image/png','buffer':base64.b64decode(photos['landscape'].split(',')[1])})
 expect(dialog.locator('[data-action="save"]')).to_be_enabled();dialog.locator('[data-action="save"]').click();expect(dialog).not_to_be_visible()
 with page.expect_download() as download:page.locator('#obsAssessment-postural').click()
 with fitz.open(download.value.path()) as pdf:
  assert pdf.page_count==2
  ratios=[r.width/r.height for image in pdf[-1].get_images() for r in pdf[-1].get_image_rects(image[0])]
  assert any(abs(r-.6)<.02 for r in ratios) and any(abs(r-2.5)<.02 for r in ratios),ratios
 expect(page.locator('#searchName')).to_have_value('Ana')
 # Failed persistence retains the original and keeps the in-progress editor open.
 page.locator('[data-posture-edit="fotoF"]').click();dialog.locator('[data-action="clear"]').click()
 page.evaluate("()=>{window.stageBefore=TreinoStorage.stageAssessment;TreinoStorage.stageAssessment=()=>{throw Error('quota simulada')};}")
 dialog.locator('[data-action="save"]').click();expect(dialog).to_be_visible();expect(page.locator('#postureStatus')).to_contain_text('Não foi possível salvar')
 page.evaluate("()=>{TreinoStorage.stageAssessment=stageBefore;}");assert av()['fotoF']==without['fotoF'];dialog.locator('[data-action="close"]').click()
 page.once('dialog',lambda d:d.dismiss());frontal.get_by_role('button',name='Apagar',exact=True).click();assert av()['fotoF']==without['fotoF']
 page.locator('[data-posture-edit="fotoF"]').click();page.once('dialog',lambda d:d.dismiss());dialog.locator('[data-action="delete-photo"]').click();expect(dialog).to_be_visible();assert av()['fotoF']==without['fotoF']
 page.once('dialog',lambda d:d.accept());dialog.locator('[data-action="delete-photo"]').click();expect(dialog).not_to_be_visible();assert av()['fotoF'] is None and av()['fotoFOriginal'] is None and 'fotoF' not in av()['posturaEdicoes']
 records=page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')")
 assert records[0]['avaliacoes'][0]['fotoF']==photos['old'];assert records[0]['avaliacoes'][1]['fotoL'];assert 'fotoF' not in records[1]['avaliacoes'][0]
 assert not errors,errors
 browser.close();print('PASS: mobile fit, endpoint dragging/angles, rotation slider/buttons, hidden handles, independent persisted grid color, top save, undo/redo, baked optional grid verified by pixels, original retained/re-edit without double overlays, camera/gallery and cancel, actual PDF aspect ratios, immediate durable saves and isolation, quota rollback and confirmed deletion inside/outside editor')
