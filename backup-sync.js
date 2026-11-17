/* Only the private Raspberry origin sends snapshots; GitHub Pages stays local. */
(() => {
  if (location.origin !== 'https://caio.tail953b6e.ts.net:8443') return;
  const panel = document.createElement('div');
  panel.style.cssText = 'padding:10px;font:12px/1.4 Arial;color:#243a4d;background:#edf2f5;border-radius:8px';
  const status = document.createElement('p'), button = document.createElement('button');
  button.type = 'button'; button.textContent = '☁️ Enviar dados para backup';
  panel.append(status, button);
  document.querySelector('#moreOptions .more-options-menu')?.append(panel);
  const key = 'treino36BackupClient';
  let client = localStorage.getItem(key), busy = false, previous = '';
  if (!client) { client = crypto.randomUUID(); localStorage.setItem(key, client); }
  const date = value => value ? new Date(value * 1000).toLocaleString('pt-BR') : 'aguardando';
  async function sync(force = false) {
    if (busy || !window.TreinoBackup?.snapshot || (!force && document.hidden)) return;
    busy = true;
    try {
      const data = await window.TreinoBackup.snapshot();
      if (!data.alunos.length) { status.textContent = 'Carregue seu JSON para iniciar o backup automático.'; return; }
      const body = JSON.stringify(data);
      if (force || body !== previous) {
        const response = await fetch('/api/backup/snapshot', {method:'POST', headers:{'Content-Type':'application/json','X-Treino36-Client':client}, body});
        const result = await response.json();
        if (!response.ok) throw Error(result.error || 'Não foi possível enviar o backup.');
        previous = body;
      }
      const response = await fetch('/api/backup/status', {cache:'no-store'});
      if (!response.ok) throw Error('Não foi possível consultar o backup.');
      const state = await response.json();
      status.textContent = 'Cópia no Raspberry: ' + date(state.received_at) + '. Drive: ' + date(state.uploaded_at) + '. Backup a cada 15 dias.' + (state.error ? ' ' + state.error : '');
    } catch (error) { status.textContent = 'Backup pendente: ' + error.message; }
    finally { busy = false; }
  }
  button.onclick = () => sync(true);
  status.textContent = 'Backup automático: preparando cópia dos dados deste navegador…';
  setTimeout(() => sync(), 8000);
  setInterval(() => sync(), 30000);
  window.addEventListener('online', () => sync());
  document.addEventListener('visibilitychange', () => { if (!document.hidden) sync(); });
})();
