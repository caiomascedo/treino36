"""Protected GIF samples survive editing, copying and moving; only explicit editor removes them."""
import json,os
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];ENGINE=os.getenv('GIF_TEST_BROWSER','chromium')
asset=next(v for v in json.loads((ROOT/'cmfit-catalog.json').read_text())['videos'] if v['name']=='Agachamento no smith')
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if ENGINE=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 c.add_init_script("window.drawn=[];const f=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(t,...a){drawn.push(String(t));return f.call(this,t,...a)}")
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['blob','data']:r.continue_();return
  f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='protected.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://protected.test/');page.evaluate('TreinoStorage.ready');page.evaluate('(url)=>localStorage.setItem("treinoAlunos",JSON.stringify([{student_id:"protected",nome:"Amostra protegida",treino:{A:["Agachamento Smith — 3x8 [Vídeo: "+url+"]"]},titulos:{A:"A. Pernas"}}]))',asset['url']);page.reload()
 link=page.locator('.sec-a ol .exercise-video');expect(link).to_have_text('(GIFs)');expect(link).to_have_attribute('contenteditable','false')
 page.evaluate('(id)=>WorkoutVideoLibrary.remove(id)',asset['id']);link.click();preview=page.locator('#movementPreview');expect(preview).to_be_visible();preview.get_by_role('button').click();page.evaluate('(id)=>WorkoutVideoLibrary.restore(id)',asset['id'])
 # Selecting the whole noneditable sample then Backspace/Paste must not delete it.
 page.evaluate('''()=>{const a=document.querySelector('.sec-a ol .exercise-video'),r=document.createRange();r.selectNode(a);const s=getSelection();s.removeAllRanges();s.addRange(r);a.closest('[contenteditable=true]').focus();}''')
 page.keyboard.press('Backspace');expect(link).to_have_count(1)
 def edit():
  page.locator('.sec-a .main-exercise-grip').first.click();page.locator('#editExerciseBtn').click();expect(page.locator('#exerciseEditDialog')).to_be_visible()
 edit()
 with page.expect_download() as dl:page.locator('#exerciseEditDownload').click()
 out=Path('/tmp/sample-download-'+ENGINE+'.mp4');dl.value.save_as(str(out));assert out.read_bytes()==(ROOT/'cmfit-media'/(asset['id']+'.mp4')).read_bytes();assert dl.value.suggested_filename.endswith('.mp4')
 page.locator('#exerciseEditText').fill('Agachamento No Smith — 4x10');page.locator('#exerciseEditSave').click();expect(link).to_have_count(1);expect(page.locator('.sec-a ol')).to_contain_text('4x10')
 page.reload();expect(link).to_have_count(1);expect(page.locator('.sec-a ol')).to_contain_text('4x10')
 # Cancel a removal: the saved attachment remains untouched.
 edit();page.locator('#exerciseEditRemove').click();page.locator('#exerciseEditDialog').get_by_role('button',name='Cancelar',exact=True).click();expect(link).to_have_count(1)
 # GIF export uses the exercise name/prescription, with no sample label in the image.
 page.locator('#workoutGifsBtn').click();d=page.locator('#workoutGifDialog');d.get_by_role('combobox',name='Biblioteca dos GIFs').select_option('cm');expect(d.locator('[role=status]')).to_contain_text('1/1');d.get_by_role('button',name='Gerar GIF CM',exact=True).click();expect(d.locator('[role=status]')).to_contain_text('GIF pronto',timeout=120000);assert not page.evaluate('drawn.some(t=>/\\(gifs?\\)|\\[v[ií]deo:/i.test(t))');d.get_by_role('button',name='Fechar',exact=True).click()
 edit();page.locator('#exerciseEditRemove').click();page.locator('#exerciseEditSave').click();expect(link).to_have_count(0);page.reload();expect(link).to_have_count(0)
 assert '[Vídeo:' not in page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A[0]')
 # Deleting the entire row is an explicit edit-menu action too.
 edit();page.locator('#exerciseEditDelete').click();expect(page.locator('.sec-a ol')).not_to_contain_text('Agachamento');assert not errors,errors;b.close()
 print('PASS',ENGINE,': protected clickable GIF sample, keyboard deletion blocked, menu rename preserves sample, cancelled removal preserved, explicit removal persists, exported GIF omits sample label, explicit exercise deletion')
