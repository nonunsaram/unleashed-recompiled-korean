"""Independent cumulative resource contract anchored to the final, approved 1.0.2 ZIP."""
from pathlib import Path
import hashlib, json, zipfile
R=Path(__file__).resolve().parents[1]
BASE=R/'outputs/GameBanana-1.0.2/UnleashedRecompiled-Korean-1.0.2-Basic.zip'
def sha(blob):return hashlib.sha256(blob).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def inputs():
    manifest=read(R/'publish/unleashed-recompiled-korean/Release/v1.0.2/manifest.json')
    item=next(x for x in manifest['assets'] if x['file']==BASE.name)
    assert sha(BASE.read_bytes())==item['sha256'],'Golden 1.0.2 package changed'
    with zipfile.ZipFile(BASE) as z:
        assert z.testzip() is None
        base={n.removeprefix('UnleashedKorean/'):z.read(n) for n in z.namelist() if not n.endswith('/')}
    translation=read(R/'Build/Translation-v103/resource-verification.json')
    assert translation['passed'] and len(translation['patches'])==42
    logo=read(R/'Build/TitleLogo-Choices/verification.json')
    assert logo['passed'] and len(logo['variants'])==5
    return base,translation,logo
META={'mod.ini','ConfigSchema.json','README-KO.md','README-EN.md','MODS-KO.md','CREDITS.md'}
def expected_hashes():
    base,translation,logo=inputs()
    expected={n:sha(b) for n,b in base.items() if n not in META and not n.startswith('TitleLogos/')}
    for item in translation['patches']:
        assert item['relative'] in expected
        expected[item['relative']]=item['after_sha256']
    for name,v in logo['variants'].items():
        for file,digest in v['archives'].items():expected[f'TitleLogos/{name}/{file}']=digest
    return expected
FULL_EXTRA={'BASIC-README-KO.md','KoreanFullSetup.exe','Source.zip','Support/InstallerLogo.png','Support/manifest.json','Support/Patches/exe-v103.krpatch.gz'}
def verify_payload(payload,full=False):
    expected=expected_hashes();ignore=META|(FULL_EXTRA if full else set())
    actual={n:sha(b) for n,b in payload.items() if n not in ignore}
    assert actual==expected,{'missing':sorted(set(expected)-set(actual)),'extra':sorted(set(actual)-set(expected)),
        'different':[n for n in expected.keys()&actual.keys() if expected[n]!=actual[n]]}
    assert not any(n.startswith('TitleLogos/Default/') for n in payload),'Default must not override title files'
    fix=read(R/'Build/LatinBaseline-Audit/packing-verification.json');count=0
    for a in fix['archives']:
        for p in a['parts']:
            assert sha(payload['Inspire/subtitle/English/'+p['name']])==p['sha256'];count+=1
    return {'passed':True,'cumulativeResourceFiles':len(expected),'baselineSubtitleFiles':count,'baselineSubtitleArchives':len(fix['archives']),'translationOverlayFiles':42,'unexpectedChanges':0}
def verify_folder(root):
    root=Path(root)
    return verify_payload({p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()})
