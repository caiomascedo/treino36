"""Optional per-clip colors, retained GIF position, and copying nonempty days only."""
import json, os
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
ENGINE=os.getenv('GIF_TEST_BROWSER','chromium')
assets=json.loads((ROOT/'gymfaster-catalog.json').read_text())['videos'][:2]
def line(name,index=0):return name+' — 3×12 [GIFs: '+assets[index]['url']+']'
training={s:[] for s in 'ABCDEF'}
training.update(A=[line('Alongamento A')],B=[line('Alongamento B')],C=[line('Primeiro movimento'),line('Segundo movimento'),
 'Agachamento Sumô C/ Pegada Neutra + Stiff Neutra — 4×10 + 10 [GIFs: '+' | '.join(a['url'] for a in assets)+']',
 *[line('Outro movimento '+str(i)) for i in range(9)]])
data=[{'student_id':'position-one','nome':'Teste posição','treino':training,'titulos':{s:s+'. '+('Pernas' if s=='C' else 'Vazio '+s if s in 'DEF' else 'Treino '+s) for s in 'ABCDEF'}},
 {'student_id':'position-two','nome':'Outro aluno','treino':{'A':[line('Exercício do outro aluno')]},'titulos':{'A':'A. Outro'}}]
with sync_playwright() as p:
 browser=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if ENGINE=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url)
  if u.scheme in ['blob','data']:r.continue_();return
  path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='gif-view.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route)
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://gif-view.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate('(d)=>localStorage.setItem("treinoAlunos",JSON.stringify(d))',data)
 page.reload();page.evaluate('TreinoStorage.ready');page.locator('#searchName').fill('Teste posição');page.locator('#searchName').press('Enter');page.keyboard.press('Escape')
 page.locator('#workoutGifsBtn').click();dialog=page.locator('#workoutGifDialog')
 section=dialog.get_by_role('combobox',name='Treino para o GIF');section.select_option('C')
 target=dialog.locator('.gif-card').filter(has=page.locator('strong',has_text='3a. Agachamento Sumô'))
 other=dialog.locator('.gif-card').filter(has=page.locator('strong',has_text='3b. Stiff Neutra'))
 expect(target).to_have_count(1);target.locator('summary').click()
 theme=dialog.get_by_role('combobox',name='Biblioteca dos GIFs');theme.select_option('cm')
 video=target.locator('video');expect(video).to_have_attribute('data-video-invert','false')
 color=target.get_by_label('Cor deste vídeo',exact=True)
 color.select_option('invert');expect(video).to_have_attribute('data-video-invert','true')
 expect(other.locator('video')).to_have_attribute('data-video-invert','false')
 color.select_option('original');assert video.evaluate('v=>getComputedStyle(v).filter')=='none'
 # Return to the same exercise after editing the underlying prescription.
 text=target.locator('.gif-card-text')
 text.evaluate('e=>{const d=document.getElementById("workoutGifDialog");d.scrollTop+=e.getBoundingClientRect().top-d.getBoundingClientRect().top-110}')
 page.wait_for_timeout(100)
 before=text.bounding_box()['y']-dialog.bounding_box()['y']
 dialog.get_by_role('button',name='Fechar',exact=True).click()
 page.locator('.sec-c ol>li .bold').first.evaluate("e=>{e.textContent='Primeiro movimento atualizado';e.dispatchEvent(new Event('input',{bubbles:true}))}")
 page.locator('#workoutGifsBtn').click();expect(section).to_have_value('C');expect(theme).to_have_value('cm')
 expect(dialog.locator('strong',has_text='Primeiro movimento atualizado')).to_have_count(1)
 page.wait_for_timeout(100)
 assert abs((text.bounding_box()['y']-dialog.bounding_box()['y'])-before)<5,(before,text.bounding_box(),dialog.bounding_box(),page.evaluate('sessionStorage.getItem("treinoGifViewV1")'))
 assert target.locator('.gif-card-options').evaluate('e=>e.open')
 assert dialog.evaluate('e=>e.scrollWidth<=e.clientWidth')
 color.select_option('invert');dialog.get_by_role('button',name='Fechar',exact=True).click()
 # Student contexts are isolated; reloading retains the selected day and clip choice.
 page.locator('#searchName').fill('Outro aluno');page.locator('#searchName').press('Enter');page.keyboard.press('Escape')
 page.locator('#workoutGifsBtn').click();expect(section).to_have_value('A');dialog.get_by_role('button',name='Fechar',exact=True).click()
 page.locator('#searchName').fill('Teste posição');page.locator('#searchName').press('Enter');page.keyboard.press('Escape')
 page.locator('#workoutGifsBtn').click();expect(section).to_have_value('C');expect(video).to_have_attribute('data-video-invert','true')
 dialog.get_by_role('button',name='Fechar',exact=True).click();page.reload();page.evaluate('TreinoStorage.ready')
 page.locator('#searchName').fill('Teste posição');page.locator('#searchName').press('Enter');page.keyboard.press('Escape');page.locator('#workoutGifsBtn').click()
 expect(section).to_have_value('C');expect(video).to_have_attribute('data-video-invert','true')
 expect(other.locator('video')).to_have_attribute('data-video-invert','false')
 dialog.get_by_role('button',name='Fechar',exact=True).click()
 # Clipboard export includes valid sections, and starts including D as soon as it has an exercise.
 page.evaluate("document.execCommand=(command)=>{if(command==='copy')window.__copied=document.activeElement.value;return true}")
 page.locator('#copyFullTreinoBtn').evaluate('b=>b.click()')
 copied=page.evaluate('__copied');assert 'c. pernas' in copied.lower() and 'agachamento sumô' in copied.lower(),copied
 assert all((s+'. Vazio '+s).lower() not in copied.lower() for s in 'DEF')
 page.locator('.sec-d ol').evaluate("e=>e.innerHTML='<li><span class=bold>Agora existe um exercício D</span> — 3×10</li>'")
 page.locator('#copyFullTreinoBtn').evaluate('b=>b.click()');copied=page.evaluate('__copied');assert 'd. vazio d' in copied.lower() and 'agora existe' in copied.lower()
 assert all((s+'. Vazio '+s).lower() not in copied.lower() for s in 'EF')
 page.evaluate("for(const s of document.querySelectorAll('.section>ol'))s.innerHTML='<li>Seção vazia</li>';window.__copied=null")
 page.locator('#copyFullTreinoBtn').evaluate('b=>b.click()')
 assert page.evaluate('__copied') is None
 assert not errors,errors
 browser.close();print('PASS',ENGINE,': per-video original/optional colors, independent student/day/exercise scroll context after edits and reload; clipboard skips only empty sections')
