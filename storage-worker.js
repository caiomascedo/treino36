/* Compression and serialization must not block the keyboard on the page. */
importScripts('storage-compression.js?v=15', 'assessment-journal.js?v=18','obs-autosave-journal.js?v=1');
const prefix = 'treino36:lz:1:';
self.onmessage = ({data}) => {
  try {
    let records = data.value;
    if (data.task === 'compact') {
      const decoded = data.raw?.startsWith(prefix) ? LZString.decompressFromUTF16(data.raw.slice(prefix.length)) : data.raw;
      if (data.raw && decoded === null) throw Error('Não foi possível ler as avaliações guardadas.');
      records = TreinoAssessmentJournal.merge(JSON.parse(decoded || '[]'), JSON.parse(data.journal?.startsWith(prefix) ? LZString.decompressFromUTF16(data.journal.slice(prefix.length)) : (data.journal || '[]')));
    }
    if(data.task==='compactObs'){const raw=data.raw?.startsWith(prefix)?LZString.decompressFromUTF16(data.raw.slice(prefix.length)):data.raw;if(data.raw&&raw===null)throw Error('Não foi possível ler o treino guardado.');records=TreinoObsJournal.merge(JSON.parse(raw||'[]'),JSON.parse(data.journal?.startsWith(prefix)?LZString.decompressFromUTF16(data.journal.slice(prefix.length)):(data.journal||'[]')),JSON.parse(data.photos?.startsWith(prefix)?LZString.decompressFromUTF16(data.photos.slice(prefix.length)):(data.photos||'[]')));}
    const decoded = JSON.stringify(records);
    const compressed = decoded.length >= 512 ? prefix + LZString.compressToUTF16(decoded) : decoded;
    self.postMessage({id:data.id, decoded, packed:compressed.length < decoded.length ? compressed : decoded, records:['compact','compactObs'].includes(data.task)?records:undefined});
  } catch (error) { self.postMessage({id:data.id, error:error.message}); }
};
