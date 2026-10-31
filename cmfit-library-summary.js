(function () {
  'use strict';
  function mount(options) {
    var data = options.catalog || {}, groups = Array.isArray(data.groups) ? data.groups : [];
    var total = groups.reduce(function (sum, group) { return sum + (Number.isInteger(group.count) && group.count > 0 ? group.count : 0); }, 0);
    var label = 'CMFit · ' + total.toLocaleString('pt-BR') + ' exercícios';
    var dialog = options.createDialog('cmfitCollectionDialog', 'Animações CMFit',
      '<p class="cmfit-total" role="status"></p><p class="cmfit-collection-description">Abra os vídeos no Drive por grupo muscular.</p><div class="cmfit-collection-groups"></div><div class="dialog-actions"><a class="cmfit-collection-open" target="_blank" rel="noopener noreferrer">Abrir coleção no Drive</a><button data-close>Fechar</button></div>');
    dialog.querySelector('.cmfit-total').textContent = label;
    function driveURL(value) {
      try { var url = new URL(value); return url.protocol === 'https:' && url.hostname === 'drive.google.com' && url.pathname.startsWith('/drive/folders/') ? url.href : null; } catch (error) { return null; }
    }
    var root = driveURL(data.folderUrl), allLink = dialog.querySelector('.cmfit-collection-open');
    if (root) allLink.href = root; else allLink.hidden = true;
    var host = dialog.querySelector('.cmfit-collection-groups');
    groups.forEach(function (group) {
      var url = driveURL(group.folderUrl); if (!url || !Number.isInteger(group.count) || group.count < 1) return;
      var link = document.createElement('a'); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer';
      var name = document.createElement('span'), count = document.createElement('span'); name.textContent = group.name; count.textContent = String(group.count); count.className = 'cmfit-group-count'; link.append(name, count); host.append(link);
    });
    var menuButton = document.createElement('button'); menuButton.type = 'button'; menuButton.id = 'cmfitCollectionBtn'; menuButton.textContent = '🎞 ' + label;
    function open() { if (options.moreOptions) options.moreOptions.open = false; if (!dialog.open) dialog.showModal(); }
    menuButton.onclick = open; options.menu.append(menuButton);
    var compact = document.createElement('button'); compact.type = 'button'; compact.id = 'generatorCmfitCount'; compact.className = 'cmfit-count-compact'; compact.textContent = '🎞 ' + label; compact.onclick = open;
    options.generator.querySelector('h3').after(compact);
    return { total: total, open: open };
  }
  window.CMFitLibrarySummary = { mount: mount };
}());
