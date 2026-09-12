import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> int:
    if len(sys.argv) != 5:
        print("usage: patch_opening_atlas.py <input.dds> <map.json> <font.ttf> <output.dds>")
        return 2

    input_path, map_path, font_path, output_path = map(Path, sys.argv[1:])
    atlas = Image.open(input_path).convert("RGBA")
    draw = ImageDraw.Draw(atlas)
    font = ImageFont.truetype(str(font_path), 27)
    hangul_left, hangul_top, hangul_right, hangul_bottom = draw.textbbox(
        (0, 0), "가", font=font
    )
    hangul_height = hangul_bottom - hangul_top

    entries = json.loads(map_path.read_text(encoding="utf-8-sig"))
    for entry in entries:
        x0, y0, x1, y1 = entry["rect"]
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(0, 0, 0, 255))

        glyph = entry["character"]
        left, top, right, bottom = draw.textbbox((0, 0), glyph, font=font)
        width, height = right - left, bottom - top
        x = x0 + ((x1 - x0) - width) / 2 - left
        if "\uac00" <= glyph <= "\ud7a3":
            # Keep every Hangul syllable on one shared baseline. Centering each
            # glyph's ink box independently makes syllables whose font bbox
            # differs by one pixel appear to jump vertically.
            y = y0 + ((y1 - y0) - hangul_height) / 2 - hangul_top
        else:
            y = y0 + ((y1 - y0) - height) / 2 - top
        y += entry.get("vertical_offset", 0)
        draw.text((x, y), glyph, font=font, fill=(255, 255, 255, 255))

    atlas.save(output_path, pixel_format="DXT5")
    atlas.save(output_path.with_suffix(".preview.png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
