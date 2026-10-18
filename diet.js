/* A small paste-to-PDF editor using the pupil already selected in the workout. */
window.DietEditor = (() => {
  const plain = text => text.replace(/\*\*|__|`/g, '').replace(/\p{Extended_Pictographic}|[\uFE0F\u200D]/gu, '').replace(/^\s*#{1,6}\s*/, '').trim();
  const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const meals = /^(?:cafe da manha|cafe|desjejum|lanche da manha|almoco|lanche da tarde|jantar|ceia|pre[- ]?treino|pos[- ]?treino|lanche(?:\s+\d+)?|refeicao\s*\d+|orientacoes(?: gerais)?|observacoes|recomendacoes)(?=$|\s*[:(–—-]|\s+\d)/;
  function parse(text) {
    const sections = [];
    let current;
    for (const raw of text.split(/\r?\n/)) {
      const line = plain(raw).replace(/^\s*(?:[-*•▪]+\s*|\d+\)\s*|\d+\.\s+)/, '').trim();
      if (!line || /^[-_=–—\s]+$/.test(line)) continue;
      const candidate = line.replace(/^\d{1,2}(?::\d{2}|h\d{0,2})\s*[-–—:]?\s*/i, '');
      const match = normalize(candidate).match(meals);
      if (match) {
        // An inline meal ("Almoço: arroz...") retains the food after the colon.
        const tail = candidate.slice(match[0].length);
        const inline = tail.match(/^\s*:\s*(.+)$/);
        const colon = inline && !/^\d{1,2}(?::\d{2}|h\d{0,2})(?:\s*(?:h|horas?))?$/i.test(inline[1]) ? inline : null;
        const prefix = line.slice(0, line.length - candidate.length);
        current = {title: colon ? prefix + candidate.slice(0, match[0].length) : line, items: []};
        sections.push(current);
        if (colon) current.items.push(colon[1]);
      } else {
        if (!current) { current = {title: 'Plano alimentar', items: []}; sections.push(current); }
        current.items.push(line);
      }
    }
    return sections;
  }
  let pdfLibrary;
  function mount(config) {
    const dialog = config.createDialog('dietDialog', '🥗 Dieta',
      '<p id="dietStudentName"></p><label for="dietText">🧠 Cola inteligente</label>' +
      '<textarea id="dietText" placeholder="Cole a dieta completa aqui. As refeições serão organizadas automaticamente.\n\nCafé da manhã\n2 ovos\n1 fruta\n\nAlmoço\nArroz, feijão e frango"></textarea>' +
      '<details id="dietPreview"><summary>Prévia organizada</summary><div id="dietPreviewBody"></div></details>' +
      '<p id="dietStatus" role="status"></p><div class="dialog-actions"><button type="button" id="dietPdfBtn" class="primary">📄 PDF</button><button type="button" data-close>Fechar</button></div>');
    const text = dialog.querySelector('#dietText'), status = dialog.querySelector('#dietStatus');
    const preview = dialog.querySelector('#dietPreview'), body = dialog.querySelector('#dietPreviewBody');
    const pdfButton = dialog.querySelector('#dietPdfBtn');
    let draftKey, name = '', previewTimer, inMemory = new Map();
    function save() {
      inMemory.set(draftKey, text.value);
      try { localStorage.setItem(draftKey, text.value); status.textContent = 'Rascunho salvo.'; }
      catch (error) { status.textContent = 'Não foi possível guardar o rascunho neste navegador. O texto continua disponível para gerar o PDF.'; }
    }
    function render() {
      clearTimeout(previewTimer);
      body.replaceChildren();
      for (const section of parse(text.value)) {
        const heading = document.createElement('h4'); heading.textContent = section.title;
        const list = document.createElement('ul');
        for (const item of section.items) { const li = document.createElement('li'); li.textContent = item; list.append(li); }
        body.append(heading, list);
      }
    }
    text.oninput = () => {
      save(); pdfButton.disabled = !text.value.trim();
      clearTimeout(previewTimer);
      if (preview.open) previewTimer = setTimeout(render, 120);
    };
    preview.ontoggle = () => { if (preview.open) render(); };
    dialog.addEventListener('close', () => clearTimeout(previewTimer));
    async function getPDF() {
      if (window.jspdf?.jsPDF) return window.jspdf.jsPDF;
      if (!pdfLibrary) pdfLibrary = (async () => {
        for (const src of ['https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js', 'https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js']) {
          try { await config.loadScript(src); if (window.jspdf?.jsPDF) return window.jspdf.jsPDF; } catch (error) {}
        }
        throw Error('Não foi possível carregar o PDF. Confira sua conexão e tente novamente.');
      })().catch(error => { pdfLibrary = null; throw error; });
      return pdfLibrary;
    }
    pdfButton.onclick = async () => {
      const sections = parse(text.value);
      if (!sections.length) { status.textContent = 'Cole a dieta antes de gerar o PDF.'; return; }
      const pdfName = name, footer = config.footer();
      const viewer = TreinoPDFViewer.reserve();
      pdfButton.disabled = true;
      status.textContent = 'Gerando PDF…';
      try {
        const jsPDF = await getPDF(), doc = new jsPDF({unit: 'mm', format: 'a4', compress: true});
        let y = 20;
        const lines = (value, size, bold, color) => {
          doc.setFont('helvetica', bold ? 'bold' : 'normal'); doc.setFontSize(size); doc.setTextColor(...color);
          for (const line of doc.splitTextToSize(value, 178)) {
            if (y > 278) { doc.addPage(); y = 20; }
            doc.text(line, 16, y); y += size * .43;
          }
        };
        lines(pdfName ? 'Dieta — ' + pdfName : 'Dieta', 16, true, [30,111,63]);
        y += 2; lines(new Date().toLocaleDateString('pt-BR'), 9, false, [100,110,120]); y += 6;
        for (const section of sections) {
          if (y > 260) { doc.addPage(); y = 20; }
          lines(section.title, 12, true, [30,111,63]); y += 2;
          for (const item of section.items) lines('• ' + item, 10.5, false, [36,55,70]);
          y += 5;
        }
        for (let page = 1; page <= doc.getNumberOfPages(); page++) {
          doc.setPage(page); doc.setFont('helvetica', 'normal'); doc.setFontSize(8); doc.setTextColor(115,125,135);
          doc.text(doc.splitTextToSize(footer, 160)[0] || '', 16, 289);
          doc.text(page + '/' + doc.getNumberOfPages(), 194, 289, {align: 'right'});
        }
        const safeName = (pdfName || 'plano_alimentar').replace(/[\\/:*?"<>|]+/g, '_').replace(/\s+/g, '_').slice(0, 80);
        TreinoPDFViewer.deliver(doc, 'Dieta_' + safeName + '.pdf', viewer);
        status.textContent = 'PDF gerado.';
      } catch (error) { TreinoPDFViewer.close(viewer); status.textContent = error.message; }
      finally { pdfButton.disabled = !text.value.trim(); }
    };
    const button = document.createElement('button'); button.type = 'button'; button.id = 'dietBtn'; button.textContent = '🥗 Dieta';
    button.onclick = () => {
      const student = config.student(); name = config.name().trim();
      draftKey = 'dieta36_rascunho_v1:' + encodeURIComponent(student?.student_id || name || 'sem_aluno');
      status.textContent = '';
      try { text.value = localStorage.getItem(draftKey) || inMemory.get(draftKey) || ''; }
      catch (error) { text.value = inMemory.get(draftKey) || ''; status.textContent = 'O armazenamento do navegador está indisponível.'; }
      dialog.querySelector('#dietStudentName').textContent = name;
      pdfButton.disabled = !text.value.trim(); preview.open = false; body.replaceChildren();
      dialog.showModal();
      // Opening is read-only until the user taps the text, as in the OBS editor.
      pdfButton.disabled ? dialog.querySelector('[data-close]').focus({preventScroll:true}) : pdfButton.focus({preventScroll:true});
    };
    return button;
  }
  return {mount, parse};
})();
