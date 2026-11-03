/* Prompt handoff for the installed anatomy Skill; generation and delivery run in the chosen tool. */
window.WorkoutDemoPrompt=(()=>{
  const unique=names=>[...new Set(names.map(name=>String(name||'').trim()).filter(Boolean))];
  function textFor(names,style,{tool='chatgpt',whatsapp=''}={}){
    names=unique(Array.isArray(names)?names:[names]);
    return [
      'Use a Skill anatomia-exercicios instalada neste ambiente para criar uma demonstração recriada por exercício selecionado:\n'+names.map((name,i)=>(i+1)+'. '+name).join('\n'),
      'Pesquise primeiro as demonstrações existentes. Se equipamento, apoio ou variação forem ambíguos, confirme só o indispensável antes de criar poses.',
      'Visual: '+(style==='cm'?'traços claros sobre fundo preto.':'anatômico, fundo branco, corpo em cinza/preto e músculos solicitados destacados em vermelho.'),
      'Mantenha corpo e equipamento inteiros, câmera fixa, identidade, proporções, mãos, pés e apoios consistentes. Prepare normalmente quatro poses do início ao extremo, com os dois pontos fixos medidos e alinhamento manual.',
      'Anime com o backend RIFE 4.26 da Skill e FFmpeg. Não substitua o movimento por foto estática, zoom ou dissolvência.',
      'Entregue um MP4 separado por exercício, H.264/yuv420p, 1920×1080, 5 segundos, 30 fps, 150 quadros, sem áudio, com ida e volta e loop suave. Use o nome do exercício no arquivo.',
      'Reproduza e revise cada MP4 exportado, a técnica, as deformações, os apoios e a emenda do loop. Corrija antes de entregar; mantenha relatório e prévia de revisão. Identifique como demonstração recriada.',
      'Publique os MP4s revisados somente no meu Google Drive, junto da minha biblioteca de exercícios. Localize a pasta existente pelo contexto; se não conseguir identificá-la, peça o destino. Retorne os links de cada arquivo para eu carregar no treino36.',
      tool==='antigravity'?'Após salvar no Drive, envie também os vídeos revisados diretamente ao meu próprio WhatsApp'+(whatsapp?' no número '+whatsapp: ' na sessão conectada')+'. Esta instrução autoriza esse envio para mim. Se não houver acesso ao WhatsApp ou não for possível confirmar meu próprio destinatário, informe o impedimento; não substitua o destinatário.':null
    ].filter(Boolean).join('\n\n');
  }
  function open({name,names=[],selectedNames,style,onFile}){
    const available=unique([name,...names]),chosen=new Set(selectedNames||[name||available[0]]);
    const el=(tag,text)=>{const item=document.createElement(tag);if(text)item.textContent=text;return item;},dialog=el('dialog');dialog.id='workoutDemoPrompt';dialog.setAttribute('aria-label','Criar demonstração do exercício');
    const title=el('h3',name?'Criar demonstração · '+name:'Criar demonstrações'),help=el('p','Selecione os exercícios e copie um único pedido. Os vídeos serão publicados no seu Drive pela ferramenta escolhida.'),prompt=el('textarea'),actions=el('div'),copy=el('button','Copiar prompt'),importVideo=el('button','Carregar MP4 gerado'),file=el('input'),close=el('button','Fechar'),status=el('p'),chat=el('a','Abrir ChatGPT'),antigravity=el('a','Site do Antigravity'),youtube=el('a','Pesquisar no YouTube');
    const settings=el('div'),tool=el('select'),phone=el('input'),toolLabel=el('label','Ferramenta '),phoneLabel=el('label','Meu WhatsApp (com DDI, opcional) '),deliveryHelp=el('small','No Antigravity, o pedido inclui envio ao seu WhatsApp, conforme o acesso disponível.');
    tool.setAttribute('aria-label','Ferramenta do prompt');for(const [value,text] of [['chatgpt','ChatGPT'],['antigravity','Antigravity']]){const option=el('option',text);option.value=value;tool.append(option);}
    try{const savedTool=localStorage.getItem('treinoDemoToolV1');if(['chatgpt','antigravity'].includes(savedTool))tool.value=savedTool;}catch(e){}
    phone.type='tel';phone.autocomplete='tel';phone.placeholder='+55 DDD número';phone.setAttribute('aria-label','Meu WhatsApp');try{phone.value=localStorage.getItem('treinoDemoWhatsAppV1')||'';}catch(e){}
    toolLabel.append(tool);phoneLabel.append(phone);settings.className='demo-prompt-settings';settings.append(toolLabel,phoneLabel,deliveryHelp);
    const selection=el('details'),summary=el('summary'),list=el('div'),selectionActions=el('div'),all=el('button','Selecionar todos'),none=el('button','Limpar seleção');selection.className='demo-prompt-selection';selection.open=!name;list.className='demo-prompt-exercises';selectionActions.className='demo-prompt-actions';selectionActions.append(all,none);selection.append(summary,selectionActions,list);
    const fields=available.map(exercise=>{const label=el('label'),check=el('input');check.type='checkbox';check.checked=chosen.has(exercise);check.setAttribute('aria-label',exercise);label.append(check,document.createTextNode(exercise));list.append(label);return {exercise,check};});
    const selected=()=>fields.filter(item=>item.check.checked).map(item=>item.exercise);
    const refresh=()=>{const items=selected();summary.textContent='Exercícios selecionados ('+items.length+'/'+available.length+')';prompt.value=items.length?textFor(items,style,{tool:tool.value,whatsapp:phone.value.trim()}):'';copy.disabled=!items.length;phoneLabel.hidden=tool.value!=='antigravity';deliveryHelp.hidden=tool.value!=='antigravity';youtube.href='https://www.youtube.com/results?search_query='+encodeURIComponent((items[0]||name||'exercício')+' execução');status.textContent='';};
    fields.forEach(item=>item.check.onchange=refresh);all.onclick=()=>{fields.forEach(item=>item.check.checked=true);refresh();};none.onclick=()=>{fields.forEach(item=>item.check.checked=false);refresh();};tool.onchange=()=>{try{localStorage.setItem('treinoDemoToolV1',tool.value);}catch(e){}refresh();};phone.oninput=()=>{try{localStorage.setItem('treinoDemoWhatsAppV1',phone.value);}catch(e){}refresh();};
    prompt.setAttribute('aria-label','Prompt da demonstração');actions.className='demo-prompt-actions';file.type='file';file.accept='video/mp4,video/webm,video/quicktime,.mp4,.m4v,.mov,.webm';file.hidden=true;file.setAttribute('aria-label','MP4 gerado para '+name);status.setAttribute('role','status');
    for(const [link,url] of [[chat,'https://chatgpt.com/'],[antigravity,'https://antigravity.google/']])link.href=url;
    for(const link of [chat,antigravity,youtube]){link.target='_blank';link.rel='noopener';}
    copy.onclick=async()=>{try{await navigator.clipboard.writeText(prompt.value);status.textContent='Prompt copiado. Cole na ferramenta escolhida.';}catch(e){prompt.focus();prompt.select();status.textContent='Selecione e copie o pedido acima.';}};importVideo.onclick=()=>file.click();file.onchange=()=>{if(onFile?.(file.files?.[0]))dialog.close();else status.textContent='Não foi possível usar este arquivo. Confira o exercício aberto e escolha um vídeo de até 100 MB.';};close.onclick=()=>dialog.close();
    actions.append(copy,youtube,chat,antigravity);if(onFile){actions.append(importVideo);help.textContent+=' Carregar MP4 aplica o arquivo somente a '+name+' nesta montagem do GIF.';}actions.append(close);dialog.append(title,help,selection,settings,prompt,actions,file,status);dialog.addEventListener('close',()=>dialog.remove(),{once:true});document.body.append(dialog);refresh();dialog.showModal();
  }
  return {open,textFor};
})();
