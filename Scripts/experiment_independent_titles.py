"""Compose independent title candidates using original upscales and user-owned captions."""
from pathlib import Path
import json, struct
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from experiment_independent_hd import R,W,arc_member,sha,dump
from probe_animated_ui import parse

def main(model="realesrgan-x4plus", reference_comparisons=True):
    hd=Image.open(W/'candidates/mat_title_001/preview.png').convert('RGBA')
    halo_base=Image.open(W/'candidates/mat_title_004/preview.png').convert('RGBA')
    assert hd.size==(3072,1536) and halo_base.size==(1920,1920)
    scene_path=W/'candidates/title-Korean/ui_title.yncp';scene_path.parent.mkdir(exist_ok=True)
    scene_path.write_bytes(arc_member('TitleLogos/Korean/+Title.ar.00','ui_title.yncp'))
    title=next(s for s in parse(scene_path) if s['name']=='/title_1');cast={c['name']:c for c in title['casts']}
    scene=scene_path.read_bytes()
    atlas=Image.new('RGBA',(3072,3072));atlas.paste(hd,(0,0))
    word=hd.crop((12,405,1524,621));atlas.paste(word,(0,1536))
    caption_path=R/'Build/TitleLogo-Reworked/KoreanLogo-clean.png'
    korean=Image.open(caption_path).convert('RGBA');korean=korean.crop(korean.getbbox());korean.thumbnail((546,153),Image.Resampling.LANCZOS)
    xy=((1512-korean.width)//2,1755);atlas.alpha_composite(korean,xy)
    pos=lambda c:struct.unpack_from('>2f',scene,c['offset']+104)
    parent=pos(cast['position']);wordpos=pos(cast['txt_unleashed']);hc=cast['Cast_1820'];hp=pos(hc)
    corners=cast['txt_unleashed']['corners'];hcorners=hc['corners']
    wordleft=parent[0]+wordpos[0]+corners[0]*1280;wordtop=parent[1]+wordpos[1]+corners[1]*720
    haloleft=hp[0]+hcorners[0]*1280;halotop=hp[1]+hcorners[1]*720
    hb=[round(v*1920) for v in hc['subimage'][1:]]
    kxy=(round((wordleft+xy[0]/3-haloleft)*3+hb[0]),round((wordtop+xy[1]/3-512-halotop)*3+hb[1]))
    mask=Image.new('L',halo_base.size);mask.paste(korean.getchannel('A'),kxy)
    glow=mask.filter(ImageFilter.MaxFilter(19)).filter(ImageFilter.GaussianBlur(6.75)).point(lambda x:round(min(255,round(x*1.3))*.92))
    halo=Image.merge('RGBA',tuple(ImageChops.lighter(halo_base.getchannel(c),glow) for c in 'RGB')+(halo_base.getchannel('A'),))
    custom=hd.copy();kana=(90,786,1302,867)
    custom_path=R/'Assets/TitleLogo/CustomLogo.png';text=Image.open(custom_path).convert('RGBA');ink=text.getchannel('A').getbbox()
    assert ink==(97,3,307,24)
    tile=Image.new('RGBA',(1212,81));tile.paste(text.crop(ink).resize((630,63),Image.Resampling.LANCZOS),(51,9));custom.paste(tile,kana)
    body=Image.new('L',halo_base.size)
    for box,size,xy in [((0,3,1536,402),(1305,339),(30,114)),((2250,303,3072,1122),(699,696),(945,33))]:
        part=hd.crop(box).getchannel('A').resize(size,Image.Resampling.LANCZOS);layer=Image.new('L',halo_base.size);layer.paste(part,xy);body=ImageChops.lighter(body,layer)
    body=body.filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.GaussianBlur(6))
    mask=Image.new('L',halo_base.size);mask.paste(tile.getchannel('A').resize((1029,69),Image.Resampling.LANCZOS),(63,33))
    caption_light=mask.filter(ImageFilter.MaxFilter(19)).filter(ImageFilter.GaussianBlur(6.75)).point(lambda v:min(255,round(v*1.3)))
    light=ImageChops.lighter(body,caption_light);orig=np.array(halo_base);result=orig.copy();ys,xs=np.mgrid[:216,:1260]
    blend=np.minimum(1.,(216-ys)/60)*np.minimum(1.,(1260-xs)/108)
    for c in range(3):result[:216,:1260,c]=np.rint(np.array(light)[:216,:1260]*blend+orig[:216,:1260,c]*(1-blend)).astype('uint8')
    variants={'Korean':(atlas,halo),'Custom':(custom,Image.fromarray(result))};report=[]
    font=ImageFont.truetype(str(R/'Tools/Fonts/LINESeedKR-Rg.ttf'),20)
    for name,images in variants.items():
        dest=W/'candidates'/('title-'+name);dest.mkdir(exist_ok=True)
        (dest/'ui_title.yncp').write_bytes(arc_member(f'TitleLogos/{name}/+Title.ar.00','ui_title.yncp'))
        for file,im in zip(['mat_title_001.dds','mat_title_004.dds'],images):
            im.save(dest/file);im.save(dest/(file[:-4]+'.png'))
            assert Image.open(dest/file).convert('RGBA').tobytes()==im.tobytes()
            if reference_comparisons:
                import io
                reference=Image.open(io.BytesIO(arc_member(f'TitleLogos/{name}/+Title.ar.00',file))).convert('RGBA')
                assert reference.width * im.height == reference.height * im.width
                reference.save(W/'references-only'/(name+'-'+file[:-4]+'.png'))
                sheet=Image.new('RGB',(1200,680),'#20242c');d=ImageDraw.Draw(sheet)
                for n,(label,pic) in enumerate([('자체 원본 기반 / '+name,im),('기존 UnleasHD 기반 / 비교 전용',reference)]):
                    d.text((n*600+12,12),label,font=font,fill='white');pic=pic.copy();pic.thumbnail((580,610),Image.Resampling.LANCZOS);sheet.paste(pic,(n*600+12,60),pic)
                sheet.save(W/'comparisons'/('title-'+name+'-'+file[:-4]+'.png'))
            report.append({'variant':name,'file':file,'size':list(im.size),'sha256':sha(dest/file),'dds_roundtrip':True,'hd_reference_used_as_input':False})
    dump(W/'title-verification.json',{'outputs':report,'original_upscale_model':model,'captions':{str(caption_path.relative_to(R)):sha(caption_path),str(custom_path.relative_to(R)):sha(custom_path)},'layout':'existing Korean mod scene metadata retained; visual title assets reconstructed from original game','gameplay_verified':False})
    print('Composed and roundtrip checked 4 title texture candidates',flush=True)
if __name__=='__main__':main()
