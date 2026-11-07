// Preserve the original SVG paths and bake the source HTML's two icon CSS rules.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),sharp=require('sharp');
const p=process.argv[2],d=JSON.parse(fs.readFileSync(path.join(p,'source-dom.json')));
const hash=x=>crypto.createHash('sha256').update(fs.readFileSync(x)).digest('hex');
(async()=>{for(const s of d.svgs){
 const sw=/class="[^"]*ac-point-icon/.test(s.xml)?1.5:1.6;
 const xml=s.xml.replace('<svg ','<svg style="color:#660874;stroke:#660874;stroke-width:'+sw+';fill:none" ');
 fs.writeFileSync(path.join(p,s.source),xml);
 await sharp(Buffer.from(xml)).resize(Math.ceil(s.box[2]*4),Math.ceil(s.box[3]*4)).png().toFile(path.join(p,s.path));
 s.source_sha256=hash(path.join(p,s.source));s.asset_sha256=hash(path.join(p,s.path));s.resolved_css={stroke:'#660874',strokeWidth:sw,fill:'none'};
}
fs.writeFileSync(path.join(p,'source-dom.json'),JSON.stringify(d,null,2));
const mp=path.join(p,'manifest.json');if(fs.existsSync(mp)){
 const m=JSON.parse(fs.readFileSync(mp));for(const a of m.asset_provenance){const s=d.svgs.find(s=>s.path===a.path);if(s){a.source_sha256=s.source_sha256;a.asset_sha256=s.asset_sha256;a.provenance_note+=' Original HTML icon CSS stroke #660874, width '+s.resolved_css.strokeWidth+' resolved before raster normalization.';}}
 fs.writeFileSync(mp,JSON.stringify(m,null,2));
}console.log('Resolved exact source SVG CSS for',d.svgs.length,'icons in',path.basename(p));})();
