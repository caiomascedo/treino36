from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844},has_touch=True)
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404,body='')
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://app.test/treino36/');page.evaluate("""()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento 3x10']}},{student_id:'b',nome:'Bruno',treino:{A:['Supino 3x10']}}]));localStorage.setItem('treinoAlunoSelecionado','Bruno');}""");page.reload()
 page.locator('#hideButtonsBtn').click();expect(page.locator('#mainContainer')).to_have_class('container hide-buttons');page.reload()
 expect(page.locator('#searchName')).to_have_value('Bruno');expect(page.locator('.sec-a ol')).to_contain_text('Supino');expect(page.locator('#searchName')).not_to_be_visible();assert page.evaluate("localStorage.getItem('treino36_buttons_hidden')")=='1'
 # Closing/reopening a tab uses durable storage, not session state or an expiry timer.
 page.close();page=context.new_page();page.goto('http://app.test/treino36/');expect(page.locator('#searchName')).to_have_value('Bruno');expect(page.locator('#searchName')).not_to_be_visible();expect(page.locator('.sec-a ol')).to_contain_text('Supino')
 # A newly revealed control sits exactly under the double-tap location.
 page.evaluate("""()=>{const trap=document.createElement('button');trap.id='gestureTrap';trap.className='global-buttons';trap.textContent='Control';trap.style.cssText='position:fixed;left:100px;top:280px;width:80px;height:60px;z-index:10000';window.trapClicks=0;window.trapDowns=0;trap.onclick=()=>window.trapClicks++;trap.onpointerdown=()=>window.trapDowns++;document.getElementById('mainContainer').append(trap);}""")
 page.touchscreen.tap(130,310);page.touchscreen.tap(130,450);expect(page.locator('#searchName')).not_to_be_visible()
 page.touchscreen.tap(130,310);page.touchscreen.tap(130,310);expect(page.locator('#searchName')).to_be_visible()
 assert page.evaluate('window.trapClicks')==0 and page.evaluate('window.trapDowns')==0
 page.evaluate("document.getElementById('gestureTrap').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,detail:0}))");assert page.evaluate('window.trapClicks')==0
 page.mouse.click(130,310);assert page.evaluate('window.trapClicks')==0 and page.evaluate('window.trapDowns')==0
 page.wait_for_timeout(550);page.mouse.click(130,310);assert page.evaluate('window.trapClicks')==1 and page.evaluate('window.trapDowns')==1
 page.evaluate("document.getElementById('gestureTrap').remove()")
 page.locator('#hideButtonsBtn').click();page.locator('.sec-a ol').dblclick();expect(page.locator('#searchName')).to_be_visible();page.reload();expect(page.locator('#searchName')).to_be_visible();assert page.evaluate("localStorage.getItem('treino36_buttons_hidden')")=='0'
 assert not errors,errors
 browser.close();print('PASS: hidden mode and pupil persist; two nearby taps reveal after release without activating controls under the finger; clicks/pointerdowns suppressed only during transition; normal controls work afterwards; distant taps stay hidden; desktop double-click retained')
