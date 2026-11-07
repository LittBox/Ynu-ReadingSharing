const fs=require('fs'),path=require('path'),crypto=require('crypto');
const sharp=require('sharp');
const base=__dirname,original='/Users/admin/Desktop/云上书屋/宣讲PPT/academic-delivery-test';
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
(async()=>{for(let i=1;i<=30;i++){
 const id='page_'+String(i).padStart(3,'0'),p=path.join(base,'run/pages',id),d=JSON.parse(fs.readFileSync(path.join(base,'input',id+'.json')));
 fs.mkdirSync(path.join(p,'assets'),{recursive:true});
 for(let j=0;j<d.images.length;j++){
  const img=d.images[j];const rel='assets/image_'+j+path.extname(img.src);fs.copyFileSync(path.join(original,img.src),path.join(p,rel));
  img.path=rel;img.source=rel;img.source_sha256=hash(path.join(p,rel));img.asset_sha256=img.source_sha256;
 }
 for(let j=0;j<d.svgs.length;j++){
  const s=d.svgs[j];const raw='assets/icon_'+j+'.svg',png='assets/icon_'+j+'.png';
  const sw=/class="[^"]*ac-point-icon/.test(s.xml)?1.5:1.6;
  const xml=s.xml.replace('<svg ','<svg style="color:#660874;stroke:#660874;stroke-width:'+sw+';fill:none" ');
  fs.writeFileSync(path.join(p,raw),xml);
  await sharp(Buffer.from(xml)).resize(Math.ceil(s.box[2]*4),Math.ceil(s.box[3]*4)).png().toFile(path.join(p,png));
  s.path=png;s.source=raw;s.source_sha256=hash(path.join(p,raw));s.asset_sha256=hash(path.join(p,png));
 }
 fs.writeFileSync(path.join(p,'source-dom.json'),JSON.stringify(d,null,2));
}console.log('Staged exact HTML text geometry and original assets for 30 pages');})();
