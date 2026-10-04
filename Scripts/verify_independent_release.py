"""Verify final independent packages against a frozen, asset-free release record."""
import argparse, configparser, hashlib, io, json, struct, tempfile, zipfile, subprocess
from pathlib import Path
from independent_option_paths import verify_option_directories

def sha(data): return hashlib.sha256(data).hexdigest()

def ar_members(data):
    assert data[:4] == b'\0\0\0\0', 'Compressed/unreadable archive'
    offset = struct.unpack_from('<I', data, 4)[0]
    while offset < len(data):
        size, length, start, _, _ = struct.unpack_from('<5I', data, offset)
        assert size >= 21 and start + length <= size and offset + size <= len(data)
        name = data[offset+20:data.index(0, offset+20, offset+start)].decode('utf8')
        yield name, data[offset+start:offset+start+length]
        offset += size
    assert offset == len(data)

def game_files(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in root.rglob('*')
            if p.is_file() and ('.ar.' in p.name or p.suffix in ('.arl', '.dds'))}

def verify_folder(root, record, edition):
    assert game_files(root) == record['approvedGameFiles'], 'Game payload changed'
    options = verify_option_directories(root)
    banned = set(record['unleasHDAndDerivedHashes'])
    owned = {x['sha256'] for x in record['blankCanvasProof']}
    count = dds = 0
    for p in root.rglob('*'):
        if not p.is_file(): continue
        rel = p.relative_to(root).as_posix()
        assert 'Compatibility/UnleasHD-' not in rel and p.name != 'UnleasHD-permission-texture-list.csv'
        blobs = list(ar_members(p.read_bytes())) if '.ar.' in p.name else [(p.name, p.read_bytes())]
        if '.ar.' in p.name: count += len(blobs)
        for name, blob in blobs:
            assert name != 'mat_stage_ss_082.dds'
            if name.endswith('.dds'): dds += 1
            assert sha(blob) not in banned - owned, (rel, name)
        if p.suffix == '.arl':
            data = p.read_bytes()
            assert b'mat_stage_ss_082.dds' not in data and data[:4] == b'ARL2'
            for i in range(struct.unpack_from('<I', data, 4)[0]):
                assert struct.unpack_from('<I', data, 8+i*4)[0] == (p.parent/(p.stem+f'.ar.{i:02}')).stat().st_size
    assert count == 1079
    cfg = configparser.ConfigParser(interpolation=None); cfg.read(root/'mod.ini', encoding='utf-8-sig')
    assert cfg['Desc']['Version'].strip('"') == record['version']
    assert cfg['Main']['IncludeDir1'].strip('"') == 'Compatibility/None'
    rows = json.loads((root/'Independent-image-provenance.json').read_text(encoding='utf8'))['outputs']
    assert len(rows) == 22
    for row in rows:
        blob = dict(ar_members((root/row['archive']).read_bytes()))[row['file']]
        assert sha(blob) == row['sha256']
    if edition == 'Full':
        for rel, digest in record['installerPayload'].items(): assert sha((root/rel).read_bytes()) == digest
        subprocess.run(['pwsh', '-NoProfile', '-File', str(Path(__file__).with_name('Verify-InstallerManifest.ps1')),
                        '-Installer', str(root/'KoreanFullSetup.exe'), '-Manifest', str(root/'Support/manifest.json')], check=True)
        manifest = json.loads((root/'Support/manifest.json').read_text(encoding='utf8'))
        assert manifest['version'] == record['version']
        for entry in manifest['files']: assert sha((root/entry['patch']).read_bytes()) == entry['patchSha256']
        with zipfile.ZipFile(root/'Source.zip') as z:
            assert z.testzip() is None
            assert any(n.endswith('render_independent_final_ui.py') for n in z.namelist())
            assert any(n.endswith('KoreanSupportSetup.cs') for n in z.namelist())
            for n in z.namelist():
                assert Path(n).suffix.lower() not in ('.dds','.exe','.dll','.arl','.zip') and '.ar.' not in n
    else:
        assert not (root/'Support').exists() and not (root/'KoreanFullSetup.exe').exists() and not (root/'Source.zip').exists()
    return dict(passed=True, archiveMembers=count, ddsInstancesScanned=dds, unexplainedUnleasHDOrDerivedHashHits=0, **options)

def verify_zip(path, record, edition):
    with tempfile.TemporaryDirectory(prefix='korean-release-') as temp:
        with zipfile.ZipFile(path) as z:
            names = z.namelist(); assert len(names) == len(set(names))
            assert all(n.startswith('UnleashedKorean/') and '..' not in Path(n).parts for n in names)
            assert z.testzip() is None
            z.extractall(temp)
        return verify_folder(Path(temp)/'UnleashedKorean', record, edition)

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('record',type=Path); p.add_argument('basic',type=Path); p.add_argument('full',type=Path); a=p.parse_args()
    record=json.loads(a.record.read_text(encoding='utf8'))
    print(json.dumps({e:verify_zip(z,record,e) for e,z in [('Basic',a.basic),('Full',a.full)]},indent=2))
