/* A prompt handoff for the installed anatomy Skill; no API key or generation request. */
window.WorkoutDemoPrompt=(()=>{
  function textFor(name,style){return [
    'Use a Skill anatomia-exercicios instalada neste ambiente para criar uma demonstração recriada de: '+name+'.',
    'Pesquise primeiro as demonstrações existentes. Se equipamento, apoio ou variação forem ambíguos, confirme só o indispensável antes de criar poses.',
    'Visual: '+(style==='cm'?'traços claros sobre fundo preto.':'anatômico, fundo branco, corpo em cinza/preto e músculos solicitados destacados em vermelho.'),
    'Mantenha corpo e equipamento inteiros, câmera fixa, identidade, proporções, mãos, pés e apoios consistentes. Prepare normalmente quatro poses do início ao extremo, com os dois pontos fixos medidos e alinhamento manual.',
    'Anime com o backend RIFE 4.26 da Skill e FFmpeg. Não substitua o movimento por foto estática, zoom ou dissolvência.',
    'Entregue MP4 H.264/yuv420p, 1920×1080, 5 segundos, 30 fps, 150 quadros, sem áudio, com ida e volta e loop suave.',
    'Reproduza e revise o MP4 exportado, a técnica, as deformações, os apoios e a emenda do loop. Corrija antes de entregar; mantenha relatório e prévia de revisão.',
    'Identifique como demonstração recriada. Entregue o MP4 revisado para eu carregar no exercício do treino36. Não publique no Drive, GitHub ou envie ao aluno nesta etapa.'
  ].join('\n\n');}
  function open({name,style,onFile}){
    const el=(tag,text)=>{const item=document.createElement(tag);if(text)item.textContent=text;return item;},dialog=el('dialog');dialog.id='workoutDemoPrompt';dialog.setAttribute('aria-label','Criar demonstração do exercício');
    const title=el('h3','Criar demonstração · '+name),help=el('p','Copie o pedido e use no ChatGPT ou no Antigravity com a Skill instalada. Depois selecione o MP4 pronto: ele será aplicado a este exercício somente nesta montagem do GIF.'),prompt=el('textarea'),actions=el('div'),copy=el('button','Copiar prompt'),importVideo=el('button','Carregar MP4 gerado'),file=el('input'),close=el('button','Fechar'),status=el('p'),chat=el('a','Abrir ChatGPT'),antigravity=el('a','Site do Antigravity');
    prompt.value=textFor(name,style);prompt.setAttribute('aria-label','Prompt da demonstração');actions.className='demo-prompt-actions';file.type='file';file.accept='video/mp4,video/webm,video/quicktime,.mp4,.m4v,.mov,.webm';file.hidden=true;file.setAttribute('aria-label','MP4 gerado para '+name);status.setAttribute('role','status');
    for(const [link,url] of [[chat,'https://chatgpt.com/'],[antigravity,'https://antigravity.google/']]){link.href=url;link.target='_blank';link.rel='noopener';}
    copy.onclick=async()=>{try{await navigator.clipboard.writeText(prompt.value);status.textContent='Prompt copiado. Cole na ferramenta escolhida.';}catch(e){prompt.focus();prompt.select();status.textContent='Selecione e copie o pedido acima.';}};importVideo.onclick=()=>file.click();file.onchange=()=>{if(onFile?.(file.files?.[0]))dialog.close();else status.textContent='Não foi possível usar este arquivo. Confira o exercício aberto e escolha um vídeo de até 100 MB.';};close.onclick=()=>dialog.close();
    actions.append(copy,importVideo,chat,antigravity,close);dialog.append(title,help,prompt,actions,file,status);dialog.addEventListener('close',()=>dialog.remove(),{once:true});document.body.append(dialog);dialog.showModal();
  }
  return {open,textFor};
})();
