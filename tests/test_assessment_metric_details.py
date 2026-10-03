import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[2] if Path(__file__).parent.parent.name == 'treino36' else Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':390, 'height':844})
    def route(request):
        url = urlparse(request.request.url)
        if url.hostname == 'app.test':
            path = ROOT / url.path.strip('/')
            if path.is_dir(): path /= 'index.html'
            if path.is_file():
                request.fulfill(body=path.read_bytes(), content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
                return
        request.fulfill(status=404, body='')
    context.route('**/*', route)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://app.test/treino36/')
    page.evaluate("""() => {
      localStorage.setItem('treinoAlunos','[]');localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Cliente',sexo:'M',idade:'30',altura:'1.75',avaliacoes:[{id:11,data:'03/10/2026',peso:'75',gordura:'20',protocolo:'jp7',triceps:'10',axilar:'11',torax:'12',abdominal:'13',suprailiaca:'14',subescapular:'15',pregaCoxa:'16',cintura:'80',quadril:'100'}]}]));
    }""")
    page.reload();page.locator('#assessmentsLibraryBtn').click()
    frame=page.frame_locator('#assessmentLibraryFrame')
    frame.locator('.aluno-nome').click();frame.locator('.av-header').click()
    frame.locator('body').evaluate("()=>{window.metricScrolls=0;const original=Element.prototype.scrollIntoView;Element.prototype.scrollIntoView=function(...args){window.metricScrolls++;return original.apply(this,args);};}")
    tmb=frame.locator('#tmb-badge-10-11');tmb.click()
    field=frame.locator('#tmb-10-11').locator('..')
    expect(field.locator('.gauge-panel.show')).to_be_visible()
    expect(field.locator('.gauge-title')).to_contain_text('TMB')
    assert field.locator('.gauge-panel').evaluate("el=>el.previousElementSibling.id")=='tmb-badge-10-11'
    assert frame.locator('body').evaluate('()=>window.metricScrolls')==0
    tmb.click();expect(field.locator('.gauge-panel')).not_to_be_visible()
    frame.locator('#peso-badge-10-11').click()
    weight=frame.locator('#peso-input-10-11').locator('..')
    expect(weight.locator('.gauge-panel.show')).to_be_visible()
    expect(field.locator('.gauge-panel')).not_to_be_visible()
    frame.locator('.av-content [data-section="dobras"]').click()
    preview=frame.locator('.preview-item[onclick*="massagordapct"]');preview.click()
    expect(preview.locator('.gauge-panel.show')).to_be_visible()
    assert frame.locator('body').evaluate('()=>window.metricScrolls')==0
    assert not errors,errors
    page.screenshot(path=str(Path(__file__).parent/'metric-details-mobile.png'))
    browser.close()
    print('PASS: metric explanation inside its own field/result, tap to close, no automatic scroll and separate assessment panels')
