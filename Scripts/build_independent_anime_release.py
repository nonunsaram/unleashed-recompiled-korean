"""Build an independent Korean-only anime overlay; never modifies review16 development/reference data."""
from pathlib import Path
import sys,json,hashlib,io,struct,shutil,zipfile,configparser,csv,ast
from PIL import Image
from check_release_guard import ar_members
def packpart(entries):
 b=bytearray(struct.pack('<4I',0,16,20,64))
 for name,data in entries:
  n=name.encode();s=21+len(n);s+=(-(len(b)+s))%64
  b+=struct.pack('<5I',s+len(data),len(data),s,0,0)+n+b'\0'+b'\0'*(s-21-len(n))+data
 return bytes(b)

import release_guard_data as HD
R=Path(__file__).resolve().parents[1];D=R/'Build/Development-v105p-Playtest/UnleashedKorean'
W=R/'Build/IndependentKorean-Anime1440-20261003';M=W/'package/UnleashedKorean'
O=R/'outputs/Korean-Independent-Anime1440-20261003';I=R/'UnleashedRecomp-Windows/mods/UnleashedKorean'
OLD_COMPAT='Compatibility/UnleasHD-1.4.2';COMPAT='Compatibility/OriginalUpscale-1440p'
sha=lambda b:hashlib.sha256(b).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def member_hashes(folder):return {(p.relative_to(folder).as_posix(),n):sha(b) for p in folder.rglob('*.ar.*') for n,b in ar_members(p.read_bytes())}
def own_text_hashes():
 from build_unleashhd_ui_compat_v105 import draw_korean
 labels=json.loads((R/'Translation/ui-textures-ko.json').read_text(encoding='utf8'))['labels']
 jobs=json.loads((W/'manifest.json').read_text(encoding='utf8'));owned=set();proof=[]
 for index in [31,32]:
  j=next(x for x in jobs if x['index']==index);ls=[]
  for original in labels:
   if original['texture']!=index:continue
   x=dict(original);x['box']=[v/2 for v in x['box']]
   for key in ['size','anchor_x','top']:x[key]/=2
   ls.append(x)
  im,count=draw_korean(Image.new('RGBA',j['target']),ls,index,None,j['target'][0]/j['source_size'][0]);out=io.BytesIO();im.save(out,format='DDS');blob=out.getvalue()
  assert blob==(W/'candidates'/j['id']/j['file']).read_bytes()
  owned.add(sha(blob));proof.append({'file':j['file'],'sha256':sha(blob),'method':'Blank transparent canvas + own Korean text rendering; zero image inputs','labels':count})
 return owned,proof
def verify(folder):
 from independent_option_paths import verify_option_directories
 verify_option_directories(folder)
 replacements=json.loads((W/'replacement-manifest.json').read_text(encoding='utf8'))['entries']
 banned=set(HD.UNLEASHD_MEMBER_SHA256)|{h for a,n,h in HD.APPROVED_CSV}
 old=R/'Build/KoreanOnly-HD1440-20261003/before-apply/Scripts/release_guard_data.py'
 for node in ast.parse(old.read_text(encoding='utf8')).body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='APPROVED_CSV' for t in node.targets):banned|={h for a,n,h in ast.literal_eval(node.value)}
 owned,proof=own_text_hashes()
 assert not (owned & set(HD.UNLEASHD_MEMBER_SHA256))
 hits=[];dds=0
 for p in folder.rglob('*'):
  if not p.is_file():continue
  assert p.name!='UnleasHD-permission-texture-list.csv';assert OLD_COMPAT not in p.relative_to(folder).as_posix()
  if '.ar.' in p.name:
   for n,b in ar_members(p.read_bytes()):
    assert n!='mat_stage_ss_082.dds'
    if n.endswith('.dds'):
     dds+=1
     if sha(b) in banned and sha(b) not in owned:hits.append((str(p),n))
  elif p.suffix=='.dds':
   dds+=1
   if sha(p.read_bytes()) in banned and sha(p.read_bytes()) not in owned:hits.append((str(p),p.name))
  if p.suffix=='.arl':assert b'mat_stage_ss_082.dds' not in p.read_bytes()
 assert not hits,hits
 for row in replacements:
  p=folder/row['archive'].replace(OLD_COMPAT,COMPAT);data=dict(ar_members(p.read_bytes()))[row['file']]
  assert sha(data)==row['sha256'];assert list(Image.open(io.BytesIO(data)).size)==row['size']
 original=member_hashes(D);current=member_hashes(folder);normalized={(a.replace(COMPAT,OLD_COMPAT),n):h for (a,n),h in current.items()}
 assert original.keys()==normalized.keys();delta={k for k in original if original[k]!=normalized[k]};assert delta=={(x['archive'],x['file']) for x in replacements if original[(x['archive'],x['file'])]!=x['sha256']}
 return {'passed':True,'archiveMembers':len(current),'replacedMembers':len(delta),'unchangedMembers':len(current)-len(delta),'ddsInstancesScanned':dds,'unexplainedUnleasHDOrDerivedHashHits':hits,'ownBlankCanvasProof':proof,'independentUniqueImages':20,'independentPlacements':22,'bulkUpscaleIncluded':False,'gameplayVerified':False}
def ini(edition,installed=False):
 c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(I/'mod.ini',encoding='utf-8-sig')
 c['Desc']['Title']='"Korean Translation / 한국어 패치 — '+('전체판' if edition=='Full' else '기본판')+' (Independent Anime)"'
 c['Desc']['Version']='"1.0.5-independent-anime1440"';c['Desc']['Date']='"2026-10-03"'
 c['Desc']['Description']='"게임 원본 기반 한국어 이미지. 업스케일 옵션으로 UnleasHD 1440p와 함께 사용. UnleasHD 유래 이미지 미포함."'
 c['Main']['IncludeDirCount']='4';c['Main']['IncludeDir2']='"."'
 c['Main'].setdefault('IncludeDir3','"TitleLogos/Default"')
 c['Main']['IncludeDir1']='"'+(COMPAT if installed else 'Compatibility/None')+'"'
 if not installed:c['Main']['IncludeDir0']='"WorldMapVariants/AllDLC"';c['Main']['IncludeDir3']='"TitleLogos/Default"'
 out=io.StringIO();c.write(out,space_around_delimiters=False);return out.getvalue().encode('utf8')
def main():
 assert not M.exists() and not O.exists();M.mkdir(parents=True);O.mkdir()
 changes=json.loads((W/'replacement-manifest.json').read_text(encoding='utf8'))['entries'];assert len(changes)==22
 # Copy proven translation/font/scene payload from the unchanged current development baseline.
 for p in D.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(D)
  if len(rel.parts)==1 and p.suffix in ['.md','.csv']:continue
  if p.name=='provider-and-permission-audit.json':continue
  dest=M/rel.as_posix().replace(OLD_COMPAT,COMPAT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 for row in changes:
  p=M/row['archive'].replace(OLD_COMPAT,COMPAT);entries=ar_members(p.read_bytes());blob=(W/row['candidate']).read_bytes();assert sha(blob)==row['sha256']
  p.write_bytes(packpart([(n,blob if n==row['file'] else b) for n,b in entries]))
 # Keep part names, update their recorded sizes.
 for p in M.rglob('*.arl'):
  data=bytearray(p.read_bytes());assert data[:4]==b'ARL2';count=struct.unpack_from('<I',data,4)[0]
  for i in range(count):struct.pack_into('<I',data,8+i*4,(p.parent/(p.stem+f'.ar.{i:02}')).stat().st_size)
  p.write_bytes(data)
 schema=json.loads((M/'ConfigSchema.json').read_text(encoding='utf8'))
 for group in schema['Groups']:
  for e in group['Elements']:
   if e['Name']=='IncludeDir1':
    e.update(DisplayName='업스케일 한국어 이미지',Description=['게임 원본을 anime 모델로 확대한 뒤 한국어를 합성한 독립 제작 이미지입니다.','UnleasHD 1440p를 함께 사용할 때 켜세요. 한국어가 들어간 이미지만 교체합니다.','한국어 패치에는 UnleasHD 유래 이미지가 들어 있지 않습니다.','HMM 순서: 한국어 패치 → UnleasHD. 나머지 UI는 별도 UnleasHD에서 읽습니다.'],Value='Compatibility/None',DefaultValue='Compatibility/None')
 schema['Enums']['UnleasHDCompatibility']=[{'DisplayName':'끄기 — 기본 한국어 UI','Value':'Compatibility/None','Description':[]},{'DisplayName':'켜기 — 독립 업스케일 / UnleasHD 1440p 호환','Value':COMPAT,'Description':['게임 원본 + 직접 만든 한국어 자료만 사용합니다.']}]
 from shorten_independent_options import shorten
 shorten(schema)
 dump(M/'ConfigSchema.json',schema);(M/'mod.ini').write_bytes(ini('Basic'))
 rows=[]
 for x in changes:rows.append({'archive':x['archive'].replace(OLD_COMPAT,COMPAT),'file':x['file'],'size':x['size'],'sha256':x['sha256'],'source':'Original game + own Korean composition','model':'own font rendering (blank canvas)' if x['file'] in ['mat_worldmap_en_001.dds','mat_worldmap_en_002.dds'] else 'realesrgan-x4plus-anime'})
 s=io.StringIO(newline='');c=csv.DictWriter(s,fieldnames=list(rows[0]));c.writeheader();c.writerows(rows);(M/'Independent-image-provenance.csv').write_bytes(s.getvalue().encode('utf-8-sig'))
 jobs=json.loads((W/'manifest.json').read_text(encoding='utf8'))
 dump(M/'Independent-image-provenance.json',{'model':'realesrgan-x4plus-anime','sourcePolicy':'Game originals and own Korean artwork only; no UnleasHD image input or derived image output','sources':[{'id':j['id'],'name':j['file'],'originalSha256':j['source_sha256'],'inputSha256':j['input_sha256']} for j in jobs],'outputs':rows,'blankCanvasProof':own_text_hashes()[1],'titles':json.loads((W/'title-verification.json').read_text(encoding='utf8')),'fontsAndSubtitles':'Existing independently produced Korean pages retained without AI processing','opening':'Existing original-game-based Korean opening artwork retained','bulkUIUpscale':False})
 readme='''# 한국어 패치 — Independent Anime 1440p 로컬 검토판\n\n게임 원본과 직접 만든 한국어 자료로 제작한 이미지입니다. UnleasHD 원본 또는 UnleasHD를 수정한 이미지를 포함하지 않습니다.\n\n1. 기본판과 전체판 중 하나만 설치합니다. 전체판은 기존 EXE 한국어화 도구를 추가로 포함합니다.\n2. 게임 화면 언어를 English, 자막을 켜기로 설정합니다. DLC 선택은 실제 설치 내용에 맞춥니다.\n3. UnleasHD 1.4.2 1440p를 함께 쓰면 HMM에서 한국어 패치 → UnleasHD 순서로 놓습니다.\n4. 한국어 패치 설정에서 ‘업스케일 한국어 이미지 → 켜기 — 독립 업스케일 / UnleasHD 1440p 호환’을 선택합니다. 함께 사용하지 않으면 끄기를 선택합니다.\n5. 저장 후 게임을 완전히 다시 시작합니다. 한국어 타이틀·오프닝 로고는 로고 설정에서 선택합니다.\n\n한국어 UI·이름표 16종과 타이틀·발광 4종, 총 20종을 22곳에 적용합니다. anime 모델은 게임 원본 그림에만 사용했고 한글은 직접 합성했습니다. 글꼴·자막·원본 기반 오프닝 로고는 기존 자체 제작 자료를 유지합니다. 번역하지 않은 영어 HUD·버튼·아이콘은 포함하지 않으며, 별도로 설치한 UnleasHD 또는 게임 원본에서 읽습니다. 배경·캐릭터·사물은 변경하지 않습니다. 전체 UI 일괄 확대 테스트는 포함하지 않습니다.\n\n실제 플레이 검증은 진행 중입니다. 게임 원본과 글꼴 등의 별도 권리·라이선스는 유지됩니다. UnleasHD 이미지 미포함은 게임 자산 전체의 자유 배포 권한을 뜻하지 않습니다.\n'''
 (M/'README-KO.md').write_text(readme,encoding='utf8')
 (M/'README-EN.md').write_text('Independent Korean-only anime UI build. Images use game originals and own Korean artwork, not UnleasHD images or derivatives. Enable the optional 1440p upscaled Korean images when using separately installed UnleasHD. Load Korean patch above UnleasHD. Other UI is provided by that mod or the game. Existing game and font rights remain applicable.\n',encoding='utf8')
 (M/'CREDITS.md').write_text('Korean translation and composition: nonunsaram project. Original art: Sonic Unleashed game assets. Upscaling: Real-ESRGAN x4plus-anime. Fonts: see Licenses. UnleasHD is an optional separately installed compatibility target; no UnleasHD artwork is included.\n',encoding='utf8')
 from independent_option_paths import ensure_option_directories
 ensure_option_directories(M)
 result=verify(M);dump(W/'payload-verification.json',result)
 # Full-only installer files are existing translation setup resources, not UI-mod art.
 fullsource=R/'outputs/KoreanOnly-HD1440-20261003/UnleashedRecompiled-Korean-1.0.5-Review16-1440p-Full.zip'
 with zipfile.ZipFile(fullsource) as z:
  extras={n:z.read(n) for n in z.namelist() if n.startswith('UnleashedKorean/Support/') or n=='UnleashedKorean/KoreanFullSetup.exe'}
 assert extras and 'UnleashedKorean/KoreanFullSetup.exe' in extras
 for edition in ['Basic','Full']:
  dest=O/f'UnleashedRecompiled-Korean-Independent-Anime1440-{edition}.zip'
  with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
   for p in M.rglob('*'):
    if p.is_file():z.writestr('UnleashedKorean/'+p.relative_to(M).as_posix(),ini(edition) if p.name=='mod.ini' else p.read_bytes())
   if edition=='Full':
    for n,b in extras.items():z.writestr(n,b)
    # Source documentation only; do not carry over the old bundled images or old release archives.
    sink=io.BytesIO()
    with zipfile.ZipFile(sink,'w',zipfile.ZIP_DEFLATED) as source:
     for p in [R/'Scripts/build_independent_anime_release.py',M/'Independent-image-provenance.json',M/'Independent-image-provenance.csv']:source.write(p,'Source/'+p.name)
    z.writestr('UnleashedKorean/Source.zip',sink.getvalue())
  # Inspect the actual packaged bytes immediately; extracting into a new verification folder.
  check=W/'zip-check'/edition
  with zipfile.ZipFile(dest) as z:
   assert z.testzip() is None;z.extractall(check)
  try:verify(check/'UnleashedKorean')
  except Exception:dest.rename(dest.with_name(dest.stem+'-FAILED.zip'));raise
 dump(O/'verification.json',result)
 (O/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(O.glob('*.zip'))),encoding='ascii')
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
