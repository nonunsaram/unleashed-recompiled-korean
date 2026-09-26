"""List every DDS in the installed Korean mod's append archives."""
from __future__ import annotations

import collections
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
OUT=ROOT/'Translation/review/unleashhd-v105e/all-mod-art.json'


def members(path:Path)->list[str]:
    data=path.read_bytes()
    assert data[:4]==b'ARL2'
    pos=8+4*struct.unpack_from('<I',data,4)[0]
    result=[]
    while pos<len(data):
        size=data[pos];pos+=1
        name=data[pos:pos+size].decode('utf8');pos+=size
        result.append(name)
    assert pos==len(data)
    return result


def main()->None:
    rows=[]
    for archive in MOD.rglob('*.arl'):
        relative=archive.relative_to(MOD).as_posix()
        for name in members(archive):
            if name.lower().endswith('.dds'):
                rows.append({'archive':relative,'file':name,'top':archive.relative_to(MOD).parts[0]})
    counts=dict(collections.Counter(x['top'] for x in rows))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({'counts':counts,'rows':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'counts':counts,'total':len(rows),
                      'subtitleSamples':[x for x in rows if x['top']=='Inspire'][:12],
                      'worldMapSamples':[x for x in rows if x['top']=='WorldMapVariants'][:12]},ensure_ascii=False))


if __name__=='__main__':main()
