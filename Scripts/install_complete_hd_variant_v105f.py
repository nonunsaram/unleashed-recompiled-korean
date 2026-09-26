"""Install review6 into the HMM Full mod while preserving user selections."""
from __future__ import annotations

import configparser
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
OLD=ROOT/'Build/Development-v105e-Playtest/UnleashedKorean'
NEW=ROOT/'Build/Development-v105f-Playtest/UnleashedKorean'
BACKUP=ROOT/'Build/HMM-Backup-v105e-20260925/UnleashedKorean'
OUT=ROOT/'Build/HMM-Install-v105f-Playtest/verification.json'
DB=ROOT/'UnleashedRecomp-Windows/mods/ModsDB.ini'


def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root:Path)->dict[Path,Path]:
    return {p.relative_to(root):p for p in root.rglob('*') if p.is_file()}


def ini(path:Path)->configparser.ConfigParser:
    out=configparser.ConfigParser(interpolation=None)
    out.read(path,encoding='utf-8-sig')
    return out


def main()->None:
    report=json.loads((NEW.parent/'verification.json').read_text(encoding='utf8'))
    assert report['passed'] and report['version']=='1.0.5-review6'
    assert MOD.is_dir() and not BACKUP.exists() and not OUT.exists()
    current=ini(MOD/'mod.ini')
    assert current['Desc']['Version'].strip('"')=='1.0.5-review5'
    assert '전체판' in current['Desc']['Title']
    assert current['Main']['IncludeDir1'].strip('"')=='Compatibility/UnleasHD-1.4.2'
    assert current['Main']['IncludeDir2'].strip('"')=='.'
    before,after=inventory(OLD),inventory(NEW)
    assert set(before)<=set(after)
    delta=sorted((p for p in after if p not in before or sha(after[p])!=sha(before[p])),key=str)
    compat=[p for p in delta if p.parts[0]=='Compatibility']
    assert len(delta)==91 and len(compat)==89
    assert set(delta)-set(compat)=={Path('mod.ini'),Path('README-1.0.5-REVIEW-KO.md')}
    database_hash=sha(DB)
    setup_hash=sha(MOD/'KoreanFullSetup.exe')
    schema_hash=sha(MOD/'ConfigSchema.json')
    base_hash=sha(MOD/'Languages/English/+Sonic.ar.00')
    ini_text=(MOD/'mod.ini').read_text(encoding='utf-8-sig')
    assert ini_text.count('Version="1.0.5-review5"')==1
    BACKUP.parent.mkdir(parents=True)
    shutil.copytree(MOD,BACKUP)
    assert sha(BACKUP/'mod.ini')==sha(MOD/'mod.ini')
    try:
        for relative in compat:
            target=MOD/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(NEW/relative,target)
        (MOD/'mod.ini').write_text(ini_text.replace('Version="1.0.5-review5"',
                                               'Version="1.0.5-review6"',1),encoding='utf8')
        shutil.copy2(NEW/'README-1.0.5-REVIEW-KO.md',MOD/'README-1.0.5-REVIEW-KO.md')
        installed=ini(MOD/'mod.ini')
        assert installed['Desc']['Version'].strip('"')=='1.0.5-review6'
        for section in current.sections():
            for key,value in current[section].items():
                if section=='Desc' and key=='version':continue
                assert installed[section][key]==value
        assert all(sha(MOD/p)==sha(NEW/p) for p in compat)
        assert sha(MOD/'ConfigSchema.json')==schema_hash
        assert sha(MOD/'Languages/English/+Sonic.ar.00')==base_hash
        assert sha(MOD/'KoreanFullSetup.exe')==setup_hash and sha(DB)==database_hash
        result={'passed':True,'version':'1.0.5-review6','edition':'Full',
                'installedMod':str(MOD),'backup':str(BACKUP),
                'hdCompatibilityEnabled':True,'hdWorldMapGlyphPages':7,
                'hdCutsceneKoreanPages':46,'hmmOptionsPreserved':True,
                'gameplayVerified':False}
        OUT.parent.mkdir(parents=True)
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(json.dumps(result,ensure_ascii=False))
    except Exception:
        for relative in compat:
            original=BACKUP/relative
            target=MOD/relative
            if original.is_file():shutil.copy2(original,target)
            elif target.is_file():target.unlink()
        for name in ('mod.ini','README-1.0.5-REVIEW-KO.md'):
            shutil.copy2(BACKUP/name,MOD/name)
        raise


if __name__=='__main__':main()
