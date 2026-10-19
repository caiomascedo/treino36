import base64,urllib.request,fitz
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
URLS=['https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js','https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js']
scripts={url:urllib.request.urlopen(url,timeout=30).read() for url in URLS}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844},has_touch=True);context.add_init_script('window.open=()=>null')
 def route(r):
  if r.request.url in scripts:r.fulfill(body=scripts[r.request.url],content_type='application/javascript');return
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.png':'image/png'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://app.test/treino36/')
 photos=page.evaluate("""()=>{const draw=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.fillStyle='rgb(245,245,245)';x.fillRect(0,0,w,h);x.fillStyle='#94a3b8';x.fillRect(w*.3,h*.2,w*.4,h*.6);return c.toDataURL('image/png');};const portrait=draw(600,1000),landscape=draw(1000,400),old=draw(200,200);localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento']},avaliacaoId:10},{student_id:'b',nome:'Bia',treino:{A:['Supino']},avaliacaoId:20}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',idade:'30',treinoStudentIds:['a'],avaliacaoPreferidaId:12,avaliacoes:[{id:11,data:'01/09/2026',fotoF:old},{id:12,data:'01/10/2026',fotoF:portrait}]},{id:20,nome:'Bia',avaliacoes:[{id:21,data:'01/10/2026'}]}]));return {portrait,landscape,old};}""");page.reload()
 def open_photos():
  page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="fotos"]').click()
 def av():return page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')[0].avaliacoes[1]")
 def pixels(src,x=90):return page.evaluate("""async ({src,pixelX})=>{const image=new Image();image.src=src;await image.decode();const c=document.createElement('canvas');c.width=image.width;c.height=image.height;const x=c.getContext('2d');x.drawImage(image,0,0);return [...x.getImageData(pixelX,100,1,1).data];}""",{"src":src,"pixelX":x})
 open_photos();page.locator('[data-posture-edit="fotoF"]').click();dialog=page.locator('#postureEditorDialog');expect(dialog).to_be_visible();dialog.locator('.posture-stage img').evaluate('(e)=>e.decode()')
 expect(page.locator('#postureGrid')).not_to_be_checked()
 box=dialog.locator('.posture-stage').bounding_box();work=dialog.locator('.posture-workspace').bounding_box()
 assert box['width']<=work['width'] and box['height']<=work['height'] and abs(box['width']/box['height']-.6)<.01,(box,work)
 # Exercise real multi-touch events, rather than calling the zoom implementation.
 cdp=context.new_cdp_session(page)
 def touch(kind,points):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[{'x':x,'y':y,'id':i+1} for i,(x,y) in enumerate(points)]})
 work=dialog.locator('.posture-workspace').bounding_box();cx=work['x']+work['width']/2;cy=work['y']+work['height']/2
 touch('touchStart',[(cx-35,cy),(cx+35,cy)]);touch('touchMove',[(cx-70,cy),(cx+70,cy)]);touch('touchEnd',[])
 expect(page.locator('#postureZoomValue')).to_have_text('200%')
 enlarged=dialog.locator('.posture-stage').bounding_box();assert abs(enlarged['width']/box['width']-2)<.02
 # A guide remains editable in source-image coordinates while zoomed.
 dialog.locator('[data-action="horizontal"]').click();end=dialog.locator('svg circle').nth(1).bounding_box()
 page.mouse.move(end['x']+end['width']/2,end['y']+end['height']/2);page.mouse.down();page.mouse.move(enlarged['x']+enlarged['width']*.65,enlarged['y']+enlarged['height']*.52,steps=8);page.mouse.up()
 assert abs(float(dialog.locator('svg circle').nth(1).get_attribute('cx'))-390)<2
 assert abs(float(dialog.locator('svg circle').nth(1).get_attribute('cy'))-520)<2
 dialog.locator('[data-action="undo"]').click();dialog.locator('[data-action="undo"]').click()
 dialog.locator('[data-action="zoom-reset"]').click();expect(page.locator('#postureZoomValue')).to_have_text('100%')
 dialog.locator('[data-action="zoom-out"]').click();expect(page.locator('#postureZoomValue')).to_have_text('83%')
 dialog.locator('[data-action="zoom-reset"]').click()
 # Lock either the default or an enlarged view; real pinch/pan cannot change it.
 dialog.locator('[data-action="zoom-in"]').click();dialog.locator('[data-action="zoom-lock"]').click()
 expect(dialog.locator('[data-action="zoom-lock"]')).to_have_attribute('aria-pressed','true');expect(dialog.locator('[data-action="zoom-reset"]')).to_be_disabled()
 frozen=dialog.locator('.posture-stage').get_attribute('style')
 work=dialog.locator('.posture-workspace').bounding_box();cx=work['x']+work['width']/2;cy=work['y']+work['height']/2
 touch('touchStart',[(cx-30,cy),(cx+30,cy)]);touch('touchMove',[(cx-65,cy+12),(cx+65,cy+12)]);touch('touchEnd',[])
 page.mouse.move(work['x']+8,cy);page.mouse.down();page.mouse.move(work['x']+25,cy+30,steps=5);page.mouse.up()
 assert dialog.locator('.posture-stage').get_attribute('style')==frozen
 expect(page.locator('#postureZoomValue')).to_have_text('120%')
 dialog.locator('[data-action="expand"]').click();expect(dialog).to_have_class('posture-editor is-expanded');expect(dialog.locator('[data-action="expand"]')).to_have_attribute('aria-pressed','true')
 page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
 expanded=dialog.bounding_box();assert expanded['width']>=389 and expanded['height']>=843,expanded
 expect(page.locator('#postureZoomValue')).to_have_text('120%')
 dialog.locator('[data-action="expand"]').click();expect(dialog).to_have_class('posture-editor')
 dialog.locator('[data-action="zoom-lock"]').click();dialog.locator('[data-action="zoom-reset"]').click()
 # Default size can be locked too.
 dialog.locator('[data-action="zoom-lock"]').click();expect(page.locator('#postureZoomValue')).to_have_text('100%');dialog.locator('[data-action="zoom-lock"]').click()
 for kind in ['vertical','horizontal','ruler']:dialog.locator('[data-action="'+kind+'"]').click()
 expect(page.locator('#postureLine option')).to_have_count(3)
 svg=dialog.locator('svg')
 # Both horizontal and vertical guides rotate freely by dragging either endpoint.
 for index in [0,1]:
  page.locator('#postureLine').select_option(index=index);dots=svg.locator('circle');start=dots.nth(0).get_attribute('cx'),dots.nth(0).get_attribute('cy')
  end=dots.nth(1).bounding_box();stage=dialog.locator('.posture-stage').bounding_box()
  page.mouse.move(end['x']+end['width']/2,end['y']+end['height']/2);page.mouse.down();page.mouse.move(stage['x']+stage['width']*.7,stage['y']+stage['height']*.65,steps=10);page.mouse.up()
  assert abs(float(dots.nth(1).get_attribute('cx'))-420)<2 and abs(float(dots.nth(1).get_attribute('cy'))-650)<2
  assert (float(dots.nth(0).get_attribute('cx')),float(dots.nth(0).get_attribute('cy')))==tuple(map(float,start)),(index,start,dots.nth(0).get_attribute('cx'),dots.nth(0).get_attribute('cy'))
  dialog.locator('[data-action="undo"]').click()
 page.locator('#postureLine').select_option(index=0);stage=dialog.locator('.posture-stage').bounding_box()
 page.mouse.move(stage['x']+stage['width']*.5,stage['y']+stage['height']*.3);page.mouse.down();page.mouse.move(stage['x']+stage['width']*.51,stage['y']+stage['height']*.305,steps=5)
 expect(page.locator('#postureAlignment')).to_have_text('Centralizado ↔ ↕');assert svg.locator('[data-alignment]').count()==4
 assert abs(float(svg.locator('circle').first.get_attribute('cx'))-300)<.01
 page.mouse.up();expect(page.locator('#postureAlignment')).not_to_be_visible();expect(svg.locator('[data-alignment]')).to_have_count(0)
 page.locator('#postureLine').select_option(index=2)
 end=svg.locator('circle').nth(1).bounding_box();stage=dialog.locator('.posture-stage').bounding_box()
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
 # Rotate directly on the image; no numeric rotation controls are shown.
 assert dialog.locator('.posture-rotation').count()==0
 end=svg.locator('circle').nth(1).bounding_box();stage=dialog.locator('.posture-stage').bounding_box()
 page.mouse.move(end['x']+end['width']/2,end['y']+end['height']/2);page.mouse.down();page.mouse.move(stage['x']+stage['width']*.7,stage['y']+stage['height']*.70173,steps=10);page.mouse.up()
 page.locator('#postureHandles').uncheck();expect(svg.locator('circle')).to_have_count(0);assert svg.locator('[data-part="body"]').count()==3
 page.locator('#postureGrid').check()
 page.locator('#postureGridColor').evaluate('(e)=>{e.value="#2563eb";e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}));}')
 for field,value in [('postureGridThickness','4'),('postureGridTransparency','70')]:
  page.locator('#'+field).evaluate('(e,value)=>{e.value=value;e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}));}',value)
 expect(page.locator('#postureGridThicknessValue')).to_have_text('4×');expect(page.locator('#postureGridTransparencyValue')).to_have_text('70%')
 assert svg.locator('line[stroke="#2563eb"]').first.get_attribute('stroke-width')=='4'
 assert abs(float(svg.locator('line[stroke="#2563eb"]').first.get_attribute('stroke-opacity'))-.3)<.001
 assert page.locator('#postureColor').input_value()=='#ef4444'
 dialog.locator('[data-action="save-top"]').click();expect(dialog).not_to_be_visible();without=av()
 settings=without['posturaEdicoes']['fotoF'];assert settings['showHandles'] is False and settings['gridColor']=='#2563eb'
 assert settings['gridThickness']==4 and settings['gridTransparency']==70
 rotated=settings['lines'][1];assert rotated['kind']=='line'
 assert abs(page.evaluate('(line)=>PostureEditor.angle(line,600,1000)',rotated)-40)<1
 pixel=pixels(without['fotoF'],91);assert pixel[2]-pixel[0]>20,pixel
 page.locator('[data-posture-edit="fotoF"]').click();expect(page.locator('#postureHandles')).not_to_be_checked();expect(svg.locator('circle')).to_have_count(0)
 assert page.locator('#postureGridColor').input_value()=='#2563eb';page.locator('#postureLine').select_option(index=1)
 assert page.locator('#postureGridThickness').input_value()=='4' and page.locator('#postureGridTransparency').input_value()=='70'
 page.locator('#postureHandles').check();expect(svg.locator('circle')).to_have_count(2)
 dialog.locator('[data-action="close"]').click();assert av()['posturaEdicoes']['fotoF']['showHandles'] is False
 # The four compact actions include a direct download of the saved composite.
 frontal=page.locator('#obs-av-fotoF').locator('..');assert frontal.locator('.posture-photo-actions button').all_text_contents()==['Câmera','Editar','Apagar','Salvar']
 row=frontal.locator('.posture-photo-actions').bounding_box();buttons=frontal.locator('.posture-photo-actions button').all()
 assert all(abs(button.bounding_box()['y']-row['y'])<2 for button in buttons)
 # Insert the bundled transparent PNG, resize and move it, then retain its placement on reload.
 page.locator('[data-posture-edit="fotoF"]').click();dialog.locator('[data-action="logo"]').click();logo=svg.locator('image[data-logo]');expect(logo).to_have_count(1)
 page.locator('#postureLogoSize').evaluate('(e)=>{e.value="55";e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}));}')
 page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
 oldLogo=logo.bounding_box();stage=dialog.locator('.posture-stage').bounding_box()
 page.mouse.move(oldLogo['x']+oldLogo['width']/2,oldLogo['y']+oldLogo['height']/2);page.mouse.down();page.mouse.move(stage['x']+stage['width']*.508,stage['y']+stage['height']*.505,steps=8)
 expect(page.locator('#postureAlignment')).to_have_text('Centralizado ↔ ↕')
 assert abs(float(logo.get_attribute('x'))+float(logo.get_attribute('width'))/2-300)<.01
 assert abs(float(logo.get_attribute('y'))+float(logo.get_attribute('height'))/2-500)<.01
 page.mouse.up();expect(svg.locator('[data-alignment]')).to_have_count(0)
 dialog.locator('[data-action="undo"]').click();expect(logo).to_have_count(1)
 oldLogo=logo.bounding_box();stage=dialog.locator('.posture-stage').bounding_box()
 page.mouse.move(oldLogo['x']+oldLogo['width']/2,oldLogo['y']+oldLogo['height']/2);page.mouse.down();page.mouse.move(stage['x']+stage['width']*.6,stage['y']+stage['height']*.72,steps=8);page.mouse.up()
 assert float(logo.get_attribute('x'))>100 and float(logo.get_attribute('y'))<800
 dialog.locator('[data-action="zoom-in"]').click();dialog.locator('[data-action="zoom-lock"]').click();dialog.locator('[data-action="save-top"]').click();expect(dialog).not_to_be_visible();without=av()
 placement=without['posturaEdicoes']['fotoF']['logo'];assert placement['src']=='assets/caio-macedo-logo.png' and placement['width']==.55 and .2<placement['x']<.5 and .6<placement['y']<.8
 assert without['fotoFOriginal']==photos['portrait'];assert without['posturaEdicoes']['fotoF']['viewLocked'] is True and without['posturaEdicoes']['fotoF']['lockedView']['zoom']==1.2
 def green_pixels(src):return page.evaluate("""async src=>{const img=new Image();img.src=src;await img.decode();const c=document.createElement('canvas');c.width=img.width;c.height=img.height;const ctx=c.getContext('2d');ctx.drawImage(img,0,0);const d=ctx.getImageData(0,0,c.width,c.height).data;let count=0;for(let i=0;i<d.length;i+=4)if(d[i+1]-d[i]>70&&d[i+1]-d[i+2]>60)count++;return {count,width:img.width,height:img.height};}""",src)
 result=green_pixels(without['fotoF']);assert result['count']>100 and result['width']==600 and result['height']==1000,result
 with page.expect_download() as saved:frontal.get_by_role('button',name='Salvar',exact=True).click()
 assert saved.value.suggested_filename=='Ana_Frontal_01_10_2026.jpg'
 assert Path(saved.value.path()).read_bytes()==base64.b64decode(without['fotoF'].split(',')[1])
 page.reload();open_photos();page.locator('[data-posture-edit="fotoF"]').click();expect(logo).to_have_count(1);expect(page.locator('#postureZoomValue')).to_have_text('120%');expect(dialog.locator('[data-action="zoom-lock"]')).to_have_attribute('aria-pressed','true')
 assert abs(float(logo.get_attribute('x'))-placement['x']*600)<1
 dialog.locator('[data-action="save"]').click();expect(dialog).not_to_be_visible();assert av()['fotoF']==without['fotoF'],'Logo must not be baked again on repeated edits'
 page.locator('[data-posture-edit="fotoF"]').click();dialog.locator('[data-action="remove-logo"]').click();expect(logo).to_have_count(0)
 dialog.locator('[data-action="undo"]').click();expect(logo).to_have_count(1)
 # Remember a replacement PNG independently of the current photo's cancel/save choice.
 page.locator('#postureLogoInput').set_input_files(str(ROOT/'treino36/assets/caio-macedo-logo.png'))
 expect(logo).to_have_attribute('href',__import__('re').compile('data:image/png;base64,'))
 assert page.evaluate("localStorage.getItem('treinoPostureLogo')").startswith('data:image/png;base64,')
 dialog.locator('[data-action="close"]').click();assert av()['posturaEdicoes']['fotoF']['logo']==placement
 # The native camera picker opens within the editor, and cancelling preserves the old photo.
 frontal=page.locator('#obs-av-fotoF').locator('..')
 with page.expect_file_chooser() as chooser:frontal.get_by_role('button',name='Câmera',exact=True).click()
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
  comparison=pdf[-1];text=comparison.get_text();assert 'COMPARATIVO FOTOGRÁFICO' in text and 'ANTES - 01/09/2026' in text and 'ATUAL - 01/10/2026' in text and 'Sem foto' in text,text
  upper=comparison.search_for('ANTES')[0];lower=comparison.search_for('ATUAL')[0];assert upper.y0<lower.y0
  rects=[r for image in comparison.get_images() for r in comparison.get_image_rects(image[0])]
  oldRect=next(r for r in rects if abs(r.width/r.height-1)<.02);frontRect=next(r for r in rects if abs(r.width/r.height-.6)<.02);lateralRect=next(r for r in rects if abs(r.width/r.height-2.5)<.02)
  assert oldRect.y1<lower.y0 and frontRect.y0>lower.y0 and lateralRect.y0>lower.y0
  assert abs((oldRect.x0+oldRect.x1)/2-(frontRect.x0+frontRect.x1)/2)<1 and lateralRect.x0>frontRect.x1
  assert len(comparison.search_for('FRONTAL'))==2 and len(comparison.search_for('LATERAL'))==2
  comparison.get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save('/tmp/posture-comparison-preview.png')
 # Long postural notes continue after the photo rows, with proper footers on every page.
 long_notes='\n'.join('Observação %d: manter o alinhamento durante a avaliação.'%i for i in range(110))
 page.locator('#obs-av-resumo').fill(long_notes)
 with page.expect_download() as long_download:page.locator('#obsAssessment-postural').click()
 with fitz.open(long_download.value.path()) as pdf:
  assert pdf.page_count>2;all_text='\n'.join(p.get_text() for p in pdf);assert 'Observação 109' in all_text and 'CONTINUAÇÃO' in all_text
  assert all('Pág. %d de %d'%(i+1,pdf.page_count) in p.get_text() for i,p in enumerate(pdf))
 page.locator('#obs-av-resumo').fill('')

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
 browser.close();print('PASS: mobile fit, endpoint dragging/angles, free endpoint rotation of horizontal/vertical lines, no numeric rotation toolbar, hidden handles, independent persisted grid color/thickness/transparency, top save, undo/redo, baked optional grid verified by pixels, original retained/re-edit without double overlays, camera/gallery and cancel, actual PDF aspect ratios, dated before/after rows aligned by view with missing-photo placeholders and paginated long analysis, native pinch zoom/reset and guide dragging while zoomed, locked pinch/pan and persisted locked view, full-window expansion, line/logo center snap with transient guides, bundled PNG logo drag/resize/persistence and exported pixels, remembered custom PNG, direct image download and compact four-action row, immediate durable saves and isolation, quota rollback and confirmed deletion inside/outside editor')
