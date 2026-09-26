"""Build the two Korean opening logo overlays from the game's separate DDS textures."""

from pathlib import Path
import hashlib
import json
import shutil

from PIL import Image, ImageChops, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'Build/OPLogoInvestigation'
OUT = WORK / 'Variants'
BG = '#202838'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def open_rgba(path):
    return Image.open(path).convert('RGBA')


def preview(im, path):
    bg = Image.new('RGB', im.size, BG)
    bg.paste(im, mask=im.getchannel('A'))
    bg.save(path, quality=96)


def korean_unleashed(original):
    caption = open_rgba(ROOT/'Build/TitleLogo-Reworked/KoreanLogo-clean.png')
    caption = caption.crop(caption.getchannel('A').getbbox())
    caption = caption.resize((208, 58), Image.Resampling.LANCZOS)
    result = Image.new('RGBA', original.size)
    result.alpha_composite(original, (0, -27))
    # Same small Korean addition shown under the selected animated title logo.
    xy = ((1280-caption.width)//2, 469)
    alpha = Image.new('L', result.size)
    alpha.paste(caption.getchannel('A'), xy)
    glow = alpha.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(3.0))
    haze = Image.new('RGBA', result.size, (255,255,255,0))
    haze.putalpha(glow.point(lambda a: round(a*.55)))
    result = Image.alpha_composite(result, haze)
    result.alpha_composite(caption, xy)
    return result


def korean_world(original):
    # Preserve the original opening logo and replace only its Japanese caption.
    from rebuild_world_opening_original import make_rgba
    return make_rgba()

def main():
    en = open_rgba(WORK/'Decoded/EN/logo.dds')
    jp = open_rgba(WORK/'Decoded/JP/logo.dds')
    assert en.size == jp.size == (1280,720)
    variants = {'Korean': korean_unleashed(en), 'Custom': korean_world(jp)}
    report = {}
    for name, image in variants.items():
        path = OUT/name/'Loading'
        path.mkdir(parents=True,exist_ok=True)
        for lang in ('EN','JP'):
            file = path/f'OPmovie_titlelogo_{lang}.dds'
            image.save(file)
            reopen = open_rgba(file)
            assert reopen.tobytes() == image.tobytes()
        preview(image,WORK/f'{name}-opening-preview.jpg')
        report[name] = {
            'size':list(image.size),
            'alphaBounds':list(image.getchannel('A').getbbox()),
            'ENsha256':digest(path/'OPmovie_titlelogo_EN.dds'),
            'JPsha256':digest(path/'OPmovie_titlelogo_JP.dds'),
            'languageVariantsIdentical':(path/'OPmovie_titlelogo_EN.dds').read_bytes()==(path/'OPmovie_titlelogo_JP.dds').read_bytes(),
            'decodedDdsRoundTrip':True,
        }
    (WORK/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
