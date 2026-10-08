const dataUrl='data.json';
const fallbackDataUrl='https://raw.githubusercontent.com/yogeshp05/ai-marketing-daily/main/data.json';

const escapeXml=(s='')=>s.replace(/[<>&'"]/g,m=>({'<':'&lt;','>':'&gt;','&':'&amp;',"'":'&apos;','"':'&quot;'}[m]));
const wrapTitle=(title='',maxChars=27,maxLines=3)=>{
  const words=String(title||'Daily intelligence').split(/\\s+/).filter(Boolean);
  const lines=[]; let line='';
  for(const word of words){
    const next=line?line+' '+word:word;
    if(next.length>maxChars && line){ lines.push(line); line=word; if(lines.length===maxLines-1) break; } else line=next;
  }
  if(lines.length<maxLines && line) lines.push(line);
  const original=String(title||'Daily intelligence');
  if(lines.length && lines.join(' ').length<original.length){ lines[lines.length-1]=lines[lines.length-1].slice(0,Math.max(1,maxChars-1))+'…'; }
  return lines;
};
const fallbackImage=(title='',section='')=>{
  const label=section||'AI MARKETING';
  const lines=wrapTitle(title,27,3);
  const tspans=lines.map((line,i)=>'<tspan x="70" dy="'+(i===0?0:68)+'">'+escapeXml(line)+'</tspan>').join('');
  const svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">'+
  '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#111827"/><stop offset="1" stop-color="#334155"/></linearGradient></defs>'+
  '<rect width="1200" height="700" fill="url(#g)"/>'+
  '<circle cx="980" cy="130" r="210" fill="none" stroke="#94a3b8" stroke-opacity=".25" stroke-width="2"/>'+
  '<circle cx="980" cy="130" r="140" fill="none" stroke="#94a3b8" stroke-opacity=".18" stroke-width="2"/>'+
  '<path d="M760 430 L900 290 L1010 380 L1120 230" fill="none" stroke="#e2e8f0" stroke-width="5" opacity=".65"/>'+
  '<text x="70" y="100" font-family="Arial,sans-serif" font-size="28" letter-spacing="5" fill="#cbd5e1">'+escapeXml(label.toUpperCase())+'</text>'+
  '<text x="70" y="225" font-family="Arial,sans-serif" font-size="54" font-weight="700" fill="white">'+tspans+'</text>'+
  '<text x="70" y="610" font-family="Arial,sans-serif" font-size="24" fill="#cbd5e1">AI MARKETING DAILY</text>'+
  '</svg>';
  return 'data:image/svg+xml;charset=UTF-8,'+encodeURIComponent(svg);
};const topicImage=(title,section='')=>fallbackImage(title,section);
const imageFor=(image,title,section)=>image||fallbackImage(title,section);
const safeImage=(src,alt,cls='',fallback='')=>src?'<img class="'+cls+'" src="'+src+'" alt="'+alt+'" loading="lazy" onerror="this.onerror=null;this.src=\''+fallback+'\'">':'';

async function loadData(){
  try{
    const r=await fetch(dataUrl+'?v='+Date.now(),{cache:'no-store'});
    if(!r.ok) throw new Error('Local data.json returned '+r.status);
    return await r.json();
  }catch(localError){
    const r=await fetch(fallbackDataUrl+'?v='+Date.now(),{cache:'no-store'});
    if(!r.ok) throw new Error('Fallback data.json returned '+r.status);
    return await r.json();
  }
}
async function init(){
  const d=await loadData();
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
      leadImage.onerror=()=>{leadImage.onerror=null;leadImage.src=fallbackImage(d.lead.title,'Lead Story');};
    }
  }
  document.getElementById('note').textContent=d.note;
  document.getElementById('nav').innerHTML=d.sections.map(s=>'<a href="#'+slug(s.name)+'">'+s.name+'</a>').join('');
  document.getElementById('ticker').textContent=d.ticker.join(' • ');
  document.getElementById('sections').innerHTML=d.sections.map(s=>'<section class="section" id="'+slug(s.name)+'"><h3>'+s.name+'</h3><div class="grid">'+(s.stories||[]).map(st=>story({...st,section:s.name})).join('')+'</div></section>').join('')+summarySection(d.summary);
}
function summarySection(s){ if(!s) return ''; return '<section class="section summary-section" id="what-s-actually-new"><h3>'+s.title+'</h3><p class="summary-intro">'+s.intro+'</p>'+(s.topics||[]).map(t=>'<article class="story summary-topic"><div class="meta">'+t.status+'</div><h4>'+t.topic+'</h4><p><strong>Common context:</strong> '+t.common_context+'</p><ul>'+(t.unique_points||[]).map(p=>'<li><strong>'+p.source+' · '+p.when+':</strong> '+p.point+' <a href="'+p.url+'" target="_blank" rel="noopener">Source</a></li>').join('')+'</ul><p><strong>Bottom line:</strong> '+t.bottom_line+'</p></article>').join('')+'</section>'; }
function story(s){
  const img=imageFor(s.image,s.title,s.section||'AI Marketing');
  return '<article class="story">'+safeImage(img,s.title,'story-image',fallbackImage(s.title,s.section||'AI Marketing'))+'<div class="meta">'+s.source+' · '+s.when+'</div><h4><a href="'+s.url+'" target="_blank" rel="noopener">'+s.title+'</a></h4><p>'+s.summary+'</p></article>';
}
function slug(s){return s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'')}
init().catch(error=>{
  console.error('AI Marketing Daily load error:',error);
  document.getElementById('leadTitle').textContent='Today\'s edition is temporarily unavailable.';
  document.getElementById('leadDeck').textContent='Please refresh in a moment while the daily edition finishes publishing.';
  document.getElementById('ticker').textContent='Edition refresh in progress…';
});