"""Audit archive precedence and the high-resolution Korean UI coverage."""
from __future__ import annotations

import configparser
import hashlib
import json
import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'Build/Development-v105b-Playtest/UnleashedKorean'
NEW = ROOT / 'Build/Development-v105c-Playtest/UnleashedKorean'
OUT = NEW.parent / 'verification.json'


def sha(path: Path) -> bytes:
    return hashlib.sha256(path.read_bytes()).digest()


def inventory(root: Path) -> dict[str, Path]:
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}


def members(path: Path) -> set[str]:
    blob = path.read_bytes()
    assert blob[:4] == b'ARL2'
    offset = 8 + 4 * struct.unpack_from('<I', blob, 4)[0]
    result = set()
    while offset < len(blob):
        n = blob[offset]
        offset += 1
        item = blob[offset:offset+n].decode('utf8')
        assert item not in result
        result.add(item)
        offset += n
    assert offset == len(blob)
    return result


def ini(path: Path) -> configparser.ConfigParser:
    data = configparser.ConfigParser(interpolation=None)
    data.read(path, encoding='utf-8-sig')
    return data


def main() -> None:
    initial = json.loads(OUT.read_text(encoding='utf8'))
    assert initial['passed'] and initial['uiTextures'] == 43
    before, after = inventory(OLD), inventory(NEW)
    assert set(before) == set(after)
    changed = {rel for rel in before if sha(before[rel]) != sha(after[rel])}
    assert changed == {'mod.ini', 'ConfigSchema.json', 'README-1.0.5-REVIEW-KO.md'}
    config = ini(NEW / 'mod.ini')
    assert config['Main']['IncludeDir0'].strip('"') == 'WorldMapVariants/AllDLC'
    assert config['Main']['IncludeDir1'].strip('"') == 'Compatibility/None'
    assert config['Main']['IncludeDir2'].strip('"') == '.'
    assert config['Main']['IncludeDirCount'] == '4'
    schema = json.loads((NEW / 'ConfigSchema.json').read_text(encoding='utf8'))
    option = [e for g in schema['Groups'] for e in g['Elements'] if e['Type'] == 'UnleasHDCompatibility']
    assert len(option) == 1 and option[0]['Name'] == 'IncludeDir1'
    assert option[0]['Value'] == 'Compatibility/None'

    hd = json.loads((ROOT / 'Build/UnleasHD-Compatibility-v105-HUD2/verification.json').read_text(encoding='utf8'))
    labels = json.loads((ROOT / 'Translation/review/unleashhd-v105/ui-textures-ko-v104-full.json').read_text(encoding='utf8'))['labels']
    assert hd['passed'] and len(hd['textures']) == 43 and len(labels) == 149
    examples = {'ActionCommon': 'mat_playscreen_en_001.dds',
                'SystemCommonCore': 'mat_status_en_001.dds',
                'Town_Common': 'mat_shop_en_001.dds'}
    size_checks = {}
    for stem, filename in examples.items():
        rel = Path('Languages/English') / ('+' + stem + '.arl')
        assert filename in members(NEW / 'Compatibility/UnleasHD-1.4.2' / rel)
        assert filename in members(NEW / rel)
        assert not (NEW / 'WorldMapVariants/AllDLC' / rel).exists()
        texture = next(x for x in hd['textures'] if x['archive'] == stem and x['file'] == filename)
        reference = next(x for x in json.loads((ROOT / 'Translation/review/remaining-ui/texture-comparison.json').read_text(encoding='utf8'))
                         if x['file'] == filename and f'BaseGame/{stem}' in x['archives'])
        with Image.open(reference['english']) as old_image:
            old_size = old_image.size
        assert texture['size'] == [old_size[0]*2, old_size[1]*2]
        size_checks[filename] = {'old': list(old_size), 'hd': texture['size']}
    assert {x['korean'] for x in labels if x['texture'] == 26} == {'구매', '판매'}
    for texture in hd['textures']:
        rel = Path('Languages/English') / ('+' + texture['archive'] + '.arl')
        assert texture['file'] in members(NEW / 'Compatibility/UnleasHD-1.4.2' / rel)

    result = initial | {'archivePrecedenceChecked': True, 'unrelatedFilesPreserved': len(after)-len(changed),
                        'representativeSizes': size_checks}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in result.items() if k != 'representativeSizes'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
