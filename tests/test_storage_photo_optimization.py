"""Real image resizing, atomic storage replacement, idempotence and menu flow."""
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url)
  if u.hostname=='space.test' and u.path=='/blank':r.fulfill(body='<html></html>',content_type='text/html');return
  path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='space.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route)
 page=context.new_page();page.goto('http://space.test/')
 seed=page.evaluate('''()=>{
 const canvas=document.createElement('canvas');canvas.width=1200;canvas.height=1600;const ctx=canvas.getContext('2d'),pixels=ctx.createImageData(1200,1600);let random=42;
 for(let i=0;i<pixels.data.length;i+=4){random=(random*1664525+1013904223)>>>0;pixels.data[i]=random&255;pixels.data[i+1]=(random>>>8)&255;pixels.data[i+2]=(random>>>16)&255;pixels.data[i+3]=255;}ctx.putImageData(pixels,0,0);const photo=canvas.toDataURL('image/jpeg',.85);
 canvas.width=canvas.height=40;const logo=canvas.toDataURL('image/png');
 const person={id:10,nome:'Exemplo',avaliacoes:[{id:11,peso:'58.7',resumo:'Preservar',fotoF:photo,fotoFOriginal:photo,fotosExtras:[{id:'extra',src:photo,label:'Espelho'}],posturaEdicoes:{fotoF:{lines:[{x1:.1,x2:.8,y1:.5,y2:.5}],logo:{src:logo,x:.1,y:.2,width:.3}}}}]};
 localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([person]));localStorage.setItem('treinoAlunos','[]');return {photo,logo,before:TreinoStorage.usage()};
 }''')
 page.reload();page.locator('#moreOptions > summary').click();page.locator('#storageSpaceBtn').click();expect(page.locator('#storageSpaceDialog')).to_be_visible();expect(page.locator('[data-usage]')).to_contain_text('Dados locais usados:')
 page.locator('[data-optimize]').click();expect(page.locator('#storageSpaceDialog [role=status]')).to_contain_text('Espaço liberado:',timeout=30000)
 result=page.evaluate('''async()=>{const av=JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0],image=new Image();image.src=av.fotoF;await image.decode();return {av,width:image.naturalWidth,height:image.naturalHeight,used:TreinoStorage.usage()};}''')
 assert result['width']==900 and result['height']==1200
 assert result['used']<seed['before']*.8,(result['used'],seed['before'])
 av=result['av'];assert av['peso']=='58.7' and av['resumo']=='Preservar'
 assert av['fotoF']==av['fotoFOriginal']==av['fotosExtras'][0]['src']
 assert av['posturaEdicoes']['fotoF']['logo']['src']==seed['logo']
 assert av['posturaEdicoes']['fotoF']['lines']==[{'x1':.1,'x2':.8,'y1':.5,'y2':.5}]
 with page.expect_download() as download:page.locator('[data-backup]').click()
 backup=json.loads(Path(download.value.path()).read_text());assert backup['avaliacoes'][0]['avaliacoes'][0]['fotoF']==av['fotoF']
 # Repeated optimization must not repeatedly degrade image quality.
 before=page.evaluate("localStorage.getItem('avaliacao_fisica_alunos')")
 page.evaluate('TreinoStorage.optimizePhotos()')
 assert page.evaluate("localStorage.getItem('avaliacao_fisica_alunos')")==before
 # A failed write leaves the original key intact.
 page.evaluate('(photo)=>localStorage.setItem("avaliacaoFailure",JSON.stringify({fotoF:photo}))',seed['photo'])
 failure=page.evaluate("localStorage.getItem('avaliacaoFailure')")
 # The adapter's saved native setItem remains atomic; exercise native quota denial in a fresh page.
 isolated=context.new_page();isolated.goto('http://space.test/blank')
 isolated.evaluate('''()=>{const original=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(window.denyWrites&&key==='avaliacaoFailure')throw new DOMException('Full','QuotaExceededError');return original.call(this,key,value);};}''')
 isolated.add_script_tag(url='http://space.test/storage-compression.js');isolated.add_script_tag(url='http://space.test/storage-adapter.js')
 isolated.evaluate('window.denyWrites=true');outcome=isolated.evaluate('TreinoStorage.optimizePhotos()')
 assert outcome['failed']>=1
 assert isolated.evaluate("localStorage.getItem('avaliacaoFailure')")==failure
 browser.close();print('PASS: photo space reduction, menu/reload/usage, original + edited photos and logo/lines preserved, idempotence and atomic quota failure')
