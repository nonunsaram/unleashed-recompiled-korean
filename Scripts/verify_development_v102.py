"""Verify the development tree against preserved inputs without packaging or game writes."""
from pathlib import Path
import ast, configparser, json
from PIL import Image
from audit_mod_resources_v102 import digest
from prepare_title_logo_v102 import scene_slots

R = Path(__file__).resolve().parents[1]

def verify_halo(source, fixed):
    """Catch the RGB/alpha confusion that created visible blocks in the game."""
    assert fixed.size == source.size == (640, 640)
    assert fixed.crop((0,72,640,640)).tobytes() == source.crop((0,72,640,640)).tobytes()
    assert fixed.crop((420,0,640,72)).tobytes() == source.crop((420,0,640,72)).tobytes()
    assert fixed.getchannel('A').tobytes() == source.getchannel('A').tobytes(), 'Additive halo alpha must remain opaque'
    assert fixed.getchannel('A').getextrema() == (255,255)
    # Locations corresponding to the screenshot's left ledge and upper-right block.
    for x,y in [(0,30),(10,30),(350,0),(380,0),(383,0)]:
        assert max(fixed.getpixel((x,y))[:3]) <= 3, f'Stray light at {(x,y)}'
    contour = [fixed.getpixel((x,8))[0] for x in range(40,208)]
    assert max(contour)-min(contour) > 20, 'Glow must follow strokes, not a flat box'
    assert fixed.getpixel((28,8))[0] < 15, 'Old rectangular corner must be absent'
    for point in [(260,15),(310,15)]:
        assert fixed.getpixel(point)[0] <= 3, 'Removed caption strip must stay dark'
    assert fixed.getpixel((45,3))[0] < fixed.getpixel((45,8))[0] < fixed.getpixel((45,15))[0], 'Outer glow must fade gradually'


def verify():
    dev = R/'Build/Development-v102/UnleashedKorean'
    base = R/'Build/GameBanana-v102-20260913-051909/Basic/UnleashedKorean'
    unchanged = 0
    for source in base.rglob('*'):
        if not source.is_file(): continue
        relative = source.relative_to(base)
        if relative.as_posix() in ('mod.ini', 'ConfigSchema.json'): continue
        assert digest(source) == digest(dev/relative), relative
        unchanged += 1
    schemas = []
    for source in (R/'Scripts').glob('*.py'):
        ast.parse(source.read_text(encoding='utf-8-sig'), filename=str(source))
    ini = configparser.ConfigParser(interpolation=None)
    ini.read(dev/'mod.ini', encoding='utf8')
    schema = json.loads((dev/'ConfigSchema.json').read_text(encoding='utf8'))
    assert ini['Main']['IncludeDirCount'] == '4'
    for group in schema['Groups']:
        for element in group['Elements']:
            if element['Name'].startswith('IncludeDir'):
                assert group['Name'] == 'Main'
                assert ini['Main'][element['Name']].strip('"') == element['Value']
                for option in schema['Enums'][element['Type']]:
                    assert (dev/option['Value']).is_dir()
                schemas.append(element['Name'])
    title = json.loads((R/'Build/TitleLogo-v102/verification.json').read_text())
    original = R/'Build/TitleLogo-v102/Originals/Core/Title/ui_title.yncp'
    assert digest(original) == title['sourceSceneSha256']
    blob = original.read_bytes(); slots = scene_slots(blob)
    for variant in title['variants']:
        path = R/'Build/TitleLogo-v102/Variants'/variant['name']
        assert digest(path/'+Title.ar.00') == variant['archiveSha256']
        assert digest(dev/'TitleLogos'/variant['name']/'+Title.ar.00') == variant['archiveSha256']
        edited = (path/'+Title/ui_title.yncp').read_bytes()
        assert len(edited) == len(blob)
        assert all(a == b or any(slots[n] <= i < slots[n]+4 for n in ('title_1','title_2')) for i,(a,b) in enumerate(zip(blob,edited)))
        for p in (path/'+Title').iterdir():
            assert digest(p) == digest(R/'Build/TitleLogo-v102/Verify'/variant['name']/'+Title'/p.name)
    if title['customReady']:
        custom_source = R/'Assets/TitleLogo/CustomLogo.png'
        assert digest(custom_source) == title['customSourceSha256']
        sheet = Image.open(original.parent/'mat_title_001.dds').convert('RGBA')
        edit = Image.open(custom_source).convert('RGBA')
        parts = json.loads((R/'outputs/TitleLogo-v102-Editing/parts.json').read_text())
        kana = next(p for p in parts if p['file'] == 'txt_KANA-original.png')
        if edit.size == tuple(kana['size']):
            sheet.paste(edit, tuple(kana['box']))
        else:
            sheet = edit
        scale = sheet.width // 1024
        box = tuple(v*scale for v in kana['box'])
        tile = sheet.crop(box); ink = tile.getchannel('A').getbbox()
        shifted = Image.new('RGBA', tile.size)
        shifted.paste(tile.crop(ink), (17*scale,ink[1]))
        sheet.paste(shifted,box)
        actual = Image.open(R/'Build/TitleLogo-v102/Variants/Custom/+Title/mat_title_001.dds').convert('RGBA')
        assert actual.size == sheet.size and actual.tobytes() == sheet.tobytes(), 'Caption shift or unrelated sprites changed'
        actual_tile = actual.crop(box); moved = actual_tile.getchannel('A').getbbox()
        assert moved[0] == 17*scale
        assert actual_tile.crop(moved).tobytes() == tile.crop(ink).tobytes(), 'Lettering must not be resampled'
    if title.get('customHalo'):
        source_halo = Image.open(original.parent/'mat_title_004.dds').convert('RGBA')
        fixed_halo = Image.open(R/'Build/TitleLogo-v102/Variants/Custom/+Title/mat_title_004.dds').convert('RGBA')
        verify_halo(source_halo, fixed_halo)
        assert digest(R/'Build/TitleLogo-v102/Variants/Custom/+Title/mat_title_004.dds') == title['customHalo']['resultSha256']
    review = json.loads((R/'Build/Translation-v102/resource-verification.json').read_text(encoding='utf-8-sig'))
    for item in review['patches']:
        assert digest(dev/item['relative']) == item['after_sha256']
    config = json.loads((R/'Build/Development-v102/hmm-config-verification.json').read_text(encoding='utf-8-sig'))
    gallery = json.loads((R/'Build/Development-v102/GalleryAudit/verification.json').read_text(encoding='utf-8-sig'))
    combinations = len(schema['Enums']['WorldMapVariant']) * len(schema['Enums']['UnleasHDCompatibility']) * len(schema['Enums']['TitleLogoVariant'])
    assert config['passed'] and len(config['choices']) == combinations
    assert gallery['passed'] and gallery['cells'] == 272
    result = {'passed':True,'unchangedBaseFiles':unchanged,'reviewedResources':len(review['patches']),
              'hmmCombinations':combinations,'galleryTitleCells':272,'titleVariants':len(title['variants']), 'haloRgbValidated':bool(title.get('customHalo')),
              'gameLaunched':False,'releasePackaged':False,'installedGameModified':False}
    (R/'Build/Development-v102/verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    verify()
