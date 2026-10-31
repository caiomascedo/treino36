"""Actual CM/Gym GIFs, smart default workout, sequential decoder and no-Range media."""
import os,json
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image,ImageChops,ImageStat
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
ENGINE=os.environ.get('GIF_TEST_BROWSER','chromium')
cm=json.loads((ROOT/'cmfit-catalog.json').read_text())['videos']
gym=json.loads((ROOT/'gymfaster-catalog.json').read_text())['videos']
assert {p.stem for p in (ROOT/'cmfit-media').glob('*.mp4')}=={v['id'] for v in cm}
assert {p.stem for p in (ROOT/'gymfaster-media').glob('*.mp4')}=={v['id'] for v in gym}
def inspect(path,rows):
 image=Image.open(path);assert image.n_frames==100,image.n_frames
 assert image.size[0]==800
 duration=0;frames=[]
 for n in range(image.n_frames):
  image.seek(n);duration+=image.info['duration']
  if n in [0,25,50,75]:frames.append(image.convert('RGB').copy())
 assert duration==5000,duration;assert image.info.get('loop')==0
 for row in range(rows):
  region=(410,175+270*row,760,175+270*row+242)
  motion=max(sum(ImageStat.Stat(ImageChops.difference(frames[0].crop(region),f.crop(region))).mean) for f in frames[1:])
  assert motion>0.8,(row,motion)
 return path.stat().st_size
with sync_playwright() as p:
 if ENGINE=='webkit':
  opts={};custom=os.environ.get('PLAYWRIGHT_WEBKIT_EXECUTABLE')
  if custom:opts['executable_path']=custom
  browser=p.webkit.launch(**opts)
 else:browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 ctx=browser.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 ctx.add_init_script("window.shared=[];Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{shared.push({name:data.files[0].name,type:data.files[0].type,size:data.files[0].size});throw new DOMException('Cancel','AbortError');}})")
 fail_media=False;network=[]
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['blob','data']:r.continue_();return
  f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='gif.test' and f.is_file():
   if f.suffix=='.mp4':
    network.append(u.path)
    if fail_media:r.fulfill(status=503);return
   # Deliberately no byte ranges: generation must use complete blobs, including on WebKit.
   r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 ctx.route('**/*',route);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda msg:print(msg.text,flush=True) if msg.type=='warning' else None)
 page.goto('http://gif.test/');page.evaluate('TreinoStorage.ready')
 initial=['Agachamento Smith — 4x 6-8','Leg Press 45 + Ag Sumo — 3x 8+10','Cadeira Extensora — 4x 10','Adutor — 3x 15','Step Up + Ag Frontal — 3x 8+20','Glúteo Na Polia — 3x 8']
 data=[{'student_id':'smart-cm','nome':'Aluno GIF','treino':{'A':initial,'B':['Remada — 3x12']},'titulos':{'A':'A. Pernas','B':'B. Costas'}}]
 page.evaluate('(people)=>localStorage.setItem("treinoAlunos",JSON.stringify(people))',data);page.reload()
 pdf=page.locator('#pdfBtn').bounding_box();c=page.locator('#cmfitWorkoutABtn').bounding_box();g=page.locator('#gymfasterWorkoutABtn').bounding_box();assert abs(pdf['y']-c['y'])<2 and abs(c['y']-g['y'])<2
 page.locator('#cmfitWorkoutABtn').click();dialog=page.locator('#workoutGifDialog');expect(dialog).to_be_visible();expect(dialog).to_have_attribute('data-library','cm');expect(dialog.locator('.gif-card')).to_have_count(8)
 expect(dialog.locator('[role=status]')).to_contain_text('6/8')
 assert not page.locator('#pdfViewerModal').evaluate('e=>e.classList.contains("open")')
 expect(dialog.locator('.gif-card').nth(1)).to_contain_text('3x 8');expect(dialog.locator('.gif-card').nth(2)).to_contain_text('3x 10')
 expect(dialog.get_by_role('button',name='Revisar 2 exercícios',exact=True)).to_be_visible()
 dialog.get_by_role('button',name='Revisar 2 exercícios',exact=True).click();expect(dialog.locator('[role=status]')).to_contain_text('Falta confirmar')
 before=page.evaluate('localStorage.getItem("treinoAlunos")')
 dialog.get_by_role('button',name='Usar sugestões mostradas (2)',exact=True).click();expect(dialog.locator('[role=status]')).to_contain_text('8/8')
 assert page.evaluate('localStorage.getItem("treinoAlunos")')==before,'Choices for compound parts must not overwrite the parent workout line'
 assert dialog.evaluate('e=>e.scrollWidth<=e.clientWidth')
 page.screenshot(path='/tmp/two-gif-'+ENGINE+'-preview.png')
 dialog.get_by_role('button',name='Gerar GIF CM',exact=True).click();expect(dialog.get_by_role('button',name='Cancelar geração',exact=True)).to_be_visible()
 page.wait_for_function("/GIF pronto|Não foi possível|não pôde|demorou demais|não foi reconhecida/.test(document.querySelector('#workoutGifDialog [role=status]').textContent)",timeout=240000)
 expect(dialog.locator('[role=status]')).to_contain_text('GIF pronto',timeout=1000)
 with page.expect_download() as download:dialog.get_by_role('button',name='Baixar GIF',exact=True).click()
 output=Path('/tmp/treino-a-cm-'+ENGINE+'.gif');download.value.save_as(str(output));cm_bytes=inspect(output,8)
 assert '_cm_' in download.value.suggested_filename
 dialog.get_by_role('button',name='Compartilhar GIF').click();page.wait_for_function('shared.length===1');assert page.evaluate('shared[0].type')=='image/gif'
 expect(dialog.locator('[role=status]')).to_contain_text('GIF pronto')
 dialog.get_by_role('button',name='Fechar',exact=True).click();page.locator('#cmfitWorkoutABtn').click();expect(dialog.locator('[role=status]')).to_contain_text('8/8');dialog.get_by_role('button',name='Fechar',exact=True).click()
 # Independent Gym choices, despite the same student's saved CM preferences.
 items=gym if ENGINE=='chromium' else gym
 ids=['1h_RNwLjYKoJtTOAEHgKYgoMd1JBB_NPo','1zuCVsAdSRy7VUtwgtjf1BwK7qa5kKQvL','1J0581Mjqk4_p6XEv5-PW1RZT5miqGXRr','11c8topUm97PrFofkMtbcgceOiyV1R2xr','1LTkLxUPSOchKmQZcLPJlwByuhk2yNhQB','1qE-BHUb2Y1kxLjWakLpxfot3J1MDdxWr']
 if ENGINE=='webkit':ids=ids[2:4]
 sources=[next(v for v in gym if v['id']==id) for id in ids]
 data[0]['treino']['A']=[v['name']+' — 4x9 [Vídeo: '+v['url']+']' for v in sources]
 page.evaluate('(people)=>localStorage.setItem("treinoAlunos",JSON.stringify(people))',data);page.reload();page.locator('#gymfasterWorkoutABtn').click()
 expect(dialog).to_have_attribute('data-library','gymfaster');expect(dialog.locator('[role=status]')).to_contain_text(str(len(ids))+'/'+str(len(ids)))
 before=page.evaluate('localStorage.getItem("treinoAlunos")')
 dialog.get_by_role('button',name='Gerar GIF GymFaster',exact=True).click();expect(dialog.locator('[role=status]')).to_contain_text('GIF pronto',timeout=240000)
 with page.expect_download() as dl:dialog.get_by_role('button',name='Baixar GIF',exact=True).click()
 path=Path('/tmp/treino-a-gym-'+ENGINE+'.gif');dl.value.save_as(str(path));gym_bytes=inspect(path,len(ids));assert '_gymfaster_' in dl.value.suggested_filename
 assert page.evaluate('localStorage.getItem("treinoAlunos")')==before
 page.evaluate("Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>false})")
 with page.expect_download() as fallback:dialog.get_by_role('button',name='Compartilhar GIF').click()
 assert fallback.value.suggested_filename==dl.value.suggested_filename
 # Cancellation must release the decoder and allow another generation.
 dialog.get_by_role('button',name='Gerar GIF GymFaster',exact=True).click();dialog.get_by_role('button',name='Cancelar geração',exact=True).click();expect(dialog.get_by_role('button',name='Gerar GIF GymFaster',exact=True)).to_be_enabled(timeout=10000)
 fail_media=True
 dialog.get_by_role('button',name='Gerar GIF GymFaster',exact=True).click();expect(dialog.locator('[role=status]')).to_contain_text('Não foi possível carregar',timeout=20000);expect(dialog.get_by_role('button',name='Gerar GIF GymFaster',exact=True)).to_be_enabled()
 expect(dialog.get_by_role('button',name='Baixar GIF',exact=True)).not_to_be_visible()
 fail_media=False
 dialog.get_by_role('combobox',name='Treino para o GIF').select_option('B');expect(dialog.get_by_role('button',name='Revisar 1 exercício',exact=True)).to_be_visible()
 # A file supplied by the user allows an exercise outside both libraries without changing saved links.
 local=next(v for v in cm if v['name']=='Cadeira extensora');dialog.locator('input[type=file]').set_input_files(str(ROOT/'cmfit-media'/(local['id']+'.mp4')))
 expect(dialog.locator('.gif-card small').last).to_contain_text('Arquivo local')
 before=page.evaluate('localStorage.getItem("treinoAlunos")');dialog.get_by_role('button',name='Gerar GIF GymFaster',exact=True).click();expect(dialog.locator('[role=status]')).to_contain_text('GIF pronto',timeout=120000);assert page.evaluate('localStorage.getItem("treinoAlunos")')==before
 dialog.get_by_role('button',name='Fechar',exact=True).click()
 assert not errors,errors
 browser.close();print('PASS',ENGINE,': both independent libraries, smart default A and bi-sets, real 100-frame 5-second moving CM/Gym GIFs, sharing/download, cancellation, local video, no Range support, original workout preserved; bytes',cm_bytes,gym_bytes)
