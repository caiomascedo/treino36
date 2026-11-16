"""Search shortcuts confirm deletions and move an archived workout into the cover."""
from pathlib import Path
from urllib.parse import urlparse
import os
from playwright.sync_api import sync_playwright, expect
ROOT = Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.webkit.launch(executable_path=os.environ['PLAYWRIGHT_WEBKIT_EXECUTABLE']) if os.getenv('GIF_TEST_BROWSER') == 'webkit' else p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 390, 'height': 844})
    def route(r):
        u = urlparse(r.request.url)
        f = ROOT / u.path.lstrip('/')
        if f.is_dir(): f /= 'index.html'
        if u.hostname == 'search.test' and f.is_file():
            r.fulfill(body=f.read_bytes(), content_type={'.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json'}.get(f.suffix, 'text/html'))
        else: r.fulfill(status=404)
    context.route('**/*', route)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: (errors.append(str(e)), print('PAGEERROR:', str(e))))
    page.goto('https://search.test/')
    page.evaluate('TreinoStorage.ready')
    students = [
        {'student_id': 'lauri', 'nome': 'Lauriane', 'treino_id': 'cover', 'treinoNome': 'Capa Lauriane', 'treino': {'A': ['Atual — 3×12']}, 'obsGuias': [{'id': 'keep', 'texto': 'Manter'}], 'historicoTreinos': [
            {'workout_id': 'shared-legacy', 'name': 'Antigo', 'treino': {'A': ['Remada — 3×10']}},
            {'workout_id': 'shared-legacy', 'name': 'Recente', 'treino': {'A': ['Supino — 4×12 [Vídeo: https://youtu.be/abcdefghijk]']}, 'titulos': {'A': 'A. Peito'}, 'validadeTreino': {'start': '2026-11-16', 'until': '2026-12-16', 'unit': 'days', 'amount': 30}}
        ]},
        {'student_id': 'other', 'nome': 'Outro aluno', 'treino_id': 'other-cover', 'treino': {'A': ['Stiff — 2×10']}, 'historicoTreinos': []}
    ]
    page.evaluate('(s)=>localStorage.setItem("treinoAlunos",JSON.stringify(s))', students)
    page.reload()
    page.evaluate('TreinoStorage.ready')
    page.wait_for_function('document.querySelector("#searchName").value==="Lauriane"')
    def records(): return page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))')
    def search(name='Lauriane'):
        page.locator('#searchName').fill(name)
        page.locator('#searchName').focus()
        expect(page.locator('.name-suggestion-group').filter(has_text=name).first).to_be_visible()
    def delete(kind, index=None):
        row = page.locator('.name-suggestion-subitem[data-type="'+kind+'"]')
        if index is not None: row = row.locator('xpath=self::*[@data-history-index="'+str(index)+'"]')
        row.first.locator('.sub-delete-btn').click()
        expect(page.locator('#historyDeleteDialog')).to_be_visible()
    baseline = records()
    search()
    delete('history', 1)
    expect(page.locator('#historyDeletePreview')).to_contain_text('Supino')
    page.locator('#historyDeleteDialog').get_by_role('button', name='Cancelar', exact=True).click()
    assert records() == baseline
    search()
    delete('cover')
    expect(page.locator('#historyReplacementChoice')).to_have_value('1')
    expect(page.locator('#historyReplacementPreview')).to_contain_text('Supino')
    page.locator('#confirmDeleteHistoryVersion').click()
    expect(page.locator('#historyDeleteDialog')).not_to_be_visible()
    saved = records()[0]
    assert saved['treino']['A'] == baseline[0]['historicoTreinos'][1]['treino']['A']
    assert saved['titulos']['A'] == 'A. Peito'
    assert saved['validadeTreino']['treinoId'] == saved['treino_id']
    assert len(saved['historicoTreinos']) == 1 and saved['historicoTreinos'][0]['name'] == 'Antigo'
    assert saved['obsGuias'] == baseline[0]['obsGuias']
    assert records()[1] == baseline[1]
    expect(page.locator('.sec-a ol li').first).to_contain_text('Supino')
    # Exact archived row can be deleted; the promoted cover stays unchanged.
    search()
    delete('history', 0)
    page.locator('#confirmDeleteHistoryVersion').click()
    assert not records()[0]['historicoTreinos']
    assert records()[0]['treino'] == saved['treino']
    # A different pupil's lone cover is cleared without touching the current pupil.
    search('Outro aluno')
    delete('cover')
    expect(page.locator('#historyDeleteHint')).to_contain_text('treino vazio')
    page.locator('#confirmDeleteHistoryVersion').click()
    assert records()[1]['nome'] == 'Outro aluno'
    assert all(not rows for rows in records()[1]['treino'].values())
    assert records()[0]['treino'] == saved['treino']
    assert not errors, errors
    browser.close()
    print('PASS: search delete buttons, cancel unchanged, exact legacy archive, latest cover replacement consumes archive, main-page sync, media/notes/validity and pupil isolation')
