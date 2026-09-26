"""Prepare the user-approved Irma/Ippolita spellings and one missing glyph."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'Build/Development-v105-Review/UnleashedKorean'
NEW = ROOT / 'Build/Development-v105b-Playtest/UnleashedKorean'
WORK = ROOT / 'Build/TwoNames-v105b'
REVIEW = ROOT / 'Translation/review/proper-name-audit-v105b'
REPLACEMENTS = {'일마': '이르마', '이포리타': '이폴리타'}
EXPECTED_KEYS = {
    '52af69eadbaf0dad4c675003', '92a069737de8247c627af048',
    '3601a90454f0b81ad40f4da7', '623d1865affa32d0f2713be7',
    '88cda157a0e0479b9b5cd68b', '880d65e7309835ca22641abe',
    '81d62c6cfacb5338fadc0134', '58f41365b620b011c795737a',
    '2703d78048f3982e75f813b3', 'af25245ef11f12cc2fd390db',
    'f6c5ed0c255881de5f6dd459', '874b5e37017e6bb78554c3a4',
    '7bc9372a8035d8c499c17452', '5ec4b8e6da0b1812a2ceee28',
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def main() -> None:
    assert OLD.is_dir() and not NEW.exists() and not WORK.exists() and not REVIEW.exists()
    edits = []
    for path in sorted((ROOT / 'Translation').glob('*-all.json')):
        data = json.loads(path.read_text(encoding='utf8'))
        touched = False
        for row in data['items']:
            before = row['korean']
            after = before
            for source, target in REPLACEMENTS.items():
                after = after.replace(source, target)
            if before == after:
                continue
            key = row['translation_key']
            assert key in EXPECTED_KEYS, (path, key, before)
            assert ('イルマ' in row['japanese'] or 'Irma' in row['english'] or
                    'イッポリータ' in row['japanese'] or 'Ippolita' in row['english']), key
            row['korean'] = after
            touched = True
            edits.append({'file': path.name, 'translation_key': key,
                          'representative_line_id': row['representative_line_id'],
                          'japanese': row['japanese'], 'english': row['english'],
                          'before': before, 'after': after})
        if touched:
            write_json(path, data)
    assert {e['translation_key'] for e in edits} == EXPECTED_KEYS
    physical = [r for r in json.loads((ROOT / 'Analysis/Full-Text-Extraction/Catalog-Reviewed/all-lines.json').read_text(encoding='utf8'))
                if r['translation_key'] in EXPECTED_KEYS]
    assert len(physical) == 40

    glossary_path = ROOT / 'Translation/glossary.json'
    glossary = json.loads(glossary_path.read_text(encoding='utf8'))
    for japanese, english, korean, former in [
        ('イルマ', 'Irma', '이르마', '일마'),
        ('イッポリータ', 'Ippolita', '이폴리타', '이포리타'),
    ]:
        assert not any(e.get('japanese') == japanese or e.get('english') == english for e in glossary['entries'])
        glossary['entries'].append({'japanese': japanese, 'english': english, 'korean': korean,
                                    'category': '인물', 'status': '확정',
                                    'evidence': '2026-09-25 사용자 결정. 일본어판을 기본으로 하되 실제 인명에 가까운 표기를 적용',
                                    'forbidden_variants': [former]})
    write_json(glossary_path, glossary)

    shutil.copytree(OLD, NEW)
    ini = NEW / 'mod.ini'
    content = ini.read_text(encoding='utf-8-sig')
    assert 'Version="1.0.5-review"' in content
    ini.write_text(content.replace('Version="1.0.5-review"', 'Version="1.0.5-review2"', 1), encoding='utf8')

    WORK.mkdir(parents=True)
    font = ImageFont.truetype(str(ROOT / 'Tools/Fonts/LINESeedKR-Rg.ttf'), 27)
    canvas = Image.new('RGBA', (512, 512), (0, 0, 0, 255))
    draw = ImageDraw.Draw(canvas)
    glyph = '폴'
    l, t, r, b = draw.textbbox((0, 0), glyph, font=font)
    gt, gb = draw.textbbox((0, 0), '가', font=font)[1::2]
    x = (28 - (r - l)) / 2 - l
    y = (35 - (gb - gt)) / 2 - gt
    y = max(-t, min(y, 35 - b))
    assert 0 <= x + l < x + r <= 28 and 0 <= y + t < y + b <= 35
    draw.text((x, y), glyph, font=font, fill=(255, 255, 255, 255))
    canvas.save(WORK / 'fte_Korean_007.dds', pixel_format='DXT5')
    write_json(WORK / 'pol-glyph.json', {'character': glyph, 'texture': 'fte_Korean_007',
                                       'page': 7, 'rect': [0, 0, 28, 35], 'ink_bounds': [x+l, y+t, x+r, y+b]})
    write_json(REVIEW / 'name-edits.json', {'decision': 'Irma=이르마, Ippolita=이폴리타; 그 밖의 이름 유지',
                                           'catalog_entries': edits,
                                           'physical_cells': [{k: r.get(k) for k in
                                                              ('translation_key', 'source_kind', 'package', 'archive',
                                                               'fco_file', 'group_index', 'cell_index')}
                                                              for r in physical]})
    (REVIEW / 'DECISIONS-KO.md').write_text(
        '# 인명 최종 결정\n\n'
        '- 일마 → 이르마 (Irma)\n'
        '- 이포리타 → 이폴리타 (Ippolita)\n'
        '- 왕, 조세프는 앞서 확정한 표기를 유지합니다.\n'
        '- 릴 앤, 데니스와 다른 검토 인명은 일본어판 우선 방침에 따라 기존 표기를 유지합니다.\n\n'
        '번역 항목 14개, 실제 게임 리소스 40곳을 수정 대상으로 확인했습니다.\n', encoding='utf8')
    print(f'catalog={len(edits)} physical={len(physical)} mod={NEW}')


if __name__ == '__main__':
    main()
