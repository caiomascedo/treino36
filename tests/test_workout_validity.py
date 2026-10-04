from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[2]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844})
    def route(r):
        u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
        if path.is_dir():path/='index.html'
        if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
        else:r.fulfill(status=404,body='')
    context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://app.test/treino36/')
    page.evaluate("""() => {localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'a',nome:'Ana',treino_id:'work-a',treino:{A:['Agachamento 3x10']}},{student_id:'b',nome:'Bruno',treino_id:'work-b',treino:{A:['Supino 3x10']}}]));localStorage.setItem('avaliacao_fisica_alunos','[]');}""")
    page.reload();expect(page.locator('#workoutValiditySummary')).not_to_be_visible()
    page.locator('#workoutValidityBtn').click()
    expect(page.locator('#workoutValidityDialogTitle')).to_be_focused()
    expect(page.locator('#validityStart')).to_have_value(page.evaluate('WorkoutValidity.today()'))
    page.locator('#validityStart').click();expect(page.locator('#validityStart')).to_be_focused()
    page.locator('#workoutValidityDialog [data-close]').click()
    cases=[('2026-01-31','months',1,'2026-02-28'),('2024-02-29','months',12,'2025-02-28'),('2026-10-04','days',45,'2026-11-18'),('2026-12-31','months',3,'2027-03-31')]
    for start,unit,amount,expected in cases:assert page.evaluate('args=>WorkoutValidity.calculate(args[0],{unit:args[1],amount:args[2]})',[start,unit,amount])==expected
    for value in ['d7','d14','m1','d45','m2','m3','custom']:
        page.locator('#workoutValidityBtn').click();page.locator('#validityStart').fill('2026-01-31');page.locator('#validityPeriod').select_option(value)
        if value=='custom':page.locator('#validityCustom').fill('63')
        page.locator('#saveWorkoutValidity').click();expect(page.locator('#workoutValidityDialog')).not_to_be_visible()
        v=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].validadeTreino")
        assert v['treinoId']=='work-a' and v['start']=='2026-01-31'
        expect(page.locator('#workoutValiditySummary')).to_contain_text('Vencido')
    page.reload();expect(page.locator('#workoutValiditySummary')).to_be_visible()
    page.locator('#workoutValidityBtn').click();page.locator('#validityPeriod').select_option('custom');page.locator('#validityCustom').fill('0');page.locator('#saveWorkoutValidity').click()
    expect(page.locator('#validityStatus')).to_contain_text('maior que zero');page.locator('#validityCustom').fill('20');page.locator('#validityStart').fill(page.evaluate('WorkoutValidity.today()'));page.locator('#saveWorkoutValidity').click()
    previous=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].validadeTreino.until")
    page.locator('#workoutValidityBtn').click();page.locator('#validityRenewal').select_option('d14');page.locator('#renewWorkoutValidity').click()
    after=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].validadeTreino")
    assert after['start']==previous and after['until']==page.evaluate("s=>WorkoutValidity.calculate(s,{unit:'days',amount:14})",previous)
    page.locator('#workoutValidityBtn').click();page.locator('#validityRenewal').select_option('none');expect(page.locator('#renewWorkoutValidity')).to_be_disabled();page.locator('#saveWorkoutValidity').click()
    assert page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].validadeTreino.until")==after['until']
    page.locator('#workoutValidityBtn').click();page.locator('#validityRenewal').select_option('custom');page.locator('#renewalCustom').fill('9');page.locator('#renewWorkoutValidity').click()
    assert page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0].validadeTreino.period.amount")==9
    page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="Bruno"] .aluno-nome').click();expect(page.locator('#workoutValiditySummary')).not_to_be_visible()
    assert page.evaluate("!AvaliacaoTreinoSync.read('treinoAlunos')[1].validadeTreino")
    page.locator('#listBtn').click();page.locator('.aluno-list-item[data-nome="Ana"] .aluno-nome').click()
    # Editing a protected cover archives its expiry and leaves the new workout without an inherited deadline.
    page.locator('.sec-a ol').fill('Agachamento 4x12');page.locator('#saveBtn').click()
    data=page.evaluate("AvaliacaoTreinoSync.read('treinoAlunos')[0]")
    assert data['treino_id']!='work-a' and not data.get('validadeTreino')
    assert data['historicoTreinos'][-1]['validadeTreino']['treinoId']=='work-a'
    expect(page.locator('#workoutValiditySummary')).not_to_be_visible()
    # Opting out removes only validity metadata, keeping exercises/history intact.
    page.locator('#workoutValidityBtn').click();page.locator('#validityPeriod').select_option('m1');page.locator('#saveWorkoutValidity').click()
    before=page.evaluate("JSON.stringify(AvaliacaoTreinoSync.read('treinoAlunos')[0].treino)")
    page.locator('#workoutValidityBtn').click();page.locator('#validityPeriod').select_option('none');page.locator('#saveWorkoutValidity').click()
    assert page.evaluate("JSON.stringify(AvaliacaoTreinoSync.read('treinoAlunos')[0].treino)")==before
    expect(page.locator('#workoutValiditySummary')).not_to_be_visible();assert not errors,errors
    browser.close();print('PASS: optional validity, calendar-month/leap-year boundaries, weeks/months/45/custom days, expired status, manual renew carries remaining time, no-renew and custom renewal, per-student isolation, archive retains old validity, new cover starts without expiry, opt-out preserves workout')
