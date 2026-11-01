"""Separate YouTube/sample links, editable text, per-part mobility and visibility/PDF layout."""
import os,json
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];ENGINE=os.getenv('GIF_TEST_BROWSER','chromium')
cm=json.loads((ROOT/'cmfit-catalog.json').read_text())['videos'];gym=json.loads((ROOT/'gymfaster-catalog.json').read_text())['videos']
smith=next(v for v in cm if v['name']=='Agachamento no smith');sumo=next(v for v in cm if v['name']=='Agachamento sumo com halter');cat=next(v for v in cm if 'gato' in v['name']);shoulder=next(v for v in gym if v['name']=='Alongamento e Mobilidade de Ombros Sentado' and v['gender']=='Masculino')
YT='https://www.youtube.com/watch?v=AbC123_XyZ&start=30'
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if ENGINE=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 c.add_init_script("window.copied=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async t=>copied.push(t),readText:async()=>copied.at(-1)||''}});window.drawn=[];const f=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(t,...a){drawn.push(String(t));return f.call(this,t,...a)}")
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['blob','data']:r.continue_();return
  f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='separate.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://separate.test/');page.evaluate('TreinoStorage.ready')
 compound='Agachamento Smith + Ag Sumo — 3x8+10 [Vídeo: '+YT+'] [GIFs: '+smith['url']+' | '+sumo['url']+']'
 people=[{'student_id':'split','nome':'Teste vínculos separados','treino':{'A':['Agachamento Smith — 3x8 [Vídeo: '+YT+'] [GIFs: '+smith['url']+']',compound],'B':['Exercício pessoal — 3x10']},'titulos':{'A':'A. Pernas','B':'B. Outro'}}]
 page.evaluate('(d)=>localStorage.setItem("treinoAlunos",JSON.stringify(d))',people);page.evaluate('(d)=>localStorage.setItem("treinoMobilidades",JSON.stringify(d))',[{'id':'mob-split','nome':'Mobilidade conjugada','texto':'Mobilidade gato e vaca + Alongamento e Mobilidade de Ombros Sentado — 2x10 [Vídeo: '+YT+'] [GIFs: '+cat['url']+' | -]'}]);page.reload()
 assert not errors,errors;expect(page.locator('.main-exercise-eye,.mobility-eye')).to_have_count(0)
 first=page.locator('.sec-a ol li').first;expect(first.locator('.exercise-video')).to_have_text('(Vídeo)');assert first.locator('.exercise-video').get_attribute('href')==YT;expect(first.locator('.gif-sample')).to_have_count(1)
 assert first.locator('.exercise-gifs').bounding_box()['y']>first.locator('.exercise-video').bounding_box()['y'];first.locator('.gif-sample').click();preview=page.locator('#movementPreview');expect(preview).to_be_visible();preview.get_by_role('button').click()
 # Caret next to the attachment remains editable.
 first.locator('.bold').evaluate('e=>{const r=document.createRange();r.setStart(e.firstChild,e.firstChild.length);r.collapse(true);getSelection().removeAllRanges();getSelection().addRange(r);e.closest("[contenteditable=true]").focus()}');page.keyboard.insert_text(' teste');expect(first.locator('.bold')).to_contain_text('teste');expect(first.locator('.gif-sample')).to_have_count(1)
 # Exercise edit keeps both channels. Move/duplicate/copy keep both portable URLs.
 page.locator('.sec-a .main-exercise-grip').first.click();page.locator('#editExerciseBtn').click();ed=page.locator('#exerciseEditDialog');expect(ed.locator('#exerciseEditYoutube')).to_have_value(YT);expect(ed.locator('.sample-edit-row')).to_have_count(1)
 with page.expect_download() as clip_download:ed.get_by_role('button',name='Baixar vídeo',exact=True).click()
 video_file=Path('/tmp/separate-download-'+ENGINE+'.mp4');clip_download.value.save_as(str(video_file));assert video_file.read_bytes()==(ROOT/'cmfit-media'/(smith['id']+'.mp4')).read_bytes()
 ed.locator('#exerciseEditText').fill('Agachamento Smith — 3x8');ed.locator('#exerciseEditSave').click()
 page.locator('.sec-a .main-exercise-grip').first.click();page.locator('#copyExerciseBtn').click();page.wait_for_function('copied.length>0');clip=page.evaluate('copied.at(-1)');assert '[Vídeo: '+YT+']' in clip and '[GIFs:' in clip;page.locator('#duplicateExerciseBtn').click();expect(page.locator('.sec-a ol li')).to_have_count(3)
 page.locator('.sec-a .main-exercise-grip').first.click();page.get_by_role('button',name='Mover para seção B',exact=True).click();moved=page.locator('.sec-b ol li').last;expect(moved.locator('.exercise-video')).to_have_count(1);expect(moved.locator('.gif-sample')).to_have_count(1);page.reload();expect(page.locator('.sec-b ol li').last.locator('.gif-sample')).to_have_count(1)
 # Global mode resets section overrides. A section override affects only that section.
 def visibility(scope,mode):
  menu=page.locator('[data-media-menu="'+scope+'"]');menu.locator('summary').click();menu.locator('[data-mode="'+mode+'"]').click()
 visibility('all','gifs');expect(page.locator('.sec-a .exercise-video').first).not_to_be_visible();expect(page.locator('.sec-a .gif-sample').first).to_be_visible();visibility('A','video');expect(page.locator('.sec-a .exercise-video').first).to_be_visible();expect(page.locator('.sec-a .gif-sample').first).not_to_be_visible();expect(page.locator('.sec-b .gif-sample').first).to_be_visible();page.reload();expect(page.locator('.sec-a .gif-sample').first).not_to_be_visible();visibility('all','none');expect(page.locator('.sec-b .gif-sample').first).not_to_be_visible();visibility('all','both')
 a=page.locator('.sec-a .section-zoom-btn').bounding_box();v=page.locator('.sec-a [data-media-menu=A]').bounding_box();page.screenshot(path='/tmp/separate-controls-'+ENGINE+'.png');assert abs(a['y']-v['y'])<5 and a['x']<v['x'],(a,v);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 # PDF links have their own right column; samples do not alter the prescription.
 page.locator('#pdfBtn').click();pdf=page.locator('#pdfBody');page.get_by_role('checkbox',name='Incluir GIFs cadastrados no PDF',exact=True).check();expect(pdf.locator('.pdf-gif-link')).to_have_count(4);positions=pdf.locator('.yt-link').evaluate_all('els=>els.map(e=>({right:e.getBoundingClientRect().right,y:e.getBoundingClientRect().y,nameY:e.closest(".pdf-ex-row").querySelector(".pdf-ex-title").getBoundingClientRect().y}))');assert max(x['right'] for x in positions)-min(x['right'] for x in positions)<2;assert all(abs(x['y']-x['nameY'])<3 for x in positions),positions
 page.locator('#closePdfViewer').click();visibility('all','none');page.locator('#pdfBtn').click();expect(page.locator('#pdfBody .yt-link')).to_have_count(0);assert page.locator('#pdfBody .pdf-gif-link:visible').count()==0;page.locator('#closePdfViewer').click();visibility('all','both')
 # Each part of a conjugated mobility can receive its own sample, preserving YouTube.
 page.locator('#moreOptions>summary').click();page.locator('#mobilityLibraryBtn').click();mob=page.locator('#mobilityDialog');mob.locator('.mobility-video-row>button').filter(has_text='Mobilidade conjugada').click();mob.locator('#mobilityRegistration>summary').click();expect(mob.locator('.sample-edit-row')).to_have_count(2);mob.locator('.sample-edit-row').nth(1).get_by_role('button',name='Escolher GIF',exact=True).click();picker=page.locator('.gif-video-picker');picker.locator('[data-video-id="'+shoulder['id']+'"]').click();preview.get_by_role('button').click();raw=mob.locator('#mobilityText').input_value();assert YT in raw and shoulder['url'] in raw and cat['url'] in raw;mob.get_by_role('button',name='Salvar na biblioteca',exact=True).click();expect(mob.locator('.mobility-video-row').first.locator('.gif-sample')).to_have_count(2);mob.get_by_role('button',name='Fechar',exact=True).click()
 saved=json.loads(page.evaluate('localStorage.getItem("treinoMobilidades")'));assert shoulder['url'] in next(m['texto'] for m in saved if m['id']=='mob-split')
 # Real compound export follows each sample without including decorative labels or replacing YouTube.
 people[0]['treino']={'A':[compound]};page.evaluate('(d)=>localStorage.setItem("treinoAlunos",JSON.stringify(d))',people);page.reload();page.locator('#workoutGifsBtn').click();d=page.locator('#workoutGifDialog');d.get_by_role('combobox',name='Biblioteca dos GIFs').select_option('cm');expect(d.locator('[role=status]')).to_contain_text('2/2');d.get_by_role('button',name='Gerar GIF CM',exact=True).click();expect(d.locator('[role=status]')).to_contain_text('GIF pronto',timeout=180000)
 with page.expect_download() as dl:d.get_by_role('button',name='Baixar GIF',exact=True).click()
 out=Path('/tmp/separate-'+ENGINE+'.gif');dl.value.save_as(str(out));assert Image.open(out).n_frames==100;assert not page.evaluate('drawn.some(t=>/\\(gifs?\\)|\\[gifs?:|\\[v[ií]deo:/i.test(t))');assert YT in json.loads(page.evaluate('localStorage.getItem("treinoAlunos")'))[0]['treino']['A'][0];assert not errors,errors;b.close()
 print('PASS',ENGINE,': no eyes; editable text; separate YouTube/GIF links survive copy/duplicate/move/reload; global/section visibility and aligned PDF; per-part mobility saves both samples; real 5-second compound export omits link labels')
