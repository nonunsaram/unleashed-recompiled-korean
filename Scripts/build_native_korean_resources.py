from pathlib import Path
import sys, struct, json, hashlib, math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Tools/UIRuntime'))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import distance_transform_edt
import zstandard
W=R/'Build/NativeUIWork';O=R/'Build/Korean Full UI Playtest/Native';O.mkdir(parents=True,exist_ok=True)
ko=json.loads((R/'Translation/native-ui-ko.json').read_text(encoding='utf8'))
ach=json.loads((R/'Translation/achievements-ko.json').read_text(encoding='utf8'))
display=json.loads((R/'Translation/native-ui-display-overrides.json').read_text(encoding='utf8'))
chars=sorted((set(''.join(ko)+display['text_language_english']+''.join(s for v in ach.values() for s in v))|set(chr(c) for c in range(33,127)))-set('\n\r\t'))
b=bytearray((W/'font-snapshot-33262e0.bin').read_bytes())
u=lambda o:struct.unpack_from('<I',b,o)[0]
q=lambda o:struct.unpack_from('<Q',b,o)[0]
f=lambda o:struct.unpack_from('<f',b,o)[0]
def put(o,fmt,*v):struct.pack_into('<'+fmt,b,o,*v)
relocs=list(struct.unpack_from('<'+'I'*u(8),b,u(12)))
b=b[:u(12)]
def append(data,align=8):
    b.extend(bytes((-len(b))%align));p=len(b);b.extend(data);return p
dds=(W/'dds-3335d80.bin').read_bytes();oldw,oldh=u(80),u(84)
assert oldw==oldh==2048 and len(dds)==148+oldw*oldh*4
tiles=[];fontrows=[];x=0;y=oldh;rowh=0
for i in range(u(104)):
    p=q(q(112)+8*i);gp=q(p+48);ng=u(p+40)
    glyphs=bytearray(b[gp:gp+40*ng]);present={struct.unpack_from('<I',glyphs,j*40)[0]>>2 for j in range(ng)}
    size=round(f(p+20));ascent=f(p+104)
    path=R/'Tools/Fonts'/('LINESeedKR-Bd.ttf' if i in (2,3,5) else 'LINESeedKR-Rg.ttf')
    font=ImageFont.truetype(str(path),size*4);small=ImageFont.truetype(str(path),size)
    new=[]
    for c in chars:
        cp=ord(c)
        if cp in present and not (i==2 and 33<=cp<=126):continue
        # Only setting values use NewRodin-DB (index 2). Preserve original Latin in headings, tabs and other faces.
        l,t,r,bot=small.getbbox(c,anchor='ls');tw=r-l+10;th=bot-t+10
        mask=Image.new('L',(tw*4,th*4));ImageDraw.Draw(mask).text(((5-l)*4,(5-t)*4),c,font=font,anchor='ls',fill=255)
        a=np.array(mask)>127
        dist=(distance_transform_edt(a)-distance_transform_edt(~a))/4
        # 0.4.9: keep the glyph contour and fill; narrow only the exterior SDF band.
        # The native outline=4 drew ~2.67 atlas pixels, versus the bitmap guide's ~1px.
        exterior_scale=(8/3) if i==4 else 2.0 if i in (1,2,3,5) else 1.0
        sdf=Image.fromarray(np.clip((dist/8+.5)*255,0,255).astype('uint8')).resize((tw,th),Image.Resampling.LANCZOS)
        encoded=np.array(sdf,dtype=np.float32)
        # Remap after resampling so all interior pixels and the 0.5 contour stay intact.
        encoded=np.where(encoded<127.5,127.5+(encoded-127.5)*exterior_scale,encoded)
        sdf=Image.fromarray(np.clip(np.rint(encoded),0,255).astype('uint8'))
        rgba=Image.merge('RGBA',(sdf,sdf,sdf,Image.new('L',sdf.size,255)))
        if x+tw+1>oldw:x=0;y+=rowh+1;rowh=0
        tiles.append((rgba,x,y));new.append((cp,small.getlength(c),l-5,ascent+t-5,r+5,ascent+bot+5,x,y,tw,th))
        x+=tw+1;rowh=max(rowh,th)
    fontrows.append((p,gp,ng,glyphs,new))
newh=2**math.ceil(math.log2(y+rowh+1));atlas=Image.new('RGBA',(oldw,newh),(0,0,0,255))
atlas.paste(Image.frombytes('RGBA',(oldw,oldh),dds[148:]),(0,0))
for tile,tx,ty in tiles:atlas.paste(tile,(tx,ty))
ratio=oldh/newh
for p,gp,ng,glyphs,new in fontrows:
    fallback=(q(p+56)-gp)//40
    for j in range(ng):
        for off in (28,36):struct.pack_into('<f',glyphs,j*40+off,struct.unpack_from('<f',glyphs,j*40+off)[0]*ratio)
    ac=u(p);lc=u(p+24);n=max(ac,lc,max(ord(c) for c in chars)+1)
    advances=bytearray(b[q(p+8):q(p+8)+ac*4])+struct.pack('<f',f(p+16))*(n-ac)
    lookup=bytearray(b[q(p+32):q(p+32)+lc*2])+b'\xff\xff'*(n-lc)
    pages=struct.unpack_from('<H',b,p+116)[0]
    for j,(cp,adv,l,t,r,bot,tx,ty,tw,th) in enumerate(new):
        glyphs.extend(struct.pack('<I9f',(cp<<2)|2,adv,l,t,r,bot,tx/oldw,ty/newh,(tx+tw)/oldw,(ty+th)/newh))
        struct.pack_into('<f',advances,cp*4,adv);struct.pack_into('<H',lookup,cp*2,ng+j);pages|=1<<(cp//4096)
    newgp=append(glyphs);put(p+40,'IIQ',ng+len(new),ng+len(new),newgp);put(p+56,'Q',newgp+fallback*40)
    put(p,'IIQ',n,n,append(advances));put(p+24,'IIQ',n,n,append(lookup));put(p+116,'H',pages)
    for cp,*_ in new:assert struct.unpack_from('<H',b,q(p+32)+cp*2)[0]!=65535
put(84,'I',newh);put(92,'f',1/newh);put(100,'f',f(100)*ratio)
for j in range(64):
    for off in (4,12):put(152+j*16+off,'f',f(152+j*16+off)*ratio)
rp=append(struct.pack('<'+'I'*len(relocs),*relocs),4);put(12,'I',rp)
for off in relocs:assert 0<=q(off)<len(b)
hdr=bytearray(dds[:148]);struct.pack_into('<I',hdr,12,newh)
rawdds=bytes(hdr)+atlas.tobytes()
(W/'korean-font-snapshot.bin').write_bytes(b);(W/'korean-font.dds').write_bytes(rawdds)
for name,raw in [('korean-font-snapshot',b),('korean-font',rawdds)]:
    (W/(name+'.zst')).write_bytes(zstandard.ZstdCompressor(level=12).compress(raw))
atlas.crop((0,oldh,1024,min(oldh+512,newh))).save(W/'korean-native-font-preview.png')
# Replace only the English achievement strings in the existing uncompressed XEX resource.
original_path=R/'UnleashedRecomp-Windows/korean-mod-backup-v040/patched/default.xex'
if not original_path.exists():original_path=R/'UnleashedRecomp-Windows/patched/default.xex'
xex=bytearray(original_path.read_bytes());source_hash=hashlib.sha256(xex).hexdigest()
assert source_hash=='8940eef6cdbf8585a58991fe5a7c7bfb4bc1b041c1628bc2757adcdd7a11b520', 'Unsupported source XEX'
src=json.loads((R/'Translation/achievements-source.json').read_text(encoding='utf8'));s=src['xdbf_offset']
h=struct.unpack_from('>6I',xex,s);base=s+24+h[2]*18+h[4]*8
entries=[struct.unpack_from('>HQII',xex,s+24+i*18) for i in range(h[3])]
idx=next(i for i,e in enumerate(entries) if e[:2]==(3,1));ns,eid,off,n=entries[idx]
pos=base+off;magic,ver,size,count=struct.unpack_from('>IIIH',xex,pos);ptr=pos+14;strings={}
for _ in range(count):
    sid,ln=struct.unpack_from('>HH',xex,ptr);ptr+=4;strings[sid]=xex[ptr:ptr+ln].decode('utf8');ptr+=ln
expected={}
for item in src['items']:
    for sid,text in zip(item['string_ids'],ach[str(item['id'])]):
        if sid in expected:assert expected[sid]==text
        expected[sid]=text;strings[sid]=text
payload=b''.join(struct.pack('>HH',sid,len(t.encode()))+t.encode() for sid,t in strings.items())
chunk=struct.pack('>IIIH',magic,ver,14+len(payload),count)+payload
assert xex[0x2178:0x2180]==b'53450812'
resource_size=struct.unpack_from('>I',xex,0x2184)[0];start=s+resource_size
assert start+len(chunk)<=len(xex) and not any(xex[start:start+len(chunk)])
xex[start:start+len(chunk)]=chunk
struct.pack_into('>II',xex,s+24+idx*18+10,start-base,len(chunk))
struct.pack_into('>I',xex,0x2184,resource_size+len(chunk))
free=s+24+h[2]*18;struct.pack_into('>II',xex,free,start+len(chunk)-base,0)
dest=O/'patched/default.xex';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(xex)
# Reparse the emitted table and verify all 150 fields by ID.
ptr=start+14;back={}
for _ in range(count):
    sid,ln=struct.unpack_from('>HH',xex,ptr);ptr+=4;back[sid]=xex[ptr:ptr+ln].decode('utf8');ptr+=ln
assert all(back[k]==v for k,v in strings.items()) and len(ach)==50
report={'native_unique_characters':len(chars),'added_glyphs_per_font':[len(row[4]) for row in fontrows],'atlas_size':[oldw,newh],'snapshot_size':len(b),'dds_size':len(rawdds),'achievements':50,'achievement_fields':150,'original_xex_sha256':source_hash,'patched_xex_sha256':hashlib.sha256(xex).hexdigest(),'verified':True}
(W/'resources-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)

import subprocess
subprocess.run([sys.executable,str(R/'Scripts/patch_mission_loading_resource_v054.py')],check=True)
