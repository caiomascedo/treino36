"""Lossless legacy migration, >5 MB photo persistence, backups and failure safety."""
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
  if u.hostname=='vault.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route)
 page=context.new_page();page.goto('http://vault.test/');page.evaluate('TreinoStorage.ready')
 # Seed old inlined storage. No resizing is permitted during migration.
 seed=page.evaluate('''()=>{const c=document.createElement('canvas');c.width=1200;c.height=1600;const ctx=c.getContext('2d'),pixels=ctx.createImageData(c.width,c.height);let seed=123;for(let i=0;i<pixels.data.length;i+=4){seed=(Math.imul(seed,1664525)+1013904223)>>>0;pixels.data[i]=seed&255;pixels.data[i+1]=(seed>>>8)&255;pixels.data[i+2]=(seed>>>16)&255;pixels.data[i+3]=255;}ctx.putImageData(pixels,0,0);const src=c.toDataURL('image/jpeg',.85);localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'one',nome:'Exemplo',avaliacaoId:10,treino:{A:[]}}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Exemplo',sexo:'F',treinoStudentIds:['one'],avaliacoes:[{id:11,data:'20/10/2026',peso:'58',fotoF:src,fotoFOriginal:src,posturaEdicoes:{fotoF:{grid:true,lines:[{id:'keep',x1:.1,x2:.9,y1:.5,y2:.5}]}},fotosExtras:[]}]}]));return {src,before:TreinoStorage.usage()};}''')
 page.reload();page.evaluate('TreinoStorage.ready')
 migrated=page.evaluate('''()=>({used:TreinoStorage.usage(),data:JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0],raw:Storage.prototype.getItem.call(localStorage,'avaliacao_fisica_alunos'),vault:PhotoVault.bytes()})''')
 assert migrated['data']['fotoF']==seed['src']==migrated['data']['fotoFOriginal']
 assert migrated['data']['posturaEdicoes']['fotoF']['lines'][0]['id']=='keep'
 assert migrated['used']<seed['before']/10
 # Persist many distinct new photos well beyond the old local-storage quota.
 result=page.evaluate('''async()=>{const extras=[];for(let n=0;n<8;n++){const c=document.createElement('canvas');c.width=1100;c.height=1500;const ctx=c.getContext('2d'),pixels=ctx.createImageData(c.width,c.height);let seed=999+n;for(let i=0;i<pixels.data.length;i+=4){seed=(Math.imul(seed,1664525)+1013904223)>>>0;pixels.data[i]=seed&255;pixels.data[i+1]=(seed>>>8)&255;pixels.data[i+2]=(seed>>>16)&255;pixels.data[i+3]=255;}ctx.putImageData(pixels,0,0);extras.push({id:'photo'+n,label:'Foto '+n,src:c.toDataURL('image/jpeg',.85)});}await PhotoVault.prepare(extras);TreinoStorage.stageAssessment(10,11,{fotosExtras:extras});await TreinoStorage.compactAssessments();return {photoBytes:PhotoVault.bytes(),local:TreinoStorage.usage()};}''')
 assert result['photoBytes']>5*1024*1024 and result['local']<20000,result
 page.reload();page.evaluate('TreinoStorage.ready')
 assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].fotosExtras.length")==8
 assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].fotoF")==seed['src']
 page.locator('#moreOptions > summary').click();page.locator('#storageSpaceBtn').click();expect(page.locator('[data-count]')).to_contain_text('9 foto(s)');expect(page.locator('[data-capacity]')).to_contain_text('Armazenamento ampliado ativo');expect(page.locator('[data-optimize]')).to_be_hidden()
 with page.expect_download() as download:page.locator('[data-backup]').click()
 backup=json.loads(Path(download.value.path()).read_text());av=backup['avaliacoes'][0]['avaliacoes'][0]
 assert av['fotoF']==seed['src'] and len(av['fotosExtras'])==8
 assert 'treino36:photo:' not in json.dumps(backup)
 # Durable IDB transaction failure must never publish references or change metadata.
 failed=page.evaluate('''async()=>{const before=localStorage.getItem('avaliacao_fisica_alunos'),put=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(){this.transaction.abort();throw new DOMException('Full','QuotaExceededError');};let rejected=false;try{await PhotoVault.prepare('data:image/jpeg;base64,newUniqueImage');}catch(error){rejected=true;}finally{IDBObjectStore.prototype.put=put;}return {rejected,unchanged:before===localStorage.getItem('avaliacao_fisica_alunos')};}''')
 assert failed=={'rejected':True,'unchanged':True},failed
 # Another tab reloads payloads before handling reference-bearing storage updates.
 other=context.new_page();other.goto('http://vault.test/');other.evaluate('TreinoStorage.ready')
 page.evaluate("async()=>{const image='data:image/jpeg;base64,crossTab';await PhotoVault.prepare(image);TreinoStorage.stageAssessment(10,11,{fotoL:image});}")
 other.wait_for_function("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].fotoL==='data:image/jpeg;base64,crossTab'")
 # Full assessment library hydrates images as well.
 library=context.new_page();library.goto('http://vault.test/avaliacao.html?treinoStudentId=one&embed=treino36&secao=fotos');library.evaluate('TreinoStorage.ready');assert library.evaluate("alunos[0].avaliacoes[0].fotoF")==seed['src']
 # Restore the complete backup into a browser with an empty vault.
 restored_context=browser.new_context();restored_context.route('**/*',route);restored=restored_context.new_page();restored.goto('http://vault.test/');restored.evaluate('TreinoStorage.ready');expect(restored.locator('#photoStorageLoading')).to_have_count(0)
 restored.locator('#moreOptions > summary').click()
 with restored.expect_file_chooser() as chooser:restored.locator('#importBtn').click()
 chooser.value.set_files({'name':'backup.json','mimeType':'application/json','buffer':json.dumps(backup).encode()})
 restored.wait_for_function("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos')||'[]')[0]?.avaliacoes[0]?.fotosExtras?.length===8",timeout=30000)
 assert restored.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].fotoF")==seed['src']
 assert restored.evaluate('TreinoStorage.usage()')<100000
 # If opening the vault is denied, block initialization rather than create blank records.
 blocked=context.new_page();blocked.add_init_script("indexedDB.open=()=>{throw new DOMException('Denied','SecurityError');}");blocked.goto('http://vault.test/')
 expect(blocked.locator('#photoStorageLoading')).to_contain_text('Seus dados foram mantidos',timeout=10000)
 assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].fotoF")==seed['src']
 browser.close();print('PASS: lossless photo migration, >5 MB persisted photos with tiny metadata, reload/full library, complete JSON, IDB quota abort and cross-tab hydration')
