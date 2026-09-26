"""Check review6 HD WorldMap/cutscene overlays and unchanged 720p assets."""
from __future__ import annotations

import configparser
import hashlib
import json
import struct
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'Build/Development-v105e-Playtest/UnleashedKorean'
NEW=ROOT/'Build/Development-v105f-Playtest/UnleashedKorean'
CUT=ROOT/'Build/Review6-ResolutionSplit/HdCutscenePages'
ROUND=ROOT/'Build/Review6-ResolutionSplit/ArchiveWork/RoundTrip'
MAP=ROOT/'Build/Review6-ResolutionSplit/cutscene-atlas-maps.json'
TAILS=ROOT/'Build/Review4-TailsHD/Check/+ExStageTails_Common'
GLYPHS=ROOT/'Build/Review5-ResolutionSplit/HdGlyphPages'


def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root:Path)->dict[str,Path]:
    return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}


def members(path:Path)->set[str]:
    data=path.read_bytes();assert data[:4]==b'ARL2'
    pos=8+4*struct.unpack_from('<I',data,4)[0];out=set()
    while pos<len(data):
        size=data[pos];pos+=1
        name=data[pos:pos+size].decode('utf8');pos+=size
        assert name not in out;out.add(name)
    assert pos==len(data);return out


def main()->None:
    before,after=inventory(OLD),inventory(NEW)
    assert set(before)<=set(after)
    changed={x for x in before if sha(before[x])!=sha(after[x])}
    added=set(after)-set(before)
    prefix='Compatibility/UnleasHD-1.4.2/'
    assert changed=={'mod.ini','README-1.0.5-REVIEW-KO.md',
                     *{x for x in changed if x.startswith(prefix)}}
    assert all(x.startswith(prefix) for x in added)
    assert all(sha(before[x])==sha(after[x]) for x in before if not x.startswith(prefix) and x not in ('mod.ini','README-1.0.5-REVIEW-KO.md'))
    assert sha(OLD/'ConfigSchema.json')==sha(NEW/'ConfigSchema.json')
    config=configparser.ConfigParser(interpolation=None)
    config.read(NEW/'mod.ini',encoding='utf-8-sig')
    assert config['Desc']['Version'].strip('"')=='1.0.5-review6'
    assert config['Main']['IncludeDir1'].strip('"')=='Compatibility/None'
    world_archive=NEW/'Compatibility/UnleasHD-1.4.2/Languages/English/+WorldMap.arl'
    world=members(world_archive)
    assert {f'fte_Korean_{i:03}.dds' for i in range(7)}<=world
    world_folder=ROUND/'Compatibility/UnleasHD-1.4.2/Languages/English/+WorldMap/+WorldMap'
    for i in range(7):
        name=f'fte_Korean_{i:03}.dds'
        assert sha(world_folder/name)==sha(GLYPHS/name)
        with Image.open(world_folder/name) as image:assert image.size==(1024,1024)
    pages=json.loads(MAP.read_text(encoding='utf-8-sig'))
    assert len(pages)==44
    for page in pages:
        archive=page['archive'];name=page['texture']
        arl=NEW/'Compatibility/UnleasHD-1.4.2/Inspire/subtitle/English'/('+'+archive+'.arl')
        assert name in members(arl)
        extracted=ROUND/'Compatibility/UnleasHD-1.4.2/Inspire/subtitle/English'/('+'+archive)/('+'+archive)/name
        assert sha(extracted)==sha(CUT/archive/name)
        with Image.open(extracted) as image:assert image.size==(1024,1024)
    for name in ('evex_ex00_event_000.dds','evex_ex01_event_000.dds'):
        extracted=ROUND/'Compatibility/UnleasHD-1.4.2/Inspire/subtitle/English/+ExStageTails_Common/+ExStageTails_Common'/name
        assert sha(extracted)==sha(TAILS/name)
        with Image.open(extracted) as image:assert image.size==(1024,1024)
    result={'passed':True,'version':'1.0.5-review6',
            'base720AssetsPreserved':True,'hdWorldMapGlyphPages':7,
            'hdCutsceneKoreanPages':46,'tailsBothPathsHd':True,
            'addedFiles':len(added),'changedFiles':len(changed),
            'gameplayVerified':False,'publicRelease':False}
    (NEW.parent/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
