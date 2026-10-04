from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='history.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404,body='')
 context.route('**/*',route);page=context.new_page();page.goto('http://history.test/')
 def seed(dob,duplicate_link=False):
  page.evaluate("""args=>{
   const birth=args.dob?'01/01/2000':'';
   localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Aluno teste',avaliacaoId:20,treino:{A:['Agachamento 3x10']},historicoTreinos:[],infoGuias:[{id:'f1',nomeCompleto:'Aluno Teste',dataNasc:birth,peso:'71',idade:'24',altura:'1.75'}]}]));
   localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:20,nome:'Aluno Teste',nasc:birth,idade:'24',altura:'1.75',sexo:'M',pesoAtual:'71',pesoAtualAvaliacaoId:21,treinoStudentIds:['a'],avaliacoes:[{id:21,data:'03/10/2026',peso:'71',resumo:'Anotação recente',protocolo:'jp7'}]},{id:10,nome:'Aluno Teste',nasc:birth,idade:'24',altura:'1.75',sexo:'F',treinoStudentIds:args.duplicate?['a']:[],avaliacoes:[{id:11,data:'11/07/2026',peso:'74.50',biceps:'30 / 29',triceps:'14',protocolo:'jp7',fotoF:'data:image/png;base64,aW1hZ2U='}]}]));
  }""",{'dob':dob,'duplicate':duplicate_link})
  page.reload()
 def assertions():
  expect(page.locator('#obsAssessmentHistory option')).to_have_count(2)
  expect(page.locator('#obsAssessmentDate')).to_have_value('2026-10-03')
  page.locator('#obsAssessmentHistory').select_option('11')
  expect(page.locator('#obsAssessmentDate')).to_have_value('2026-07-11')
  expect(page.locator('#obs-av-peso')).to_have_value('74.50')
  expect(page.locator('#infoPeso')).to_have_value('71')
  expect(page.locator('#fichaAssessmentDate')).to_have_text('Avaliação: 03/10/2026')
  expect(page.locator('#obsAssessmentSex')).to_have_value('F')
  page.locator('#obsAssessmentHistory').select_option('21');expect(page.locator('#obs-av-peso')).to_have_value('71')
  page.locator('#obsAssessmentHistory').select_option('11')
  page.locator('#obsAssessmentSections [data-assessment-section="medidas"]').click();expect(page.locator('#obs-av-biceps')).to_have_value('30 / 29');page.locator('#obs-av-biceps').fill('31 / 30')
  expect(page.locator('#infoPeso')).to_have_value('71')
  data=page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))")
  assert len(data)==1 and len(data[0]['avaliacoes'])==2
  assert data[0]['id']==10 and data[0]['pesoAtual']=='71'
  assert next(a for a in data[0]['avaliacoes'] if a['id']==21)['resumo']=='Anotação recente'
  assert next(a for a in data[0]['avaliacoes'] if a['id']==11)['fotoF']=='data:image/png;base64,aW1hZ2U='
  student=page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0]")
  assert student['avaliacaoId']==10 and student['treino']['A']==['Agachamento 3x10']
 seed(True)
 page.locator('#searchName').fill('Aluno teste');page.locator('#studentEvaluationBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click();assertions()
 page.locator('#workoutObsDialog [data-close]').click();page.locator('#assessmentsLibraryBtn').click()
 library=page.frame_locator('#assessmentLibraryFrame');library.locator('.aluno-nome').click();library.locator('.aluno-content > .assessment-tabs [data-section="avaliacoes"]').click();library.locator('#av-item-11 .av-header').click();library.locator('#av-item-11 .assessment-tabs [data-section="medidas"]').click()
 expect(library.locator('#biceps-10-11')).to_have_value('31 / 30')
 page.locator('#assessmentLibraryDialog [data-close]').click()
 # Without birth dates, no automatic merge. Explicit confirmation also repairs duplicate bindings.
 seed(False,True);page.locator('#assessmentsLibraryBtn').click();library=page.frame_locator('#assessmentLibraryFrame')
 if 'active' not in library.locator('[data-aluno-card="10"]').get_attribute('class').split():
  library.locator('[data-aluno-card="10"] .aluno-nome').click()
 library.locator('.btn-add-to-training[onclick="adicionarAvaliacaoAoTreino(10)"]').click()
 expect(library.locator('.assessment-training-confirm')).to_be_visible();library.locator('.assessment-training-confirm').check();library.locator('.assessment-training-add').click()
 expect(library.locator('.training-student-picker')).to_have_count(0)
 page.locator('#assessmentLibraryDialog [data-close]').click();page.locator('#searchName').fill('Aluno teste');page.locator('#studentEvaluationBtn').click();page.locator('#obsAssessmentSections [data-assessment-section="composicao"]').click();assertions()
 browser.close();print('PASS: old/imported and new linked histories reunited; original date/sex/photos/measures retained, current 71kg independent of historical 74.50kg; explicit duplicate-link repair and two-way edits')
