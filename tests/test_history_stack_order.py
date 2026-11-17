"""Three successive new covers keep all ancestors and label the newest Anterior 1 everywhere."""
from pathlib import Path
from urllib.parse import urlparse,unquote
import os,json
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if os.getenv('GIF_TEST_BROWSER')=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 def route(r):
  u=urlparse(r.request.url);f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='history.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:(errors.append(str(e)),print(str(e))));page.goto('https://history.test/');page.evaluate('TreinoStorage.ready')
 page.evaluate('localStorage.setItem("treinoAlunos",JSON.stringify([{student_id:"ana",nome:"Ana Teste",treino_id:"base",treinoProtegido:false,treino:{A:["Ciclo zero — 3×12 [Vídeo: https://youtu.be/abcdefghijk]"]},titulos:{A:"A. Original"},historicoTreinos:[]}]))');page.reload();page.evaluate('TreinoStorage.ready');page.wait_for_function('document.querySelector("#searchName").value==="Ana Teste"')
 def student():return page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))[0]')
 originals=[]
 for n in range(1,4):
  before=student();originals.append(before['treino'])
  page.locator('#fullTreinoBtn').click();page.locator('#pasteTextarea').fill(f'A. Ciclo {n}\n1. Exercício ciclo {n} — 4×12');page.locator('#confirmPasteBtn').click();page.locator('#pasteArchiveYes').click();page.locator('#saveBtn').click()
  saved=student();assert len(saved['historicoTreinos'])==n
  assert [v['treino'] for v in saved['historicoTreinos']]==originals
  assert len({v['workout_id'] for v in saved['historicoTreinos']})==n
  # A reload between updates must not reduce the retained stack.
  page.reload();page.evaluate('TreinoStorage.ready');page.wait_for_function('document.querySelector("#searchName").value==="Ana Teste"')
 baseline=student()
 page.locator('#searchName').focus()
 rows=page.locator('.name-suggestion-subitem[data-type="history"]')
 assert rows.count()==3
 for i in range(3):
  expect(rows.nth(i).locator('.sub-badge')).to_have_text('◷ Ant '+str(i+1))
  assert rows.nth(i).get_attribute('data-history-index')==str(2-i)
 box=page.locator('#nameSuggestions').bounding_box();last=rows.last.bounding_box();assert last['y']+last['height']<=box['y']+box['height']+1
 rows.nth(1).click();expect(page.locator('.cover-badge')).to_contain_text('EDITANDO ANTERIOR 2');expect(page.locator('.sec-a ol')).to_contain_text('Exercício Ciclo 1')
 page.locator('#backToWorkoutCover').click();page.locator('#historyWorkoutBtn').click()
 expect(page.locator('#historyStackSummary')).to_contain_text('3 anteriores')
 opts=page.locator('#historyVersion option[data-history-student="ana"]')
 assert opts.count()==3
 for rank in range(1,4):
  expect(opts.nth(rank-1)).to_contain_text('Anterior '+str(rank)+' (arquivado)')
  page.locator('#historyVersion').select_option(index=rank)
  expect(page.locator('#historyStudentName')).to_contain_text('Anterior '+str(rank)+' · arquivado')
  text='Exercício Ciclo '+str(3-rank) if rank<3 else 'Ciclo zero'
  expect(page.locator('#historyVersionText')).to_contain_text(text)
 page.locator('#workoutHistoryDialog [data-close]').click()
 page.locator('#compareWorkoutBtn').click();page.locator('#chooseComparePrevious').click()
 choices=page.locator('#comparePreviousChoice .compare-version-option')
 for rank in range(1,4):
  choice=choices.filter(has_text='Anterior '+str(rank)+' (arquivado)');assert choice.count()==1
  assert json.loads(unquote(choice.get_attribute('data-choice')[8:]))==['ana',3-rank]
 page.locator('#comparePreviousChoice .compare-version-cancel').click();page.locator('#compareWorkoutsDialog .dialog-actions [data-close]').click()
 page.locator('#moreOptions > summary').click()
 with page.expect_download() as dl:page.locator('#exportBtn').click()
 backup=json.loads(Path(dl.value.path()).read_text());assert backup['alunos'][0]['historicoTreinos']==baseline['historicoTreinos']
 assert student()['historicoTreinos']==baseline['historicoTreinos']
 # Older JSON files can reuse a workout ID; merging them must not collapse distinct previous workouts.
 legacy={'student_id':'legacy','nome':'Legado','treino_id':'legacy-cover','treino':{'A':['Capa atual — 3×12']},'historicoTreinos':[{'workout_id':'shared','name':'Primeiro antigo','treino':{'A':['Primeiro — 2×10']}},{'workout_id':'shared','name':'Segundo antigo','treino':{'A':['Segundo — 3×10']}}]}
 page.evaluate('(s)=>localStorage.setItem("treinoAlunos",JSON.stringify([s]))',legacy);page.reload();page.evaluate('TreinoStorage.ready');page.wait_for_function('document.querySelector("#searchName").value==="Legado"')
 incoming=dict(legacy,historicoTreinos=[{'workout_id':'shared','name':'Terceiro antigo','treino':{'A':['Terceiro — 4×10']}}])
 page.locator('#moreOptions > summary').click()
 with page.expect_file_chooser() as chooser:page.locator('#importBtn').click()
 chooser.value.set_files({'name':'legacy.json','mimeType':'application/json','buffer':json.dumps([incoming]).encode()})
 page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].historicoTreinos.length===3')
 assert [v['treino']['A'][0] for v in student()['historicoTreinos']]==['Primeiro — 2×10','Segundo — 3×10','Terceiro — 4×10']
 page.locator('#historyWorkoutBtn').click();page.locator('#historyVersion').select_option(index=2);page.locator('#compareSelectedVersion').click();expect(page.locator('.comparison-previous-line').first).to_have_text('Segundo — 3×10')
 assert not errors,errors
 b.close();print('PASS: three sequential saved/reloaded updates retain all ancestors; Anterior 1/2/3 consistently newest-first in search, history, comparison and archive editor; exact content/IDs/media and JSON preserved')
