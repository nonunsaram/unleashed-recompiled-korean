"""Replace only JP caption blocks in the original opening World Adventure DDS."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'Build/OPLogoInvestigation'
ORIGINAL=WORK/'Decoded/JP/logo.dds'
TEXCONV=WORK/'Tools/texconv.exe'
OUTPUT=WORK/'OriginalBased/OPmovie_titlelogo_KR_World.dds'
# DXT5 4x4 blocks. Only edited blocks inside this rectangle are replaced.
BLOCK_RECT=(348,200,752,288)


def restore_body_top(original: Image.Image) -> Image.Image:
    """Remove caption AND its matte without cutting through the globe.

    A horizontal y cutoff leaves the caption's white backing as a shelf and
    erases the rising left edge of the globe. Find the connected logo instead:
    the Japanese glyphs are separated from it by white pixels. Its upper
    envelope gives the actual curved outline, including the S/O valleys.
    """
    native=np.asarray(original)
    ink=(np.min(native[:,:,:3],axis=2)<128) & (native[:,:,3]>200)
    connected=Image.fromarray(ink.astype(np.uint8),'L').copy()
    ImageDraw.floodfill(connected,(650,263),2)
    body=np.asarray(connected)==2
    assert body[260,650] and body[245,740]
    assert not np.any(body[220:252,380:710])
    top=np.where(body.any(axis=0),body.argmax(axis=0),720)
    yy=np.arange(720)[:,None]
    silhouette=(yy>=top[None,:]).astype(np.uint8)*255
    # Match the native soft white outline (roughly 7px spread, 3px blur).
    halo=np.asarray(Image.fromarray(silhouette,'L').filter(
        ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(3.0)))
    data=native.copy()
    x1,y1,x2,y2=BLOCK_RECT
    # Blend into undamaged source glow at the sides, never at a horizontal
    # cut across the top. Preserve the source edge antialiasing and all ink.
    weight=np.zeros(1280,dtype=np.float32)
    weight[360:732]=1
    weight[348:360]=np.linspace(0,1,12,endpoint=False)
    weight[732:752]=np.linspace(1,0,20,endpoint=False)
    exterior=(yy<top[None,:]-1)
    editable=np.zeros((720,1280),dtype=bool)
    editable[y1:y2,x1:x2]=True
    exterior &= editable
    blend=weight[None,:]*exterior
    repaired=np.full_like(data,255)
    repaired[:,:,3]=halo
    data=np.rint(data*(1-blend[:,:,None])+repaired*blend[:,:,None]).astype(np.uint8)
    assert np.array_equal(native[body],data[body])
    return Image.fromarray(data,'RGBA')


def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_rgba()->Image.Image:
    original=Image.open(ORIGINAL).convert('RGBA')
    body=restore_body_top(original)
    caption=Image.open(ROOT/'Assets/TitleLogo/CustomLogo.png').convert('RGBA')
    caption=caption.crop(caption.getchannel('A').getbbox())
    caption=caption.resize((210,21),Image.Resampling.LANCZOS)
    xy=(391,231)
    alpha=Image.new('L',original.size)
    alpha.paste(caption.getchannel('A'),xy)
    glow=alpha.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(2.5))
    white=Image.new('RGBA',original.size,(255,255,255,0))
    white.putalpha(glow)
    body=Image.alpha_composite(body,white)
    black=Image.new('RGBA',caption.size,(0,0,0,0))
    black.putalpha(caption.getchannel('A'))
    body.alpha_composite(black,xy)
    before=np.asarray(original)
    after=np.asarray(body)
    x1,y1,x2,y2=BLOCK_RECT
    unchanged=np.ones((720,1280),dtype=bool)
    unchanged[y1:y2,x1:x2]=False
    assert np.array_equal(before[unchanged],after[unchanged])
    return body


def splice_blocks(source:bytes,edited:bytes,changed_pixels:np.ndarray)->bytes:
    assert len(source)==len(edited)==921728
    assert source[:4]==edited[:4]==b'DDS '
    assert source[84:88]==edited[84:88]==b'DXT5'
    # Keep the original header, format flags and every untouched DXT5 block.
    out=bytearray(source)
    x1,y1,x2,y2=BLOCK_RECT
    blocks_per_row=1280//4
    for by in range(y1//4,y2//4):
        for bx in range(x1//4,x2//4):
            if not changed_pixels[by*4:by*4+4,bx*4:bx*4+4].any():
                continue
            offset=128+(by*blocks_per_row+bx)*16
            out[offset:offset+16]=edited[offset:offset+16]
    return bytes(out)


def main()->None:
    assert TEXCONV.is_file() and ORIGINAL.is_file()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    rgba=make_rgba()
    png=OUTPUT.parent/'OPmovie_titlelogo_KR_World.png'
    rgba.save(png)
    subprocess.run([str(TEXCONV),'-nologo','-f','BC3_UNORM','-m','1','-y',
                    '-o',str(OUTPUT.parent),str(png)],check=True)
    encoded=OUTPUT.with_suffix('.dds')
    assert encoded==OUTPUT
    source=np.asarray(Image.open(ORIGINAL).convert('RGBA'))
    intended=np.asarray(rgba)
    changed_pixels=np.any(source!=intended,axis=2)
    final=splice_blocks(ORIGINAL.read_bytes(),encoded.read_bytes(),changed_pixels)
    OUTPUT.write_bytes(final)
    candidate=np.asarray(Image.open(OUTPUT).convert('RGBA'))
    unchanged=np.ones((720,1280),dtype=bool)
    x1,y1,x2,y2=BLOCK_RECT
    unchanged[y1:y2,x1:x2]=False
    assert np.array_equal(source[unchanged],candidate[unchanged])
    assert not np.array_equal(source[~unchanged],candidate[~unchanged])
    image=Image.fromarray(candidate,'RGBA')
    canvas=Image.new('RGB',image.size,'#202838')
    canvas.paste(image,mask=image.getchannel('A'))
    canvas.save(OUTPUT.parent/'World-opening-corrected.jpg',quality=97)
    canvas.save(OUTPUT.parent/'World-opening-corrected.png')
    # Regression: the old horizontal crop erased this part of the globe.
    assert np.array_equal(source[249:253,730:736],candidate[249:253,730:736])
    # Regression: a hard y=251 crop creates an abrupt alpha step in the
    # exposed top edge to the right of the shorter Korean caption.
    fade=candidate[235:258,620:696,3].astype(np.int16)
    max_step=int(np.abs(np.diff(fade,axis=0)).max())
    assert max_step<=55, max_step
    # Blocks with no edited pixels must survive byte-for-byte, including
    # blocks inside the replacement rectangle.
    dirty=changed_pixels.reshape(180,4,320,4).any(axis=(1,3))
    original_blocks=np.frombuffer(ORIGINAL.read_bytes()[128:],np.uint8).reshape(180,320,16)
    final_blocks=np.frombuffer(final[128:],np.uint8).reshape(180,320,16)
    assert np.array_equal(original_blocks[~dirty],final_blocks[~dirty])
    report={
        'passed':True,'source':str(ORIGINAL),'output':str(OUTPUT),
        'sourceSha256':digest(ORIGINAL),'outputSha256':digest(OUTPUT),
        'format':'1280x720 DXT5; one mip',
        'changedBlockRectangle':[x1,y1,x2,y2],
        'outsideRectangleIdenticalToOriginal':True,
        'originalOutsideCaptionRectanglePreserved':True,
        'uneditedDxtBlocksIdentical':True,
        'changedDxtBlocks':int(dirty.sum()),
        'globeLeftArcRestored':True,
        'topEdgeMaxAlphaStep':max_step,
        'captionTextSizeAndPositionPreserved':True,
        'gameplayVerified':False,
    }
    (OUTPUT.parent/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
