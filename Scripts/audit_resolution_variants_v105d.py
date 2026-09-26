"""Inventory Korean glyph pages that do not collide with UnleasHD textures."""
from __future__ import annotations

import collections
import json
import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'UnleashedRecomp-Windows/mods/UnleashedKorean'
BASE = MOD / 'Languages/English'
HD = MOD / 'Compatibility/UnleasHD-1.4.2/Languages/English'
EXTRACT = ROOT / 'Build/Review4-FontInspection'
OUTPUT = ROOT / 'Translation/review/unleashhd-v105d/resolution-inventory.json'


def members(path: Path) -> set[str]:
    data = path.read_bytes()
    assert data[:4] == b'ARL2'
    pos = 8 + 4*struct.unpack_from('<I', data, 4)[0]
    out = set()
    while pos < len(data):
        size = data[pos]
        pos += 1
        name = data[pos:pos+size].decode('utf8')
        assert name not in out
        out.add(name)
        pos += size
    assert pos == len(data)
    return out


def main() -> None:
    rows=[]
    for arl in sorted(BASE.glob('+*.arl')):
        stem=arl.stem
        compat=HD / arl.name
        hd_names=members(compat) if compat.is_file() else set()
        for name in sorted(members(arl)):
            if not name.lower().endswith('.dds'): continue
            kind=('korean-glyph' if name.startswith('fte_Korean_') else
                  'legacy-converse' if name.startswith('fte_ConverseMain_') else
                  'event' if name.startswith('evex_') else 'ui-or-other')
            archive=stem[1:]
            source=EXTRACT / archive / stem / name
            size=None
            if source.is_file():
                with Image.open(source) as image: size=list(image.size)
            rows.append({'archive':archive, 'file':name, 'kind':kind,
                         'hasHdOverride':name in hd_names, 'baseSize':size})
    counts=collections.Counter(x['kind'] for x in rows)
    glyphs=[x for x in rows if x['kind']=='korean-glyph']
    report={'totalBaseDds':len(rows),'counts':dict(counts),
            'koreanGlyphPages':len(glyphs),
            'koreanGlyphPagesHdOverridden':sum(x['hasHdOverride'] for x in glyphs),
            'koreanGlyphPagesSizeKnown':sum(x['baseSize'] is not None for x in glyphs),
            'koreanGlyphArchiveCounts':dict(collections.Counter(x['archive'] for x in glyphs)),
            'rows':rows}
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},ensure_ascii=False))


if __name__=='__main__': main()
