"""Install the review10 opening overlays into the current Full test mod."""

from __future__ import annotations

import configparser
import hashlib
import json
import shutil
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
SOURCE=ROOT/'Build/Development-v105j-Playtest/UnleashedKorean'
BACKUP=ROOT/'Build/HMM-Backup-v105j-20260925'
REPORT=ROOT/'Build/HMM-Install-v105j-Playtest/verification.json'
DB=ROOT/'UnleashedRecomp-Windows/mods/ModsDB.ini'
ADDED=[Path('TitleLogos')/v/'Loading'/f'OPmovie_titlelogo_{lang}.dds'
       for v in ('Korean','Custom') for lang in ('EN','JP')]
CHANGED=[Path('mod.ini'),Path('ConfigSchema.json'),Path('README-1.0.5-REVIEW-KO.md')]


def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ini(path:Path)->configparser.ConfigParser:
    out=configparser.ConfigParser(interpolation=None)
    out.read(path,encoding='utf-8-sig')
    return out


def main()->None:
    source_report=json.loads((SOURCE.parent/'verification.json').read_text(encoding='utf8'))
    assert source_report['passed'] and source_report['version']=='1.0.5-review10'
    assert MOD.is_dir() and not BACKUP.exists() and not REPORT.exists()
    old=ini(MOD/'mod.ini')
    assert old['Desc']['Version'].strip('"')=='1.0.5-review9'
    assert '전체판' in old['Desc']['Title']
    assert old['Main']['IncludeDir3'].strip('"') in {'TitleLogos/Korean','TitleLogos/Custom',
        'TitleLogos/Default','TitleLogos/Original','TitleLogos/Japanese'}
    assert all(not (MOD/p).exists() for p in ADDED)
    before={str(p):digest(p) for p in (DB,MOD/'KoreanFullSetup.exe',
              MOD/'+Town_Common.ar.00',MOD/'TitleLogos/Korean/+Title.ar.00',
              MOD/'TitleLogos/Custom/+Title.ar.00')}
    for rel in CHANGED:
        target=BACKUP/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(MOD/rel,target)
    try:
        for rel in ADDED:
            target=MOD/rel;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(SOURCE/rel,target)
        for rel in CHANGED[1:]:
            shutil.copy2(SOURCE/rel,MOD/rel)
        current=(MOD/'mod.ini').read_text(encoding='utf-8-sig')
        assert current.count('Version="1.0.5-review9"')==1
        (MOD/'mod.ini').write_text(current.replace('Version="1.0.5-review9"',
             'Version="1.0.5-review10"',1),encoding='utf8')
        new=ini(MOD/'mod.ini')
        assert new['Desc']['Version'].strip('"')=='1.0.5-review10'
        for section in old.sections():
            for key,value in old[section].items():
                if section=='Desc' and key=='version':continue
                assert new[section][key]==value
        assert all(digest(MOD/rel)==digest(SOURCE/rel) for rel in ADDED+CHANGED[1:])
        assert all(digest(Path(p))==value for p,value in before.items())
        schema=json.loads((MOD/'ConfigSchema.json').read_text(encoding='utf8'))
        entries={e['Value']:e for e in schema['Enums']['TitleLogoVariant']}
        assert all('오프닝' in entries[f'TitleLogos/{v}']['Description'][0]
                   for v in ('Korean','Custom'))
        result={'passed':True,'version':'1.0.5-review10','edition':'Full',
                'installedMod':str(MOD),'backup':str(BACKUP),
                'selectedLogo':new['Main']['IncludeDir3'].strip('"'),
                'openingAssets':[p.as_posix() for p in ADDED],
                'hmmSettingsAndOtherAssetsPreserved':True,
                'gameplayVerified':False,'publicRelease':False}
        REPORT.parent.mkdir(parents=True)
        REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(json.dumps(result,ensure_ascii=False))
    except Exception:
        for rel in CHANGED:shutil.copy2(BACKUP/rel,MOD/rel)
        for rel in ADDED:
            if (MOD/rel).exists():(MOD/rel).unlink()
        raise


if __name__=='__main__':main()
