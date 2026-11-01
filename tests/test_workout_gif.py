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
 slots=rows if isinstance(rows,list) else [{'x':410,'y':175+270*row,'width':350,'height':242} for row in range(rows)]
 for row,slot in enumerate(slots):
  region=(slot['x'],slot['y'],slot['x']+slot['width'],slot['y']+slot['height'])
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
 ctx.add_init_script("window.gifDrawnText=[];const oldFill=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(text,...args){gifDrawnText.push(String(text));return oldFill.call(this,text,...args)};window.shared=[];Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});Object.defineProperty(navigator,'share',{configurable:true,value:async data=>{shared.push({name:data.files[0].name,type:data.files[0].type,size:data.files[0].size});throw new DOMException('Cancel','AbortError');}})")
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
 boxes=[page.locator(selector).bounding_box() for selector in ['#pdfBtn','#workoutGifsBtn','#screenshotBtn','#moreOptions']];assert max(box['y'] for box in boxes)-min(box['y'] for box in boxes)<2
 page.locator('#workoutGifsBtn').click();dialog=page.locator('#workoutGifDialog');dialog.get_by_role('combobox',name='Biblioteca dos GIFs').select_option('cm');expect(dialog).to_be_visible();expect(dialog).to_have_attribute('data-library','cm');expect(dialog.locator('.gif-card')).to_have_count(8)
 expect(dialog.locator('[role=status]')).to_contain_text('6/8')
 assert not page.locator('#pdfViewerModal').evaluate('e=>e.classList.contains("open")')
 expect(dialog.locator('.gif-card').nth(1)).to_contain_text('3x 8');expect(dialog.locator('.gif-card').nth(2)).to_contain_text('3x 10')
 expect(dialog.get_by_role('button',name='Revisar 2 exercícios',exact=True)).to_be_visible()
 dialog.get_by_role('button',name='Revisar 2 exercícios',exact=True).click();expect(dialog.locator('[role=status]')).to_contain_text('Falta confirmar')
 before=page.evaluate('localStorage.getItem("treinoAlunos")')
 dialog.get_by_role('button',name='Usar sugestões mostradas (2)',exact=True).click();expect(dialog.locator('[role=status]')).to_contain_text('8/8')
 assert page.evaluate('localStorage.getItem("treinoAlunos")')==before,'Choices for compound parts must not overwrite the parent workout line'
 expect(dialog.locator('.gif-card video.cm-ink-on-white')).to_have_count(0)
 assert dialog.locator('.gif-card video').first.evaluate("v=>getComputedStyle(v).filter==='none'")
 page.wait_for_function("document.querySelector('#workoutGifDialog .gif-card video').readyState>=2")
 assert dialog.evaluate('e=>e.scrollWidth<=e.clientWidth')
 expect(dialog.locator('.gif-compound')).to_have_count(2)
 for pair in dialog.locator('.gif-compound-grid').all():
  boxes=pair.locator('video').evaluate_all('items=>items.map(i=>({x:i.getBoundingClientRect().x,y:i.getBoundingClientRect().y}))')
  assert len(boxes)==2 and boxes[0]['x']<boxes[1]['x'] and abs(boxes[0]['y']-boxes[1]['y'])<2,boxes
  texts=pair.locator('.gif-card-text').evaluate_all('items=>items.map(i=>i.getBoundingClientRect().y)')
  assert texts[0]<texts[1],texts
 page.screenshot(path='/tmp/two-gif-'+ENGINE+'-preview.png')
 dialog.get_by_role('button',name='Gerar GIF CM',exact=True).click();expect(dialog.get_by_role('button',name='Cancelar geração',exact=True)).to_be_visible()
 page.wait_for_function("/GIF pronto|Não foi possível|não pôde|demorou demais|não foi reconhecida/.test(document.querySelector('#workoutGifDialog [role=status]').textContent)",timeout=240000)
 expect(dialog.locator('[role=status]')).to_contain_text('GIF pronto',timeout=1000)
 with page.expect_download() as download:dialog.get_by_role('button',name='Baixar GIF',exact=True).click()
 output=Path('/tmp/treino-a-cm-'+ENGINE+'.gif');download.value.save_as(str(output));cm_slots=dialog.locator('.gif-card').evaluate_all('items=>items.map(i=>JSON.parse(i.dataset.gifSlot))');cm_bytes=inspect(output,cm_slots)
 assert cm_slots[1]['y']==cm_slots[2]['y'] and cm_slots[1]['x']<cm_slots[2]['x']
 assert cm_slots[5]['y']==cm_slots[6]['y'] and cm_slots[5]['x']<cm_slots[6]['x']
 assert cm_slots[0]['y']<cm_slots[1]['y']<cm_slots[3]['y']
 assert Image.open(output).height<2385
 assert not page.evaluate("gifDrawnText.some(text=>text.startsWith('Demonstrações')||text.includes('—'))")
 assert '_cm_' in download.value.suggested_filename
 # The dark CM theme must keep black illustration backgrounds,
 # light linework and green highlights in the actual encoded GIF.
 cm_image=Image.open(output).convert('RGB');green=0
 for row,slot in enumerate(cm_slots):
  pixels=list(cm_image.crop((slot['x'],slot['y'],slot['x']+slot['width'],slot['y']+slot['height'])).get_flattened_data())
  assert sum(r<35 and g<35 and b<35 for r,g,b in pixels)>len(pixels)*.45,row
  assert sum(r>150 and g>150 and b>150 for r,g,b in pixels)>100,row
  green+=sum(g>r+15 and g>b+8 and g>70 for r,g,b in pixels)
 assert green>300,green
 dialog.get_by_role('button',name='Compartilhar GIF').click();page.wait_for_function('shared.length===1');assert page.evaluate('shared[0].type')=='image/gif'
 expect(dialog.locator('[role=status]')).to_contain_text('GIF pronto')
 dialog.get_by_role('button',name='Fechar',exact=True).click();page.locator('#workoutGifsBtn').click();expect(dialog.locator('[role=status]')).to_contain_text('8/8');dialog.get_by_role('button',name='Fechar',exact=True).click()
 # Independent Gym choices, despite the same student's saved CM preferences.
 items=gym if ENGINE=='chromium' else gym
 ids=['1h_RNwLjYKoJtTOAEHgKYgoMd1JBB_NPo','1zuCVsAdSRy7VUtwgtjf1BwK7qa5kKQvL','1J0581Mjqk4_p6XEv5-PW1RZT5miqGXRr','11c8topUm97PrFofkMtbcgceOiyV1R2xr','1LTkLxUPSOchKmQZcLPJlwByuhk2yNhQB','1qE-BHUb2Y1kxLjWakLpxfot3J1MDdxWr']
 if ENGINE=='webkit':ids=ids[2:4]
 sources=[next(v for v in gym if v['id']==id) for id in ids]
 data[0]['treino']['A']=[v['name']+' — 4x9 [Vídeo: '+v['url']+']' for v in sources]
 page.evaluate('(people)=>localStorage.setItem("treinoAlunos",JSON.stringify(people))',data);page.reload();page.locator('#workoutGifsBtn').click();page.get_by_role('combobox',name='Biblioteca dos GIFs').select_option('gymfaster')
 expect(dialog).to_have_attribute('data-library','gymfaster');expect(dialog.locator('.gif-card video.cm-ink-on-white')).to_have_count(0);expect(dialog.locator('[role=status]')).to_contain_text(str(len(ids))+'/'+str(len(ids)))
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
