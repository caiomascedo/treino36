"""Mixed CM/Gym demonstration backgrounds follow the selected output theme."""
import os,json
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];ENGINE=os.getenv('GIF_TEST_BROWSER','chromium')
cm=next(v for v in json.loads((ROOT/'cmfit-catalog.json').read_text())['videos'] if v['name']=='Agachamento no smith')
gym=next(v for v in json.loads((ROOT/'gymfaster-catalog.json').read_text())['videos'] if v['name']=='Cadeira Extensora' and v['gender']=='Masculino')
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if ENGINE=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['blob','data']:r.continue_();return
  f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='colors.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://colors.test/');page.evaluate('TreinoStorage.ready');page.evaluate('(d)=>localStorage.setItem("treinoAlunos",JSON.stringify(d))',[{'student_id':'mixed-color','nome':'Teste cores','treino':{'A':['Agachamento Smith — 3x8 [Vídeo: '+cm['url']+']','Cadeira Extensora — 3x10 [Vídeo: '+gym['url']+']']},'titulos':{'A':'A. Pernas'}}]);page.reload();page.locator('#workoutGifsBtn').click();d=page.locator('#workoutGifDialog');d.get_by_role('combobox',name='Biblioteca dos GIFs').select_option('cm')
 def choose(index,source,id):
  d.locator('.gif-card').nth(index).get_by_role('button',name='Escolher outro vídeo',exact=True).click();picker=page.locator('.gif-video-picker');picker.get_by_role('combobox',name='Biblioteca da demonstração').select_option(source);picker.locator('[data-video-id="'+id+'"]').click()
 choose(1,'gymfaster',gym['id']);expect(d.locator('video.gym-ink-on-black')).to_have_count(1);expect(d.locator('video.cm-ink-on-white')).to_have_count(0)
 assert d.locator('video.gym-ink-on-black').evaluate("v=>getComputedStyle(v).filter.includes('invert(1)')")
 d.get_by_role('button',name='Gerar GIF CM',exact=True).click();expect(d.locator('[role=status]')).to_contain_text('GIF pronto',timeout=180000)
 with page.expect_download() as dl:d.get_by_role('button',name='Baixar GIF',exact=True).click()
 out=Path('/tmp/mixed-dark-'+ENGINE+'.gif');dl.value.save_as(str(out));im=Image.open(out);assert im.n_frames==100
 slots=d.locator('.gif-card').evaluate_all('items=>items.map(i=>JSON.parse(i.dataset.gifSlot))')
 for frame in [0,25,50,75]:
  im.seek(frame);rgb=im.convert('RGB')
  for slot in slots:
   pixels=list(rgb.crop((slot['x'],slot['y'],slot['x']+slot['width'],slot['y']+slot['height'])).get_flattened_data());assert sum(max(pixel)<40 for pixel in pixels)>len(pixels)*.55
 d.get_by_role('combobox',name='Biblioteca dos GIFs').select_option('gymfaster');choose(0,'cm',cm['id']);expect(d.locator('video.cm-ink-on-white')).to_have_count(1);expect(d.locator('video.gym-ink-on-black')).to_have_count(0);assert not errors,errors;b.close()
 print('PASS',ENGINE,': mixed CM/Gym footage has black backgrounds in dark preview/export, real 100-frame GIF; source inversion updates for light theme')
