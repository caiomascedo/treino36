"""Run with Playwright and /usr/bin/chromium; isolates all data in a temp server."""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import urllib.request
import urllib.error
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('backup',ROOT/'backup-server.py')
backend=importlib.util.module_from_spec(spec);spec.loader.exec_module(backend)
sample={'tipo':'treino36-completo','schema_version':'3.0','alunos':[{'student_id':'sync-a','nome':'Teste sincronização','treino':{'A':['Agachamento 3x10']},'titulos':{'A':'A. PERNAS'},'historicoTreinos':[]}], 'avaliacoes':[{'id':10,'nome':'Teste avaliação','avaliacoes':[{'id':11,'data':'17/11/2026','peso':'70'}]}], 'mobilidades':[], 'treinos_favoritos':[], 'preferencias':{}}
with tempfile.TemporaryDirectory() as temp, sync_playwright() as p:
    backend.DATA=Path(temp);backend.snapshot(sample)
    class QuietHandler(backend.Handler):
        def log_message(self, *args): pass
    server=backend.ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    local='http://127.0.0.1:'+str(server.server_port)
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    errors=[]
    def route(req):
        target=urlsplit(req.request.url)
        if target.hostname!='caio.tail953b6e.ts.net':
            return req.fulfill(status=404,body='')
        headers={k:v for k,v in req.request.headers.items() if k.lower() in ('origin','content-type','x-treino36-client','x-treino36-revision')}
        request=urllib.request.Request(local+target.path+('?' + target.query if target.query else ''),data=req.request.post_data_buffer,headers=headers,method=req.request.method)
        try:
            with urllib.request.urlopen(request,timeout=20) as response: req.fulfill(status=response.status,body=response.read(),headers={'Content-Type':response.headers.get('Content-Type','text/html')})
        except urllib.error.HTTPError as error: req.fulfill(status=error.code,body=error.read(),headers={'Content-Type':'application/json'})
    contexts=[browser.new_context() for _ in range(2)]
    for context in contexts:context.route('**/*',route)
    pages=[context.new_page() for context in contexts]
    for page in pages:
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(backend.ORIGIN+'/',wait_until='domcontentloaded')
        page.wait_for_selector('#privateSyncPanel',state='attached',timeout=30000)
        assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].student_id")=='sync-a'
    # Restoring from a newer server snapshot must not seed default/example students.
    assert all(page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos')).length")==1 for page in pages)
    a,b=pages
    # Persisted edits from A reach B, without ever importing a JSON on B.
    a.evaluate("""() => {const s=JSON.parse(localStorage.getItem('treinoAlunos'));s[0].treino.A=['Agachamento 4x12'];localStorage.setItem('treinoAlunos',JSON.stringify(s));}""")
    a.reload();a.wait_for_selector('#privateSyncPanel',state='attached');a.evaluate('PrivateSync.cycle(true)')
    b.evaluate('PrivateSync.cycle(true)');b.wait_for_timeout(1500)
    assert b.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].treino.A[0]")=='Agachamento 4x12'
    # Standalone assessment page also sends changes to the main page.
    b.goto(backend.ORIGIN+'/avaliacao.html',wait_until='domcontentloaded');b.wait_for_selector('#privateSyncPanel',state='attached')
    b.evaluate("""() => {const s=JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'));s[0].avaliacoes[0].peso='72';localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify(s));}""")
    b.reload();b.wait_for_selector('#privateSyncPanel',state='attached');b.evaluate('PrivateSync.cycle(true)')
    a.evaluate('PrivateSync.cycle(true)');a.wait_for_timeout(1500)
    assert a.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].peso")=='72'
    assert not errors,errors
    browser.close();server.shutdown();server.server_close()
    print('PASS: two isolated browsers bootstrap, workout edit A→B, assessment edit B→A, no JavaScript errors.')
