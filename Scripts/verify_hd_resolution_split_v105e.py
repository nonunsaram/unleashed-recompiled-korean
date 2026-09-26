"""Verify that review5 selects 720p and HD Korean art without changing text."""
from __future__ import annotations

import configparser
import hashlib
import json
import struct
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'Build/Development-v105d-Playtest/UnleashedKorean'
NEW=ROOT/'Build/Development-v105e-Playtest/UnleashedKorean'
INV=ROOT/'Translation/review/unleashhd-v105d/resolution-inventory.json'
ROUND=ROOT/'Build/Review5-ResolutionSplit/ArchiveWork/RoundTrip'
HD_PAGES=ROOT/'Build/Review5-ResolutionSplit/HdGlyphPages'


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(path:Path)->dict[str,Path]:
    return {p.relative_to(path).as_posix():p for p in path.rglob('*') if p.is_file()}


def members(path:Path)->set[str]:
    data=path.read_bytes()
    assert data[:4]==b'ARL2'
    pos=8+4*struct.unpack_from('<I',data,4)[0]
    out=set()
    while pos<len(data):
        size=data[pos];pos+=1
        name=data[pos:pos+size].decode('utf8');pos+=size
        assert name not in out
        out.add(name)
    assert pos==len(data)
    return out


def ini(path:Path)->configparser.ConfigParser:
    out=configparser.ConfigParser(interpolation=None)
    out.read(path,encoding='utf-8-sig')
    return out


def main()->None:
    source=json.loads(INV.read_text(encoding='utf8'))
    source_pages=defaultdict(set)
    for row in source['rows']:
        if row['kind']=='korean-glyph':source_pages[row['archive']].add(row['file'])
    before,after=inventory(OLD),inventory(NEW)
    assert set(before)<=set(after)
    changed={name for name in before if sha(before[name])!=sha(after[name])}
    added=set(after)-set(before)
    assert all(x.startswith('Compatibility/UnleasHD-1.4.2/Languages/English/+') for x in added)
    allowed={'mod.ini','ConfigSchema.json','README-1.0.5-REVIEW-KO.md'}
    assert all(x in allowed or x.startswith('Compatibility/UnleasHD-1.4.2/Languages/English/+') for x in changed)
    assert all(sha(before[x])==sha(after[x]) for x in before if not x.startswith('Compatibility/') and x not in allowed)
    for archive,names in source_pages.items():
        stem='+'+archive
        base=NEW/'Languages/English'/(stem+'.arl')
        hd=NEW/'Compatibility/UnleasHD-1.4.2/Languages/English'/(stem+'.arl')
        assert names<=members(base) and names<=members(hd)
        extracted=ROUND/archive/stem
        for name in names:
            file=extracted/name
            assert sha(file)==sha(HD_PAGES/name)
            with Image.open(file) as image:assert image.size==(1024,1024)
    assert sum(map(len,source_pages.values()))==106
    title=ROUND/'Title/+Title/mat_title_en_002.dds'
    with Image.open(title) as image:assert image.size==(256,512)
    tails=ROUND/'ExStageTails_Common/+ExStageTails_Common'
    for name in ('evex_ex00_event_000.dds','evex_ex01_event_000.dds'):
        with Image.open(tails/name) as image:assert image.size==(1024,1024)
    assert 'mat_playscreen_en_003.dds' not in members(NEW/'Languages/English/+Sonic.arl')
    config=ini(NEW/'mod.ini')
    assert config['Desc']['Version'].strip('"')=='1.0.5-review5'
    assert config['Main']['IncludeDir1'].strip('"')=='Compatibility/None'
    assert config['Main']['IncludeDir2'].strip('"')=='.'
    schema=json.loads((NEW/'ConfigSchema.json').read_text(encoding='utf8'))
    option=next(x for group in schema['Groups'] for x in group['Elements'] if x['Type']=='UnleasHDCompatibility')
    assert option['Name']=='IncludeDir1' and option['DisplayName']=='한국어 UI 해상도'
    assert option['Value']=='Compatibility/None'
    result={'passed':True,'version':'1.0.5-review5','baseTranslationFilesPreserved':True,
            'hdKoreanGlyphAtlases':106,'hdTitleLanguageAtlases':1,
            'review4TailsAtlasesPreserved':2,'review4GaugeFixPreserved':True,
            'newFiles':len(added),'changedFiles':len(changed),
            'gameplayVerified':False,'publicRelease':False}
    report=NEW.parent/'verification.json'
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
