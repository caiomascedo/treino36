/* Assessment report colors; keep values neutral and color only signed deltas. */
window.AssessmentPDFStyle=(()=>{
  const emerald=[30,111,63],positive=[190,45,45],negative=[30,111,63];
  function tableHooks(doc){
    return {
      willDrawCell(data){
        const cell=data.cell;
        if(data.section!=='body'||data.column.index===0||! /\([+-]\d/.test(cell.text.join('\n')))return;
        const lines=[[]],neutral=cell.styles.textColor;
        cell.text.join('\n').split(/(\([+-][^)]*\))/g).forEach(part=>{
          const color=/^\(\+/.test(part)?positive:/^\(-/.test(part)?negative:neutral;
          part.split('\n').forEach((text,index)=>{if(index)lines.push([]);if(text)lines.at(-1).push({text,color});});
        });
        cell._deltaLines=lines;cell._deltaOriginalText=cell.text;cell.text=[];
      },
      didDrawCell(data){
        const cell=data.cell,lines=cell._deltaLines;if(!lines)return;
        const fontHeight=cell.styles.fontSize/doc.internal.scaleFactor,lineHeight=fontHeight*1.15,pos=cell.getTextPos();
        let y=pos.y+fontHeight*.85;
        if(cell.styles.valign==='middle')y-=lines.length*lineHeight/2;
        else if(cell.styles.valign==='bottom')y-=lines.length*lineHeight;
        const originalColor=doc.getTextColor();
        lines.forEach(line=>{
          const width=line.reduce((sum,run)=>sum+doc.getTextWidth(run.text),0);
          let x=pos.x-(cell.styles.halign==='right'?width:cell.styles.halign==='center'?width/2:0);
          line.forEach(run=>{doc.setTextColor(...(Array.isArray(run.color)?run.color:[run.color]));doc.text(run.text,x,y);x+=doc.getTextWidth(run.text);});y+=lineHeight;
        });
        doc.setTextColor(originalColor);cell.text=cell._deltaOriginalText;delete cell._deltaLines;delete cell._deltaOriginalText;
      }
    };
  }
  return {emerald,tableHooks};
})();
