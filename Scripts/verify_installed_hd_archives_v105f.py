"""Final static check of the installed HMM HD profile and split archives."""
from __future__ import annotations

import configparser
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
HD=MOD/'Compatibility/UnleasHD-1.4.2'
DB=ROOT/'UnleashedRecomp-Windows/mods/ModsDB.ini'
OUT=ROOT/'Build/HMM-Install-v105f-Playtest/final-verification.json'


def ini(path:Path)->configparser.ConfigParser:
    result=configparser.ConfigParser(interpolation=None)
    result.read(path,encoding='utf-8-sig')
    return result


def main()->None:
    config=ini(MOD/'mod.ini')
    assert config['Desc']['Version'].strip('"')=='1.0.5-review6'
    assert config['Main']['IncludeDir1'].strip('"')=='Compatibility/UnleasHD-1.4.2'
    assert config['Main']['IncludeDir2'].strip('"')=='.'
    schema=json.loads((MOD/'ConfigSchema.json').read_text(encoding='utf8'))
    option=next(x for g in schema['Groups'] for x in g['Elements'] if x['Type']=='UnleasHDCompatibility')
    assert option['DisplayName']=='한국어 UI 해상도'
    assert option['Value']=='Compatibility/UnleasHD-1.4.2'
    db=ini(DB)
    korean=db['Main']['ActiveMod0'].strip('"')
    hd=db['Main']['ActiveMod2'].strip('"')
    assert 'UnleashedKorean' in db['Mods'][korean]
    assert 'UnleasHD-1440p' in db['Mods'][hd]
    archives=0;splits=0
    for path in HD.rglob('*.arl'):
        data=path.read_bytes()
        assert data[:4]==b'ARL2'
        count=struct.unpack_from('<I',data,4)[0]
        parts=sorted(path.parent.glob(path.stem+'.ar.*'))
        assert count==len(parts)>0,(path,count,[x.name for x in parts])
        archives+=1;splits+=len(parts)
    result={'passed':True,'version':'1.0.5-review6','hdOptionSelected':True,
            'koreanAboveUnleasHd':True,'hdAppendArchives':archives,
            'hdArchiveSplits':splits,'gameplayVerified':False}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
