from pathlib import Path
from urllib.parse import urlparse
import os,json
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if os.getenv('GIF_TEST_BROWSER')=='webkit' else p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844},accept_downloads=True)
 def route(r):
  u=urlparse(r.request.url);f=ROOT/u.path.lstrip('/')
  if f.is_dir():f/='index.html'
  if u.hostname=='app.test' and f.is_file():r.fulfill(body=f.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json'}.get(f.suffix,'text/html'))
  else:r.fulfill(status=404)
 c.route('**/*',route);page=c.new_page();errors=[];page.on('pageerror',lambda e:(errors.append(str(e)),print(str(e))));page.goto('https://app.test/');page.evaluate('TreinoStorage.ready')
 seed=[{'student_id':'ana','nome':'Ana','treino_id':'active','treinoProtegido':False,'treino':{'A':['Supino — 3×12 [Vídeo: https://youtu.be/abcdefghijk]'],'B':['Remada — 4×10']},'titulos':{'A':'A. Peito','B':'B. Costas'},'historicoTreinos':[{'workout_id':'old','name':'Anterior','treino':{'A':['Supino — 3×12','Flexora — 4×10','Afundo — 3×10']}}]}]
 page.evaluate('(s)=>localStorage.setItem("treinoAlunos",JSON.stringify(s))',seed);page.reload();page.evaluate('TreinoStorage.ready');page.wait_for_function('document.querySelector("#searchName").value==="Ana"')
 def records():return page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))')
 def favorites():return page.evaluate('JSON.parse(localStorage.getItem("treinoSectionFavoritesV1")||"[]")')
 baseline=records()
 # Paste whose browser selection still points to the main document must go to the textarea.
 page.locator('#fullTreinoBtn').click();page.evaluate('()=>{const area=document.querySelector(".sec-a ol"),range=document.createRange();range.selectNodeContents(area);getSelection().removeAllRanges();getSelection().addRange(range);const e=new Event("paste",{bubbles:true,cancelable:true});Object.defineProperty(e,"clipboardData",{value:{getData:()=>"A. Rascunho\\n1. Extensora — 2×10"}});area.dispatchEvent(e)}')
 expect(page.locator('#pasteTextarea')).to_have_value('A. Rascunho\n1. Extensora — 2×10');assert records()==baseline;page.locator('#cancelPasteBtn').click()
 # Add in a previously missing slot, including a gap, and undo via the footer.
 page.locator('#compareWorkoutBtn').click();missing=page.locator('.comparison-current-line').nth(2);expect(missing).to_have_attribute('contenteditable','true');missing.evaluate('line=>{const r=document.createRange();r.selectNodeContents(document.querySelector(".sec-a ol"));getSelection().removeAllRanges();getSelection().addRange(r);const e=new Event("paste",{bubbles:true,cancelable:true});Object.defineProperty(e,"clipboardData",{value:{getData:()=>"Afundo novo — 5×10"}});line.dispatchEvent(e)}');page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A.length===2');expect(page.locator('.sec-a ol')).to_contain_text('Afundo Novo');assert all(isinstance(v,str) for v in records()[0]['treino']['A'])
 page.locator('#compareUndoFooter').click();page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A.length===1');page.locator('.comparison-current-line').first.fill('');expect(page.locator('#compareUndoFooter')).to_be_enabled();page.locator('#compareUndoFooter').click();expect(page.locator('.comparison-current-line').first).to_have_text('Supino — 3×12');page.locator('#compareWorkoutsDialog .dialog-actions [data-close]').click()
 # Picking a person's section from the list inside Cola fills only the editor.
 before_list=records();page.locator('.sec-b .colar-btn').click();page.locator('#pasteFavoriteList').click();person=page.locator('#copyStudentList .aluno-list-item').first;person.locator('.copy-source-section').select_option('A');person.locator('.select-aluno-btn').click();expect(page.locator('#pasteTextarea')).to_have_value('B. Peito\n1. Supino — 3×12');assert records()==before_list;page.locator('#cancelPasteBtn').click()
 page.locator('#compareWorkoutBtn').click();page.locator('.comparison-current-line').nth(2).fill('Afundo novo — 5×10');page.locator('#applyCompareEdit').click();assert len(records()[0]['treino']['A'])==2 and all(isinstance(v,str) for v in records()[0]['treino']['A'])
 # Section snapshots, scope filters and pins are independent of pupil favourites.
 filter=page.locator('#sectionFavoritesBar [data-scope]');filter.select_option('A');page.locator('#sectionFavoritesBar [data-add]').click();assert len(favorites())==1 and favorites()[0]['section']=='A'
 filter.select_option('B');page.locator('#sectionFavoritesBar [data-add]').click();assert len(favorites())==2;assert page.locator('#sectionFavoritesBar .section-favorite-tab').count()==1;expect(page.locator('#sectionFavoritesBar .section-favorite-tab')).to_contain_text('B · Ana')
 filter.select_option('A');page.locator('#sectionFavoritesBar .section-favorite-tab button').nth(1).click();assert next(v for v in favorites() if v['section']=='A')['pinned'];page.locator('#sectionFavoritesBar [data-sticky]').click();expect(page.locator('#sectionFavoritesBar')).to_have_class('section-favorites is-sticky')
 page.locator('.sec-b .copy-aluno-btn').click();picker=page.locator('.section-favorite-picker');expect(picker.locator('select')).to_have_value('B');assert picker.locator('.section-favorite-tab').count()==1;picker.locator('select').select_option('all');assert picker.locator('.section-favorite-tab').count()==2
 page.once('dialog',lambda d:d.accept());picker.locator('.section-favorite-tab button').filter(has_text='A · Ana').click();assert records()[0]['treino']['B']==records()[0]['treino']['A'];assert 'abcdefghijk' in records()[0]['treino']['B'][0]
 # Removal requires confirmation; cancelling keeps the record and main workout unchanged.
 filter.select_option('A');close=page.locator('#sectionFavoritesBar .section-favorite-tab button').last;page.once('dialog',lambda d:d.dismiss());close.click();assert len(favorites())==2;page.once('dialog',lambda d:d.accept());close.click();assert len(favorites())==1 and favorites()[0]['section']=='B'
 # The title/grip menu can save and pin an entire section snapshot.
 page.locator('.sec-a .workout-grip').click();page.locator('#sectionActionsDialog [data-pin-favorite]').click();assert any(v['section']=='A' and v['pinned'] for v in favorites());page.locator('#sectionActionsDialog [data-close]').click()
 # The exercise grip also favourites/pins its whole section and clears stale text selection.
 before_menu=favorites();page.locator('.sec-a .main-exercise-grip').first.click();expect(page.locator('#exerciseActionsDialog [data-favorite-section]')).to_contain_text('treino A');page.once('dialog',lambda d:d.dismiss());page.locator('#exerciseActionsDialog [data-favorite-section]').click();assert favorites()==before_menu;page.locator('#exerciseActionsDialog [data-pin-favorite-section]').click();assert not next(v for v in favorites() if v['section']=='A')['pinned'];assert page.evaluate('getSelection().toString()')=='';page.locator('#exerciseActionsDialog button').filter(has_text='Fechar').click()
 # The person-copy dialog must fit the phone without lateral movement.
 page.locator('.sec-b .copy-aluno-btn').click();row=page.locator('#copyStudentList .aluno-list-item').first;row.locator('.copy-source-section').select_option('A');expect(row.locator('.copy-favorite-btn')).to_have_text('★');page.once('dialog',lambda d:d.dismiss());row.locator('.copy-favorite-btn').click();page.screenshot(path='/tmp/copy-favorites-layout.png');page.locator('.copy-source-controls select').first.evaluate('e=>e.options[0].textContent="Versão muito longa ".repeat(20)')
 for width in [320,390]:
  page.set_viewport_size({'width':width,'height':844});assert page.locator('#copyStudentList').evaluate('e=>e.scrollWidth<=e.clientWidth+1');assert page.locator('#modalContent').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
 page.locator('#closeModalBtn').click()
 # Normal undo remains visible; the preference only applies to hidden-button mode.
 expect(page.locator('.sec-a .section-undo-btn')).to_be_visible();page.locator('#moreOptions > summary').click();expect(page.locator('#showSectionUndo')).not_to_be_checked();page.locator('#showSectionUndo').check();page.locator('#moreOptions > summary').click();page.locator('#hideButtonsBtn').click();expect(page.locator('.sec-a .section-undo-btn')).to_be_visible();page.locator('.sec-a ol').dblclick();page.wait_for_timeout(550);page.locator('#moreOptions > summary').click();page.locator('#showSectionUndo').uncheck();page.locator('#moreOptions > summary').click();page.locator('#hideButtonsBtn').click();expect(page.locator('.sec-a .section-undo-btn')).not_to_be_visible();page.locator('.sec-a ol').dblclick();page.wait_for_timeout(550)
 # Snapshot data is included in the real JSON backup and restored on confirmation.
 saved=favorites();page.locator('#moreOptions > summary').click()
 with page.expect_download() as dl:page.locator('#exportBtn').click()
 backup=json.loads(Path(dl.value.path()).read_text());assert backup['treinos_favoritos']==saved
 page.evaluate('()=>{localStorage.setItem("treinoAlunos","[]");localStorage.setItem("treinoSectionFavoritesV1","[]");localStorage.setItem("treinoSectionFavoritesPinnedV1","0");localStorage.setItem("avaliacao_fisica_alunos","[]")}');page.reload();page.evaluate('TreinoStorage.ready');page.locator('#moreOptions > summary').click()
 with page.expect_file_chooser() as chooser:page.locator('#importBtn').click()
 chooser.value.set_files({'name':'favorites.json','mimeType':'application/json','buffer':json.dumps(backup).encode()});page.locator('#confirmCompleteBackupImport').click();assert favorites()==saved;expect(page.locator('#sectionFavoritesBar')).to_have_class('section-favorites is-sticky')
 page.evaluate('()=>{localStorage.setItem("treinoAlunos","[]");localStorage.setItem("treinoSectionFavoritesV1","[]")}');page.reload();page.evaluate('TreinoStorage.ready');page.locator('#moreOptions > summary').click()
 library_only=dict(backup,alunos=[],avaliacoes=[])
 with page.expect_file_chooser() as chooser:page.locator('#importBtn').click()
 chooser.value.set_files({'name':'library-only.json','mimeType':'application/json','buffer':json.dumps(library_only).encode()});page.locator('#confirmCompleteBackupImport').click();assert favorites()==saved and records()==[]
 assert not errors,errors;b.close();print('PASS: modal paste isolation, editable missing comparison rows + autosave/undo, section favourites/filter/cross-copy/pins/confirmed removal/menu and JSON roundtrip; mobile chooser bounds; hidden-mode undo preference')
