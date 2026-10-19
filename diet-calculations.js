/* Calculations use entered values, never guessed nutrition for food names. */
window.DietCalculations = (() => {
  const normalize = text => String(text).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  function number(value) {
    let text = String(value ?? '').trim().replace(/\s/g, '');
    if (!text) return null;
    if (/^\d{1,3}(?:\.\d{3})+(?:,\d+)?$/.test(text)) text = text.replace(/\./g, '');
    text = text.replace(',', '.');
    if (!/^\d+(?:\.\d+)?$/.test(text)) return null;
    const n = Number(text); return Number.isFinite(n) ? n : null;
  }
  function basal(settings) {
    const age = number(settings.age), weight = number(settings.weight), rawHeight = number(settings.height);
    if (!['F','M'].includes(settings.sex) || !age || !weight || !rawHeight) return null;
    const height = rawHeight < 3.5 ? rawHeight * 100 : rawHeight;
    // Harris–Benedict, matching the reference diet editor without fabricated defaults.
    const value = settings.sex === 'F' ? 655 + 9.6 * weight + 1.8 * height - 4.7 * age : 66 + 13.7 * weight + 5 * height - 6.8 * age;
    return value > 0 ? Math.round(value) : null;
  }
  const macroPatterns = {
    protein: /\b(?:proteinas?|prot|p)\s*[:=]?\s*(\d+(?:[.,]\d+)*)\s*g\b/gi,
    carbs: /\b(?:carboidratos?|carbo|carbs?|c)\s*[:=]?\s*(\d+(?:[.,]\d+)*)\s*g\b/gi,
    fat: /\b(?:gorduras?|gord|lipidios?|g)\s*[:=]?\s*(\d+(?:[.,]\d+)*)\s*g\b/gi
  };
  const sum = values => values.reduce((a,b) => a + b, 0);
  const energy = macros => (macros.protein || 0)*4 + (macros.carbs || 0)*4 + (macros.fat || 0)*9;
  const isDaily = text => /\b(?:resumo|total\s+(?:diario|do dia|geral)|totais(?:\s+do dia)?|calorias\s+(?:do dia|totais))\b/.test(normalize(text));
  function nutrition(sections, settings = {}) {
    const totals = {protein:0, carbs:0, fat:0}, daily = {}, energies = [];
    let explicit = false, missing = 0, count = 0, macrosFound = false;
    for (const section of sections) {
      const summary = isDaily(section.title), raw = section.items.map(normalize), macroStart = raw.findIndex(line => /^macros\s*:?$/.test(line));
      const macroLines = macroStart < 0 ? raw : raw.slice(macroStart+1);
      const values = {};
      for (const [key,pattern] of Object.entries(macroPatterns)) {
        const matches = macroLines.flatMap(line => [...line.matchAll(pattern)].map(m => number(m[1])).filter(value => value !== null));
        if (matches.length) { values[key] = sum(matches); macrosFound = true; if (summary) daily[key] = values[key]; else totals[key] += values[key]; }
      }
      let calorie = null, declared = null;
      const entries = [];
      for (const line of raw) {
        const matches = [...line.matchAll(/(\d+(?:[.,]\d+)*)\s*(?:kcal|calorias)\b/gi)].map(m => number(m[1])).filter(value => value !== null);
        if (!matches.length) continue;
        if (isDaily(line)) { daily.calories = matches.at(-1); continue; }
        if (/\btotal\b/.test(line)) declared = matches.at(-1); else entries.push(...matches);
      }
      if (declared !== null) calorie = declared;
      else if (entries.length) calorie = sum(entries);
      if (summary) { if (calorie !== null) daily.calories = calorie; continue; }
      if (!section.items.length || /^(?:observacoes|orientacoes|recomendacoes)/.test(normalize(section.title))) continue;
      count++;
      if (calorie !== null) { energies.push(calorie); explicit = true; }
      else if (Object.keys(values).length) { energies.push(energy(values)); if(Object.keys(values).length<3)missing++; }
      else missing++;
    }
    const manualMacros = ['protein','carbs','fat'].some(key => number(settings[key]) !== null);
    for (const key of ['protein','carbs','fat']) totals[key] = number(settings[key]) ?? daily[key] ?? totals[key];
    let calories = number(settings.calories), source = 'manual';
    if (calories === null) {
      if (manualMacros) { calories = energy(totals); source = 'macros editados'; if(['protein','carbs','fat'].every(key=>number(settings[key])!==null))missing=0; }
      else if (daily.calories !== undefined) { calories = daily.calories; source = 'total do texto'; missing = 0; }
      else if (Object.keys(daily).some(key => key !== 'calories')) { calories = energy(totals); source = 'macros do dia'; missing = ['protein','carbs','fat'].every(key=>daily[key]!==undefined)?0:Math.max(1,missing); }
      else if (energies.length) { calories = sum(energies); source = explicit ? 'valores do texto' : 'macros (4/4/9)'; }
      else { calories = null; source = 'sem valores informados'; }
    } else missing = 0;
    const tmb = Object.hasOwn(settings,'obsTmb')?number(settings.obsTmb):basal(settings), factor = {baixa:1.2,moderada:1.3,intensa:1.4}[settings.activity] || 1.3;
    const automaticGoal=Object.hasOwn(settings,'obsGoal')?number(settings.obsGoal):(tmb===null?null:Math.round(tmb*factor));
    const goal = number(settings.goal) ?? automaticGoal;
    return {...totals,calories:calories === null ? null : Math.round(calories),source,missing,count,macrosFound:macrosFound||manualMacros,tmb,goal};
  }
  return {number,basal,nutrition};
})();
