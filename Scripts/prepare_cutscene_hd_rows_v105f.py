"""Join translated cutscene text to every physical FCO coordinate."""
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Build/Review6-ResolutionSplit/cutscene-physical.json'


def main()->None:
    translated=json.loads((ROOT/'Translation/cutscenes-all.json').read_text(encoding='utf8'))['items']
    by_key={row['translation_key']:row for row in translated}
    assert len(by_key)==len(translated)==602
    catalog=json.loads((ROOT/'Analysis/Full-Text-Extraction/Catalog-Reviewed/all-lines.json').read_text(encoding='utf8'))
    physical=[]
    for row in catalog:
        if row.get('source_kind')!='cutscene':continue
        key=row['translation_key']
        assert key in by_key
        item=by_key[key]
        physical.append({k:row[k] for k in ('archive','fco_file','group_index','cell_index','translation_key')}|
                        {'korean':item.get('korean') or ''})
    assert len(physical)==606 and len({r['archive'] for r in physical})==42
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(physical,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'physical':len(physical),'archives':42,
                      'translated':sum(bool(r['korean']) for r in physical)},ensure_ascii=False))


if __name__=='__main__':main()
