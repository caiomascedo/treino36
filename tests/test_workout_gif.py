"""Export the actual student's workout as one animated, shareable GIF, without opening PDF."""
import json
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT/'gymfaster-catalog.json').read_text())['videos']
assert {p.stem for p in (ROOT/'gymfaster-media').glob('*.mp4')}=={v['id'] for v in catalog}, 'Every catalog choice needs an embeddable media file'
ids=['1h_RNwLjYKoJtTOAEHgKYgoMd1JBB_NPo','1zuCVsAdSRy7VUtwgtjf1BwK7qa5kKQvL','1J0581Mjqk4_p6XEv5-PW1RZT5miqGXRr','11c8topUm97PrFofkMtbcgceOiyV1R2xr','1LTkLxUPSOchKmQZcLPJlwByuhk2yNhQB','1qE-BHUb2Y1kxLjWakLpxfot3J1MDdxWr']
videos=[next(v for v in catalog if v['id']==id) for id in ids]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 ctx=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 ctx.add_init_script("window.shared=[];Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{shared.push({name:data.files[0].name,type:data.files[0].type,size:data.files[0].size});throw new DOMException('Cancelled','AbortError');}})")
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='gif.test' and u.path.endswith('.mp4'):
   media=(R if 'R' in globals() else ROOT)/u.path.lstrip('/');data=media.read_bytes();length=len(data)
   requested=r.request.headers.get('range','');start,end=0,length-1
   if requested:
    parts=requested.replace('bytes=','').split('-');start=int(parts[0] or 0);end=min(int(parts[1]) if parts[1] else length-1,length-1)
   r.fulfill(status=206 if requested else 200,body=data[start:end+1],headers={'Accept-Ranges':'bytes','Content-Range':f'bytes {start}-{end}/{length}','Content-Length':str(end-start+1),'Content-Type':'video/mp4'});return
  if u.hostname=='gif.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 ctx.route('**/*',route);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://gif.test/');page.evaluate('TreinoStorage.ready')
 data=[{'student_id':'gif-one','nome':'Aluno GIF','treino':{'A':[v['name']+' — 4×9 · descanso 75 s [Vídeo: '+v['url']+']' for v in videos],'B':['Remada — 3×12']},'titulos':{'A':'A. Treino real de pernas','B':'B. Costas'}}]
 data[0]['treino']['A'][0]=data[0]['treino']['A'][0].replace('?usp=drivesdk','')
 page.evaluate('(people)=>localStorage.setItem("treinoAlunos",JSON.stringify(people))',data);page.reload()
 page.locator('#gymfasterWorkoutABtn').click();dialog=page.locator('#workoutGifDialog');expect(dialog).to_be_visible();expect(dialog.locator('.gif-card')).to_have_count(6)
 assert not page.locator('#pdfViewerModal').evaluate('e=>e.classList.contains("open")')
 expect(dialog.locator('.gif-card').first).to_contain_text('4×9')
 before=page.evaluate('localStorage.getItem("treinoAlunos")')
 page.wait_for_function("[...document.querySelectorAll('#workoutGifDialog video')].every(v=>v.readyState>=2)")
 assert dialog.evaluate('e=>e.scrollWidth<=e.clientWidth')
 page.screenshot(path='/tmp/gif-workout-preview.png')
 dialog.get_by_role('button',name='Gerar GIF animado',exact=True).click()
 expect(dialog.get_by_role('button',name='Cancelar geração')).to_be_visible()
 expect(dialog.locator('[role=status]')).to_contain_text('GIF pronto',timeout=180000)
 assert page.evaluate('localStorage.getItem("treinoAlunos")')==before
 page.screenshot(path='/tmp/gif-workout-ready.png')
 dialog.get_by_role('button',name='Compartilhar GIF').click();page.wait_for_function('shared.length===1')
 assert page.evaluate('shared[0].type')=='image/gif';assert page.evaluate('shared[0].name').startswith('treino_A_')
 expect(dialog.locator('[role=status]')).to_contain_text('GIF pronto')
 with page.expect_download() as dl:dialog.get_by_role('button',name='Baixar GIF',exact=True).click()
 output=Path('/tmp/treino-a-gymfaster-browser.gif');dl.value.save_as(str(output))
 image=Image.open(output);assert image.n_frames==100,image.n_frames;assert image.size==(800,1845),image.size
 total=0;frames=[]
 for i in range(image.n_frames):
  image.seek(i);total+=image.info.get('duration',0)
  if i in [0,25,50,75]:frames.append(image.convert('RGB').copy())
 assert total==5000,total;assert image.info.get('loop')==0
 for row in range(6):
  region=(410,175+270*row,760,175+270*row+250)
  motion=max(sum(ImageStat.Stat(ImageChops.difference(frames[0].crop(region),f.crop(region))).mean) for f in frames[1:])
  assert motion>1,(row,motion)
 page.evaluate("Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>false})")
 with page.expect_download() as fallback:dialog.get_by_role('button',name='Compartilhar GIF').click()
 assert fallback.value.suggested_filename==dl.value.suggested_filename
 expect(dialog.locator('[role=status]')).to_contain_text('Baixe o GIF')
 # A section with an unmatched exercise cannot silently export another variant.
 dialog.get_by_role('combobox',name='Treino para o GIF').select_option('B');expect(dialog.locator('.gif-card')).to_have_count(1)
 dialog.get_by_role('button',name='Gerar GIF animado',exact=True).click();expect(dialog.locator('[role=status]')).to_contain_text('Escolha um vídeo para cada exercício')
 expect(dialog.get_by_role('button',name='Baixar GIF',exact=True)).not_to_be_visible()
 dialog.get_by_role('combobox',name='Treino para o GIF').select_option('A')
 dialog.get_by_role('button',name='Gerar GIF animado',exact=True).click();dialog.get_by_role('button',name='Cancelar geração',exact=True).click()
 expect(dialog.get_by_role('button',name='Gerar GIF animado',exact=True)).to_be_enabled(timeout=25000)
 dialog.locator('.gif-card').first.get_by_role('button',name='Escolher vídeo GymFaster',exact=True).click()
 picker=page.locator('#gymfasterLibrary');expect(picker).to_be_visible();expect(picker).to_contain_text('ficha em GIF')
 picker.get_by_role('searchbox').fill('Agachamento Clássico com Barra')
 expect(picker.locator('.gym-result')).to_have_count(1)
 picker.get_by_role('button',name='Ver movimento',exact=True).click()
 expect(picker.locator('video')).to_have_attribute('src','gymfaster-media/'+ids[0]+'.mp4')
 expect(picker.locator('iframe')).to_have_count(0)
 picker.get_by_role('button',name='Usar este vídeo',exact=True).click()
 expect(picker).not_to_be_visible();expect(dialog).to_be_visible()
 saved=page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))')
 assert videos[0]['url'] in saved[0]['treino']['A'][0]
 assert saved[0]['treino']['B']==json.loads(before)[0]['treino']['B']
 dialog.get_by_role('combobox',name='Treino para o GIF').select_option('B')
 current=page.evaluate('localStorage.getItem("treinoAlunos")')
 dialog.locator('input[type=file]').set_input_files(str(ROOT/'gymfaster-media'/(ids[0]+'.mp4')))
 expect(dialog.locator('.gif-card small')).to_contain_text('Arquivo local')
 dialog.get_by_role('button',name='Gerar GIF animado',exact=True).click()
 expect(dialog.locator('[role=status]')).to_contain_text('GIF pronto',timeout=90000)
 with page.expect_download() as local:dialog.get_by_role('button',name='Baixar GIF',exact=True).click()
 assert local.value.suggested_filename.startswith('treino_B_')
 assert Path(local.value.path()).read_bytes().startswith(b'GIF89a')
 assert page.evaluate('localStorage.getItem("treinoAlunos")')==current
 dialog.get_by_role('button',name='Fechar',exact=True).click()
 assert not errors,errors
 b.close()
 print('PASS: actual workout, six independent motions, 100 frames / 5 s, loop, image/gif download/share, missing variants blocked, cancellation and unchanged saved training data; bytes',output.stat().st_size)
