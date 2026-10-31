/* gifenc 1.0.3 (MIT): encode one frame at a time to bound mobile memory use. */
self.exports = {};
importScripts('gif-vendor/gifenc.js');
let encoder, palette;
self.onmessage = ({data}) => {
  try {
    if (data.type === 'frame') {
      const rgba = new Uint8Array(data.pixels);
      if (!encoder) {
        encoder = exports.GIFEncoder();
        palette = exports.quantize(rgba, 128, {format: 'rgb444'});
      }
      const index = exports.applyPalette(rgba, palette, 'rgb444');
      encoder.writeFrame(index, data.width, data.height, {palette, delay: 50, repeat: 0});
      self.postMessage({type: 'ready'});
    } else if (data.type === 'finish') {
      encoder.finish();
      const bytes = encoder.bytes();
      self.postMessage({type: 'gif', bytes}, [bytes.buffer]);
      encoder = null; palette = null;
    }
  } catch (error) { self.postMessage({type: 'error', message: error.message}); }
};
