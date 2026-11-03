/* Retire legacy sheet coloring once. Never observe text while editing. */
(()=>{
  function clean(){
    document.querySelectorAll('.compound-colors-control').forEach(button=>button.remove());
    document.querySelectorAll('.section .compound-ink').forEach(span=>span.replaceWith(...span.childNodes));
    document.querySelectorAll('.compound-ink-link').forEach(link=>{link.classList.remove('compound-ink-link');link.style.removeProperty('--compound-ink');});
    document.querySelectorAll('[data-compound-ink]').forEach(row=>row.removeAttribute('data-compound-ink'));
    try{localStorage.removeItem('treinoCompoundColorsV1');}catch(e){}
  }
  document.addEventListener('DOMContentLoaded',()=>{clean();Promise.resolve(window.TreinoStorage?.ready).then(()=>requestAnimationFrame(clean));},{once:true});
})();
