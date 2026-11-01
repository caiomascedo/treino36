"""Personal library edits persist without changing saved prescriptions or originals."""
import json,os
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];ENGINE=os.environ.get('GIF_TEST_BROWSER','chromium')
videos=json.loads((ROOT/'gymfaster-catalog.json').read_text())['videos'];female=next(v for v in videos if v['name']=='Cadeira Extensora' and v['gender']=='Feminino');id=female['id'];original_catalog=(ROOT/'gymfaster-catalog.json').read_bytes()
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if ENGINE=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 ctx=b.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['blob','data']:r.continue_();return
  f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='edit.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 ctx.route('**/*',route);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://edit.test/');page.evaluate('TreinoStorage.ready');page.evaluate('''()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'personal-lib',nome:'Teste biblioteca pessoal',treino:{A:['Cadeira Extensora — 3x12']},titulos:{A:'A. Pernas'}}]))''');page.reload()
 before=page.evaluate('localStorage.getItem("treinoAlunos")');page.locator('#workoutGifsBtn').click();main=page.locator('#workoutGifDialog');expect(main.locator('.gif-card')).to_have_count(1);main.get_by_role('button',name='Escolher outro vídeo',exact=True).click();picker=page.locator('.gif-video-picker')
 expect(picker.locator('.gif-library-row')).to_have_count(2);expect(picker.get_by_role('button',name='Renomear',exact=True)).not_to_be_visible()
 picker.get_by_role('button',name='Editar biblioteca',exact=True).click();row=picker.locator('[data-video-id="'+id+'"]').locator('..');row.get_by_role('button',name='Renomear',exact=True).click();picker.get_by_role('textbox',name='Novo nome do vídeo').fill('Extensora personalizada');picker.get_by_role('button',name='Salvar nome',exact=True).click()
 expect(picker.locator('[data-video-id="'+id+'"]')).to_contain_text('Extensora personalizada');expect(picker.locator('.gif-picker-count')).to_contain_text('Nome atualizado');expect(picker.locator('[data-video-id="'+id+'"]').locator('..')).to_contain_text('Nome original: Cadeira Extensora')
 picker.get_by_role('button',name='Fechar',exact=True).click();expect(main.locator('.gif-card small').last).to_contain_text('Extensora personalizada');expect(main.locator('.gif-card strong')).to_contain_text('Cadeira Extensora');assert page.evaluate('localStorage.getItem("treinoAlunos")')==before
 main.get_by_role('button',name='Fechar',exact=True).click();page.reload();page.locator('#workoutGifsBtn').click();expect(main.locator('.gif-card small').last).to_contain_text('Extensora personalizada')
 main.get_by_role('button',name='Escolher outro vídeo',exact=True).click();picker.get_by_role('button',name='Editar biblioteca',exact=True).click();row=picker.locator('[data-video-id="'+id+'"]').locator('..');row.get_by_role('button',name='Apagar',exact=True).click();expect(picker.locator('[data-video-id="'+id+'"]')).to_have_count(0);expect(picker.locator('.gif-picker-count')).to_contain_text('670 disponíveis de 671')
 picker.get_by_role('button',name='Desfazer exclusão',exact=True).click();expect(picker.locator('[data-video-id="'+id+'"]')).to_have_count(1)
 picker.locator('[data-video-id="'+id+'"]').locator('..').get_by_role('button',name='Apagar',exact=True).click();picker.get_by_role('button',name='Fechar',exact=True).click();main.get_by_role('button',name='Fechar',exact=True).click()
 page.locator('#moreOptions>summary').click();expect(page.locator('#gymfasterCollectionBtn')).to_contain_text('670/671');page.locator('#gymfasterCollectionBtn').click();root=page.locator('#gymfasterLibrary');root.get_by_role('searchbox').fill('Extensora personalizada');expect(root.locator('.gym-result')).to_have_count(0);root.get_by_role('button',name='Fechar',exact=True).click()
 page.reload();page.locator('#workoutGifsBtn').click();main.get_by_role('button',name='Escolher outro vídeo',exact=True).click();expect(picker.locator('[data-video-id="'+id+'"]')).to_have_count(0);picker.get_by_role('button',name='Editar biblioteca',exact=True).click();picker.get_by_role('button',name='Ver apagados (1)',exact=True).click();removed=picker.locator('[data-video-id="'+id+'"]').locator('..');expect(removed.locator('[data-video-id]')).to_be_disabled();removed.get_by_role('button',name='Restaurar',exact=True).click();picker.get_by_role('button',name='Voltar aos disponíveis',exact=True).click();expect(picker.locator('[data-video-id="'+id+'"]')).to_contain_text('Extensora personalizada')
 row=picker.locator('[data-video-id="'+id+'"]').locator('..');row.get_by_role('button',name='Restaurar nome',exact=True).click();expect(picker.locator('[data-video-id="'+id+'"]')).to_contain_text('Cadeira Extensora');assert picker.evaluate('e=>e.scrollWidth<=e.clientWidth')
 assert page.evaluate('localStorage.getItem("treinoAlunos")')==before;assert (ROOT/'gymfaster-catalog.json').read_bytes()==original_catalog;assert not errors,errors;b.close()
print('PASS',ENGINE,': library rename, search aliases, delete, undo/restore, reload persistence and original prescriptions preserved')
