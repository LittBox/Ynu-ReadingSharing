const fs=require('fs');
const path=require('path');
const {chromium}=require('playwright');
const root='/Users/admin/Desktop/云上书屋/宣讲PPT/academic-delivery-test';
const out=path.join(__dirname,'input');
(async()=>{
const browser=await chromium.launch({headless:true,executablePath:'/Users/admin/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'});
console.log('browser ready');
const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
await page.route('https://**',r=>r.abort());
const html=fs.readFileSync(root+'/index.html','utf8').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'').replace('<head>','<head><base href="file://'+root+'/">');
fs.writeFileSync(out+'/source-snapshot.html',html);
await page.goto('file://'+out+'/source-snapshot.html',{waitUntil:'domcontentloaded'});
console.log('loaded');
await page.evaluate(()=>{document.getAnimations().forEach(a=>a.cancel());document.body.classList.add('low-power');});
await page.addStyleTag({content:'*{animation:none!important;transition:none!important} #deck{transform:none!important} .slide{display:none!important} .slide.capture{display:block!important} [data-anim]{opacity:1!important;transform:none!important} body>nav,body>.nav,canvas,#nav,#overview,#progress,#hint{display:none!important}'});
for(let i=0;i<30;i++){
await page.evaluate(i=>{document.querySelectorAll('.slide').forEach((s,j)=>s.classList.toggle('capture',i===j));},i);
const slide=page.locator('.slide.capture');
const data=await slide.evaluate(s=>{
 const origin=s.getBoundingClientRect();
 const rect=r=>[r.x-origin.x,r.y-origin.y,r.width,r.height].map(x=>Math.round(x*100)/100);
 const col=x=>{const m=x.match(/[\d.]+/g);if(!m||m.length>3&&+m[3]===0)return null;return '#'+m.slice(0,3).map(x=>(+x).toString(16).padStart(2,'0')).join('')};
 let texts=[],shapes=[],images=[],svgs=[],order=0;
 const walk=el=>{
  const c=getComputedStyle(el),b=el.getBoundingClientRect();
  if(c.display==='none'||c.visibility==='hidden'||!b.width||!b.height)return;
  const z=order++;
  if(el.tagName.toLowerCase()==='svg'){svgs.push({box:rect(b),xml:new XMLSerializer().serializeToString(el),color:c.color,z});return;}
  const bg=col(c.backgroundColor);
  if(bg)shapes.push({type:'fill',box:rect(b),fill:bg,radius:parseFloat(c.borderTopLeftRadius)||0,z});
  for(const edge of ['Top','Right','Bottom','Left']){
   const w=parseFloat(c['border'+edge+'Width']);if(w&&c['border'+edge+'Style']!=='none')shapes.push({type:'border',box:rect(b),edge,width:w,color:col(c['border'+edge+'Color']),style:c['border'+edge+'Style'],z});
  }
  if(el.tagName==='IMG'){images.push({box:rect(b),src:el.getAttribute('src'),fit:c.objectFit,position:c.objectPosition,natural:[el.naturalWidth,el.naturalHeight],alt:el.alt,z});return;}
  for(const n of el.childNodes){
   if(n.nodeType===1){walk(n);continue;}
   if(n.nodeType!==3||!n.textContent.trim())continue;
   let lines=[];
   for(let k=0;k<n.textContent.length;k++){
    const r=document.createRange();r.setStart(n,k);r.setEnd(n,k+1);const a=r.getBoundingClientRect();if(!a.width||!a.height)continue;
    let line=lines.find(l=>Math.abs(l.y-a.y)<2);if(!line){line={y:a.y,x:a.x,right:a.right,height:a.height,text:''};lines.push(line);}
    line.text+=n.textContent[k];line.x=Math.min(line.x,a.x);line.right=Math.max(line.right,a.right);
   }
   for(const l of lines)if(l.text.trim())texts.push({text:l.text.trim(),box:[l.x-origin.x,l.y-origin.y,l.right-l.x,l.height],font:c.fontFamily,size:parseFloat(c.fontSize),weight:c.fontWeight,color:col(c.color),lineHeight:c.lineHeight,letterSpacing:c.letterSpacing,z:order++,tag:el.tagName,cls:el.className});
  }
 };
 walk(s);return {id:s.dataset.slideId,title:s.querySelector('h1')?.innerText,size:[1920,1080],texts,shapes,images,svgs};
});
const n=String(i+1).padStart(3,'0');
fs.writeFileSync(out+'/page_'+n+'.json',JSON.stringify(data,null,2));
await slide.screenshot({path:out+'/page_'+n+'.png'});
console.log(n,data.title,data.texts.length,data.shapes.length,data.images.length,data.svgs.length);
}
await browser.close();
})();
