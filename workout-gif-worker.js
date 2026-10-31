/* gifenc 1.0.3 (MIT). Cache small indexed frames; use one video decoder on
   the main thread instead of seeking several HD videos together on phones. */
self.exports = {};
importScripts('gif-vendor/gifenc.js');
let state;
self.onmessage = ({data}) => {
  try {
    if (data.type === 'init') {
      const palette = exports.quantize(new Uint8Array(data.sample), 192, {format:'rgb565'});
      state = {palette, base:exports.applyPalette(new Uint8Array(data.base),palette), width:data.width,height:data.height,slots:data.slots,frames:new Map(),count:data.count};
      self.postMessage({type:'ready'});
    } else if (data.type === 'cache') {
      if (!state.frames.has(data.key)) state.frames.set(data.key,[]);
      state.frames.get(data.key)[data.frame] = exports.applyPalette(new Uint8Array(data.pixels),state.palette);
      self.postMessage({type:'ready'});
    } else if (data.type === 'finish') {
      const encoder = exports.GIFEncoder();
      for(let frame=0;frame<state.count;frame++) {
        const pixels = state.base.slice();
        for(const slot of state.slots) {
          const image = state.frames.get(slot.key)?.[frame];
          if(!image)throw Error('Um movimento não foi preparado. Tente gerar novamente.');
          for(let y=0;y<slot.height;y++) pixels.set(image.subarray(y*slot.width,(y+1)*slot.width),(slot.y+y)*state.width+slot.x);
        }
        encoder.writeFrame(pixels,state.width,state.height,{palette:state.palette,delay:50,repeat:0});
        if(frame%5===0)self.postMessage({type:'progress',percent:85+Math.round((frame+1)/state.count*15)});
      }
      encoder.finish(); const bytes=encoder.bytes();
      state=null; self.postMessage({type:'gif',bytes},[bytes.buffer]);
    }
  }catch(error){state=null;self.postMessage({type:'error',message:error.message});}
};
