"""Build inspectable review15 ZIPs. These are local candidates, not public uploads."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "Build/Development-v105o-Playtest/UnleashedKorean"
PUBLIC = ROOT / "publish/unleashed-recompiled-korean"
DOCS = PUBLIC / "Release/v1.0.5-review15"
PRIOR = ROOT / "outputs/GameBanana-1.0.4-FinalCandidate/UnleashedRecompiled-Korean-1.0.4-Full.zip"
OUTPUT = ROOT / "outputs/GameBanana-1.0.5-Review15-Candidate"
WORK = ROOT / "Build/Review15-Package-Work"
VERSION = "1.0.5-review15"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def source_zip(destination: Path) -> None:
    tracked = subprocess.check_output(
        ["git", "-c", f"safe.directory={PUBLIC.as_posix()}", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=PUBLIC,
    ).decode("utf8").splitlines()
    allowed = {".py", ".cjs", ".cs", ".ps1", ".md", ".txt", ".json", ".cpp", ".h", ".patch", ".ttf", ".png", ".pdf", ".csv"}
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(set(tracked)):
            path = PUBLIC / name
            if not path.is_file() or path.suffix.lower() not in allowed or path.stat().st_size >= 100 * 1024 * 1024:
                continue
            assert ".." not in Path(name).parts
            archive.write(path, "Source/" + name.replace("\\", "/"))
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert "Source/Release/v1.0.5-review15/CHANGELOG-KO.md" in archive.namelist()


def setup_full() -> dict:
    support = WORK / "Support"
    (support / "Patches").mkdir(parents=True)
    with zipfile.ZipFile(PRIOR) as old:
        for relative in ("InstallerLogo.png", "Patches/exe-v103.krpatch.gz"):
            (support / relative).write_bytes(old.read("UnleashedKorean/Support/" + relative))
        manifest = json.loads(old.read("UnleashedKorean/Support/manifest.json"))
    assert manifest["scope"] == "native-exe" and len(manifest["files"]) == 1
    assert digest(support / "Patches/exe-v103.krpatch.gz") == manifest["files"][0]["patchSha256"]
    manifest["version"] = VERSION
    (support / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    compiler = Path("C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe")
    assert compiler.is_file()
    setup = WORK / "KoreanFullSetup.exe"
    subprocess.run([
        str(compiler), "/nologo", "/target:winexe", "/platform:x64",
        "/reference:System.Windows.Forms.dll", "/reference:System.Drawing.dll",
        "/reference:System.Web.Extensions.dll",
        "/resource:" + str(support / "manifest.json") + ",KoreanFullManifest",
        "/resource:" + str(ROOT / "Assets/Installer/UnleashedRecompiledLogo.png") + ",UnleashedRecompiledLogo",
        "/out:" + str(setup),
        str(ROOT / "Scripts/KoreanSupportSetup_v102.cs"),
        str(ROOT / "Scripts/KoreanSupportEngine.cs"),
    ], check=True)
    return manifest


def mod_ini(edition: str) -> bytes:
    raw = (MOD / "mod.ini").read_text(encoding="utf-8-sig")
    assert raw.count(f'Version="{VERSION}"') == 1
    raw = re.sub(r"(?m)^Date=.*$", 'Date="2026-09-26"', raw)
    if edition == "Full":
        raw = re.sub(r"(?m)^Title=.*$", 'Title="Korean Translation / 한국어 패치 — 전체판"', raw)
        raw = re.sub(r"(?m)^Description=.*$", 'Description="기본판과 EXE UI 한국어화 도구를 포함합니다. UnleasHD 1.4.2 1440p 호환 옵션이 있습니다."', raw)
    return raw.encode("utf8")


def create_archive(edition: str, source: Path) -> dict:
    overrides = {
        "mod.ini": mod_ini(edition),
        "README-KO.md": (DOCS / f"README-{edition.upper()}-KO.md").read_bytes(),
        "README-EN.md": (DOCS / "README-EN.md").read_bytes(),
        "CHANGELOG-KO.md": (DOCS / "CHANGELOG-KO.md").read_bytes(),
        "CREDITS.md": (PUBLIC / "Release/v1.0.4/CREDITS.md").read_bytes(),
    }
    if edition == "Full":
        overrides["BASIC-README-KO.md"] = (DOCS / "README-BASIC-KO.md").read_bytes()
    name = f"UnleashedRecompiled-Korean-1.0.5-Review15-{edition}.zip"
    destination = OUTPUT / name
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(MOD.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(MOD).as_posix()
            if relative in overrides:
                continue
            archive.write(path, "UnleashedKorean/" + relative)
        for relative, blob in sorted(overrides.items()):
            archive.writestr("UnleashedKorean/" + relative, blob)
        if edition == "Full":
            for relative in ("InstallerLogo.png", "manifest.json", "Patches/exe-v103.krpatch.gz"):
                archive.write(WORK / "Support" / relative, "UnleashedKorean/Support/" + relative)
            archive.write(WORK / "KoreanFullSetup.exe", "UnleashedKorean/KoreanFullSetup.exe")
            archive.write(source, "UnleashedKorean/Source.zip")
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == len(set(names))
        assert all(n.startswith("UnleashedKorean/") and ".." not in Path(n).parts for n in names)
        for path in MOD.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(MOD).as_posix()
            if relative not in overrides:
                assert hashlib.sha256(archive.read("UnleashedKorean/" + relative)).hexdigest() == digest(path)
        assert archive.read("UnleashedKorean/mod.ini") == overrides["mod.ini"]
        assert ("UnleashedKorean/KoreanFullSetup.exe" in names) == (edition == "Full")
        assert not any(n.lower().endswith((".iso", ".xex")) for n in names)
    return {"file": name, "bytes": destination.stat().st_size, "sha256": digest(destination), "files": len(names)}


def main() -> None:
    report = json.loads((MOD.parent / "verification.json").read_text(encoding="utf8"))
    assert report["passed"] and report["version"] == VERSION and not report["publicRelease"]
    assert MOD.is_dir() and PRIOR.is_file() and DOCS.is_dir()
    assert not OUTPUT.exists() and not WORK.exists()
    OUTPUT.mkdir(parents=True)
    WORK.mkdir(parents=True)
    source = WORK / "Source.zip"
    source_zip(source)
    manifest = setup_full()
    records = [create_archive("Basic", source), create_archive("Full", source)]
    (OUTPUT / "SHA256SUMS.txt").write_text(
        "".join(f"{r['sha256']}  {r['file']}\n" for r in records), encoding="ascii")
    for name in ("CHANGELOG-KO.md", "GameBanana-update.md", "Upload-guide-KO.md"):
        shutil.copy2(DOCS / name, OUTPUT / name)
    shutil.copy2(ROOT / "Build/OPLogoInvestigation/ContourFix/before-after.png",
                 OUTPUT / "Review15-opening-before-after.png")
    (OUTPUT / "DO-NOT-UPLOAD.txt").write_text(
        "LOCAL REVIEW CANDIDATE ONLY. UnleasHD-derived HD files require redistribution permission or an on-device build path.\n",
        encoding="utf8")
    verification = {
        "passed": True, "version": VERSION, "archives": records,
        "setupSha256": digest(WORK / "KoreanFullSetup.exe"),
        "exePatchSha256": manifest["files"][0]["patchSha256"],
        "review15SourceVerified": True, "zipIntegrityVerified": True,
        "gameplayVerified": False, "redistributionPermissionVerified": False,
        "publicRelease": False,
    }
    (OUTPUT / "package-verification.json").write_text(
        json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
