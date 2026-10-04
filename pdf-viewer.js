/* Open generated PDFs inline so Safari can display and share the document. */
window.TreinoPDFViewer = {
  reserve() {
    // Reserve during the tap, before loading libraries or preparing photos.
    const viewer = window.open('', '_blank');
    if (viewer) {
      viewer.opener = null;
      viewer.document.title = 'Preparando PDF';
      viewer.document.body.textContent = 'Preparando PDF…';
    }
    return viewer;
  },
  close(viewer) { if (viewer && !viewer.closed) viewer.close(); },
  deliver(doc, filename, viewer) {
    if (!viewer || viewer.closed) {
      // Preserve access to the file when the browser blocks a new window.
      doc.save(filename);
      return;
    }
    doc.setProperties({title:filename.replace(/\.pdf$/i, '')});
    const blob = doc.output('blob');
    const url = URL.createObjectURL(blob.type === 'application/pdf' ? blob : new Blob([blob], {type:'application/pdf'}));
    try { viewer.location.replace(url); }
    catch (error) { URL.revokeObjectURL(url); this.close(viewer); throw error; }
    // Keep the URL usable for sharing while the viewer is open.
    const cleanup = setInterval(() => {
      if (viewer.closed) { clearInterval(cleanup); URL.revokeObjectURL(url); }
    }, 30000);
  }
};
