"""Replace only upscaled Latin/punctuation DXT5 blocks in HD cutscene pages."""
from __future__ import annotations
import json,hashlib,sys
from pathlib import Path
from PIL import Image,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent))
from probe_tails_atlas_v105d import render_one
from render_cutscene_hd_v105f import draw_hd,iou

ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/'Build/Review6-ResolutionSplit/cutscene-atlas-maps.json'
SOURCE=ROOT/'Build/FinalAudit-v104/Archives/Inspire/subtitle/English'
OLD=ROOT/'Build/Review6-ResolutionSplit/HdCutscenePages'
OUT=ROOT/'Build/Review12-Feedback/HdCutsceneLatinPages'

def splice(old:bytes,new:bytes,entries:list[dict])->bytes:
    assert len(old)==len(new)==1048704 and old[84:88]==new[84:88]==b'DXT5'
    changed=set()
    for entry in entries:
        x0,y0,x1,y1=(int(v)*2 for v in entry['rect'])
        for by in range(y0//4,(y1+3)//4):
            for bx in range(x0//4,(x1+3)//4):changed.add((bx,by))
    output=bytearray(old)
    for bx,by in changed:
        off=128+(by*256+bx)*16
        output[off:off+16]=new[off:off+16]
    assert all(output[off:off+16]==old[off:off+16]
        for by in range(256) for bx in range(256) if (bx,by) not in changed
        for off in [128+(by*256+bx)*16])
    return bytes(output)

def main():
    assert not OUT.exists()
    fonts={size:ImageFont.truetype(str(ROOT/'Tools/Fonts/LINESeedKR-Rg.ttf'),size) for size in range(48,55)}
    pages=json.loads(MAP.read_text(encoding='utf8'))
    records=[]
    for page in pages:
        path=SOURCE/('+'+page['archive'])/('+'+page['archive'])/page['texture']
        original=Image.open(path).convert('RGBA')
        recreated=render_one(original,page['entries'],1)
        retained=[e for e in page['entries'] if e['character']!=' ' and iou(original,recreated,tuple(e['rect']))<.95]
        if not retained:continue
        old=OLD/page['archive']/page['texture']
        high=Image.open(old).convert('RGBA')
        for entry in retained:draw_hd(high,entry,fonts)
        target=OUT/page['archive']/page['texture']
        target.parent.mkdir(parents=True,exist_ok=True)
        candidate=target.with_suffix('.temp.dds')
        high.save(candidate,pixel_format='DXT5')
        final=splice(old.read_bytes(),candidate.read_bytes(),retained)
        candidate.unlink()
        target.write_bytes(final)
        assert Image.open(target).size==(1024,1024)
        records.append({'archive':page['archive'],'texture':page['texture'],
                        'redrawn':len(retained),'characters':''.join(e['character'] for e in retained),
                        'oldSha256':hashlib.sha256(old.read_bytes()).hexdigest(),
                        'newSha256':hashlib.sha256(final).hexdigest()})
    assert sum(x['redrawn'] for x in records)==103
    report={'passed':True,'redrawnGlyphs':103,'pagesChanged':len(records),
            'unchangedDxt5BlocksPreserved':True,'files':records,'gameplayVerified':False}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    (OUT.parent/'cutscene-latin-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'passed':True,'glyphs':103,'pages':len(records)},ensure_ascii=False))
if __name__=='__main__':main()
