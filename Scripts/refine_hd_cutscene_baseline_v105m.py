"""Align every HD cutscene ASCII glyph to the verified shared Hangul baseline."""
from __future__ import annotations
import hashlib,json
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/'Build/Review6-ResolutionSplit/cutscene-atlas-maps.json'
BASE=ROOT/'Build/Review6-ResolutionSplit/HdCutscenePages'
REVIEW12=ROOT/'Build/Review12-Feedback/HdCutsceneLatinPages'
OUT=ROOT/'Build/Review13-Feedback/HdCutsceneAsciiPages'
FONT=ROOT/'Tools/Fonts/LINESeedKR-Rg.ttf'

def sha(blob:bytes)->str:return hashlib.sha256(blob).hexdigest()

def draw_ascii(canvas:Image.Image,entry:dict,font:ImageFont.FreeTypeFont)->tuple[int,int,int,int]:
    glyph=entry['character']
    assert glyph.isascii() and glyph!=' '
    x0,y0,x1,y1=(int(v)*2 for v in entry['rect'])
    width,height=x1-x0,y1-y0
    cell=Image.new('RGBA',(width,height),(0,0,0,255))
    painter=ImageDraw.Draw(cell)
    l,t,r,b=painter.textbbox((0,0),glyph,font=font)
    _,ht,_,hb=painter.textbbox((0,0),'가',font=font)
    x=(width-(r-l))/2-l
    y=(height-(hb-ht))/2-ht
    assert x+l>=0 and x+r<=width and y+t>=0 and y+b<=height,(glyph,entry['rect'])
    painter.text((x,y),glyph,font=font,fill=(255,255,255,255))
    canvas.paste(cell,(x0,y0))
    return (round(x+l),round(y+t),round(x+r),round(y+b))

def splice(old:bytes,new:bytes,entries:list[dict])->bytes:
    assert len(old)==len(new)==1048704 and old[84:88]==new[84:88]==b'DXT5'
    blocks=set()
    for entry in entries:
        x0,y0,x1,y1=(int(v)*2 for v in entry['rect'])
        for by in range(y0//4,(y1+3)//4):
            for bx in range(x0//4,(x1+3)//4):blocks.add((bx,by))
    out=bytearray(old)
    for bx,by in blocks:
        at=128+(by*256+bx)*16
        out[at:at+16]=new[at:at+16]
    assert all(out[at:at+16]==old[at:at+16]
               for by in range(256) for bx in range(256) if (bx,by) not in blocks
               for at in [128+(by*256+bx)*16])
    return bytes(out)

def main():
    assert not OUT.exists()
    font=ImageFont.truetype(str(FONT),54)
    pages=json.loads(MAP.read_text(encoding='utf8'))
    results=[];counts=Counter()
    for page in pages:
        entries=[e for e in page['entries'] if e['character'].isascii() and e['character']!=' ']
        if not entries:continue
        source=REVIEW12/page['archive']/page['texture']
        if not source.is_file():source=BASE/page['archive']/page['texture']
        high=Image.open(source).convert('RGBA')
        assert high.size==(1024,1024)
        expected={}
        for e in entries:
            draw_ascii(high,e,font)
            box=tuple(v*2 for v in e['rect'])
            expected[e['character'],tuple(e['rect'])]=high.crop(box).convert('L').point(lambda v:255 if v>=128 else 0).getbbox()
            counts[e['character']]+=1
        target=OUT/page['archive']/page['texture']
        target.parent.mkdir(parents=True,exist_ok=True)
        candidate=target.with_suffix('.temp.dds')
        high.save(candidate,pixel_format='DXT5')
        data=splice(source.read_bytes(),candidate.read_bytes(),entries)
        candidate.unlink()
        target.write_bytes(data)
        decoded=Image.open(target).convert('L')
        for e in entries:
            box=tuple(v*2 for v in e['rect'])
            actual=decoded.crop(box).point(lambda v:255 if v>=128 else 0).getbbox()
            reference=expected[e['character'],tuple(e['rect'])]
            assert actual is not None,(page['archive'],e['character'])
            assert max(abs(a-b) for a,b in zip(actual,reference))<=2,(page['archive'],e['character'],actual,reference)
        results.append({'archive':page['archive'],'texture':page['texture'],
                        'glyphs':len(entries),'characters':''.join(e['character'] for e in entries),
                        'sourceSha256':sha(source.read_bytes()),'outputSha256':sha(data)})
    assert sum(x['glyphs'] for x in results)==178 and len(results)==43
    assert counts['E']>=1 and counts['D']>=1 and counts['r']>=1
    for mark in '.,!?\'':assert counts[mark]>0,(mark,counts)
    report={'passed':True,'asciiGlyphsAligned':sum(counts.values()),'pagesChanged':len(results),
            'fontSize':54,'sharedHangulBaseline':True,'punctuationCounts':{x:counts[x] for x in '.,!?\''},
            'allGlyphsFitUvCells':True,'unchangedDxt5BlocksPreserved':True,
            'files':results,'gameplayVerified':False}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    (OUT.parent/'cutscene-ascii-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False))
if __name__=='__main__':main()
