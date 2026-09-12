"""Verify final Basic/Full archives and run extracted production installer tests."""
from pathlib import Path
import argparse, zipfile, hashlib, json, io, subprocess, sys, uuid, configparser

R=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()

def verify(output):
    output=Path(output).resolve();checks=[]
    report=json.loads((output/'package-verification.json').read_text())
    checksum_lines=(output/'SHA256SUMS.txt').read_text().splitlines()
    work=R/'Build'/('Package-v101-Verify-'+uuid.uuid4().hex);work.mkdir()
    packs={}
    for item in report['archives']:
        p=output/item['file'];assert sha(p.read_bytes())==item['sha256']
        assert item['sha256']+'  '+item['file'] in checksum_lines
        edition='Basic' if '-Basic.zip' in p.name else 'Full'
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            assert len(z.namelist())==len(set(z.namelist()))
            assert sum(n.endswith('/mod.ini') for n in z.namelist())==1
            for n in z.namelist():assert n.startswith('UnleashedKorean/') and '..' not in Path(n).parts and ':' not in n
            packs[edition]={n.removeprefix('UnleashedKorean/'):z.read(n) for n in z.namelist() if not n.endswith('/')}
            z.extractall(work/edition)
    checks.append('ZIP integrity, unique entries, safe paths and published checksums')
    basic,full=packs['Basic'],packs['Full']
    assert not any(Path(n).suffix.lower() in ('.exe','.dll','.xex') for n in basic)
    assert [n for n in full if Path(n).suffix.lower() in ('.exe','.dll','.xex')]==['KoreanFullSetup.exe']
    manifest=json.loads(full['Support/manifest.json'])
    assert manifest['schemaVersion']==2 and manifest['scope']=='native-exe'
    assert all(f['relative']=='UnleashedRecomp.exe' for f in manifest['files'])
    patch_names={f['patch'] for f in manifest['files']}
    assert {n for n in full if n.startswith('Support/Patches/')}==patch_names
    for f in manifest['files']:assert sha(full[f['patch']])==f['patchSha256']
    checks.append('Full contains only setup EXE and native EXE delta; no XEX delta/game binaries')
    prior=R/'outputs/GameBanana-1.0.0/UnleashedRecompiled-Korean-1.0.0-Basic.zip'
    with zipfile.ZipFile(prior) as z:
        original={n.removeprefix('UnleashedKorean/'):z.read(n) for n in z.namelist() if not n.endswith('/')}
    assert basic.keys()==original.keys()
    resource_review=json.loads((R/'Build/Translation-v101/resource-verification.json').read_text(encoding='utf-8-sig'))
    assert resource_review['passed'] and len(resource_review['archives'])==17
    edited={p['relative']:p for p in resource_review['patches']}
    count=0;changed=0
    for name,blob in original.items():
        if name not in ('README-KO.md','README-EN.md','mod.ini'):
            assert basic[name]==full[name],name
            if name in edited:
                assert sha(blob)==edited[name]['before_sha256']
                assert sha(basic[name])==edited[name]['after_sha256'];changed+=1
            else:
                assert basic[name]==blob,name;count+=1
    assert changed==len(edited)==34
    checks.append(str(count)+' retained Basic files unchanged; 34 reviewed archive files match verified dialogue edits; Basic and Full identical')
    for package in (basic,full):
        ini=configparser.ConfigParser();ini.read_string(package['mod.ini'].decode('utf8'))
        assert ini['Desc']['Version'].strip('"')=='1.0.1'
        assert ini['Main']['IncludeDir0'].strip('"')=='WorldMapVariants/AllDLC'
        assert ini['Main']['IncludeDirCount']=='2'
        assert package['ConfigSchema.json']==original['ConfigSchema.json']
    checks.append('HMM identity/schema/include order/default DLC preserved; Basic has no setup dependency')
    with zipfile.ZipFile(io.BytesIO(full['Source.zip'])) as z:
        assert z.testzip() is None
        assert not any(Path(n).suffix.lower() in ('.exe','.dll','.xex','.iso','.ar','.arl','.bin','.zst','.zip') for n in z.namelist())
        for name in ('KoreanSupportSetup.cs','KoreanSupportEngine.cs','build_native_korean_exe_v101.py','extend_native_font_v101.py','build_full_backend_v101.py','package_hmm_release_v101.py','test_full_backend_v101.py','test_full_release_v101.py','verify_package_v101.py','review_translation_v101.py','build_translation_resources_v101.ps1','subtitle_resource_functions.ps1','patch_opening_atlas.py','verify_translation_review_v101.py'):
            assert z.read('Source/Scripts/'+name)==(R/'Scripts'/name).read_bytes(),name
        for lang in ('KO','EN'):
            assert z.read('Source/Release/v1.0.1/README-'+lang+'.md')==full['README-'+lang+'.md']
    checks.append('bundled current backend/build/test/docs sources match; no game binaries in Source.zip')
    subprocess.run([sys.executable,str(R/'Scripts/test_full_release_v101.py'),'--package',str(work/'Full/UnleashedKorean')],check=True)
    checks.append('extracted final setup passed real EXE install/reinstall/restore and legacy migration tests')
    result={'passed':True,'checks':checks,'published':False,'game_exe_sha256':manifest['files'][0]['patchedSha256'],'setup_sha256':sha(full['KoreanFullSetup.exe'])}
    (output/'release-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default=str(R/'outputs/GameBanana-1.0.1'));verify(p.parse_args().output)
