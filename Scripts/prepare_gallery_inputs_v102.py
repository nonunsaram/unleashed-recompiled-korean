"""Prepare small gallery verification inputs, reusing verified local extractions."""
from pathlib import Path
import json, shutil, struct
from bounded_archive_tool import unpack
from audit_mod_resources_v102 import digest

R = Path(__file__).resolve().parents[1]

def prepare():
    work = R/'Build/Development-v102/GalleryAudit'
    work.mkdir(parents=True, exist_ok=True)
    rows = json.loads((R/'Translation/media-room-ending-ui-all.json').read_text(encoding='utf8'))['items']
    by_key = {row['translation_key']: row for row in rows}
    slots = json.loads((R/'Translation/review/v102/gallery-title-slots.json').read_text(encoding='utf8'))
    expected = {str(row['group']): by_key[row['translation_key']]['korean'] for row in slots}
    assert set(expected) == {str(g) for g in range(201,269)}
    (work/'expected.json').write_text(json.dumps(expected, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    for name in ('Town_EULabo_Common', 'Town_PetraLabo_Common'):
        source = R/'Build/Development-v102/UnleashedKorean/Languages/English'/('+'+name+'.ar.00')
        destination = work/name
        destination.mkdir(exist_ok=True)
        ar = destination/source.name
        # The unchanged archive and cached extracted files were verified during recovery.
        stamp = destination/'verified-source.json'
        source_hash = digest(source)
        if stamp.exists():
            cached = json.loads(stamp.read_text())
            if cached['sourceSha256'] == source_hash and all(
                (destination/('+'+name)/n).is_file() and digest(destination/('+'+name)/n) == h
                for n,h in cached['members'].items()):
                continue
        for item in source.parent.glob('+'+name+'.ar*'):
            target = destination/item.name
            if target.exists() and digest(target) != digest(item):
                shutil.copy2(target, target.with_name(target.name+'.before-recovery'))
            if not target.exists() or digest(target) != digest(item):
                shutil.copy2(item, target)
        unpack(ar)
        members = {p.name: digest(p) for p in (destination/('+'+name)).iterdir() if p.is_file()}
        stamp.write_text(json.dumps({'sourceSha256':source_hash,'members':members},indent=2)+'\n')

if __name__ == '__main__':
    prepare()
