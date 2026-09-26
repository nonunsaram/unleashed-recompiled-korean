"""Add HD WorldMap and cutscene Korean pages to the selectable HD variant."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

from PIL import Image

from bounded_archive_tool import unpack
from build_unleashhd_ui_compat_v105 import members

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'Build/Development-v105e-Playtest/UnleashedKorean'
NEW=ROOT/'Build/Development-v105f-Playtest/UnleashedKorean'
WORK=ROOT/'Build/Review6-ResolutionSplit/ArchiveWork'
HD_GLYPHS=ROOT/'Build/Review5-ResolutionSplit/HdGlyphPages'
HD_CUTSCENES=ROOT/'Build/Review6-ResolutionSplit/HdCutscenePages'
HD_TAILS=ROOT/'Build/Review4-TailsHD/Check/+ExStageTails_Common'


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pack(folder:Path)->None:
    subprocess.run([str(ROOT/'Tools/HedgeArcPack/HedgeArcPack.exe'),str(folder)],
                   input='hh\n',text=True,capture_output=True,check=True,timeout=30,
                   creationflags=subprocess.CREATE_NO_WINDOW)


def update_archive(relative_dir:Path,stem:str,add:dict[str,Path])->dict:
    destination=NEW/relative_dir
    area=WORK/relative_dir/stem
    area.mkdir(parents=True)
    folder=area/stem
    old=destination/(stem+'.ar.00')
    if old.is_file():
        for part in destination.glob(stem+'.ar.*'):
            shutil.copy2(part,area/part.name)
        unpack(area/old.name)
    else:
        folder.mkdir()
    before={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
    assert not (set(before)&set(add))
    for name,source in add.items():
        assert source.is_file()
        shutil.copy2(source,folder/name)
        with Image.open(folder/name) as image:assert image.size==(1024,1024)
    pack(folder)
    expected=set(before)|set(add)
    assert members(area/(stem+'.arl'))==expected
    destination.mkdir(parents=True,exist_ok=True)
    for part in [area/(stem+'.arl'),*sorted(area.glob(stem+'.ar.*'))]:
        shutil.copy2(part,destination/part.name)
    check=WORK/'RoundTrip'/relative_dir/stem/(stem+'.ar.00')
    check.parent.mkdir(parents=True)
    for part in destination.glob(stem+'.ar.*'):
        shutil.copy2(part,check.parent/part.name)
    unpack(check)
    actual={p.name:p for p in (check.parent/stem).iterdir() if p.is_file()}
    assert set(actual)==expected
    assert all(sha(actual[name])==digest for name,digest in before.items())
    assert all(sha(actual[name])==sha(add[name]) for name in add)
    return {'path':relative_dir.as_posix()+'/'+stem,'preserved':len(before),'added':len(add)}


def main()->None:
    assert OLD.is_dir() and not NEW.exists() and not WORK.exists()
    cut=json.loads((HD_CUTSCENES.parent/'cutscene-hd-render-verification.json').read_text(encoding='utf8'))
    assert cut['passed'] and cut['pages']==44 and cut['redrawnHangul']==2905
    tails=[HD_TAILS/'evex_ex00_event_000.dds',HD_TAILS/'evex_ex01_event_000.dds']
    assert all(x.is_file() for x in tails)
    shutil.copytree(OLD,NEW)
    WORK.mkdir(parents=True)
    results=[]
    world={f'fte_Korean_{i:03}.dds':HD_GLYPHS/f'fte_Korean_{i:03}.dds' for i in range(7)}
    results.append(update_archive(Path('Compatibility/UnleasHD-1.4.2/Languages/English'),'+WorldMap',world))
    cutscene_jobs=defaultdict(dict)
    for page in cut['pagesDetail']:
        archive=page['archive'];name=page['texture']
        cutscene_jobs[archive][name]=HD_CUTSCENES/archive/name
    assert len(cutscene_jobs)==42 and sum(len(x) for x in cutscene_jobs.values())==44
    cutscene_jobs['ExStageTails_Common']={p.name:p for p in tails}
    assert len(cutscene_jobs)==43 and sum(len(x) for x in cutscene_jobs.values())==46
    for archive,files in sorted(cutscene_jobs.items()):
        results.append(update_archive(Path('Compatibility/UnleasHD-1.4.2/Inspire/subtitle/English'),
                                      '+'+archive,files))
    ini_path=NEW/'mod.ini'
    ini=ini_path.read_text(encoding='utf-8-sig')
    assert ini.count('Version="1.0.5-review5"')==1
    ini_path.write_text(ini.replace('Version="1.0.5-review5"','Version="1.0.5-review6"',1),encoding='utf8')
    readme_path=NEW/'README-1.0.5-REVIEW-KO.md'
    readme=readme_path.read_text(encoding='utf8')
    assert '# 한국어 패치 1.0.5-review5 플레이 테스트 후보' in readme
    readme=readme.replace('# 한국어 패치 1.0.5-review5 플레이 테스트 후보',
                          '# 한국어 패치 1.0.5-review6 플레이 테스트 후보',1)
    readme+=('\nHD 선택 시 DLC별 월드맵의 한국어 글자 7장을 1024×1024 아틀라스로 덮어씁니다. '
             '컷신 전용 경로의 한국어 자막 46장도 1024×1024로 공급합니다. '
             '원래 글꼴과 맞는 한글 2,905자를 다시 그렸고, 글꼴이 다른 영문·기호 일부는 원본 모양을 확대 보존했습니다. '
             '테일즈 자막은 일반 언어 경로와 컷신 전용 경로 모두에 HD 파일이 들어 있습니다. '
             '일본어 원본 글자 페이지는 별도 작업 대상입니다. 실제 게임에서 월드맵·컷신 표시를 확인해 주십시오.\n')
    readme_path.write_text(readme,encoding='utf8')
    report={'passed':True,'version':'1.0.5-review6','profileNames':['720p','UnleasHD-1440p'],
            'hdCommonKoreanGlyphAtlases':106,'hdWorldMapKoreanGlyphAtlases':7,
            'worldMapVariantCount':7,'hdCutsceneAtlases':46,'hdCutsceneRedrawnHangul':2905,
            'hdArchivesAddedOrUpdated':len(results),'archiveResults':results,
            'gameplayVerified':False,'publicRelease':False}
    (NEW.parent/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='archiveResults'},ensure_ascii=False))


if __name__=='__main__':main()
