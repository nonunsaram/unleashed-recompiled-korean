"""Add the missing 혹 glyph to all six preserved native fonts, without repacking them."""
from pathlib import Path
import sys,struct,math,hashlib,json

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'Tools/UIRuntime'))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import distance_transform_edt
import zstandard

def extend(raw,pe):
    resources={}
    for name,inst,loc in [('snapshot',0xfa9f4,0xfa9f0),('texture',0xd0fa8,0xd0fa4)]:
        target=inst+7+struct.unpack('<i',pe.get_data(inst+3,4))[0]
        size=struct.unpack('<I',pe.get_data(loc,4))[0]
        resources[name]=zstandard.ZstdDecompressor().decompress(pe.get_data(target,size))
    original=resources['snapshot'];b=bytearray(original)
    u=lambda off:struct.unpack_from('<I',b,off)[0]
    q=lambda off:struct.unpack_from('<Q',b,off)[0]
    f=lambda off:struct.unpack_from('<f',b,off)[0]
    relocations=list(struct.unpack_from('<'+'I'*u(8),b,u(12)))
    b=b[:u(12)]
    def append(data,alignment=8):
        b.extend(bytes((-len(b))%alignment));offset=len(b);b.extend(data);return offset
    width,height=u(80),u(84);assert (width,height)==(2048,4096) and u(104)==6
    original_dds=resources['texture'];assert len(original_dds)==148+width*height*4
    atlas=Image.frombytes('RGBA',(width,height),original_dds[148:]);old_pixels=np.array(atlas)
    fonts=[];maximum_y=0
    for index in range(u(104)):
        p=q(q(112)+index*8);gp=q(p+48);ng=u(p+40)
        glyphs=bytes(b[gp:gp+ng*40]);cps=[struct.unpack_from('<I',glyphs,j*40)[0]>>2 for j in range(ng)]
        assert ord('혹') not in cps
        maximum_y=max(maximum_y,max(struct.unpack_from('<f',glyphs,j*40+36)[0]*height for j in range(ng)))
        fonts.append((index,p,gp,ng,glyphs))
    x=0;y=math.ceil(maximum_y)+2;rectangles=[];details=[]
    for index,p,gp,ng,glyphs in fonts:
        size=round(f(p+20));ascent=f(p+104)
        path=R/'Tools/Fonts'/('LINESeedKR-Bd.ttf' if index in (2,3,5) else 'LINESeedKR-Rg.ttf')
        font=ImageFont.truetype(str(path),size*4);small=ImageFont.truetype(str(path),size)
        left,top,right,bottom=small.getbbox('혹',anchor='ls');tw=right-left+10;th=bottom-top+10
        assert x+tw<width and y+th<height
        assert np.all(old_pixels[y:y+th,x:x+tw]==np.array([0,0,0,255])), 'Occupied native atlas space'
        mask=Image.new('L',(tw*4,th*4))
        ImageDraw.Draw(mask).text(((5-left)*4,(5-top)*4),'혹',font=font,anchor='ls',fill=255)
        a=np.array(mask)>127;distance=(distance_transform_edt(a)-distance_transform_edt(~a))/4
        sdf=Image.fromarray(np.clip((distance/8+.5)*255,0,255).astype('uint8')).resize((tw,th),Image.Resampling.LANCZOS)
        scale=(8/3) if index==4 else 2.0 if index in (1,2,3,5) else 1.0
        pixels=np.array(sdf,dtype=np.float32);pixels=np.where(pixels<127.5,127.5+(pixels-127.5)*scale,pixels)
        sdf=Image.fromarray(np.clip(np.rint(pixels),0,255).astype('uint8'))
        tile=Image.merge('RGBA',(sdf,sdf,sdf,Image.new('L',sdf.size,255)))
        atlas.paste(tile,(x,y));advance=small.getlength('혹');cp=ord('혹')
        record=struct.pack('<I9f',(cp<<2)|2,advance,left-5,ascent+top-5,right+5,ascent+bottom+5,
                           x/width,y/height,(x+tw)/width,(y+th)/height)
        new_gp=append(glyphs+record)
        fallback=(q(p+56)-gp)//40;assert 0<=fallback<ng
        struct.pack_into('<IIQ',b,p+40,ng+1,ng+1,new_gp)
        struct.pack_into('<Q',b,p+56,new_gp+fallback*40)
        assert cp<u(p) and cp<u(p+24)
        assert struct.unpack_from('<H',b,q(p+32)+cp*2)[0]==65535
        struct.pack_into('<f',b,q(p+8)+cp*4,advance)
        struct.pack_into('<H',b,q(p+32)+cp*2,ng)
        pages=struct.unpack_from('<H',b,p+116)[0]|(1<<(cp//4096));struct.pack_into('<H',b,p+116,pages)
        assert bytes(b[new_gp:new_gp+ng*40])==glyphs
        rectangles.append((x,y,x+tw,y+th));details.append({'font_index':index,'glyph_id':ng,'codepoint':cp,'rectangle':rectangles[-1]})
        x+=tw+2
    table=append(struct.pack('<'+'I'*len(relocations),*relocations),4);struct.pack_into('<I',b,12,table)
    for off in relocations:assert 0<=q(off)<len(b)
    pixels=np.array(atlas);allowed=np.zeros((height,width),dtype=bool)
    for x0,y0,x1,y1 in rectangles:allowed[y0:y1,x0:x1]=True
    assert np.array_equal(pixels[~allowed],old_pixels[~allowed])
    # Verify every character in the current native UI and achievements resolves.
    ui=json.loads((R/'Translation/native-ui-ko.json').read_text(encoding='utf8'))
    ach=json.loads((R/'Translation/achievements-ko.json').read_text(encoding='utf8'))
    chars=set(''.join(ui)+''.join(s for values in ach.values() for s in values))-set('\n\r\t')
    for _,p,_,_,_ in fonts:
        for c in chars:
            cp=ord(c);assert cp<u(p+24)
            glyph=struct.unpack_from('<H',b,q(p+32)+cp*2)[0]
            assert glyph!=65535 and u(q(p+48)+glyph*40)>>2==cp,(c,p,glyph)
    snapshot=bytes(b);dds=original_dds[:148]+atlas.tobytes()
    out=R/'Build/Translation-v101/NativeFont';out.mkdir(parents=True,exist_ok=True)
    (out/'snapshot.bin').write_bytes(snapshot);(out/'font.dds').write_bytes(dds)
    atlas.crop((0,y,min(x+2,width),max(v[3] for v in rectangles)+2)).resize((x*4,(max(v[3] for v in rectangles)-y+2)*4)).save(out/'added-glyphs.png')
    compressed_snapshot=zstandard.ZstdCompressor(level=12).compress(snapshot)
    compressed_texture=zstandard.ZstdCompressor(level=12).compress(dds)
    assert zstandard.ZstdDecompressor().decompress(compressed_snapshot)==snapshot
    assert zstandard.ZstdDecompressor().decompress(compressed_texture)==dds
    return compressed_snapshot,compressed_texture,len(snapshot),{'added_character':'혹','font_count':6,'glyphs':details,
        'all_existing_glyph_records_preserved':True,'pixels_outside_new_tiles_preserved':True,
        'all_current_native_characters_resolve':True,'atlas_size':[width,height],
        'snapshot_sha256':hashlib.sha256(snapshot).hexdigest(),'texture_sha256':hashlib.sha256(dds).hexdigest()}
