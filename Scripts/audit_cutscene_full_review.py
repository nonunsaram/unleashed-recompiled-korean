"""Render and audit all actual subtitle cells; not a game renderer emulator."""
from pathlib import Path
from collections import defaultdict,Counter
import json,re,math,html,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];W=R/'Build/CutsceneFullReview-20260914'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def main():
    expected={(x['archive'],x['fco_file'],x['group_index'],x['cell_index']):x for x in read(R/'Build/LatinBaseline-Audit/cutscene-expected.json')}
    tables=read(W/'layouts.json');gallery=read(W/'gallery.json');app=R/'Analysis/Full-Text-Extraction/Audit/ArchiveInventory/scratch-0027/#Application'
    gallery_by_archive=defaultdict(list)
    for e in gallery:
        p=app/(e['sequence']+'.seq.xml');scenes=[]
        if p.exists():scenes=sorted({n.text for n in ET.parse(p).findall('.//SceneName') if n.text})
        canonical='evrt_'+e['sequence'].removeprefix('PlayMovie_').lower()
        if canonical not in scenes:scenes.append(canonical)
        e['archives']=scenes
        for name in scenes:gallery_by_archive[name].append(e)
    font=ImageFont.truetype(str(R/'Tools/Fonts/LINESeedKR-Rg.ttf'),27)
    cache={};issues=[];glyphchecks=[];sentences=[];xmlrefs={};seen=set();empty=0
    (W/'sentences').mkdir(exist_ok=True)
    def texture(path):
        if path not in cache:cache[path]=Image.open(path).convert('L')
        return cache[path]
    def reference(c,size,fixed):
        im=Image.new('L',size);d=ImageDraw.Draw(im);l,t,r,b=font.getbbox(c);_,ht,_,hb=font.getbbox('가')
        x=(size[0]-(r-l))/2-l
        if '가'<=c<='힣' or (fixed and c.isascii()):y=(size[1]-(hb-ht))/2-ht
        else:y=(size[1]-(b-t))/2-t
        if not(fixed and c.isascii()):y+=8 if c in ',.' else 3 if c=='~' else 2 if c=='…' else 0
        d.text((x,y),c,font=font,fill=255)
        return im,(x+l,y+t,x+r,y+b)
    for table in tables:
        a=table['archive'];folder=Path(table['folder']);glyphs={g['id']:g for g in table['glyphs']};mapping=defaultdict(set)
        for cell in table['cells']:
            key=(a,table['file'],cell['group'],cell['cell']);row=expected.get(key);text=row['korean'].replace('\r','') if row else ''
            if row:seen.add(key)
            if not cell['ids']:
                empty+=1
                if text:issues.append({'kind':'unexpected_empty_message','key':key})
                continue
            if not row or len(text)!=len(cell['ids']):issues.append({'kind':'message_mapping','key':key});continue
            if cell['highlights'] or cell['subCells']:issues.append({'kind':'extra_text_ranges','key':key})
            for c,gid in zip(text,cell['ids']):mapping[gid].add(c)
            lineimages=[];line=[]
            for c,gid in zip(text,cell['ids']):
                if c=='\n':lineimages.append(line);line=[];continue
                g=glyphs.get(gid)
                if g is None:issues.append({'kind':'missing_glyph_id','key':key,'id':gid});continue
                rect=tuple(map(round,g['rect']));size=(rect[2]-rect[0],rect[3]-rect[1])
                tile=Image.new('L',(size[0],36)) if c==' ' else texture(folder/(g['texture']+'.dds')).crop(rect)
                line.append(tile)
            lineimages.append(line)
            widths=[sum(t.width for t in line) for line in lineimages];height=42*len(lineimages)
            preview=Image.new('RGB',(max(1,max(widths)),height),(12,16,22))
            for ln,line in enumerate(lineimages):
                x=(preview.width-widths[ln])//2
                for tile in line:
                    preview.paste(Image.new('RGB',tile.size,(250,250,250)),(x,ln*42),tile);x+=tile.width
            uid=f"{a}__{Path(table['file']).stem}__{cell['group']}_{cell['cell']}";preview.save(W/'sentences'/(uid+'.png'))
            sentences.append({'id':uid,'archive':a,'fco':table['file'],'group':cell['group'],'cell':cell['cell'],'text':text,'hasLatinOrDigit':bool(re.search('[A-Za-z0-9]',text)),'lineWidths':widths,'maxLineWidth':max(widths),'lines':len(lineimages),'alignment':cell['alignment'],'gallery':[{'position':e['position'],'title':e['title']} for e in gallery_by_archive[Path(table['file']).stem.removesuffix('_event')]],'preview':'sentences/'+uid+'.png'})
        for gid,chars in mapping.items():
            if len(chars)!=1:issues.append({'kind':'glyph_alias','archive':a,'id':gid,'chars':sorted(chars)});continue
            c=next(iter(chars))
            if c in ' \n':continue
            g=glyphs[gid];rect=tuple(map(round,g['rect']));im=texture(folder/(g['texture']+'.dds'))
            if not(0<=rect[0]<rect[2]<=im.width and 0<=rect[1]<rect[3]<=im.height):issues.append({'kind':'atlas_bounds','archive':a,'glyph':c});continue
            tile=im.crop(rect);ref,ink=reference(c,tile.size,table['fixed']);aa=np.array(tile)>=128;bb=np.array(ref)>=128;intersection=np.logical_and(aa,bb).sum();union=np.logical_or(aa,bb).sum();iou=float(intersection/union) if union else 0
            box=tile.point(lambda v:255 if v>=128 else 0).getbbox();outside=ink[0]<0 or ink[1]<0 or ink[2]>tile.width or ink[3]>tile.height
            gcheck={'archive':a,'file':table['file'],'id':gid,'glyph':c,'iou':round(iou,5),'inkBounds':box,'cellSize':tile.size,'referenceOutsideCell':outside}
            glyphchecks.append(gcheck)
            if not box or iou<.94 or outside:issues.append({'kind':'glyph_pixels',**gcheck})
        for p in folder.glob('*.inspire_resource.xml'):
            root=ET.parse(p).getroot();resources={x.findtext('ID'):x for x in root.findall('.//ResourceInfo/Resource')}
            for trig in root.findall('.//TriggerInfo/Trigger'):
                res=resources.get(trig.findtext('ResourceID'))
                if res is None or res.findtext('Type')!='ConverseData':continue
                par=res.find('Param');k=(a,par.findtext('FileName')+'.fco',int(par.findtext('GroupID')),int(par.findtext('CellID')))
                if k not in expected:continue
                start=trig.findtext('Frame/Start');end=trig.findtext('Frame/End')
                info={'startFrame':float(start) if start else None,'endFrame':float(end) if end else None,'position':par.findtext('Position')}
                if info not in xmlrefs.setdefault(k,[]):xmlrefs[k].append(info)
    for s in sentences:s['sceneReferences']=xmlrefs.get((s['archive'],s['fco'],s['group'],s['cell']),[])
    missing=set(expected)-seen
    if missing:issues.append({'kind':'unseen_catalog_rows','keys':sorted(missing)})
    english=[s for s in sentences if s['hasLatinOrDigit']]
    write(W/'sentences.json',sentences);write(W/'glyph-checks.json',glyphchecks);write(W/'gallery.json',gallery)
    report={'archives':len({t['archive'] for t in tables}),'tables':len(tables),'catalogPhysicalRows':len(expected),'renderedSentences':len(sentences),'emptyCells':empty,'glyphInstancesChecked':len(glyphchecks),'englishSentences':len(english),'englishArchives':len({s['archive'] for s in english}),'issues':issues,'maxLineWidth':max(s['maxLineWidth'] for s in sentences),'lineCountDistribution':dict(Counter(s['lines'] for s in sentences)),'alignmentDistribution':dict(Counter(s['alignment'] for s in sentences)),'sentencesWithoutXmlReference':sum(not s['sceneReferences'] for s in sentences),'gameRendererEmulated':False,'gameLaunched':False}
    write(W/'audit.json',report)
    label=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
    english.sort(key=lambda s:((s['gallery'][0]['position'] if s['gallery'] else 999),s['cell']))
    for page in range(math.ceil(len(english)/6)):
        batch=english[page*6:(page+1)*6];sheet=Image.new('RGB',(1200,200*len(batch)),(25,29,36));d=ImageDraw.Draw(sheet)
        for j,s in enumerate(batch):
            y=j*200;g=s['gallery'][0] if s['gallery'] else {'position':'-','title':s['archive']}
            d.text((15,y+4),f"{g['position']} | {g['title']} | cell {s['cell']} | widths {s['lineWidths']}",font=label,fill='#8ed5ff')
            d.text((15,y+29),s['text'].replace('\n',' / '),font=label,fill='white')
            sheet.paste(Image.open(W/s['preview']),(15,y+62))
        sheet.save(W/f'english-contact-{page+1}.png')
    cards=[]
    for s in sorted(sentences,key=lambda s:((s['gallery'][0]['position'] if s['gallery'] else 999),s['archive'],s['fco'],s['group'],s['cell'])):
        title=' / '.join(f"{g['position']}. {g['title']}" for g in s['gallery']) or s['archive'];esc=html.escape
        cards.append(f"<article data-latin='{int(s['hasLatinOrDigit'])}'><h3>{esc(title)} · {s['cell']}</h3><p>{esc(s['text']).replace(chr(10),'<br>')}</p><img loading='lazy' src='{s['preview']}'><small>원본 글자 칸 기준 폭 {s['lineWidths']} / {esc(s['archive'])}</small></article>")
    page='''<!doctype html><meta charset="utf-8"><title>컷신 전체 자막 검수</title><style>body{background:#151a22;color:#edf2fa;font:17px sans-serif;margin:32px;max-width:1300px}article{padding:16px;margin:16px 0;border:1px solid #506079;border-radius:8px}img{display:block;max-width:100%;height:auto}small{color:#a9c5d9}input,button{font:inherit;padding:8px}p{line-height:1.5}</style><h1>컷신 전체 자막 검수</h1><p>실제 DDS 글자와 FTE 칸 폭으로 조합한 비교 그림입니다. 게임의 화면 크기·자간·위치·연출은 재현하지 않습니다.</p><input id="search" placeholder="제목 또는 대사 검색"><label><input id="latin" type="checkbox">영문·숫자 포함만</label>'''+''.join(cards)+'''<script>function filter(){let q=document.querySelector('#search').value.toLowerCase(),l=document.querySelector('#latin').checked;document.querySelectorAll('article').forEach(e=>e.hidden=!e.innerText.toLowerCase().includes(q)||(l&&e.dataset.latin!='1'))}document.querySelector('#search').oninput=filter;document.querySelector('#latin').onchange=filter</script>'''
    (W/'index.html').write_text(page,encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='issues'}));print('Issues:',len(issues));print(json.dumps(issues[:15],ensure_ascii=True))
if __name__=='__main__':main()

