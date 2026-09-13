"""Export original title artwork and build opt-in title scenes; no release packaging."""
from pathlib import Path
import argparse, hashlib, json, shutil, struct, subprocess
from PIL import Image, ImageFilter, ImageChops
from probe_animated_ui import parse

R = Path(__file__).resolve().parents[1]
W = R / 'Build/TitleLogo-v102'
EXPORT = R / 'outputs/TitleLogo-v102-Editing'
CUSTOM = R / 'Assets/TitleLogo/CustomLogo.png'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def arc(argument, packing=False):
    subprocess.run([str(R/'Tools/HedgeArcPack/HedgeArcPack.exe'), str(argument)],
                   input='hh\n' if packing else '\n', text=True, capture_output=True, check=True)

def scene_slots(blob):
    base = blob.index(b'nCPJ')
    u = lambda offset: struct.unpack_from('>I', blob, offset)[0]
    ptr = lambda offset: base + u(offset)
    root = ptr(base + 16)
    table, names = ptr(root + 4), ptr(root + 8)
    result = {}
    for index in range(u(root)):
        name = ptr(names + 8 * index)
        name = blob[name:blob.index(0, name)].decode('ascii')
        result[name] = table + 4 * u(names + 8 * index + 4)
    assert {'title_1', 'title_2'} <= result.keys()
    return result

def left_align_caption(sheet, kana_box):
    """Move supplied pixels inside their sprite, without changing art or animation."""
    scale = sheet.width / 1024
    box = tuple(round(v*scale) for v in kana_box)
    tile = sheet.crop(box)
    ink = tile.getchannel('A').getbbox()
    assert ink, 'Custom caption must contain visible pixels'
    target_x = round(17*scale)
    shifted = Image.new('RGBA', tile.size)
    shifted.paste(tile.crop(ink), (target_x, ink[1]))
    assert target_x + ink[2]-ink[0] <= tile.width
    result = sheet.copy(); result.paste(shifted, box)
    new_ink = (target_x, ink[1], target_x+ink[2]-ink[0], ink[3])
    # title_2's parent scale is 0.85; coordinates are relative to the halo sprite.
    bounds = [21.1 + new_ink[0]*.85/scale, 10.825 + new_ink[1]*.85/scale,
              21.1 + new_ink[2]*.85/scale, 10.825 + new_ink[3]*.85/scale]
    return result, {'sourceInk': list(ink), 'shiftedInk': list(new_ink),
                    'haloInkBounds': bounds, 'pixelShiftX': target_x-ink[0]}


def caption_outer_glow(edited_sheet, kana_box):
    """Derive a soft outer glow from the actual Korean strokes, never a rectangle."""
    scale = edited_sheet.width / 1024
    box = tuple(round(v*scale) for v in kana_box)
    alpha = edited_sheet.crop(box).getchannel('A').resize((343,23), Image.Resampling.LANCZOS)
    mask = Image.new('L',(640,640)); mask.paste(alpha,(21,11))
    glow = mask.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(2.25))
    return glow.point(lambda value: min(255, round(value*1.3)))


def smooth_caption_halo(original, source_sheet, caption_light):
    """Stroke-shaped caption glow over the logo's glyph-free body contour.

    Source title_2 transforms put Sonic at (10.05,38.025), Earth at (314.775,11.25)
    in the 559x303 halo sprite. Reconstruct just the upper body silhouette so
    shortening the caption does not leave the original Japanese glyph glow.
    RGB encodes additive light; alpha remains 255 throughout.
    """
    assert original.size == (640, 640)
    assert original.getchannel('A').getextrema() == (255, 255)
    body = Image.new('L', original.size)
    for box, size, xy in [((0,1,512,134),(435,113),(10,38)),
                           ((750,101,1024,374),(233,232),(315,11))]:
        tile = source_sheet.crop(box).getchannel('A').resize(size, Image.Resampling.LANCZOS)
        layer = Image.new('L', original.size); layer.paste(tile,xy)
        body = ImageChops.lighter(body, layer)
    body = body.filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.GaussianBlur(2))
    light = ImageChops.lighter(body,caption_light)
    before = original.getchannel('R'); result = original.copy()
    for y in range(72):
        for x in range(420):
            blend = min(1.0, (72-y)/20) * min(1.0, (420-x)/36)
            value = round(light.getpixel((x,y))*blend + before.getpixel((x,y))*(1-blend))
            result.putpixel((x,y),(value,value,value,255))
    return result

def build(custom=None):
    custom = custom or (CUSTOM if CUSTOM.is_file() else None)
    original = W / 'Originals/Core'
    original.mkdir(parents=True, exist_ok=True)
    for source in (R/'UnleashedRecomp-Windows/game').glob('Title.ar*'):
        shutil.copy2(source, original/source.name)
    arc(original/'Title.ar.00')
    source = original/'Title'
    EXPORT.mkdir(parents=True, exist_ok=True)
    for name in ('mat_title_001.dds', 'mat_title_004.dds'):
        shutil.copy2(source/name, EXPORT/name)
        Image.open(source/name).save(EXPORT/(Path(name).stem+'-original.png'))
    scenes = parse(source/'ui_title.yncp')
    japanese = next(s for s in scenes if s['name'] == '/title_2')
    sheet = Image.open(source/'mat_title_001.dds').convert('RGBA')
    parts = []
    for cast in japanese['casts']:
        if cast['name'] not in ('txt_KANA', 'txt_sonic', 'txt_world', 'txt_adventure', 'img_earth'):
            continue
        texture, *uv = cast['subimage']
        assert texture == 0
        box = [round(v * (sheet.width if i % 2 == 0 else sheet.height)) for i, v in enumerate(uv)]
        filename = cast['name']+'-original.png'
        sheet.crop(box).save(EXPORT/filename)
        parts.append({'file': filename, 'box': box, 'size': [box[2]-box[0], box[3]-box[1]]})
    (EXPORT/'parts.json').write_text(json.dumps(parts, indent=2)+'\n', encoding='utf8')
    (EXPORT/'README-KO.md').write_text('''# 일본어판 타이틀 로고 편집 원본

게임 원본의 DDS를 손실 없이 PNG로 풀었습니다. AI 생성·보정은 하지 않았습니다.
로고는 한 장의 완성 이미지가 아니라 게임이 조합·애니메이션하는 여러 조각입니다.

- **mat_title_001-original.png**: 실제 편집용 전체 시트, 1024×512, 투명 RGBA. 위치와 캔버스 크기를 유지해서 수정본을 주세요. 전체 시트를 정수 배율로 확대한 PNG도 지원합니다.
- **txt_KANA-original.png**: 상단 「ソニック ワールドアドベンチャー」만 추출한 404×27 PNG. 이 문구만 편집하시면 이 파일만 같은 크기로 돌려주셔도 됩니다.
- txt_sonic / txt_world / txt_adventure / img_earth: 로고의 개별 원본 조각입니다. 위치는 parts.json에 있습니다.
- **mat_title_004-original.png**: 로고 외곽 발광용 시트입니다. 큰 윤곽까지 바꿀 때 참고하세요.
- 같은 이름의 DDS 두 개는 게임에 들어 있던 원본 바이트 그대로입니다.

투명도를 유지한 PNG로 저장해 주세요. 흰 글자가 안 보이면 편집기 배경을 어둡게 바꿔 보세요.
사용자 수정본은 Assets/TitleLogo/CustomLogo.png에 별도로 보존하며, 위 파일들은 편집 전 원본입니다.
''', encoding='utf8')
    blob = (source/'ui_title.yncp').read_bytes()
    slots = scene_slots(blob)
    report = {'sourceArchiveSha256': sha(original/'Title.ar.00'), 'sourceSceneSha256': sha(source/'ui_title.yncp'),
              'customReady': bool(custom), 'customSourceSha256': sha(custom) if custom else None,
              'gameLaunched': False, 'variants': []}
    for variant, target in [('Original', 'title_1'), ('Japanese', 'title_2')] + ([('Custom', 'title_2')] if custom else []):
        folder = W/'Variants'/variant/'+Title'
        folder.mkdir(parents=True, exist_ok=True)
        changed = bytearray(blob)
        # Both runtime branches resolve to the chosen scene, even with HMM's alternate-title code.
        for name in ('title_1', 'title_2'):
            changed[slots[name]:slots[name]+4] = blob[slots[target]:slots[target]+4]
        assert all(a == b or any(slots[n] <= i < slots[n]+4 for n in ('title_1', 'title_2'))
                   for i, (a, b) in enumerate(zip(blob, changed)))
        (folder/'ui_title.yncp').write_bytes(changed)
        parsed = parse(folder/'ui_title.yncp')
        for name in ('/title_1', '/title_2'):
            assert next(s for s in parsed if s['name'] == name)['casts'] == next(s for s in scenes if s['name'] == '/'+target)['casts']
        if variant == 'Custom':
            im = Image.open(custom)
            assert im.mode == 'RGBA', 'Custom logo must preserve RGBA transparency.'
            kana = next(p for p in parts if p['file'] == 'txt_KANA-original.png')
            if im.size == tuple(kana['size']):
                edited = sheet.copy()
                edited.paste(im, tuple(kana['box']))
            else:
                assert im.width % sheet.width == 0 and im.width // sheet.width in range(1, 9)
                assert im.height == sheet.height * (im.width // sheet.width), 'Keep the atlas aspect ratio.'
                edited = im
            edited, caption_layout = left_align_caption(edited, kana['box'])
            report['customCaptionLayout'] = caption_layout
            # Uncompressed RGBA avoids recompressing and degrading unrelated logo sprites.
            edited.save(folder/'mat_title_001.dds')
            reopened = Image.open(folder/'mat_title_001.dds').convert('RGBA')
            assert reopened.size == edited.size and reopened.tobytes() == edited.tobytes()
            halo = Image.open(source/'mat_title_004.dds').convert('RGBA')
            caption_light = caption_outer_glow(edited, kana['box'])
            smooth = smooth_caption_halo(halo, sheet, caption_light)
            caption_light.save(EXPORT/'caption-outer-glow-mask.png')
            smooth.save(folder/'mat_title_004.dds')
            assert Image.open(folder/'mat_title_004.dds').convert('RGBA').tobytes() == smooth.tobytes()
            smooth.save(EXPORT/'mat_title_004-custom-smooth.png')
            report['customHalo'] = {'style': 'left-aligned-glyph-outer-glow',
                'glowSpreadPixels': 3, 'glowBlurPixels': 2.25, 'glowGain': 1.3,
                'encoding': 'RGB luminance, opaque alpha',
                'modifiedBox': [0, 0, 420, 72], 'sourceSha256': sha(source/'mat_title_004.dds'),
                'resultSha256': sha(folder/'mat_title_004.dds')}

        arc(folder, packing=True)
        verify = W/'Verify'/variant
        verify.mkdir(parents=True, exist_ok=True)
        for p in folder.parent.glob('+Title.ar*'):
            shutil.copy2(p, verify/p.name)
        arc(verify/'+Title.ar.00')
        for p in folder.iterdir():
            assert p.read_bytes() == (verify/'+Title'/p.name).read_bytes()
        report['variants'].append({'name': variant, 'targetScene': target, 'archiveSha256': sha(folder.parent/'+Title.ar.00'),
                                   'files': sorted(p.name for p in folder.iterdir()), 'roundTrip': True})
    (W/'verification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--custom', type=Path)
    build(parser.parse_args().custom)
