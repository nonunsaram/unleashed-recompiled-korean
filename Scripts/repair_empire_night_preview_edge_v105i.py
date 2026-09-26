"""Restore the Empire City night Act 2 DLC preview hidden by UnleasHD 1.4.2.

Builds a one-member +WorldMap overlay for the Korean mod's UnleasHD option.
The other preview cells remain identical after decoding.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from bounded_archive_tool import unpack


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "Build/SubStage02Investigation"
HD = WORK / "HDWorldMap/+WorldMap/mat_stage_ss_082.dds"
DLC = WORK / "EmpireCityDLCWorldMap/WorldMap/mat_stage_ss_082.dds"
TARGET = WORK / "CandidateEdgeFix/Pack/+WorldMap/mat_stage_ss_082.dds"
ORIGINAL_BOX = (542, 0, 814, 136)
HD_BOX = (1084, 0, 1628, 272)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert digest(HD) == "fc5f16a497ab89f4c29a21f1dcb1207b96fd2a187822731661a2b8407bf994c7"
    assert digest(DLC) == "6b785f58cc6dba757fdfa50cc804cf3b8f980df87387f2e8cbe537c21b7d6a7f"
    assert not TARGET.exists()

    with Image.open(HD) as source, Image.open(DLC) as addition:
        before = source.convert("RGBA")
        tile = addition.convert("RGBA").crop(ORIGINAL_BOX)
        assert tile.size == (272, 136)
        tile = tile.resize((544, 272), Image.Resampling.LANCZOS)
        after = before.copy()
        after.paste(tile, HD_BOX[:2])

    TARGET.parent.mkdir(parents=True)
    after.save(TARGET)
    with Image.open(TARGET) as check:
        actual = check.convert("RGBA")
    old_pixels = np.asarray(before)
    new_pixels = np.asarray(actual)
    outside = np.ones((before.height, before.width), dtype=bool)
    outside[HD_BOX[1]:HD_BOX[3], HD_BOX[0]:HD_BOX[2]] = False
    assert np.array_equal(old_pixels[outside], new_pixels[outside])
    assert not np.array_equal(old_pixels[~outside], new_pixels[~outside])
    assert np.array_equal(np.asarray(tile), new_pixels[~outside].reshape(tile.height, tile.width, 4))
    assert int(new_pixels[160, 1084:1088, :3].max()) < 200

    packer = ROOT / "Tools/HedgeArcPack/HedgeArcPack.exe"
    subprocess.run([str(packer), str(TARGET.parent)], input="hh\n", text=True,
                   capture_output=True, check=True, timeout=30,
                   creationflags=subprocess.CREATE_NO_WINDOW)
    packed = TARGET.parent.parent
    archive = packed / "+WorldMap.ar.00"
    index = packed / "+WorldMap.arl"
    assert archive.is_file() and index.is_file()
    verify = WORK / "CandidateEdgeFix/RoundTrip"
    verify.mkdir(parents=True)
    shutil.copy2(archive, verify / archive.name)
    shutil.copy2(index, verify / index.name)
    unpack(verify / archive.name)
    assert digest(verify / "+WorldMap/mat_stage_ss_082.dds") == digest(TARGET)

    report = {
        "passed": True,
        "cause": "UnleasHD's base mat_stage_ss_082 atlas replaces the DLC's Act 2 photo with SUB STAGE 02",
        "asset": "mat_stage_ss_082.dds",
        "originalBox": ORIGINAL_BOX,
        "hdBox": HD_BOX,
        "outsidePixelChangeCount": 0,
        "originalHdSha256": digest(HD),
        "originalDlcSha256": digest(DLC),
        "patchedSha256": digest(TARGET),
        "archiveSha256": digest(archive),
        "installed": False,
        "gameplayVerified": False,
    }
    (WORK / "CandidateEdgeFix/verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
