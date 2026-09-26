"""Package the original-based World opening correction on top of review13."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Build/Development-v105m-Playtest/UnleashedKorean"
OUT = ROOT / "Build/Development-v105n-Playtest/UnleashedKorean"
LOGO = ROOT / "Build/OPLogoInvestigation/OriginalBased/OPmovie_titlelogo_KR_World.dds"
ZIP = ROOT / "outputs/UnleashedRecompiled-Korean-1.0.5-Review14-LocalPlaytest.zip"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert SOURCE.is_dir() and LOGO.is_file()
    assert not OUT.exists() and not ZIP.exists()
    logo_report = json.loads((LOGO.parent / "verification.json").read_text(encoding="utf8"))
    assert logo_report["passed"] and logo_report["outsideRectangleIdenticalToOriginal"]
    assert sha(LOGO) == logo_report["outputSha256"]

    shutil.copytree(SOURCE, OUT)
    for lang in ("EN", "JP"):
        dest = OUT / "TitleLogos/Custom/Loading" / f"OPmovie_titlelogo_{lang}.dds"
        shutil.copy2(LOGO, dest)
        assert sha(dest) == sha(LOGO)

    ini = OUT / "mod.ini"
    raw = ini.read_text(encoding="utf-8-sig")
    assert raw.count('Version="1.0.5-review13"') == 1
    ini.write_text(raw.replace('Version="1.0.5-review13"',
                               'Version="1.0.5-review14"', 1), encoding="utf8")
    readme = OUT / "README-1.0.5-REVIEW-KO.md"
    raw = readme.read_text(encoding="utf8")
    assert raw.startswith("# 한국어 패치 1.0.5-review13 플레이 테스트 후보")
    raw = raw.replace("# 한국어 패치 1.0.5-review13 플레이 테스트 후보",
                      "# 한국어 패치 1.0.5-review14 플레이 테스트 후보", 1)
    raw += ("\n월드 어드벤처 오프닝 로고에서 일본어 글자 아래에 겹친 원본 흰 윤곽선을 "
            "복원하고 한국어 문구를 유지했습니다. 실제 게임 화면에서 확인해 주십시오.\n")
    readme.write_text(raw, encoding="utf8")

    before = {p.relative_to(SOURCE).as_posix(): sha(p)
              for p in SOURCE.rglob("*") if p.is_file()}
    after = {p.relative_to(OUT).as_posix(): sha(p)
             for p in OUT.rglob("*") if p.is_file()}
    changed = {p for p in after if after[p] != before[p]}
    assert set(after) == set(before)
    assert changed == {
        "TitleLogos/Custom/Loading/OPmovie_titlelogo_EN.dds",
        "TitleLogos/Custom/Loading/OPmovie_titlelogo_JP.dds",
        "mod.ini", "README-1.0.5-REVIEW-KO.md",
    }, changed

    files = sorted(p for p in OUT.rglob("*") if p.is_file())
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            z.write(p, "UnleashedKorean/" + p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None and len(z.namelist()) == len(files)
    report = {
        "passed": True, "version": "1.0.5-review14", "edition": "Basic",
        "openingTexturesChanged": 2, "otherAssetsPreservedFromReview13": True,
        "includesReview13HdCutsceneBaselineFix": True,
        "zip": str(ZIP), "zipSha256": sha(ZIP),
        "gameplayVerified": False, "publicRelease": False,
    }
    (OUT.parent / "verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
