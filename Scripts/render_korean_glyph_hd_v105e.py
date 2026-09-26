"""Re-render the eight shared Korean font pages at 2x with fixed FTE UVs."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'Build/Review5-ResolutionSplit'
OUT = WORK / 'HdGlyphPages'
BASE = ROOT / 'Build/Review4-FontInspection/Town_China_Common/+Town_China_Common'
FONT = ROOT / 'Tools/Fonts/LINESeedKR-Rg.ttf'
FALLBACK = ROOT / 'Tools/Converse/net8.0/Resources/NotoSansJP-Regular.ttf'
MAP = ROOT / 'Build/PlayableModWork/common-atlas.json'
POL = ROOT / 'Build/TwoNames-v105b/pol-glyph.json'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def draw_pages(layout: list[dict], scale: int) -> tuple[dict[int,Image.Image], list[dict]]:
    pages: dict[int,Image.Image] = {}
    sizes = [27] if scale == 1 else list(range(54, 47, -1))
    faces = {size: ImageFont.truetype(str(FONT), size) for size in sizes}
    fallbacks = {size: ImageFont.truetype(str(FALLBACK), size) for size in sizes}
    checks=[]
    for entry in layout:
        page=int(entry['page'])
        if page not in pages:
            pages[page] = Image.new('RGBA',(512*scale,512*scale),(0,0,0,255))
        glyph=entry['character']
        if glyph==' ': continue
        x0,y0,x1,y1=(int(x)*scale for x in entry['rect'])
        width,height=x1-x0,y1-y0
        cell=Image.new('RGBA',(width,height),(0,0,0,255))
        painter=ImageDraw.Draw(cell)
        font_set=fallbacks if ord(glyph)>127 and not ('\uac00'<=glyph<='\ud7a3') else faces
        for size in sizes:
            active=font_set[size]
            l,t,r,b=painter.textbbox((0,0),glyph,font=active)
            if r-l<=width and b-t<=height: break
        else:
            raise ValueError(f'Glyph clipping: {page} {glyph!r} {entry["rect"]} {scale}')
        _,ht,_,hb=painter.textbbox((0,0),'가',font=active)
        x=(width-(r-l))/2-l
        y=(height-(hb-ht))/2-ht
        y=max(-t,min(y,height-b))

        painter.text((x,y),glyph,font=active,fill=(255,255,255,255))
        pages[page].paste(cell,(x0,y0))
        checks.append({'page':page,'character':glyph,'scale':scale,'fontSize':size,
                       'inkBounds':[x+l,y+t,x+r,y+b],'cellSize':[width,height]})
    return pages,checks


def main() -> None:
    assert MAP.is_file() and POL.is_file() and BASE.is_dir()
    assert not OUT.exists()
    layout=json.loads(MAP.read_text(encoding='utf-8-sig'))
    pol=json.loads(POL.read_text(encoding='utf8'))
    assert pol['character']=='폴' and pol['page']==7 and pol['rect']==[0,0,28,35]
    layout.append({'character':pol['character'],'page':7,'rect':pol['rect']})
    assert len(layout)==1234 and {e['page'] for e in layout}==set(range(8))
    reference,checked1=draw_pages(layout,1)
    assert len(reference)==8
    for index,image in reference.items():
        target=BASE / f'fte_Korean_{index:03}.dds'
        assert target.is_file()
        candidate=WORK / f'fte_Korean_{index:03}-reference.dds'
        image.save(candidate,pixel_format='DXT5')
        assert sha(candidate)==sha(target), f'1x reconstruction differs for page {index}'
    pages,checked2=draw_pages(layout,2)
    OUT.mkdir(parents=True)
    for index,image in pages.items():
        output=OUT / f'fte_Korean_{index:03}.dds'
        image.save(output,pixel_format='DXT5')
        with Image.open(output) as reopened:
            assert reopened.size==(1024,1024)
        if index==0: image.save(OUT / 'fte_Korean_000-preview.png')
    report={'passed':True,'sourcePages':8,'sourceGlyphs':len(layout),
            'sourcePagesByteIdentical':8,'sourceSize':[512,512],
            'hdSize':[1024,1024],'hdPageNames':sorted(p.name for p in OUT.glob('*.dds')),
            'glyphsDrawn1x':len(checked1),'glyphsDrawn2x':len(checked2),
            'uvLayoutPreserved':True,'gameplayVerified':False}
    (WORK / 'glyph-render-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__': main()
