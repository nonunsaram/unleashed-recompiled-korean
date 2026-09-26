"""Install the review7 HD nameplate into the HMM Full playtest mod."""
from __future__ import annotations

import configparser
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
NEW=ROOT/'Build/Development-v105g-Playtest/UnleashedKorean'
BACKUP=ROOT/'Build/HMM-Backup-v105f-20260925/UnleashedKorean'
OUT=ROOT/'Build/HMM-Install-v105g-Playtest/verification.json'
DB=ROOT/'UnleashedRecomp-Windows/mods/ModsDB.ini'
RELS=[Path('Compatibility/UnleasHD-1.4.2/+Town_Common.arl'),
      Path('Compatibility/UnleasHD-1.4.2/+Town_Common.ar.00'),
      Path('README-1.0.5-REVIEW-KO.md')]


def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def ini(path:Path)->configparser.ConfigParser:
    out=configparser.ConfigParser(interpolation=None)
    out.read(path,encoding='utf-8-sig')
    return out


def main()->None:
    report=json.loads((NEW.parent/'verification.json').read_text(encoding='utf8'))
    assert report['passed'] and report['version']=='1.0.5-review7'
    assert MOD.is_dir() and not BACKUP.exists() and not OUT.exists()
    current=ini(MOD/'mod.ini')
    assert current['Desc']['Version'].strip('"')=='1.0.5-review6'
    assert current['Main']['IncludeDir1'].strip('"')=='Compatibility/UnleasHD-1.4.2'
    assert '전체판' in current['Desc']['Title']
    assert not (MOD/RELS[0]).exists() and not (MOD/RELS[1]).exists()
    db_hash=sha(DB);schema_hash=sha(MOD/'ConfigSchema.json')
    setup_hash=sha(MOD/'KoreanFullSetup.exe')
    base_hash=sha(MOD/'+Town_Common.ar.00')
    ini_text=(MOD/'mod.ini').read_text(encoding='utf-8-sig')
    assert ini_text.count('Version="1.0.5-review6"')==1
    BACKUP.parent.mkdir(parents=True)
    shutil.copytree(MOD,BACKUP)
    try:
        for relative in RELS:shutil.copy2(NEW/relative,MOD/relative)
        (MOD/'mod.ini').write_text(ini_text.replace('Version="1.0.5-review6"',
                                               'Version="1.0.5-review7"',1),encoding='utf8')
        installed=ini(MOD/'mod.ini')
        assert installed['Desc']['Version'].strip('"')=='1.0.5-review7'
        for section in current.sections():
            for key,value in current[section].items():
                if section=='Desc' and key=='version':continue
                assert installed[section][key]==value
        assert all(sha(MOD/r)==sha(NEW/r) for r in RELS)
        assert sha(MOD/'+Town_Common.ar.00')==base_hash
        assert sha(MOD/'ConfigSchema.json')==schema_hash
        assert sha(MOD/'KoreanFullSetup.exe')==setup_hash and sha(DB)==db_hash
        result={'passed':True,'version':'1.0.5-review7','edition':'Full',
                'installedMod':str(MOD),'backup':str(BACKUP),
                'hdCompatibilityEnabled':True,'hdNameplateInstalled':True,
                'hmmOptionsPreserved':True,'gameplayVerified':False}
        OUT.parent.mkdir(parents=True)
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(json.dumps(result,ensure_ascii=False))
    except Exception:
        for relative in RELS:
            previous=BACKUP/relative;target=MOD/relative
            if previous.is_file():shutil.copy2(previous,target)
            elif target.is_file():target.unlink()
        shutil.copy2(BACKUP/'mod.ini',MOD/'mod.ini')
        raise


if __name__=='__main__':main()
