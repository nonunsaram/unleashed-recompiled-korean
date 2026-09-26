"""Remove duplicate unchanged HD textures. Preserve every Korean HD edit."""
from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import struct
import subprocess
import sys
sys.stdout.reconfigure(encoding="utf8")
from collections import defaultdict
from pathlib import Path

from PIL import Image
from bounded_archive_tool import unpack
from build_unleashhd_ui_compat_v105 import members

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "Build/Development-v105o-Playtest/UnleashedKorean"
NEW = ROOT / "Build/Development-v105p-Playtest/UnleashedKorean"
WORK = ROOT / "Build/Review16-HDDeduplication"
COMPAT = Path("Compatibility/UnleasHD-1.4.2")

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_archive(path: Path) -> dict[str, bytes]:
    result = {}
    for part in sorted(path.parent.glob(path.name[:-6] + ".ar.*")):
        data = part.read_bytes()
        assert data[:4] == b"\0\0\0\0", part
        offset = 16
        while offset < len(data):
            size, length, start, _, _ = struct.unpack_from("<5I", data, offset)
            assert size >= 21 and start >= 21 and start + length <= size
            name = data[offset + 20:data.index(0, offset + 20, offset + start)].decode("utf8")
            assert name not in result and offset + size <= len(data), (part, name)
            result[name] = data[offset + start:offset + start + length]
            offset += size
        assert offset == len(data)
    assert set(result) == members(path.with_name(path.name[:-6] + ".arl")), path
    return result

def replace_archive(relative: Path, content: dict[str, bytes]) -> None:
    target = NEW / relative
    stem = target.name[:-6]
    # Remove only exact archive files in the newly created candidate.
    assert target.resolve().is_relative_to(NEW.resolve()) and NEW != OLD
    for path in [*target.parent.glob(stem + ".ar.*"), target.with_name(stem + ".arl")]:
        if path.is_file():
            assert path.resolve().is_relative_to(NEW.resolve())
            path.unlink()
    if not content:
        return
    job = WORK / "Pack" / relative.parent / stem
    job.mkdir(parents=True)
    for name, data in content.items():
        assert Path(name).name == name
        (job / name).write_bytes(data)
    subprocess.run([str(ROOT / "Tools/HedgeArcPack/HedgeArcPack.exe"), str(job)],
                   input="hh\n", text=True, capture_output=True, check=True,
                   timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
    target.parent.mkdir(parents=True, exist_ok=True)
    for path in [*job.parent.glob(stem + ".ar.*"), job.with_name(stem + ".arl")]:
        shutil.copy2(path, target.parent / path.name)
    assert read_archive(target) == content
    check = WORK / "RoundTrip" / relative
    check.parent.mkdir(parents=True, exist_ok=True)
    for path in [*target.parent.glob(stem + ".ar.*"), target.with_name(stem + ".arl")]:
        shutil.copy2(path, check.parent / path.name)
    unpack(check)
    decoded = {p.name: p.read_bytes() for p in (check.parent / stem).iterdir() if p.is_file()}
    assert decoded == content

def all_members(root: Path) -> dict[tuple[str, str], str]:
    return {(p.relative_to(root).as_posix(), name): sha(data)
            for p in sorted(root.rglob("*.ar.00")) for name, data in read_archive(p).items()}

def main() -> None:
    assert OLD.is_dir() and not NEW.exists() and not WORK.exists()
    WORK.mkdir(parents=True)
    shutil.copytree(OLD, NEW)
    before = all_members(OLD)
    report = json.loads((ROOT / "Build/UnleasHD-Compatibility-v105-HUD2/verification.json").read_text(encoding="utf8"))
    rows = json.loads((ROOT / "Translation/review/remaining-ui/texture-comparison.json").read_text(encoding="utf8"))
    remove_by_archive = defaultdict(set)
    removed_hd, removed_base, expected_removed = [], [], set()
    for item in report["textures"]:
        if item["labels"]:
            continue
        base = Path("Languages/English") / ("+" + item["archive"] + ".ar.00")
        hd = COMPAT / base
        hd_data = read_archive(OLD / hd)[item["file"]]
        assert sha(hd_data) == item["sourceSha256"]
        base_data = read_archive(OLD / base)[item["file"]]
        assert base_data == Path(rows[item["textureIndex"]]["english"]).read_bytes()
        for relative, data, records in ((hd, hd_data, removed_hd), (base, base_data, removed_base)):
            remove_by_archive[relative].add(item["file"])
            expected_removed.add((relative.as_posix(), item["file"]))
            records.append({"archive": relative.as_posix(), "file": item["file"], "sha256": sha(data),
                            "size": list(Image.open(io.BytesIO(data)).size)})
    assert len(removed_hd) == len(removed_base) == 28

    # Original/Japanese options select a scene without bundling the HD artwork.
    title_source = ROOT / "Build/TitleLogo-HD/UnleasHD-4K/+Title"
    for variant in ("Original", "Japanese"):
        relative = Path("TitleLogos") / variant / "+Title.ar.00"
        content = read_archive(OLD / relative)
        for name in ("mat_title_001.dds", "mat_title_004.dds"):
            assert content[name] == (title_source / name).read_bytes()
            remove_by_archive[relative].add(name)
            expected_removed.add((relative.as_posix(), name))
            removed_hd.append({"archive": relative.as_posix(), "file": name, "sha256": sha(content[name]),
                               "size": list(Image.open(io.BytesIO(content[name])).size)})
    for relative, names in remove_by_archive.items():
        content = read_archive(OLD / relative)
        replace_archive(relative, {name: data for name, data in content.items() if name not in names})

    after = all_members(NEW)
    assert before.keys() - after.keys() == expected_removed
    assert after.keys() <= before.keys()
    assert all(before[key] == value for key, value in after.items()), "A retained Korean HD edit changed"
    for path in OLD.rglob("*.dds"):
        assert (NEW / path.relative_to(OLD)).read_bytes() == path.read_bytes()
    for variant in ("Korean", "Custom"):
        for path in (OLD / "TitleLogos" / variant).rglob("*"):
            if path.is_file():
                assert (NEW / path.relative_to(OLD)).read_bytes() == path.read_bytes()

    ini_path = NEW / "mod.ini"
    ini = ini_path.read_text(encoding="utf-8-sig").replace('Version="1.0.5-review15"', 'Version="1.0.5-review16"')
    ini = re.sub(r"(?m)^Date=.*$", 'Date="2026-09-26"', ini)
    ini_path.write_text(ini, encoding="utf8")
    schema_path = NEW / "ConfigSchema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8-sig"))
    for choice in schema["Enums"]["TitleLogoVariant"]:
        if Path(choice["Value"]).name in ("Original", "Japanese"):
            choice["Description"] = ["로고 그림은 아래에 설치한 UnleasHD 또는 게임 원본에서 읽습니다.",
                                     "UnleasHD가 있으면 HD 로고, 없으면 게임 원본 화질로 표시됩니다."]
    schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    result = {"passed": True, "version": "1.0.5-review16", "removedUnchangedHdTextureInstances": removed_hd,
              "removedUnchangedBaseGameTextureInstances": removed_base,
              "allRetainedArchiveMembersByteIdentical": True, "allKoreanHdEditsPreserved": True,
              "koreanAndCustomTitleArchivesByteIdentical": True, "openingLogosByteIdentical": True,
              "retainedArchiveMembers": len(after), "gameplayVerified": False, "publicRelease": False,
              "redistributionPermissionStillRequiredForModifiedHdAssets": True}
    for path in (NEW.parent / "verification.json", WORK / "verification.json"):
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({k: len(v) if isinstance(v, list) else v for k, v in result.items()}, ensure_ascii=False))

if __name__ == "__main__":
    main()
