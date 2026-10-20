"""Selected deletion, complete backup sharing and pending edit preservation."""
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='manager.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route)
 page=context.new_page();page.goto('http://manager.test/')
 page.evaluate('''()=>{const c=document.createElement('canvas');c.width=c.height=40;const photo=c.toDataURL('image/jpeg');localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'one',nome:'Exemplo',treino:{A:[]},obsGuias:[{id:'obs',titulo:'Exames',texto:'Preservar',exameFotos:[{id:'exam',src:photo}]}]}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Exemplo',avaliacoes:[{id:11,data:'20/10/2026',peso:'58',fotoF:photo,fotoFOriginal:photo,fotoL:photo,posturaEdicoes:{fotoF:{lines:[{id:'line'}]},fotoL:{lines:[]}},fotosExtras:[{id:'extra',src:photo,label:'Espelho'}]}]},{id:20,nome:'Outro',avaliacoes:[{id:21,peso:'80'}]}]));}''')
 page.reload();page.locator('#moreOptions > summary').click();page.locator('#storageSpaceBtn').click();page.locator('[data-gallery] > summary').click();expect(page.locator('[data-count]')).to_contain_text('4 foto(s)');expect(page.locator('[data-photos] img')).to_have_count(4)
 # Sharing offers the complete JSON file, without uploading to an invented Drive endpoint.
 page.evaluate('''()=>{navigator.canShare=()=>true;navigator.share=async data=>{window.sharedBackup=JSON.parse(await data.files[0].text());};}''')
 page.locator('[data-drive]').click();expect(page.locator('#storageSpaceDialog [role=status]')).to_contain_text('Compartilhamento concluído')
 shared=page.evaluate('window.sharedBackup');assert shared['tipo']=='treino36-completo';assert shared['avaliacoes'][0]['avaliacoes'][0]['fotoF'].startswith('data:image/')
 # Download fallback works when native file sharing is absent.
 page.evaluate('navigator.canShare=()=>false')
 with page.expect_download() as download:page.locator('[data-drive]').click()
 assert json.loads(Path(download.value.path()).read_text())['tipo']=='treino36-completo'
 expect(page.locator('#storageSpaceDialog [role=status]')).to_contain_text('Google Drive')
 # Concurrent non-photo drafts are merged into the new base before clearing the journal.
 page.evaluate("TreinoStorage.stageAssessment(10,11,{peso:'59',resumo:'Edição pendente'})")
 page.get_by_role('checkbox',name='Selecionar Exemplo · Frontal · 20/10/2026',exact=True).check()
 page.get_by_role('checkbox',name='Selecionar Exemplo · Foto da OBS · Exames',exact=True).check()
 page.once('dialog',lambda dialog:dialog.dismiss());page.locator('[data-delete]').click();expect(page.locator('[data-count]')).to_contain_text('4 foto(s)')
 page.once('dialog',lambda dialog:dialog.accept());page.locator('[data-delete]').click();expect(page.locator('#storageSpaceDialog [role=status]')).to_contain_text('2 foto(s) apagada(s)',timeout=15000)
 expect(page.locator('[data-count]')).to_contain_text('2 foto(s)')
 records=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))");av=records[0]['avaliacoes'][0]
 assert 'fotoF' not in av and 'fotoFOriginal' not in av and 'fotoF' not in av['posturaEdicoes']
 assert av['fotoL'] and av['fotosExtras'][0]['id']=='extra' and av['peso']=='59' and av['resumo']=='Edição pendente'
 assert records[1]['avaliacoes'][0]['peso']=='80'
 assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].obsGuias[0].exameFotos")==[]
 assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].obsGuias[0].texto")=='Preservar'
 # A stale photo selection cannot delete a replacement uploaded in another window.
 stale=page.evaluate("StoragePhotoManager.list()[0]")
 page.evaluate("TreinoStorage.stageAssessment(10,11,{fotoL:'data:image/jpeg;base64,changed'})")
 result=page.evaluate('(item)=>StoragePhotoManager.remove([item])',stale)
 assert result['removed']==[] and result['errors']
 assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].fotoL")=='data:image/jpeg;base64,changed'
 browser.close();print('PASS: photo count, thumbnails, share/download full JSON, cancellation/selected deletion, pending drafts, unrelated photos and pupils, stale photo protection')
