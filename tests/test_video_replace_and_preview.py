"""Replace a clip through Save, purge from the review list, and retain an accidental B close."""
import os,subprocess,tempfile
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1];ENGINE=os.getenv('GIF_TEST_BROWSER','chromium')
directory=tempfile.TemporaryDirectory();files=[]
for color in ['red','blue']:
 file=Path(directory.name)/(color+'.mp4')
 subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=c='+color+':s=160x120:r=10:d=1','-c:v','libx264','-pix_fmt','yuv420p',str(file)],check=True);files.append(file)
with sync_playwright() as p:
 browser=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if ENGINE=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['blob','data']:r.continue_();return
  f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='localhost' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route)
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://localhost:8765/');page.evaluate('TreinoStorage.ready');page.evaluate('GymFasterLibrary.open()')
 library=page.locator('#gymfasterLibrary');library.get_by_role('searchbox').fill('Vídeo pessoal de substituição')
 library.get_by_role('button',name='Adicionar vídeo',exact=True).click();form=page.locator('.gif-video-add')
 form.get_by_label('Categoria do vídeo',exact=True).select_option('Peito');form.get_by_label('Arquivo de vídeo',exact=True).set_input_files(str(files[0]))
 for label in ['Salvar vídeo','Cancelar']:
  box=form.get_by_role('button',name=label,exact=True).bounding_box();assert box['height']>=50 and box['width']>290
 form.get_by_role('button',name='Salvar vídeo',exact=True).click();expect(form).to_have_count(0)
 original=page.evaluate("WorkoutCatalog.current().find(v=>v.name==='Vídeo pessoal de substituição')")
 page.evaluate("(id)=>{WorkoutVideoLibrary.toggleFavorite(id);WorkoutVideoLibrary.rename(id,'Meu vídeo renomeado')}",original['id'])
 library.get_by_role('button',name='Fechar',exact=True).click()
 page.evaluate("(asset)=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'replace-test',nome:'Teste substituir',treino:{A:['Meu vídeo renomeado — 3×12 [GIFs: '+asset.url+']'],B:['Meu vídeo renomeado — 3×10 [GIFs: '+asset.url+']']},titulos:{A:'A. Primeiro',B:'B. Segundo'}}]));localStorage.setItem('treinoAlunoSelecionado','Teste substituir')}",original)
 page.reload();page.evaluate('TreinoStorage.ready');before=page.evaluate('localStorage.getItem("treinoAlunos")')
 page.evaluate('GymFasterLibrary.open()');library.get_by_role('searchbox').fill('Meu vídeo renomeado');library.get_by_role('button',name='Adicionar vídeo',exact=True).click()
 expect(form.locator('.video-existing-choice')).to_contain_text('Já existe')
 expect(form.locator('.video-existing-choice')).to_contain_text('Meu vídeo renomeado')
 form.get_by_label('Arquivo de vídeo',exact=True).set_input_files(str(files[1]));form.get_by_role('button',name='Salvar vídeo',exact=True).click();expect(form).to_have_count(1)
 assert page.evaluate('(id)=>WorkoutCatalog.lookup(id).sha256',original['id'])==original['sha256']
 form.get_by_role('button',name='Ver vídeo existente',exact=True).click();old_preview=page.locator('#movementPreview');expect(old_preview).to_contain_text('Meu vídeo renomeado');expect(old_preview.locator('video')).to_be_visible();old_preview.get_by_role('button',name='Fechar prévia',exact=True).click()
 form.get_by_role('radio',name='Não, manter o vídeo existente',exact=True).check();expect(form.get_by_label('Arquivo de vídeo',exact=True)).to_be_disabled();form.get_by_role('button',name='Salvar vídeo',exact=True).click();expect(form).to_have_count(0)
 assert page.evaluate('(id)=>WorkoutCatalog.lookup(id).sha256',original['id'])==original['sha256']
 library.get_by_role('button',name='Adicionar vídeo',exact=True).click();form.get_by_role('radio',name='Sim, substituir pelo novo arquivo',exact=True).check();form.get_by_label('Arquivo de vídeo',exact=True).set_input_files(str(files[1]));form.get_by_role('button',name='Salvar vídeo',exact=True).click();expect(form).to_have_count(0)
 updated=page.evaluate('(id)=>WorkoutCatalog.lookup(id)',original['id'])
 assert updated['id']==original['id'] and updated['url']==original['url'] and updated['sha256']!=original['sha256']
 assert page.evaluate('(id)=>WorkoutVideoLibrary.isFavorite(id)',original['id'])
 assert page.evaluate('WorkoutCatalog.current().filter(v=>v.source==="Meu vídeo").length')==1
 assert page.evaluate('localStorage.getItem("treinoAlunos")')==before
 library.get_by_role('button',name='Fechar',exact=True).click();page.reload();page.evaluate('TreinoStorage.ready');page.evaluate('WorkoutCatalog.load()')
 assert page.evaluate('(id)=>WorkoutCatalog.lookup(id).sha256',original['id'])==updated['sha256']
 assert page.evaluate('async id=>{const asset=WorkoutCatalog.lookup(id),bytes=await fetch(asset.media).then(r=>r.arrayBuffer());return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)),b=>b.toString(16).padStart(2,"0")).join("")}',original['id'])==updated['sha256']
 # Custom preview is compact and controlled without a native mobile video overlay.
 page.evaluate('(id)=>WorkoutVideoPreview.open(WorkoutCatalog.lookup(id))',original['id']);preview=page.locator('#movementPreview');video=preview.locator('video')
 expect(video).to_be_visible();assert not video.evaluate('v=>v.controls');assert video.bounding_box()['height']<=335
 page.wait_for_function('document.querySelector("#movementPreview video").readyState>=2')
 preview.get_by_role('button',name='Pausar vídeo',exact=True).click();assert video.evaluate('v=>v.paused')
 preview.get_by_role('button',name='Reproduzir vídeo',exact=True).click();preview.get_by_role('button',name='Reiniciar vídeo',exact=True).click()
 preview.get_by_role('button',name='Ativar som',exact=True).click();assert not video.evaluate('v=>v.muted')
 preview.get_by_role('button',name='Ampliar prévia',exact=True).click();assert preview.bounding_box()['width']>=389
 preview.get_by_role('button',name='Reduzir prévia',exact=True).click();assert preview.bounding_box()['width']<390
 page.screenshot(path='/tmp/new-preview-'+ENGINE+'.png')
 preview.get_by_role('button',name='Fechar prévia',exact=True).click();page.wait_for_function('v=>v.paused&&!v.hasAttribute("src")',arg=video.element_handle())
 # Closing synchronously in the same event as choosing B must retain B.
 page.locator('#workoutGifsBtn').click();main=page.locator('#workoutGifDialog');expect(main.locator('.gif-card')).to_have_count(1)
 assert page.evaluate('document.activeElement.id')=='workoutGifTitle'
 page.evaluate("const d=document.getElementById('workoutGifDialog'),s=d.querySelector('[aria-label=\"Treino para o GIF\"]');s.value='B';s.dispatchEvent(new Event('change'));d.close()")
 page.locator('#workoutGifsBtn').click();expect(main.get_by_label('Treino para o GIF',exact=True)).to_have_value('B')
 page.keyboard.press('Escape');expect(main).not_to_be_visible()
 # A fresh tab has no sessionStorage; the chosen B is also stored locally.
 other=context.new_page();other.goto('http://localhost:8765/');other.evaluate('TreinoStorage.ready');other.locator('#workoutGifsBtn').click()
 expect(other.locator('#workoutGifDialog').get_by_label('Treino para o GIF',exact=True)).to_have_value('B');assert other.evaluate('document.activeElement.id')=='workoutGifTitle';other.close()
 # A built-in catalog clip can also be replaced without a duplicate or broken ID.
 builtin=page.evaluate("async()=>{await WorkoutCatalog.load();const all=WorkoutCatalog.current();return all.find(v=>v.collection==='gymfaster'&&v.source!=='Meu vídeo'&&all.filter(a=>WorkoutCatalog.key(a.name)===WorkoutCatalog.key(v.name)).length===1)}")
 count=page.evaluate('WorkoutCatalog.current().length');page.evaluate('GymFasterLibrary.open()');library.get_by_role('searchbox').fill(builtin['name']);library.get_by_role('button',name='Adicionar vídeo',exact=True).click()
 expect(form.locator('.video-existing-choice')).to_contain_text('Já existe');form.get_by_role('radio',name='Sim, substituir pelo novo arquivo',exact=True).check();form.get_by_label('Arquivo de vídeo',exact=True).set_input_files(str(files[0]));form.get_by_role('button',name='Salvar vídeo',exact=True).click();expect(form).to_have_count(0)
 assert page.evaluate('WorkoutCatalog.current().length')==count
 assert page.evaluate('(id)=>WorkoutCatalog.lookup(id).localReplacement',builtin['id'])
 assert page.evaluate('(id)=>WorkoutCatalog.lookup(id).media.startsWith("blob:")',builtin['id'])
 library.get_by_role('button',name='Fechar',exact=True).click()
 # Both purge buttons work directly in the deletion-review dialog.
 page.evaluate('(ids)=>{ids.forEach(id=>WorkoutVideoLibrary.remove(id));WorkoutVideoLibrary.openReview()}',[builtin['id'],original['id']]);review=page.locator('#videoDeletionReview')
 for id in [builtin['id'],original['id']]:
  row=review.locator('[data-video-id="'+id+'"]');page.once('dialog',lambda d:d.dismiss());row.get_by_role('button',name='Apagar definitivamente',exact=True).click();expect(row.get_by_role('button',name='Apagar definitivamente',exact=True)).to_be_visible()
  page.once('dialog',lambda d:d.accept());row.get_by_role('button',name='Apagar definitivamente',exact=True).click();expect(row).to_contain_text('Apagado definitivamente');expect(row.get_by_role('button',name='Apagar definitivamente',exact=True)).to_have_count(0)
 stored=page.evaluate("()=>new Promise(resolve=>{const r=indexedDB.open('treino36-private-videos',1);r.onsuccess=()=>{const db=r.result,q=db.transaction('videos').objectStore('videos').count();q.onsuccess=()=>{resolve(q.result);db.close()}}})")
 assert stored==0
 assert page.evaluate('(ids)=>ids.every(id=>!WorkoutCatalog.current().some(v=>v.id===id))',[builtin['id'],original['id']])
 # Saving through an exercise's picker applies the clip immediately, without another selection click.
 review.get_by_role('button',name='Fechar',exact=True).click();page.locator('#workoutGifsBtn').click()
 expect(main.get_by_label('Treino para o GIF',exact=True)).to_have_value('B')
 main.get_by_role('button',name='Escolher outro vídeo',exact=True).click();picker=page.locator('.gif-video-picker')
 picker.get_by_role('button',name='Adicionar vídeo',exact=True).click();form.get_by_label('Categoria do vídeo',exact=True).select_option('Peito');form.get_by_label('Arquivo de vídeo',exact=True).set_input_files(str(files[1]));form.get_by_role('button',name='Salvar vídeo',exact=True).click()
 expect(form).to_have_count(0);expect(picker).to_have_count(0);expect(main.locator('.gif-missing')).to_have_count(0)
 chosen=main.locator('.gif-card').get_attribute('data-video-id')
 page.wait_for_function('(id)=>JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.B[0].includes(id)',arg=chosen)
 # Existing male/female variants with the same name must be disambiguated, not blocked as duplicates.
 main.get_by_role('button',name='Fechar',exact=True).click();page.evaluate('GymFasterLibrary.open()');library.get_by_role('searchbox').fill('Cadeira Extensora');library.get_by_role('button',name='Adicionar vídeo',exact=True).click()
 version=form.get_by_label('Vídeo a substituir',exact=True);expect(version).to_be_visible();assert version.locator('option').count()>2
 target_id=version.locator('option').nth(1).get_attribute('value');group=page.evaluate('(id)=>WorkoutCatalog.lookup(id).group',target_id)
 form.get_by_label('Categoria do vídeo',exact=True).select_option(group);form.get_by_label('Arquivo de vídeo',exact=True).set_input_files(str(files[0]));form.get_by_role('button',name='Salvar vídeo',exact=True).click();expect(form).to_have_count(1)
 version.select_option(target_id);form.get_by_role('radio',name='Sim, substituir pelo novo arquivo',exact=True).check();form.get_by_role('button',name='Salvar vídeo',exact=True).click();expect(form).to_have_count(0)
 assert page.evaluate('(id)=>WorkoutCatalog.lookup(id).localReplacement',target_id)
 assert not errors,errors;browser.close()
 print('PASS',ENGINE,': large Save/Cancel; replacements preserve IDs, labels, favorites and prescriptions; compact player; immediate B close and fresh-tab restore; confirmed review-list purge removes private bytes')
