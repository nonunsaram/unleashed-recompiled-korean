"""Prepare a local review9 playtest with the preview cell aligned to its atlas."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Build/Development-v105h-Playtest/UnleashedKorean"
OUTPUT = ROOT / "Build/Development-v105i-Playtest/UnleashedKorean"
PATCH = ROOT / "Build/SubStage02Investigation/CandidateEdgeFix/Pack"
OLD_PATCH = ROOT / "Build/SubStage02Investigation/Candidate/Pack"
ZIP = ROOT / "outputs/UnleashedRecompiled-Korean-1.0.5-Review9-LocalPlaytest.zip"
RELATIVE = Path("Compatibility/UnleasHD-1.4.2")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert SOURCE.is_dir() and not OUTPUT.exists() and not ZIP.exists()
    assert json.loads((PATCH.parent / "verification.json").read_text(encoding="utf8"))["passed"]
    shutil.copytree(SOURCE, OUTPUT)
    destination = OUTPUT / RELATIVE
    for name in ("+WorldMap.ar.00", "+WorldMap.arl"):
        assert digest(destination / name) == digest(OLD_PATCH / name)
        shutil.copy2(PATCH / name, destination / name)
        assert digest(PATCH / name) == digest(destination / name)

    ini = OUTPUT / "mod.ini"
    old = ini.read_text(encoding="utf-8-sig")
    assert old.count('Version="1.0.5-review8"') == 1
    ini.write_text(old.replace('Version="1.0.5-review8"',
                               'Version="1.0.5-review9"', 1), encoding="utf8")
    readme = OUTPUT / "README-1.0.5-REVIEW-KO.md"
    content = readme.read_text(encoding="utf8")
    assert content.startswith("# 한국어 패치 1.0.5-review8 플레이 테스트 후보")
    content = content.replace("# 한국어 패치 1.0.5-review8 플레이 테스트 후보",
                              "# 한국어 패치 1.0.5-review9 플레이 테스트 후보", 1)
    content += ("\n월드맵 스카이스크레이퍼 스캠퍼 밤 Act 2 사진의 왼쪽 흰 선을 수정했습니다. "
                "실제 사진 칸의 시작점에 맞춰 4픽셀 왼쪽으로 옮겼습니다. "
                "다른 미리보기 칸과 UI 자산은 그대로입니다.\n")
    readme.write_text(content, encoding="utf8")

    files = sorted(path for path in OUTPUT.rglob("*") if path.is_file())
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, "UnleashedKorean/" + path.relative_to(OUTPUT).as_posix())
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == len(files)
    report = {"passed": True, "version": "1.0.5-review9", "edition": "Basic",
              "edgeAligned": True, "files": len(files), "zip": str(ZIP),
              "zipSha256": digest(ZIP), "gameplayVerified": False,
              "publicRelease": False}
    (OUTPUT.parent / "verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
