const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
let saved = [];
const ctx = {window: {}, AvaliacaoTreinoSync: {
  key: 'assessments', read: () => saved,
  link(record, id) {
    record.treinoStudentIds = [...new Set([...(record.treinoStudentIds || []), record.treinoStudentId, id].filter(Boolean))];
    if (!record.treinoStudentId) record.treinoStudentId = id;
  }
}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(root, 'avaliacao-import.js'), 'utf8'), ctx);
ctx.AvaliacoesJSON = ctx.window.AvaliacoesJSON;
vm.runInContext(html.slice(html.indexOf('  function prepararAvaliacoesBackupCompleto('), html.indexOf('  function abrirImportacaoCompleta(')), ctx);
const clone = value => JSON.parse(JSON.stringify(value));
const raw = {alunos:[{student_id:'s1',nome:'Ana',avaliacaoId:20}],avaliacoes:[
  {id:10,nome:'Ana',treinoStudentId:'s1',avaliacoes:[{id:11,peso:'60'}]},
  {id:20,nome:'Ana Vitória',avaliacoes:[{id:11,peso:'70'}]}
]};
const original = JSON.stringify(raw), students = clone(raw.alunos);
const plan = ctx.prepararAvaliacoesBackupCompleto(raw, students);
assert.equal(plan.linkWarnings.length, 1);
assert.equal(students[0].avaliacaoId, undefined);
assert.equal(plan.records.length, 2);
assert.equal(plan.records[0].avaliacoes[0].peso, '60');
assert.equal(plan.records[1].avaliacoes[0].peso, '70');
assert.ok(plan.records.every(p => !p.treinoStudentId));
assert.equal(JSON.stringify(raw), original);
const valid = clone(raw); valid.alunos[0].avaliacaoId = 10;
assert.equal(ctx.prepararAvaliacoesBackupCompleto(valid, clone(valid.alunos)).records[0].treinoStudentId, 's1');
const invalid = clone(raw); invalid.avaliacoes[0].treinoStudentId = 'missing';
assert.throws(() => ctx.prepararAvaliacoesBackupCompleto(invalid, clone(invalid.alunos)), /não corresponde/);
if (process.argv[2]) {
  const backup = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const imported = clone(backup.alunos);
  for (const s of imported) {
    ctx.validarTreinoImportado(s);
    for (const version of s.historicoTreinos || []) ctx.validarTreinoImportado(clone(version));
  }
  const result = ctx.prepararAvaliacoesBackupCompleto(backup, imported);
  assert.equal(imported.length, 62);
  assert.equal(result.records.length, 26);
  assert.equal(result.records.flatMap(p => p.avaliacoes).length, 27);
  assert.equal(result.linkWarnings.length, 1);
  for (const p of backup.avaliacoes) {
    const out = result.records.find(r => r.id === p.id);
    for (let i = 0; i < p.avaliacoes.length; i++) {
      const a = p.avaliacoes[i], b = out.avaliacoes.find(r => r.data === a.data);
      for (const key of Object.keys(a)) if (key !== 'id') assert.equal(JSON.stringify(b[key]), JSON.stringify(a[key]));
    }
  }
  saved = result.records;
  const again = ctx.prepararAvaliacoesBackupCompleto(backup, clone(backup.alunos));
  assert.equal(JSON.stringify(again.records), JSON.stringify(result.records));
  console.log('PASS real backup: 62 alunos, 26 cadastros, 27 avaliações; treino, histórico, vínculos, fotos e reimportação.');
}
console.log('PASS complete backup links: conflicts preserved separately, valid links retained, unknown students rejected.');
