"""Prepare a local review8 Basic playtest with the Empire City Act 2 preview fix."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Build/Development-v105g-Playtest/UnleashedKorean"
OUTPUT = ROOT / "Build/Development-v105h-Playtest/UnleashedKorean"
PATCH = ROOT / "Build/SubStage02Investigation/Candidate/Pack"
ZIP = ROOT / "outputs/UnleashedRecompiled-Korean-1.0.5-Review8-LocalPlaytest.zip"
RELATIVE = Path("Compatibility/UnleasHD-1.4.2")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert SOURCE.is_dir() and not OUTPUT.exists() and not ZIP.exists()
    assert json.loads((PATCH.parent / "verification.json").read_text(encoding="utf8"))["passed"]
    shutil.copytree(SOURCE, OUTPUT)
    destination = OUTPUT / RELATIVE
    for name in ("+WorldMap.ar.00", "+WorldMap.arl"):
        assert not (destination / name).exists()
        shutil.copy2(PATCH / name, destination / name)
        assert digest(PATCH / name) == digest(destination / name)

    ini = OUTPUT / "mod.ini"
    old = ini.read_text(encoding="utf-8-sig")
    assert old.count('Version="1.0.5-review7"') == 1
    ini.write_text(old.replace('Version="1.0.5-review7"',
                               'Version="1.0.5-review8"', 1), encoding="utf8")
    readme = OUTPUT / "README-1.0.5-REVIEW-KO.md"
    content = readme.read_text(encoding="utf8")
    assert content.startswith("# 한국어 패치 1.0.5-review7 플레이 테스트 후보")
    content = content.replace("# 한국어 패치 1.0.5-review7 플레이 테스트 후보",
                              "# 한국어 패치 1.0.5-review8 플레이 테스트 후보", 1)
    content += ("\n엠파이어 시티의 스카이스크레이퍼 스캠퍼 밤 Act 2 미리보기에서 "
                "UnleasHD가 DLC 사진 대신 표시하던 `SUB STAGE 02`를 수정했습니다. "
                "HD 호환 옵션에서 DLC 원본의 해당 사진 한 칸만 확대해 표시하며 다른 칸은 유지합니다. "
                "이 장면을 게임에서 확인해 주십시오.\n")
    readme.write_text(content, encoding="utf8")

    files = sorted(path for path in OUTPUT.rglob("*") if path.is_file())
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, "UnleashedKorean/" + path.relative_to(OUTPUT).as_posix())
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == len(files)
    report = {"passed": True, "version": "1.0.5-review8", "edition": "Basic",
              "previewOnly": True, "files": len(files), "zip": str(ZIP),
              "zipSha256": digest(ZIP), "gameplayVerified": False,
              "publicRelease": False}
    (OUTPUT.parent / "verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
