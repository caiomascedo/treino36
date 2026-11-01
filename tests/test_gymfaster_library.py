"""GymFaster selection persists without swapping variants; exported A has the chosen links."""
import base64, json, urllib.request
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import fitz
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
cache=Path('/tmp/treino36-html2pdf.bundle.js')
if not cache.exists(): cache.write_bytes(urllib.request.urlopen('https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js',timeout=30).read())
catalog=json.loads((ROOT/'gymfaster-catalog.json').read_text())
assert len(catalog['videos'])==671
assert len({v['id'] for v in catalog['videos']})==671
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':390,'height':844})
    context.add_init_script('''window.pdfBlobs=new Map();const create=URL.createObjectURL.bind(URL);URL.createObjectURL=blob=>{const url=create(blob);pdfBlobs.set(url,blob);return url;};window.pdfWindows=[];window.open=()=>{const v={closed:false,document:{title:'',body:{textContent:''}},location:{replace(url){v.url=url}},close(){this.closed=true}};pdfWindows.push(v);return v;};''')
    fail_catalog=False
    def route(r):
        u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
        if path.is_dir():path/='index.html'
        if 'html2pdf.bundle' in u.path:
            r.fulfill(body=Path('/tmp/treino36-html2pdf.bundle.js').read_bytes(),content_type='application/javascript');return
        if u.hostname=='gym.test' and path.is_file():
            if fail_catalog and path.name=='gymfaster-catalog.json':r.fulfill(status=503);return
            r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json'}.get(path.suffix,'text/html'))
        else:r.fulfill(status=404)
    context.route('**/*',route)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://gym.test/');page.evaluate('TreinoStorage.ready')
    seed=[{'student_id':'gym-one','nome':'Teste Gym','treino':{'A':['Cadeira extensora — 3×12','Glúteo na polia — 3×12 [Vídeo: https://example.com/meu-video]'],'B':['Remada — 4×10']},'titulos':{'A':'A. Pernas','B':'B. Costas'}}]
    page.evaluate('(data)=>localStorage.setItem("treinoAlunos",JSON.stringify(data))',seed);page.reload()
    page.locator('#pdfBtn').click();page.get_by_role('button',name='Preparar treino A · GymFaster',exact=True).click()
    expect(page.locator('#pdfBody .pdf-sec:not([hidden])')).to_have_count(1)
    expect(page.locator('#pdfBody .pdf-sec:not([hidden])')).to_have_attribute('data-pdf-section','A')
    choices=page.locator('.pdf-video-choice');expect(choices.nth(1).locator('input')).to_have_value('https://example.com/meu-video')
    before=page.evaluate('localStorage.getItem("treinoAlunos")')
    choices.first.get_by_role('button',name='GymFaster',exact=True).click()
    dialog=page.locator('#gymfasterLibrary');expect(dialog).to_be_visible()
    expect(dialog.locator('.gym-result')).to_have_count(2)
    dialog.get_by_role('combobox',name='Versão GymFaster').select_option('Feminino')
    expect(dialog.locator('.gym-result')).to_have_count(1)
    dialog.get_by_role('button',name='Ver movimento').click()
    expect(dialog.locator('iframe')).to_have_attribute('src','https://drive.google.com/file/d/1J0581Mjqk4_p6XEv5-PW1RZT5miqGXRr/preview')
    assert page.evaluate('localStorage.getItem("treinoAlunos")')==before
    page.screenshot(path='/tmp/gymfaster-mobile.png')
    assert dialog.evaluate('e=>e.scrollWidth<=e.clientWidth')
    dialog.get_by_role('button',name='Usar este vídeo').click()
    expect(dialog).not_to_be_visible();expect(dialog.locator('iframe')).to_have_count(0)
    chosen=choices.first.locator('input').input_value();assert '/1J0581Mjqk4_p6XEv5-PW1RZT5miqGXRr/' in chosen
    expect(choices.first.locator('.gym-selected')).to_contain_text('Cadeira Extensora')
    choices.first.get_by_role('button',name='Automático',exact=True).click()
    expect(choices.first.locator('input')).to_have_value('')
    expect(choices.first.locator('.gym-selected')).to_be_empty()
    choices.first.locator('input').fill(chosen)
    saved=page.evaluate('JSON.parse(localStorage.getItem("treinoAlunos"))')
    assert chosen in saved[0]['treino']['A'][0] and '3×12' in saved[0]['treino']['A'][0]
    assert saved[0]['treino']['A'][1].casefold()==json.loads(before)[0]['treino']['A'][1].casefold()
    assert saved[0]['treino']['B']==json.loads(before)[0]['treino']['B']
    choices.nth(1).get_by_role('button',name='GymFaster',exact=True).click()
    expect(dialog.locator('.gym-result')).to_have_count(0)
    expect(dialog.locator('[role=status]')).to_contain_text('Sem essa variação')
    search=dialog.get_by_role('searchbox');search.fill('glúteo coice')
    expect(dialog.locator('.gym-results')).to_contain_text('Máquina')
    dialog.get_by_role('button',name='Fechar',exact=True).click()
    expect(choices.nth(1).locator('input')).to_have_value('https://example.com/meu-video')
    page.get_by_role('combobox',name='Monitoramento dos vídeos').select_option('direct')
    page.locator('#downloadPdfBtn').click();page.wait_for_function('pdfWindows.length===1&&pdfWindows[0].url',timeout=30000)
    encoded=page.evaluate("async()=>{const b=new Uint8Array(await pdfBlobs.get(pdfWindows[0].url).arrayBuffer());let s='';for(const v of b)s+=String.fromCharCode(v);return btoa(s)}")
    with fitz.open(stream=base64.b64decode(encoded),filetype='pdf') as doc:
        links=[a['uri'] for pg in doc for a in pg.get_links() if 'uri' in a]
        assert chosen in links and 'https://example.com/meu-video' in links,links
        assert len(links)==2,links
    page.locator('#closePdfViewer').click();page.reload();page.locator('#pdfBtn').click()
    expect(page.locator('.pdf-video-choice input').first).to_have_value(chosen)
    # The normal PDF path still includes B; the preparation shortcut changes only the current draft.
    expect(page.locator('#pdfBody .pdf-sec:not([hidden])')).to_have_count(2)
    page.locator('#closePdfViewer').click();page.locator('#moreOptions > summary').click();page.locator('#gymfasterCollectionBtn').click()
    expect(dialog.locator('.gym-result')).to_have_count(671)
    dialog.get_by_role('combobox',name='Versão GymFaster').select_option('Masculino')
    assert 0<dialog.locator('.gym-result').count()<671
    expect(dialog.get_by_role('button',name='Usar este vídeo')).to_have_count(0)
    dialog.get_by_role('button',name='Fechar',exact=True).click()
    # Failed catalog loads are recoverable and do not assign or clear links.
    fail_catalog=True;page.reload();page.locator('#moreOptions > summary').click();page.locator('#gymfasterCollectionBtn').click()
    expect(dialog.locator('[role=status]')).to_contain_text('Não foi possível carregar')
    dialog.get_by_role('button',name='Fechar',exact=True).click();fail_catalog=False
    page.locator('#moreOptions > summary').click();page.locator('#gymfasterCollectionBtn').click()
    expect(dialog.locator('.gym-result')).to_have_count(671)
    dialog.get_by_role('button',name='Fechar',exact=True).click()
    # An absent A must not hide another available section.
    page.evaluate("()=>{const people=JSON.parse(localStorage.getItem('treinoAlunos'));people[0].treino.A=[];localStorage.setItem('treinoAlunos',JSON.stringify(people));}")
    page.reload();page.locator('#pdfBtn').click();page.get_by_role('button',name='Preparar treino A · GymFaster',exact=True).click()
    expect(page.locator('#pdfReviewTools [role=status]')).to_contain_text('treino A está vazio')
    expect(page.locator('#pdfBody .pdf-sec:not([hidden])')).to_have_count(1)
    assert not errors,errors
    browser.close()
print('PASS: 671 verified videos, preview, explicit variant choice, preserved manual links and workout B, persistence, mobile layout, actual A-only PDF links')
