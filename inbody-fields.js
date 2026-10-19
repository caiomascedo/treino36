/* Optional transcription of the supplied InBody120 report, never a device calculation. */
window.InBodyFields=(()=>{
  const field=(key,label,group,description,kind='measurement')=>({key,label:label.includes('InBody')?label:label+' · InBody',group,description,kind,report:'InBody'});
  const fields=[
    field('aguaLitros','Água corporal total (L) · InBody','inbody','Volume de água corporal informado no laudo. É o mesmo indicador de água corporal em outra unidade; não converte nem substitui o valor em %.'),
    field('proteinaKg','Proteína (kg) · InBody','inbody','Massa de proteínas informada no laudo. Usa kg, em vez do percentual de proteína.'),
    field('mineraisKg','Minerais (kg) · InBody','inbody','Minerais totais estimados no laudo. Não são sinônimo de massa óssea nem uma medida de densidade mineral óssea.'),
    field('pontuacaoInbody','Pontuação InBody (pontos)','inbody','Pontuação emitida pelo equipamento. Pode ultrapassar 100 em pessoas com mais massa muscular; não é um diagnóstico isolado.','score'),
    field('pesoIdealInbody','Peso ideal / alvo (kg) · InBody','inbody','Peso-alvo definido pelo laudo, diferente da faixa de peso estimada pelo IMC no aplicativo.','target'),
    field('controlePesoInbody','Controle de peso (kg) · InBody','inbody','Ajuste de peso sugerido pelo equipamento; valores negativos indicam redução e positivos, aumento. Não é uma prescrição automática.','target'),
    field('controleGorduraInbody','Controle de gordura (kg) · InBody','inbody','Ajuste de massa de gordura sugerido pelo laudo, com sinal positivo ou negativo.','target'),
    field('controleMuscularInbody','Controle muscular (kg) · InBody','inbody','Ajuste muscular sugerido pelo laudo; não é a massa muscular medida.','target'),
    field('rcqInformado','Relação cintura/quadril · InBody','inbody','RCQ informada pelo laudo. É o mesmo índice que pode ser calculado pelas circunferências, com origem de medição diferente.'),
    field('grauObesidadeInbody','Grau de obesidade (%) · InBody','inbody','Relação entre peso e peso-padrão do aparelho. Não é percentual de gordura e não equivale às classes clínicas de obesidade do IMC.'),
    field('idLaudoInbody','ID do exame · InBody','inbody','Identificador do exame no laudo, sem substituir o cadastro do aluno.','text'),
    field('horaLaudoInbody','Horário do exame · InBody','inbody','Horário informado no laudo; a data continua na própria avaliação.','text')
  ];
  const segments=[['bracoDireito','braço direito'],['bracoEsquerdo','braço esquerdo'],['tronco','tronco'],['pernaDireita','perna direita'],['pernaEsquerda','perna esquerda']];
  for(const [key,name] of segments){
    fields.push(field('magra_'+key,'Massa magra · '+name+' (kg)','inbody-lean','Massa magra segmentar informada pela InBody. Inclui tecidos sem gordura; não equivale à massa muscular esquelética isolada.'));
    fields.push(field('adequacaoMagra_'+key,'Adequação massa magra · '+name+' (%)','inbody-lean','Percentual em relação à referência segmentar do laudo InBody. Não é percentual do peso corporal. Use a classificação do próprio laudo.'));
    fields.push(field('gordura_'+key,'Gordura · '+name+' (kg)','inbody-fat','Massa de gordura segmentar informada no laudo InBody.'));
    fields.push(field('adequacaoGordura_'+key,'Adequação gordura · '+name+' (%)','inbody-fat','Percentual relativo ao padrão segmentar do laudo InBody; não é o percentual de gordura corporal total.'));
  }
  for(const hz of [20,100])for(const [key,name] of [['bd','braço direito'],['be','braço esquerdo'],['tr','tronco'],['pd','perna direita'],['pe','perna esquerda']])fields.push(field('impedancia'+hz+'_'+key,'Impedância '+hz+' kHz · '+name+' (Ω)','inbody-impedance','Impedância segmentar a '+hz+' kHz transcrita do laudo InBody. Não permite, isoladamente, classificar alguém como saudável.','impedance'));
  return {fields};
})();
