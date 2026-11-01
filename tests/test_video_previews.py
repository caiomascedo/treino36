"""Preview is read-only until explicit selection; both libraries and mobility links."""
import os,json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];ENGINE=os.getenv('GIF_TEST_BROWSER','chromium')
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if ENGINE=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844});errors=[]
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['data','blob']:r.continue_();return
  f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='preview.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://preview.test/');page.evaluate('TreinoStorage.ready')
 data=[{'student_id':'preview-test','nome':'Teste prévia','treino':{'A':['Agachamento Smith — 3x8','Leg Press 45 + Ag Sumo — 3x8+10']},'titulos':{'A':'A. Pernas'}}]
 page.evaluate('(d)=>localStorage.setItem("treinoAlunos",JSON.stringify(d))',data)
 page.evaluate('''()=>localStorage.setItem('treinoMobilidades',JSON.stringify([{id:'mob-eye',nome:'Mobilidade gato e vaca',texto:'Mobilidade gato e vaca — 2x10'}]))''');page.reload()
 before=page.evaluate('localStorage.getItem("treinoAlunos")');mob_before=page.evaluate('localStorage.getItem("treinoMobilidades")')
 page.get_by_role('button',name='Ver movimento do exercício 1 da seção A',exact=True).click();standalone=page.locator('.gif-video-picker');expect(standalone).to_be_visible();standalone.get_by_role('button',name='Fechar',exact=True).click();assert not errors,errors
 page.locator('#workoutGifsBtn').click();main=page.locator('#workoutGifDialog');main.locator('.gif-card').first.get_by_role('button',name='Escolher outro vídeo',exact=True).click();picker=page.locator('.gif-video-picker')
 edit=picker.get_by_role('button',name='Editar biblioteca',exact=True);assert edit.bounding_box()['y']<picker.get_by_role('searchbox').bounding_box()['y'];assert edit.bounding_box()['height']<36
 picker.get_by_role('combobox',name='Biblioteca da demonstração').select_option('both');picker.get_by_role('button',name='Ver todos os vídeos',exact=True).click();expect(picker.locator('[data-video-id]')).to_have_count(992)
 picker.get_by_role('searchbox').fill('Cadeira Extensora');row=picker.locator('.gif-library-row').first
 asset_id=row.locator('[data-video-id]').get_attribute('data-video-id');row.locator('.gif-preview-eye').click();preview=page.locator('#movementPreview');expect(preview).to_be_visible();page.wait_for_function('document.querySelector("#movementPreview video").readyState>=2',timeout=20000)
 page.wait_for_function('document.querySelector("#movementPreview video").currentTime>.1',timeout=10000)
 assert page.evaluate('localStorage.getItem("treinoAlunos")')==before;assert not page.evaluate('localStorage.getItem("treinoGifChoicesV1")')
 preview.get_by_role('button',name='Fechar prévia').click();expect(picker).to_be_visible();assert preview.locator('video').get_attribute('src') is None
 picker.get_by_role('combobox',name='Biblioteca da demonstração').select_option('cm');picker.get_by_role('searchbox').fill('gato');picker.locator('.gif-preview-eye').first.click();expect(preview.locator('video')).to_have_class('cm-ink-on-white');preview.get_by_role('button').click()
 assert picker.evaluate('e=>e.scrollWidth<=e.clientWidth');picker.get_by_role('button',name='Fechar',exact=True).click();main.get_by_role('button',name='Fechar',exact=True).click()
 # Main exercise eye does not add its icon to saved text. Compound has switches for both parts.
 page.get_by_role('button',name='Ver movimento do exercício 2 da seção A',exact=True).click();expect(picker.locator('.gif-picker-parts button')).to_have_count(2);picker.locator('.gif-picker-parts button').last.click();expect(picker.locator('h3')).to_have_text('Ag Sumo');picker.get_by_role('button',name='Fechar',exact=True).click();assert page.evaluate('localStorage.getItem("treinoAlunos")')==before
 # Viewing mobility never selects the template or changes its text.
 page.locator('#moreOptions>summary').click();page.locator('#mobilityLibraryBtn').click();mob=page.locator('#mobilityDialog');page.get_by_role('button',name='Ver movimentos de Mobilidade gato e vaca',exact=True).click();expect(picker).to_be_visible();expect(mob.locator('#mobilityText')).to_have_value('');picker.locator('.gif-preview-eye').first.click();expect(preview).to_be_visible();preview.get_by_role('button').click();picker.get_by_role('button',name='Fechar',exact=True).click();assert page.evaluate('localStorage.getItem("treinoMobilidades")')==mob_before
 mob.locator('.mobility-video-row>button:first-child').filter(has_text='Mobilidade gato e vaca').click();mob.locator('#mobilityRegistration>summary').click();mob.locator('#mobilityVideoBtn').click();picker.locator('[data-video-id]').first.click();expect(preview).to_be_visible();preview.get_by_role('button').click();assert '[Vídeo:' in mob.locator('#mobilityText').input_value()
 mob.get_by_role('button',name='Salvar na biblioteca',exact=True).click();saved=json.loads(page.evaluate('localStorage.getItem("treinoMobilidades")'));assert '[Vídeo:' in next(m['texto'] for m in saved if m['id']=='mob-eye')
 assert page.evaluate('localStorage.getItem("treinoAlunos")')==before
 mob.get_by_role('button',name='Fechar',exact=True).click();page.get_by_role('button',name='Ver movimento do exercício 1 da seção A',exact=True).click();picker.locator('[data-video-id]').first.click();expect(preview).to_be_visible();preview.get_by_role('button').click();page.wait_for_function('document.querySelector(".sec-a ol li a.exercise-video")');assert '[Vídeo:' in json.loads(page.evaluate('localStorage.getItem("treinoAlunos")'))[0]['treino']['A'][0]
 page.locator('.sec-a ol .exercise-video').first.click();expect(preview).to_be_visible();expect(page.locator('.gif-video-picker')).to_have_count(0);preview.get_by_role('button').click();assert not errors,errors
 page.screenshot(path='/tmp/video-preview-'+ENGINE+'.png');b.close()
 print('PASS',ENGINE,': compact top editor; 992 clips in both sources; real playback before selection; main compound eyes; mobility eyes and saved video links; prescriptions unchanged')
