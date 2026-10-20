const fs=require('fs'),vm=require('vm'),assert=require('assert');const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('workout-sequence.js','utf8'),ctx);const s=ctx.window.WorkoutSequence;
for(const division of ['A','AB','ABC','ABCD','ABCDE','ABCDEF']){
 const student={student_id:'a',treino_id:'w',secaoFAtiva:division.includes('F'),treino:Object.fromEntries([...division].map(key=>[key,['Agachamento 3x10']]))};
 assert.equal(s.tracking(student),false);assert.equal(s.summary(student),'');student.acompanharSequencia=true;
 assert.equal(s.enabled(student),division.length<5);
 if(division.length>=5)assert.equal(s.summary(student),'');
 assert.equal(s.describe(student).next,'A');
 for(const key of division){assert.equal(s.describe(student).next,key);student.sequenciaTreino=s.mark(student,key,'2026-10-20T15:00:00Z');assert.equal(s.get(student).ultima,key);}
 assert.equal(s.describe(student).next,'A');assert.equal(s.get(student).anterior?.anterior,null);
 const other={...student,student_id:'b',sequenciaTreino:null};assert.equal(s.get(other),null);
 student.treino_id='another';assert.equal(s.get(student),null);assert.equal(s.describe(student).next,'A');
}
const a={treino_id:'w',treino:{A:['Agachamento'],B:['Sem treino cadastrado'],C:['Supino'],F:['Mobilidade']},secaoFAtiva:false};
assert.deepEqual(Array.from(s.sections(a)),['A','C']);a.sequenciaTreino=s.mark(a,'C');assert.equal(s.describe(a).next,'A');
assert.throws(()=>s.mark(a,'B'));assert.throws(()=>s.mark(a,'F'));a.secaoFAtiva=true;assert.equal(s.describe(a).next,'F');
delete a.treino.C;assert.equal(s.describe(a).removed,true);assert.equal(s.describe(a).next,'A');
assert.equal(s.sanitize({treinoId:'w',ultima:'G',feitoEm:'today'}),null);assert.equal(s.summary({treino:{}}),'');
console.log('PASS: A/AB/ABC/ABCD/ABCDE/ABCDEF cycles, sparse sections, placeholders, hidden F, manual skips, bounded undo, invalid records, removed sections and workout isolation');
