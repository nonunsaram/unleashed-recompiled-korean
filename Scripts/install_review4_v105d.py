"""Install review4 deltas into the existing HMM Full mod, preserving options."""
from __future__ import annotations

import configparser
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'UnleashedRecomp-Windows/mods/UnleashedKorean'
SOURCE = ROOT / 'Build/Development-v105d-Playtest/UnleashedKorean'
BACKUP = ROOT / 'Build/HMM-Backup-v105c-20260925/UnleashedKorean'
OUT = ROOT / 'Build/HMM-Install-v105d-Playtest/verification.json'
DB = ROOT / 'UnleashedRecomp-Windows/mods/ModsDB.ini'
RELS = [
    Path('Languages/English/+Sonic.ar.00'),
    Path('Languages/English/+Sonic.arl'),
    Path('Compatibility/UnleasHD-1.4.2/Languages/English/+ExStageTails_Common.ar.00'),
    Path('Compatibility/UnleasHD-1.4.2/Languages/English/+ExStageTails_Common.arl'),
    Path('README-1.0.5-REVIEW-KO.md'),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ini(path: Path) -> configparser.ConfigParser:
    out = configparser.ConfigParser(interpolation=None)
    out.read(path, encoding='utf-8-sig')
    return out


def main() -> None:
    report = json.loads((SOURCE.parent / 'verification.json').read_text(encoding='utf8'))
    assert report['passed'] and report['version'] == '1.0.5-review4'
    assert MOD.is_dir() and SOURCE.is_dir() and not BACKUP.exists() and not OUT.exists()
    current = ini(MOD / 'mod.ini')
    assert current['Desc']['Version'].strip('"') == '1.0.5-review3'
    assert '전체판' in current['Desc']['Title']
    assert current['Main']['IncludeDir1'].strip('"') == 'Compatibility/UnleasHD-1.4.2'
    assert current['Main']['IncludeDir2'].strip('"') == '.'
    assert (MOD / 'KoreanFullSetup.exe').is_file()
    db_hash = sha(DB)
    setup_hash = sha(MOD / 'KoreanFullSetup.exe')
    backup_ini = (MOD / 'mod.ini').read_text(encoding='utf-8-sig')
    assert backup_ini.count('Version="1.0.5-review3"') == 1
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(MOD, BACKUP)
    assert sha(MOD / 'mod.ini') == sha(BACKUP / 'mod.ini')
    try:
        for relative in RELS:
            shutil.copy2(SOURCE / relative, MOD / relative)
        (MOD / 'mod.ini').write_text(
            backup_ini.replace('Version="1.0.5-review3"', 'Version="1.0.5-review4"', 1), encoding='utf8')
        installed = ini(MOD / 'mod.ini')
        assert installed['Desc']['Version'].strip('"') == '1.0.5-review4'
        for section in current.sections():
            for key, value in current[section].items():
                if section == 'Desc' and key == 'version': continue
                assert installed[section][key] == value, (section, key)
        assert all(sha(MOD / relative) == sha(SOURCE / relative) for relative in RELS)
        assert sha(MOD / 'KoreanFullSetup.exe') == setup_hash
        assert sha(DB) == db_hash
        result = {'passed': True, 'version': '1.0.5-review4', 'edition': 'Full',
                  'installedMod': str(MOD), 'backup': str(BACKUP),
                  'hdCompatibilityEnabled': True, 'hmmOptionsPreserved': True,
                  'modsDatabasePreserved': True, 'gameplayVerified': False}
        OUT.parent.mkdir(parents=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        for relative in RELS + [Path('mod.ini')]:
            shutil.copy2(BACKUP / relative, MOD / relative)
        raise


if __name__ == '__main__': main()
