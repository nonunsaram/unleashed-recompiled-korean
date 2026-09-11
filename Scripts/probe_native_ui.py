from pathlib import Path
import sys,struct,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'Tools/UIRuntime'))
import pefile,zstandard
out=ROOT/'Build/NativeUIWork';out.mkdir(parents=True,exist_ok=True)
data=(ROOT/'UnleashedRecomp-Windows/UnleashedRecomp.exe').read_bytes();pe=pefile.PE(data=data,fast_load=True)
print([(s.Name.decode().strip('\0'),hex(s.VirtualAddress),s.SizeOfRawData) for s in pe.sections],flush=True)
frames=[];pos=0
while True:
    pos=data.find(b'\x28\xb5\x2f\xfd',pos)
    if pos<0:break
    try:
        d=zstandard.ZstdDecompressor().decompressobj();raw=d.decompress(data[pos:]);consumed=len(data)-pos-len(d.unused_data)
        if not d.eof:raise ValueError()
        kind='dds' if raw.startswith(b'DDS ') else 'other'
        if len(raw)>=16:
            header=struct.unpack_from('<4I',raw)
            if 18000<header[0]<200000 and header[1]<4096 and header[3]<len(raw):kind='font-snapshot'
        item={'offset':pos,'rva':pe.get_rva_from_offset(pos),'compressed':consumed,'raw':len(raw),'kind':kind,'head':raw[:16].hex()}
        if kind=='font-snapshot' or (kind=='dds' and len(raw)>10_000_000):
            name=f'{kind}-{pos:x}.bin';(out/name).write_bytes(raw);item['file']=name
            print(item,flush=True)
        frames.append(item);pos+=consumed
    except Exception:pos+=4
(out/'embedded-frames.json').write_text(json.dumps(frames,indent=2))
print('Frames',len(frames),flush=True)
