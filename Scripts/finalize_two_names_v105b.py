"""Update local playtest notes after the approved name changes."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'Build/Development-v105b-Playtest/UnleashedKorean'
REVIEW = ROOT / 'Translation/review/proper-name-audit-v105b'


def update(name: str, replacements: list[tuple[str, str]]) -> None:
    path = MOD / name
    text = path.read_text(encoding='utf-8-sig')
    for before, after in replacements:
        assert before in text, (name, before)
        text = text.replace(before, after)
    path.write_text(text, encoding='utf8')


def main() -> None:
    assert json.loads((REVIEW / 'resource-verification.json').read_text(encoding='utf8'))['passed']
    update('README-1.0.5-REVIEW-KO.md', [
        ('# 한국어 패치 1.0.5 검토 후보', '# 한국어 패치 1.0.5-review2 플레이 테스트 후보'),
        ('기존 1.0.4 검토본에 다음 두 수정을', '기존 1.0.5 검토 후보에 다음 세 수정을'),
        ('2. **왕 씨 표기:** 춘난 상점 주인의 이름표, 관련 아이템, 미디어룸 설명의 `완`을 `왕`으로 통일했습니다.',
         '2. **왕 씨 표기:** 춘난 상점 주인의 이름표, 관련 아이템, 미디어룸 설명의 `완`을 `왕`으로 통일했습니다.\n3. **인명 확정:** 스파고니아의 `일마`를 `이르마`로, `이포리타`를 `이폴리타`로 변경했습니다. 이름표·대사·미디어룸 등 40곳에 반영했습니다. 다른 이름은 유지했습니다.'),
        ('춘난 상점 주인과 도시락·중화면, 미디어룸의 인물 설명에서는 `왕` 표기를 확인할 수 있습니다.',
         '춘난 상점 주인과 도시락·중화면, 미디어룸의 인물 설명에서는 `왕` 표기를 확인할 수 있습니다. 스파고니아에서는 이르마와 이폴리타의 이름표·대사, 미디어룸 설명을 확인해 주십시오.'),
    ])
    update('NAME-AUDIT-KO.md', [
        ('기존 용어집의 인물 관련 38건', '기존 용어집의 인물 관련 38건과 이번 확정 2건'),
        ('## 변경 고려 목록', '## 이르마·이폴리타 확정 수정\n\n사용자 결정으로 `일마→이르마`, `이포리타→이폴리타`를 적용했습니다. 번역 항목 14개, 실제 리소스 40곳입니다.\n\n## 변경 고려 목록'),
        ('| イルマ | Irma | 일마 | 이르마 | 영어·이탈리아어 통용 표기 |\n', ''),
        ('| イッポリータ | Ippolita | 이포리타 | 이폴리타 | 이탈리아어 통용 표기 |\n', ''),
        ('현재 추가 변경을 추천하는 표기는 `일마→이르마`, `이포리타→이폴리타`이며 아직 게임 파일에는 적용하지 않았습니다.',
         '두 표기는 이번 플레이 테스트 후보의 게임 파일에 적용했습니다.'),
        ('검토 이력 14건(조세프 유지 확정, 나머지 13건)', '검토 이력 14건(조세프 유지 확정, 두 이름 수정 확정, 나머지 11건)'),
    ])
    update('NAME-RECOMMENDATIONS-KO.md', [
        ('아래 두 건의 변경 추천은 제안일 뿐이며 현재 게임 리소스에는 아직 적용하지 않았습니다.',
         '이르마와 이폴리타는 사용자 결정에 따라 현재 게임 리소스에 적용했습니다.'),
        ('| 스파고니아 | イッポリータ / Ippolita | 이포리타 | **이폴리타** (변경 추천) |',
         '| 스파고니아 | イッポリータ / Ippolita | 이폴리타 | **이폴리타** (수정 확정) |'),
        ('| 스파고니아 | イルマ / Irma | 일마 | **이르마** (변경 추천) |',
         '| 스파고니아 | イルマ / Irma | 이르마 | **이르마** (수정 확정) |'),
    ])
    csv_path = MOD / 'NAME-REGIONS-113.csv'
    with csv_path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 113
    count = 0
    for row in rows:
        if row['translation_key'] == '52af69eadbaf0dad4c675003':
            assert row['korean'] == '일마'
            row['korean'] = '이르마'
            row['recommendation'] = '이르마'
            row['action'] = '수정 확정'
            row['reason'] += '; 2026-09-25 사용자 확정'
            count += 1
        if row['translation_key'] == '92a069737de8247c627af048':
            assert row['korean'] == '이포리타'
            row['korean'] = '이폴리타'
            row['recommendation'] = '이폴리타'
            row['action'] = '수정 확정'
            row['reason'] += '; 2026-09-25 사용자 확정'
            count += 1
    assert count == 2
    with csv_path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (MOD / 'NAME-DECISIONS-REVIEW2-KO.md').write_text(
        (REVIEW / 'DECISIONS-KO.md').read_text(encoding='utf8'), encoding='utf8')
    print('Updated review2 playtest notes and name table')


if __name__ == '__main__':
    main()
