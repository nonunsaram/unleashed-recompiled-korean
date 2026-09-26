"""Install the reviewed two-name update into the existing HMM Full mod."""
from __future__ import annotations

import configparser
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'Build/Development-v105-Review/UnleashedKorean'
PATCH = ROOT / 'Build/Development-v105b-Playtest/UnleashedKorean'
INSTALLED = ROOT / 'UnleashedRecomp-Windows/mods/UnleashedKorean'
MODSDB = ROOT / 'UnleashedRecomp-Windows/mods/ModsDB.ini'
BACKUP = ROOT / 'Build/HMM-Backup-v105-20260925/UnleashedKorean'
REPORT = ROOT / 'Build/HMM-Install-v105b-Playtest/verification.json'


def sha(path: Path) -> bytes:
    return hashlib.sha256(path.read_bytes()).digest()


def ini(path: Path) -> configparser.ConfigParser:
    data = configparser.ConfigParser(interpolation=None)
    data.read(path, encoding='utf-8-sig')
    return data


def main() -> None:
    verify = json.loads((PATCH.parent / 'verification.json').read_text(encoding='utf8'))
    assert verify['passed'] and not verify['gameplayVerified']
    assert BASE.is_dir() and PATCH.is_dir() and INSTALLED.is_dir()
    assert not BACKUP.exists() and not REPORT.exists()
    old = ini(INSTALLED / 'mod.ini')
    assert old['Desc']['Version'].strip('"') == '1.0.5-review'
    assert '전체판' in old['Desc']['Title']
    assert old['Main']['IncludeDir2'].strip('"') == 'Compatibility/UnleasHD-1.4.2'
    assert old['Main']['IncludeDir3'].strip('"') == 'TitleLogos/Korean'
    assert (INSTALLED / 'KoreanFullSetup.exe').is_file()
    db = ini(MODSDB)
    korean = db['Main']['ActiveMod0'].strip('"')
    hd = db['Main']['ActiveMod2'].strip('"')
    assert Path(db['Mods'][korean].strip('"')).resolve() == (INSTALLED / 'mod.ini').resolve()
    assert 'UnleasHD-1440p' in db['Mods'][hd]

    edited_archives = {r['archive'] for r in json.loads(
        (ROOT / 'Translation/review/proper-name-audit-v105b/resource-verification.json').read_text(encoding='utf8'))['archives']}
    assert len(edited_archives) == 8
    archive_files = sorted(p.relative_to(BASE) for p in (BASE / 'Languages/English').iterdir()
                           if p.is_file() and any(p.name.startswith('+' + a + '.ar.') or
                                                  p.name == '+' + a + '.arl' for a in edited_archives))
    assert len(archive_files) == 16
    docs = [Path(n) for n in ('README-1.0.5-REVIEW-KO.md', 'NAME-AUDIT-KO.md',
                             'NAME-RECOMMENDATIONS-KO.md', 'NAME-REGIONS-113.csv')]
    new_doc = Path('NAME-DECISIONS-REVIEW2-KO.md')
    assert not (INSTALLED / new_doc).exists()
    for rel in archive_files + docs:
        assert (INSTALLED / rel).is_file() and sha(INSTALLED / rel) == sha(BASE / rel), rel
        assert (PATCH / rel).is_file()

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(INSTALLED, BACKUP)
    assert sha(BACKUP / 'mod.ini') == sha(INSTALLED / 'mod.ini')
    changed = []
    try:
        for rel in archive_files + docs + [new_doc]:
            shutil.copy2(PATCH / rel, INSTALLED / rel)
            changed.append(rel)
        modini = INSTALLED / 'mod.ini'
        data = modini.read_text(encoding='utf-8-sig')
        assert 'Version="1.0.5-review"' in data
        modini.write_text(data.replace('Version="1.0.5-review"', 'Version="1.0.5-review2"', 1), encoding='utf8')
        changed.append(Path('mod.ini'))
        for rel in archive_files + docs + [new_doc]:
            assert sha(INSTALLED / rel) == sha(PATCH / rel), rel
        now = ini(INSTALLED / 'mod.ini')
        assert now['Desc']['Version'].strip('"') == '1.0.5-review2'
        assert now['Main']['IncludeDir0'] == old['Main']['IncludeDir0']
        assert now['Main']['IncludeDir2'] == old['Main']['IncludeDir2']
        assert now['Main']['IncludeDir3'] == old['Main']['IncludeDir3']
        assert sha(INSTALLED / 'KoreanFullSetup.exe') == sha(BACKUP / 'KoreanFullSetup.exe')
        assert sha(MODSDB) == sha(ROOT / 'UnleashedRecomp-Windows/mods/ModsDB.ini')
        result = {'passed': True, 'installedMod': str(INSTALLED), 'backup': str(BACKUP),
                  'version': '1.0.5-review2', 'edition': 'Full',
                  'nameArchiveFilesUpdated': len(archive_files), 'documentationFilesUpdated': len(docs)+1,
                  'hdCompatibilityEnabled': True, 'koreanPriority': 0, 'hdPriority': 2,
                  'fullInstallerPreserved': True, 'gameplayVerified': False}
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        (INSTALLED / new_doc).unlink(missing_ok=True)
        shutil.copytree(BACKUP, INSTALLED, dirs_exist_ok=True)
        raise


if __name__ == '__main__':
    main()
