"""Repeated real-image uploads with a constrained browser store and picker refresh."""
import base64
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 context.add_init_script('''window.nativeGet=Storage.prototype.getItem;window.nativeSet=Storage.prototype.setItem;
 window.storageBytes=()=>{let size=0;for(let i=0;i<localStorage.length;i++){const key=localStorage.key(i);size+=2*(key.length+(nativeGet.call(localStorage,key)||'').length);}return size;};
 Storage.prototype.setItem=function(key,value){if(this===localStorage&&window.testBudget){const previous=nativeGet.call(this,key);const total=storageBytes()- (previous===null?0:2*(key.length+previous.length))+2*(key.length+String(value).length);if(total>testBudget)throw new DOMException('Storage full','QuotaExceededError');}return nativeSet.call(this,key,value);};''')
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.jpg':'image/jpeg','.png':'image/png'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://app.test/treino36/')
 photo=page.evaluate('''()=>{const c=document.createElement('canvas');c.width=480;c.height=640;const ctx=c.getContext('2d'),d=ctx.createImageData(480,640);let seed=12345;for(let i=0;i<d.data.length;i++){seed=(Math.imul(seed,1664525)+1013904223)|0;d.data[i]=i%4===3?255:(seed>>>24);}ctx.putImageData(d,0,0);const src=c.toDataURL('image/jpeg',.85);localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento']},avaliacaoId:10}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',idade:'30',treinoStudentIds:['a'],avaliacoes:[{id:11,data:'20/10/2026',fotosExtras:[{id:'old',label:'Foto 1',src}]}]}]));return src;}''')
 page.reload();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="fotos"]').click();page.locator('#obsExtraPhotos > summary').click()
 def upload():
  with page.expect_file_chooser() as chooser:page.locator('#extraPhotoAdd').click()
  chooser.value.set_files({'name':'foto.jpg','mimeType':'image/jpeg','buffer':base64.b64decode(photo.split(',')[1])})
 # One existing photo plus enough remaining space for compressed durable storage,
 # but not a second uncompressed copy of the entire photo collection.
 page.evaluate('window.testBudget=storageBytes()+Math.floor('+str(len(photo))+'*2.5)')
 upload();expect(page.locator('.extra-photo-card')).to_have_count(2,timeout=15000)
 page.evaluate('window.testBudget=0')
 # A background data sync while the system picker is open must not remove its input.
 with page.expect_file_chooser() as chooser:page.locator('#extraPhotoAdd').click()
 page.evaluate("document.activeElement.blur();window.dispatchEvent(new StorageEvent('storage',{key:'treinoAlunos'}));")
 assert chooser.value.element.is_visible() is False
 assert chooser.value.element.evaluate('(input)=>input.isConnected'),'Picker input was detached during sync'
 chooser.value.set_files({'name':'foto.jpg','mimeType':'image/jpeg','buffer':base64.b64decode(photo.split(',')[1])})
 expect(page.locator('.extra-photo-card')).to_have_count(3,timeout=15000)
 # The same file can be picked again, followed by a multi-file batch.
 upload();expect(page.locator('.extra-photo-card')).to_have_count(4)
 with page.expect_file_chooser() as chooser:page.locator('#extraPhotoAdd').click()
 chooser.value.set_files([{'name':f'foto{i}.jpg','mimeType':'image/jpeg','buffer':base64.b64decode(photo.split(',')[1])} for i in range(2)])
 expect(page.locator('.extra-photo-card')).to_have_count(6,timeout=15000)
 records=page.evaluate("AvaliacaoTreinoSync.read('avaliacao_fisica_alunos')")
 assert records[0]['avaliacoes'][0]['fotosExtras'][0]['src']==photo
 assert len({x['id'] for x in records[0]['avaliacoes'][0]['fotosExtras']})==6
 page.reload();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="fotos"]').click();page.locator('#obsExtraPhotos > summary').click();expect(page.locator('.extra-photo-card')).to_have_count(6)
 assert not errors,errors
 browser.close();print('PASS: second detailed photo under limited storage, picker survives sync, repeated same-file additions, batch append, original preservation and reload')
