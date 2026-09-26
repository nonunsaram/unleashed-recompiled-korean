"""Build a 1440p Korean UI overlay from an installed UnleasHD 1.4.2 mod.

Only overlapping English UI DDS members are included. The game's text tables,
fonts, models, and original archives remain supplied by the Korean mod and HD mod.
"""
from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import shutil
import struct
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from bounded_archive_tool import unpack

ROOT = Path(__file__).resolve().parents[1]
FONT_FILES = {"regular": "LINESeedKR-Rg.ttf", "bold": "SBAggroM.ttf", "slant": "SBAggroB.ttf"}
COLORS = {"white": ((255, 255, 255), (225, 229, 233), (8, 8, 8)),
          "gold": ((255, 255, 255), (242, 207, 101), (99, 73, 16))}
SUPERSAMPLE = 4


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def members(path: Path) -> set[str]:
    blob = path.read_bytes()
    assert blob[:4] == b"ARL2", path
    offset = 8 + 4 * struct.unpack_from("<I", blob, 4)[0]
    found = set()
    while offset < len(blob):
        length = blob[offset]
        offset += 1
        name = blob[offset:offset + length].decode("utf8")
        assert name not in found
        found.add(name)
        offset += length
    assert offset == len(blob)
    return found


def extract_archive(source: Path, destination: Path) -> Path:
    assert source.name.endswith(".ar.00")
    destination.mkdir(parents=True)
    stem = source.name[:-6]
    for part in source.parent.glob(stem + ".ar.*"):
        shutil.copy2(part, destination / part.name)
    shutil.copy2(source.with_name(stem + ".arl"), destination / (stem + ".arl"))
    unpack(destination / source.name)
    result = destination / stem
    assert result.is_dir(), source
    return result


def draw_korean(source: Image.Image, labels: list[dict], index: int,
                panel: Image.Image | None, factor: float) -> tuple[Image.Image, int]:
    original = source.convert("RGBA")
    output = original.copy()
    allowed = np.zeros((output.height, output.width), dtype=bool)
    for label in labels:
        x0, y0, x1, y1 = [round(v * factor) for v in label["box"]]
        assert 0 <= x0 < x1 <= output.width and 0 <= y0 < y1 <= output.height
        font_name = FONT_FILES[label["font"]]
        font = ImageFont.truetype(str(ROOT / "Tools/Fonts" / font_name),
                                  round(label["size"] * factor * SUPERSAMPLE))
        if label["background"]:
            if index == 16:
                clear = (round(90 * factor), y0 + round(2 * factor),
                         round(200 * factor), y0 + round(29 * factor))
                for py in range(clear[1], clear[3]):
                    for px in range(clear[0], clear[2]):
                        output.putpixel((px, py), original.getpixel((round(70 * factor), py)))
            else:
                assert panel is not None and index in (19, 25)
                clear = (round(130 * factor), y0 + round(3 * factor),
                         round(254 * factor), min(y0 + round(28 * factor), y1))
                for py in range(clear[1], clear[3]):
                    for px in range(clear[0], clear[2]):
                        ref_x = px if px < round(150 * factor) or px > round(237 * factor) else round(140 * factor)
                        ref_y = round(98 * factor) + py - y0
                        output.putpixel((px, py), panel.getpixel((ref_x, ref_y)))
        else:
            clear = (x0, y0, x1, y1)
            output.paste((0, 0, 0, 0), clear)
        allowed[clear[1]:clear[3], clear[0]:clear[2]] = True
        baseline_box = font.getbbox("가나다", anchor="ls")
        top = label["top"] * factor
        baseline = round(top * SUPERSAMPLE - baseline_box[1])
        anchor = label["anchor_x"] * factor * SUPERSAMPLE
        advance = font.getlength(label["korean"])
        text_x = (anchor if label["align"] == "left" else
                  anchor - advance / 2 if label["align"] == "center" else anchor - advance)
        layer = Image.new("RGBA", (output.width * SUPERSAMPLE, (y1 - y0) * SUPERSAMPLE))
        face = Image.new("L", layer.size)
        ImageDraw.Draw(face).text((round(text_x), baseline - y0 * SUPERSAMPLE),
                                  label["korean"], font=font, anchor="ls", fill=255)
        stroke_size = 19 if index in (28, 29) else (9 if label["font"] == "regular" else 11)
        stroke = face.filter(ImageFilter.MaxFilter(stroke_size))
        top_color, bottom_color, edge = COLORS[label["style"]]
        if index in (28, 29): edge = (40, 30, 12)
        layer.paste((*edge, 255), (0, 0, layer.width, layer.height))
        layer.putalpha(stroke)
        gradient = np.zeros((layer.height, layer.width, 4), dtype="uint8")
        for py in range(layer.height):
            t = min(1, max(0, (py - (top - y0) * SUPERSAMPLE) /
                           (label["size"] * factor * SUPERSAMPLE)))
            if label["style"] == "gold":
                t = min(1, max(0, (t - .35) / .65))
            gradient[py, :, :3] = np.array(top_color) * (1 - t) + np.array(bottom_color) * t
        gradient[:, :, 3] = np.asarray(face)
        layer.alpha_composite(Image.fromarray(gradient))
        if label["font"] == "slant":
            displacement = -(label["size"] * factor + top - y0) * SUPERSAMPLE * .12
            layer = layer.transform(layer.size, Image.Transform.AFFINE,
                                    (1, .12, displacement, 0, 1, 0),
                                    resample=Image.Resampling.BICUBIC)
        layer = layer.resize((output.width, y1 - y0), Image.Resampling.LANCZOS)
        bounds = layer.getbbox()
        assert bounds, label["korean"]
        output.alpha_composite(layer, (0, y0))
        allowed[y0 + bounds[1]:y0 + bounds[3], bounds[0]:bounds[2]] = True
    assert np.array_equal(np.asarray(original)[~allowed], np.asarray(output)[~allowed])
    return output, len(labels)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--korean-mod", type=Path,
                        default=ROOT / "Build/Development-v104-Final/UnleashedKorean")
    parser.add_argument("--unleashhd-mod", type=Path,
                        default=ROOT / "UnleashedRecomp-Windows/mods/UnleasHD-1440p")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    korean, hd, output = (p.resolve() for p in
                          (args.korean_mod, args.unleashhd_mod, args.output))
    assert korean.is_dir() and hd.is_dir() and not output.exists()
    ini = configparser.ConfigParser(interpolation=None)
    ini.read(hd / "mod.ini", encoding="utf-8-sig")
    assert ini["Main"]["ID"].strip('"') == "pupsi.UnleasHD"
    assert ini["Desc"]["Version"].strip('"') == "1.4.2"
    rows = json.loads((ROOT / "Translation/review/remaining-ui/texture-comparison.json").read_text(encoding="utf8"))
    labels = json.loads((ROOT / "Translation/review/unleashhd-v105/ui-textures-ko-v104-full.json").read_text(encoding="utf8"))["labels"]
    by_index = defaultdict(list)
    for label in labels:
        by_index[label["texture"]].append(label)
    mapping = {}
    for index, row in enumerate(rows):
        if index >= 30:  # Existing reviewed 1440p WorldMap option remains separate.
            continue
        for archive in row["archives"]:
            if archive.startswith("BaseGame/"):
                key = (archive.split("/", 1)[1], row["file"])
                assert key not in mapping
                mapping[key] = index
    hd_archives = hd / "MainMod/Languages/English"
    korean_archives = korean / "Languages/English"
    jobs = defaultdict(list)
    for (stem, file), index in mapping.items():
        ka, ha = korean_archives / ("+" + stem + ".arl"), hd_archives / ("+" + stem + ".arl")
        if ka.is_file() and ha.is_file() and file in members(ka) and file in members(ha):
            jobs[stem].append((file, index))
    assert jobs and all(("+" + stem + ".ar.00") in
                        {p.name for p in korean_archives.glob("*.ar.00")} for stem in jobs)
    output.mkdir(parents=True)
    extracted = {}
    for stem in sorted(jobs):
        extracted[stem] = extract_archive(hd_archives / ("+" + stem + ".ar.00"),
                                          output / "HDSource" / stem)
    panel_path = extracted["SystemCommonCore"] / "mat_pause_en_001.dds"
    panel = Image.open(panel_path).convert("RGBA")
    result = []
    packed_root = output / "Overlay/Languages/English"
    packed_root.mkdir(parents=True)
    for stem, files in sorted(jobs.items()):
        work = output / "PackWork" / ("+" + stem)
        work.mkdir(parents=True)
        for file, index in sorted(files):
            source = extracted[stem] / file
            assert source.is_file(), source
            original_size = Image.open(rows[index]["english"]).size
            with Image.open(source) as decoded:
                factor = decoded.width / original_size[0]
                assert factor >= 2 and abs(factor - decoded.height / original_size[1]) < .002, (stem, file, decoded.size, original_size)
                if by_index[index]:
                    rendered, label_count = draw_korean(decoded, by_index[index], index, panel, factor)
                    destination = work / file
                    rendered.save(destination)
                    with Image.open(destination) as reopened:
                        assert np.array_equal(np.asarray(reopened.convert("RGBA")), np.asarray(rendered))
                else:
                    destination = work / file
                    shutil.copy2(source, destination)
                    label_count = 0
            result.append({"archive": stem, "file": file, "textureIndex": index,
                           "labels": label_count, "sourceSha256": digest(source),
                           "outputSha256": digest(destination), "size": list(Image.open(destination).size)})
        subprocess.run([str(ROOT / "Tools/HedgeArcPack/HedgeArcPack.exe"), str(work)],
                       input="hh\n", text=True, capture_output=True, check=True, timeout=30,
                       creationflags=subprocess.CREATE_NO_WINDOW)
        parts = sorted(work.parent.glob(work.name + ".ar.*"))
        arl = work.with_suffix(".arl")
        assert parts and arl.is_file()
        assert members(arl) == {file for file, _ in files}
        for path in [*parts, arl]:
            shutil.copy2(path, packed_root / path.name)
        verified = extract_archive(packed_root / (work.name + ".ar.00"),
                                   output / "RoundTrip" / stem)
        for file, _ in files:
            assert (work / file).read_bytes() == (verified / file).read_bytes()
    report = {"passed": True, "unleashHDVersion": "1.4.2", "resolution": "1440p",
              "koreanSource": str(korean), "hdSource": str(hd),
              "archiveCount": len(jobs), "textureCount": len(result),
              "translatedTextureCount": sum(bool(x["labels"]) for x in result),
              "unmodifiedHdTextureCount": sum(not x["labels"] for x in result),
              "textures": result}
    (output / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("textures", "koreanSource", "hdSource")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
