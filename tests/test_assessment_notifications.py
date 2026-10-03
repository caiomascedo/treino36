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
    context.add_init_script("""(() => {
      window.sentNotifications=[]; window.permissionRequests=0;
      class TestNotification {
        static permission='granted';
        static requestPermission(){window.permissionRequests++;return Promise.resolve('granted');}
        constructor(title,options){window.sentNotifications.push({title,options});}
      }
      Object.defineProperty(window,'Notification',{configurable:true,value:TestNotification});
    })();""")
    page.goto('http://app.test/treino36/')
    page.evaluate("""() => {
      localStorage.setItem('treinoAlunos','[]');
      localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:100,nome:'Cliente teste',sexo:'M',renovacaoDias:'30',avaliacoes:[{id:101,data:'01/01/2000',peso:'70',protocolo:'jp7'}]}]));
      localStorage.removeItem('avaliacao_notificacoes_ativas');localStorage.removeItem('notifRenovacaoData');
    }""")
    page.reload();page.locator('#assessmentsLibraryBtn').click()
    frame=page.frame_locator('#assessmentLibraryFrame')
    expect(frame.locator('#bannerRenovacao')).not_to_be_visible()
    assert frame.locator('body').evaluate('()=>window.sentNotifications.length')==0
    frame.locator('.assessment-more-options summary').click()
    toggle=frame.locator('#assessmentNotificationsToggle')
    expect(toggle).not_to_be_checked()
    toggle.check()
    expect(frame.locator('#bannerRenovacao')).to_be_visible()
    assert page.evaluate("localStorage.getItem('avaliacao_notificacoes_ativas')")=='1'
    assert frame.locator('body').evaluate('()=>window.sentNotifications.length')==1
    toggle.uncheck()
    expect(frame.locator('#bannerRenovacao')).not_to_be_visible()
    assert page.evaluate("localStorage.getItem('avaliacao_notificacoes_ativas')")=='0'
    frame.locator('body').evaluate("()=>verificarRenovacoesEnviarNotificacao(true)")
    assert frame.locator('body').evaluate('()=>window.sentNotifications.length')==1
    frame.locator('body').evaluate("()=>notifMsg('✅ Alteração salva')")
    expect(frame.locator('#notif')).to_have_css('opacity','0')
    # Preferences survive reopening; permission denial still allows in-app reminders.
    page.locator('#assessmentLibraryDialog [data-close]').click(); page.locator('#assessmentsLibraryBtn').click()
    frame.locator('.assessment-more-options summary').click(); expect(toggle).not_to_be_checked()
    frame.locator('body').evaluate("()=>{Notification.permission='default';Notification.requestPermission=()=>{window.permissionRequests++;return Promise.resolve('denied');};}")
    toggle.check()
    expect(frame.locator('#assessmentNotificationsStatus')).to_have_text('Avisos na avaliação ligados')
    expect(frame.locator('#bannerRenovacao')).to_be_visible()
    assert frame.locator('body').evaluate('()=>window.permissionRequests')==1
    other=context.new_page();other.goto('http://app.test/treino36/avaliacao.html?embed=treino36-library')
    other.locator('.assessment-more-options summary').click();expect(other.locator('#assessmentNotificationsToggle')).to_be_checked()
    toggle.uncheck();expect(other.locator('#assessmentNotificationsToggle')).not_to_be_checked();expect(other.locator('#bannerRenovacao')).not_to_be_visible()
    frame.locator('.assessment-more-options summary').click()
    sizes=frame.locator('.compact-actions').evaluate("el=>({height:el.getBoundingClientRect().height,width:el.clientWidth,scroll:el.scrollWidth})")
    assert sizes['height']<48 and sizes['scroll']<=sizes['width'],sizes
    assert not errors,errors
    page.screenshot(path=str(Path(__file__).parent/'notifications-mobile.png'))
    browser.close()
    print('PASS: compact action row and notification switch; off by default, no forced delivery while off, remembered preference, denied permission and shared settings')
