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
        {'student_id': 'caio', 'nome': 'Caio Macedo', 'treino_id': 'now', 'treino': {'A': ['Supino — 3×12 [Vídeo: https://youtu.be/abcdefghijk]', 'Extensora — 3×15', 'Leg Press — 4×10'], 'B': ['Rosca — 4×10']}, 'historicoTreinos': [{'workout_id': 'old', 'name': 'Anterior', 'treino': {'A': ['Remada — 3×10']}}]},
        {'student_id': 'maria', 'nome': 'Maria Teste', 'treino_id': 'm-now', 'treino': {'A': ['Puxada — 4×12']}, 'historicoTreinos': []}
    ]
    page.evaluate('(s)=>localStorage.setItem("treinoAlunos",JSON.stringify(s))', students)
    page.reload()
    page.evaluate('TreinoStorage.ready')
    page.wait_for_function('document.querySelector("#searchName").value==="Caio Macedo"')
    def saved(): return page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))')
    baseline=saved()
    page.locator('#compareWorkoutBtn').click()
    page.locator('#compareMoveMode').click()
    def line(i,side='current',sec='A'):
        return page.locator(f'.comparison-{side}-line[data-section="{sec}"][data-index="{i}"]')
    def drag(source,target,after=True):
        handle=source.locator('..').locator('.compare-move-handle');handle.scroll_into_view_if_needed();a=handle.bounding_box();b=target.bounding_box();page.mouse.move(a['x']+a['width']/2,a['y']+a['height']/2);page.mouse.down();page.mouse.move(b['x']+b['width']/2,b['y']+b['height']*(.9 if after else .1),steps=12);expect(page.locator('.compare-drag-ghost')).to_be_visible();page.mouse.up();expect(page.locator('.compare-drag-ghost')).to_have_count(0)
    page.locator('#compareWorkoutsDialog .compare-scroll').evaluate('e=>e.scrollTop=document.querySelector("#compare-section-A").offsetTop-20')
    drag(line(0),line(2))
    page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A[2].startsWith("Supino")')
    assert 'abcdefghijk' in saved()[0]['treino']['A'][2]
    expect(page.locator('.sec-a ol li').nth(2)).to_contain_text('Supino')
    page.locator('#compareUndoFooter').click()
    assert saved()[0]['treino']['A'][0].startswith('Supino')
    page.locator('#compareRedo').click()
    assert saved()[0]['treino']['A'][2].startswith('Supino')
    # Independent sides, cross-section movement, and keyboard movement.
    drag(line(2),line(0,sec='B'))
    assert len(saved()[0]['treino']['A'])==2 and len(saved()[0]['treino']['B'])==2
    line(1,sec='B').locator('..').locator('.compare-move-handle').press('Alt+ArrowUp')
    assert saved()[0]['treino']['B'][0].startswith('Supino')
    assert saved()[0]['historicoTreinos']==baseline[0]['historicoTreinos']
    page.locator('[data-add-side="current"][data-section="A"]').click()
    line(2).fill('Mesa Flexora unilateral 3x15 Com 3s Na Descida')
    line(2).press('Enter')
    page.wait_for_function('JSON.parse(localStorage.getItem("treinoAlunos"))[0].treino.A[2]==="Mesa Flexora unilateral — 3x15 Com 3s Na Descida"')
    main=page.locator('.sec-a ol li').nth(2)
    expect(main.locator('.bold')).to_have_text('Mesa Flexora Unilateral')
    assert '3x15' not in main.locator('.bold').inner_text()
    page.locator('[data-add-side="previous"][data-section="A"]').click()
    line(1,'previous').fill('Anterior novo 2x12');line(1,'previous').press('Enter')
    assert saved()[0]['historicoTreinos']==baseline[0]['historicoTreinos']
    page.locator('#applyCompareEdit').click()
    assert saved()[0]['historicoTreinos'][0]['treino']['A'][1]=='Anterior novo — 2x12'
    assert not errors,errors
    b.close()
    print('PASS: floating pointer reorder, cross-section and keyboard movement, independent sides, undo/redo, media, automatic cover sync, add exercise and name/sets formatting')
