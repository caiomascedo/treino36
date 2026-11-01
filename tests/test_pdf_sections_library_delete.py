"""Compact PDF section disclosure and reversible deletion in the standalone library."""
import json,os
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];ENGINE=os.getenv('GIF_TEST_BROWSER','chromium');catalog=json.loads((ROOT/'gymfaster-catalog.json').read_text());asset=next(v for v in catalog['videos'] if v.get('kind')=='created-example');yt='https://youtu.be/Keep_TEST123'
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if ENGINE=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['blob','data']:r.continue_();return
  f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='sections-delete.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://sections-delete.test/');page.evaluate('TreinoStorage.ready')
 data=[{'student_id':'sections-delete','nome':'Teste biblioteca','treino':{'A':['Agachamento Smith — 3x8 [Vídeo: '+yt+'] [GIFs: '+asset['url']+']'],'B':['Remada — 3x10']},'titulos':{'A':'A. Pernas','B':'B. Costas'}}];page.evaluate('(d)=>localStorage.setItem("treinoAlunos",JSON.stringify(d))',data);page.reload();page.evaluate('TreinoStorage.ready');before=page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino')
 page.locator('#pdfBtn').click();tools=page.locator('#pdfReviewTools');edit=tools.locator('.pdf-edit-tools>button');sections=tools.locator('.pdf-section-choice>summary');a=edit.bounding_box();bb=sections.bounding_box();assert abs(a['y']-bb['y'])<2 and a['x']+a['width']<=bb['x'],(a,bb)
 edit.click();expect(tools.locator('.pdf-section-choice')).not_to_have_attribute('open','');expect(edit).to_have_text('Concluir edição');sections.click();expect(tools.locator('.pdf-section-choice')).to_have_attribute('open','');page.get_by_role('checkbox',name='Incluir seção B no PDF',exact=True).uncheck();expect(page.locator('#pdfBody [data-pdf-section=B]')).to_be_hidden();edit.click();expect(tools.locator('.pdf-section-choice')).not_to_have_attribute('open','');expect(edit).to_have_text('Editar texto');sections.click();page.get_by_role('button',name='Marcar todas',exact=True).click();expect(page.locator('#pdfBody [data-pdf-section=B]')).to_be_visible();page.screenshot(path='/tmp/sections-side-'+ENGINE+'.png');page.locator('#closePdfViewer').click()
 def library():
  page.locator('#moreOptions>summary').click();page.locator('#gymfasterCollectionBtn').click();return page.locator('#gymfasterLibrary')
 lib=library();lib.get_by_role('searchbox').fill('exemplo criado');row=lib.locator('[data-video-id="'+asset['id']+'"]');expect(row).to_have_count(1);row.get_by_role('button',name='Apagar',exact=True).click();expect(row).to_have_count(0);expect(lib.get_by_role('button',name='Desfazer exclusão',exact=True)).to_be_visible();expect(lib.locator('[role=status]')).to_contain_text('apagado da sua lista');lib.get_by_role('button',name='Desfazer exclusão',exact=True).click();expect(row).to_have_count(1)
 row.get_by_role('button',name='Apagar',exact=True).click();lib.get_by_role('button',name='Fechar',exact=True).click();page.reload();page.evaluate('TreinoStorage.ready');lib=library();lib.get_by_role('searchbox').fill('exemplo criado');expect(lib.locator('[data-video-id="'+asset['id']+'"]')).to_have_count(0);lib.get_by_role('button',name='Ver apagados (1)',exact=True).click();deleted=lib.locator('[data-video-id="'+asset['id']+'"]');expect(deleted).to_have_count(1);deleted.get_by_role('button',name='Restaurar',exact=True).click();expect(deleted).to_have_count(0);lib.get_by_role('button',name='Voltar aos disponíveis',exact=True).click();expect(lib.locator('[data-video-id="'+asset['id']+'"]')).to_have_count(1)
 assert lib.evaluate('e=>e.scrollWidth<=e.clientWidth');page.screenshot(path='/tmp/library-delete-'+ENGINE+'.png');lib.get_by_role('button',name='Fechar',exact=True).click();actual=page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino');assert actual==before,(before,actual);assert not errors,errors;b.close();print('PASS',ENGINE,': sections beside edit without accidental toggles; section filters still work; library delete/undo/reload/restore; links and prescriptions preserved')
