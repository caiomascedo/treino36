/* Visual help only: never changes measurements or saved assessments. */
window.SkinfoldGuides=(()=>{
  const source='https://www.sanny.com.br/dobras-cutaneas',assets=new URL('assets/skinfolds/',document.currentScript.src);
  const guides={
    triceps:{title:'Tríceps',image:'triceps',location:'Face posterior do braço, no ponto médio entre o ombro (acrômio) e o cotovelo (olécrano).',direction:'Vertical.',tip:'Deixe o braço relaxado ao lado do corpo.'},
    axilar:{title:'Axilar média',image:'axilar',location:'Linha axilar média, na altura do apêndice xifoide, na extremidade inferior do esterno.',direction:'Vertical no Jackson–Pollock.',tip:'Afaste o braço para acessar o ponto; a fotografia ilustra a região, não substitui a marcação.'},
    torax:{title:'Tórax · peitoral',image:'torax-masculino',location:'Entre a prega axilar anterior e o mamilo: metade da distância nos homens; um terço a partir da axila nas mulheres.',direction:'Diagonal, acompanhando a linha entre axila e mamilo.',tip:'Use a marcação correspondente ao sexo e ao protocolo.'},
    abdominal:{title:'Abdominal',image:'abdominal',location:'Aproximadamente 2 cm à direita do umbigo.',direction:'Vertical nesta configuração.',tip:'Mantenha o abdômen relaxado.'},
    suprailiaca:{title:'Suprailíaca',image:'suprailiaca',location:'Imediatamente acima da crista ilíaca, na linha axilar anterior no Jackson–Pollock.',direction:'Oblíqua, seguindo a prega natural.',tip:'Não confunda crista ilíaca com o ponto supraespinal; a padronização muda conforme a referência.'},
    subescapular:{title:'Subescapular',image:'subescapular',location:'Logo abaixo do ângulo inferior da escápula, cerca de 1–2 cm.',direction:'Diagonal, aproximadamente 45°.',tip:'Localize a escápula antes de marcar o ponto.'},
    pregaCoxa:{title:'Coxa · prega',image:'coxa',location:'Face anterior da coxa, no ponto médio entre a prega inguinal e a borda superior da patela.',direction:'Vertical.',tip:'Mantenha a perna avaliada relaxada.'},
    bicipital:{title:'Bicipital',image:'bicipital',location:'Face anterior do braço, no mesmo nível do ponto médio usado para o tríceps no Durnin–Womersley.',direction:'Vertical.',tip:'Braço relaxado; esta é uma dobra em mm, não a circunferência do bíceps.'},
    panturrilha:{title:'Panturrilha medial',image:'panturrilha',location:'Face interna da panturrilha, no nível de maior perímetro.',direction:'Vertical.',tip:'Joelho a 90°, musculatura relaxada; não confunda com circunferência em cm.'}
  };
  let serial=0,viewer;
  function guide(key,protocol,sex){
    if(!guides[key])return null;const data={...guides[key]};
    if(key==='torax'&&sex==='F')data.image='torax-feminino';
    if(key==='torax'&&protocol==='carter6')data.tip+=' Medida adicional: não integra as seis dobras nem o cálculo Carter-Yuhasz; não substitui a panturrilha.';
    if(key==='suprailiaca'&&protocol==='dw4')data.location='Logo acima da crista ilíaca, na linha axilar média, conforme Durnin–Womersley.';
    if(key==='suprailiaca'&&['carter6','yuhasz6','registro'].includes(protocol))data.location='Acima da crista ilíaca. Confirme a linha de marcação na referência da configuração usada; não troque por supraespinal.';
    if(key==='axilar'&&protocol==='registro')data.direction='Registre a direção usada e mantenha a mesma padronização nas próximas medidas.';
    data.src=new URL(data.image+'.jpg',assets).href;return data;
  }
  function el(tag,cls,text){const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node;}
  function enlarge(data){
    if(!viewer){viewer=el('dialog','skinfold-image-viewer');const toolbar=el('div','skinfold-image-toolbar'),title=el('strong'),close=el('button',null,'Fechar');close.type='button';close.onclick=()=>viewer.close();toolbar.append(title,close);viewer.append(toolbar,el('div','skinfold-image-body'));document.body.append(viewer);}
    viewer.querySelector('strong').textContent=data.title;const image=el('img');image.src=data.src;image.alt='Imagem de referência Sanny: '+data.title;viewer.querySelector('.skinfold-image-body').replaceChildren(image);viewer.showModal();
  }
  function mount(grid,{fields,protocol,sex,input}){
    grid.classList.add('skinfold-fields');
    const entries=fields.map(key=>{const control=input(key);return control&&guides[key]?{key,wrap:control.parentElement}:null;}).filter(Boolean),panels=[];
    for(const entry of entries){
      const {key,wrap}=entry;if(wrap.querySelector('.skinfold-help-toggle'))continue;
      const label=wrap.querySelector('label'),heading=el('div','skinfold-field-heading'),button=el('button','skinfold-help-toggle','+'),panel=el('section','skinfold-help-panel');panel.id='skinfold-guide-'+(++serial);panel.hidden=true;panel.dataset.skinfoldGuide=key;
      button.type='button';button.setAttribute('aria-label','Ver orientação: '+guides[key].title);button.setAttribute('aria-controls',panel.id);button.setAttribute('aria-expanded','false');
      label.replaceWith(heading);heading.append(label,button);grid.append(panel);panels.push({panel,button});
      button.onclick=()=>{
        const opening=panel.hidden;panels.forEach(({panel,button})=>{panel.hidden=true;button.textContent='+';button.setAttribute('aria-expanded','false');});if(!opening)return;
        const data=guide(key,protocol,sex);
        if(!panel.childElementCount){
          const image=el('img','skinfold-guide-photo');image.src=data.src;image.alt='Local de referência: '+data.title+' · Sanny';image.decoding='async';
          const zoom=el('button','skinfold-guide-zoom','⛶ Ampliar imagem');zoom.type='button';zoom.onclick=()=>enlarge(data);panel.append(el('strong','skinfold-guide-title',data.title),image,zoom);
          for(const [title,text] of [['Localização',data.location],['Sentido da dobra',data.direction],['Dica',data.tip]]){const p=el('p');p.append(el('b',null,title+': '),document.createTextNode(text));panel.append(p);}
          panel.append(el('p','skinfold-guide-note','Imagem de referência. Meça no lado direito e siga a padronização do protocolo escolhido; os pontos não são intercambiáveis.'));const link=el('a','skinfold-guide-source','Foto e referência: Sanny');link.href=source;link.target='_blank';link.rel='noopener noreferrer';panel.append(link);
        }
        const index=entries.indexOf(entry),rowEnd=entries[Math.min(index-index%2+1,entries.length-1)];rowEnd.wrap.after(panel);panel.hidden=false;button.textContent='−';button.setAttribute('aria-expanded','true');
      };
    }
  }
  return {guides,guide,mount};
})();
