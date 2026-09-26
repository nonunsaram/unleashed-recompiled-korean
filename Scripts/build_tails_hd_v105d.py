"""Add faithful 2x Korean Tails subtitle pages to the review4 HD layer."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from bounded_archive_tool import unpack
from probe_tails_atlas_v105d import render_one

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / 'Build/Development-v105d-Playtest/UnleashedKorean'
COMPAT = CANDIDATE / 'Compatibility/UnleasHD-1.4.2/Languages/English'
SOURCE = ROOT / 'Build/Review4-FontInspection/ExStageTails_Common/+ExStageTails_Common'
WORK = ROOT / 'Build/Review4-TailsHD'
MAP = json.loads((ROOT / 'Build/Review4-RingEnergy/tails-atlas-map.json').read_text(encoding='utf-8-sig'))
STEM = '+ExStageTails_Common'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert CANDIDATE.is_dir() and not WORK.exists()
    assert len(MAP) == 2
    old = WORK / 'Old' / (STEM + '.ar.00')
    old.parent.mkdir(parents=True)
    shutil.copy2(COMPAT / old.name, old)
    unpack(old)
    unpacked = old.parent / STEM
    before = {p.name: sha(p) for p in unpacked.iterdir() if p.is_file()}
    assert len(before) == 4 and all(name.startswith('mat_') for name in before)
    packed_dir = WORK / 'Packed'
    packed_dir.mkdir()
    folder = packed_dir / STEM
    shutil.copytree(unpacked, folder)
    for page in MAP:
        filename = page['texture']
        assert filename not in before and (SOURCE / filename).is_file()
        base = Image.open(SOURCE / filename).convert('RGBA')
        assert base.size == (512, 512)
        high = render_one(base, page['entries'], 2)
        assert high.size == (1024, 1024)
        high.save(folder / filename, pixel_format='DXT5')
        with Image.open(folder / filename) as reread:
            assert reread.size == (1024, 1024)
        # Keep a PNG for visible review of the exact submitted texture.
        high.save(WORK / (page['stem'] + '-preview.png'))
    subprocess.run([str(ROOT / 'Tools/HedgeArcPack/HedgeArcPack.exe'), str(folder)],
                   input='hh\n', text=True, capture_output=True, check=True, timeout=30)
    for ext in ('.arl', '.ar.00'):
        shutil.copy2(packed_dir / (STEM + ext), COMPAT / (STEM + ext))
    check = WORK / 'Check' / (STEM + '.ar.00')
    check.parent.mkdir()
    shutil.copy2(COMPAT / check.name, check)
    unpack(check)
    entries = {p.name: p for p in (check.parent / STEM).iterdir() if p.is_file()}
    assert set(entries) == set(before) | {x['texture'] for x in MAP}
    assert all(sha(entries[name]) == digest for name, digest in before.items())
    for page in MAP:
        with Image.open(entries[page['texture']]) as texture:
            assert texture.size == (1024, 1024)
    report = {'passed': True, 'archive': STEM, 'originalMembersPreserved': 4,
              'koreanSubtitlePages': [page['texture'] for page in MAP],
              'outputSize': [1024, 1024], 'gameplayVerified': False}
    (WORK / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
