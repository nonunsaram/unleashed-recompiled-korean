"""Check the installed review7 HMM profile, priority, and HD archives."""
from __future__ import annotations

import configparser
import json
import struct
from pathlib import Path

from PIL import Image

from bounded_archive_tool import unpack

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
HD=MOD/'Compatibility/UnleasHD-1.4.2'
DB=ROOT/'UnleashedRecomp-Windows/mods/ModsDB.ini'
OUT=ROOT/'Build/HMM-Install-v105g-Playtest/final-verification.json'
NAME=ROOT/'Build/Review7-ResolutionSplit/ArchiveWork/RoundTrip/+Town_Common/mat_talk_comon_002.dds'


def ini(path:Path)->configparser.ConfigParser:
    result=configparser.ConfigParser(interpolation=None)
    result.read(path,encoding='utf-8-sig')
    return result


def main()->None:
    config=ini(MOD/'mod.ini')
    assert config['Desc']['Version'].strip('"')=='1.0.5-review7'
    assert config['Main']['IncludeDir1'].strip('"')=='Compatibility/UnleasHD-1.4.2'
    assert config['Main']['IncludeDir2'].strip('"')=='.'
    schema=json.loads((MOD/'ConfigSchema.json').read_text(encoding='utf8'))
    option=next(x for g in schema['Groups'] for x in g['Elements'] if x['Type']=='UnleasHDCompatibility')
    assert option['DisplayName']=='한국어 UI 해상도' and option['Value']=='Compatibility/UnleasHD-1.4.2'
    db=ini(DB)
    assert 'UnleashedKorean' in db['Mods'][db['Main']['ActiveMod0'].strip('"')]
    assert 'UnleasHD-1440p' in db['Mods'][db['Main']['ActiveMod2'].strip('"')]
    count=0;splits=0
    for path in HD.rglob('*.arl'):
        data=path.read_bytes();assert data[:4]==b'ARL2'
        split_count=struct.unpack_from('<I',data,4)[0]
        parts=sorted(path.parent.glob(path.stem+'.ar.*'))
        assert split_count==len(parts)>0,(path,split_count)
        count+=1;splits+=len(parts)
    with Image.open(NAME) as image:assert image.size==(512,512)
    assert (HD/'+Town_Common.arl').is_file()
    result={'passed':True,'version':'1.0.5-review7','hdOptionSelected':True,
            'koreanAboveUnleasHd':True,'hdAppendArchives':count,
            'hdArchiveSplits':splits,'hdNameplateReady':True,
            'gameplayVerified':False}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
