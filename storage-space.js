/* Storage figures describe this browser, never the phone's total free space. */
(()=>{
  const mb=bytes=>(bytes/1024/1024).toLocaleString('pt-BR',{maximumFractionDigits:2})+' MB';
  function mount(){
    const menu=document.querySelector('#moreOptions .more-options-menu');if(!menu)return;
    const open=document.createElement('button');open.type='button';open.id='storageSpaceBtn';open.textContent='💾 Espaço e fotos';menu.append(open);
    const dialog=document.createElement('dialog');dialog.id='storageSpaceDialog';dialog.style.cssText='max-width:480px;width:calc(100% - 32px);box-sizing:border-box;border:1px solid #cbd5e1;border-radius:12px;padding:18px;color:#29465a;background:white';
    dialog.innerHTML='<h3 style="margin-top:0">Espaço e fotos</h3><p data-usage></p><p data-capacity style="font-size:12px"></p><p style="font-size:13px">Reduz as fotos grandes para até 900 × 1.200 pixels, sem excluir fotos, alunos ou avaliações. As linhas e a logo são mantidas. Seu backup JSON anterior conserva as imagens anteriores à redução.</p><p role="status" style="font-size:13px"></p><div style="display:flex;flex-wrap:wrap;gap:8px"><button type="button" data-backup>Salvar backup JSON</button><button type="button" data-optimize>Liberar espaço das fotos</button><button type="button" data-close>Fechar</button></div>';
    document.body.append(dialog);const q=s=>dialog.querySelector(s),status=q('[role=status]');let busy=false;
    async function show(){q('[data-usage]').textContent='Dados locais usados: '+mb(TreinoStorage.usage())+'.';q('[data-capacity]').textContent='O limite local varia conforme o navegador. Esse número não é o espaço livre do celular.';dialog.showModal();try{const estimate=await navigator.storage?.estimate?.();if(estimate?.quota&&Number.isFinite(estimate.usage))q('[data-capacity]').textContent+=' O navegador informa '+mb(Math.max(0,estimate.quota-estimate.usage))+' disponíveis no armazenamento geral do site, mas os dados locais das fotos têm um limite separado e menor.';}catch(error){}}
    open.onclick=show;q('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('cancel',event=>{if(busy)event.preventDefault();});
    q('[data-backup]').onclick=()=>document.querySelector('#exportBtn').click();
    q('[data-optimize]').onclick=async()=>{
      if(busy)return;busy=true;dialog.querySelectorAll('button').forEach(b=>b.disabled=true);status.textContent='Otimizando as fotos. Aguarde…';
      let message;
      try{const result=await TreinoStorage.optimizePhotos((current,total)=>{status.textContent='Otimizando dados '+current+' de '+total+'…';});message='Espaço liberado: '+mb(Math.max(0,result.before-result.after))+'. Dados locais usados: '+mb(result.after)+'.'+(result.failed?' Alguns arquivos não puderam ser otimizados e foram mantidos.':'')+(result.conflicts?' Alguns dados mudaram durante a operação; tente novamente para otimizar o restante.':'');if(result.before===result.after)message+=' As fotos atuais já estão compactas. Se o limite continuar cheio, será necessário retirar fotos antigas após guardar o backup.';}
      catch(error){message='Não foi possível concluir a otimização. Os arquivos que não puderam ser reduzidos foram mantidos.';}
      // Reload before any older in-memory pupil snapshot can overwrite optimized photos.
      try{sessionStorage.setItem('treino36_storage_result',message);}catch(error){}
      location.reload();
    };
    const result=sessionStorage.getItem('treino36_storage_result');if(result){sessionStorage.removeItem('treino36_storage_result');status.textContent=result;show();}
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();
