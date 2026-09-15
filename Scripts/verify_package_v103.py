"""Verify the final v1.0.3 GameBanana archives without launching the game."""
from pathlib import Path
import configparser
import hashlib
import io
import json
import subprocess
import sys
import uuid
import zipfile

R = Path(__file__).resolve().parents[1]
VERSION = "1.0.3"


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def config(blob: bytes) -> configparser.ConfigParser:
    ini = configparser.ConfigParser(interpolation=None)
    ini.optionxform = str
    ini.read_string(blob.decode("utf8"))
    return ini


def main() -> None:
    output = R / "outputs" / f"GameBanana-{VERSION}"
    report = json.loads((output / "package-verification.json").read_text(encoding="utf8"))
    sums = set((output / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines())
    packages = {}
    work = R / "Build" / ("Package-v103-Verify-" + uuid.uuid4().hex)
    work.mkdir()
    for item in report["archives"]:
        path = output / item["file"]
        blob = path.read_bytes()
        assert sha(blob) == item["sha256"]
        assert f"{item['sha256']}  {item['file']}" in sums
        edition = "Basic" if "-Basic.zip" in item["file"] else "Full"
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            assert archive.testzip() is None and len(archive.namelist()) == len(set(archive.namelist()))
            assert all(name.startswith("UnleashedKorean/") and ".." not in Path(name).parts and ":" not in name for name in archive.namelist())
            packages[edition] = {name.removeprefix("UnleashedKorean/"): archive.read(name) for name in archive.namelist() if not name.endswith("/")}
            archive.extractall(work / edition)
    basic, full = packages["Basic"], packages["Full"]
    assert not any("KoreanOfficial" in name or "KoreanOfficial" in blob.decode("utf8", errors="ignore") for name, blob in basic.items())
    assert not any("KoreanOfficial" in name or "KoreanOfficial" in blob.decode("utf8", errors="ignore") for name, blob in full.items())
    assert not any(Path(name).suffix.lower() in (".exe", ".dll", ".xex") for name in basic)
    executable = [name for name in full if Path(name).suffix.lower() in (".exe", ".dll", ".xex")]
    assert executable == ["KoreanFullSetup.exe"]
    assert set(full) - set(basic) == {"BASIC-README-KO.md", "KoreanFullSetup.exe", "Source.zip", "Support/InstallerLogo.png", "Support/manifest.json", "Support/Patches/exe-v103.krpatch.gz"}
    resources = json.loads((R / "Build/Translation-v103/resource-verification.json").read_text(encoding="utf8"))
    assert resources["passed"] and len(resources["patches"]) == 42
    for item in resources["patches"]:
        rel = item["relative"]
        assert sha(basic[rel]) == item["after_sha256"]
        assert basic[rel] == full[rel]
    for package in (basic, full):
        ini = config(package["mod.ini"])
        assert ini["Desc"]["Version"].strip('"') == VERSION
        assert ini["Desc"]["Date"].strip(chr(34)) == "2026-09-16"
        assert ini["Main"]["IncludeDir0"].strip('"') == "WorldMapVariants/AllDLC"
        assert ini["Main"]["IncludeDir2"].strip('"') == "Compatibility/None"
        assert ini["Main"]["IncludeDir3"].strip('"') == "TitleLogos/Default"
        schema = json.loads(package["ConfigSchema.json"])
        assert [x["Value"] for x in schema["Enums"]["TitleLogoVariant"]] == [
            "TitleLogos/Default", "TitleLogos/Original", "TitleLogos/Japanese", "TitleLogos/Custom"]
        assert all("KoreanOfficial" not in json.dumps(value, ensure_ascii=False) for value in schema["Enums"]["TitleLogoVariant"])
        assert "TitleLogos/Default/+Title.ar.00" not in package
        assert "TitleLogos/Default/+Title.arl" not in package
        for logo in ("Original", "Japanese", "Custom"):
            assert f"TitleLogos/{logo}/+Title.ar.00" in package
            assert f"TitleLogos/{logo}/+Title.arl" in package
        assert "MODS-KO.md" in package
    manifest = json.loads(full["Support/manifest.json"])
    assert manifest["version"] == VERSION and manifest["scope"] == "native-exe"
    assert sha(full["KoreanFullSetup.exe"]) == report["setupSha256"]
    with zipfile.ZipFile(io.BytesIO(full["Source.zip"])) as source:
        assert source.testzip() is None
        assert "Source/Release/v1.0.3/manifest.json" not in source.namelist()
        assert not any("KoreanOfficial" in name or "vector" in name.lower() or "title-logo-review" in name.lower() for name in source.namelist())
        assert source.read("Source/Scripts/package_hmm_release_v103.py") == (R / "publish/unleashed-recompiled-korean/Scripts/package_hmm_release_v103.py").read_bytes()
        assert source.read("Source/Scripts/verify_package_v103.py") == (R / "publish/unleashed-recompiled-korean/Scripts/verify_package_v103.py").read_bytes()
    subprocess.run([str(Path("C:/Users/iobo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe")), str(R / "Scripts/test_full_release_v101.py"), "--package", str(work / "Full/UnleashedKorean")], check=True)
    result = {
        "passed": True, "zipIntegrity": True, "safePaths": True,
        "basicFiles": len(basic), "fullFiles": len(full), "resourceFiles": len(resources["patches"]),
        "defaultConfiguration": report["defaultConfiguration"], "titleLogoChoices": 4,
        "experimentalKoreanUnleashedLogoExcluded": True, "unleashHDCompatibilityVerified": True,
        "installerRealExeRoundTrip": True, "actualGameLaunched": False, "published": False,
    }
    (output / "release-verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
