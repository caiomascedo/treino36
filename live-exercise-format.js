/* Format only the name prefix when a prescription starts; retain media nodes and caret. */
(()=>{
 function point(root,offset){const walk=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let node,last;while(node=walk.nextNode()){last=node;if(offset<=node.length)return [node,offset];offset-=node.length;}return last?[last,last.length]:[root,0];}
 function format(event){
  if(event.isComposing||event.inputType?.startsWith('delete'))return;
  const selection=getSelection();if(!selection.rangeCount||!selection.isCollapsed)return;
  const element=selection.anchorNode.nodeType===1?selection.anchorNode:selection.anchorNode.parentElement;
  const row=element.closest('.section>ol>li,.zoom-exercises>li');if(!row||element.closest('a,button,.exercise-gifs,.exercise-videos'))return;
  const root=row.querySelector('.exercise-text')||row,text=root.textContent;if(!root.isContentEditable)return;
  const marker=/\s*[—–]\s*|\s+\d+\s*[x×]/i.exec(text);if(!marker)return;
  const explicit=/[—–]/.test(marker[0]),start=marker.index,name=text.slice(0,start).trim();if(!name)return;
  const end=explicit?marker.index+marker[0].length:marker.index+marker[0].search(/\d/);
  const prefix=name+' — ',existing=root.querySelector('.bold');
  const plain=root.querySelector('.exercise-prescription');if(explicit&&existing?.textContent===name&&plain?.contains(selection.anchorNode))return;
  const caret=document.createRange();caret.selectNodeContents(root);try{caret.setEnd(selection.anchorNode,selection.anchorOffset);}catch(e){return;}const offset=caret.toString().length;if(offset<end)return;
  const range=document.createRange();range.selectNodeContents(root);const media=root.querySelector('.exercise-video,.exercise-videos,.exercise-gifs');if(media)range.setEndBefore(media);const content=range.toString();if(content.length<end)return;const suffix=content.slice(end);range.deleteContents();const strong=document.createElement('span');strong.className='bold';strong.textContent=name;const prescription=document.createElement('span');prescription.className='exercise-prescription';prescription.style.fontWeight='normal';prescription.textContent=' —\u00a0'+suffix;const fragment=document.createDocumentFragment();fragment.append(strong,prescription);range.insertNode(fragment);
  const next=offset>=end?offset+prefix.length-end:Math.min(offset,name.length);const restored=document.createRange();restored.setStart(...point(root,next));restored.collapse(true);selection.removeAllRanges();selection.addRange(restored);
 }
 document.addEventListener('input',format,true);
 document.addEventListener('compositionend',format,true);
})();
