const dataUrl='data.json';
const topicImage=(title,section='')=>{const q=(section+' '+title).toLowerCase();let tags='marketing,technology,ai';if(/microsoft|bing|linkedin/.test(q))tags='microsoft,technology,business';else if(/meta|facebook|instagram/.test(q))tags='social-media,technology,business';else if(/amazon|shopping|ecommerce/.test(q))tags='ecommerce,shopping,technology';else if(/google|search|seo/.test(q))tags='search,technology,marketing';else if(/tiktok|creator/.test(q))tags='social-media,creator,technology';else if(/openai|agent|mcp/.test(q))tags='artificial-intelligence,technology,computer';return 'https://loremflickr.com/1200/700/'+tags+'?lock='+encodeURIComponent(title).slice(0,60)};
const imageFor=(image,title,section)=>image||topicImage(title,section);
const safeImage=(src,alt,cls='')=>src?'<img class="'+cls+'" src="'+src+'" alt="'+alt+'" loading="lazy" onerror="this.onerror=null;this.src=\'data:image/svg+xml;charset=UTF-8,\'+encodeURIComponent(\'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700"><rect width="100%" height="100%" fill="#eee"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Georgia" font-size="42" fill="#333">'+alt.replace(/&/g,\'and\').replace(/</g,\'\').replace(/>/g,\'\')+\'</text></svg>\')">':' ';
async function init(){
  const d=await fetch(dataUrl+'?v='+Date.now()).then(r=>r.json());
  document.getElementById('editionDate').textContent=d.date;
  document.getElementById('authorName').textContent=d.author||'Yogesh Raghupati';
  document.getElementById('leadTitle').textContent=d.lead.title;
  document.getElementById('leadDeck').textContent=d.lead.deck;
  document.getElementById('leadLink').href=d.lead.url;
  const leadImage=document.getElementById('leadImage');
  if(leadImage){
    const src=imageFor(d.lead.image,d.lead.title,'Lead Story');
    if(src){
      leadImage.src=src;
      leadImage.alt=d.lead.title;
      leadImage.hidden=false;
    }
  }
  document.getElementById('note').textContent=d.note;
  document.getElementById('nav').innerHTML=d.sections.map(s=>'<a href="#'+slug(s.name)+'">'+s.name+'</a>').join('');
  document.getElementById('ticker').textContent=d.ticker.join(' • ');
  document.getElementById('sections').innerHTML=d.sections.map(s=>'<section class="section" id="'+slug(s.name)+'"><h3>'+s.name+'</h3><div class="grid">'+s.stories.map(st=>story({...st,section:s.name})).join('')+'</div></section>').join('')
}
function story(s){
  const img=imageFor(s.image,s.title,s.section||'AI Marketing');
  return '<article class="story">'+safeImage(img,s.title,'story-image')+'<div class="meta">'+s.source+' · '+s.when+'</div><h4><a href="'+s.url+'" target="_blank" rel="noopener">'+s.title+'</a></h4><p>'+s.summary+'</p></article>'
}
function slug(s){return s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'')}
init().catch(()=>document.getElementById('leadTitle').textContent='Today\'s edition is being refreshed.');