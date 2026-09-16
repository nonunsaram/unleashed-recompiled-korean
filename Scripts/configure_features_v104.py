"""Configure the five approved v1.0.4 title choices, preserving the current selection."""
from pathlib import Path
import json, configparser, re
LABELS={'Default':'게임 기본값','Original':'소닉 언리쉬드 (영어 원본)','Korean':'소닉 언리쉬드 (한국어 추가)','Japanese':'소닉 월드 어드벤처 (일본어 원본)','Custom':'소닉 월드 어드벤처 (한국어 추가)'}

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

if __name__=="__main__":
 import argparse
 p=argparse.ArgumentParser();p.add_argument("mod_root",type=Path)
 configure(p.parse_args().mod_root)
