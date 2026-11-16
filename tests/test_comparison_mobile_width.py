from pathlib import Path
from urllib.parse import urlparse
import os
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if os.getenv('GIF_TEST_BROWSER')=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url);f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='edit.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('https://edit.test/');page.evaluate('TreinoStorage.ready');students=[{'student_id':'scroll','nome':'Maria Teste','treino_id':'now','treino':{'A':['Extensora '+str(i)+' — 3×12' for i in range(25)]},'titulos':{'A':'A. Atual'},'historicoTreinos':[{'workout_id':'old','name':'Anterior Maria','treino':{'A':['Remada '+str(i)+' — 4×10' for i in range(25)]},'titulos':{'A':'A. Anterior'}}]}];page.evaluate('(s)=>localStorage.setItem("treinoAlunos",JSON.stringify(s))',students);page.reload();page.evaluate('TreinoStorage.ready');page.wait_for_function('document.querySelector("#searchName").value==="Maria Teste"');baseline=page.evaluate('localStorage.getItem("treinoAlunos")');page.locator('#compareWorkoutBtn').click();dialog=page.locator('#compareWorkoutsDialog');surface=dialog.locator('.compare-scroll');header=dialog.locator('.compare-header');footer=dialog.locator('.dialog-actions');body=page.locator('#compareBody')
 baseline=page.evaluate('localStorage.getItem("treinoAlunos")')
 # Native selects must fit their column even with long pupil, title and timestamp labels.
 page.locator('#compareCurrentPicker option').first.evaluate("e=>e.textContent='CAPA ATUAL · Treino de Lauriane '+('Quadríceps e posteriores '.repeat(15))+' · Atualizado em 16/11/2026, 13:29'")
 for width in [320,390,430,844]:
  page.set_viewport_size({'width':width,'height':844})
  for fullscreen in [False,True]:
   active=dialog.evaluate('e=>e.classList.contains("compare-full-screen")')
   if active!=fullscreen:page.locator('#compareFullscreen').evaluate('e=>e.click()')
   for minimized in [False,True]:
    active=dialog.evaluate('e=>e.classList.contains("compare-options-collapsed")')
    if active!=minimized:page.locator('#compareMinimizeOptions').evaluate('e=>e.click()')
    surface.evaluate('e=>{e.scrollTop=0;e.scrollLeft=0}')
    dimensions=surface.evaluate('e=>({width:e.clientWidth,scrollWidth:e.scrollWidth})')
    assert dimensions['scrollWidth']<=dimensions['width']+1,(width,fullscreen,minimized,dimensions)
    rect=surface.bounding_box();page.mouse.move(rect['x']+rect['width']*.7,rect['y']+rect['height']*.7);page.mouse.wheel(350,400)
    page.wait_for_function('document.querySelector(".compare-scroll").scrollTop>100')
    assert surface.evaluate('e=>e.scrollLeft')==0
    for line in page.locator('.comparison-row').all()[:3]:
     box=line.bounding_box();assert box['x']>=rect['x']-1 and box['x']+box['width']<=rect['x']+rect['width']+1
    assert footer.bounding_box()['y']+footer.bounding_box()['height']<=844
 page.screenshot(path='/tmp/comparison-no-sideways.png')
 assert page.evaluate('localStorage.getItem("treinoAlunos")')==baseline
 assert not errors,errors
 b.close();print('PASS: no sideways overflow with long native-select labels at 320/390/430/844px, regular/fullscreen, selection expanded/collapsed; diagonal scroll remains vertical; footer and saved data preserved')
