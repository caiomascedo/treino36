window.GymFasterWorkout = (() => {
  'use strict';
  let integration, dialog, controls, catalog, workout, selected, cards = [], worker, busy = false, cancelled = false, generation = 0, layoutHeader = 175, file, blobURL;
  const DURATION = 5, FPS = 20, WIDTH = 800, CARD = 270, HEADER = 175;
  const node = (tag, attrs = {}, text) => {
    const item = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) item.setAttribute(key, value);
    if (text !== undefined) item.textContent = text;
    return item;
  };
  const normalized = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  function configure(options) { integration = options; }
  function clearResult() {
    file = null;
    if (blobURL) URL.revokeObjectURL(blobURL);
    blobURL = null;
    controls.result.replaceChildren(); controls.result.hidden = true;
    controls.share.hidden = true; controls.download.hidden = true;
  }
  function create() {
    dialog = node('dialog', {id: 'workoutGifDialog', 'aria-labelledby': 'workoutGifTitle'});
    const heading = node('h3', {id: 'workoutGifTitle'}, 'Treino em GIF · GymFaster');
    const help = node('p', {}, 'Confira os vídeos na ficha e gere um único GIF animado para enviar. Duração: 5 segundos em repetição.');
    const section = node('select', {'aria-label': 'Treino para o GIF'});
    const student = node('strong', {class: 'gif-student'});
    const status = node('p', {role: 'status', 'aria-live': 'polite'});
    const list = node('div', {class: 'gif-cards'}), result = node('div', {class: 'gif-result', hidden: ''});
    const actions = node('div', {class: 'gif-actions'});
    const generate = node('button', {type: 'button', class: 'gif-primary'}, 'Gerar GIF animado');
    const share = node('button', {type: 'button', hidden: ''}, 'Compartilhar GIF');
    const download = node('button', {type: 'button', hidden: ''}, 'Baixar GIF');
    const cancel = node('button', {type: 'button', hidden: ''}, 'Cancelar geração');
    const close = node('button', {type: 'button'}, 'Fechar');
    actions.append(generate, share, download, cancel, close);
    dialog.append(heading, help, student, section, status, list, result, actions);
    document.body.append(dialog);
    controls = {section, student, status, list, result, generate, share, download, cancel};
    section.onchange = () => { selected = workout.sections.find(s => s.id === section.value); render(); };
    generate.onclick = generateGIF;
    cancel.onclick = () => { cancelled = true; stopWorker(); };
    close.onclick = () => dialog.close();
    dialog.addEventListener('close', () => {
      cancelled = true; generation++; stopWorker(); setBusy(false);
      cards.forEach(card => { card.video.pause(); card.video.removeAttribute('src'); card.video.load(); if (card.localURL) URL.revokeObjectURL(card.localURL); });
      cards = []; clearResult();
      document.getElementById('gymfasterWorkoutABtn')?.focus();
    });
    download.onclick = () => {
      if (!file || !blobURL) return;
      const link = node('a', {href: blobURL, download: file.name}); document.body.append(link); link.click(); link.remove();
    };
    share.onclick = async () => {
      if (!file) return;
      try {
        if (navigator.canShare?.({files: [file]})) await navigator.share({files: [file], title: 'Treino ' + selected.id});
        else { controls.status.textContent = 'Baixe o GIF e anexe a imagem na conversa do aluno.'; download.click(); }
      } catch (error) { if (error.name !== 'AbortError') controls.status.textContent = 'Não foi possível compartilhar. Use Baixar GIF e anexe a imagem na conversa.'; }
    };
  }
  function exactVideo(row) {
    if (row.video) {
      try { const url = new URL(row.video); const id = url.hostname === 'drive.google.com' && (url.pathname.match(/\/file\/d\/([^/]+)/)?.[1] || url.searchParams.get('id')); return catalog.videos.find(video => video.id === id) || null; }
      catch (error) { return null; }
    }
    const name = normalized(row.nome);
    return catalog.videos.find(video => video.gender === 'Feminino' && normalized(video.name) === name) || null;
  }
  function setVideo(card, video) {
    if (card.localURL && card.localURL !== video?.localURL) URL.revokeObjectURL(card.localURL);
    card.localURL = video?.localURL || null; card.asset = video;
    card.video.pause(); card.video.removeAttribute('src');
    card.caption.textContent = video ? video.name + ' · ' + (video.localURL ? 'Arquivo local · reenvie ao reabrir a ficha' : video.gender) : 'Escolha a demonstração para este exercício.';
    card.video.hidden = !video;
    if (video) { card.video.src = video.localURL || 'gymfaster-media/' + video.id + '.mp4'; card.video.load(); card.video.play().catch(() => {}); }
    clearResult();
  }
  function render() {
    clearResult();
    cards.forEach(card => { card.video.pause(); card.video.removeAttribute('src'); card.video.load(); if (card.localURL) URL.revokeObjectURL(card.localURL); });
    cards = []; controls.list.replaceChildren();
    controls.student.textContent = workout.student + ' · ' + (selected?.title || 'Treino');
    if (!selected?.rows.length) { controls.status.textContent = 'Este treino está vazio. Adicione os exercícios na ficha.'; controls.generate.disabled = true; return; }
    controls.generate.disabled = false;
    controls.status.textContent = 'Confira a variação de cada exercício. As sugestões com nome idêntico aparecem na ficha; escolha os vídeos que faltam.';
    selected.rows.forEach((row, index) => {
      const article = node('article', {class: 'gif-card'}), text = node('div', {class: 'gif-card-text'});
      const name = node('strong', {}, (index + 1) + '. ' + row.nome), details = node('p', {}, row.detalhes), caption = node('small');
      const choose = node('button', {type: 'button'}, 'Escolher vídeo GymFaster');
      const video = node('video', {muted: '', playsinline: '', loop: '', preload: 'metadata', 'aria-label': 'Demonstração de ' + row.nome});
      video.muted = true;
      const upload = node('button', {type: 'button'}, 'Vídeo do aparelho'), input = node('input', {type: 'file', accept: 'video/*', hidden: '', 'aria-label': 'Arquivo de vídeo de ' + row.nome});
      const card = {row, video, caption, choose, upload, asset: null, localURL: null};
      upload.onclick = () => input.click();
      input.onchange = () => {
        const file = input.files?.[0]; if (!file || busy) return;
        if (!file.type.startsWith('video/') || file.size > 100 * 1048576) { controls.status.textContent = 'Escolha um arquivo de vídeo de até 100 MB.'; input.value = ''; return; }
        setVideo(card, {name: file.name, localURL: URL.createObjectURL(file)});
        controls.status.textContent = 'Vídeo do aparelho adicionado só para este GIF. O link salvo no treino foi mantido. Reenvie o arquivo ao reabrir a ficha.';
      };
      video.onerror = () => { if (card.asset) { caption.textContent = 'Não foi possível carregar ' + card.asset.name + '. Verifique a internet e tente escolher o vídeo novamente.'; } };
      choose.onclick = () => GymFasterLibrary.open({name: row.nome, context: 'gif', apply(asset) {
        if (!dialog.open || busy) return;
        integration.save(row.source, asset.url, workout.student);
        row.video = asset.url; setVideo(card, asset);
      }});
      text.append(name, details, caption, choose, upload, input); article.append(text, video); controls.list.append(article); cards.push(card);
      setVideo(card, exactVideo(row));
    });
  }
  async function open() {
    if (!integration) return;
    if (!dialog) create();
    workout = integration.read();
    controls.section.replaceChildren();
    workout.sections.forEach(section => controls.section.append(node('option', {value: section.id}, section.title)));
    selected = workout.sections.find(section => section.id === 'A') || workout.sections[0];
    controls.section.value = selected?.id || '';
    if (!dialog.open) dialog.showModal();
    controls.status.textContent = 'Carregando os vídeos para o GIF…';
    try {
      if (!catalog) { const response = await fetch('gymfaster-catalog.json?v=1'); if (!response.ok) throw Error('Catálogo indisponível'); catalog = await response.json(); }
      if (dialog.open) render();
    } catch (error) { controls.status.textContent = 'Não foi possível carregar o catálogo. Feche e tente novamente.'; }
  }
  function stopWorker() { if (worker) { worker.terminate(); worker = null; } }
  function setBusy(value) {
    busy = value; controls.generate.disabled = value; controls.section.disabled = value;
    controls.cancel.hidden = !value; cards.forEach(card => { card.choose.disabled = value; card.upload.disabled = value; });
  }
  function waitForVideo(video) {
    if (video.error) return Promise.reject(Error('Não foi possível carregar uma demonstração. Escolha o vídeo novamente.'));
    if (video.readyState >= 2 && Number.isFinite(video.duration)) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => finish(Error('O vídeo não carregou. Confira a internet e tente novamente.')), 20000);
      const cancellation = setInterval(() => { if (cancelled) finish(Error('Geração cancelada.')); }, 100);
      const loaded = () => finish(); const failed = () => finish(Error('Não foi possível carregar uma demonstração. Escolha o vídeo novamente.'));
      function finish(error) { clearTimeout(timer); clearInterval(cancellation); video.removeEventListener('loadeddata', loaded); video.removeEventListener('error', failed); error ? reject(error) : resolve(); }
      video.addEventListener('loadeddata', loaded, {once: true}); video.addEventListener('error', failed, {once: true});
    });
  }
  function seek(video, time) {
    if (Math.abs(video.currentTime - time) < 0.001 && video.readyState >= 2) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => finish(Error('A leitura de um vídeo demorou demais. Tente novamente.')), 10000);
      const done = () => finish(Math.abs(video.currentTime - time) > 0.08 ? Error('Não foi possível ler o movimento deste vídeo. Confira a internet e tente novamente.') : null);
      function finish(error) { clearTimeout(timer); video.removeEventListener('seeked', done); error ? reject(error) : resolve(); }
      video.addEventListener('seeked', done, {once: true}); video.currentTime = time;
    });
  }
  function send(data, transfers = []) {
    const target = worker;
    return new Promise((resolve, reject) => {
      const timer = setInterval(() => { if (cancelled || worker !== target) finish(Error('Geração cancelada.')); }, 100);
      const response = event => event.data.type === 'error' ? finish(Error(event.data.message)) : finish(null, event.data);
      const fail = () => finish(Error('Não foi possível gerar o GIF neste navegador.'));
      function finish(error, value) { clearInterval(timer); target.removeEventListener('message', response); target.removeEventListener('error', fail); error ? reject(error) : resolve(value); }
      target.addEventListener('message', response); target.addEventListener('error', fail); target.postMessage(data, transfers);
    });
  }
  function wrap(ctx, text, x, y, width, lineHeight) {
    let line = '';
    for (const word of text.split(/\s+/)) {
      const next = line ? line + ' ' + word : word;
      if (ctx.measureText(next).width > width && line) { ctx.fillText(line, x, y); y += lineHeight; line = word; } else line = next;
    }
    if (line) ctx.fillText(line, x, y);
    return y + lineHeight;
  }
  function lineCount(ctx, text, width) {
    let lines = 1, line = '';
    for (const word of text.split(/\s+/)) { const next = line ? line + ' ' + word : word; if (ctx.measureText(next).width > width && line) { lines++; line = word; } else line = next; }
    return lines;
  }
  function layout(ctx) {
    ctx.font = 'bold 29px Arial'; layoutHeader = Math.max(HEADER, 88 + lineCount(ctx, selected.title, 744) * 32 + 55);
    let top = layoutHeader;
    cards.forEach((card, index) => {
      ctx.font = 'bold 23px Arial'; const names = lineCount(ctx, (index + 1) + '. ' + card.row.nome, 358);
      ctx.font = '20px Arial'; const details = lineCount(ctx, card.row.detalhes, 358);
      card.top = top; card.height = Math.max(CARD, Math.max(38 + names * 28 + 13, 120) + details * 26 + 25); top += card.height;
    });
    return top + 50;
  }
  function paint(ctx, canvas) {
    ctx.fillStyle = '#eff5f1'; ctx.fillRect(0, 0, WIDTH, canvas.height);
    ctx.fillStyle = '#176b43'; ctx.fillRect(0, 0, WIDTH, 7); ctx.font = 'bold 23px Arial'; ctx.fillText('CAIO MACÊDO · PERSONAL TRAINER', 28, 43);
    ctx.fillStyle = '#1b3428'; ctx.font = 'bold 29px Arial'; wrap(ctx, selected.title, 28, 88, 744, 32);
    ctx.font = '19px Arial'; ctx.fillText(workout.student.slice(0, 65), 28, layoutHeader - 29);
    cards.forEach((card, index) => {
      const top = card.top;
      ctx.fillStyle = '#fff'; ctx.fillRect(20, top, 760, card.height - 12);
      ctx.fillStyle = '#1b3428'; ctx.font = 'bold 23px Arial';
      const next = wrap(ctx, (index + 1) + '. ' + card.row.nome, 36, top + 38, 358, 28);
      ctx.fillStyle = '#176b43'; ctx.font = '20px Arial'; wrap(ctx, card.row.detalhes, 36, Math.max(next + 13, top + 120), 358, 26);
      const video = card.video, scale = Math.min(350 / video.videoWidth, 242 / video.videoHeight);
      const width = video.videoWidth * scale, height = video.videoHeight * scale;
      ctx.drawImage(video, 410 + (350 - width) / 2, top + 5 + (242 - height) / 2, width, height);
    });
    ctx.fillStyle = '#176b43'; ctx.font = '17px Arial'; ctx.fillText((cards.some(card => card.localURL) ? 'Demonstrações escolhidas · Treino ' : 'Demonstrações GymFaster · Treino ') + selected.id, 28, canvas.height - 20);
  }
  async function generateGIF() {
    if (busy || !cards.length) return;
    if (cards.some(card => !card.asset)) { controls.status.textContent = 'Escolha um vídeo para cada exercício antes de gerar o GIF. Nenhuma variação será substituída automaticamente.'; return; }
    if (cards.length > 20) { controls.status.textContent = 'Use até 20 exercícios por GIF. Divida esta seção para gerar as fichas.'; return; }
    clearResult(); setBusy(true); cancelled = false; const token = ++generation;
    try {
      controls.status.textContent = 'Carregando as demonstrações…';
      cards.forEach(card => card.video.pause());
      await Promise.all(cards.map(card => waitForVideo(card.video)));
      if (cancelled || token !== generation) throw Error('Geração cancelada.');
      const canvas = document.createElement('canvas'); canvas.width = WIDTH; canvas.height = HEADER + cards.length * CARD + 50;
      const ctx = canvas.getContext('2d', {willReadFrequently: true}); const height = layout(ctx); if (height > 12000) throw Error('Esta ficha ficou muito longa. Divida o treino ou reduza o texto para gerar o GIF.'); canvas.height = height; worker = new Worker('workout-gif-worker.js?v=1');
      for (let frame = 0; frame < DURATION * FPS; frame++) {
        if (cancelled || token !== generation) throw Error('Geração cancelada.');
        await Promise.all(cards.map(card => seek(card.video, Math.max(0.001, frame / (DURATION * FPS) * card.video.duration))));
        if (cancelled || token !== generation) throw Error('Geração cancelada.');
        paint(ctx, canvas);
        const pixels = ctx.getImageData(0, 0, WIDTH, canvas.height).data.buffer;
        await send({type: 'frame', width: WIDTH, height: canvas.height, pixels}, [pixels]);
        controls.status.textContent = 'Gerando GIF: ' + (frame + 1) + '%';
      }
      const result = await send({type: 'finish'});
      if (cancelled || token !== generation || !dialog.open) return;
      file = new File([result.bytes], 'treino_' + selected.id + '_' + workout.student.slice(0, 80).replace(/[^a-z0-9áéíóúâêôãõç_-]+/gi, '_') + '.gif', {type: 'image/gif'});
      blobURL = URL.createObjectURL(file);
      controls.result.replaceChildren(node('img', {src: blobURL, alt: 'Treino ' + selected.id + ' com exercícios em movimento'})); controls.result.hidden = false;
      controls.share.hidden = false; controls.download.hidden = false;
      controls.status.textContent = 'GIF pronto · 5 segundos · ' + (file.size / 1048576).toFixed(1) + ' MB. Confira abaixo e compartilhe a imagem.';
      controls.result.scrollIntoView({block: 'start'});
    } catch (error) { if (dialog.open && token === generation) controls.status.textContent = error.message || 'Não foi possível gerar o GIF. Tente novamente.'; }
    finally { if (token === generation) { stopWorker(); setBusy(false); if (dialog.open) cards.forEach(card => card.video.play().catch(() => {})); } }
  }
  return {configure, open};
})();
