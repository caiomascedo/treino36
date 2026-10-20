const fs=require('fs'),vm=require('vm'),assert=require('assert'),ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('diet-calculations.js','utf8'),ctx);const c=ctx.window.DietCalculations;
for(const [ratio,carbs,calories] of [['2',112,1299],['3',168,1523],['4',224,1747]]){const value=c.weightMacros('56',ratio);assert.equal(value.protein,112);assert.equal(value.fat,44.8);assert.equal(value.carbs,carbs);assert.equal(value.calories,calories);}
assert.equal(c.weightMacros('56,7','2,5').protein,113.4);assert.equal(c.weightMacros('56,7','2,5').fat,45.4);assert.equal(c.weightMacros('56,7','2,5').carbs,141.8);
for(const args of [['','2'],['-1','2'],['56',''],['56','-1'],['abc','2']])assert.throws(()=>c.weightMacros(...args));
for(const [text,result] of [['56×2',112],['56 x 0,8',44.8],['2+3*4',14],['(2+3)*4',20],['1.000 + 12,5',1012.5],['-5+3',-2],['.5 + ,5',1],['0,1+0,2',.3],['56÷2',28]])assert.equal(c.evaluate(text),result,text);
for(const text of ['1/0','alert(1)','1;2','2**4','(2+3','2+)3(','','1e5','Infinity'])assert.throws(()=>c.evaluate(text),text);
console.log('PASS: weight multipliers and kcal 4/4/9, comma fractions, invalid/missing factors, arithmetic precedence/unary/parentheses, decimal formatting, no code evaluation and divide-by-zero handling');

for(const [mode,carbs,calories] of [['deficit',112,1299],['surplus',224,1747],['daily',287.2,2000]]){const result=c.objectiveMacros(56,mode,2000);assert.equal(result.protein,112);assert.equal(result.fat,44.8);assert.equal(result.carbs,carbs);assert.equal(result.calories,calories);}
for(const args of [[null,'deficit'],[56,'tmb'],[56,'daily',null],[56,'daily',800]])assert.throws(()=>c.objectiveMacros(...args));
console.log('PASS: direct objective formulas, maintenance calorie remainder, missing weight/target and insufficient calories rejected');

for(const [ratio,carbs,calories] of [[4.25,238,1803],[4.5,252,1859]]){const result=c.objectiveMacros(56,'surplus',2000,ratio);assert.equal(result.carbs,carbs);assert.equal(result.calories,calories);assert.equal(result.protein,112);assert.equal(result.fat,44.8);}
assert.equal(c.objectiveMacros(56,'deficit',2000,4.5).carbs,112);console.log('PASS: progressive hypertrophy ratios preserve protein/fat and do not alter other objectives');
