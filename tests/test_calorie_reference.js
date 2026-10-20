const fs=require('fs'),vm=require('vm'),assert=require('assert'),ctx={window:{}};
vm.runInNewContext(fs.readFileSync('diet-calculations.js','utf8'),ctx);const C=ctx.window.DietCalculations;
// Independently transcribed from the classic Unimed calculator, retrieved 2026-10-20.
// https://unimed.coop.br/portalunimed/aplicativos/tmb/
for(const [sex,tmb,values] of [['F',1382.6,[1659.12,1797.38,1935.64]],['M',1496.4,[1870.5,2020.14,2169.78]]]){
 for(const [i,activity] of ['nenhuma','moderada','intensa'].entries()){
  const v=C.calorieEstimate('58 kg','153 cm','19 anos',sex,activity);
  assert.equal(v.tmb,tmb);assert.equal(v.gastoTotal,values[i]);
  assert.equal(v.deficit,Math.round((values[i]-500)*100)/100);assert.equal(v.superavit,Math.round((values[i]+500)*100)/100);
  assert.equal(C.calorieEstimate('58','1,53','19',sex,activity).gastoTotal,values[i]);
 }
}
for(const args of [['58','153','19','', 'moderada'],['-58','153','19','F','moderada'],['58','999','19','F','moderada'],['58','153','1199','F','moderada'],['58','153','','F','moderada']])assert.equal(C.calorieEstimate(...args),null);
const noActivity=C.calorieEstimate('58','153','19','F','pesado');assert.equal(noActivity.tmb,1382.6);assert.equal(noActivity.gastoTotal,null);
const macros=C.objectiveMacros(58,'daily',1797.38);assert.equal(macros.protein,116);assert.equal(macros.fat,46.4);assert.equal(macros.carbs,228.9);assert.equal(macros.calories,1797);
console.log('PASS: exact Unimed example for both sexes and all activity levels, units, missing/invalid data, no training-level fallback and maintenance macros');

assert.equal(C.calorieEstimate(58,153,19,'F','intensa').deficit,1435.64);assert.equal(C.calorieEstimate(58,153,19,'F','intensa').superavit,2435.64);
