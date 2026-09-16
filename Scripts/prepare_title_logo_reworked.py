"""Clean the supplied logo's exterior matte and build a reversible local title test."""
from pathlib import Path
from collections import deque
from datetime import datetime
import argparse, json, shutil, hashlib, re, configparser
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from prepare_title_logo_v102 import arc, sha
R=Path(__file__).resolve().parents[1]
W=R/'Build/TitleLogo-Reworked'
SOURCE=R/'Assets/소닉언리쉬드한국어로고.png'
if not SOURCE.exists():SOURCE=R/'Assets/TitleLogo/Reworked/KoreanLogo.png'
BASE=R/'Build/TitleLogo-v103/Variants/KoreanOfficial/+Title'
D=R/'UnleashedRecomp-Windows/mods/UnleashedKorean'

def build():
 W.mkdir(parents=True,exist_ok=True)
 im=Image.open(SOURCE).convert('RGBA'); original=np.array(im); a=original.copy(); h,w=a.shape[:2]
 # These two isolated, opaque canvas-corner pixels are unrelated to the logo.
 removed=[]
 for y,x in [(0,0),(h-1,0)]:
  patch=a[max(0,y-1):min(h,y+2),:2,3]
  if a[y,x,3] and np.count_nonzero(patch)==1:
   a[y,x]=0; removed.append([x,y])
 # Only flood transparent space reachable from the canvas exterior.
 transparent=a[:,:,3]==0; outside=np.zeros((h,w),bool); q=deque()
 for y in range(h):
  for x in (0,w-1):
   if transparent[y,x] and not outside[y,x]:outside[y,x]=1;q.append((y,x))
 for x in range(w):
  for y in (0,h-1):
   if transparent[y,x] and not outside[y,x]:outside[y,x]=1;q.append((y,x))
 while q:
  y,x=q.popleft()
  for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
   yy,xx=y+dy,x+dx
   if 0<=yy<h and 0<=xx<w and transparent[yy,xx] and not outside[yy,xx]:outside[yy,xx]=1;q.append((yy,xx))
 dilate=lambda mask: np.array(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
 rgb=a[:,:,:3].astype(float)
 boundary=dilate(outside)&(a[:,:,3]>0)
 black=(rgb.max(2)<24)&(a[:,:,3]>240)
 neutral=(rgb.max(2)-rgb.min(2)<=4)
 matte=boundary&dilate(black)&neutral&(rgb.max(2)>0)
 # Unmatte black contours antialiased against white: coverage = 1 - luminance.
 coverage=1-rgb.mean(2)/255
 a[matte,3]=np.rint(a[matte,3]*coverage[matte]).astype('uint8')
 a[matte,:3]=0
 clean=Image.fromarray(a)
 clean_path=W/'KoreanLogo-clean.png';clean.save(clean_path)
 allowed=matte.copy()
 for x,y in removed:allowed[y,x]=1
 assert np.array_equal(a[~allowed],original[~allowed])
 white_inside=(original[:,:,:3].min(2)>180)&(original[:,:,3]>0)&~boundary&~allowed
 assert np.array_equal(a[white_inside],original[white_inside])
 # Retain the exact validated scene, UVs, timing, opacity and vertex coordinates.
 out=W/'Variant/+Title';out.mkdir(parents=True,exist_ok=True)
 scene=BASE/'ui_title.yncp';shutil.copy2(scene,out/scene.name)
 atlas=Image.open(BASE/'mat_title_001.dds').convert('RGBA');before=atlas.copy()
 assert atlas.size==(4096,4096)
 box=(0,584*4,504*4,645*4)
 atlas.paste((0,0,0,0),box)
 logo=clean.crop(clean.getbbox());logo.thumbnail((224*4,60*4),Image.Resampling.LANCZOS)
 xy=((504*4-logo.width)//2,585*4);atlas.alpha_composite(logo,xy)
 assert xy[1]+logo.height<=box[3]
 check=atlas.copy();check.paste(before.crop(box),box)
 assert check.tobytes()==before.tobytes()
 atlas.save(out/'mat_title_001.dds')
 assert Image.open(out/'mat_title_001.dds').convert('RGBA').tobytes()==atlas.tobytes()
 assert (out/scene.name).read_bytes()==scene.read_bytes()
 arc(out,packing=True)
 verify=W/'Verify';verify.mkdir(exist_ok=True)
 archive_files=sorted(p for p in out.parent.glob('+Title.ar*') if p.is_file())
 assert any(p.name=='+Title.arl' for p in archive_files)
 for p in archive_files:shutil.copy2(p,verify/p.name)
 arc(verify/'+Title.ar.00')
 for p in out.iterdir():assert p.read_bytes()==(verify/'+Title'/p.name).read_bytes()
 # Review full source and cleanup on dark panels, plus final title composition.
 qa=Image.new('RGB',(1280,920),'#202838');draw=ImageDraw.Draw(qa)
 for i,pic in enumerate([im,clean]):
  bg=Image.new('RGBA',pic.size,'#202838');bg.alpha_composite(pic);qa.paste(bg.convert('RGB'),(0,i*400+20))
  draw.text((12,i*400+5),'SOURCE' if i==0 else 'CLEANED',fill='white')
 for i,pic in enumerate([im,clean]):
  small=pic.crop(clean.getbbox());small.thumbnail((224,60),Image.Resampling.LANCZOS)
  bg=Image.new('RGBA',(300,100),'#202838');bg.alpha_composite(small,(35,20));qa.paste(bg.convert('RGB'),(i*320,820))
 qa.save(W/'cleanup-comparison.jpg',quality=98)
 preview=Image.new('RGBA',(560,330))
 original_sheet=Image.open(R/'Build/TitleLogo-v102/Originals/Core/Title/mat_title_001.dds').convert('RGBA')
 preview.alpha_composite(original_sheet.crop((0,1,512,134)),(24,8))
 tile=atlas.crop((0,512*4,504*4,645*4)).resize((504,133),Image.Resampling.LANCZOS)
 preview.alpha_composite(tile,(28,141))
 preview.save(W/'title-composite.png')
 report={'passed':True,'source':str(SOURCE),'sourceSha256':sha(SOURCE),'cleaned':str(clean_path),'cleanedSha256':sha(clean_path),'exteriorMattePixels':int(matte.sum()),'removedIsolatedPixels':removed,'interiorWhitePixelsUnchanged':int(white_inside.sum()),'allOtherPixelsUnchanged':True,'sceneIdenticalToValidatedV103':True,'sceneSha256':sha(scene),'outsideCaptionAtlasIdentical':True,'placedSize':list(logo.size),'placedPosition':list(xy),'archiveRoundTrip':True,'archives':{p.name:sha(p) for p in archive_files},'installed':False,'gameVisuallyVerified':False}
 (W/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return report

def install(report):
 db=R/'UnleashedRecomp-Windows/mods/ModsDB.ini';db_before=db.read_bytes()
 before={p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file()}
 backup=W/('Backup-'+datetime.now().strftime('%Y%m%d-%H%M%S'));backup.mkdir()
 for name in ['mod.ini','ConfigSchema.json']:shutil.copy2(D/name,backup/name)
 target=D/'TitleLogos/ReworkedTest';assert not target.exists(),'Test already installed; preserve existing backup and inspect before reinstalling'
 target.mkdir(parents=True)
 for name,expected in report['archives'].items():
  shutil.copy2(W/'Variant'/name,target/name);assert sha(target/name)==expected
 p=D/'ConfigSchema.json';schema=json.loads(p.read_text(encoding='utf-8-sig'))
 schema['Enums']['TitleLogoVariant'].append({'DisplayName':'소닉 언리쉬드 (한국어 재작업 · 테스트)','Value':'TitleLogos/ReworkedTest','Description':['사용자 제공 로고의 외곽 잔여 배경을 정리한 테스트본입니다. 기존 1.0.3 시험본의 위치와 연출을 유지합니다.']})
 element=next(e for g in schema['Groups'] for e in g['Elements'] if e.get('Name')=='IncludeDir3');element['Value']='TitleLogos/ReworkedTest'
 element['Description'].append('한국어 재작업 · 테스트는 소닉 언리쉬드 한국어 로고를 표시합니다.')
 p.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 p=D/'mod.ini';text=p.read_text(encoding='utf-8-sig');text,n=re.subn(r'(?m)^IncludeDir3=.*$', 'IncludeDir3="TitleLogos/ReworkedTest"',text);assert n==1
 text=text.replace('언리쉬드 한국어 로고 제외.', '한국어 재작업 로고 테스트 적용.')
 p.write_text(text,encoding='utf8')
 after={p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file()}
 changed=sorted(n for n in after if before.get(n)!=after[n]);assert set(before)<=set(after)
 assert all(n in ['mod.ini','ConfigSchema.json'] or n.startswith('TitleLogos/ReworkedTest/') for n in changed)
 old=configparser.ConfigParser(interpolation=None);old.read(backup/'mod.ini',encoding='utf-8-sig')
 new=configparser.ConfigParser(interpolation=None);new.read(D/'mod.ini',encoding='utf8')
 for section in old:
  for key in old[section]:
   if (section=='Main' and key=='includedir3') or (section=='Desc' and key=='description'):continue
   assert old[section][key]==new[section][key]
 assert db.read_bytes()==db_before
 report.update(installed=True,installedMod=str(D),backup=str(backup),changedFiles=changed,hmmLoadOrderUnchanged=True,otherSettingsUnchanged=True)
 (W/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--install',action='store_true');args=parser.parse_args()
 report=build()
 if args.install:install(report)
 print(json.dumps(report,ensure_ascii=False,indent=2))

