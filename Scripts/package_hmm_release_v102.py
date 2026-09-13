"""Assemble reproducible v1.0.2 Basic and Full packages from v1.0.1."""
from pathlib import Path
import datetime,hashlib,json,shutil,zipfile
from configure_features_v102 import configure

R=Path(__file__).resolve().parents[1]
VERSION='1.0.2'
BASE=R/'outputs/GameBanana-1.0.1/UnleashedRecompiled-Korean-1.0.1-Basic.zip'
FULL=R/'outputs/GameBanana-1.0.1/UnleashedRecompiled-Korean-1.0.1-Full.zip'
BASE_SHA='760a62682d11567f6365d3b44e7b5508754a9019f09d66ff6f10010162365716'
FULL_SHA='7571e6794438fdd8c077ea360dcd8822f46057a302ba24b0580e6d8325afb96e'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def safe_extract(archive,destination):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for entry in z.infolist():
            p=Path(entry.filename)
            assert not p.is_absolute() and '..' not in p.parts and ':' not in entry.filename
            assert entry.filename.startswith('UnleashedKorean/')
        z.extractall(destination)

def update_config(root):
    configure(root)

def build():
    assert sha(BASE)==BASE_SHA and sha(FULL)==FULL_SHA
    output=R/f'outputs/GameBanana-{VERSION}'
    assert not output.exists(),'Preserve previous output; remove only a failed v1.0.2 output before retrying.'
    output.mkdir(parents=True)
    work=R/'Build'/('GameBanana-v102-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    basic=work/'Basic/UnleashedKorean';full=work/'Full/UnleashedKorean'
    safe_extract(BASE,basic.parent);safe_extract(FULL,full.parent)
    review=json.loads((R/'Build/Translation-v102/resource-verification.json').read_text(encoding='utf-8-sig'))
    assert review['passed'] and len(review['archives'])==25 and len(review['patches'])==50
    assert sum(x['changed_physical_cells'] for x in review['archives'])==170
    replaced=[]
    for root in (basic,full):
        for item in review['patches']:
            rel=Path(item['relative']);target=root/rel;source=R/'Build/Translation-v102/Resources'/rel
            assert target.is_file() and source.is_file() and sha(source)==item['after_sha256']
            before=sha(target);shutil.copy2(source,target)
            if root==basic:replaced.append({'relative':rel.as_posix(),'v101Sha256':before,'v102Sha256':sha(target)})
        update_config(root)
        compat=root/'Compatibility/UnleasHD-1.4.2/Languages/English';compat.mkdir(parents=True,exist_ok=True)
        for name in ('+WorldMap.ar.00','+WorldMap.arl'):
            source=R/'Build/UnleasHD-Compatibility-v102/Archive'/name
            assert source.is_file();shutil.copy2(source,compat/name)
        (root/'Compatibility/README-KO.txt').write_text(
            'UnleasHD 1.4.2 사용 시 HMM 모드 설정에서 UnleasHD 호환을 켜고, 한국어 패치를 UnleasHD보다 위에 두세요.\n',encoding='utf8')
    docs=R/'publish/unleashed-recompiled-korean/Release/v1.0.2'
    for root in (basic,full):
        shutil.copy2(docs/'MODS-KO.md',root/'MODS-KO.md')
    for lang in ('KO','EN'):
        bp=basic/f'README-{lang}.md'
        bp.write_text(bp.read_text(encoding='utf8').replace('1.0.1','1.0.2')+
            (docs/f'BASIC-CHANGES-{lang}.md').read_text(encoding='utf8'),encoding='utf8')
        shutil.copy2(docs/f'README-{lang}.md',full/f'README-{lang}.md')
    shutil.copy2(basic/'README-KO.md',full/'BASIC-README-KO.md')
    backend=R/'Build/FullBackend-v102/Package'
    support = (full/'Support').resolve()
    assert support.is_relative_to(work.resolve()) and support.name == 'Support'
    shutil.rmtree(support);shutil.copytree(backend/'Support',support)
    shutil.copy2(backend/'KoreanFullSetup.exe',full/'KoreanFullSetup.exe')
    public=R/'publish/unleashed-recompiled-korean'
    with zipfile.ZipFile(full/'Source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        allowed={'.py','.cs','.ps1','.md','.txt','.json','.cpp','.h','.patch','.ttf','.png','.pdf'}
        sources=[]
        for name in ('Scripts','Translation','Patches','Licenses','Assets/Installer','Assets/TitleLogo','Tools/Fonts','Release/v1.0.2'):
            folder=public/name
            if folder.exists():sources.extend(p for p in folder.rglob('*') if p.is_file())
        sources.extend(p for p in public.iterdir() if p.is_file())
        for p in sorted(set(sources)):
            if p.parent == docs and p.name in {'manifest.json','verification.json','SHA256SUMS.txt'}:continue
            if p.suffix.lower() in allowed and p.stat().st_size<100*1024*1024:
                z.write(p,'Source/'+p.relative_to(public).as_posix())
    archives=[]
    for edition,root in (('Basic',basic),('Full',full)):
        path=output/f'UnleashedRecompiled-Korean-{VERSION}-{edition}.zip'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in sorted(root.rglob('*')):
                if p.is_file():z.write(p,'UnleashedKorean/'+p.relative_to(root).as_posix())
                elif p.is_dir() and not any(p.iterdir()):z.write(p,'UnleashedKorean/'+p.relative_to(root).as_posix()+'/')
        with zipfile.ZipFile(path) as z:assert z.testzip() is None
        archives.append({'file':path.name,'sha256':sha(path),'bytes':path.stat().st_size})
    (output/'SHA256SUMS.txt').write_text(''.join(x['sha256']+'  '+x['file']+'\n' for x in archives),encoding='ascii')
    for name in ('GameBanana-post.md','GameBanana-update.md','Upload-guide-KO.md','CHANGELOG-KO.md','MODS-KO.md'):
        shutil.copy2(docs/name,output/name)
    manifest=json.loads((backend/'Support/manifest.json').read_text())
    verification={'version':VERSION,'archives':archives,'translationArchives':25,'translationRows':272,
        'changedPhysicalCells':170,'resourceFiles':50,'unleashHDCompatibility':'1.4.2',
        'compatibilityArchiveSha256':sha(R/'Build/UnleasHD-Compatibility-v102/Archive/+WorldMap.ar.00'),
        'setupSha256':sha(full/'KoreanFullSetup.exe'),'patchedExeSha256':manifest['files'][0]['patchedSha256'],
        'patchedExeChangedFromV101':False,'gameLaunched':False,'published':False,'replacedResources':replaced,
        'stagingDirectory':str(work),
        'userGameTest': {'finalLogoAccepted':True,'fourModsEnabledTogether':True,'exhaustiveCoverage':False},
        'titleLogoSha256':{v['name']:v['archiveSha256'] for v in json.loads((R/'Build/TitleLogo-v102/verification.json').read_text())['variants']}}
    (output/'package-verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    public_manifest={'version':VERSION,'assets':archives,'unleashHDCompatibility':'1.4.2',
        'compatibilityArchiveSha256':verification['compatibilityArchiveSha256'],
        'setupSha256':verification['setupSha256'],'patchedExeSha256':verification['patchedExeSha256'],
        'patchedExeChangedFromV101':False,'published':False,
        'userGameTest':verification['userGameTest'],'titleLogoSha256':verification['titleLogoSha256']}
    (docs/'manifest.json').write_text(json.dumps(public_manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(verification,ensure_ascii=False,indent=2))

if __name__=='__main__':build()
