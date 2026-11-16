from pathlib import Path
from urllib.parse import urlparse
import os
import re
from playwright.sync_api import sync_playwright, expect
ROOT = Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    b = p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if os.getenv('GIF_TEST_BROWSER') == 'webkit' else p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    c = b.new_context(viewport={'width': 390, 'height': 844})
    def route(r):
        u = urlparse(r.request.url)
        f = ROOT / u.path.lstrip('/')
        if f.is_dir(): f /= 'index.html'
        if u.hostname == 'edit.test' and f.is_file():
            r.fulfill(body=f.read_bytes(), content_type={'.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json'}.get(f.suffix, 'text/html'))
        else: r.fulfill(status=404)
    c.route('**/*', route)
    page = c.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto('https://edit.test/')
    page.evaluate('TreinoStorage.ready')
    students = [
        {'student_id': 'caio', 'nome': 'Caio Macedo', 'treino_id': 'now', 'treino': {'A': ['Supino — 3×12 [Vídeo: https://youtu.be/abcdefghijk]'], 'B': ['Rosca — 4×10']}, 'historicoTreinos': [{'workout_id': 'old', 'name': 'Anterior', 'treino': {'A': ['Remada — 3×10']}}]},
        {'student_id': 'maria', 'nome': 'Maria Teste', 'treino_id': 'm-now', 'treino': {'A': ['Puxada — 4×12']}, 'historicoTreinos': []}
    ]
    page.evaluate('(s)=>localStorage.setItem("treinoAlunos",JSON.stringify(s))', students)
    page.reload()
    page.evaluate('TreinoStorage.ready')
    page.wait_for_function('document.querySelector("#searchName").value==="Caio Macedo"')
    def saved(): return page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))')
    baseline = saved()
    page.locator('#compareWorkoutBtn').click()
    current = page.locator('.comparison-current-line').first
    current.fill('Supino inclinado — 4×12')
    page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A[0].startsWith("Supino inclinado")')
    expect(page.locator('.sec-a ol li').first).to_contain_text(re.compile('Supino inclinado', re.I))
    assert '[Vídeo: https://youtu.be/abcdefghijk]' in saved()[0]['treino']['A'][0]
    assert saved()[0]['treino']['B'] == students[0]['treino']['B']
    assert saved()[0]['historicoTreinos'] == baseline[0]['historicoTreinos']
    page.locator('#compareUndo').click()
    page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A[0].startsWith("Supino —")')
    page.locator('#compareRedo').click()
    page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A[0].startsWith("Supino inclinado")')
    current.fill('Supino final — 5×8')
    page.locator('#compareWorkoutsDialog .dialog-actions button').filter(has_text='Fechar').click()
    page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A[0].startsWith("Supino final")')
    page.locator('#compareWorkoutBtn').click()
    page.locator('.comparison-previous-line').first.fill('Anterior separado — 2×10')
    page.locator('#searchCompareCurrentCover').click()
    page.locator('#compareSearchInput').fill('Maria')
    page.locator('#compareSearchResults .btn-curr').click()
    page.locator('#compareChoiceViewOnly').click()
    current.fill('Puxada Maria — 5×10')
    page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[1].treino.A[0]==="Puxada Maria — 5×10"')
    assert saved()[0]['treino']['A'][0].lower().startswith('supino final')
    expect(page.locator('.sec-a ol li').first).to_contain_text(re.compile('Supino final', re.I))
    assert saved()[0]['historicoTreinos'] == baseline[0]['historicoTreinos']
    # Displaying an archive on the right must not promote or overwrite the cover.
    options = page.locator('#compareCurrentPicker option').evaluate_all('(xs)=>xs.map(x=>({value:x.value,text:x.textContent}))')
    archive = next(x['value'] for x in options if x['value'].startswith('archive:'))
    page.locator('#compareCurrentPicker').select_option(archive)
    page.locator('#compareChoiceViewOnly').click()
    before_archive = saved()
    current.fill('Histórico rascunho — 1×10')
    page.wait_for_timeout(450)
    assert saved() == before_archive
    assert not errors, errors
    b.close()
    print('PASS: automatic current-cover persistence, main-page sync, media, undo/redo, close flush, correct pupil and archive isolation')
