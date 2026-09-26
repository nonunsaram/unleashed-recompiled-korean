"""Add the last Korean root UI sprite to the selectable HD layer."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from bounded_archive_tool import unpack
from build_unleashhd_ui_compat_v105 import members

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'Build/Development-v105f-Playtest/UnleashedKorean'
NEW=ROOT/'Build/Development-v105g-Playtest/UnleashedKorean'
WORK=ROOT/'Build/Review7-ResolutionSplit/ArchiveWork'
SOURCE=ROOT/'Build/Review7-ResolutionSplit/HdNameplate/mat_talk_comon_002.dds'
STEM='+Town_Common'


def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def main()->None:
    verified=json.loads((SOURCE.parent/'verification.json').read_text(encoding='utf8'))
    assert verified['passed'] and verified['outsideNamesPreserved']
    assert OLD.is_dir() and not NEW.exists() and not WORK.exists()
    shutil.copytree(OLD,NEW)
    folder=WORK/STEM
    folder.mkdir(parents=True)
    shutil.copy2(SOURCE,folder/SOURCE.name)
    subprocess.run([str(ROOT/'Tools/HedgeArcPack/HedgeArcPack.exe'),str(folder)],
                   input='hh\n',text=True,capture_output=True,check=True,timeout=30,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    assert members(WORK/(STEM+'.arl'))=={SOURCE.name}
    compat=NEW/'Compatibility/UnleasHD-1.4.2'
    for file in (WORK/(STEM+'.arl'),*sorted(WORK.glob(STEM+'.ar.*'))):
        shutil.copy2(file,compat/file.name)
    check=WORK/'RoundTrip'/(STEM+'.ar.00')
    check.parent.mkdir()
    for part in compat.glob(STEM+'.ar.*'):
        shutil.copy2(part,check.parent/part.name)
    unpack(check)
    actual=check.parent/STEM/SOURCE.name
    assert sha(actual)==sha(SOURCE)
    with Image.open(actual) as image:assert image.size==(512,512)
    assert sha(NEW/(STEM+'.ar.00'))==sha(OLD/(STEM+'.ar.00'))
    ini_path=NEW/'mod.ini';ini=ini_path.read_text(encoding='utf-8-sig')
    assert ini.count('Version="1.0.5-review6"')==1
    ini_path.write_text(ini.replace('Version="1.0.5-review6"','Version="1.0.5-review7"',1),encoding='utf8')
    readme_path=NEW/'README-1.0.5-REVIEW-KO.md'
    readme=readme_path.read_text(encoding='utf8')
    assert '# 한국어 패치 1.0.5-review6 플레이 테스트 후보' in readme
    readme=readme.replace('# 한국어 패치 1.0.5-review6 플레이 테스트 후보',
                          '# 한국어 패치 1.0.5-review7 플레이 테스트 후보',1)
    readme+='\nHD 선택 경로의 대화 이름표도 512×512로 보완해 소닉·테일즈·칩 세 이름을 고해상도로 표시합니다.\n'
    readme_path.write_text(readme,encoding='utf8')
    result={'passed':True,'version':'1.0.5-review7','hdNameplateSize':[512,512],
            'base720NameplatePreserved':True,'koreanNames':3,
            'gameplayVerified':False,'publicRelease':False}
    (NEW.parent/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
