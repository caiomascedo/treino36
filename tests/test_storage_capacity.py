from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context()
 def route(r):
  u=urlparse(r.request.url);path=ROOT/u.path.lstrip('/')
  if path.is_dir():path/= 'index.html'
  if u.hostname=='capacity.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404,body='')
 context.route('**/*',route)
 context.add_init_script("""() => {}""")
 context.add_init_script("""window.rawGet=Storage.prototype.getItem; window.rawSet=Storage.prototype.setItem;
 if(!sessionStorage.getItem('seeded')){
 const note='Histórico preservado e medidas do aluno. '.repeat(25000);
 const record={id:10,nome:'Raynara',sexo:'F',idade:'24',altura:'1.60',avaliacoes:[{id:11,data:'06/08/2026',peso:'46',obs:note}]};
 localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([record]));
 localStorage.setItem('avaliacao_treino_antes_uniao',JSON.stringify({avaliacoes:[record],treinos:[]}));
 localStorage.setItem('treinoAlunos','[]');sessionStorage.setItem('seeded','1');}
 """)
 page=context.new_page();page.goto('http://capacity.test/avaliacao.html')
 assert page.evaluate("rawGet.call(localStorage,'avaliacao_fisica_alunos').startsWith('treino36:lz:1:')")
 assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].obs.length") == len('Histórico preservado e medidas do aluno. ')*25000
 # Reproduce a backup-only quota failure: the real registration must still succeed.
 page.evaluate("""() => {const set=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(key==='avaliacao_treino_antes_uniao')throw new DOMException('The quota has been exceeded.','QuotaExceededError');return set.call(this,key,value)};adicionarAvaliacaoAoTreino(10)}""")
 page.locator('.assessment-training-add').click()
 expect(page.locator('.training-student-picker')).to_have_count(0)
 students=page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))")
 assert len(students)==1 and students[0]['nome']=='Raynara'
 assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].obs.length") == len('Histórico preservado e medidas do aluno. ')*25000
 page.reload()
 assert page.evaluate("JSON.parse(localStorage.getItem('treinoAlunos'))[0].nome")=='Raynara'
 assert page.evaluate("JSON.parse(localStorage.getItem('avaliacao_fisica_alunos'))[0].avaliacoes[0].peso")=='46'
 browser.close();print('PASS: lossless migration/reload of large records; extra backup quota does not block adding assessment to training')
