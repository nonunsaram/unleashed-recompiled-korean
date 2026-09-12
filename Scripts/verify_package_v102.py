"""Verify final v1.0.2 archives, configuration, resources and installer."""
from pathlib import Path
import configparser,hashlib,io,json,subprocess,sys,uuid,zipfile

R=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
    output=R/'outputs/GameBanana-1.0.2'
    report=json.loads((output/'package-verification.json').read_text(encoding='utf8'))
    sums=(output/'SHA256SUMS.txt').read_text(encoding='ascii').splitlines()
    work=R/'Build'/('Package-v102-Verify-'+uuid.uuid4().hex);work.mkdir()
    packages={}
    for item in report['archives']:
        path=output/item['file'];blob=path.read_bytes();assert sha(blob)==item['sha256']
        assert item['sha256']+'  '+item['file'] in sums
        edition='Basic' if '-Basic.zip' in path.name else 'Full'
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
            for name in z.namelist():
                assert name.startswith('UnleashedKorean/') and '..' not in Path(name).parts and ':' not in name
            packages[edition]={n.removeprefix('UnleashedKorean/'):z.read(n) for n in z.namelist() if not n.endswith('/')}
            z.extractall(work/edition)
    basic,full=packages['Basic'],packages['Full']
    assert not any(Path(n).suffix.lower() in ('.exe','.dll','.xex') for n in basic)
    assert [n for n in full if Path(n).suffix.lower() in ('.exe','.dll','.xex')]==['KoreanFullSetup.exe']
    review=json.loads((R/'Build/Translation-v102/resource-verification.json').read_text(encoding='utf-8-sig'))
    assert review['passed'] and len(review['archives'])==25 and len(review['patches'])==50
    for item in review['patches']:
        assert sha(basic[item['relative']])==item['after_sha256']
        assert basic[item['relative']]==full[item['relative']]
    for package in (basic,full):
        ini=configparser.ConfigParser();ini.read_string(package['mod.ini'].decode('utf8'))
        assert ini['Desc']['Version'].strip('"')=='1.0.2'
        assert ini['Main']['IncludeDir2'].strip('"')=='Compatibility/None' and ini['Main']['IncludeDirCount']=='3'
        schema=json.loads(package['ConfigSchema.json'])
        assert schema['Enums']['UnleasHDCompatibility'][1]['Value']=='Compatibility/UnleasHD-1.4.2'
        prefix='Compatibility/UnleasHD-1.4.2/Languages/English/'
        assert sha(package[prefix+'+WorldMap.ar.00'])==report['compatibilityArchiveSha256']
        assert prefix+'+WorldMap.arl' in package
    manifest=json.loads(full['Support/manifest.json'])
    assert manifest['version']=='1.0.2' and manifest['scope']=='native-exe'
    assert manifest['files'][0]['patchedSha256']==report['patchedExeSha256']
    assert sha(full['KoreanFullSetup.exe'])==report['setupSha256']
    with zipfile.ZipFile(io.BytesIO(full['Source.zip'])) as z:
        assert z.testzip() is None
        assert not any(Path(n).suffix.lower() in ('.exe','.dll','.xex','.ar','.arl','.bin','.zip') for n in z.namelist())
        for name in ('build_full_backend_v102.py','package_hmm_release_v102.py','verify_package_v102.py',
                     'subtitle_resource_functions_v102.ps1','render_korean_ui_textures.py','ui_texture_layout_v041.py'):
            assert z.read('Source/Scripts/'+name)==(R/'publish/unleashed-recompiled-korean/Scripts'/name).read_bytes()
    subprocess.run([sys.executable,str(R/'Scripts/test_full_release_v101.py'),
        '--package',str(work/'Full/UnleashedKorean')],check=True)
    result={'passed':True,'zipIntegrity':True,'safePaths':True,'resourceFiles':50,
        'unleashHDCompatibilityVerified':True,'installerRealExeRoundTrip':True,
        'gameExeSha256':report['patchedExeSha256'],'setupSha256':report['setupSha256'],
        'actualGameLaunched':False,'published':False}
    (output/'release-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
