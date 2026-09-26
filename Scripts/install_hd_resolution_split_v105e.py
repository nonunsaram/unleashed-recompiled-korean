"""Install review5 HD glyph overlay into the existing HMM Full mod."""
from __future__ import annotations

import configparser
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
OLD=ROOT/'Build/Development-v105d-Playtest/UnleashedKorean'
NEW=ROOT/'Build/Development-v105e-Playtest/UnleashedKorean'
BACKUP=ROOT/'Build/HMM-Backup-v105d-20260925/UnleashedKorean'
OUT=ROOT/'Build/HMM-Install-v105e-Playtest/verification.json'
DB=ROOT/'UnleashedRecomp-Windows/mods/ModsDB.ini'


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ini(path:Path)->configparser.ConfigParser:
    value=configparser.ConfigParser(interpolation=None)
    value.read(path,encoding='utf-8-sig')
    return value


def inventory(root:Path)->dict[Path,Path]:
    return {p.relative_to(root):p for p in root.rglob('*') if p.is_file()}


def main()->None:
    report=json.loads((NEW.parent/'verification.json').read_text(encoding='utf8'))
    assert report['passed'] and report['version']=='1.0.5-review5'
    assert MOD.is_dir() and NEW.is_dir() and not BACKUP.exists() and not OUT.exists()
    current=ini(MOD/'mod.ini')
    assert current['Desc']['Version'].strip('"')=='1.0.5-review4'
    assert '전체판' in current['Desc']['Title']
    assert current['Main']['IncludeDir1'].strip('"')=='Compatibility/UnleasHD-1.4.2'
    assert current['Main']['IncludeDir2'].strip('"')=='.'
    old_files=inventory(OLD)
    new_files=inventory(NEW)
    assert set(old_files)<=set(new_files)
    delta=sorted((p for p in new_files if p not in old_files or sha(new_files[p])!=sha(old_files[p])),key=str)
    compatibility=[p for p in delta if p.parts[0]=='Compatibility']
    assert len(delta)==35 and len(compatibility)==32
    assert set(delta)-set(compatibility)=={Path('mod.ini'),Path('ConfigSchema.json'),Path('README-1.0.5-REVIEW-KO.md')}
    db_hash=sha(DB)
    setup_hash=sha(MOD/'KoreanFullSetup.exe')
    base_hashes={p:sha(MOD/p) for p in (Path('Languages/English/+Sonic.ar.00'),Path('Languages/English/+Sonic.arl'))}
    old_schema=json.loads((MOD/'ConfigSchema.json').read_text(encoding='utf8'))
    new_schema=json.loads((NEW/'ConfigSchema.json').read_text(encoding='utf8'))
    old_option=next(x for g in old_schema['Groups'] for x in g['Elements'] if x['Type']=='UnleasHDCompatibility')
    new_option=next(x for g in new_schema['Groups'] for x in g['Elements'] if x['Type']=='UnleasHDCompatibility')
    assert old_option['Value']=='Compatibility/UnleasHD-1.4.2'
    assert new_option['Value']=='Compatibility/None'
    new_option['Value']=old_option['Value']
    for old_g,new_g in zip(old_schema['Groups'],new_schema['Groups']):
        for old_e,new_e in zip(old_g['Elements'],new_g['Elements']):
            if old_e['Type']!='UnleasHDCompatibility':
                new_e['Value']=old_e['Value']
    BACKUP.parent.mkdir(parents=True)
    shutil.copytree(MOD,BACKUP)
    assert sha(BACKUP/'mod.ini')==sha(MOD/'mod.ini')
    original_ini=(MOD/'mod.ini').read_text(encoding='utf-8-sig')
    assert original_ini.count('Version="1.0.5-review4"')==1
    try:
        for relative in compatibility:
            target=MOD/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(NEW/relative,target)
        (MOD/'mod.ini').write_text(original_ini.replace('Version="1.0.5-review4"',
                                           'Version="1.0.5-review5"',1),encoding='utf8')
        (MOD/'ConfigSchema.json').write_text(json.dumps(new_schema,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        shutil.copy2(NEW/'README-1.0.5-REVIEW-KO.md',MOD/'README-1.0.5-REVIEW-KO.md')
        installed=ini(MOD/'mod.ini')
        assert installed['Desc']['Version'].strip('"')=='1.0.5-review5'
        for section in current.sections():
            for key,value in current[section].items():
                if section=='Desc' and key=='version':continue
                assert installed[section][key]==value
        assert all(sha(MOD/relative)==sha(NEW/relative) for relative in compatibility)
        assert all(sha(MOD/p)==digest for p,digest in base_hashes.items())
        assert sha(MOD/'KoreanFullSetup.exe')==setup_hash and sha(DB)==db_hash
        check_schema=json.loads((MOD/'ConfigSchema.json').read_text(encoding='utf8'))
        check_option=next(x for g in check_schema['Groups'] for x in g['Elements'] if x['Type']=='UnleasHDCompatibility')
        assert check_option['Value']=='Compatibility/UnleasHD-1.4.2'
        result={'passed':True,'version':'1.0.5-review5','edition':'Full',
                'installedMod':str(MOD),'backup':str(BACKUP),
                'hdCompatibilityEnabled':True,'newHdGlyphAtlases':106,
                'hmmOptionsPreserved':True,'gameplayVerified':False}
        OUT.parent.mkdir(parents=True)
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(json.dumps(result,ensure_ascii=False))
    except Exception:
        for relative in compatibility:
            previous=BACKUP/relative
            target=MOD/relative
            if previous.is_file():shutil.copy2(previous,target)
            elif target.is_file():target.unlink()
        for name in ('mod.ini','ConfigSchema.json','README-1.0.5-REVIEW-KO.md'):
            shutil.copy2(BACKUP/name,MOD/name)
        raise


if __name__=='__main__':main()
