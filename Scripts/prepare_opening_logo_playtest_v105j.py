"""Prepare a local review10 Basic candidate with both Korean opening overlays."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Build/Development-v105i-Playtest/UnleashedKorean'
OUTPUT = ROOT / 'Build/Development-v105j-Playtest/UnleashedKorean'
ASSETS = ROOT / 'Build/OPLogoInvestigation/Variants'
ZIP = ROOT / 'outputs/UnleashedRecompiled-Korean-1.0.5-Review10-LocalPlaytest.zip'
VARIANTS = ('Korean','Custom')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def patch_schema(path: Path) -> None:
    schema=json.loads(path.read_text(encoding='utf-8-sig'))
    for entry in schema['Enums']['TitleLogoVariant']:
        if entry['Value'] in {'TitleLogos/Korean','TitleLogos/Custom'}:
            entry['Description'] = [
                '고해상도 타이틀 로고와 한국어 오프닝 로고를 함께 적용합니다. '
                'UnleasHD를 별도로 설치하지 않아도 됩니다.'
            ]
    element=next(e for g in schema['Groups'] for e in g['Elements'] if e.get('Name')=='IncludeDir3')
    element['DisplayName']='타이틀·오프닝 로고'
    element['Description']=[
        '게임 기본값은 로고를 덮어쓰지 않고 기존 게임·모드 설정을 따릅니다.',
        '한국어 추가 두 가지를 선택하면 같은 디자인이 타이틀 화면과 오프닝에 적용됩니다.',
        '다른 로고 모드를 함께 쓰면 한국어 패치를 위에 두고 저장한 뒤 게임을 다시 시작하세요.'
    ]
    path.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def main() -> None:
    assert SOURCE.is_dir() and ASSETS.is_dir()
    assert not OUTPUT.exists() and not ZIP.exists()
    build=json.loads((ASSETS.parent/'build-report.json').read_text(encoding='utf8'))
    assert all(build[v]['decodedDdsRoundTrip'] for v in VARIANTS)
    shutil.copytree(SOURCE,OUTPUT)
    changed=[]
    for variant in VARIANTS:
        for language in ('EN','JP'):
            rel=Path('TitleLogos')/variant/'Loading'/f'OPmovie_titlelogo_{language}.dds'
            target=OUTPUT/rel
            assert not target.exists()
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ASSETS/variant/'Loading'/target.name,target)
            assert digest(target)==build[variant][f'{language}sha256']
            changed.append(rel.as_posix())
    ini=OUTPUT/'mod.ini';old=ini.read_text(encoding='utf-8-sig')
    assert old.count('Version="1.0.5-review9"')==1
    ini.write_text(old.replace('Version="1.0.5-review9"','Version="1.0.5-review10"',1),encoding='utf8')
    patch_schema(OUTPUT/'ConfigSchema.json')
    readme=OUTPUT/'README-1.0.5-REVIEW-KO.md'
    contents=readme.read_text(encoding='utf8')
    assert contents.startswith('# 한국어 패치 1.0.5-review9 플레이 테스트 후보')
    contents=contents.replace('# 한국어 패치 1.0.5-review9 플레이 테스트 후보',
                              '# 한국어 패치 1.0.5-review10 플레이 테스트 후보',1)
    contents += ('\n오프닝의 로고도 타이틀 로고 선택을 따릅니다. '
                 '소닉 언리쉬드·소닉 월드 어드벤처 한국어 추가를 선택하면 '
                 '각 디자인의 한국어 오프닝 로고를 표시합니다. '
                 '오프닝 영상 파일 자체는 변경하지 않았습니다.\n')
    readme.write_text(contents,encoding='utf8')
    old_files={p.relative_to(SOURCE).as_posix():digest(p) for p in SOURCE.rglob('*') if p.is_file()}
    new_files={p.relative_to(OUTPUT).as_posix():digest(p) for p in OUTPUT.rglob('*') if p.is_file()}
    allowed=set(changed)|{'mod.ini','ConfigSchema.json','README-1.0.5-REVIEW-KO.md'}
    assert {p for p in new_files if new_files[p]!=old_files.get(p)}==allowed
    assert all(new_files[p]==h for p,h in old_files.items() if p not in allowed)
    files=sorted(p for p in OUTPUT.rglob('*') if p.is_file())
    with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for p in files:
            archive.write(p,'UnleashedKorean/'+p.relative_to(OUTPUT).as_posix())
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None and len(archive.namelist())==len(files)
    result={'passed':True,'version':'1.0.5-review10','edition':'Basic',
            'openingVariants':list(VARIANTS),'filesAdded':changed,'otherAssetsPreserved':True,
            'zip':str(ZIP),'zipSha256':digest(ZIP),'gameplayVerified':False,'publicRelease':False}
    (OUTPUT.parent/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__': main()
