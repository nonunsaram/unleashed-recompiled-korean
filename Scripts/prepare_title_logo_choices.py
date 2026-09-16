"""Build five independent title choices and install without touching other mod resources."""
from pathlib import Path
from datetime import datetime
import argparse, json, shutil, configparser, re
import numpy as np
from PIL import Image, ImageFilter, ImageChops, ImageDraw
from prepare_title_logo_v102 import arc, sha
from probe_animated_ui import parse
R=Path(__file__).resolve().parents[1]
W=R/'Build/TitleLogo-Choices'
HD=R/'Build/TitleLogo-HD/UnleasHD-4K/+Title'
OLD=R/'Build/TitleLogo-v102/Originals/Core/Title'
MOD=R/'UnleashedRecomp-Windows/mods/UnleashedKorean'
LABELS={'Default':'게임 기본값','Original':'소닉 언리쉬드 (영어 원본)','Korean':'소닉 언리쉬드 (한국어 추가)','Japanese':'소닉 월드 어드벤처 (일본어 원본)','Custom':'소닉 월드 어드벤처 (한국어 추가)'}

def pack_verify(name,folder):
 arc(folder,packing=True)
 verify=W/'Verify'/name;verify.mkdir(parents=True,exist_ok=True)
 archives=sorted(p for p in folder.parent.glob('+Title.ar*') if p.is_file())
 for p in archives:shutil.copy2(p,verify/p.name)
 arc(verify/'+Title.ar.00')
 assert {p.name for p in folder.iterdir()}=={p.name for p in (verify/'+Title').iterdir()}
 for p in folder.iterdir():assert p.read_bytes()==(verify/'+Title'/p.name).read_bytes()
 return {'archives':{p.name:sha(p) for p in archives},'members':{p.name:sha(p) for p in folder.iterdir()},'roundTrip':True}

def build():
 W.mkdir(exist_ok=True)
 hd=Image.open(HD/'mat_title_001.dds').convert('RGBA')
 halo_base=Image.open(HD/'mat_title_004.dds').convert('RGBA')
 assert hd.size==(3072,1536) and halo_base.size==(1920,1920)
 previous=R/'Build/TitleLogo-HD/Variant/+Title'
 glow=Image.open(R/'Build/TitleLogo-HD/Korean-native-glow-mask.png').convert('L')
 dim=glow.point(lambda v:round(v*.92))
 new_halo=Image.merge('RGBA',tuple(ImageChops.lighter(halo_base.getchannel(c),dim) for c in 'RGB')+(halo_base.getchannel('A'),))
 before=Image.open(previous/'mat_title_004.dds').convert('RGBA')
 check=new_halo.copy();bounds=glow.getbbox();check.paste(before.crop(bounds),bounds)
 assert check.tobytes()==before.tobytes()
 assert np.all(np.array(new_halo)[:,:,:3]<=np.array(before)[:,:,:3])
 # The original logo's complete glow region remains pixel-identical wherever the Korean mask is zero.
 zero=np.array(glow)==0
 assert np.array_equal(np.array(new_halo)[zero],np.array(before)[zero])
 # Preserve World Adventure's user-supplied lettering and exact original ink placement.
 custom=hd.copy();kana=(30*3,262*3,434*3,289*3)
 text=Image.open(R/'Assets/TitleLogo/CustomLogo.png').convert('RGBA');ink=text.getchannel('A').getbbox()
 assert ink==(97,3,307,24)
 tile=Image.new('RGBA',(404*3,27*3));letters=text.crop(ink).resize((210*3,21*3),Image.Resampling.LANCZOS)
 tile.paste(letters,(17*3,3*3));custom.paste(tile,kana)
 test=custom.copy();test.paste(hd.crop(kana),kana);assert test.tobytes()==hd.tobytes()
 # Rebuild the Japanese caption glow at native 3x scale with the v102 method.
 body=Image.new('L',halo_base.size)
 for box,size,xy in [((0,3,1536,402),(1305,339),(30,114)),((2250,303,3072,1122),(699,696),(945,33))]:
  part=hd.crop(box).getchannel('A').resize(size,Image.Resampling.LANCZOS)
  layer=Image.new('L',halo_base.size);layer.paste(part,xy);body=ImageChops.lighter(body,layer)
 body=body.filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.GaussianBlur(6))
 mask=Image.new('L',halo_base.size)
 alpha=tile.getchannel('A').resize((1029,69),Image.Resampling.LANCZOS);mask.paste(alpha,(63,33))
 caption_light=mask.filter(ImageFilter.MaxFilter(19)).filter(ImageFilter.GaussianBlur(6.75)).point(lambda v:min(255,round(v*1.3)))
 light=ImageChops.lighter(body,caption_light)
 orig=np.array(halo_base);result=orig.copy();ys,xs=np.mgrid[:216,:1260]
 blend=np.minimum(1.,(216-ys)/60)*np.minimum(1.,(1260-xs)/108)
 for c in range(3):result[:216,:1260,c]=np.rint(np.array(light)[:216,:1260]*blend+orig[:216,:1260,c]*(1-blend)).astype('uint8')
 custom_halo=Image.fromarray(result)
 assert np.array_equal(result[:,:,3],orig[:,:,3])
 assert np.array_equal(result[216:],orig[216:]) and np.array_equal(result[:216,1260:],orig[:216,1260:])
 variants={}
 for name in LABELS:
  folder=W/'Variants'/name/'+Title';folder.mkdir(parents=True,exist_ok=True)
  if name=='Default':
   assert not any(folder.iterdir()),'Default must contain no override files'
   variants[name]={'archives':{},'members':{},'roundTrip':True,'atlasSize':None,'haloSize':None,'routing':'passthrough','sceneIdenticalToPrevious':True}
   continue
  elif name=='Korean':
   for file in ['ui_title.yncp','mat_title_001.dds']:shutil.copy2(previous/file,folder/file)
   new_halo.save(folder/'mat_title_004.dds')
   assert Image.open(folder/'mat_title_004.dds').convert('RGBA').tobytes()==new_halo.tobytes()
  else:
   shutil.copy2(R/'Build/TitleLogo-v102/Variants'/name/'+Title/ui_title.yncp',folder/'ui_title.yncp')
   if name=='Custom':
    custom.save(folder/'mat_title_001.dds');custom_halo.save(folder/'mat_title_004.dds')
    for file,im in [('mat_title_001.dds',custom),('mat_title_004.dds',custom_halo)]:assert Image.open(folder/file).convert('RGBA').tobytes()==im.tobytes()
   else:
    for file in ['mat_title_001.dds','mat_title_004.dds']:shutil.copy2(HD/file,folder/file)
  info=pack_verify(name,folder)
  info['atlasSize']=list(Image.open(folder/'mat_title_001.dds').size)
  info['haloSize']=list(Image.open(folder/'mat_title_004.dds').size)
  src=OLD/'ui_title.yncp' if name=='Default' else previous/'ui_title.yncp' if name=='Korean' else R/'Build/TitleLogo-v102/Variants'/name/'+Title/ui_title.yncp'
  assert (folder/'ui_title.yncp').read_bytes()==src.read_bytes()
  info['sceneIdenticalToPrevious']=True
  scenes=parse(folder/'ui_title.yncp');one=next(s for s in scenes if s['name']=='/title_1');two=next(s for s in scenes if s['name']=='/title_2')
  assert (one['offset']!=two['offset']) if name=='Default' else (one['offset']==two['offset'])
  info['routing']='game choice' if name=='Default' else 'title_1' if name in ('Original','Korean') else 'title_2'
  variants[name]=info
  print('Verified:',name,flush=True)
 # A gentle old/new comparison using the exact masks and the exact Korean sprite.
 sheet=Image.open(previous/'mat_title_001.dds').convert('RGBA');logo=sheet.crop((483,1755,1028,1908))
 # Bounding placement from the previously verified native halo geometry.
 qa=Image.new('RGB',(1300,520),'#202838');draw=ImageDraw.Draw(qa)
 for i,g in enumerate([glow,dim]):
  light=g.crop((500,1525,1150,1815));a=np.full((290,650,3),[32,40,56],dtype='uint16');a=np.minimum(a+np.array(light)[:,:,None],255).astype('uint8');panel=Image.fromarray(a).convert('RGBA');panel.alpha_composite(logo,(46,51));qa.paste(panel.convert('RGB'),(i*650,90));draw.text((30+i*650,35),'BEFORE' if i==0 else 'AFTER: 8% LESS LIGHT',fill='white')
 qa.save(W/'glow-comparison.jpg',quality=97)
 # High-resolution Japanese/Korean wordmark proof, preserving previous positioning.
 custom.crop((0,780,1400,879)).save(W/'world-caption-HD-preview.png')
 custom_halo.resize((640,640),Image.Resampling.LANCZOS).convert('RGB').save(W/'world-halo-preview.jpg',quality=96)
 report={'passed':True,'sourceRepository':'https://github.com/UnleasHD-Team/UnleasHD','sourceRevision':'c7a709743926a94eb4b9337c54d9abdb103fb8f1','variants':variants,'koreanGlowMultiplier':.92,'previousGlowMax':glow.getextrema()[1],'newGlowMax':dim.getextrema()[1],'originalEnglishGlowUnchanged':True,'koreanArtworkPositionSizeAndAnimationUnchanged':True,'worldKoreanSourceSize':list(text.size),'worldKoreanInkSize':[210,21],'worldKoreanSourcePreserved':True,'worldKoreanCaptionResampling':'Lanczos 3x; no invented lettering detail','worldCaptionSourceSha256':sha(R/'Assets/TitleLogo/CustomLogo.png'),'installed':False,'gameVisuallyVerified':False}
 (W/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return report

def configure(root):
 root=Path(root);p=root/'ConfigSchema.json';schema=json.loads(p.read_text(encoding='utf-8-sig'))
 schema['Enums']['TitleLogoVariant']=[{'DisplayName':label,'Value':'TitleLogos/'+name,'Description':['로고를 덮어쓰지 않습니다. 설치된 로고 모드가 있으면 따르고, 없으면 게임 원본을 사용합니다.'] if name=='Default' else ['고해상도 타이틀 로고입니다. UnleasHD를 별도로 설치하지 않아도 적용됩니다.']} for name,label in LABELS.items()]
 ini_path=root/'mod.ini';text=ini_path.read_text(encoding='utf-8-sig');ini=configparser.ConfigParser(interpolation=None);ini.read_string(text)
 selected=ini['Main'].get('IncludeDir3','"TitleLogos/Default"').strip('"')
 if selected in ['TitleLogos/ReworkedHDTest','TitleLogos/ReworkedTest','TitleLogos/KoreanOfficial']:selected='TitleLogos/Korean'
 if selected not in {'TitleLogos/'+n for n in LABELS}:selected='TitleLogos/Default'
 text,n=re.subn(r'(?m)^IncludeDir3=.*$',f'IncludeDir3="{selected}"',text);assert n==1
 ini_path.write_text(text,encoding='utf8')
 element=next(e for g in schema['Groups'] for e in g['Elements'] if e.get('Name')=='IncludeDir3')
 element.update(Value=selected,DefaultValue='TitleLogos/Default',Description=['게임 기본값은 로고를 덮어쓰지 않고 기존 게임·모드 설정을 따릅니다.','나머지 네 가지는 고해상도 로고이며, UnleasHD 설치 여부와 관계없이 적용됩니다.','다른 로고 모드를 함께 쓰면 한국어 패치를 위에 두고 저장한 뒤 게임을 다시 시작하세요.'])
 p.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return schema

def install(report):
 before={p.relative_to(MOD).as_posix():sha(p) for p in MOD.rglob('*') if p.is_file()}
 db=R/'UnleashedRecomp-Windows/mods/ModsDB.ini';db_before=db.read_bytes()
 backup=W/('Backup-'+datetime.now().strftime('%Y%m%d-%H%M%S'));backup.mkdir()
 for name in ['mod.ini','ConfigSchema.json']:shutil.copy2(MOD/name,backup/name)
 # Move the complete old logo set to a verified workspace backup; no archives are deleted.
 src=(MOD/'TitleLogos').resolve();dst=(backup/'TitleLogos').resolve()
 assert src.is_relative_to(R.resolve()) and dst.is_relative_to(R.resolve()) and not dst.exists()
 shutil.move(str(src),str(dst))
 for name in LABELS:
  out=MOD/'TitleLogos'/name;out.mkdir(parents=True)
  for file,digest in report['variants'][name]['archives'].items():shutil.copy2(W/'Variants'/name/file,out/file);assert sha(out/file)==digest
 configure(MOD)
 (MOD/'TitleLogos/manifest.json').write_text(json.dumps({'format':'title-logo-choices-v1','variants':report['variants']},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 after={p.relative_to(MOD).as_posix():sha(p) for p in MOD.rglob('*') if p.is_file()}
 for name,digest in before.items():
  if name in ['mod.ini','ConfigSchema.json'] or name.startswith('TitleLogos/'):continue
  assert after.get(name)==digest,name
 assert db.read_bytes()==db_before
 old=configparser.ConfigParser(interpolation=None);old.read(backup/'mod.ini',encoding='utf-8-sig');new=configparser.ConfigParser(interpolation=None);new.read(MOD/'mod.ini',encoding='utf8')
 for s in old:
  for k in old[s]:
   if s=='Main' and k=='includedir3':continue
   assert old[s][k]==new[s][k]
 report.update(installed=True,backup=str(backup),selected=new['Main']['IncludeDir3'].strip('"'),otherFilesAndSettingsUnchanged=True,loadOrderUnchanged=True)
 (W/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('Installed five title choices.',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--install',action='store_true');p.add_argument('--install-built',action='store_true');args=p.parse_args()
 report=json.loads((W/'verification.json').read_text(encoding='utf8')) if args.install_built else build()
 if args.install or args.install_built:install(report)
