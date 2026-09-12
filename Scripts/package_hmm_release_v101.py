"""Assemble EXE-only v1.0.1 from verified Basic assets and the new backend.

Run build_native_korean_exe_v101.py and build_full_backend_v101.py first.
No installed game files or previous release outputs are modified.
"""
from pathlib import Path
import argparse, hashlib, json, shutil, zipfile, datetime

R=Path(__file__).resolve().parents[1]
VERSION='1.0.1'
BASE_SHA='b42667b076606f6d01ed0a2081cd6d57fdd034ed8da92e9d8f911599f3027429'
FULL_SHA='3612c84d112e0227e2e50d39bc1fa94e19a24565cd6c1a023eb17ee04bc00313'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def build(destination=None):
    output=Path(destination).resolve() if destination else R/'outputs/GameBanana-1.0.1'
    assert not output.exists(), 'Preserve previous outputs; choose a new --output directory.'
    public=R/'publish/unleashed-recompiled-korean'
    if not public.exists():public=R
    docs=public/'Release/v1.0.1'
    backend=R/'Build/FullBackend-v101/Package'
    manifest=json.loads((backend/'Support/manifest.json').read_text())
    assert manifest['schemaVersion']==2 and manifest['scope']=='native-exe'
    assert all(f['relative']=='UnleashedRecomp.exe' for f in manifest['files'])
    for f in manifest['files']:assert sha(backend/f['patch'])==f['patchSha256']
    original=R/'outputs/GameBanana-1.0.0/UnleashedRecompiled-Korean-1.0.0-Basic.zip'
    assert sha(original)==BASE_SHA
    oldfull=original.with_name(original.name.replace('-Basic.zip','-Full.zip'))
    assert sha(oldfull)==FULL_SHA
    for name in ('README-KO.md','README-EN.md','GameBanana-post.md','Upload-guide-KO.md'):assert (docs/name).is_file()
    output.mkdir(parents=True)
    work=R/'Build'/('GameBanana-v101-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));work.mkdir()
    basic=work/'Basic/UnleashedKorean'
    with zipfile.ZipFile(original) as z:
        assert z.testzip() is None
        for entry in z.infolist():
            p=Path(entry.filename)
            assert not p.is_absolute() and '..' not in p.parts and ':' not in entry.filename
            assert entry.filename.startswith('UnleashedKorean/')
        z.extractall(basic.parent)
    resources=R/'Build/Translation-v101'
    review=json.loads((resources/'resource-verification.json').read_text(encoding='utf-8-sig'))
    assert review['passed'] and len(review['archives'])==17
    assert sum(a['changed_physical_cells'] for a in review['archives'])==74
    for patch in review['patches']:
        relative=patch['relative'];assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
        target=basic/relative;updated=resources/'Resources'/relative
        assert sha(target)==patch['before_sha256'] and sha(updated)==patch['after_sha256']
        shutil.copy2(updated,target)
    ini=(basic/'mod.ini').read_text(encoding='utf8').replace('Version="1.0.0"','Version="1.0.1"')
    (basic/'mod.ini').write_text(ini,encoding='utf8')
    for lang in ('KO','EN'):
        p=basic/f'README-{lang}.md';p.write_text(p.read_text(encoding='utf8').replace('1.0.0','1.0.1'),encoding='utf8')
        with p.open('a',encoding='utf8') as f:f.write('\n'+(docs/f'BASIC-CHANGES-{lang}.md').read_text(encoding='utf8'))
    full=work/'Full/UnleashedKorean';shutil.copytree(basic,full)
    (full/'mod.ini').write_text(ini.replace('기본판','전체판').replace(
        'Description="','Description="옵션·도전과제는 KoreanFullSetup.exe로 추가 적용합니다. ',1),encoding='utf8')
    shutil.copy2(basic/'README-KO.md',full/'BASIC-README-KO.md')
    for lang in ('KO','EN'):shutil.copy2(docs/f'README-{lang}.md',full/f'README-{lang}.md')
    shutil.copytree(backend/'Support',full/'Support')
    shutil.copy2(backend/'KoreanFullSetup.exe',full/'KoreanFullSetup.exe')
    with zipfile.ZipFile(oldfull) as z:
        for name in z.namelist():
            prefix='UnleashedKorean/Support/Licenses/'
            if name.startswith(prefix) and not name.endswith('/'):
                target=full/'Support/Licenses'/Path(name).name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    # Only reviewed source/document/font assets, never game binaries or test fixtures.
    with zipfile.ZipFile(full/'Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        sources=[]
        for name in ('Scripts','Translation','Patches','Licenses','Assets/Installer','Tools/Fonts','Release/v1.0.1'):
            sources.extend(p for p in (public/name).rglob('*') if p.is_file())
        sources.extend(p for p in public.iterdir() if p.is_file() and p.suffix in ('.md','.txt'))
        metric=public/'Build/PlayableModWork/common-atlas.json'
        if metric.exists():sources.append(metric)
        allowed={'.py','.cs','.ps1','.md','.txt','.json','.cpp','.h','.patch','.ttf','.png','.pdf'}
        for p in sorted(set(sources)):
            if p.suffix.lower() in allowed:
                assert p.stat().st_size<100*1024*1024
                z.write(p,'Source/'+p.relative_to(public).as_posix())
    archives=[]
    for edition,folder in [('Basic',basic),('Full',full)]:
        path=output/f'UnleashedRecompiled-Korean-{VERSION}-{edition}.zip'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in sorted(folder.rglob('*')):
                if p.is_file():z.write(p,'UnleashedKorean/'+p.relative_to(folder).as_posix())
        with zipfile.ZipFile(path) as z:assert z.testzip() is None
        archives.append({'file':path.name,'sha256':sha(path),'bytes':path.stat().st_size})
    (output/'SHA256SUMS.txt').write_text(''.join(a['sha256']+'  '+a['file']+'\n' for a in archives),encoding='ascii')
    for name in ('GameBanana-post.md','Upload-guide-KO.md'):shutil.copy2(docs/name,output/name)
    (output/'package-verification.json').write_text(json.dumps({
        'version':VERSION,'archives':archives,'game_exe_sha256':manifest['files'][0]['patchedSha256'],
        'setup_sha256':sha(full/'KoreanFullSetup.exe'),'xex_patch':False,'published':False,
        'staging_directory':str(work)},indent=2),encoding='utf8')
    print(json.dumps(archives,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args();build(args.output)
