const dataUrl='data.json';
const screenshotUrl=url=>url?'https://s.wordpress.com/mshots/v1/'+encodeURIComponent(url)+'?w=1200&h=700':'';
const imageFor=(image,url)=>image||screenshotUrl(url);
const safeImage=(src,alt,cls='')=>src?'<img class="'+cls+'" src="'+src+'" alt="'+alt+'" loading="lazy" onerror="this.style.display=\'none\'">':'';
async function init(){
  const d=await fetch(dataUrl+'?v='+Date.now()).then(r=>r.json());
  document.getElementById('editionDate').textContent=d.date;
  document.getElementById('authorName').textContent=d.author||'Yogesh Raghupati';
  document.getElementById('leadTitle').textContent=d.lead.title;
  document.getElementById('leadDeck').textContent=d.lead.deck;
  document.getElementById('leadLink').href=d.lead.url;
  const leadImage=document.getElementById('leadImage');
  if(leadImage){
    const src=imageFor(d.lead.image,d.lead.url);
    if(src){
      leadImage.src=src;
      leadImage.alt=d.lead.title;
      leadImage.hidden=false;
    }
  }
  document.getElementById('note').textContent=d.note;
  document.getElementById('nav').innerHTML=d.sections.map(s=>'<a href="#'+slug(s.name)+'">'+s.name+'</a>').join('');
  document.getElementById('ticker').textContent=d.ticker.join(' • ');
  document.getElementById('sections').innerHTML=d.sections.map(s=>'<section class="section" id="'+slug(s.name)+'"><h3>'+s.name+'</h3><div class="grid">'+s.stories.map(story).join('')+'</div></section>').join('')
}
function story(s){
  const img=imageFor(s.image,s.url);
  return '<article class="story">'+safeImage(img,s.title,'story-image')+'<div class="meta">'+s.source+' · '+s.when+'</div><h4><a href="'+s.url+'" target="_blank" rel="noopener">'+s.title+'</a></h4><p>'+s.summary+'</p></article>'
}
function slug(s){return s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'')}
init().catch(()=>document.getElementById('leadTitle').textContent='Today\'s edition is being refreshed.');