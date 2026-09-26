"""Check the two review4 HD fixes and unchanged translation payload."""
from __future__ import annotations

import configparser
import hashlib
import json
import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'Build/Development-v105c-Playtest/UnleashedKorean'
NEW = ROOT / 'Build/Development-v105d-Playtest/UnleashedKorean'
HD = ROOT / 'UnleashedRecomp-Windows/mods/UnleasHD-1440p'
FONT = ROOT / 'Build/Review4-FontInspection'
RESIDUAL = ROOT / 'Translation/review/unleashhd-v105/residual-conflicts.json'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(path: Path) -> dict[str, Path]:
    return {p.relative_to(path).as_posix(): p for p in path.rglob('*') if p.is_file()}


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


def ini(path: Path) -> configparser.ConfigParser:
    out = configparser.ConfigParser(interpolation=None)
    out.read(path, encoding='utf-8-sig')
    return out


def main() -> None:
    before, after = inventory(OLD), inventory(NEW)
    assert set(before) == set(after)
    changed = {name for name in before if sha(before[name]) != sha(after[name])}
    expected = {'mod.ini', 'README-1.0.5-REVIEW-KO.md',
                'Languages/English/+Sonic.ar.00', 'Languages/English/+Sonic.arl',
                'Compatibility/UnleasHD-1.4.2/Languages/English/+ExStageTails_Common.ar.00',
                'Compatibility/UnleasHD-1.4.2/Languages/English/+ExStageTails_Common.arl'}
    assert changed == expected, changed ^ expected
    config = ini(NEW / 'mod.ini')
    assert config['Desc']['Version'].strip('"') == '1.0.5-review4'
    assert config['Main']['IncludeDir1'].strip('"') == 'Compatibility/None'
    assert config['Main']['IncludeDir2'].strip('"') == '.'
    compat_sonic = members(NEW / 'Compatibility/UnleasHD-1.4.2/Languages/English/+Sonic.arl')
    base_sonic = members(NEW / 'Languages/English/+Sonic.arl')
    ring = members(HD / 'BoostGauge/ringenergy/Languages/English/+Sonic.arl')
    boost = members(HD / 'BoostGauge/boostenergy/Languages/English/+Sonic.arl')
    target = 'mat_playscreen_en_003.dds'
    assert target not in compat_sonic and target not in base_sonic
    assert target in ring and target in boost
    assert len(base_sonic) == 3
    texture = ROOT / 'Build/Review4-RingEnergy/ArchiveInspection/hd-ringenergy/+Sonic' / target
    with Image.open(texture) as image: assert image.size == (512, 32)
    tails = members(NEW / 'Compatibility/UnleasHD-1.4.2/Languages/English/+ExStageTails_Common.arl')
    event_names = {'evex_ex00_event_000.dds', 'evex_ex01_event_000.dds'}
    assert event_names <= tails and len(tails) == 6
    existing = json.loads(RESIDUAL.read_text(encoding='utf8'))['entries']
    glyph_pages = [x for x in existing if x['file'].startswith('fte_ConverseMain_')]
    assert len(glyph_pages) == 15
    for row in glyph_pages:
        archive, name = row['archive'], row['file']
        kept = FONT / archive / ('+' + archive) / name
        assert kept.is_file()
        with Image.open(kept) as image: assert image.size == (512, 512)
    result = {'passed': True, 'version': '1.0.5-review4', 'changedFiles': sorted(changed),
              'unchangedFiles': len(after)-len(changed), 'ringEnergyHdVariantAvailable': True,
              'ringEnergyHdPixels': [512, 32], 'tailsHdAtlases': 2,
              'japaneseGlyphPagesRetained': 15, 'gameplayVerified': False,
              'publicRelease': False}
    report = NEW.parent / 'verification.json'
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k != 'changedFiles'}, ensure_ascii=False))


if __name__ == '__main__': main()
