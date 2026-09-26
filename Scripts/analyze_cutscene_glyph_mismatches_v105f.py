import json
from pathlib import Path
import numpy as np
from PIL import Image
from probe_tails_atlas_v105d import render_one

ROOT=Path(__file__).resolve().parents[1]
pages=json.loads((ROOT/'Build/Review6-ResolutionSplit/cutscene-atlas-maps.json').read_text(encoding='utf-8-sig'))
bad=[]
for page in pages:
    original=Image.open(ROOT/'Build/FinalAudit-v104/Archives/Inspire/subtitle/English'/('+'+page['archive'])/('+'+page['archive'])/page['texture']).convert('RGBA')
    recreated=render_one(original,page['entries'],1)
    for entry in page['entries']:
        if entry['character']==' ':continue
        box=tuple(entry['rect'])
        a=np.asarray(original.crop(box).convert('L'))>127
        b=np.asarray(recreated.crop(box).convert('L'))>127
        union=np.logical_or(a,b).sum()
        iou=float(np.logical_and(a,b).sum()/union) if union else 1
        if iou<.85:bad.append({'archive':page['archive'],'file':page['texture'],
                              'character':entry['character'],'id':entry['id'],'rect':entry['rect'],'iou':iou})
out=ROOT/'Build/Review6-ResolutionSplit/cutscene-mismatched-glyphs.json'
out.write_text(json.dumps(bad,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('mismatched',len(bad),'byCharacter',{})
from collections import Counter
print('characters',[(hex(ord(c)),n) for c,n in Counter(x['character'] for x in bad).most_common(20)])
print('worst',[(x['archive'],hex(ord(x['character'])),round(x['iou'],3)) for x in sorted(bad,key=lambda x:x['iou'])[:15]])
