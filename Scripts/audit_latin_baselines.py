"""Audit all shipped subtitle cells and every printable ASCII glyph's geometry."""
from pathlib import Path
from collections import defaultdict,Counter
import json,re,math
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];W=R/'Build/LatinBaseline-Audit'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    expected={(r['archive'],r['fco_file'],r['group_index'],r['cell_index']):r for r in read(W/'cutscene-expected.json')}
    index=read(W/'archive-index.json');font=ImageFont.truetype(str(R/'Tools/Fonts/LINESeedKR-Rg.ttf'),27)
    results=[];mismatches=[];conflicts=[];samples=[];textures={}
    for ar in [x for x in index if x['version']=='v102']:
        folder=Path(ar['folder'])
        for table in read(folder.parent/'font-layouts.json'):
            glyphs={g['id']:g for g in table['glyphs']};letters=defaultdict(set)
            for cell in table['cells']:
                key=(ar['archive'],table['file'],cell['group'],cell['cell']);row=expected.get(key)
                if not row:
                    if cell['ids']:mismatches.append({'key':key,'reason':'unmapped cell'})
                    continue
                text=row['korean'].replace('\r','')
                if len(text)!=len(cell['ids']):mismatches.append({'key':key,'reason':'length mismatch','text':text,'ids':cell['ids']});continue
                for c,gid in zip(text,cell['ids']):letters[gid].add(c)
                if 'Dr.' in text:samples.append((ar,table,cell,text))
            for gid,chars in letters.items():
                if not any(c.isascii() and c.isalnum() for c in chars):continue
                g=glyphs[gid];path=folder/(g['texture']+'.dds')
                if path not in textures:textures[path]=Image.open(path).convert('L')
                box=tuple(map(round,g['rect']));tile=textures[path].crop(box);bounds=tile.point(lambda v:255 if v>=128 else 0).getbbox()
                info={'archive':ar['archive'],'fco':table['file'],'id':gid,'expectedChars':sorted(chars),'rect':box,'inkBounds':bounds}
                if len(chars)>1:conflicts.append(info)
                results.append(info)
    old={x['archive']:x['sha256'] for x in index if x['version']=='v100'}
    dr_archives=sorted({s[0]['archive'] for s in samples})
    atlas=Image.new('RGB',(900,150*len(samples)),(24,24,24));draw=ImageDraw.Draw(atlas)
    label=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    for i,(ar,table,cell,text) in enumerate(samples):
        text=text.replace('\r','');start=text.index('Dr.');glyphs={g['id']:g for g in table['glyphs']};x=16;y=i*150+30
        draw.text((16,i*150+4),ar['archive']+'  '+text.replace('\n',' / '),font=label,fill='white')
        for gid in cell['ids'][start:start+7]:
            g=glyphs[gid];im=textures.get(Path(ar['folder'])/(g['texture']+'.dds'))
            if im is None:im=Image.open(Path(ar['folder'])/(g['texture']+'.dds')).convert('L')
            tile=im.crop(tuple(map(round,g['rect']))).convert('RGB')
            if tile.width and tile.height:atlas.paste(tile.resize((tile.width*3,tile.height*3),Image.Resampling.NEAREST),(x,y))
            x+=tile.width*3
        draw.line((16,y+81,x,y+81),fill='#0080ff',width=1)
    atlas.save(W/'dr-current-all.png')
    metrics=[]
    for c in map(chr,range(33,127)):
        l,t,r,b=font.getbbox(c);old_y=(36-(b-t))/2-t
        metrics.append({'character':c,'inkWidth':r-l,'legacyCellWidth':18,'legacyOriginY':old_y,'commonOriginY':6.5,'baselineErrorPixels':old_y-6.5,'widerThan18':r-l>18})
    report={'catalogLatinOrDigitRows':len(read(W/'latin-rows.json')),'cutsceneArchives':43,'cutsceneCellsMapped':len(expected),'unmappedOrLengthMismatch':mismatches,'latinGlyphRecords':len(results),'caseAliases':conflicts,'drRows':len(samples),'drArchives':dr_archives,'drArchivesByteIdenticalToV100':all(old[x]==next(a['sha256'] for a in index if a['version']=='v102' and a['archive']==x) for x in dr_archives),'asciiMetrics':metrics,'glyphs':results}
    (W/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['asciiMetrics','glyphs','caseAliases','unmappedOrLengthMismatch']}));print('Case aliases',len(conflicts),'unmapped/length',len(mismatches))
if __name__=='__main__':main()
