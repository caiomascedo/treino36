// Execute: node tests/test_assessment_import.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');
const context = {window:{},localStorage:{getItem:()=>null}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../avaliacao-import.js'),'utf8'),context);
const api = context.window.AvaliacoesJSON;
const base = [{id:100,nome:'Pessoa',treinoStudentId:'t1',treinoStudentIds:['t1','t2'],avaliacoes:[{id:101,data:'01/09/2026',peso:'70',resumo:'Original'},{id:103,data:'03/10/2026',peso:'67'}]}];
const old = api.prepare([{id:100,nome:'Pessoa',avaliacoes:[{id:99,data:'01/08/2026',peso:'80'}]}],base,false).records[0];
assert.equal(old.avaliacoes.at(-1).peso,'67');
assert.equal(old.avaliacoes[0].id,99);
assert.equal(old.treinoStudentIds.join(','),'t1,t2');
for (const choice of [false,true]) {
  const value = api.prepare([{id:100,nome:'Pessoa',avaliacoes:[{id:101,peso:'71'}]}],base,choice).records[0].avaliacoes.find(a=>a.id===101);
  assert.equal(value.peso,choice?'71':'70');
  assert.equal(value.resumo,'Original');
}
const fresh = api.prepare([{id:200,nome:'Outra',treinoStudentId:'t1',treinoStudentIds:['t1'],avaliacoes:[]}],base,false).records.find(a=>a.id===200);
assert.equal(fresh.treinoStudentId,undefined);
assert.equal(fresh.treinoStudentIds,undefined);
assert.throws(()=>api.prepare([{id:200,nome:'Inválida',avaliacoes:[{}]}],base,false));
assert.throws(()=>api.prepare([{id:200,nome:'Outra',avaliacoes:[{id:101,peso:'65'}]}],base,false));
assert.equal(JSON.stringify(api.prepare(base,base,false).records),JSON.stringify(base));
assert.equal(api.isAssessmentPayload({alunos:[{nome:'Treino',treino:{A:[]}}]}),false);
console.log('PASS: histórico por data, conflitos, vínculos confirmados, IDs, arquivo inválido e reimportação sem duplicatas');
