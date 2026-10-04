/* Compression and serialization must not block the keyboard on the page. */
importScripts('storage-compression.js?v=15', 'assessment-journal.js?v=17');
const prefix = 'treino36:lz:1:';
self.onmessage = ({data}) => {
  try {
    let records = data.value;
    if (data.task === 'compact') {
      const decoded = data.raw?.startsWith(prefix) ? LZString.decompressFromUTF16(data.raw.slice(prefix.length)) : data.raw;
      if (data.raw && decoded === null) throw Error('Não foi possível ler as avaliações guardadas.');
      records = TreinoAssessmentJournal.merge(JSON.parse(decoded || '[]'), JSON.parse(data.journal?.startsWith(prefix) ? LZString.decompressFromUTF16(data.journal.slice(prefix.length)) : (data.journal || '[]')));
    }
    const decoded = JSON.stringify(records);
    const compressed = decoded.length >= 512 ? prefix + LZString.compressToUTF16(decoded) : decoded;
    self.postMessage({id:data.id, decoded, packed:compressed.length < decoded.length ? compressed : decoded, records:data.task === 'compact' ? records : undefined});
  } catch (error) { self.postMessage({id:data.id, error:error.message}); }
};
