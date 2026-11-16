"""A pasted replacement archives the cover and remains reversible after saving/switching pupils."""
from pathlib import Path
from urllib.parse import urlparse
import os, json
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if os.getenv('GIF_TEST_BROWSER')=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':1100,'height':850},accept_downloads=True)
 def route(r):
  u=urlparse(r.request.url);f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='paste.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:(errors.append(str(e)),print(str(e))));page.goto('https://paste.test/');page.evaluate('TreinoStorage.ready')
 students=[{'student_id':'ana','nome':'Ana Original','treino_id':'cover-old','treinoNome':'Ciclo anterior','treinoProtegido':False,'validadeTreino':{'treinoId':'cover-old','start':'2026-11-16','until':'2026-12-16'},'treino':{'A':['Extensora — 3×12 [Vídeo: https://youtu.be/abcdefghijk]'],'B':['Rosca — 2×10']},'titulos':{'A':'A. Pernas','B':'B. Braços'},'obsGuias':[{'id':'note','texto':'Não alterar'}],'historicoTreinos':[{'workout_id':'older','name':'Muito antigo','treino':{'A':['Remada — 4×10']},'edited_at':'2026-11-10T10:00:00Z','revisoes':[{'treino':{'A':['Remada — 3×10']}}]}]}, {'student_id':'outro','nome':'Outro aluno','treino_id':'other','treino':{'A':['Supino — 3×10']}}]
 page.evaluate('(s)=>localStorage.setItem("treinoAlunos",JSON.stringify(s))',students);page.reload();page.evaluate('TreinoStorage.ready');page.wait_for_function('document.querySelector("#searchName").value==="Ana Original"')
 def records():return page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))')
 baseline=records()
 page.locator('#fullTreinoBtn').click();page.locator('#pasteTextarea').fill('A. Novo ciclo\n1. Agachamento — 4×12\n2. Afundo — 3×10\nB. Costas\n1. Puxada — 4×10');page.locator('#confirmPasteBtn').click()
 assert len(records()[0]['historicoTreinos'])==2
 assert records()[0]['historicoTreinos'][-1]['treino']==baseline[0]['treino']
 assert records()[0]['historicoTreinos'][-1]['workout_id']=='cover-old'
 # Explicit save used to reset undo history.
 page.locator('#saveBtn').click();saved=records()[0]
 page.locator('#undoBtn').click();expect(page.locator('.sec-a ol')).to_contain_text('Extensora')
 assert records()[0]['treino']==baseline[0]['treino']
 assert records()[0]['historicoTreinos']==baseline[0]['historicoTreinos']
 assert records()[0]['treino_id']=='cover-old'
 assert records()[0]['validadeTreino']==baseline[0]['validadeTreino']
 assert records()[0]['obsGuias']==baseline[0]['obsGuias']
 page.locator('#redoBtn').click();expect(page.locator('.sec-a ol')).to_contain_text('Agachamento')
 assert records()[0]['treino']==saved['treino'] and records()[0]['historicoTreinos']==saved['historicoTreinos']
 # Switching pupils must still allow recovering the last mistaken paste and its owner name.
 page.locator('#searchName').fill('Outro aluno');page.locator('.name-suggestion-load').filter(has_text='Outro aluno').click()
 expect(page.locator('.sec-a ol')).to_contain_text('Supino')
 page.locator('#undoBtn').click();expect(page.locator('#searchName')).to_have_value('Ana Original');expect(page.locator('.sec-a ol')).to_contain_text('Extensora')
 assert records()[0]['treino']==baseline[0]['treino'] and records()[1]==baseline[1]
 page.locator('#redoBtn').click()
 # A section paste is one undo step and preserves every other section.
 before_section=records()[0]
 page.locator('.colar-btn[data-section="A"]').click();page.locator('#pasteTextarea').fill('A. Teste seção\n1. Mesa flexora unilateral — 3×15');page.locator('#confirmPasteBtn').click()
 assert len(records()[0]['historicoTreinos'])==len(before_section['historicoTreinos'])+1
 assert records()[0]['treino']['B']==before_section['treino']['B']
 page.locator('#undoBtn').click()
 assert records()[0]['treino']==before_section['treino'] and records()[0]['historicoTreinos']==before_section['historicoTreinos']
 # Export and restore the actual JSON; preserve archive IDs, revisions and media markers.
 page.locator('#moreOptions > summary').click()
 with page.expect_download() as dl:page.locator('#exportBtn').click()
 backup=json.loads(Path(dl.value.path()).read_text());assert backup['alunos'][0]['treino']==records()[0]['treino'];assert backup['alunos'][0]['historicoTreinos']==records()[0]['historicoTreinos']
 page.evaluate('()=>{localStorage.setItem("treinoAlunos","[]");localStorage.setItem("avaliacao_fisica_alunos","[]")}');page.reload();page.evaluate('TreinoStorage.ready');page.locator('#moreOptions > summary').click()
 with page.expect_file_chooser() as chooser:page.locator('#importBtn').click()
 chooser.value.set_files({'name':'roundtrip.json','mimeType':'application/json','buffer':json.dumps(backup).encode()})
 expect(page.locator('#completeBackupImportDialog')).to_be_visible();page.locator('#confirmCompleteBackupImport').click()
 restored=records()[0];assert restored['treino']==backup['alunos'][0]['treino'];assert restored['historicoTreinos']==backup['alunos'][0]['historicoTreinos'];assert restored['obsGuias']==baseline[0]['obsGuias']
 assert not errors,errors
 b.close();print('PASS: atomic full paste archives an unprotected cover; save/undo/redo and wrong-pupil recovery preserve names, media, unrelated data; real JSON download/import retains current/archive/revisions')
