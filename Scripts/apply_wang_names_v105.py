"""Apply the confirmed Wang spelling and audit all character name tags."""
from __future__ import annotations
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Translation/review/proper-name-audit-v105'
EDITS = {
    '8f6d66c30e1c4af51f26c29b': ('완', '왕'),
    'e48d7755134a763aa470ff24': ('길을 막아선 완', '길을 막아선 왕'),
    'f0f5b6d86978e7e37b037784': ('완 씨의 도시락', '왕 씨의 도시락'),
    '49b1d0616b23dbe655879131': ('주인 완 씨가 직접 만든 도시락\n완 씨의 기분이 좋으면 곱빼기가 되기도 한다', '주인 왕 씨가 직접 만든 도시락\n왕 씨의 기분이 좋으면 곱빼기가 되기도 한다'),
    '8c693a598c42aacc12814fb3': ('완 씨의 중화면', '왕 씨의 중화면'),
    '2564bef5806b4cec58dcaea9': ('완', '왕'),
    '9c920e905569e727c0272d47': ('진린과 완의 딸. 고기만두 가게\n집안에서 태어났지만 만두뿐인\n삶에 조금 질렸다. 최근에는\n고기만두가 미용의 적이라며\n채소만 먹는 한창 나이의 소녀다.', '진린과 왕의 딸. 고기만두 가게\n집안에서 태어났지만 만두뿐인\n삶에 조금 질렸다. 최근에는\n고기만두가 미용의 적이라며\n채소만 먹는 한창 나이의 소녀다.'),
}
# These entries need human preference / language-context review, not automatic replacement.
RESOLVED = {'1cbcc46fad028bbe156f19ae': '사용자 결정: 조세프 유지 (2026-09-25)'}
CANDIDATES = {
    '6eb23920508410d4ce9d520d': ('쿠워드', '쿼드', '영어 Kwod와 기존 쿠워드의 차이'),
    'fbc2d77303a107570fb20e4c': ('데니스', '드니즈', '영어 Denise 및 지역 언어의 통용 발음'),
    '52af69eadbaf0dad4c675003': ('일마', '이르마', '영어 Irma의 통용 표기'),
    '92a069737de8247c627af048': ('이포리타', '이폴리타', '이탈리아어 Ippolita의 통용 표기'),
    'df408559739cb12a9d647de6': ('이프산', '에흐산', '영어 Ehsan과 일본어 イフサーン의 차이'),
    '16e632d48a3f4b6c60ebcdda': ('스두키', '사디크', '영어 Sadiq와 일본어 スドゥキー의 이름 차이'),
    'f8b81bb1f56a5a6ce2775c03': ('야리수레', '야리투레', '영어 Jari-Thure의 Th 발음과 일본어 スーレ의 차이'),
    '645e891cfb772ac1c0fdbb06': ('파티마', '사마르', '영어 Sammar와 일본어 ファティマ의 이름 차이'),
    'e6785377c924d5a074c2a335': ('릴 앤', '릴 케이트', '영어 Li\'l Kate와 일본어 リル・アン의 이름 차이'),
    'afbba6e74d13ab9e20eb515b': ('디나', '디마', '영어 Dimah와 일본어 ディナ의 이름 차이'),
    '15683f3678b478595b3b659a': ('후줄', '히지르', '영어 Hizir와 일본어 フズル의 이름 차이'),
    '3327c7be085b387ac167fb0b': ('사파', '사피', '영어 Safi와 일본어 サファー의 이름 차이'),
    '485e7f2b0df2d418e24b02ca': ('제나', '사미아', '영어 Samia와 일본어 ゼーナ의 이름 차이'),
}

def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = {}
    edit_rows = []
    count = 0
    for path in sorted((ROOT / 'Translation').glob('*-all.json')):
        data = json.loads(path.read_text(encoding='utf8'))
        count += len(data['items'])
        touched = False
        for row in data['items']:
            key = row['translation_key']
            assert key not in catalog, key
            catalog[key] = row
            if key in EDITS:
                before, after = EDITS[key]
                assert row['korean'] in (before, after), (path, key, row['korean'])
                if row['korean'] == before:
                    row['korean'] = after
                    touched = True
                edit_rows.append({'file': path.name, 'translation_key': key,
                                  'representative_line_id': row['representative_line_id'],
                                  'japanese': row['japanese'], 'english': row['english'],
                                  'before': before, 'after': after})
        if touched:
            write_json(path, data)
    assert len(edit_rows) == len(EDITS)
    assert count == 11912 and len(catalog) == count
    glossary_path = ROOT / 'Translation/glossary.json'
    glossary = json.loads(glossary_path.read_text(encoding='utf8'))
    wang = [x for x in glossary['entries'] if x['japanese'] == 'ワン' or x['english'] == 'Wang']
    assert len(wang) <= 1
    if wang:
        assert wang[0]['korean'] == '왕'
    else:
        glossary['entries'].append({'japanese': 'ワン', 'english': 'Wang', 'korean': '왕',
                                    'category': '인물', 'status': '확정',
                                    'evidence': '춘난 상점 주인. 한자 성 Wang의 국내 통용 표기와 사용자 제보를 반영',
                                    'forbidden_variants': ['완']})
        write_json(glossary_path, glossary)
    physical = [r for r in json.loads((ROOT / 'Analysis/Full-Text-Extraction/Catalog-Reviewed/all-lines.json').read_text(encoding='utf8')) if r['translation_key'] in EDITS]
    write_json(OUT / 'wang-edits.json', {'decision': 'Wang = 왕', 'catalog_entries': edit_rows,
                                        'physical_cells': [{k: r.get(k) for k in ('translation_key','source_kind','package','archive','fco_file','group_index','cell_index')} for r in physical]})
    tags = [r for r in json.loads((ROOT / 'Translation/core-ui-all.json').read_text(encoding='utf8'))['items'] if r.get('content_role') == 'name_tag']
    assert len(tags) == 113 and set(CANDIDATES) <= {r['translation_key'] for r in tags}
    fields = ['translation_key','japanese','english','korean','decision','possible_korean','reason','representative_line_id']
    with (OUT / 'name-tags-113.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for row in tags:
            key = row['translation_key']
            candidate = CANDIDATES.get(key)
            if candidate:
                assert candidate[0] == row['korean'], key
            writer.writerow({'translation_key': key, 'japanese': row['japanese'],
                             'english': row['english'], 'korean': row['korean'],
                             'decision': '확정 수정' if key in EDITS else '유지 확정' if key in RESOLVED else '추가 검토' if candidate else '유지',
                             'possible_korean': candidate[1] if candidate else '',
                             'reason': 'Wang의 국내 통용 표기 왕으로 수정' if key in EDITS else RESOLVED[key] if key in RESOLVED else candidate[2] if candidate else '일본어 우선 방침으로 대조',
                             'representative_line_id': row['representative_line_id']})
    person_glossary = [x for x in glossary['entries'] if '인물' in x.get('category', '')]
    assert len(person_glossary) == 38
    tag_japanese = {r['japanese'] for r in tags}
    with (OUT / 'glossary-people-38.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=['japanese', 'english', 'korean', 'category', 'status', 'name_tag_exact_match'])
        writer.writeheader()
        for row in person_glossary:
            writer.writerow({k: row.get(k, '') for k in ('japanese', 'english', 'korean', 'category', 'status')} |
                            {'name_tag_exact_match': row['japanese'] in tag_japanese})
    write_json(OUT / 'summary.json', {'catalog_entries_scanned': count, 'name_tags_compared': len(tags), 'person_glossary_compared': len(person_glossary),
                                      'wang_catalog_entries_changed': len(EDITS), 'wang_physical_cells': len(physical),
                                      'additional_name_candidates': len(CANDIDATES), 'resolved_name_cases': len(RESOLVED),
                                      'gameplay_verified': False})
    print(f'catalog={count} tags={len(tags)} wang_entries={len(EDITS)} physical={len(physical)} candidates={len(CANDIDATES)}')

if __name__ == '__main__':
    main()
