"""Render Sonic/Tails/Chip names on UnleasHD's 512px dialogue atlas."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Build/Review6-ResolutionSplit/HdRootTown/+Town_Common/mat_talk_comon_002.dds'
OUT=ROOT/'Build/Review7-ResolutionSplit/HdNameplate/mat_talk_comon_002.dds'
FONT=ROOT/'Tools/Fonts/LINESeedKR-Rg.ttf'


def main()->None:
    assert SOURCE.is_file() and not OUT.exists()
    original=Image.open(SOURCE).convert('RGBA')
    assert original.size==(512,512)
    result=original.copy()
    font=ImageFont.truetype(str(FONT),54*4)
    mask=np.zeros((512,512),dtype=bool)
    labels=[(0,'소닉',0,0),(64,'테일즈',0,0),(128,'칩',-4,-3)]
    for y,text,dx,dy in labels:
        rect=(0,y,192,y+64)
        result.paste((0,0,0,0),rect)
        mask[y:y+64,0:192]=True
        layer=Image.new('RGBA',(192*4,64*4),(0,0,0,0))
        painter=ImageDraw.Draw(layer)
        l,t,r,b=painter.textbbox((0,0),text,font=font)
        painter.text(((192*4-(r-l))/2-l+dx*4,
                      (64*4-(b-t))/2-t+dy*4),text,font=font,fill='white')
        result.alpha_composite(layer.resize((192,64),Image.Resampling.LANCZOS),(0,y))
    assert np.array_equal(np.asarray(original)[~mask],np.asarray(result)[~mask])
    OUT.parent.mkdir(parents=True)
    result.save(OUT)
    with Image.open(OUT) as reopened:
        assert reopened.size==(512,512)
        assert np.array_equal(np.asarray(reopened.convert('RGBA'))[~mask],np.asarray(original)[~mask])
    report={'passed':True,'sourceSize':[512,512],'outputSize':[512,512],
            'koreanNames':['소닉','테일즈','칩'],'outsideNamesPreserved':True,
            'gameplayVerified':False}
    (OUT.parent/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
