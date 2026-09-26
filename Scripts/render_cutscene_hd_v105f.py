"""Re-render verified Korean cutscene glyphs at 2x, keeping unmatched source art."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from probe_tails_atlas_v105d import render_one

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'Build/Review6-ResolutionSplit'
MAP=WORK/'cutscene-atlas-maps.json'
SOURCE=ROOT/'Build/FinalAudit-v104/Archives/Inspire/subtitle/English'
DEST=WORK/'HdCutscenePages'
FONT=ROOT/'Tools/Fonts/LINESeedKR-Rg.ttf'
THRESHOLD=.95


def iou(original:Image.Image,recreated:Image.Image,box:tuple[int,int,int,int])->float:
    a=np.asarray(original.crop(box).convert('L'))>127
    b=np.asarray(recreated.crop(box).convert('L'))>127
    union=np.logical_or(a,b).sum()
    return float(np.logical_and(a,b).sum()/union) if union else 1.0


def draw_hd(canvas:Image.Image,entry:dict,fonts:dict[int,ImageFont.FreeTypeFont])->int:
    glyph=entry['character']
    x0,y0,x1,y1=(int(x)*2 for x in entry['rect'])
    width,height=x1-x0,y1-y0
    for size in sorted(fonts,reverse=True):
        font=fonts[size]
        draw=ImageDraw.Draw(canvas)
        l,t,r,b=draw.textbbox((0,0),glyph,font=font)
        offset={',':8,'.':8,'~':3,'\u2026':2}.get(glyph,0)*2
        if r-l<=width and b-t+offset<=height:break
    else:
        raise ValueError(f'Glyph cannot fit its scaled UV cell: {glyph!r} {entry["rect"]}')
    cell=Image.new('RGBA',(width,height),(0,0,0,255))
    painter=ImageDraw.Draw(cell)
    _,ht,_,hb=painter.textbbox((0,0),'가',font=font)
    x=(width-(r-l))/2-l
    ink_height=(hb-ht) if '\uac00'<=glyph<='\ud7a3' else (b-t)
    ink_top=ht if '\uac00'<=glyph<='\ud7a3' else t
    y=(height-ink_height)/2-ink_top+offset
    y=max(-t,min(y,height-b))
    painter.text((x,y),glyph,font=font,fill=(255,255,255,255))
    canvas.paste(cell,(x0,y0))
    return size


def main()->None:
    pages=json.loads(MAP.read_text(encoding='utf-8-sig'))
    assert len(pages)==44 and not DEST.exists()
    fonts={size:ImageFont.truetype(str(FONT),size) for size in range(48,55)}
    results=[]
    for page in pages:
        source=SOURCE/('+'+page['archive'])/('+'+page['archive'])/page['texture']
        original=Image.open(source).convert('RGBA')
        assert original.size==(512,512)
        recreated=render_one(original,page['entries'],1)
        high=original.resize((1024,1024),Image.Resampling.LANCZOS)
        drawn=0;retained=0;hangul=0;sizes=[]
        for entry in page['entries']:
            glyph=entry['character']
            if glyph==' ':continue
            score=iou(original,recreated,tuple(entry['rect']))
            if score<THRESHOLD:
                assert not ('\uac00'<=glyph<='\ud7a3'),(page['archive'],glyph,score)
                retained+=1
                continue
            sizes.append(draw_hd(high,entry,fonts));drawn+=1
            if '\uac00'<=glyph<='\ud7a3':hangul+=1
        target=DEST/page['archive']/page['texture']
        target.parent.mkdir(parents=True,exist_ok=True)
        high.save(target,pixel_format='DXT5')
        with Image.open(target) as result:assert result.size==(1024,1024)
        results.append({'archive':page['archive'],'texture':page['texture'],
                        'redrawnGlyphs':drawn,'redrawnHangul':hangul,
                        'sourceGlyphsRetained':retained,'smallestFontSize':min(sizes) if sizes else None})
    report={'passed':True,'pages':len(results),
            'redrawnGlyphs':sum(r['redrawnGlyphs'] for r in results),
            'redrawnHangul':sum(r['redrawnHangul'] for r in results),
            'sourceGlyphsRetained':sum(r['sourceGlyphsRetained'] for r in results),
            'outputSize':[1024,1024],'minimumSourceIoUToRedraw':THRESHOLD,
            'pagesDetail':results,'gameplayVerified':False}
    (WORK/'cutscene-hd-render-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='pagesDetail'},ensure_ascii=False))


if __name__=='__main__':main()
