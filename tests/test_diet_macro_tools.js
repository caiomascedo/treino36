const fs=require('fs'),vm=require('vm'),assert=require('assert'),ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('diet-calculations.js','utf8'),ctx);const c=ctx.window.DietCalculations;
for(const [ratio,carbs,calories] of [['2',112,1299],['3',168,1523],['4',224,1747]]){const value=c.weightMacros('56',ratio);assert.equal(value.protein,112);assert.equal(value.fat,44.8);assert.equal(value.carbs,carbs);assert.equal(value.calories,calories);}
assert.equal(c.weightMacros('56,7','2,5').protein,113.4);assert.equal(c.weightMacros('56,7','2,5').fat,45.4);assert.equal(c.weightMacros('56,7','2,5').carbs,141.8);
for(const args of [['','2'],['-1','2'],['56',''],['56','-1'],['abc','2']])assert.throws(()=>c.weightMacros(...args));
for(const [text,result] of [['56×2',112],['56 x 0,8',44.8],['2+3*4',14],['(2+3)*4',20],['1.000 + 12,5',1012.5],['-5+3',-2],['.5 + ,5',1],['0,1+0,2',.3],['56÷2',28]])assert.equal(c.evaluate(text),result,text);
for(const text of ['1/0','alert(1)','1;2','2**4','(2+3','2+)3(','','1e5','Infinity'])assert.throws(()=>c.evaluate(text),text);
console.log('PASS: weight multipliers and kcal 4/4/9, comma fractions, invalid/missing factors, arithmetic precedence/unary/parentheses, decimal formatting, no code evaluation and divide-by-zero handling');
