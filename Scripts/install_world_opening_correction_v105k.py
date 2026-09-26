"""Update the installed Full mod to the corrected review11 opening logo."""

from __future__ import annotations

from pathlib import Path
import configparser
import hashlib
import json
import shutil


ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
SOURCE=ROOT/'Build/Development-v105k-Playtest/UnleashedKorean'
BACKUP=ROOT/'Build/HMM-Backup-v105k-20260925'
REPORT=ROOT/'Build/HMM-Install-v105k-Playtest/verification.json'
FILES=[Path('TitleLogos/Custom/Loading/OPmovie_titlelogo_EN.dds'),
       Path('TitleLogos/Custom/Loading/OPmovie_titlelogo_JP.dds'),
       Path('README-1.0.5-REVIEW-KO.md'),Path('mod.ini')]


def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ini(path:Path)->configparser.ConfigParser:
    result=configparser.ConfigParser(interpolation=None)
    result.read(path,encoding='utf-8-sig')
    return result


def main()->None:
    report=json.loads((SOURCE.parent/'verification.json').read_text(encoding='utf8'))
    assert report['passed'] and report['version']=='1.0.5-review11'
    assert MOD.is_dir() and not BACKUP.exists() and not REPORT.exists()
    old=ini(MOD/'mod.ini')
    assert old['Desc']['Version'].strip('"')=='1.0.5-review10'
    assert '전체판' in old['Desc']['Title']
    assert all((MOD/p).is_file() and (SOURCE/p).is_file() for p in FILES)
    before={str(p):digest(p) for p in (
        ROOT/'UnleashedRecomp-Windows/mods/ModsDB.ini',
        MOD/'ConfigSchema.json',MOD/'KoreanFullSetup.exe',
        MOD/'TitleLogos/Korean/Loading/OPmovie_titlelogo_EN.dds',
        MOD/'TitleLogos/Korean/+Title.ar.00',
        MOD/'TitleLogos/Custom/+Title.ar.00')}
    for rel in FILES:
        destination=BACKUP/rel
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(MOD/rel,destination)
    try:
        for rel in FILES[:3]:
            shutil.copy2(SOURCE/rel,MOD/rel)
        current=(MOD/'mod.ini').read_text(encoding='utf-8-sig')
        assert current.count('Version="1.0.5-review10"')==1
        (MOD/'mod.ini').write_text(current.replace('Version="1.0.5-review10"',
            'Version="1.0.5-review11"',1),encoding='utf8')
        new=ini(MOD/'mod.ini')
        assert new['Desc']['Version'].strip('"')=='1.0.5-review11'
        for section in old.sections():
            for key,value in old[section].items():
                if section=='Desc' and key=='version':continue
                assert new[section][key]==value
        assert all(digest(MOD/p)==digest(SOURCE/p) for p in FILES[:3])
        assert all(digest(Path(p))==value for p,value in before.items())
        result={'passed':True,'version':'1.0.5-review11','edition':'Full',
                'installedMod':str(MOD),'backup':str(BACKUP),
                'selectedLogo':new['Main']['IncludeDir3'].strip('"'),
                'worldLogoSha256':digest(MOD/FILES[0]),
                'koreanUnleashedLogoUnchanged':True,
                'otherSettingsAndAssetsPreserved':True,
                'gameplayVerified':False,'publicRelease':False}
        REPORT.parent.mkdir(parents=True)
        REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(json.dumps(result,ensure_ascii=False))
    except Exception:
        for rel in FILES:shutil.copy2(BACKUP/rel,MOD/rel)
        raise


if __name__=='__main__':main()
