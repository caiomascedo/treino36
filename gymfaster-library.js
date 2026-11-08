/* Verified Drive catalog. Selection is explicit: exercise variants are never replaced automatically. */
window.GymFasterLibrary = (() => {
  'use strict';
  let catalog, pending, dialog, selection, previousFocus,showDeleted=false,lastRemoved=null,notice='';
  const el = (tag, attrs = {}, text) => {
    const node = document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  async function load() {
    const videos = await WorkoutCatalog.load();
    catalog = {videos:videos.filter(video=>video.collection!=='cm')}; return catalog;
  }
  function create() {
    dialog = el('dialog', {id: 'gymfasterLibrary', 'aria-labelledby': 'gymfasterTitle'});
    const heading = el('h3', {id: 'gymfasterTitle'}, 'Biblioteca de vídeos');
    const help = el('p', {class: 'gym-help'});
    const search = el('input', {type: 'search', placeholder: 'Buscar exercício ou equipamento', 'aria-label': 'Buscar na biblioteca de vídeos'});
    const searchRow=el('div',{class:'video-search-row'}),clearSearch=el('button',{type:'button',class:'video-search-clear','aria-label':'Limpar pesquisa',title:'Limpar pesquisa'},'×');searchRow.append(search,clearSearch);
    const filters = el('div', {class: 'gym-filters'});
    const group = el('select', {'aria-label': 'Categoria dos vídeos'});
    const gender = el('select', {'aria-label': 'Versão dos vídeos'});
    group.append(el('option', {value: ''}, 'Todos os grupos'));
    gender.append(el('option', {value: ''}, 'Todas as versões'));
    const favoriteLabel=el('label',{class:'video-favorites-filter'}),favoriteOnly=el('input',{type:'checkbox','aria-label':'Somente favoritos'});favoriteLabel.append(favoriteOnly,document.createTextNode(' ★ Favoritos'));favoriteOnly.onchange=()=>{browser.scrollTop=0;render();};filters.append(group,gender,favoriteLabel);
    const status = el('p', {role: 'status'}), list = el('div', {class: 'gym-results'});
    const preview = el('div', {class: 'gym-preview', hidden: ''});
    const addVideo=el('button',{type:'button'},'Adicionar vídeo');addVideo.onclick=()=>WorkoutCatalog.openAdd(async asset=>{await load();if(selection){selection.apply(asset);dialog.close();return;}controls.search.value=asset.name;controls.group.value='';controls.gender.value='';controls.render();},{name:selection?.name||search.value,group:group.value});
    const libraryTools=el('div',{class:'gym-library-tools'}),removed=el('button',{type:'button'},'Ver apagados'),undo=el('button',{type:'button',hidden:''},'Desfazer exclusão'),libraryHint=el('small',{},'Em Ver apagados, restaure ou apague definitivamente desta biblioteca neste navegador.');libraryTools.append(removed,undo,WorkoutVideoLibrary.reviewButton(),libraryHint);
    const drive = el('a', {target:'_blank',rel:'noopener noreferrer'}, 'Abrir coleção unificada no Drive');
    const close = el('button', {type: 'button', class: 'gym-close'}, 'Fechar');
    function clearPreview() { preview.querySelectorAll('video').forEach(video => { video.pause(); video.removeAttribute('src'); video.load(); }); preview.replaceChildren(); preview.hidden = true; }
    close.onclick = () => dialog.close();
    const browser=el('div',{class:'video-browser-scroll'});browser.append(heading,help,drive,searchRow,filters,status,addVideo,libraryTools,preview,list);dialog.append(browser,close);
    document.body.append(dialog);
    document.addEventListener('click', event => { if (dialog.open && !preview.hidden && !preview.contains(event.target)) clearPreview(); }, true);
    dialog.addEventListener('close', () => { clearTimeout(searchTimer);rememberSearch(true);clearPreview(); selection = null; if (previousFocus?.isConnected) previousFocus.focus(); });
    function rememberSearch(force=false){if(selection||(!dialog.open&&!force))return;try{localStorage.setItem('treinoGeneralVideoSearchV1',JSON.stringify({query:search.value,group:group.value,gender:gender.value,scroll:browser.scrollTop}));}catch(e){}}
    let searchTimer;browser.addEventListener('scroll',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(rememberSearch,120);},{passive:true});
    function render() {
      const scroll=browser.scrollTop;list.replaceChildren(); clearPreview();
      if (!catalog) return;
      drive.href=WorkoutCatalog.folderURL;drive.hidden=!WorkoutCatalog.folderURL;
      const words = normalize(search.value).split(' ').filter(Boolean);
      const all=WorkoutVideoLibrary.apply(catalog.videos,true),available=all.filter(v=>!v.removed),deleted=all.length-available.length;removed.textContent=showDeleted?'Voltar aos disponíveis':'Ver apagados ('+deleted+')';removed.disabled=!deleted&&!showDeleted;undo.hidden=!all.some(v=>v.id===lastRemoved&&v.removed);
      const matches = all.filter(video => (!favoriteOnly.checked||WorkoutVideoLibrary.isFavorite(video.id)) && video.removed===showDeleted && (!group.value || video.group === group.value) && (!gender.value || video.gender === gender.value) && words.every(word => normalize([video.name,...(video.aliases||[])].join(' ')).includes(word)));
      status.textContent = (notice?notice+' ':'')+matches.length + ' de ' + (showDeleted?deleted:available.length) + (showDeleted?' vídeos apagados. ':' vídeos disponíveis. ') + (deleted?'('+deleted+' apagados da sua lista) ':'') + (matches.length ? 'Confira o aparelho e a variação antes de escolher.' : 'Tente menos palavras ou outro grupo. Sem essa variação, mantenha o vídeo atual ou cole outro link.');
      matches.sort((a,b)=>a.group.localeCompare(b.group,'pt-BR')||a.name.localeCompare(b.name,'pt-BR'));
      let category='';
      matches.forEach(video => {
        if(video.group!==category){category=video.group;list.append(el('h4',{class:'video-category-title'},category));}
        const row = el('article', {class: 'gym-result','data-video-id':video.id}), title = el('strong', {}, video.name), meta = el('small', {}, video.group + ' · ' + video.gender);
        const actions = el('div', {class: 'gym-actions'}), watch = el('button', {type: 'button'}, 'Ver movimento');
        const original = el('a', {href: video.driveUrl||video.url, target: '_blank', rel: 'noopener noreferrer'}, 'Abrir no Drive');
        watch.onclick = () => {
          clearPreview();
          const player=WorkoutVideoPreview.createPlayer(video);
          preview.replaceChildren(el('strong', {}, video.name + ' · ' + video.gender), player.element);
          preview.hidden=false;preview.scrollIntoView({block:'nearest'});player.play();
        };
        if(video.url.startsWith('local-video:'))original.hidden=true;actions.append(watch,WorkoutVideoLibrary.favoriteButton(video));
        if(!video.removed){const rename=el('button',{type:'button',class:'gym-rename','aria-label':'Renomear vídeo: '+video.name,title:'Renomear'},'✎');rename.onclick=()=>{
          row.querySelector('form')?.remove();const form=el('form',{class:'video-rename-form'}),input=el('input',{type:'text',value:selection?.name||video.name,maxlength:'160','aria-label':'Novo nome do vídeo'}),save=el('button',{type:'submit'},'Salvar nome'),cancel=el('button',{type:'button'},'Cancelar');form.append(input,save,cancel);row.append(form);input.focus();input.select();cancel.onclick=()=>{form.remove();rename.focus();};form.onsubmit=event=>{event.preventDefault();try{WorkoutVideoLibrary.rename(video.id,input.value);notice='Nome atualizado na sua biblioteca.';render();}catch(error){let message=form.querySelector('[role=status]');if(!message){message=el('small',{role:'status'});form.append(message);}message.textContent=error.message;}};
        };actions.append(rename);}actions.append(original);
        const remove=el('button',{type:'button',class:video.removed?'gym-restore':'gym-remove'},video.removed?'Restaurar':'Apagar');remove.onclick=()=>{try{if(video.removed){notice='Vídeo restaurado.';WorkoutVideoLibrary.restore(video.id);}else{lastRemoved=video.id;notice='Vídeo apagado da sua lista.';WorkoutVideoLibrary.remove(video.id);}}catch(error){lastRemoved=null;notice=error.message;render();}};actions.append(remove);
        if(video.removed){const purge=el('button',{type:'button',class:'gym-remove gym-purge'},'Apagar definitivamente');purge.onclick=async()=>{purge.disabled=true;try{if(await WorkoutVideoLibrary.purge(video)){if(lastRemoved===video.id)lastRemoved=null;notice='Vídeo apagado definitivamente desta biblioteca.';render();}}catch(error){notice=error.message;render();}finally{purge.disabled=false;}};actions.append(purge);}
        if (selection&&!video.removed) {
          const use = el('button', {type: 'button', class: 'gym-use'}, 'Usar este vídeo');
          use.onclick = () => { const apply = selection.apply; apply(video); dialog.close(); };
          actions.append(use);
        }
        row.append(title, meta, actions); list.append(row);
      });browser.scrollTop=scroll;rememberSearch();
    }
    removed.onclick=()=>{showDeleted=!showDeleted;notice='';browser.scrollTop=0;render();};undo.onclick=()=>{if(!lastRemoved)return;const id=lastRemoved;lastRemoved=null;notice='Exclusão desfeita.';try{WorkoutVideoLibrary.restore(id);}catch(error){lastRemoved=id;notice=error.message;render();}};
    clearSearch.onclick=()=>{search.value='';filter();search.focus();};
    function filter(){notice='';browser.scrollTop=0;render();}search.oninput = filter; group.onchange = filter; gender.onchange = filter;
    return {help, search, group, gender, status, browser, render};
  }
  let controls;
  async function open(options) {
    if (!controls) controls = create();
    previousFocus = document.activeElement; selection = options || null;showDeleted=false;notice='';
    controls.help.textContent = options ? 'Escolha o vídeo de “' + options.name + '”. A escolha fica salva neste exercício. ' + (options.context === 'gif' ? 'O movimento aparecerá na ficha em GIF.' : 'O PDF abre o vídeo por link.') : 'Vídeos organizados por categoria, com uma demonstração por exercício e variação. Use Adicionar vídeo para incluir um arquivo deste aparelho.';
    let saved={};if(!options)try{saved=JSON.parse(localStorage.getItem('treinoGeneralVideoSearchV1')||'{}')||{};}catch(e){}
    controls.search.value=options?options.name:typeof saved.query==='string'?saved.query:'';controls.group.value='';controls.gender.value='';
    controls.status.textContent = 'Carregando catálogo…';
    dialog.querySelector('.gym-results').replaceChildren();
    if (!dialog.open) dialog.showModal();
    try {
      const data = await load();
      {
        controls.group.replaceChildren(el('option',{value:''},'Todas as categorias'));controls.gender.replaceChildren(el('option',{value:''},'Todas as versões'));
        [...new Set(data.videos.map(video => video.group))].sort((a,b)=>a.localeCompare(b,'pt-BR')).forEach(value => controls.group.append(el('option', {value}, value)));
        [...new Set(data.videos.map(video => video.gender))].sort().forEach(value => controls.gender.append(el('option', {value}, value)));
      }
      if(dialog.open){controls.group.value=saved.group||'';controls.gender.value=saved.gender||'';controls.render();controls.browser.scrollTop=Math.max(0,Number(saved.scroll)||0);}
    } catch (error) {
      controls.status.textContent = 'Não foi possível carregar a biblioteca. Feche e tente novamente; seus vídeos atuais foram mantidos.';
    }
  }
  function addChoice({item, input, title}) {
    const button = el('button', {type: 'button', class: 'gym-choice'}, 'GymFaster');
    const chosen = el('small', {class: 'gym-selected'});
    function describe() {
      const video = catalog?.videos.find(video => video.url === input.value);
      chosen.textContent = video ? 'GymFaster: ' + video.name + ' · ' + video.gender : '';
    }
    input.addEventListener('input', describe);
    load().then(describe).catch(() => {});
    button.onclick = () => open({name: title.textContent.trim(), apply(video) {
      if (!input.isConnected) return;
      input.value = video.url; input.dispatchEvent(new Event('input', {bubbles: true}));
    }});
    item.append(button, chosen);
  }
  function prepareA() {
    const tools = document.getElementById('pdfReviewTools');
    if (!tools.querySelector('[aria-label="Incluir seção A no PDF"]')) {
      tools.querySelector('[role="status"]').textContent = 'O treino A está vazio. Adicione os exercícios antes de preparar o envio.';
      tools.scrollIntoView({block: 'start'}); return;
    }
    tools.querySelectorAll('.pdf-section-checks input').forEach(input => { input.checked = input.getAttribute('aria-label') === 'Incluir seção A no PDF'; input.dispatchEvent(new Event('change')); });
    const include = tools.querySelector('[aria-label="Incluir vídeos no PDF"]');
    if (include) { include.checked = true; include.dispatchEvent(new Event('change')); }
    const panel = tools.querySelector('.pdf-video-section');
    if (panel && !panel.hidden) { panel.open = true; panel.parentElement.parentElement.open = true; }
    const status = tools.querySelector('[role="status"]');
    status.textContent = 'Treino A selecionado. Toque em GIFs em cada exercício para conferir e associar a demonstração. Depois use Enviar PDF. Os vídeos abrem pelos links do PDF.';
    tools.scrollIntoView({block: 'start'});
  }
  document.addEventListener('DOMContentLoaded', () => {
    const menu = document.querySelector('#moreOptions .more-options-menu');
    if (!menu) return;
    const library = el('button', {type: 'button', id: 'gymfasterCollectionBtn'}, '🎞 GymFaster');
    function updateCount(){load().then(data => { const all=WorkoutVideoLibrary.apply(data.videos,true),available=all.filter(video=>!video.removed),examples=available.filter(video=>video.kind==='created-example').length; library.textContent=available.length<all.length?'🎞 Biblioteca de vídeos · '+available.length+'/'+all.length+' disponíveis':'🎞 Biblioteca de vídeos · '+(available.length-examples)+' vídeos'+(examples?' + '+examples+' exemplo'+(examples>1?'s':''):''); }).catch(()=>{});}
    updateCount();window.addEventListener('workout-video-library-change',()=>{updateCount();if(dialog?.open)controls.render();});
    library.onclick = () => { document.getElementById('moreOptions').open = false; open(); };
    const gifs = el('button', {type: 'button', id: 'workoutGifsBtn'}, '🎞 GIFs');
    gifs.onclick = () => { document.getElementById('moreOptions').open = false; GymFasterWorkout.open(); };
    menu.append(library);
    const pdf = document.getElementById('pdfBtn');
    const actions = el('div', {id: 'workoutExportActions', role: 'group', 'aria-label': 'PDF, GIFs e outras opções'});
    pdf.before(actions);
    actions.append(pdf, gifs, document.getElementById('screenshotBtn'), document.getElementById('moreOptions'));
  });
  return {open, addChoice, prepareA};
})();
