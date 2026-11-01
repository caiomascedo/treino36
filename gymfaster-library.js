/* Verified Drive catalog. Selection is explicit: exercise variants are never replaced automatically. */
window.GymFasterLibrary = (() => {
  'use strict';
  let catalog, pending, dialog, selection, previousFocus;
  const el = (tag, attrs = {}, text) => {
    const node = document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  async function load() {
    if (catalog) return catalog;
    if (!pending) pending = fetch('gymfaster-catalog.json?v=2').then(response => {
      if (!response.ok) throw Error('Catálogo indisponível.');
      return response.json();
    }).then(data => {
      if (!Array.isArray(data.videos) || !data.videos.length) throw Error('Catálogo vazio.');
      catalog = data; return data;
    }).finally(() => { pending = null; });
    return pending;
  }
  function create() {
    dialog = el('dialog', {id: 'gymfasterLibrary', 'aria-labelledby': 'gymfasterTitle'});
    const heading = el('h3', {id: 'gymfasterTitle'}, 'Vídeos GymFaster');
    const help = el('p', {class: 'gym-help'});
    const search = el('input', {type: 'search', placeholder: 'Buscar exercício ou equipamento', 'aria-label': 'Buscar no GymFaster'});
    const filters = el('div', {class: 'gym-filters'});
    const group = el('select', {'aria-label': 'Grupo muscular GymFaster'});
    const gender = el('select', {'aria-label': 'Versão GymFaster'});
    group.append(el('option', {value: ''}, 'Todos os grupos'));
    gender.append(el('option', {value: ''}, 'Todas as versões'));
    filters.append(group, gender);
    const status = el('p', {role: 'status'}), list = el('div', {class: 'gym-results'});
    const preview = el('div', {class: 'gym-preview', hidden: ''});
    const close = el('button', {type: 'button', class: 'gym-close'}, 'Fechar');
    function clearPreview() { preview.querySelectorAll('video').forEach(video => { video.pause(); video.removeAttribute('src'); video.load(); }); preview.replaceChildren(); preview.hidden = true; }
    close.onclick = () => dialog.close();
    dialog.append(heading, help, search, filters, status, preview, list, close);
    document.body.append(dialog);
    dialog.addEventListener('close', () => { clearPreview(); selection = null; if (previousFocus?.isConnected) previousFocus.focus(); });
    function render() {
      list.replaceChildren(); clearPreview();
      if (!catalog) return;
      const words = normalize(search.value).split(' ').filter(Boolean);
      const matches = catalog.videos.filter(video => (!group.value || video.group === group.value) && (!gender.value || video.gender === gender.value) && words.every(word => normalize(video.name).includes(word)));
      status.textContent = matches.length + ' de ' + catalog.videos.length + ' vídeos. ' + (matches.length ? 'Confira o aparelho e a variação antes de escolher.' : 'Tente menos palavras ou outro grupo. Sem essa variação, mantenha o vídeo atual ou cole outro link.');
      matches.forEach(video => {
        const row = el('article', {class: 'gym-result'}), title = el('strong', {}, video.name), meta = el('small', {}, video.group + ' · ' + video.gender);
        const actions = el('div', {class: 'gym-actions'}), watch = el('button', {type: 'button'}, 'Ver movimento');
        const original = el('a', {href: video.url, target: '_blank', rel: 'noopener noreferrer'}, 'Abrir no Drive');
        watch.onclick = () => {
          clearPreview();
          const motion = selection?.context === 'gif' ? el('video', {src: 'gymfaster-media/' + video.id + '.mp4', controls: '', loop: '', playsinline: '', muted: '', class: 'gym-motion', 'aria-label': video.name}) : el('iframe', {src: 'https://drive.google.com/file/d/' + video.id + '/preview', title: video.name, allow: 'fullscreen', allowfullscreen: ''});
          preview.replaceChildren(el('strong', {}, video.name + ' · ' + video.gender), motion);
          preview.hidden = false; preview.scrollIntoView({block: 'nearest'});
          if (motion.tagName === 'VIDEO') { motion.muted = true; motion.play().catch(() => {}); }
        };
        actions.append(watch, original);
        if (selection) {
          const use = el('button', {type: 'button', class: 'gym-use'}, 'Usar este vídeo');
          use.onclick = () => { const apply = selection.apply; apply(video); dialog.close(); };
          actions.append(use);
        }
        row.append(title, meta, actions); list.append(row);
      });
    }
    search.oninput = render; group.onchange = render; gender.onchange = render;
    return {help, search, group, gender, status, render};
  }
  let controls;
  async function open(options) {
    if (!controls) controls = create();
    previousFocus = document.activeElement; selection = options || null;
    controls.help.textContent = options ? 'Escolha o vídeo de “' + options.name + '”. A escolha fica salva neste exercício. ' + (options.context === 'gif' ? 'O movimento aparecerá na ficha em GIF.' : 'O PDF abre o vídeo por link.') : 'Explore a coleção. Para montar a ficha animada do aluno, use o botão GIFs ao lado do PDF e escolha CM ou GymFaster.';
    controls.search.value = options ? options.name : ''; controls.group.value = ''; controls.gender.value = '';
    controls.status.textContent = 'Carregando catálogo…';
    dialog.querySelector('.gym-results').replaceChildren();
    if (!dialog.open) dialog.showModal();
    try {
      const data = await load();
      if (controls.group.options.length === 1) {
        [...new Set(data.videos.map(video => video.group))].sort((a,b)=>a.localeCompare(b,'pt-BR')).forEach(value => controls.group.append(el('option', {value}, value)));
        [...new Set(data.videos.map(video => video.gender))].sort().forEach(value => controls.gender.append(el('option', {value}, value)));
      }
      if (dialog.open) controls.render();
    } catch (error) {
      controls.status.textContent = 'Não foi possível carregar o GymFaster. Feche e tente novamente; seus vídeos atuais foram mantidos.';
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
    status.textContent = 'Treino A selecionado. Toque em GymFaster em cada exercício para conferir e salvar o vídeo. Depois use Enviar PDF. Os vídeos abrem pelos links do PDF.';
    tools.scrollIntoView({block: 'start'});
  }
  document.addEventListener('DOMContentLoaded', () => {
    const menu = document.querySelector('#moreOptions .more-options-menu');
    if (!menu) return;
    const library = el('button', {type: 'button', id: 'gymfasterCollectionBtn'}, '🎞 GymFaster');
    load().then(data => { const examples=data.videos.filter(video=>video.kind==='created-example').length; library.textContent='🎞 GymFaster · '+(data.videos.length-examples)+' vídeos'+(examples?' + '+examples+' exemplo'+(examples>1?'s':''):''); }).catch(()=>{});
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
