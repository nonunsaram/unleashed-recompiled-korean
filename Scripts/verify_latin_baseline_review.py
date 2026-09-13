"""Verify shipped fixed font geometry against a true baseline reference."""
from pathlib import Path
from collections import defaultdict
import json,subprocess,sys,math
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];W=R/'Build/LatinBaseline-Audit'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def reference(glyph,width,height,font):
    im=Image.new('L',(width,height));l,t,r,b=font.getbbox(glyph)
    # Independent baseline-anchor rendering: ascent + the shared Hangul origin.
    ht=font.getbbox('가');origin=(height-(ht[3]-ht[1]))/2-ht[1]
    ImageDraw.Draw(im).text(((width-(r-l))/2-l,font.getmetrics()[0]+origin),glyph,font=font,anchor='ls',fill=255)
    return im

def bounds(im):return im.point(lambda v:255 if v>=128 else 0).getbbox()
def main():
    font=ImageFont.truetype(str(R/'Tools/Fonts/LINESeedKR-Rg.ttf'),27);expected={(x['archive'],x['fco_file'],x['group_index'],x['cell_index']):x['korean'].replace('\r','') for x in read(W/'cutscene-expected.json')}
    cases=[];total=0;examples=[]
    for job in read(W/'fix-jobs.json'):
        folder=Path(job['folder'])
        for table in read(W/'FixedLayouts'/(job['archive']+'.json')):
            glyphs={x['id']:x for x in table['glyphs']};mapping=defaultdict(set)
            for cell in table['cells']:
                text=expected.get((job['archive'],table['file'],cell['group'],cell['cell']),'')
                assert len(text)==len(cell['ids'])
                for char,gid in zip(text,cell['ids']):mapping[gid].add(char)
                if cell['ids']:total+=1
                if 'Dr.' in text:examples.append((job,table,cell,text))
            for gid,chars in mapping.items():
                assert len(chars)==1, ('case alias',job['archive'],chars)
                c=next(iter(chars))
                if not (c.isascii() and not c.isspace()):continue
                g=glyphs[gid];im=Image.open(folder/(g['texture']+'.dds')).convert('L').crop(tuple(map(round,g['rect'])));ref=reference(c,im.width,im.height,font)
                a,b=bounds(im),bounds(ref);assert a and b and max(abs(x-y) for x,y in zip(a,b))<=1,(job['archive'],c,a,b)
                assert a[0]>0 and a[2]<im.width,('horizontal clipping',c,a,im.size)
                cases.append({'archive':job['archive'],'glyph':c,'actualBounds':a,'baselineReferenceBounds':b,'width':im.width})
    # Test every printable ASCII glyph, including characters absent from current subtitles.
    widths=read(W/'latin-widths.json');entries=[{'character':'','id':-1,'rect':[0,0,512,512]}]
    for i,n in enumerate(range(33,127)):
        x=(i%12)*40;y=(i//12)*40;entries.append({'character':chr(n),'id':n,'rect':[x,y,x+widths[str(n)],y+36]})
    Image.new('RGBA',(512,512),(0,0,0,255)).save(W/'ascii-input.dds');(W/'ascii-map.json').write_text(json.dumps(entries),encoding='utf8')
    subprocess.run([sys.executable,str(R/'Scripts/patch_subtitle_atlas_baseline.py'),str(W/'ascii-input.dds'),str(W/'ascii-map.json'),str(R/'Tools/Fonts/LINESeedKR-Rg.ttf'),str(W/'ascii-fixed.dds')],check=True)
    image=Image.open(W/'ascii-fixed.dds').convert('L')
    for e in entries[1:]:
        im=image.crop(e['rect']);a=bounds(im);b=bounds(reference(e['character'],im.width,im.height,font));assert a and b and max(abs(x-y) for x,y in zip(a,b))<=1,(e['character'],a,b);assert a[0]>0 and a[2]<im.width
    # Independently check the existing common font used by non-cutscene text.
    common=[];layout=read(R/'Build/PlayableModWork/common-atlas.json')
    for e in layout:
        c=e['character']
        if not(c.isascii() and c.isalnum()):continue
        im=Image.open(R/f"Build/PlayableModWork/fte_Korean_{e['page']:03}.dds").convert('L').crop(e['rect']);a=bounds(im);b=bounds(reference(c,im.width,im.height,font));common.append({'glyph':c,'actual':a,'reference':b,'matches':bool(a and b and abs(a[1]-b[1])<=1 and abs(a[3]-b[3])<=1)})
    assert all(x['matches'] for x in common), common
    out=Image.new('RGB',(900,150*len(examples)),(24,24,24));draw=ImageDraw.Draw(out);label=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    for i,(job,table,cell,text) in enumerate(examples):
        draw.text((16,i*150+4),job['archive']+'  '+text.replace('\n',' / '),font=label,fill='white');glyphs={x['id']:x for x in table['glyphs']};x=16;y=i*150+30
        for gid in cell['ids'][text.index('Dr.'):text.index('Dr.')+7]:
            g=glyphs[gid];im=Image.open(Path(job['folder'])/(g['texture']+'.dds')).convert('RGB').crop(tuple(map(round,g['rect'])))
            if im.width and im.height:out.paste(im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST),(x,y))
            x+=im.width*3
        draw.line((16,y+81,x,y+81),fill='#0080ff')
    out.save(W/'dr-fixed-all.png')
    result={'passed':True,'fixedArchives':16,'serializedSubtitleCells':total,'asciiGlyphInstancesChecked':len(cases),'printableAsciiTested':94,'commonFontLettersAndDigits':len(common),'commonFontBaselineMismatches':[x for x in common if not x['matches']],'drExamples':len(examples),'gameLaunched':False,'releasePackagesModified':False,'cases':cases}
    (W/'fixed-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
if __name__=='__main__':main()
