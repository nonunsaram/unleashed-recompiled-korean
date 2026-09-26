"""Install the corrected HD-first include order into the HMM Full mod."""
from __future__ import annotations

import configparser
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'UnleashedRecomp-Windows/mods/UnleashedKorean'
NEW = ROOT / 'Build/Development-v105c-Playtest/UnleashedKorean'
BACKUP = ROOT / 'Build/HMM-Backup-v105b-20260925/UnleashedKorean'
OUT = ROOT / 'Build/HMM-Install-v105c-Playtest/verification.json'
DB = ROOT / 'UnleashedRecomp-Windows/mods/ModsDB.ini'


def sha(path: Path) -> bytes:
    return hashlib.sha256(path.read_bytes()).digest()


def ini(path: Path) -> configparser.ConfigParser:
    result = configparser.ConfigParser(interpolation=None)
    result.read(path, encoding='utf-8-sig')
    return result


def main() -> None:
    verify = json.loads((NEW.parent / 'verification.json').read_text(encoding='utf8'))
    assert verify['passed'] and verify['archivePrecedenceChecked']
    assert MOD.is_dir() and not BACKUP.exists() and not OUT.exists()
    old = ini(MOD / 'mod.ini')
    assert old['Desc']['Version'].strip('"') == '1.0.5-review2'
    assert '전체판' in old['Desc']['Title']
    assert old['Main']['IncludeDir1'].strip('"') == '.'
    assert old['Main']['IncludeDir2'].strip('"') == 'Compatibility/UnleasHD-1.4.2'
    assert (MOD / 'KoreanFullSetup.exe').is_file()
    database_hash = sha(DB)
    setup_hash = sha(MOD / 'KoreanFullSetup.exe')
    hd_files = [p.relative_to(MOD) for p in (MOD / 'Compatibility/UnleasHD-1.4.2').rglob('*') if p.is_file()]
    assert len(hd_files) == 31
    for rel in hd_files:
        assert sha(MOD / rel) == sha(NEW / rel), rel

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(MOD, BACKUP)
    assert sha(MOD / 'mod.ini') == sha(BACKUP / 'mod.ini')
    try:
        mod_ini = MOD / 'mod.ini'
        text = mod_ini.read_text(encoding='utf-8-sig')
        assert 'Version="1.0.5-review2"' in text
        assert 'IncludeDir1="."\nIncludeDir2="Compatibility/UnleasHD-1.4.2"' in text
        text = text.replace('Version="1.0.5-review2"', 'Version="1.0.5-review3"', 1)
        text = text.replace('IncludeDir1="."\nIncludeDir2="Compatibility/UnleasHD-1.4.2"',
                            'IncludeDir1="Compatibility/UnleasHD-1.4.2"\nIncludeDir2="."', 1)
        mod_ini.write_text(text, encoding='utf8')

        schema_path = MOD / 'ConfigSchema.json'
        schema = json.loads(schema_path.read_text(encoding='utf8'))
        options = [e for g in schema['Groups'] for e in g['Elements'] if e['Type'] == 'UnleasHDCompatibility']
        assert len(options) == 1 and options[0]['Name'] == 'IncludeDir2'
        assert options[0]['Value'] == 'Compatibility/UnleasHD-1.4.2'
        options[0]['Name'] = 'IncludeDir1'
        options[0]['Description'] = [
            'UnleasHD 1.4.2 (1440p) 설치 시 선택하세요.',
            '한국어 패치를 UnleasHD보다 위에 두고 저장한 뒤 게임을 다시 시작하세요.',
            '호환 파일을 기본 한국어 파일보다 먼저 읽도록 하여 HUD·상점·결과 화면 등의 고해상도 UI를 적용합니다.',
        ]
        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        shutil.copy2(NEW / 'README-1.0.5-REVIEW-KO.md', MOD / 'README-1.0.5-REVIEW-KO.md')

        current = ini(MOD / 'mod.ini')
        assert current['Desc']['Version'].strip('"') == '1.0.5-review3'
        assert current['Main']['IncludeDir0'] == old['Main']['IncludeDir0']
        assert current['Main']['IncludeDir1'].strip('"') == 'Compatibility/UnleasHD-1.4.2'
        assert current['Main']['IncludeDir2'].strip('"') == '.'
        assert current['Main']['IncludeDir3'] == old['Main']['IncludeDir3']
        assert sha(MOD / 'KoreanFullSetup.exe') == setup_hash
        assert sha(DB) == database_hash
        assert all(sha(MOD / rel) == sha(NEW / rel) for rel in hd_files)
        assert sha(MOD / 'README-1.0.5-REVIEW-KO.md') == sha(NEW / 'README-1.0.5-REVIEW-KO.md')
        result = {'passed': True, 'version': '1.0.5-review3', 'edition': 'Full',
                  'installedMod': str(MOD), 'backup': str(BACKUP),
                  'hdCompatibilityEnabled': True, 'hdLayerBeforeBase': True,
                  'hdArchiveFilesPreserved': len(hd_files), 'hmmRestartNeeded': True,
                  'gameplayVerified': False}
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        shutil.copytree(BACKUP, MOD, dirs_exist_ok=True)
        raise


if __name__ == '__main__':
    main()
