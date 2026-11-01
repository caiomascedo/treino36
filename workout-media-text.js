/* Media stays in records, never in the visible prescription/editor text. */
window.WorkoutMediaText=(()=>{
 const tags=/\[(?:gifs?|v[ií]deos?):[^\]]*\]/gi;
 function strip(value){return String(value||'').replace(tags,'').replace(/https?:\/\/[^\s<>\]]+/gi,'').replace(/[ \t]+\n/g,'\n').replace(/[ \t]{2,}/g,' ').trim();}
 function merge(edited,original){const own=String(edited||'').match(tags),stored=String(original||'').match(tags);return strip(edited)+((own||stored)?.length?' '+(own||stored).join(' '):'');}
 function restore(lines,original){const old=original||[],clean=old.map(strip),used=new Set();return lines.map((line,index)=>{let found=clean.findIndex((v,i)=>!used.has(i)&&v===strip(line));if(found<0){const name=strip(line).split(/\s+[—–]\s+|\s+\d+\s*[x×]/)[0];const candidates=clean.map((v,i)=>({name:v.split(/\s+[—–]\s+|\s+\d+\s*[x×]/)[0],i})).filter(v=>!used.has(v.i)&&v.name===name);if(candidates.length===1)found=candidates[0].i;}if(found<0&&lines.length===old.length&&!used.has(index))found=index;if(found>=0)used.add(found);return merge(line,old[found]||'');});}
 return {strip,merge,restore};
})();
