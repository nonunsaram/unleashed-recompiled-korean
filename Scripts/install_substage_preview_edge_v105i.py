"""Replace the review8 preview atlas with the aligned review9 version."""

from __future__ import annotations

import configparser
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "UnleashedRecomp-Windows/mods/UnleashedKorean"
OLD = ROOT / "Build/Development-v105h-Playtest/UnleashedKorean"
NEW = ROOT / "Build/Development-v105i-Playtest/UnleashedKorean"
BACKUP = ROOT / "Build/HMM-Backup-v105i-20260925"
REPORT = ROOT / "Build/HMM-Install-v105i-Playtest/verification.json"
DB = ROOT / "UnleashedRecomp-Windows/mods/ModsDB.ini"
FILES = [Path("Compatibility/UnleasHD-1.4.2/+WorldMap.ar.00"),
         Path("Compatibility/UnleasHD-1.4.2/+WorldMap.arl"),
         Path("README-1.0.5-REVIEW-KO.md"), Path("mod.ini")]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_ini(path: Path) -> configparser.ConfigParser:
    result = configparser.ConfigParser(interpolation=None)
    result.read(path, encoding="utf-8-sig")
    return result


def main() -> None:
    source_report = json.loads((NEW.parent / "verification.json").read_text(encoding="utf8"))
    assert source_report["passed"] and source_report["version"] == "1.0.5-review9"
    assert MOD.is_dir() and not BACKUP.exists() and not REPORT.exists()
    current = load_ini(MOD / "mod.ini")
    assert current["Desc"]["Version"].strip('"') == "1.0.5-review8"
    assert "전체판" in current["Desc"]["Title"]
    assert current["Main"]["IncludeDir1"].strip('"') == "Compatibility/UnleasHD-1.4.2"
    assert all(digest(MOD / relative) == digest(OLD / relative) for relative in FILES[:2])
    ini_text = (MOD / "mod.ini").read_text(encoding="utf-8-sig")
    assert ini_text.count('Version="1.0.5-review8"') == 1
    preserved = {str(path): digest(path) for path in
                 (DB, MOD / "ConfigSchema.json", MOD / "KoreanFullSetup.exe",
                  MOD / "+Town_Common.ar.00")}

    for relative in FILES:
        target = BACKUP / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MOD / relative, target)
    try:
        for relative in FILES[:3]:
            shutil.copy2(NEW / relative, MOD / relative)
        (MOD / "mod.ini").write_text(
            ini_text.replace('Version="1.0.5-review8"',
                             'Version="1.0.5-review9"', 1), encoding="utf8")
        installed = load_ini(MOD / "mod.ini")
        assert installed["Desc"]["Version"].strip('"') == "1.0.5-review9"
        for section in current.sections():
            for key, value in current[section].items():
                if section == "Desc" and key == "version":
                    continue
                assert installed[section][key] == value
        assert all(digest(MOD / relative) == digest(NEW / relative)
                   for relative in FILES[:3])
        assert all(digest(Path(path)) == value for path, value in preserved.items())
        result = {"passed": True, "version": "1.0.5-review9", "edition": "Full",
                  "installedMod": str(MOD), "backup": str(BACKUP),
                  "correctedAsset": "mat_stage_ss_082.dds",
                  "archiveSha256": digest(MOD / FILES[0]),
                  "hmmOptionsPreserved": True, "gameplayVerified": False,
                  "publicRelease": False}
        REPORT.parent.mkdir(parents=True)
        REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf8")
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        for relative in FILES:
            shutil.copy2(BACKUP / relative, MOD / relative)
        raise


if __name__ == "__main__":
    main()
