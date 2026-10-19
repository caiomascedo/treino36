const fs=require('fs'),vm=require('vm'),assert=require('assert');
const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('composition-context.js','utf8'),ctx);
const record=ctx.window.CompositionContext.record;
let av={};let patch=record(av,'massaOssea','2','Balança 1',10000);Object.assign(av,{massaOssea:'2'},patch);
assert.equal(av.massaOsseaRegistro.createdAt,10000);assert.equal(av.massaOsseaRegistro.changes.length,1);
patch=record(av,'massaOssea','2,9','Balança 1',11000);Object.assign(av,{massaOssea:'2,9'},patch);
assert.equal(av.massaOsseaRegistro.createdAt,10000);assert.equal(av.massaOsseaRegistro.changes.length,1);assert.equal(av.massaOsseaRegistro.changes[0].value,'2,9');
patch=record(av,'massaOssea','3','Balança 2',12000);Object.assign(av,{massaOssea:'3'},patch);assert.equal(av.massaOsseaRegistro.changes.length,2);assert.equal(av.massaOsseaRegistro.source,'Balança 2');
assert.equal(Object.keys(record(av,'massaOssea','3','Balança 2',13000)).length,0);
const legacy=record({pesoGordura:'20,8'},'pesoGordura','20,5','Balança azul',20000).pesoGorduraRegistro;
assert.equal(legacy.createdAt,null);assert.equal(legacy.changes[0].at,null);assert.equal(legacy.changes[0].value,'20,8');assert.equal(legacy.changes[0].source,'');assert.equal(legacy.changes[1].source,'Balança azul');
for(let i=0;i<20;i++){Object.assign(av,record(av,'massaOssea',String(i),'Balança 2',30000+i*4000));av.massaOssea=String(i);}
assert.equal(av.massaOsseaRegistro.changes.length,8);assert.equal(av.massaOsseaRegistro.changes.at(-1).value,'19');
console.log('PASS: entry/update dates, unknown legacy dates retained, no fabricated prior source, typing coalesced, per-reading sources and bounded history');

assert.equal(ctx.window.CompositionContext.pdfSource({massaOssea:'2',massaOsseaRegistro:{source:'Balança 1'},pesoGordura:'10',pesoGorduraRegistro:{source:'Balança 2'}}),'Balança 1 / Balança 2');
assert.equal(ctx.window.CompositionContext.pdfSource({peso:'50',origemComposicao:'Laudo externo'}),'Laudo externo');
