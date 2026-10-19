from pathlib import Path
from urllib.parse import urlparse
import urllib.request,fitz
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
LIBS=['https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js','https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.28/jspdf.plugin.autotable.min.js']
scripts={url:urllib.request.urlopen(url,timeout=30).read() for url in LIBS}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':390,'height':844})
 def route(r):
  if r.request.url in scripts:r.fulfill(body=scripts[r.request.url],content_type='application/javascript');return
  u=urlparse(r.request.url);path=ROOT/u.path.strip('/')
  if path.is_dir():path/='index.html'
  if u.hostname=='app.test' and path.is_file():r.fulfill(body=path.read_bytes(),content_type={'.js':'application/javascript','.css':'text/css'}.get(path.suffix,'text/html'))
  else:r.fulfill(status=404,body='')
 context.route('**/*',route);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://app.test/treino36/avaliacao.html')
 page.evaluate("""()=>{localStorage.setItem('treinoAlunos','[]');localStorage.setItem('avaliacao_fisica_alunos',JSON.stringify([{id:10,nome:'Ana',sexo:'F',idade:'30',altura:'1.60',composicaoExtras:['pesoGordura','musculoEsqueleticoKg'],medidasExtras:['antebraco'],avaliacoes:[{id:11,data:'01/09/2026',peso:'60',gordura:'25',massamuscular:'25',pesoGordura:'15',musculoEsqueleticoKg:'18',peitoral:'90',biceps:'30 / 28',coxa:'50 / 48',antebraco:'24 / 22',triceps:'10'},{id:12,data:'01/10/2026',peso:'62',gordura:'24',massamuscular:'26',pesoGordura:'14',musculoEsqueleticoKg:'19',peitoral:'89',biceps:'31 / 27',coxa:'49 / 49',antebraco:'25 / 21',triceps:'9'}]}]));}""");page.reload()
 with page.expect_download() as downloaded:page.evaluate("gerarPDFAluno(10,{mode:'completo',viewer:null})")
 file=downloaded.value;file.save_as('/tmp/treino36-assessment-emerald.pdf')
 green=0x1e6f3f;red=0xbe2d2d
 with fitz.open(file.path()) as pdf:
  spans=[span for pg in pdf for block in pg.get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for span in line['spans']]
  positive=[s for s in spans if '(+' in s['text']];negative=[s for s in spans if '(-' in s['text']]
  assert len(positive)>=5 and len(negative)>=5,[(s['text'],hex(s['color'])) for s in spans]
  assert all(s['color']==red for s in positive),positive
  assert all(s['color']==green for s in negative),negative
  assert any('(+1,0)' in s['text'] for s in positive) and any('(-1,0)' in s['text'] for s in negative)
  # Base readings remain neutral, not colored along with the variation.
  assert any(s['text'].strip()=='62' and s['color'] not in [red,green] for s in spans)
  title=next(s for s in spans if s['text']=='AVALIAÇÃO FÍSICA');assert title['color']==green,title
  fills=[d.get('fill') for pg in pdf for d in pg.get_drawings() if d.get('fill')]
  assert any(all(abs(a-b)<.005 for a,b in zip(fill,[30/255,111/255,63/255])) for fill in fills)
  assert not any(all(abs(a-b)<.005 for a,b in zip(fill,[230/255,57/255,57/255])) for fill in fills)
  assert all(pg.rect.width<pg.rect.height for pg in pdf)
  pdf[0].get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save('/tmp/treino36-assessment-emerald.png')
 page.evaluate("alunos[0].avaliacoes.forEach(av=>av.protocolo='registro')")
 with page.expect_download() as registered:page.evaluate("gerarPDFAluno(10,{mode:'completo',viewer:null})")
 with fitz.open(registered.value.path()) as manual_pdf:
  manual_text=' '.join(pg.get_text() for pg in manual_pdf)
  assert 'Registro sem %' in manual_text,manual_text
  assert '10.00 mm' in manual_text and '9.00 mm' in manual_text,manual_text
 assert not errors,errors
 browser.close();print('PASS: actual assessment PDF emerald accents; positive deltas red and negative green across composition/extras/measures/paired values/skinfolds; original values neutral and layout retained')
