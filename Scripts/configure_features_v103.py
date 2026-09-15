"""Configure the playable v103 review; the experimental Korean Unleashed logo is withdrawn."""
from pathlib import Path
import json,shutil,hashlib,re,configparser
R=Path(__file__).resolve().parents[1]
LABELS={
 'TitleLogos/Default':'게임 기본값',
 'TitleLogos/Original':'소닉 언리쉬드 (영문 원본)',
 'TitleLogos/Japanese':'소닉 월드 어드벤처 (일본어 원본)',
 'TitleLogos/Custom':'소닉 월드 어드벤처 (한국어 편집)'}
def configure(root):
 root=Path(root).resolve();assert root.is_relative_to(R.resolve())
 p=root/'ConfigSchema.json';schema=json.loads(p.read_text(encoding='utf-8-sig'))
 values={v['Value'] for v in schema['Enums']['TitleLogoVariant']}
 options=[{'DisplayName':label,'Value':value,'Description':['일본어판 로고의 상단 문구를 한국어로 편집한 로고입니다.'] if value.endswith('/Custom') else []} for value,label in LABELS.items() if value in values]
 assert len(options)>=3
 schema['Enums']['TitleLogoVariant']=options
 element=next(e for g in schema['Groups'] for e in g['Elements'] if e.get('Name')=='IncludeDir3')
 element['Description']=['한국어 메뉴를 유지하면서 타이틀 로고를 선택합니다.',
  '한국어 편집은 일본어판 로고의 상단 문구를 한국어로 표시합니다.',
  '게임 기본값은 기존 로고 설정을 따릅니다. 로고 모드를 함께 쓰면 한국어 패치를 위에 두세요.']
 ini_path=root/'mod.ini';text=ini_path.read_text(encoding='utf-8-sig')
 ini=configparser.ConfigParser(interpolation=None);ini.optionxform=str;ini.read_string(text)
 current=ini['Main'].get('IncludeDir3','"TitleLogos/Default"').strip('"')
 allowed={v['Value'] for v in options}
 if current not in allowed:
  current='TitleLogos/Custom' if 'TitleLogos/Custom' in allowed else 'TitleLogos/Original'
  text,count=re.subn(r'(?m)^IncludeDir3=.*$',f'IncludeDir3="{current}"',text);assert count==1
  ini_path.write_text(text,encoding='utf8')
 element['Value']=current
 if element.get('DefaultValue') not in allowed:element['DefaultValue']='TitleLogos/Default'
 p.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 # Keep the rejected artwork for community handoff, outside any loadable mod directory.
 excluded=(root/'TitleLogos/KoreanOfficial').resolve()
 if excluded.exists():
  stash=(R/'Build/TitleLogo-v103/ExcludedFromPlayable'/hashlib.sha256(str(root).encode()).hexdigest()[:10]).resolve()
  assert excluded.is_relative_to(root) and stash.is_relative_to(R.resolve())
  stash.mkdir(parents=True,exist_ok=True);destination=stash/'KoreanOfficial'
  n=1
  while destination.exists():destination=stash/f'KoreanOfficial-{n}';n+=1
  shutil.move(str(excluded),str(destination))
 assert 'KoreanOfficial' not in p.read_text(encoding='utf8')
 assert '언리시드' not in p.read_text(encoding='utf8')
 return schema
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('mod_root',type=Path)
 configure(parser.parse_args().mod_root)