"""Use UnleasHD's 4K title sprites, reduce the Korean caption and extend native glow."""
from pathlib import Path
from datetime import datetime
import argparse, configparser, hashlib, json, re, shutil, struct
from PIL import Image, ImageFilter, ImageChops, ImageDraw
from probe_animated_ui import parse
from prepare_title_logo_v102 import arc, sha
R=Path(__file__).resolve().parents[1]
W=R/'Build/TitleLogo-HD'
PREVIOUS=R/'Build/TitleLogo-Reworked/Variant/+Title'
HD=W/'UnleasHD-4K/+Title'
ORIGINAL=R/'Build/TitleLogo-v102/Originals/Core/Title'
MOD=R/'UnleashedRecomp-Windows/mods/UnleashedKorean'
SCALE=3
VALUE='TitleLogos/ReworkedHDTest'

def build():
 out=W/'Variant/+Title';out.mkdir(parents=True,exist_ok=True)
 clean=Image.open(R/'Build/TitleLogo-Reworked/KoreanLogo-clean.png').convert('RGBA')
 assert sha(R/'Build/TitleLogo-Reworked/KoreanLogo-clean.png')=='51817ceb29f494e47ee3a30af0ee4ba9b2a7e1c8fe6b35f9e39010934089d30e'
 scene=(PREVIOUS/'ui_title.yncp').read_bytes();blob=bytearray(scene)
 title=next(s for s in parse(PREVIOUS/'ui_title.yncp') if s['name']=='/title_1')
 cast={c['name']:c for c in title['casts']}
 original=Image.open(ORIGINAL/'mat_title_001.dds').convert('RGBA')
 hd=Image.open(HD/'mat_title_001.dds').convert('RGBA')
 assert hd.size==(3072,1536)
 atlas=Image.new('RGBA',(3072,3072));atlas.paste(original.resize((3072,1536),Image.Resampling.NEAREST),(0,0))
 baseline=atlas.copy();boxes=set()
 # Copy only the English logo, slash, animated slash halo and TM sprite regions.
 for c in title['casts']:
  uv=c['subimage']
  if not uv or uv[0]!=0 or c['name']=='txt_unleashed':continue
  box=tuple(round(v*3072) for v in uv[1:]);assert box[3]<=1536
  atlas.paste(hd.crop(box),box);boxes.add(box)
 # The lower wordmark retains the exact old screen rectangle in its extended sprite.
 word=hd.crop((4*3,135*3,508*3,207*3));atlas.paste(word,(0,512*3))
 korean=clean.crop(clean.getbbox());korean.thumbnail((182*3,51*3),Image.Resampling.LANCZOS)
 korean_xy=((504*3-korean.width)//2,585*3)
 atlas.alpha_composite(korean,korean_xy)
 boxes.add((0,512*3,504*3,645*3))
 check=atlas.copy()
 for box in boxes:check.paste(baseline.crop(box),box)
 assert check.tobytes()==baseline.tobytes(),'Unrelated UI texels changed'
 # Native title halo is texture #6. It is additive RGB with opaque alpha.
 halo=Image.open(HD/'mat_title_004.dds').convert('RGBA');halo_before=halo.copy()
 assert halo.size==(1920,1920) and halo.getchannel('A').getextrema()[0]>=254
 hcast=cast['Cast_1820'];uv=hcast['subimage'];assert uv[0]==6
 halo_box=[round(v*1920) for v in uv[1:]];assert halo_box==[0,918,1644,1611]
 # Resolve the same rest-pose transforms used by the two existing cast groups.
 pos=lambda c:struct.unpack_from('>2f',scene,c['offset']+104)
 parent=pos(cast['position']);word_pos=pos(cast['txt_unleashed']);halo_pos=pos(hcast)
 corners=cast['txt_unleashed']['corners'];halo_corners=hcast['corners']
 word_left=parent[0]+word_pos[0]+corners[0]*1280
 word_top=parent[1]+word_pos[1]+corners[1]*720
 halo_left=halo_pos[0]+halo_corners[0]*1280
 halo_top=halo_pos[1]+halo_corners[1]*720
 k_world=(word_left+korean_xy[0]/3,word_top+korean_xy[1]/3-512)
 k_halo_xy=(round((k_world[0]-halo_left)*3+halo_box[0]),round((k_world[1]-halo_top)*3+halo_box[1]))
 mask=Image.new('L',halo.size);mask.paste(korean.getchannel('A'),k_halo_xy)
 # Match caption_outer_glow from prepare_title_logo_v102: 3px spread, 2.25px blur, 1.3 gain.
 glow=mask.filter(ImageFilter.MaxFilter(19)).filter(ImageFilter.GaussianBlur(2.25*3)).point(lambda x:min(255,round(x*1.3)))
 channels=[ImageChops.lighter(halo.getchannel(c),glow) for c in 'RGB']
 halo=Image.merge('RGBA',(*channels,halo.getchannel('A')))
 outside=halo.copy();glow_box=glow.getbbox();outside.paste(halo_before.crop(glow_box),glow_box)
 assert outside.tobytes()==halo_before.tobytes(),'Glow changed outside the caption'
 # Grow only the existing glow quad downward. No transforms, materials or keyframes change.
 allowed=set()
 def put(off,fmt,*values):
  data=struct.pack(fmt,*values);blob[off:off+len(data)]=data;allowed.update(range(off,off+len(data)))
 bottom=600;put(title['subs']+hcast['sub_index']*20+16,'>f',bottom/640)
 for idx in (3,7):put(hcast['offset']+12+idx*4,'>f',halo_corners[1]+(bottom-306)/720)
 assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(scene,blob)))
 assert len(blob)==len(scene)
 assert glow_box[0]>=halo_box[0] and glow_box[2]<=halo_box[2] and glow_box[3]<=bottom*3
 (out/'ui_title.yncp').write_bytes(blob);atlas.save(out/'mat_title_001.dds');halo.save(out/'mat_title_004.dds')
 for name,im in [('mat_title_001.dds',atlas),('mat_title_004.dds',halo)]:
  assert Image.open(out/name).convert('RGBA').tobytes()==im.tobytes()
 after=next(s for s in parse(out/'ui_title.yncp') if s['name']=='/title_1')
 for old,new in zip(title['casts'],after['casts']):
  if old['name']!='Cast_1820':assert old==new
 assert all(0<=v<=1 for c in after['casts'] if c['subimage'] for v in c['subimage'][1:])
 arc(out,packing=True);verify=W/'VerifyHD';verify.mkdir(exist_ok=True)
 archives=sorted(p for p in out.parent.glob('+Title.ar*') if p.is_file())
 for p in archives:shutil.copy2(p,verify/p.name)
 arc(verify/'+Title.ar.00')
 assert {p.name for p in out.iterdir()}=={p.name for p in (verify/'+Title').iterdir()}
 for p in out.iterdir():assert p.read_bytes()==(verify/'+Title'/p.name).read_bytes()
 # Export review assets from the exact DDS inputs, not reconstructed lettering.
 hd.crop((0,3,1536,402)).save(W/'EnglishHD-Sonic.png');word.save(W/'EnglishHD-Unleashed.png')
 glow.save(W/'Korean-native-glow-mask.png')
 # Static rest-pose preview; not a captured frame. Additive halo over dark/light backgrounds.
 import numpy as np
 preview_size=(1740,1000);origin=(350,190)
 def render(sheet,light,bgcolor):
  bg=Image.new('RGB',preview_size,bgcolor)
  lightpart=light.crop((0,918,1644,1800))
  location=(round((halo_left-origin[0])*3),round((halo_top-origin[1])*3))
  lightcanvas=Image.new('RGB',preview_size);lightcanvas.paste(lightpart.convert('RGB'),location)
  arr=np.minimum(np.array(bg).astype('uint16')+np.array(lightcanvas).astype('uint16'),255).astype('uint8')
  result=Image.fromarray(arr).convert('RGBA')
  # The tear is independently animated; its rest-pose silhouette is retained from the texture.
  for name in ['txt_sonic','txt_unleashed','txt_tm']:
   c=cast[name];x,y=pos(c);corn=c['corners'];u=c['subimage'];box=tuple(round(v*sheet.width) for v in u[1:])
   tile=sheet.crop(box);xy=(round((parent[0]+x+corn[0]*1280-origin[0])*3),round((parent[1]+y+corn[1]*720-origin[1])*3))
   result.alpha_composite(tile,xy)
  return result.convert('RGB')
 for label,color in [('dark','#172033'),('light','#b7c8d9')]:render(atlas,halo,color).save(W/f'preview-{label}.jpg',quality=96)
 # Compare former and reduced Korean caption with native additive glow at displayed scale.
 qa=Image.new('RGB',(1200,380),'#202838');dr=ImageDraw.Draw(qa)
 old=clean.crop(clean.getbbox());old.thumbnail((428,120),Image.Resampling.LANCZOS)
 panel=Image.new('RGBA',(580,280),'#202838');panel.alpha_composite(old,((580-old.width)//2,80));qa.paste(panel.convert('RGB'),(0,60));dr.text((30,30),'PREVIOUS',fill='white')
 new=korean.resize((round(korean.width*2/3),round(korean.height*2/3)),Image.Resampling.LANCZOS)
 ma=Image.new('L',(580,280));ma.paste(new.getchannel('A'),((580-new.width)//2,80));gl=ma.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(4.5)).point(lambda x:min(255,round(x*1.3)))
 ba=np.full((280,580,3),[32,40,56],dtype='uint16');ba=np.minimum(ba+np.array(gl)[:,:,None],255).astype('uint8');pa=Image.fromarray(ba).convert('RGBA');pa.alpha_composite(new,((580-new.width)//2,80));qa.paste(pa.convert('RGB'),(620,60));dr.text((650,30),'15% SMALLER + NATIVE WHITE GLOW',fill='white');qa.save(W/'korean-size-glow-comparison.jpg',quality=97)
 report={'passed':True,'sourceRepository':'https://github.com/UnleasHD-Team/UnleasHD','sourceRevision':'c7a709743926a94eb4b9337c54d9abdb103fb8f1','sourceAtlasSize':list(hd.size),'nativeEnglishSonicSprite':[1536,399],'nativeEnglishUnleashedSprite':list(word.size),'sourceTitleFiles':{p.name:sha(p) for p in HD.glob('*.dds')},'koreanSourceSha256':sha(R/'Build/TitleLogo-Reworked/KoreanLogo-clean.png'),'previousKoreanSizeAt720p':[214,60],'koreanSizeAt720p':[korean.width/3,korean.height/3],'koreanLinearScale':korean.width/3/214,'koreanAnchorUnchanged':True,'koreanWorldPosition':list(k_world),'glowPlacement':list(k_halo_xy),'glowBounds':list(glow_box),'glowSpreadAt720p':3,'glowBlurAt720p':2.25,'glowGain':1.3,'nativeAdditiveHalo':True,'haloSourceBottomBefore':537,'haloSourceBottomAfter':600,'changedSceneByteOffsets':sorted(i for i,(a,b) in enumerate(zip(scene,blob)) if a!=b),'onlyHaloUVAndBottomVerticesChanged':True,'allAnimationBytesPreserved':True,'englishLogoPositionUnchanged':True,'unrelatedAtlasTexelsUnchanged':True,'archiveRoundTrip':True,'archives':{p.name:sha(p) for p in archives},'installed':False,'gameVisuallyVerified':False}
 (W/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(report,ensure_ascii=True,indent=2));return report

def install(report):
 target=MOD/VALUE;assert not target.exists(),'Target already exists; inspect the previous installation before reinstalling'
 backup=W/('Backup-'+datetime.now().strftime('%Y%m%d-%H%M%S'));backup.mkdir()
 before={p.relative_to(MOD).as_posix():sha(p) for p in MOD.rglob('*') if p.is_file()}
 db=R/'UnleashedRecomp-Windows/mods/ModsDB.ini';db_before=db.read_bytes()
 for name in ['mod.ini','ConfigSchema.json']:shutil.copy2(MOD/name,backup/name)
 target.mkdir(parents=True)
 for name,digest in report['archives'].items():shutil.copy2(W/'Variant'/name,target/name);assert sha(target/name)==digest
 p=MOD/'ConfigSchema.json';schema=json.loads(p.read_text(encoding='utf-8-sig'))
 schema['Enums']['TitleLogoVariant'].append({'DisplayName':'소닉 언리쉬드 (고해상도·외부광선 테스트)','Value':VALUE,'Description':['고해상도 영문 로고, 약 15% 축소한 한글 로고, 기존 타이틀 발광 방식의 흰 외부광선을 적용합니다.']})
 next(e for g in schema['Groups'] for e in g['Elements'] if e.get('Name')=='IncludeDir3')['Value']=VALUE
 p.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 p=MOD/'mod.ini';text=p.read_text(encoding='utf-8-sig');text,n=re.subn(r'(?m)^IncludeDir3=.*$',f'IncludeDir3="{VALUE}"',text);assert n==1;p.write_text(text,encoding='utf8')
 after={p.relative_to(MOD).as_posix():sha(p) for p in MOD.rglob('*') if p.is_file()};changed=sorted(n for n in after if before.get(n)!=after[n])
 assert set(before)<=set(after)
 assert all(n in ('mod.ini','ConfigSchema.json') or n.startswith(VALUE+'/') for n in changed)
 assert db.read_bytes()==db_before
 old=configparser.ConfigParser(interpolation=None);old.read(backup/'mod.ini',encoding='utf-8-sig');new=configparser.ConfigParser(interpolation=None);new.read(MOD/'mod.ini',encoding='utf8')
 for s in old:
  for k in old[s]:
   if s=='Main' and k=='includedir3':continue
   assert old[s][k]==new[s][k]
 report.update(installed=True,backup=str(backup),installedVariant=VALUE,changedFiles=changed,otherResourcesAndSettingsUnchanged=True,hmmLoadOrderUnchanged=True)
 (W/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('Installed:',VALUE)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--install',action='store_true');args=parser.parse_args()
 if args.install:assert not (MOD/VALUE).exists()
 report=build()
 if args.install:install(report)
