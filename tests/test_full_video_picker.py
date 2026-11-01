"""Every catalog item is reachable, including >80; new male clips generate real GIFs."""
import json,os
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image,ImageChops,ImageStat
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];ENGINE=os.environ.get('GIF_TEST_BROWSER','chromium')
catalog=json.loads((ROOT/'gymfaster-catalog.json').read_text());videos=catalog['videos'];assert len(videos)==671
assert sum(v.get('kind')!='created-example' for v in videos)==670
male=next(v for v in videos if v['name']=='Cadeira Extensora' and v['gender']=='Masculino')
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if ENGINE=='webkit' and os.environ.get('PLAYWRIGHT_WEBKIT_EXECUTABLE') else p.webkit.launch() if ENGINE=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 ctx=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['blob','data']:r.continue_();return
  f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='full.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 ctx.route('**/*',route);page=ctx.new_page();page.goto('http://full.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate('''()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'full-library',nome:'Teste biblioteca',treino:{A:['Cadeira Extensora — 3x12']},titulos:{A:'A. Pernas'}}]))''');page.reload();page.locator('#workoutGifsBtn').click()
 main=page.locator('#workoutGifDialog');expect(main.locator('.gif-card')).to_have_count(1);main.get_by_role('button',name='Escolher outro vídeo',exact=True).click();picker=page.locator('.gif-video-picker')
 picker.get_by_role('button',name='Ver todos os vídeos',exact=True).click();expect(picker.locator('.gif-picker-results button')).to_have_count(671)
 actual=set(picker.locator('.gif-picker-results button').evaluate_all('items=>items.map(i=>i.dataset.videoId)'));assert actual=={v['id'] for v in videos}
 expect(picker.locator('.gif-picker-count')).to_contain_text('671 resultados')
 picker.get_by_role('combobox',name='Versão da demonstração').select_option('Masculino');assert picker.locator('.gif-picker-results button').count()==sum(v['gender']=='Masculino' for v in videos)
 picker.get_by_role('combobox',name='Grupo muscular da demonstração').select_option('Glúteos e Quadril');assert picker.locator('.gif-picker-results button').count()==sum(v['gender']=='Masculino' and v['group']=='Glúteos e Quadril' for v in videos)
 picker.get_by_role('searchbox',name='Buscar demonstração').fill('extensora');expect(picker.locator('.gif-picker-results button')).to_have_count(1)
 picker.locator('[data-video-id="'+male['id']+'"]').click();expect(picker).not_to_be_visible();expect(main.locator('.gif-card small').last).to_contain_text('Masculino')
 main.get_by_role('button',name='Gerar GIF GymFaster',exact=True).click();page.wait_for_function("/GIF pronto|Não foi possível|não pôde|demorou demais/.test(document.querySelector('#workoutGifDialog [role=status]').textContent)",timeout=120000);expect(main.locator('[role=status]')).to_contain_text('GIF pronto')
 with page.expect_download() as download:main.get_by_role('button',name='Baixar GIF',exact=True).click()
 out=Path('/tmp/new-male-library-'+ENGINE+'.gif');download.value.save_as(str(out));im=Image.open(out);assert im.n_frames==100;duration=0;frames=[]
 for n in range(im.n_frames):
  im.seek(n);duration+=im.info['duration']
  if n in [0,25,50,75]:frames.append(im.convert('RGB').copy())
 assert duration==5000;assert max(sum(ImageStat.Stat(ImageChops.difference(frames[0],f)).mean) for f in frames[1:])>0.8
 main.get_by_role('button',name='Escolher outro vídeo',exact=True).click();picker.get_by_role('combobox',name='Biblioteca da demonstração').select_option('cm');picker.get_by_role('button',name='Ver todos os vídeos',exact=True).click();expect(picker.locator('.gif-picker-results button')).to_have_count(321)
 assert picker.evaluate('e=>e.scrollWidth<=e.clientWidth');b.close()
print('PASS',ENGINE,': every one of 671 Gym/example and 321 CM items reachable, no 80-item cutoff, group/version filters, newly added male clip exported as moving 5-second GIF')
