"""Real catalog, category filtering, persistent uploads, duplicate blocking and GIF output."""
import json
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT/'gymfaster-catalog.json').read_text())
videos = catalog['videos']
assert len(videos) == 843
assert len({v['exerciseKey'] for v in videos}) == len(videos)
assert len({v['sha256'] for v in videos}) == len(videos)
assert all((ROOT/v['media']).is_file() for v in videos)
fixture_dir = tempfile.TemporaryDirectory()
upload_path = Path(fixture_dir.name)/'upload.mp4'
subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','testsrc2=size=320x240:rate=15','-t','2','-c:v','libx264','-pix_fmt','yuv420p',str(upload_path)],check=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':390,'height':844}, accept_downloads=True)
    def route(r):
        u = urlparse(r.request.url)
        if u.scheme in ['blob','data']:
            r.continue_(); return
        f = ROOT/u.path.lstrip('/')
        if f.is_dir(): f /= 'index.html'
        if u.hostname == 'localhost' and f.is_file():
            r.fulfill(body=f.read_bytes(), content_type={'.js':'application/javascript','.css':'text/css','.json':'application/json','.mp4':'video/mp4'}.get(f.suffix,'text/html'))
        else: r.fulfill(status=404)
    context.route('**/*', route)
    page=context.new_page(); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://localhost:8765/');page.evaluate('TreinoStorage.ready')
    page.locator('#moreOptions>summary').click();page.locator('#gymfasterCollectionBtn').click()
    root=page.locator('#gymfasterLibrary');expect(root.locator('.gym-result')).to_have_count(843)
    expect(root.locator('.video-category-title')).to_have_count(17)
    root.get_by_role('combobox',name='Categoria dos vídeos').select_option('Peito')
    expect(root.locator('.gym-result')).to_have_count(sum(v['group']=='Peito' for v in videos))
    root.get_by_role('button',name='Adicionar vídeo',exact=True).click()
    add=page.get_by_role('dialog',name='Adicionar vídeo à biblioteca')
    expect(add).to_contain_text('somente neste navegador e aparelho')
    add.get_by_role('textbox',name='Nome do exercício').fill('Vídeo pessoal de teste com pausa')
    add.get_by_role('combobox',name='Categoria do vídeo').select_option('Peito')
    add.get_by_label('Arquivo de vídeo').set_input_files(str(upload_path))
    add.get_by_role('button',name='Salvar vídeo',exact=True).click();expect(add).not_to_be_visible(timeout=30000)
    expect(root.locator('.gym-result')).to_have_count(1);expect(root).to_contain_text('Vídeo pessoal de teste com pausa')
    # A second title cannot bypass the file fingerprint check.
    root.get_by_role('button',name='Adicionar vídeo',exact=True).click()
    add.get_by_role('textbox',name='Nome do exercício').fill('Outro nome para o mesmo arquivo')
    add.get_by_role('combobox',name='Categoria do vídeo').select_option('Peito')
    add.get_by_label('Arquivo de vídeo').set_input_files(str(upload_path))
    add.get_by_role('button',name='Salvar vídeo',exact=True).click();expect(add.get_by_role('status')).to_contain_text('já está na biblioteca')
    add.get_by_role('button',name='Cancelar',exact=True).click()
    # Name duplicates are also blocked, even when the file has different bytes.
    message=page.evaluate('''async () => {try {await WorkoutCatalog.add(new File([new Uint8Array([1,2,3])],'new.mp4',{type:'video/mp4'}),'  '+WorkoutCatalog.current().find(v=>v.collection==='gymfaster').name.toUpperCase()+'  ','Peito');return 'accepted';}catch(e){return e.message;}}''')
    assert 'já está na biblioteca' in message, message
    page.reload();page.evaluate('TreinoStorage.ready');awaited=page.evaluate('WorkoutCatalog.load().then(v=>v.filter(x=>x.source==="Meu vídeo").length)');assert awaited==1
    # A saved old Drive ID resolves to the chosen canonical version.
    asset=next(v for v in videos if any(i!=v['id'] for i in v['sourceIds']))
    old=next(i for i in asset['sourceIds'] if i!=asset['id'])
    resolved=page.evaluate('''({old,name})=>WorkoutVideoMatch.resolve({nome:'qualquer',video:'https://drive.google.com/file/d/'+old+'/view'},WorkoutCatalog.current(),'gymfaster').video?.name''',{'old':old,'name':asset['name']})
    assert resolved==asset['name'],(resolved,asset['name'])
    page.evaluate('''()=>localStorage.setItem('treinoAlunos',JSON.stringify([{student_id:'unified-test',nome:'Teste união',treino:{A:['Vídeo pessoal de teste com pausa — 3x12']},titulos:{A:'A. Teste'}}]))''');page.reload()
    page.locator('#workoutGifsBtn').click();main=page.locator('#workoutGifDialog');expect(main.locator('.gif-card')).to_have_count(1)
    expect(main.locator('[role=status]')).to_contain_text('1/1')
    main.get_by_role('button',name='Escolher outro vídeo',exact=True).click();picker=page.locator('.gif-video-picker')
    picker.get_by_role('combobox',name='Biblioteca da demonstração').select_option('both')
    picker.get_by_role('button',name='Ver todos os vídeos',exact=True).click()
    expect(picker.locator('button[data-video-id]')).to_have_count(844)
    assert picker.evaluate('e=>e.scrollWidth<=e.clientWidth')
    picker.get_by_role('button',name='Fechar',exact=True).click()
    main.locator('.gif-primary').click()
    expect(main.locator('[role=status]')).to_contain_text('GIF pronto',timeout=180000)
    page.screenshot(path=str(Path(fixture_dir.name)/'library-tested.png'))
    assert not errors,errors
    browser.close()
print('PASS: 843 unique entries/17 categories, upload persistence, duplicate name/hash blocking, legacy IDs, 844 picker results and actual GIF generation')
