/* Lossless local storage for Treino36. Existing JSON and exports keep their schema. */
(() => {
  const prefix = 'treino36:lz:1:';
  const originalGet = Storage.prototype.getItem;
  const originalSet = Storage.prototype.setItem;
  const owned = key => /^(treino|avaliacao)/.test(key);
  const unpack = value => {
    if (value === null || !value.startsWith(prefix)) return value;
    const decoded = LZString.decompressFromUTF16(value.slice(prefix.length));
    if (decoded === null) throw Error('Não foi possível ler os dados guardados. Preserve o backup JSON.');
    return decoded;
  };
  const pack = value => {
    if (value.length < 512) return value;
    const compressed = prefix + LZString.compressToUTF16(value);
    return compressed.length < value.length ? compressed : value;
  };
  Storage.prototype.getItem = function(key) {
    const value = originalGet.call(this, key);
    return owned(String(key)) ? unpack(value) : value;
  };
  Storage.prototype.setItem = function(key, value) {
    key = String(key); value = String(value);
    originalSet.call(this, key, owned(key) ? pack(value) : value);
  };
  // Replace one key at a time. A failed migration always leaves that original key intact.
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!owned(key)) continue;
      const value = originalGet.call(localStorage, key);
      if (value && !value.startsWith(prefix)) {
        const compressed = pack(value);
        if (compressed.length < value.length) originalSet.call(localStorage, key, compressed);
      }
    }
  } catch (error) { console.warn('Os dados existentes foram preservados:', error.name); }
})();
