/* Lossless local storage for Treino36. Existing JSON and exports keep their schema. */
(() => {
  const prefix = 'treino36:lz:1:';
  const originalGet = Storage.prototype.getItem;
  const originalSet = Storage.prototype.setItem;
  const owned = key => /^(treino|avaliacao)/.test(key);
  const caches = new WeakMap();
  const cacheFor = storage => {
    if (!caches.has(storage)) caches.set(storage, new Map());
    return caches.get(storage);
  };
  const remember = (cache, key, raw, decoded) => {
    if (cache.size >= 12 && !cache.has(key)) cache.delete(cache.keys().next().value);
    cache.set(key, {raw, decoded});
  };
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
    key = String(key);
    const value = originalGet.call(this, key);
    if (!owned(key)) return value;
    const cache = cacheFor(this), entry = cache.get(key);
    // Always compare with the actual storage, including changes made by another window.
    if (entry && entry.raw === value) return entry.decoded;
    const decoded = unpack(value);
    remember(cache, key, value, decoded);
    return decoded;
  };
  Storage.prototype.setItem = function(key, value) {
    key = String(key); value = String(value);
    if (!owned(key)) return originalSet.call(this, key, value);
    const cache = cacheFor(this), entry = cache.get(key);
    if (entry && entry.decoded === value && originalGet.call(this, key) === entry.raw) return;
    const packed = pack(value);
    originalSet.call(this, key, packed);
    remember(cache, key, packed, value);
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
