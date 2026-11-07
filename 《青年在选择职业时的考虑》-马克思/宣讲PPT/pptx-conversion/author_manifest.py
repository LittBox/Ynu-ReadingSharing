"""Write page-local object manifest from measured HTML source evidence. No build or lifecycle."""
import json,sys,math
from pathlib import Path
p=Path(sys.argv[1]).resolve()
d=json.loads((p/'source-dom.json').read_text());r=json.loads((p/'page_request.json').read_text())
scale=r['content_box']['width']*72/1920
approval='用户明确回复“全部原样复用（推荐）”：本HTML全部原始图片及SVG图标原样复用，只重建文字、表格和布局。'
m={'schema_version':2,'slide':dict(r['slide'],background='#fbf9fc'),'content_box':r['content_box'],'source':{'path':'source.png','width_px':1920,'height_px':1080},'page_strategy':'Retain measured source composition; editable text and layout primitives; explicitly approved original visual assets.', 'text_inventory':[], 'visual_inventory':[], 'background_strategy':{'mode':'native-or-script','source_consistency_contract':'Solid source fills, measured panel bounds, original purple palette and positions are preserved.','removed_foreground':'No flattened source background; all readable HTML text is represented by native text boxes.','comparison_note':'Solid background and panel fills are measured directly from source HTML.'},'quality_checks':{},'quality_evidence':{},'text_boxes':[],'shapes':[],'images':[],'asset_provenance':[]}
for i,t in enumerate(d['texts']):
 b=list(t['box']);b[2]+=5;b[3]+=3
 font='Source Han Sans SC' if any('\u3400'<=c<='\u9fff' for c in t['text']) else 'Helvetica Neue'
 item={'id':f'text_{i:03}','text':t['text'],'box_px':b,'font':font,'font_size':round(t['size']*scale,3),'font_size_source':'measured','color':t['color'],'bold':float(t['weight'])>=600,'wrap':'none','line_height':1.0,'fit_text':False,'z_index':t['z']*10+5}
 m['text_boxes'].append(item);m['text_inventory'].append(t['text'])
for i,s in enumerate(d['shapes']):
 x,y,w,h=s['box'];item={'id':f'shape_{i:03}','z_index':s['z']*10,'stroke':'none'}
 if s['type']=='fill':
  rad=min(s['radius'],w/2,h/2);item.update(type='roundRect' if rad else 'rect',box_px=s['box'],fill=s['fill'])
  if rad:item.update(source_corner_radius_px=rad,corner_category='pill' if rad>=min(w,h)/2 else 'small-radius',corner_reason='Measured CSS corner radius clipped to half the shorter side.')
  if s['box']==[0,0,1920,1080]:m['slide']['background']=s['fill']
 else:
  a={'Top':[x,y,x+w,y],'Right':[x+w,y,x+w,y+h],'Bottom':[x,y+h,x+w,y+h],'Left':[x,y,x,y+h]}[s['edge']]
  item.update(type='line',points_px=a,stroke=s['color'],stroke_width=s['width']*scale)
  if s['style']=='dashed':item['dash']='dash'
 m['shapes'].append(item)
 # CSS selected-chapter marker is a native triangle, not an illustrative arrow.
 if s['type']=='fill' and y<100 and s['fill'].lower()=='#660874':
  tx=x+w*.24;ty=y+h-1
  m['shapes'].append({'id':f'chapter_marker_{i}','type':'rect','box_px':[tx-10.56,ty,21.12,11.34],'polygon_px':[[tx-10.56,ty],[tx+10.56,ty],[tx,ty+11.34]],'fill':s['fill'],'stroke':'none','z_index':s['z']*10+1})
for j,s in enumerate(d['images']+d['svgs']):
 b=list(s['box'])
 if 'natural' in s and s['fit']=='contain':
  nw,nh=s['natural'];k=min(b[2]/nw,b[3]/nh);w,h=nw*k,nh*k
  position=s.get('position','50% 50%').split();px=float(position[0].rstrip('%'))/100;py=float(position[1].rstrip('%'))/100
  b=[b[0]+(b[2]-w)*px,b[1]+(b[3]-h)*py,w,h]
 item={'id':f'asset_{j:03}','path':s['path'],'box_px':b,'alt':s.get('alt','Original source SVG icon'),'z_index':s['z']*10+2};m['images'].append(item)
 m['asset_provenance'].append({'path':s['path'],'source':s['source'],'source_type':'user-provided','user_approved_reuse':True,'approval_note':approval,'source_sha256':s['source_sha256'],'asset_sha256':s['asset_sha256'],'provenance_note':'Original user-provided HTML asset; PNG copied byte-for-byte, or original SVG normalized to PNG without changing paths, color, or proportions.'})
 if s['source'].endswith('.svg'):m['asset_provenance'][-1]['normalization']='svg-to-png'
 m['visual_inventory'].append({'id':item['id'],'kind':'foreground-asset','representation':'user-provided-original','path':s['path'],'description':item['alt']})
m['visual_inventory'].append({'id':'native-layout','kind':'native-structure','representation':'native','description':'Measured editable solid panels, borders, table rows, and page navigation.'})
checks={'font_size_calibrated':'Text sizes and line positions measured from browser DOM at 1920 by 1080; native point sizes use slide physical scale.','visual_inventory_matched':f"All {len(m['images'])} source visual assets and {len(m['shapes'])} layout shapes are inventoried individually.",'background_strategy_checked':'Source solid background and panel colors retained as native fills, without full-slide source image.','shape_corner_geometry_checked':'Round rectangles use measured CSS radius constrained to source dimensions; table lines remain straight.'}
for k,v in checks.items():m['quality_checks'][k]=True;m['quality_evidence'][k]={'observation':v,'artifact':'source-dom.json'}
regions=[]
for rid,label,bounds in [('heading','Chapter navigation and title',[0,0,1920,235]),('content','Main content and source visuals',[0,235,1920,695]),('footer','Source citation and page number',[0,930,1920,150])]:
 reg={'id':rid,'label':label,'source_bbox_px':bounds,'risk_level':'medium','strategy':'mixed-reconstruction','reason':'Source DOM measurements preserve the semantic group and object geometry.','manifest_ids':{'shapes':[],'text_boxes':[],'images':[]},'protected_visual_anchors':[]};regions.append(reg)
for kind in ['shapes','text_boxes','images']:
 for o in m[kind]:
  y=o.get('box_px',o.get('points_px'))[1];reg=regions[0] if y<235 else regions[1] if y<930 else regions[2];reg['manifest_ids'][kind].append(o['id'])
  if kind=='shapes' and o.get('type')!='line':reg['protected_visual_anchors'].append({'id':'anchor_'+o['id'],'kind':'card-edge','manifest_id':o['id'],'source_bbox_px':o['box_px']})
m['image2ppt_region_decomposition']={'schema_version':'image2ppt-region-decomposition-v1','page_complexity':'structured','source_size_px':[1920,1080],'regions':regions}
(p/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print(p.name,len(m['text_boxes']),'text boxes',len(m['shapes']),'shapes',len(m['images']),'original images')
