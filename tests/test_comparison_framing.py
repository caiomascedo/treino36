"""The crop preview and exported poster fill frames without changing proportions."""
import io,base64
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='framing.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();page.goto('http://framing.test/');page.evaluate('TreinoStorage.ready')
 source=page.evaluate('''()=>{const c=document.createElement('canvas');c.width=1200;c.height=1600;const ctx=c.getContext('2d');ctx.fillStyle='#ff0000';ctx.fillRect(0,0,400,1600);ctx.fillStyle='#0000ff';ctx.fillRect(400,0,400,1600);ctx.fillStyle='#00ff00';ctx.fillRect(800,0,400,1600);const src=c.toDataURL('image/jpeg',.95);localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'one',nome:'Exemplo',avaliacaoId:10,treino:{A:[]}}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Exemplo',treinoStudentIds:['one'],avaliacoes:[{id:11,data:'20/10/2026',peso:'60',fotoF:src,fotoL:src,comparativoFoto:{fit:'contain',format:'story',logo:false,weights:false}}]}]));return src;}''')
 page.reload();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('[data-assessment-section=fotos]').click();page.locator('#obsExtraPhotos > summary').click();page.locator('#extraPhotoCompare').click()
 expect(page.locator('#comparisonFit')).to_have_value('cover');expect(page.locator('#comparisonFormat')).to_have_value('story')
 def generate():
  page.locator('#comparisonGenerate').click();expect(page.locator('#comparisonPreview')).to_be_visible()
  with page.expect_download() as result:page.locator('#comparisonDownload').click()
  return Image.open(io.BytesIO(Path(result.value.path()).read_bytes())).convert('RGB')
 centered=generate();assert centered.size==(1080,1920)
 assert centered.getpixel((285,300))[2]>240 # top of photo is filled, no letterboxing
 assert centered.getpixel((285,915))[2]>240
 frame=page.locator('#comparisonBeforeFrame');frame.scroll_into_view_if_needed();bounds=frame.bounding_box();x=bounds['x']+bounds['width']/2;y=bounds['y']+bounds['height']/2
 page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+120,y,steps=6);page.mouse.up();expect(page.locator('#comparisonPreview')).not_to_be_visible()
 moved=generate();assert moved.getpixel((285,915))[0]>240 and moved.getpixel((285,915))[2]<10
 assert moved.getpixel((795,915))[2]>240 # moving Before never changes After
 saved=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].comparativoFoto")
 assert saved['beforeCrop']['x']>0 and saved['afterCrop']['x']==0 and saved['framingVersion']==1
 # A real two-finger gesture changes only the active frame, keeping a single scale factor.
 frame.scroll_into_view_if_needed();bounds=frame.bounding_box();x=bounds['x']+bounds['width']/2;y=bounds['y']+bounds['height']/2
 cdp=context.new_cdp_session(page)
 def touch(kind,points):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[{'x':px,'y':py,'id':i,'radiusX':1,'radiusY':1} for i,(px,py) in enumerate(points)]})
 touch('touchStart',[(x-15,y),(x+15,y)]);touch('touchMove',[(x-35,y),(x+35,y)]);touch('touchEnd',[])
 expect(page.locator('#comparisonBeforeZoom')).not_to_have_text('100%');expect(page.locator('#comparisonAfterZoom')).to_have_text('100%')
 ratio=page.locator('#comparisonBeforeImage').evaluate('image=>({drawn:parseFloat(image.style.width)/parseFloat(image.style.height),source:image.naturalWidth/image.naturalHeight})')
 assert abs(ratio['drawn']-ratio['source'])<.00001,ratio
 generate();page.locator('#assessmentComparisonDialog [data-close]').click();page.locator('#extraPhotoCompare').click();expect(page.locator('#comparisonBeforeZoom')).not_to_have_text('100%')
 page.get_by_role('button',name='Restaurar enquadramento Antes',exact=True).click();expect(page.locator('#comparisonBeforeZoom')).to_have_text('100%')
 page.locator('#comparisonSuggest').click();expect(page.locator('#comparisonFormat')).to_have_value('feed');expect(page.locator('#comparisonStatus')).to_contain_text('menos corte')
 feed=generate();assert feed.size==(1080,1350)
 # Explicit Foto inteira remains available and is retained after regeneration.
 page.locator('#comparisonFit').select_option('contain');generate();page.locator('#assessmentComparisonDialog [data-close]').click();page.locator('#extraPhotoCompare').click();expect(page.locator('#comparisonFit')).to_have_value('contain')
 assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].fotoF")==source
 page.screenshot(path='/tmp/comparison-framing-mobile.png')
 browser.close();print('PASS: no letterboxing in cover export, uniform image scale, independent drag/pinch, saved framing, reset, format suggestion and original preservation')
