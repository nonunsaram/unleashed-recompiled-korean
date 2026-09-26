"""Compare a known-font reconstruction with the installed Tails subtitle atlas."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'Build/Review4-RingEnergy'
SOURCE = ROOT / 'Build/Review4-FontInspection/ExStageTails_Common/+ExStageTails_Common'
MAP = json.loads((WORK / 'tails-atlas-map.json').read_text(encoding='utf-8-sig'))
FONT = ROOT / 'Tools/Fonts/LINESeedKR-Rg.ttf'


def render_one(base: Image.Image, entries: list[dict], scale: int) -> Image.Image:
    image = base.resize((512*scale, 512*scale), Image.Resampling.LANCZOS) if scale > 1 else base.copy()
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT), 27*scale)
    _, htop, _, hbottom = draw.textbbox((0, 0), '가', font=font)
    hheight = hbottom - htop
    for entry in entries:
        glyph = entry['character']
        if glyph == ' ': continue
        x0, y0, x1, y1 = [coord*scale for coord in entry['rect']]
        draw.rectangle((x0, y0, x1-1, y1-1), fill=(0, 0, 0, 255))
        left, top, right, bottom = draw.textbbox((0, 0), glyph, font=font)
        width, height = right-left, bottom-top
        x = x0 + ((x1-x0)-width)/2-left
        y = y0 + ((y1-y0)-(hheight if '\uac00' <= glyph <= '\ud7a3' else height))/2-(htop if '\uac00' <= glyph <= '\ud7a3' else top)
        y += ({',':8, '.':8, '~':3, '\u2026':2}.get(glyph, 0))*scale
        draw.text((x, y), glyph, font=font, fill=(255, 255, 255, 255))
    return image


def main() -> None:
    for page in MAP:
        original = Image.open(SOURCE / page['texture']).convert('RGBA')
        recreated = render_one(original, page['entries'], 1)
        original.save(WORK / (page['stem'] + '-original.png'))
        recreated.save(WORK / (page['stem'] + '-recreated.png'))
        stats=[]
        for item in page['entries']:
            if item['character'] == ' ': continue
            box=tuple(item['rect'])
            a=original.crop(box).convert('L')
            b=recreated.crop(box).convert('L')
            ap=[v>127 for v in a.getdata()]
            bp=[v>127 for v in b.getdata()]
            intersection=sum(x and y for x,y in zip(ap,bp))
            union=sum(x or y for x,y in zip(ap,bp))
            stats.append(intersection/union if union else 1)
        print(page['stem'], 'glyphs', len(stats), 'meanIoU', round(sum(stats)/len(stats),4),
              'minIoU', round(min(stats),4))
        high=render_one(original,page['entries'],2)
        high.save(WORK / (page['stem'] + '-1024-preview.png'))


if __name__ == '__main__': main()
