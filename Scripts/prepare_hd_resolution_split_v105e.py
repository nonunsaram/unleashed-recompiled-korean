"""Create a 720p/HD selectable Korean UI candidate from review4."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

from bounded_archive_tool import unpack
from build_unleashhd_ui_compat_v105 import draw_korean, members

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'Build/Development-v105d-Playtest/UnleashedKorean'
NEW = ROOT / 'Build/Development-v105e-Playtest/UnleashedKorean'
WORK = ROOT / 'Build/Review5-ResolutionSplit/ArchiveWork'
GLYPHS = ROOT / 'Build/Review5-ResolutionSplit/HdGlyphPages'
INVENTORY = ROOT / 'Translation/review/unleashhd-v105d/resolution-inventory.json'
LABELS = ROOT / 'Translation/review/unleashhd-v105/ui-textures-ko-v104-full.json'
TITLE_NAME = 'mat_title_en_002.dds'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pack_folder(folder: Path) -> None:
    subprocess.run([str(ROOT/'Tools/HedgeArcPack/HedgeArcPack.exe'), str(folder)],
                   input='hh\n', text=True, capture_output=True, check=True, timeout=30,
                   creationflags=subprocess.CREATE_NO_WINDOW)


def title_texture() -> Path:
    labels=json.loads(LABELS.read_text(encoding='utf8'))['labels']
    selected=[label for label in labels if label['texture']==24]
    assert len(selected)==6
    source=ROOT/'Build/Review5-ResolutionSplit/OtherUI/+Title'/TITLE_NAME
    with Image.open(source) as original: assert original.size==(128,256)
    blank=Image.new('RGBA',(256,512),(0,0,0,0))
    rendered,count=draw_korean(blank,selected,24,None,2)
    assert count==6 and rendered.size==(256,512)
    output=WORK/TITLE_NAME
    rendered.save(output,pixel_format='DXT5')
    rendered.save(WORK/'title-language-hd-preview.png')
    with Image.open(output) as reopened: assert reopened.size==(256,512)
    return output


def main() -> None:
    assert OLD.is_dir() and GLYPHS.is_dir() and not NEW.exists() and not WORK.exists()
    render=json.loads((GLYPHS.parent/'glyph-render-verification.json').read_text(encoding='utf8'))
    assert render['passed'] and render['sourcePagesByteIdentical']==8 and render['uvLayoutPreserved']
    inventory=json.loads(INVENTORY.read_text(encoding='utf8'))
    pages=defaultdict(set)
    for row in inventory['rows']:
        if row['kind']=='korean-glyph':
            assert row['baseSize']==[512,512] and not row['hasHdOverride']
            pages[row['archive']].add(row['file'])
    assert len(pages)==14 and sum(map(len,pages.values()))==106
    assert set.union(*pages.values())=={f'fte_Korean_{i:03}.dds' for i in range(8)}
    shutil.copytree(OLD,NEW)
    WORK.mkdir(parents=True)
    extra_title=title_texture()
    compat=NEW/'Compatibility/UnleasHD-1.4.2/Languages/English'
    results=[]
    for archive in sorted(set(pages)|{'Title'}):
        stem='+'+archive
        input_archive=compat/(stem+'.ar.00')
        area=WORK/archive
        area.mkdir()
        folder=area/stem
        if input_archive.is_file():
            for part in input_archive.parent.glob(stem+'.ar.*'):
                shutil.copy2(part,area/part.name)
            unpack(area/input_archive.name)
            assert folder.is_dir()
        else:
            folder.mkdir()
        before={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
        added=pages.get(archive,set()) if archive!='Title' else {TITLE_NAME}
        assert not (set(before)&added)
        for name in sorted(added):
            shutil.copy2(extra_title if name==TITLE_NAME else GLYPHS/name,folder/name)
        pack_folder(folder)
        expected=set(before)|added
        assert members(area/(stem+'.arl'))==expected
        for part in [area/(stem+'.arl'),*sorted(area.glob(stem+'.ar.*'))]:
            shutil.copy2(part,compat/part.name)
        check=WORK/'RoundTrip'/archive/(stem+'.ar.00')
        check.parent.mkdir(parents=True)
        for part in compat.glob(stem+'.ar.*'):
            shutil.copy2(part,check.parent/part.name)
        unpack(check)
        actual={p.name:p for p in (check.parent/stem).iterdir() if p.is_file()}
        assert set(actual)==expected
        assert all(sha(actual[name])==digest for name,digest in before.items())
        assert all(sha(actual[name])==sha(folder/name) for name in added)
        for name in added:
            with Image.open(actual[name]) as image:
                assert image.size==((256,512) if name==TITLE_NAME else (1024,1024))
        results.append({'archive':archive,'preserved':len(before),'added':sorted(added)})
    ini_path=NEW/'mod.ini'
    ini=ini_path.read_text(encoding='utf-8-sig')
    assert ini.count('Version="1.0.5-review4"')==1
    ini_path.write_text(ini.replace('Version="1.0.5-review4"','Version="1.0.5-review5"',1),encoding='utf8')
    schema_path=NEW/'ConfigSchema.json'
    schema=json.loads(schema_path.read_text(encoding='utf8'))
    option=next(e for group in schema['Groups'] for e in group['Elements'] if e['Type']=='UnleasHDCompatibility')
    assert option['Name']=='IncludeDir1' and option['Value']=='Compatibility/None'
    option['DisplayName']='한국어 UI 해상도'
    option['Description']=[
        '기본은 원본 UI 크기에 맞춘 한국어 이미지입니다.',
        'UnleasHD 1.4.2 (1440p)를 설치했다면 HD 한국어 UI를 선택하세요.',
        '화면 해상도 자체를 바꾸지 않으며, 고해상도 글자·HUD·상점·타이틀 이미지를 적용합니다.',
    ]
    choices=schema['Enums']['UnleasHDCompatibility']
    assert [x['Value'] for x in choices]==['Compatibility/None','Compatibility/UnleasHD-1.4.2']
    choices[0]['DisplayName']='기본 UI (720p용)'
    choices[1]['DisplayName']='UnleasHD UI (1440p용)'
    schema_path.write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    readme_path=NEW/'README-1.0.5-REVIEW-KO.md'
    readme=readme_path.read_text(encoding='utf8')
    assert '# 한국어 패치 1.0.5-review4 플레이 테스트 후보' in readme
    readme=readme.replace('# 한국어 패치 1.0.5-review4 플레이 테스트 후보',
                          '# 한국어 패치 1.0.5-review5 플레이 테스트 후보',1)
    readme+=('\n한국어 UI 해상도를 기본(720p용)과 UnleasHD(1440p용)로 나누었습니다. '
             '공통 대사·이름·설정은 동일하고 HD 선택 시에만 한국어 글자 페이지 106장(공통 원본 8장)을 '
             '1024×1024로, 타이틀 언어 선택 화면을 256×512로 덮어씁니다. '
             '일본어 원본 글자 페이지는 글꼴·배치가 달라 유지했습니다.\n')
    readme_path.write_text(readme,encoding='utf8')
    report={'passed':True,'version':'1.0.5-review5','profileNames':['720p','UnleasHD-1440p'],
            'newHdKoreanGlyphAtlases':106,'uniqueHdKoreanGlyphAtlases':8,
            'newHdTitleLanguageAtlases':1,'compatArchivesTouched':len(results),
            'archiveResults':results,'gameplayVerified':False,'publicRelease':False}
    output=NEW.parent/'verification.json'
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='archiveResults'},ensure_ascii=False))


if __name__=='__main__': main()
