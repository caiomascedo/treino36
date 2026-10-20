from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.removeprefix('/treino36/').lstrip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404)
 ctx.route('**/*',route);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://app.test/treino36/')
 page.evaluate('''()=>{localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',avaliacaoId:10,infoRelevante:{idade:'19',altura:'1.53',peso:'58',nivelTreino:'pesado'},treino:{A:['Agachamento 3x10']}},{student_id:'b',nome:'Bia',infoRelevante:{idade:'19',altura:'1.53',peso:'58'},treino:{A:['Supino 3x10']}}]));localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',treinoStudentIds:['a'],sexo:'F',idade:'19',altura:'1.53',pesoAtual:'58',avaliacoes:[]} ]));localStorage.setItem('dieta36_calculos_v1:a',JSON.stringify({goalMode:'daily',macroAuto:true,protein:'116',carbs:'400',fat:'46.4',calories:'2496'}));}''');page.reload()
 page.locator('#dietBtn').click();page.locator('#dietCalculations > summary').click()
 expect(page.locator('#dietTmb')).to_have_text('1.382,6')
 expect(page.locator('#diet-calories')).to_have_value('');expect(page.locator('#dietMacroNotice')).to_contain_text('dados na OBS')
 expect(page.locator('[data-diet-goal="daily"]')).to_contain_text('—')
 page.locator('#dietDialog [data-close]').click();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click()
 expect(page.locator('#infoSexoCalorico')).to_have_value('F');expect(page.locator('#infoAtividadeCalorica')).to_have_value('')
 page.locator('#infoAtividadeCalorica').select_option('moderada');expect(page.locator('#kcalBadge')).to_contain_text('1.797,38');expect(page.locator('#kcalDetails')).to_contain_text('1.382,6')
 # The unrelated training intensity must not change calorie estimates.
 page.locator('#treinoLevelSelector [data-level="leve"]').click();expect(page.locator('#kcalBadge')).to_contain_text('1.797,38')
 page.locator('#infoAtividadeCalorica').select_option('intensa');expect(page.locator('#kcalBadge')).to_contain_text('1.935,64')
 page.locator('#infoSexoCalorico').select_option('M');expect(page.locator('#kcalBadge')).to_contain_text('2.169,78')
 page.locator('#infoAtividadeCalorica').select_option('nenhuma');expect(page.locator('#kcalBadge')).to_contain_text('1.870,5')
 page.locator('#infoSexoCalorico').select_option('F');page.locator('#infoAtividadeCalorica').select_option('moderada')
 for width in [320,390]:
  page.set_viewport_size({'width':width,'height':844});assert page.locator('#workoutObsDialog').evaluate('el=>el.scrollWidth<=el.clientWidth+1')
 page.locator('#workoutObsDialog [data-close]').click();page.locator('#dietBtn').click()
 expect(page.locator('[data-diet-goal="daily"]')).to_contain_text('1.797,38')
 page.locator('[data-diet-goal="daily"]').click()
 for key,value in [('protein','116'),('carbs','228.9'),('fat','46.4'),('calories','1797')]:expect(page.locator('#diet-'+key)).to_have_value(value)
 page.screenshot(path='/tmp/treino36-calorie-reference-mobile.png')
 # Live OBS changes refresh the automatic diet calculation without reloading.
 page.evaluate('''()=>{const s=AvaliacaoTreinoSync.read('treinoAlunos');for(const g of [s[0].infoRelevante,...(s[0].infoGuias||[])])g.atividadeCalorica='nenhuma';localStorage.setItem('treinoAlunos',JSON.stringify(s));window.dispatchEvent(new Event('focus'));}''')
 expect(page.locator('[data-diet-goal="daily"]')).to_contain_text('1.659,12');expect(page.locator('#diet-carbs')).to_have_value('194.4')
 page.locator('#diet-goal').fill('1800');page.locator('#diet-protein').fill('120');page.reload();page.locator('#dietBtn').click();page.locator('#dietCalculations > summary').click();expect(page.locator('#diet-protein')).to_have_value('120');expect(page.locator('#diet-goal')).to_have_value('1800')
 # Missing sex is explicit, never inferred from names; independent pupils retain blank settings.
 page.locator('#dietDialog [data-close]').click();page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="Bia"] .aluno-nome').click();page.locator('#dietBtn').click();expect(page.locator('#dietTmb')).to_have_text('—')
 page.locator('#dietDialog [data-close]').click();page.locator('#obsIconBtn').click();page.locator('#toggleInfoRelevanteBtn').click();expect(page.locator('#infoSexoCalorico')).to_have_value('');expect(page.locator('#infoAtividadeCalorica')).to_have_value('')
 assert not errors,errors
 browser.close();print('PASS: Unimed example in OBS and diet, correct sex factors, explicit missing activity/sex, no training-factor coupling, old automatic estimate migration, mobile layout, OBS persistence and live diet refresh, manual targets and pupil isolation')
