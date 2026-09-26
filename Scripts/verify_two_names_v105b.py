"""Verify the local review2 candidate against the reviewed 1.0.5 baseline."""
from __future__ import annotations

import configparser
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / 'Build/Development-v105-Review/UnleashedKorean'
AFTER = ROOT / 'Build/Development-v105b-Playtest/UnleashedKorean'
REVIEW = ROOT / 'Translation/review/proper-name-audit-v105b'
OUT = ROOT / 'Build/Development-v105b-Playtest/verification.json'


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root: Path) -> dict[str, Path]:
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}


def main() -> None:
    resource = read(REVIEW / 'resource-verification.json')
    edits = read(REVIEW / 'name-edits.json')
    assert resource['passed'] and resource['catalog_entries'] == 14
    assert resource['physical_cells'] == 40 and resource['archive_count'] == 8
    assert all(x['roundtrip_verified'] for x in resource['archives'])
    assert len(edits['catalog_entries']) == 14 and len(edits['physical_cells']) == 40
    assert len({e['translation_key'] for e in edits['catalog_entries']}) == 14
    assert all('일마' not in e['after'] and '이포리타' not in e['after'] for e in edits['catalog_entries'])
    assert all('이르마' in e['after'] or '이폴리타' in e['after'] for e in edits['catalog_entries'])
    expected_archives = {x['archive'] for x in resource['archives']}
    assert len(expected_archives) == 8
    old, new = files(BEFORE), files(AFTER)
    assert set(old) <= set(new)
    assert set(new) - set(old) == {'NAME-DECISIONS-REVIEW2-KO.md'}
    changed = {rel for rel in old if sha(old[rel]) != sha(new[rel])}
    archive_changes = {rel for rel in changed if rel.startswith('Languages/English/')}
    allowed_archives = {rel for rel in old if any(rel.startswith(f'Languages/English/+{name}.ar.') or
                                                rel == f'Languages/English/+{name}.arl'
                                                for name in expected_archives)}
    assert archive_changes <= allowed_archives
    assert all(any(rel.startswith(f'Languages/English/+{name}.ar.') for rel in archive_changes)
               for name in expected_archives)
    other_changes = changed - archive_changes
    assert other_changes == {'mod.ini', 'README-1.0.5-REVIEW-KO.md', 'NAME-AUDIT-KO.md',
                             'NAME-RECOMMENDATIONS-KO.md', 'NAME-REGIONS-113.csv'}
    assert all(sha(old[rel]) == sha(new[rel]) for rel in old if rel.startswith('Compatibility/'))

    ini = configparser.ConfigParser(interpolation=None)
    ini.read(AFTER / 'mod.ini', encoding='utf-8-sig')
    assert ini['Desc']['Version'].strip('"') == '1.0.5-review2'
    assert ini['Main']['IncludeDir2'].strip('"') == 'Compatibility/None'
    schema = read(AFTER / 'ConfigSchema.json')
    options = [e for g in schema['Groups'] for e in g['Elements'] if e['Name'] == 'IncludeDir2']
    assert len(options) == 1
    assert any(e['Value'] == 'Compatibility/UnleasHD-1.4.2' for e in schema['Enums'][options[0]['Type']])

    glyph = read(ROOT / 'Build/TwoNames-v105b/pol-glyph.json')
    assert glyph['character'] == '폴' and glyph['rect'] == [0, 0, 28, 35]
    with Image.open(ROOT / 'Build/TwoNames-v105b/fte_Korean_007.dds') as image:
        assert image.size == (512, 512)
        assert image.crop((0, 0, 28, 35)).getbbox() is not None
    glossary = read(ROOT / 'Translation/glossary.json')['entries']
    assert any(e.get('japanese') == 'イルマ' and e.get('korean') == '이르마' for e in glossary)
    assert any(e.get('japanese') == 'イッポリータ' and e.get('korean') == '이폴리타' for e in glossary)

    result = {'passed': True, 'candidate': str(AFTER), 'catalogEntriesChanged': 14,
              'physicalCellsChanged': 40, 'archivesChanged': 8,
              'archiveFilesChanged': len(archive_changes), 'otherFilesChanged': len(other_changes),
              'unrelatedFilesPreserved': len(old) - len(changed),
              'newGlyph': '폴', 'hdCompatibilityPreserved': True,
              'gameplayVerified': False, 'publicRelease': False}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
