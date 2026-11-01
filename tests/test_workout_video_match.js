const fs=require('fs'),vm=require('vm'),assert=require('assert');global.window={};
vm.runInThisContext(fs.readFileSync(__dirname+'/../workout-video-match.js','utf8'));
const m=window.WorkoutVideoMatch;
const cm=JSON.parse(fs.readFileSync(__dirname+'/../cmfit-catalog.json')).videos.map(v=>({...v,collection:'cm'}));
const gym=JSON.parse(fs.readFileSync(__dirname+'/../gymfaster-catalog.json')).videos.map(v=>({...v,collection:'gymfaster'}));
const all=[...cm,...gym];
function get(name,mode='cm',video=''){return m.resolve({nome:name,video},all,mode);}
for(const [input,expected] of [['Ag. Smith','agachamento smith'],['Cad extensora','cadeira extensora'],['Adutor','cadeira adutora'],['Abdutor','cadeira abdutora'],['Step Up','subida step'],['Glúteo na polia','gluteo polia'],['Sup Máquina','supino maquina']]){
 const result=get(input);assert(result.video,input);assert.strictEqual(m.canonical(result.video.name),expected,input);
}
assert.strictEqual(get('Leg Press 45').video.id,'1wq8rmGfeoY0pyiq3eXo90SHPx1ePSN1v');
for(const input of ['Ag Sumô','Ag Frontal']){const result=get(input);assert(!result.video,input);assert(result.suggestions.length,input);}
const cable=get('Glúteo na polia','gymfaster');assert(!cable.video);assert(cable.suggestions.every(v=>v.collection==='cm'));assert(cable.suggestions.every(v=>m.canonical(v.name).includes('polia')));
const press=get('Leg Press 45','gymfaster');assert(!press.video);assert(press.suggestions.length);assert(!press.suggestions.some(v=>/panturrilha/i.test(v.name)));
assert.deepStrictEqual(m.parts('Leg Press 45 + Ag Sumo'),['Leg Press 45','Ag Sumo']);assert.deepStrictEqual(m.parts('Agachamento'),['Agachamento']);
const other=get('Cadeira Extensora','gymfaster');const cross=get('Cadeira Extensora','cm',other.video.url);assert(cross.video.collection==='cm');
const custom=all.find(v=>v.collection==='gymfaster'&&/Leg Press 45/.test(v.name));assert.strictEqual(m.resolve({nome:'Leg Press 45'},all,'gymfaster',custom.id).video.id,custom.id);
for(const term of ['Crucifixo inverso na polia','Rosca direta alternada','Agachamento unilateral','Gluteo coice na polia com perna reta']){
 const result=get(term);if(result.video){if(/inverso/.test(term))assert(/inverso/.test(result.video.name));if(/alternada/.test(term))assert(/alternad/.test(result.video.name));}
}
console.log('PASS: abbreviations, synonyms, combinations, remembered choices, independent libraries, explicit equipment/angle variants and cable-vs-machine safety');

assert.deepStrictEqual(m.parts('Agachamento No\nSmith + Agachamento Sumô\nCom Halteres'),['Agachamento No\nSmith','Agachamento Sumô\nCom Halteres']);
for(const line of ['Cadeira Extensora 3x8+10','Supino + elástico','Cadeira Extensora + curtinhas'])assert.deepStrictEqual(m.parts(line),[line]);
