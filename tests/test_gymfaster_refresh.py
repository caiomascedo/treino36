"""Drive rename/category refresh keeps existing prescriptions and media IDs working."""
import json,os
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];ENGINE=os.getenv('GIF_TEST_BROWSER','chromium')
catalog=json.loads((ROOT/'gymfaster-catalog.json').read_text());videos=catalog['videos'];assert len(videos)==671 and len({v['id'] for v in videos})==671
fixtures=[('1FTZ0JBqxL-gmpStYFz2wooBxrNzSqvWs','Avanço _ Passada com Halteres','Afundo com Halteres'),('1P6NT4mS0QT7TnpThJl5Vs89RcCwmJmli','Avanço _ Passada com Halteres','Afundo com Halteres'),('1JWhB45kIpwLvY7ENnB1rd2GefUDEpxZt','Passada _ Avanço com Barra','Afundo com Barra'),('1pv9US0aY3jP77OAN64JWcHgkcFzektkW','Passada _ Avanço com Barra','Afundo com Barra')]
for id,old,name in fixtures:
 v=next(v for v in videos if v['id']==id);assert v['name']==name and old in v['aliases'];assert v['group']=='Quadríceps';assert (ROOT/'gymfaster-media'/(id+'.mp4')).is_file();assert id in v['url']
assert {'Glúteos','Adutores','Posterior de Coxa','Quadríceps'}<={v['group'] for v in videos}
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if ENGINE=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['blob','data']:r.continue_();return
  f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='refresh.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://refresh.test/');page.evaluate('TreinoStorage.ready');chosen=next(v for v in videos if v['id']==fixtures[0][0]);line=fixtures[0][1]+' — 3x10 [GIFs: '+chosen['url']+']';page.evaluate('(line)=>localStorage.setItem("treinoAlunos",JSON.stringify([{student_id:"renamed",nome:"Teste atualização",treino:{A:[line]},titulos:{A:"A. Pernas"}}]))',line);page.reload();before=page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino')
 page.locator('#moreOptions>summary').click();page.locator('#gymfasterCollectionBtn').click();library=page.locator('#gymfasterLibrary');library.get_by_role('searchbox').fill('Afundo com Halteres');expect(library.locator('.gym-result strong').filter(has_text='Afundo com Halteres')).to_have_count(2)
 library.get_by_role('searchbox').fill('Avanço _ Passada com Halteres');expect(library.locator('.gym-result')).to_have_count(2);library.get_by_role('combobox',name='Grupo muscular GymFaster').select_option('Quadríceps');expect(library.locator('.gym-result')).to_have_count(2);library.get_by_role('button',name='Ver movimento',exact=True).first.click();expect(library.locator('.gym-preview strong')).to_contain_text('Afundo com Halteres');assert any(id in library.locator('.gym-preview iframe').get_attribute('src') for id,_,name in fixtures if name=='Afundo com Halteres');library.get_by_role('button',name='Fechar',exact=True).click()
 page.locator('#workoutGifsBtn').click();d=page.locator('#workoutGifDialog');d.get_by_role('combobox',name='Biblioteca dos GIFs').select_option('gymfaster');expect(d.locator('.gif-card small')).to_contain_text('Afundo com Halteres');expect(d.locator('.gif-card strong')).to_contain_text('Avanço _ Passada');page.wait_for_function('document.querySelector("#workoutGifDialog video").readyState>=2',timeout=20000);d.get_by_role('button',name='Escolher outro vídeo',exact=True).click();picker=page.locator('.gif-video-picker');expect(picker.locator('[data-video-id]')).to_have_count(2);expect(picker.locator('[data-video-id]')).to_contain_text(['Afundo com Halteres','Afundo com Halteres']);picker.get_by_role('button',name='Fechar',exact=True).click();d.get_by_role('button',name='Fechar',exact=True).click()
 # Matching by either the old label or corrected name must resolve to the same IDs.
 for id,old,name in fixtures:
  assert page.evaluate('([name,id])=>WorkoutVideoMatch.rank(name,'+json.dumps([{**v,'collection':'gymfaster'} for v in videos],ensure_ascii=False)+',"gymfaster").some(r=>r.video.id===id&&r.score===1)',[old,id])
 assert page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino')==before;assert not errors,errors;page.screenshot(path='/tmp/refresh-gym-'+ENGINE+'.png');b.close()
 print('PASS',ENGINE,': all 671 IDs retained; four corrected names and old aliases searchable; updated groups and actual playback; existing source choice and prescription preserved')
