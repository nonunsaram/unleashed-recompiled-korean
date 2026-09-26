"""Install review14 over the existing Full review12 without changing user options."""

from __future__ import annotations

import configparser
import hashlib
import json
import shutil
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "Build/Development-v105n-Playtest/UnleashedKorean"
PREVIOUS = ROOT / "Build/Development-v105l-Playtest/UnleashedKorean"
FULL = ROOT / "UnleashedRecomp-Windows/mods/UnleashedKorean"
BACKUP = ROOT / "Build/HMM-Backup-v105n-20260926"
REPORT = ROOT / "Build/HMM-Install-v105n-Playtest/verification.json"
BUILD = ROOT / "Build/Development-v105n-Playtest/verification.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ini(path: Path) -> configparser.ConfigParser:
    config = configparser.ConfigParser(interpolation=None)
    config.read(path, encoding="utf-8-sig")
    return config


def main() -> None:
    assert STAGE.is_dir() and PREVIOUS.is_dir() and FULL.is_dir()
    assert not BACKUP.exists() and not REPORT.exists()
    running = [(p.name(), p.pid) for p in psutil.process_iter()
               if any(name in p.name().lower()
                      for name in ("hedgemodmanager", "unleashedrecomp"))]
    assert not running, f"Close game/HMM before installing: {running}"
    build = json.loads(BUILD.read_text(encoding="utf8"))
    assert build["passed"] and build["version"] == "1.0.5-review14"

    source = {p.relative_to(PREVIOUS) for p in PREVIOUS.rglob("*") if p.is_file()}
    target = {p.relative_to(STAGE) for p in STAGE.rglob("*") if p.is_file()}
    assert source == target
    changed = {p for p in source if p not in {Path("mod.ini"), Path("README-1.0.5-REVIEW-KO.md")}
               and sha(STAGE / p) != sha(PREVIOUS / p)}
    logo = {Path("TitleLogos/Custom/Loading/OPmovie_titlelogo_EN.dds"),
            Path("TitleLogos/Custom/Loading/OPmovie_titlelogo_JP.dds")}
    assert logo <= changed and len(changed) == 32, len(changed)
    assert all(p.as_posix().startswith("Compatibility/UnleasHD-1.4.2/Inspire/subtitle/English/")
               for p in changed - logo)
    files = changed | {Path("mod.ini"), Path("README-1.0.5-REVIEW-KO.md")}

    old = ini(FULL / "mod.ini")
    assert old["Desc"]["Version"].strip('"') == "1.0.5-review12"
    assert "전체판" in old["Desc"]["Title"]
    assert old["Main"]["IncludeDir1"].strip('"') == "Compatibility/UnleasHD-1.4.2"
    assert old["Main"]["IncludeDir3"].strip('"') == "TitleLogos/Custom"
    for p in changed:
        assert (FULL / p).is_file() and sha(FULL / p) == sha(PREVIOUS / p), p
    fixed = {p: sha(FULL / p) for p in (
        Path("ConfigSchema.json"), Path("KoreanFullSetup.exe"),
        Path("TitleLogos/Korean/Loading/OPmovie_titlelogo_EN.dds"),
        Path("TitleLogos/Korean/+Title.ar.00"),
        Path("TitleLogos/Custom/+Title.ar.00"))}

    for p in files:
        dest = BACKUP / p
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(FULL / p, dest)
    try:
        for p in changed:
            shutil.copy2(STAGE / p, FULL / p)
        ini_file = FULL / "mod.ini"
        raw = ini_file.read_text(encoding="utf-8-sig")
        assert raw.count('Version="1.0.5-review12"') == 1
        ini_file.write_text(raw.replace('Version="1.0.5-review12"',
                                        'Version="1.0.5-review14"', 1), encoding="utf8")
        readme = FULL / "README-1.0.5-REVIEW-KO.md"
        raw = readme.read_text(encoding="utf8")
        assert raw.startswith("# 한국어 패치 1.0.5-review12 플레이 테스트 후보")
        raw = raw.replace("# 한국어 패치 1.0.5-review12 플레이 테스트 후보",
                          "# 한국어 패치 1.0.5-review14 플레이 테스트 후보", 1)
        raw += ("\nHD 컷신의 영문·숫자·문장부호를 한글과 같은 기준선에 맞췄습니다. "
                "월드 어드벤처 오프닝의 한국어 문구를 유지하면서 로고 윗선과 지구 왼쪽 "
                "흰 윤곽선을 보완했습니다.\n")
        readme.write_text(raw, encoding="utf8")

        assert all(sha(FULL / p) == sha(STAGE / p) for p in changed)
        assert all(sha(FULL / p) == digest for p, digest in fixed.items())
        new = ini(FULL / "mod.ini")
        for section in old.sections():
            for key, value in old[section].items():
                if section == "Desc" and key == "version":
                    continue
                assert new[section][key] == value, (section, key)
        report = {
            "passed": True, "version": "1.0.5-review14", "edition": "Full",
            "installedMod": str(FULL), "backup": str(BACKUP),
            "archivePartsChanged": len(changed) - 2, "openingTexturesChanged": 2,
            "selectedLogo": new["Main"]["IncludeDir3"].strip('"'),
            "otherSettingsAndAssetsPreserved": True,
            "gameplayVerified": False, "publicRelease": False,
        }
        REPORT.parent.mkdir(parents=True)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf8")
        print(json.dumps(report, ensure_ascii=False))
    except Exception:
        for p in files:
            shutil.copy2(BACKUP / p, FULL / p)
        raise


if __name__ == "__main__":
    main()
