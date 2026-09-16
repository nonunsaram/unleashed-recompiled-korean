"""Create the v1.0.4 GameBanana Basic and Full packages from the approved v104 mod."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import uuid
import zipfile

from configure_features_v104 import configure
from release_contract_v104 import verify_folder

R = Path(__file__).resolve().parents[1]
VERSION = "1.0.4"
SOURCE_MOD = R / "Build" / "Development-v104-Final" / "UnleashedKorean"
PUBLIC = R / "publish" / "unleashed-recompiled-korean"
RELEASE = PUBLIC / "Release" / "v1.0.4"
PYTHON = Path("C:/Users/iobo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_version(path: Path) -> None:
    text = path.read_text(encoding="utf-8-sig")
    old = 'Version="1.0.4-review"'
    assert old in text
    updated = text.replace(old, f'Version="{VERSION}"')
    updated = re.sub(r"(?m)^Date=.*$", "Date=\"2026-09-16\"", updated)
    path.write_text(updated, encoding="utf8")


def compile_full_backend(destination: Path) -> tuple[Path, dict]:
    """Copy the unchanged EXE delta, updating only its package-version manifest."""
    prior = R / "Build" / "FullBackend-v102" / "Package"
    support = destination / "Support"
    shutil.copytree(prior / "Support", support)
    manifest_path = support / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf8"))
    assert manifest["scope"] == "native-exe" and len(manifest["files"]) == 1
    manifest["version"] = VERSION
    patch = support / "Patches" / "exe-v103.krpatch.gz"
    assert sha(patch) == manifest["files"][0]["patchSha256"]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf8")
    compiler = Path("C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe")
    assert compiler.is_file()
    logo = R / "Assets" / "Installer" / "UnleashedRecompiledLogo.png"
    setup = destination / "KoreanFullSetup.exe"
    subprocess.run([
        str(compiler), "/nologo", "/target:winexe", "/platform:x64",
        "/reference:System.Windows.Forms.dll", "/reference:System.Drawing.dll",
        "/reference:System.Web.Extensions.dll",
        "/resource:" + str(manifest_path) + ",KoreanFullManifest",
        "/resource:" + str(logo) + ",UnleashedRecompiledLogo",
        "/out:" + str(setup),
        str(R / "Scripts" / "KoreanSupportSetup_v102.cs"),
        str(R / "Scripts" / "KoreanSupportEngine.cs"),
    ], check=True)
    return setup, manifest


def source_zip(full: Path) -> None:
    allowed = {".py", ".cjs", ".cs", ".ps1", ".md", ".txt", ".json", ".cpp", ".h", ".patch", ".ttf", ".png", ".pdf", ".csv"}
    folders = ("Scripts", "Translation", "Patches", "Licenses", "Assets/Installer", "Assets/TitleLogo", "Tools/Fonts", "Release/v1.0.4")
    files = []
    for name in folders:
        folder = PUBLIC / name
        if folder.exists():
            files.extend(path for path in folder.rglob("*") if path.is_file())
    files.extend(path for path in PUBLIC.iterdir() if path.is_file())
    # Published validation code must include its own local modules and review inputs.
    for name in ("Scripts/astra_review_common.cjs", "Scripts/source_status_common_v048.cjs",
                 "Translation/review/astra-final/fixes.json", "Translation/review/source-status-v048/decisions.json",
                 "Translation/review/v103/edits.json", "Translation/display-overrides-v042.json"):
        assert (PUBLIC/name).is_file(), "Missing public validation dependency: " + name
    forbidden = ("KoreanOfficial", "vector", "title-logo-review")
    with zipfile.ZipFile(full / "Source.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(set(files)):
            rel = path.relative_to(PUBLIC).as_posix()
            if path.parent == RELEASE and path.name in {"manifest.json", "verification.json", "SHA256SUMS.txt", "final-audit.json"}:
                continue
            if any(token.lower() in rel.lower() for token in forbidden):
                continue
            if path.suffix.lower() in allowed and path.stat().st_size < 100 * 1024 * 1024:
                archive.write(path, "Source/" + rel)


def archive(root: Path, path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for item in sorted(root.rglob("*")):
            rel = item.relative_to(root).as_posix()
            if item.is_file():
                output.write(item, "UnleashedKorean/" + rel)
            elif not any(item.iterdir()):
                output.writestr("UnleashedKorean/" + rel + "/", b"")
    with zipfile.ZipFile(path) as output:
        assert output.testzip() is None


def main() -> None:
    assert SOURCE_MOD.is_dir() and RELEASE.is_dir()
    cumulative = verify_folder(SOURCE_MOD)
    for name in ("verification.json", "reflow-verification.json", "layer-verification.json"):
        assert json.loads((R / "Translation/review/v103" / name).read_text(encoding="utf8"))["passed"]
    resources = json.loads((R / "Build/Translation-v103/resource-verification.json").read_text(encoding="utf8"))
    assert resources["passed"] and len(resources["archives"]) == 21 and len(resources["patches"]) == 42
    output = R / "outputs" / f"GameBanana-{VERSION}-FinalCandidate"
    assert not output.exists(), f"Refusing to overwrite {output}"
    staging = R / "Build" / ("GameBanana-v104-" + uuid.uuid4().hex)
    basic = staging / "Basic" / "UnleashedKorean"
    full = staging / "Full" / "UnleashedKorean"
    try:
        shutil.copytree(SOURCE_MOD, basic)
        configure(basic)
        set_version(basic / "mod.ini")
        assert not (basic / "TitleLogos/KoreanOfficial").exists()
        assert "KoreanOfficial" not in (basic / "ConfigSchema.json").read_text(encoding="utf8")
        for lang in ("KO", "EN"):
            shutil.copy2(RELEASE / f"README-{lang}.md", basic / f"README-{lang}.md")
        shutil.copy2(RELEASE / "MODS-KO.md", basic / "MODS-KO.md")
        shutil.copy2(RELEASE / "CREDITS.md", basic / "CREDITS.md")
        shutil.copy2(RELEASE / "README-BASIC-KO.md", basic / "README-KO.md")
        shutil.copy2(RELEASE / "README-BASIC-EN.md", basic / "README-EN.md")
        shutil.copytree(basic, full)
        full_ini = full / "mod.ini"
        full_text = full_ini.read_text(encoding="utf-8-sig")
        full_text = re.sub(r"(?m)^Title=.*$", "Title=\"Korean Translation / \ud55c\uad6d\uc5b4 \ud328\uce58 \u2014 \uc804\uccb4\ud310\"", full_text)
        full_text = re.sub(r"(?m)^Description=.*$", "Description=\"\uae30\ubcf8\ud310 \uc804\uccb4\uc640 \uc635\uc158\u00b7\ub3c4\uc804\uacfc\uc81c EXE UI \ud55c\uad6d\uc5b4\ud654\ub97c \ud3ec\ud568\ud569\ub2c8\ub2e4. KoreanFullSetup.exe\ub85c \ucd94\uac00 \uc801\uc6a9\ud569\ub2c8\ub2e4. \uc804\uccb4 DLC \uc124\uce58\ub294 \uae30\ubcf8 \uc124\uc815\uc73c\ub85c \uc0ac\uc6a9\ud569\ub2c8\ub2e4.\"", full_text)
        full_text = re.sub(r"(?m)^Date=.*$", "Date=\"2026-09-16\"", full_text)
        full_ini.write_text(full_text, encoding="utf8")
        shutil.copy2(basic / "README-KO.md", full / "BASIC-README-KO.md")
        for lang in ("KO", "EN"):
            shutil.copy2(RELEASE / f"README-{lang}.md", full / f"README-{lang}.md")
        setup, manifest = compile_full_backend(full)
        verify_folder(basic)
        source_zip(full)
        output.mkdir(parents=True)
        records = []
        for edition, root in (("Basic", basic), ("Full", full)):
            package = output / f"UnleashedRecompiled-Korean-{VERSION}-{edition}.zip"
            archive(root, package)
            records.append({"file": package.name, "sha256": sha(package), "bytes": package.stat().st_size})
        (output / "SHA256SUMS.txt").write_text(
            "".join(f"{item['sha256']}  {item['file']}\n" for item in records), encoding="ascii")
        for name in ("GameBanana-post.md", "GameBanana-update.md", "Upload-guide-KO.md", "CHANGELOG-KO.md", "MODS-KO.md", "CREDITS.md"):
            shutil.copy2(RELEASE / name, output / name)
        report = {
            "version": VERSION, "revision": "20260916-final-audit", "cumulativeResourceVerification": cumulative, "archives": records, "translationArchives": 21,
            "resourceFiles": 42, "changedPhysicalCells": sum(x["changed_physical_cells"] for x in resources["archives"]),
            "unleashHDCompatibility": "1.4.2", "setupSha256": sha(setup),
            "patchedExeSha256": manifest["files"][0]["patchedSha256"], "gameLaunched": False,
            "published": False, "stagingDirectory": str(staging),
            "defaultConfiguration": {"dlc": "WorldMapVariants/AllDLC", "compatibility": "Compatibility/None", "titleLogo": "TitleLogos/Default"},
            "titleLogoChoices": 5, "approvedTitleAssetsPreserved": True,
            "verification": {
                "dialogue": json.loads((R / "Translation/review/v103/verification.json").read_text(encoding="utf8")),
                "reflow": json.loads((R / "Translation/review/v103/reflow-verification.json").read_text(encoding="utf8")),
                "layer": json.loads((R / "Translation/review/v103/layer-verification.json").read_text(encoding="utf8")),
            },
        }
        (output / "package-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
        public_manifest = {key: report[key] for key in ("version", "revision", "cumulativeResourceVerification", "archives", "translationArchives", "resourceFiles", "changedPhysicalCells", "unleashHDCompatibility", "setupSha256", "patchedExeSha256", "gameLaunched", "published", "defaultConfiguration", "titleLogoChoices", "approvedTitleAssetsPreserved")}
        (RELEASE / "manifest.json").write_text(json.dumps(public_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except Exception:
        # Preserve a failed package and staging tree for diagnosis.
        raise


if __name__ == "__main__":
    main()
