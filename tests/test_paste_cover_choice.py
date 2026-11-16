"""Confirm the old-cover destination in both smart paste and the prefilled expanded editor."""
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
  if u.hostname=='paste.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:(errors.append(str(e)),print(str(e))));page.goto('https://paste.test/');page.evaluate('TreinoStorage.ready')
 students=[{'student_id':'ana','nome':'Ana Original','treino_id':'active','treinoProtegido':False,'treino':{'A':['Extensora — 3×12 [Vídeo: https://youtu.be/abcdefghijk]'],'B':['Rosca — 2×10']},'titulos':{'A':'A. Pernas'},'historicoTreinos':[]},{'student_id':'outro','nome':'Outro aluno','treino_id':'legacy-shared','treino':{'A':['Supino — 3×10']},'historicoTreinos':[{'workout_id':'legacy-shared','name':'Arquivo antigo','treino':{'A':['Remada — 4×10']}}]}]
 page.evaluate('(s)=>localStorage.setItem("treinoAlunos",JSON.stringify(s))',students);page.reload();page.evaluate('TreinoStorage.ready');page.wait_for_function('document.querySelector("#searchName").value==="Ana Original"')
 def records():return page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))')
 baseline=records()
 # This editor sets pasteEditingExisting; a replacement here used to skip archiving.
 page.locator('.sec-a .section-zoom-btn').click();page.locator('#pasteTextarea').fill('A. Novo treino\n1. Agachamento — 4×12');page.locator('#confirmPasteBtn').click()
 choice=page.locator('#pasteCoverChoiceDialog');expect(choice).to_be_visible();expect(choice).to_contain_text('Ana Original')
 assert records()==baseline
 choice.get_by_role('button',name='Cancelar',exact=True).click();expect(page.locator('#pasteModal')).to_be_visible();assert records()==baseline
 page.locator('#confirmPasteBtn').click();page.locator('#pasteArchiveYes').click()
 saved=records()[0];assert saved['treino_id']!='active';assert saved['historicoTreinos'][-1]['treino']==baseline[0]['treino'];assert saved['treino']['B']==baseline[0]['treino']['B'];expect(page.locator('.sec-a ol')).to_contain_text('Agachamento');assert 'abcdefghijk' not in saved['treino']['A'][0]
 page.locator('#saveBtn').click();assert len(records()[0]['historicoTreinos'])==1
 # Editing the new cover must leave the archived snapshot immutable.
 page.locator('.sec-a ol li').first.fill('Agachamento livre — 5×10');page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A[0].includes("5×10")')
 assert records()[0]['historicoTreinos'][0]['treino']==baseline[0]['treino']
 # Choosing No replaces the cover without adding an archive, and Undo still restores it.
 before_no=records()[0]
 page.locator('#fullTreinoBtn').click();page.locator('#pasteTextarea').fill('A. Substituir\n1. Afundo — 2×12');page.locator('#confirmPasteBtn').click();page.locator('#pasteArchiveNo').click()
 assert records()[0]['historicoTreinos']==before_no['historicoTreinos'], (records()[0]['historicoTreinos'],before_no['historicoTreinos']);assert records()[0]['treino_id']!=before_no['treino_id']
 page.locator('#undoBtn').click();assert records()[0]['treino']==before_no['treino']
 # An exact typed pupil name is sufficient; the correct cover is archived, even with reused legacy IDs.
 page.locator('#searchName').fill('Outro aluno')
 page.locator('#fullTreinoBtn').click();page.locator('#pasteTextarea').fill('A. Novo\n1. Puxada — 4×10');page.locator('#confirmPasteBtn').click();expect(choice).to_contain_text('Outro aluno');page.locator('#pasteArchiveYes').click()
 owner=records()[1];assert len(owner['historicoTreinos'])==2;assert owner['historicoTreinos'][-1]['treino']==baseline[1]['treino'];assert 'Puxada' in owner['treino']['A'][0]
 assert records()[0]['treino']==before_no['treino']
 page.locator('#fullTreinoBtn').click();page.locator('#pasteTextarea').fill('A. Não sobrescrever\n1. Extensora — 1×10');page.locator('#confirmPasteBtn').click()
 page.evaluate('()=>{const rows=JSON.parse(localStorage.getItem("treinoAlunos"));rows[1].treino.A=["Edição externa — 3×10"];localStorage.setItem("treinoAlunos",JSON.stringify(rows))}')
 changed=records();page.locator('#pasteArchiveYes').click();expect(page.locator('#pasteCoverChoiceStatus')).to_contain_text('A capa mudou');assert records()==changed
 assert not errors,errors
 b.close();print('PASS: prefilled editor confirms archive/replace/cancel; previous cover retained while new cover edits; save does not duplicate; undo, typed-name targeting and reused archive IDs work')
