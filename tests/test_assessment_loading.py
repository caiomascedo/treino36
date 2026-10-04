from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 pdf_requests=[]
 def route(r):
  u=urlparse(r.request.url)
  if 'jspdf' in r.request.url:
   pdf_requests.append(r.request.url)
   return # The PDF network never completes. Editing must still be available.
  path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='loading.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404,body='')
 context.route('**/*',route)
 page=context.new_page();page.goto('http://loading.test/')
 page.evaluate("""() => {localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino:{A:['Agachamento']},avaliacaoId:10,infoGuias:[{id:'f1',idade:'24',altura:'1.7',peso:'72'}]}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',idade:'24',altura:'1.7',treinoStudentIds:['a'],avaliacoes:[{id:11,data:'11/07/2026',peso:'72',peitoral:'95'}]}]));}""")
 page.reload();page.locator('#searchName').fill('Ana');page.locator('#studentEvaluationBtn').click()
 expect(page.locator('#obs-av-peso')).to_have_value('72',timeout=5000)
 page.locator('#obsAssessmentSections [data-assessment-section="medidas"]').click()
 expect(page.locator('#obs-av-peitoral')).to_have_value('95',timeout=5000)
 assert not pdf_requests,pdf_requests
 # A tap on the backdrop closes the window; a tap on its fields did not.
 page.mouse.click(2,2);expect(page.locator('#workoutObsDialog')).not_to_be_visible()
 page.locator('#studentEvaluationBtn').click();page.locator('#closeObsFocusBtn').click();expect(page.locator('#workoutObsDialog')).not_to_be_visible()
 page.locator('#listBtn').click()
 check=page.locator('.lista-select-student').bounding_box();name=page.locator('.lista-student-heading .aluno-nome').bounding_box();archive=page.locator('.archive-aluno-btn').bounding_box()
 assert check['width']<=16 and abs((check['y']+check['height']/2)-(name['y']+name['height']/2))<3
 assert archive['x']>name['x'] and archive['width']<=28
 page.locator('#closeModalBtn').click();page.locator('#assessmentsLibraryBtn').click()
 library=page.frame_locator('#assessmentLibraryFrame');expect(library.locator('.aluno-nome')).to_have_text('Ana',timeout=5000)
 assert not pdf_requests
 page.mouse.click(2,2);expect(page.locator('#assessmentLibraryDialog')).not_to_be_visible()
 # A previous cached page may have replaced assessments; offer the preserved link snapshot.
 page.evaluate("""() => {const records=JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'));localStorage.setItem('avaliacao_treino_antes_uniao',JSON.stringify({avaliacoes:records}));localStorage.setItem('avaliacao_fisica_alunos','[]');}""")
 page.goto('http://loading.test/avaliacao.html?embed=treino36-library&v=13')
 page.locator('#recoverAssessmentBackupBtn').click()
 expect(page.locator('.aluno-nome')).to_have_text('Ana')
 assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].peso")=='72'
 # Unreadable records must not be replaced with an empty list or a demo pupil.
 page.evaluate("localStorage.setItem('avaliacao_fisica_alunos','broken records')")
 page.goto('http://loading.test/avaliacao.html')
 expect(page.locator('#alunosList')).to_contain_text('Seus dados foram preservados')
 assert page.evaluate("localStorage.getItem('avaliacao_fisica_alunos')")=='broken records'
 browser.close();print('PASS: assessment fields/library independent of PDF network; backdrop/top close; compact inline selection; invalid records preserved')
