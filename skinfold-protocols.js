/* Equations and population guidance; measurement sites are not interchangeable. */
window.SkinfoldProtocols=(()=>{
  const catalog={
    jp7:{nome:'Jackson-Pollock (7 Dobras)',nomeCurto:'7 Dobras',campos:()=>['triceps','axilar','torax','abdominal','suprailiaca','subescapular','pregaCoxa'],publico:'Adultos: homens 18–61 anos; mulheres 18–55 anos. Protocolo geral, com mais locais de medição.'},
    pollock3:{nome:'Jackson-Pollock (3 Dobras)',nomeCurto:'3 Dobras',campos:sexo=>sexo==='F'?['triceps','suprailiaca','pregaCoxa']:['torax','abdominal','pregaCoxa'],publico:'Adultos: homens 18–61 anos; mulheres 18–55 anos. Mais rápido; os locais mudam conforme o sexo.'},
    carter6:{adicionais:['torax'],nome:'Carter-Yuhasz (6 Dobras)',nomeCurto:'Carter-Yuhasz 6',campos:()=>['triceps','subescapular','suprailiaca','abdominal','pregaCoxa','panturrilha'],publico:'As seis dobras do cálculo são obrigatórias. Peitoral pode ser registrado como medida adicional e não entra na soma nem na estimativa. Pessoas adultas treinadas / atletas. Não é específico para idosos ou pessoas sedentárias; não usar o nível moderado de treino como critério de validação.'},
    dw4:{nome:'Durnin-Womersley (4 Dobras)',nomeCurto:'Durnin-Womersley 4',campos:()=>['bicipital','triceps','subescapular','suprailiaca'],publico:'16–72 anos, com coeficientes por idade e sexo. Inclui a faixa de idosos de 60–72 anos, mas não é um protocolo específico para idosos frágeis.'},
    registro:{nome:'Registro de dobras (sem estimativa)',nomeCurto:'Registro sem %',campos:()=>['bicipital','triceps','axilar','torax','abdominal','suprailiaca','subescapular','pregaCoxa','panturrilha'],publico:'Acompanhamento das medidas, inclusive quando não há equação adequada à idade/população. Não calcula gordura corporal; compare os mesmos locais.',semCalculo:true},
    yuhasz6:{nome:'Yuhasz (configuração anterior)',nomeCurto:'Yuhasz anterior',campos:()=>['triceps','torax','subescapular','suprailiaca','abdominal','pregaCoxa'],publico:'Configuração anterior com tórax, preservada para consultar registros antigos. Para novas avaliações, use Carter-Yuhasz e meça a panturrilha; não troque um local pelo outro.',legacy:true}
  };
  const number=value=>{const text=String(value??'').trim().replace(',','.');return text!==''&&Number.isFinite(Number(text))?Number(text):null;};
  function validation(id,sex,age){
    const def=catalog[id]||catalog.jp7;if(def.semCalculo||def.legacy)return '';
    if(!['M','F'].includes(sex))return 'Informe o sexo para escolher a equação.';
    if(!Number.isFinite(age)||age<=0)return 'Informe a idade desta avaliação; não será assumida uma idade padrão.';
    if(['jp7','pollock3'].includes(id)&&(age<18||age>(sex==='F'?55:61)))return 'Idade fora da faixa da equação. Considere Durnin-Womersley até 72 anos ou registro sem estimativa.';
    if(id==='dw4'&&(age<16||age>72))return 'Durnin-Womersley: fora de 16–72 anos. Use registro sem estimativa ou avaliação específica.';
    if(id==='carter6'&&(age<18||age>=60))return 'Carter-Yuhasz não é aplicado automaticamente a menores ou idosos. Escolha uma referência adequada ou registro sem estimativa.';
    return '';
  }
  function guidance(id,sex,age){const def=catalog[id]||catalog.jp7;return def.publico+(['jp7','pollock3'].includes(id)&&sex==='F'&&age>40&&age<=55?' A publicação recomenda cuidado adicional na aplicação em mulheres acima de 40 anos.':'')+' '+validation(id,sex,age)+' Dobras são medidas com adipômetro; não são protocolos de balança de bioimpedância.';}
  function densityDW(sum,age,sex){
    if(validation('dw4',sex,age)||!Number.isFinite(sum)||sum<=0)return null;
    const band=age<20?0:age<30?1:age<40?2:age<50?3:4;
    const coefficients=sex==='F'?[[1.1549,.0678],[1.1599,.0717],[1.1423,.0632],[1.1333,.0612],[1.1339,.0645]]:[[1.1620,.0630],[1.1631,.0632],[1.1422,.0544],[1.1620,.0700],[1.1715,.0779]];
    const [a,b]=coefficients[band];return a-b*Math.log10(sum);
  }
  function options(current){return Object.entries(catalog).filter(([id,def])=>!def.legacy||id===current).map(([id,def])=>({id,label:def.nome+(def.legacy?' · revisar locais':'')}));}
  return {catalog,validation,guidance,densityDW,options,number};
})();
