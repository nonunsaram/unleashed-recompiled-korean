"""Inventory real archive members, not just archive filenames. Read-only to installed mods."""
from pathlib import Path
import hashlib, json, struct, subprocess, zipfile, shutil, zlib
from bounded_archive_tool import unpack

R = Path(__file__).resolve().parents[1]
OUT = R/'Analysis/ModCompatibility-v102'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()

def atomic_json(path, data):
    temp = path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(data, indent=2)+'\n', encoding='utf8')
    temp.replace(path)

def resume_zip(z, work):
    for info in z.infolist():
        target = work/info.filename
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if target.exists() and target.stat().st_size == info.file_size:
            crc = 0
            with target.open('rb') as stream:
                while chunk := stream.read(1024*1024): crc = zlib.crc32(chunk, crc)
            if crc == info.CRC:
                continue
        if target.exists():
            backup = target.with_name(target.name+'.before-recovery')
            if not backup.exists(): shutil.copy2(target, backup)
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name(target.name+'.tmp')
        with z.open(info) as source, temp.open('wb') as dest:
            shutil.copyfileobj(source, dest, 1024*1024)
        temp.replace(target)

def arl_names(blob):
    assert blob[:4] == b'ARL2'
    pos = 8 + 4 * struct.unpack_from('<I', blob, 4)[0]
    result = []
    while pos < len(blob):
        size = blob[pos]; pos += 1
        result.append(blob[pos:pos+size].decode('utf8')); pos += size
    assert pos == len(blob)
    return result

def main():
    korean = R/'Build/Development-v102/UnleashedKorean'
    references = {}
    for p in korean.rglob('*.arl'):
        for name in arl_names(p.read_bytes()):
            references.setdefault(name.casefold(), []).append(p.relative_to(korean).as_posix())
    summaries = []
    for archive in sorted(OUT.glob('*.zip')):
        work = OUT/'Extracted'/archive.stem
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist():
                path = Path(info.filename)
                assert not path.is_absolute() and '..' not in path.parts and ':' not in info.filename
            resume_zip(z, work)
        results = []
        archives = sorted(work.rglob('*.ar.00'))
        for i, ar in enumerate(archives):
            unpacked = ar.with_name(ar.name[:-6])
            marker = ar.with_name(ar.name+'.members.json')
            if marker.exists():
                members = json.loads(marker.read_text())
                for member in members:
                    cached = unpacked/member['name']
                    assert cached.is_file() and cached.stat().st_size == member['bytes'] and digest(cached) == member['sha256'], f'Cached extraction changed: {cached}'
            else:
                try:
                    unpack(ar)
                except (subprocess.TimeoutExpired, RuntimeError, OSError) as error:
                    results.append({'archive': ar.relative_to(work).as_posix(), 'memberCount': 0,
                                    'collisions': [], 'members': [], 'error': str(error)})
                    print('Could not decode', ar.name, type(error).__name__, flush=True)
                    atomic_json(OUT/(archive.stem+'-progress.json'), results)
                    continue
                assert unpacked.is_dir(), ar
                members = [{'name': p.relative_to(unpacked).as_posix(), 'bytes': p.stat().st_size,
                            'sha256': digest(p)} for p in sorted(unpacked.rglob('*')) if p.is_file()]
                atomic_json(marker, members)
            hits = [{**m, 'koreanArchives': references[m['name'].casefold()]} for m in members if m['name'].casefold() in references]
            text_members = [m['name'] for m in members if m['name'].endswith(('.fco', '.fte', '.yncp')) or 'subtitle' in m['name'].casefold()]
            results.append({'archive': ar.relative_to(work).as_posix(), 'memberCount': len(members),
                            'collisions': hits, 'textOrLayoutMembers': text_members, 'members': members})
            atomic_json(OUT/(archive.stem+'-progress.json'), results)
            if i % 20 == 0:
                print(archive.name, i+1, '/', len(archives), flush=True)
        report = {'download': archive.name, 'sha256': digest(archive),
                  'archiveCount': len(results), 'memberCount': sum(r['memberCount'] for r in results),
                  'collisions': [dict(archive=r['archive'], **m) for r in results for m in r['collisions']],
                  'decodeFailures': [r for r in results if 'error' in r],
                  'gameLaunched': False, 'archives': results}
        atomic_json(OUT/(archive.stem+'-audit.json'), report)
        summaries.append({k: v for k, v in report.items() if k != 'archives'})
        print('Completed', archive.name, 'collisions', len(report['collisions']), flush=True)
    atomic_json(OUT/'summary.json', summaries)

if __name__ == '__main__':
    main()
