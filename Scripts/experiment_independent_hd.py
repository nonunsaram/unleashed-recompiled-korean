"""Isolated original-game Real-ESRGAN experiment; never installs or packages."""
from pathlib import Path
import argparse, csv, hashlib, io, json, struct, subprocess, time
from collections import defaultdict
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from build_unleashhd_ui_compat_v105 import draw_korean
R=Path(__file__).resolve().parents[1]
W=R/'Build/IndependentHD-Experiment-20261003'
T=R/'Tools/RealESRGAN-v0.2.0'
EXE=T/'runtime/realesrgan-ncnn-vulkan-v0.2.0-windows/realesrgan-ncnn-vulkan.exe'
MODELS=T/'official-model-bundle/models'
DEV=R/'Build/Development-v105p-Playtest/UnleashedKorean'
CSV=R/'publish/unleashed-recompiled-korean/Release/v1.0.5-review16/UnleasHD-permission-texture-list.csv'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
def arc_member(relative,name):
    p=DEV/relative
    for part in sorted(p.parent.glob(p.name.split('.ar.')[0]+'.ar.*')):
        b=part.read_bytes(); off=16
        while off<len(b):
            size,length,start,_,_=struct.unpack_from('<5I',b,off)
            assert size>0 and off+size<=len(b)
            n=b[off+20:b.index(0,off+20,off+start)].decode('utf8')
            if n==name: return b[off+start:off+start+length]
            off+=size
    raise KeyError((relative,name))
def prepare():
    assert not (W/'manifest.json').exists(),'Experiment already prepared'
    for d in ['inputs','originals','references-only','logs','inference','candidates','comparisons']:(W/d).mkdir(parents=True,exist_ok=True)
    rows=json.loads((R/'Translation/review/remaining-ui/texture-comparison.json').read_text(encoding='utf8'))
    permissions=list(csv.DictReader(CSV.open(encoding='utf-8-sig')))
    jobs=[]
    for i in [0,10,11,16,17,18,19,21,23,25,26,28,29,31,32]:
        row=rows[i]; src=Path(row['english'])
        archive=next(a.split('/',1)[1] for a in row['archives'] if a.startswith('BaseGame/'))
        ref=next(p for p in permissions if p['file']==row['file'] and '/+'+archive+'.ar.' in p['archive'])
        jobs.append(dict(id=f'{i:02d}',index=i,source=str(src),file=row['file'],archive=ref['archive'],target=json.loads(ref['size']),category='UI'))
    src=R/'Analysis/Full-Text-Extraction/Audit/ArchiveInventory/scratch-0561/Town_Common/mat_talk_comon_002.dds'
    ref=next(p for p in permissions if p['file']==src.name)
    jobs.append(dict(id='nameplate',index=None,source=str(src),file=src.name,archive=ref['archive'],target=[512,512],category='nameplate'))
    for name in ['mat_title_001.dds','mat_title_004.dds']:
        src=R/'Build/TitleLogo-v102/Originals/Core/Title'/name
        im=Image.open(src)
        jobs.append(dict(id=name[:-4],index=None,source=str(src),file=name,archive=None,target=[im.width*3,im.height*3],category='title-source-test'))
    for j in jobs:
        src=Path(j['source']); assert 'UnleasHD' not in str(src) and src.is_file()
        im=Image.open(src).convert('RGBA'); j['source_size']=list(im.size);j['source_sha256']=sha(src)
        im.save(W/'originals'/(j['id']+'.png'))
        # RGB input only. Alpha uses deterministic bicubic resampling, never neural reconstruction.
        rgb=np.array(im)[:,:,:3].copy(); a=np.array(im)[:,:,3]; valid=a>0
        # Bleed colors at most eight texels into transparent margins to reduce dark fringes.
        for _ in range(8):
            total=np.zeros(rgb.shape,dtype=np.uint32); count=np.zeros(a.shape,dtype=np.uint16)
            for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:
                v=np.roll(valid,(dy,dx),(0,1)); c=np.roll(rgb,(dy,dx),(0,1))
                if dy==1:v[0]=False
                if dy==-1:v[-1]=False
                if dx==1:v[:,0]=False
                if dx==-1:v[:,-1]=False
                total+=c.astype(np.uint32)*v[:,:,None];count+=v
            fill=(~valid)&(count>0);rgb[fill]=(total[fill]/count[fill,None]).astype('uint8');valid|=fill
        Image.fromarray(rgb).save(W/'inputs'/(j['id']+'.png'))
        j['input_sha256']=sha(W/'inputs'/(j['id']+'.png'))
        if j['archive']:
            b=arc_member(j['archive'],j['file']);p=W/'references-only'/(j['id']+'.png')
            Image.open(io.BytesIO(b)).save(p);j['reference_sha256']=hashlib.sha256(b).hexdigest()
    protected={str(p.relative_to(R)):sha(p) for p in DEV.rglob('*') if p.is_file()}
    for p in [CSV,R/'Scripts/release_guard_data.py']:protected[str(p.relative_to(R))]=sha(p)
    dump(W/'protected-before.json',protected)
    dump(W/'manifest.json',jobs)
    dump(W/'tool-provenance.json',{'runtime_url':'https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan/releases/tag/v0.2.0','model_bundle_url':'https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.5.0','runtime_sha256':sha(EXE),'models':{p.name:sha(p) for p in MODELS.iterdir() if p.is_file()},'alpha':'Bicubic from original','references_used_for_inference':False})
    print(f'Prepared {len(jobs)} original inputs; {len(protected)} protected files',flush=True)
def infer(model,ids):
    jobs=json.loads((W/'manifest.json').read_text(encoding='utf8'));out=W/'inference'/model;out.mkdir(exist_ok=True)
    for j in jobs:
        if ids and j['id'] not in ids:continue
        dest=out/(j['id']+'.png')
        if dest.exists():continue
        args=[str(EXE),'-i',str(W/'inputs'/(j['id']+'.png')),'-o',str(dest),'-m',str(MODELS),'-n',model,'-s','4','-t','256','-j','1:1:1','-f','png']
        start=time.monotonic()
        with (W/'logs'/(model+'-'+j['id']+'.log')).open('w',encoding='utf8') as log:
            subprocess.run(args,stdout=log,stderr=log,check=True,timeout=600,creationflags=subprocess.CREATE_NO_WINDOW)
        im=Image.open(dest);assert im.size==tuple(v*4 for v in j['source_size'])
        print(f'{model} {j["id"]}: {time.monotonic()-start:.1f}s {im.size}',flush=True)
def finalize(model):
    jobs=json.loads((W/'manifest.json').read_text(encoding='utf8'))
    labels=json.loads((R/'Translation/review/unleashhd-v105/ui-textures-ko-v104-full.json').read_text(encoding='utf8'))['labels']
    # World map's current reviewed labels are in the current typography manifest.
    current=json.loads((R/'Translation/ui-textures-ko.json').read_text(encoding='utf8'))['labels']
    by=defaultdict(list)
    for l in labels:
        if l['texture']<30:by[l['texture']].append(l)
    for l in current:
        if l['texture'] in (31,32):
            l=dict(l); l['box']=[v/2 for v in l['box']]
            for key in ['size','anchor_x','top']:l[key]/=2
            by[l['texture']].append(l)
    def base(j):
        ori=Image.open(W/'originals'/(j['id']+'.png')).convert('RGBA')
        result=Image.open(W/'inference'/model/(j['id']+'.png')).convert('RGB').resize(j['target'],Image.Resampling.LANCZOS).convert('RGBA')
        result.putalpha(ori.getchannel('A').resize(j['target'],Image.Resampling.BICUBIC));return result
    panel=base(next(j for j in jobs if j['id']=='19'))
    report=[]
    font=ImageFont.truetype(str(R/'Tools/Fonts/LINESeedKR-Rg.ttf'),19)
    for j in jobs:
        if not (W/'inference'/model/(j['id']+'.png')).exists():continue
        im=base(j);factor=j['target'][0]/j['source_size'][0];count=0
        if j['category']=='UI':
            assert by[j['index']],j
            im,count=draw_korean(im,by[j['index']],j['index'],panel,factor)
        elif j['category']=='nameplate':
            f=ImageFont.truetype(str(R/'Tools/Fonts/LINESeedKR-Rg.ttf'),216)
            for y,text,dx,dy in [(0,'소닉',0,0),(64,'테일즈',0,0),(128,'칩',-4,-3)]:
                im.paste((0,0,0,0),(0,y,192,y+64));layer=Image.new('RGBA',(768,256));d=ImageDraw.Draw(layer);l,t,r,b=d.textbbox((0,0),text,font=f)
                d.text(((768-r+l)/2-l+dx*4,(256-b+t)/2-t+dy*4),text,font=f,fill='white');im.alpha_composite(layer.resize((192,64),Image.Resampling.LANCZOS),(0,y))
            count=3
        dst=W/'candidates'/j['id'];dst.mkdir(exist_ok=True)
        im.save(dst/'preview.png');im.save(dst/j['file'])
        assert Image.open(dst/j['file']).convert('RGBA').tobytes()==im.tobytes()
        original=Image.open(W/'originals'/(j['id']+'.png')).resize(im.size,Image.Resampling.LANCZOS)
        panels=[('원본 일반 확대',original),('자체 Real-ESRGAN + 한글',im)]
        if j['archive']:panels.append(('기존 UnleasHD 기반 / 비교 전용',Image.open(W/'references-only'/(j['id']+'.png'))))
        tw,th=460,560; sheet=Image.new('RGB',(tw*len(panels),th+70),'#20242c');d=ImageDraw.Draw(sheet)
        for n,(label,pic) in enumerate(panels):
            d.text((n*tw+12,10),label,font=font,fill='white');pic=pic.convert('RGBA');pic.thumbnail((tw-24,th-10),Image.Resampling.LANCZOS)
            sheet.paste(pic,(n*tw+12,55),pic)
        sheet.save(W/'comparisons'/(j['id']+'.png'))
        report.append({**j,'labels':count,'output_sha256':sha(dst/j['file']),'dds_roundtrip':True,'model':model,'status':'source-only; Korean composition pending' if j['category']=='title-source-test' else 'candidate; game test pending'})
    before=json.loads((W/'protected-before.json').read_text(encoding='utf8'));assert all(sha(R/p)==v for p,v in before.items())
    dump(W/'verification.json',{'outputs':report,'protected_files_unchanged':len(before),'gameplay_verified':False,'installed':False,'packaged':False,'hd_reference_used_as_input':False})
    print(f'Validated {len(report)} outputs; protected {len(before)} files unchanged',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','infer','finalize']);p.add_argument('--model',default='realesrgan-x4plus');p.add_argument('--ids',nargs='*');a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='infer':infer(a.model,a.ids)
    else:finalize(a.model)
