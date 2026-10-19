"""The browser owns PDF viewing; there is no app wrapper or automatic share flow."""
import base64
from pathlib import Path
import fitz
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with fitz.open() as doc:
 page=doc.new_page();page.insert_text((60,60),'PDF original - layout preservado')
 data=base64.b64encode(doc.tobytes()).decode()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page()
 page.set_content('<input id="student" value="Ana">')
 page.evaluate("""()=>{
  window.shares=0;window.saves=[];window.urls=new Map();window.viewers=[];window.cleanup=[];
  Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{shares++}});
  Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});
  const create=URL.createObjectURL.bind(URL);URL.createObjectURL=file=>{const url=create(file);urls.set(url,file);return url;};
  window.open=()=>{const viewer={closed:false,opener:window,document:{title:'',body:{textContent:''}},location:{replace(url){viewer.url=url}},close(){this.closed=true}};viewers.push(viewer);return viewer;};
  window.setInterval=fn=>{cleanup.push(fn);return cleanup.length;};window.clearInterval=()=>{};
 }""")
 page.add_script_tag(path=str(ROOT/'pdf-viewer.js'))
 result=page.evaluate("""async data=>{
  const bytes=Uint8Array.from(atob(data),c=>c.charCodeAt(0));
  const doc={setProperties(value){this.properties=value},output(){return new Blob([bytes],{type:'application/pdf'})},save(name){saves.push(name)}};
  const target=TreinoPDFViewer.reserve();await Promise.resolve();TreinoPDFViewer.deliver(doc,'Avaliacao_Ana.pdf',target);
  const file=urls.get(target.url),content=await file.arrayBuffer();
  return {name:file.name,type:file.type,same:content.byteLength===bytes.byteLength&&new Uint8Array(content).every((v,i)=>v===bytes[i]),opener:target.opener,title:doc.properties.title,ui:document.querySelectorAll('dialog,iframe').length,shares,saves};
 }""",data)
 assert result=={'name':'Avaliacao_Ana.pdf','type':'application/pdf','same':True,'opener':None,'title':'Avaliacao_Ana','ui':0,'shares':0,'saves':[]},result
 assert page.locator('#student').input_value()=='Ana'
 page.evaluate("""()=>{const target=TreinoPDFViewer.reserve();target.close();TreinoPDFViewer.deliver({output(){throw Error('Late result must be ignored')}},'cancelado.pdf',target)}""")
 page.evaluate("""()=>{window.open=()=>null;TreinoPDFViewer.deliver({save(name){saves.push(name)}},'Dieta_Ana.pdf',TreinoPDFViewer.reserve())}""")
 assert page.evaluate('saves')==['Dieta_Ana.pdf']
 assert page.evaluate('shares')==0
 browser.close()
 print('PASS: native PDF handoff even with file sharing supported; identical PDF bytes, named PDF MIME/title, no app UI or automatic sharing, cancellation ignored, blocked popup download fallback')
