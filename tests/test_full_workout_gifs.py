"""Full A–F GIF generation: confirmation, cancellation, actual files and multi-file sharing."""
import os,json
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];ENGINE=os.getenv('GIF_TEST_BROWSER','chromium');asset=next(v for v in json.loads((ROOT/'gymfaster-catalog.json').read_text())['videos'] if v['name']=='Alongamento de Adutores')
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if ENGINE=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 c.add_init_script('''window.sent=[];Object.defineProperty(navigator,'canShare',{configurable:true,value:o=>o.files.length>0});Object.defineProperty(navigator,'share',{configurable:true,value:async o=>sent.push(o.files.map(f=>({name:f.name,size:f.size,type:f.type})))})''')
 denied=set()
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['blob','data']:r.continue_();return
  if u.path in denied:r.fulfill(status=404);return
  f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='full-gif.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://full-gif.test/');page.evaluate('TreinoStorage.ready')
 def seed(count=1,empty=False):
  line=asset['name']+' — 1×15s [GIFs: '+asset['url']+']';data=[{'student_id':'full-gif','nome':'Teste completo','treino':{s:[line]*count if not(empty and s in 'CE') else [] for s in 'ABCDEF'},'titulos':{s:s+'. Mobilidade' for s in 'ABCDEF'},'secaoFAtiva':True}];page.evaluate('(d)=>localStorage.setItem("treinoAlunos",JSON.stringify(d))',data);page.reload();page.evaluate('TreinoStorage.ready')
 def open_full():
  page.locator('#workoutGifsBtn').click();d=page.locator('#workoutGifDialog');d.get_by_role('combobox',name='Biblioteca dos GIFs').select_option('gymfaster');d.get_by_role('combobox',name='Treino para o GIF').select_option('ALL');return d
 # More than 20 across the workout is permitted; each section retains its own limit.
 seed(4);d=open_full();expect(d.locator('.gif-card')).to_have_count(24);messages=[]
 def dismiss(q):messages.append(q.message);q.dismiss()
 page.on('dialog',dismiss);d.get_by_role('button',name='Gerar GIFs do treino completo para enviar',exact=True).click();assert len(messages)==1 and '6 GIFs' in messages[0] and 'vários minutos' in messages[0];expect(d.locator('.gif-decoder')).to_have_count(0);expect(d.locator('.gif-batch-result')).to_have_count(0);page.remove_listener('dialog',dismiss);d.get_by_role('button',name='Fechar',exact=True).click()
 # Empty sections are skipped instead of producing blank files.
 seed(1,True);d=open_full();expect(d.locator('.gif-section-heading')).to_have_count(4);page.on('dialog',dismiss);d.get_by_role('button',name='Gerar GIFs do treino completo para enviar',exact=True).click();assert '4 GIFs' in messages[-1];page.remove_listener('dialog',dismiss);d.get_by_role('button',name='Fechar',exact=True).click()
 seed();d=open_full();before=page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino');expect(d.locator('.gif-section-heading')).to_have_text([s+'. Mobilidade' for s in 'ABCDEF']);expect(d.locator('.gif-card strong')).to_have_text(['1. '+asset['name']]*6,ignore_case=True)
 def accept(q):q.accept()
 page.on('dialog',accept);generate=d.get_by_role('button',name='Gerar GIFs do treino completo para enviar',exact=True);generate.click();expect(d.get_by_role('combobox',name='Treino para o GIF')).to_be_disabled();d.get_by_role('button',name='Cancelar geração',exact=True).click();expect(d.locator('[role=status]')).to_contain_text('Geração cancelada',timeout=30000);expect(d.locator('.gif-decoder')).to_have_count(0);expect(generate).to_be_enabled()
 generate.click();expect(d.locator('[role=status]')).to_contain_text('6 GIFs prontos',timeout=240000);expect(d.locator('.gif-batch-result')).to_have_count(6);expect(d.get_by_role('combobox',name='Treino para o GIF')).to_have_value('ALL');expect(generate).to_be_enabled()
 for i,s in enumerate('ABCDEF'):
  with page.expect_download() as dl:d.locator('.gif-batch-result').nth(i).get_by_role('link',name='Baixar GIF '+s,exact=True).click()
  out=Path('/tmp/full-gif-'+ENGINE+'-'+s+'.gif');dl.value.save_as(str(out));im=Image.open(out);assert im.size[0]==800 and im.n_frames==100;total=0
  for frame in range(im.n_frames):im.seek(frame);total+=im.info['duration']
  assert total==5000
 d.get_by_role('button',name='Enviar GIFs do treino completo',exact=True).click();sent=page.evaluate('sent');assert len(sent)==1 and len(sent[0])==6 and all(f['name'].startswith('treino_'+s+'_gymfaster_') for f,s in zip(sent[0],'ABCDEF'));assert all(f['type']=='image/gif' and f['size']>1000 for f in sent[0]);assert page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino')==before
 d.get_by_role('combobox',name='Treino para o GIF').select_option('A');expect(d.locator('.gif-batch-result')).to_have_count(0);expect(d.get_by_role('button',name='Gerar GIF GymFaster',exact=True)).to_be_enabled();expect(d.get_by_role('button',name='Compartilhar GIF',exact=True)).to_be_hidden()
 # A failed later section leaves completed files available.
 d.get_by_role('button',name='Fechar',exact=True).click();other=next(v for v in json.loads((ROOT/'gymfaster-catalog.json').read_text())['videos'] if v['name']=='Alongamento de Quadríceps em Pé');seed(1,True);page.evaluate('(v)=>{const data=JSON.parse(localStorage.getItem("treinoAlunos"));data[0].treino.B=[v.name+" — 1×15s [GIFs: "+v.url+"]"];data[0].treino.D=[];data[0].treino.F=[];localStorage.setItem("treinoAlunos",JSON.stringify(data))}',other);denied.add('/gymfaster-media/'+other['id']+'.mp4');page.reload();page.evaluate('TreinoStorage.ready');d=open_full();d.get_by_role('button',name='Gerar GIFs do treino completo para enviar',exact=True).click();expect(d.locator('[role=status]')).to_contain_text('1/2 GIFs prontos',timeout=120000);expect(d.locator('.gif-batch-result')).to_have_count(1);expect(d.get_by_role('link',name='Baixar GIF A',exact=True)).to_be_visible();expect(d.get_by_role('button',name='Compartilhar GIF',exact=True)).to_be_visible();assert not errors,errors;b.close();print('PASS',ENGINE,': full A–F confirmation/rejection, per-section limits, skip empty sections, cancellation/retry, six real 100-frame/5-second GIFs, multi-file sharing, unchanged prescriptions and original single-section flow')
