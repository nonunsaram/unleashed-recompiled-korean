"""Measure whether all cutscene Korean glyphs match the known source font."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from probe_tails_atlas_v105d import render_one

ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/'Build/Review6-ResolutionSplit/cutscene-atlas-maps.json'
BASE=ROOT/'Build/FinalAudit-v104/Archives/Inspire/subtitle/English'
OUT=ROOT/'Build/Review6-ResolutionSplit/cutscene-font-probe.json'


def main()->None:
    pages=json.loads(MAP.read_text(encoding='utf-8-sig'))
    assert len(pages)==44
    results=[]
    for page in pages:
        original_path=BASE/('+'+page['archive'])/('+'+page['archive'])/page['texture']
        original=Image.open(original_path).convert('RGBA')
        assert original.size==(512,512)
        rebuilt=render_one(original,page['entries'],1)
        scores=[]
        for item in page['entries']:
            if item['character']==' ':continue
            box=tuple(item['rect'])
            a=np.asarray(original.crop(box).convert('L'))>127
            b=np.asarray(rebuilt.crop(box).convert('L'))>127
            union=np.logical_or(a,b).sum()
            scores.append(float(np.logical_and(a,b).sum()/union) if union else 1.0)
        results.append({'archive':page['archive'],'file':page['texture'],
                        'glyphs':len(scores),'meanIoU':sum(scores)/len(scores),
                        'minimumIoU':min(scores)})
    report={'pages':len(results),'glyphs':sum(r['glyphs'] for r in results),
            'meanPageIoU':sum(r['meanIoU'] for r in results)/len(results),
            'minimumPageMeanIoU':min(r['meanIoU'] for r in results),
            'worstPages':sorted(results,key=lambda r:r['meanIoU'])[:5],
            'rows':results}
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False))


if __name__=='__main__':main()
