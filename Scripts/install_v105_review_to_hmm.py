"""Install the local v1.0.5 review changes into the existing HMM Full mod.

The original Full mod and its options are backed up and preserved.
"""
from __future__ import annotations
import configparser, hashlib, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'Build/Development-v104-Final/UnleashedKorean'
PATCH=ROOT/'Build/Development-v105-Review/UnleashedKorean'
INSTALLED=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
BACKUP=ROOT/'Build/HMM-Backup-v104-20260925/UnleashedKorean'
REPORT=ROOT/'Build/HMM-Install-v105-Review/verification.json'
VARIANTS={'BaseGame':'BaseGame','Apotos & Shamar Adventure Pack':'ApotosShamar','Chun-nan Adventure Pack':'ChunNan','Empire City & Adabat Adventure Pack':'AllDLC','Holoska Adventure Pack':'Holoska','Mazuri Adventure Pack':'Mazuri','Spagonia Adventure Pack':'Spagonia'}
def sha(path): return hashlib.sha256(path.read_bytes()).digest()
def ini(path):
 d=configparser.ConfigParser(interpolation=None);d.read(path,encoding='utf-8-sig');return d

def main():
 assert BASE.is_dir() and PATCH.is_dir() and INSTALLED.is_dir() and not BACKUP.exists() and not REPORT.exists()
 old=ini(INSTALLED/'mod.ini')
 assert old['Desc']['Version'].strip('"')=='1.0.4'
 assert '전체판' in old['Desc']['Title']
 assert old['Main']['IncludeDir2'].strip('"')=='Compatibility/UnleasHD-1.4.2'
 assert old['Main']['IncludeDir3'].strip('"')=='TitleLogos/Korean'
 assert (INSTALLED/'KoreanFullSetup.exe').is_file()
 report=json.loads((ROOT/'Translation/review/proper-name-audit-v105/resource-verification.json').read_text(encoding='utf8'))
 affected=[]
 for group in report['archives']:
  name=group['archive'];stem='WorldMap' if name=='WorldMap' else '+'+name
  parent=(Path('WorldMapVariants')/VARIANTS[group['package']]/'Languages/English' if name=='WorldMap' else Path('Languages/English'))
  affected += [p.relative_to(BASE) for p in (BASE/parent).glob(stem+'.ar.*')]
  affected.append(parent/(stem+'.arl'))
 assert len(affected)==40 and len(set(affected))==40
 for rel in affected:
  assert (INSTALLED/rel).is_file() and sha(INSTALLED/rel)==sha(BASE/rel),rel
  assert (PATCH/rel).is_file()
 overlay=ROOT/'Build/UnleasHD-Compatibility-v105-HUD2/Overlay/Languages/English'
 new_files=[]
 for source in overlay.iterdir():
  if source.is_file():
   rel=Path('Compatibility/UnleasHD-1.4.2/Languages/English')/source.name
   assert not (INSTALLED/rel).exists() and sha(source)==sha(PATCH/rel)
   new_files.append(rel)
 assert len(new_files)==29
 BACKUP.parent.mkdir(parents=True,exist_ok=True)
 shutil.copytree(INSTALLED,BACKUP)
 assert sha(BACKUP/'mod.ini')==sha(INSTALLED/'mod.ini')
 changed=[]
 try:
  for rel in affected:
   shutil.copy2(PATCH/rel,INSTALLED/rel);changed.append(rel)
  for rel in new_files:
   target=INSTALLED/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PATCH/rel,target);changed.append(rel)
  modini=INSTALLED/'mod.ini';text=modini.read_text(encoding='utf-8-sig')
  assert 'Version="1.0.4"' in text
  text=text.replace('Version="1.0.4"','Version="1.0.5-review"',1)
  text=text.replace('Date="2026-09-16"','Date="2026-09-25"',1)
  modini.write_text(text,encoding='utf8');changed.append(Path('mod.ini'))
  config=INSTALLED/'ConfigSchema.json';data=json.loads(config.read_text(encoding='utf8'))
  options=[x for group in data['Groups'] for x in group['Elements'] if x['Name']=='IncludeDir2']
  assert len(options)==1
  options[0]['Description']=['UnleasHD 1.4.2 (1440p) 설치 시 선택하세요.','한국어 패치를 UnleasHD보다 위에 두고 저장한 뒤 게임을 다시 시작하세요.','월드맵과 HUD·결과 화면 등의 고해상도 UI 호환 파일을 적용합니다.']
  config.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');changed.append(Path('ConfigSchema.json'))
  for name in ('README-1.0.5-REVIEW-KO.md','NAME-AUDIT-KO.md'):
   rel=Path(name);assert not (INSTALLED/rel).exists();shutil.copy2(PATCH/rel,INSTALLED/rel);changed.append(rel)
  for rel in affected+new_files: assert sha(INSTALLED/rel)==sha(PATCH/rel),rel
  now=ini(INSTALLED/'mod.ini')
  assert now['Desc']['Version'].strip('"')=='1.0.5-review'
  assert now['Main']['IncludeDir0']==old['Main']['IncludeDir0']
  assert now['Main']['IncludeDir2']==old['Main']['IncludeDir2']
  assert now['Main']['IncludeDir3']==old['Main']['IncludeDir3']
  assert (INSTALLED/'KoreanFullSetup.exe').is_file() and sha(INSTALLED/'KoreanFullSetup.exe')==sha(BACKUP/'KoreanFullSetup.exe')
  REPORT.parent.mkdir(parents=True,exist_ok=True)
  result={'passed':True,'installedMod':str(INSTALLED),'backup':str(BACKUP),'version':'1.0.5-review','edition':'Full',
          'wangArchiveFilesUpdated':len(affected),'hdArchiveFilesAdded':len(new_files),'oldSettingsPreserved':True,
          'fullInstallerPreserved':True,'gameplayVerified':False}
  REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  print(json.dumps(result,ensure_ascii=False))
 except Exception:
  for rel in new_files+[Path('README-1.0.5-REVIEW-KO.md'),Path('NAME-AUDIT-KO.md')]:
   target=INSTALLED/rel
   if target.is_file():target.unlink()
  shutil.copytree(BACKUP,INSTALLED,dirs_exist_ok=True)
  raise
if __name__=='__main__':main()
