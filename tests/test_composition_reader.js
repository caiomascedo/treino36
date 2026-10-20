const fs=require('fs'),vm=require('vm'),assert=require('assert'),ctx={window:{}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('composition-reader.js','utf8'),ctx);const C=ctx.window.CompositionReader;
function parsed(file){return C.parse(fs.readFileSync('tests/fixtures/composition/'+file+'.txt','utf8'));}
function values(result){return Object.fromEntries(result.candidates.map(c=>[c.key,Number(c.value)]));}
const f=parsed('fitdays');console.log(f.candidates.map(c=>c.key+':'+c.value).join(', '));assert.equal(f.source,'Fitdays');const fv=values(f);
for(const [k,v] of Object.entries({peso:77.6,imc:27.8,gordura:27.9,massaMuscularPct:67.6,massaLivreGordura:55.9,gorduraSubcutanea:18.6,visceral:10.8,agua:49.5,musculoEsqueleticoPct:49.5,massamuscular:52.5,massaOssea:2.9,proteina:18.8,metabolismoInformado:1597,idadeMetabolica:32}))assert.equal(fv[k],v,k);
assert.equal(f.date,'12/08/2026');assert.equal(f.time,'22:12');
const p=parsed('planilha'),pv=values(p);console.log(pv);for(const [k,v] of Object.entries({peso:58.7,imc:25.4,gordura:35.4,pesoGordura:20.8,musculoEsqueleticoPct:34.1,musculoEsqueleticoKg:20,massaMuscularPct:59.8,massamuscular:35,metabolismoInformado:1197.8,altura:152,idade:17}))assert.equal(pv[k],v,k);for(const key of ['agua','pesoAgua','visceral'])assert(!(key in pv),key);
const b=parsed('inbody'),bv=values(b);console.log(bv);for(const [k,v] of Object.entries({peso:56.9,aguaLitros:27.2,proteinaKg:7.2,mineraisKg:2.84,pesoGordura:19.7,pontuacaoInbody:67,pesoIdealInbody:56.5,controlePesoInbody:-.4,controleGorduraInbody:-6.7,controleMuscularInbody:6.3,musculoEsqueleticoKg:19.7,massaLivreGordura:37.2,metabolismoInformado:1174,rcqInformado:.86,visceral:10,grauObesidadeInbody:101,imc:21.2,gordura:34.6,magra_bracoDireito:1.61,gordura_tronco:10,impedancia20_bd:474.1,impedancia100_pe:319.1}))assert.equal(bv[k],v,k);
assert.equal(b.candidates.find(c=>c.key==='aguaLitros').refMin,28.8);assert.equal(b.sex,'F');assert(!b.candidates.some(c=>c.key==='peso'&&c.value==='99.9'));
const ambiguous=C.parse('Massa muscular 52\nÁgua corporal 49\nGordura corporal 25');assert.equal(ambiguous.candidates.length,0);assert(ambiguous.unresolved.length);
const conflicts=C.parse('Peso 70 kg\nPeso 71 kg');assert(conflicts.candidates.every(c=>c.conflict&&!c.selected));
assert.equal(C.parse([{text:'Peso 70 kg',confidence:50}]).candidates[0].selected,false);
assert.equal(C.parse('Gordura corporal 200 %').candidates[0].valid,false);
console.log('PASS: Fitdays, planilha and InBody field identities/units, reference limits, signed control targets, segments, impedance, history exclusion, missing/ambiguous values and confidence/conflicts');

assert.equal(values(C.parse('Fitdays\nPeso 77.6kg\nMassa Muscular 52.5kg\nTMB 1597kcal')).massamuscular,52.5);

assert.equal(values(C.parse('Idade Metabdlica 32')).idadeMetabolica,32);assert(!('idade' in values(C.parse('Idade AlgumaCoisa 32'))));
assert.equal(values(C.parse('Controle de Peso − 0,4 kg')).controlePesoInbody,-.4);assert.equal(C.parse('Proteína (kg) (7,7-9,4)').candidates.length,0);

const av={id:1,peso:'72',ficha:{altura:'1.63'},agua:'50'},person={id:2,altura:'1.63',avaliacoes:[av]};const report=C.parse('Peso 77.6 kg\nIMC 27.8\nIdade Metabólica 32\nMetabolismo 1597 kcal');const change=C.prepare({person,av},report,report.candidates);assert.equal(change.fields.metabolismoInformado,'1597');assert(!('tmb' in change.fields));assert(!('agua' in change.fields));
const imported={...av,...change.fields};assert.equal(C.reportedValue(person,imported,'imc','calculado'),'27.8');assert.equal(C.reportedValue(person,{...imported,peso:'78'},'imc','calculado'),'calculado');
ctx.TreinoStorage={stageAssessment(){throw Error('quota');}};assert.throws(()=>C.commit({person,av},change,p=>{p.avaliacoes[0].imc='99';}));assert.equal(av.peso,'72');assert.equal(av.imc,undefined);
assert.equal(C.parse('09:53\nInBody\n11/05/2022 12:11').time,'12:11');assert.equal(C.parse('Data 99/99/2026').date,'');
console.log('PASS: reported vs calculated TMB, protected report IMC, changed-measurement invalidation, missing-field preservation, atomic write failure and document vs phone time');

const positioned=[],r=(text,x,y,width=80)=>{const word={text,x0:x,x1:x+width,y0:y,y1:y+10};positioned.push({text,confidence:100,words:[word]});};
r('InBody',0,0);r('Análise da Massa Magra Segmentar',0,100,200);r('Análise da Gordura Segmentar',250,100,200);
for(const offset of [0,250]){r('Esquerdo',offset+5,170);r('Direito',offset+190,170);for(const [value,x,y] of [[1.1,30,140],[1.2,160,140],[10,100,210],[4.1,30,270],[4.2,160,270]])r(value+'kg',offset+x,y,35);}
r('Histórico da Composição Corporal',0,400,300);const diagram=C.parse(positioned);assert.equal(values(diagram).magra_bracoEsquerdo,1.1);assert.equal(values(diagram).magra_bracoDireito,1.2);assert(diagram.candidates.filter(c=>c.key.startsWith('magra_')||c.key.startsWith('gordura_')).every(c=>!c.selected&&c.review.includes('confirme')));
console.log('PASS: positioned InBody diagram values require explicit review of anatomical regions/sides');
