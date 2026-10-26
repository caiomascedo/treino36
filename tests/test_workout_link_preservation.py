"""Custom URLs stay attached to prescriptions through all existing workout copy tools."""
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
VIDEO='https://youtu.be/AbC_123?list=BigCASE&start=30'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 context.add_init_script("window.copied=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>copied.push(text),readText:async()=>copied.at(-1)||''}});document.execCommand=(cmd)=>{if(cmd==='copy'){copied.push(document.activeElement.value);return true;}return false;}")
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='links.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://links.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate("video=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'ana',nome:'Ana',treino_id:'ana-now',treino:{A:['Agachamento — 3×12 [Vídeo: '+video+']']},titulos:{A:'A. Pernas'}},{student_id:'bia',nome:'Bia',treino_id:'bia-now',treino:{A:['Supino — 3×10']}}]))",VIDEO)
 page.reload()
 def stored(name,section):return page.evaluate("([name,section])=>JSON.parse(localStorage.getItem('treinoAlunos')).find(a=>a.nome===name).treino[section]||[]",[name,section])
 def linked(section,count=1):
  anchors=page.locator('.sec-'+section.lower()+' ol .exercise-video');expect(anchors).to_have_count(count)
  for a in anchors.all():assert a.get_attribute('href')==VIDEO
 def open_section(section):page.locator('#mainContainer .workout-grip[data-section='+section+']').click()
 def choose(name):page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="'+name+'"] .aluno-nome').click()
 linked('A');choose('Ana')
 # Copy the individual exercise, duplicate and paste using its own action menu.
 page.locator('.sec-a .main-exercise-grip').first.click();page.locator('#copyExerciseBtn').click();page.wait_for_function('copied.length>0');assert VIDEO in page.evaluate('copied.at(-1)')
 page.locator('#duplicateExerciseBtn').click();linked('A',2)
 page.locator('.sec-a .main-exercise-grip').last.click();page.locator('#pasteExerciseBtn').click();linked('A',3)
 # Move the prescription to B, then reorder the section with the normal arrow gesture.
 page.locator('.sec-a .main-exercise-grip').first.click();page.get_by_role('button',name='Mover para seção B',exact=True).click();linked('B')
 page.locator('#mainContainer .workout-grip[data-section=B]').press('ArrowUp');linked('A');linked('B',2)
 # Copy whole-section rich content; duplication and the portable clipboard keep URLs.
 open_section('A');page.locator('#sectionActionsDialog [data-copy]').click();page.wait_for_function('copied.length>1');assert VIDEO in page.evaluate('copied.at(-1)');page.locator('#sectionActionsDialog [data-close]').click()
 open_section('A');page.get_by_role('combobox',name='Destino da seção duplicada').select_option('C');page.locator('#sectionActionsDialog [data-duplicate]').click();linked('C')
 open_section('D');page.locator('#sectionActionsDialog [data-paste]').click();linked('D')
 # Plain section copy -> regular Cola Inteligente, bypassing the internal rich clipboard.
 page.locator('.sec-a .copy-section-btn').click();assert VIDEO in page.evaluate('copied.at(-1)')
 page.locator('.sec-e .colar-btn').click();page.locator('#pasteTextarea').fill(page.evaluate('copied.at(-1)'));page.locator('#confirmPasteBtn').click();linked('E')
 page.reload();linked('A');linked('E');assert VIDEO in stored('Ana','A')[0]
 # Copy one section from the pupil list, while another pupil is selected.
 choose('Bia');page.locator('.sec-a .copy-aluno-btn').click();page.locator('.select-aluno-btn[data-nome="Ana"]').click();linked('A')
 page.wait_for_function("JSON.parse(localStorage.getItem('treinoAlunos')).find(a=>a.nome==='Bia').treino.A[0].includes('BigCASE')")
 page.reload();linked('A')
 # Copy the complete workout between pupils, preserving the URL in every section.
 page.locator('#copyBtn').click();page.locator('#origemSelect').select_option('Ana');page.locator('#destinoInput').fill('Bia');page.locator('#confirmCopyBtn').click();linked('A');linked('E')
 assert VIDEO in stored('Bia','E')[0]
 page.locator('#pdfBtn').click()
 for link in page.locator('#pdfBody .yt-link').all():
  parsed=urlparse(link.get_attribute('href'));query=parse_qs(parsed.query)
  assert parsed.path=='/r/yt' and query['aluno']==['Bia'] and query['url']==[VIDEO]
 page.locator('#closePdfViewer').click()
 # Text expansion exposes a portable link and reapplying edited text retains it.
 page.locator('.sec-a .section-zoom-btn').click()
 assert VIDEO in page.locator('#pasteTextarea').input_value()
 page.locator('#pasteTextarea').fill(page.locator('#pasteTextarea').input_value().replace('3×12','4×10'));page.locator('#confirmPasteBtn').click();linked('A')
 assert not errors,errors
 browser.close();print('PASS: URL case/query preserved on reload, exercise copy/paste/duplicate/move, section reorder/copy/paste/duplicate, plain text paste, pupil-list copy, complete cross-pupil copy and text editing')
