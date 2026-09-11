from pathlib import Path
import struct,sys,bisect,re,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Tools/UIRuntime'))
import pefile,capstone
W=R/'Build/HMMWorldMap-v059/Binary';W.mkdir(parents=True,exist_ok=True)
xe=(R/'Build/CleanOriginals-v057/patched/default.xex').read_bytes();ex=(R/'Build/CleanOriginals-v057/UnleashedRecomp.exe').read_bytes();pe=pefile.PE(data=ex)
funcs=pe.DIRECTORY_ENTRY_EXCEPTION;starts=[e.struct.BeginAddress for e in funcs]
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
def dump(rva):
    f=funcs[bisect.bisect_right(starts,rva)-1].struct
    out=[]
    for a,s,m,o in cs.disasm_lite(pe.get_data(f.BeginAddress,f.EndAddress-f.BeginAddress),f.BeginAddress):
        note=''
        for n in re.findall(r'0xffffffff(82[0-9a-f]{6})',o):
            off=int(n,16)-0x82000000+0x4000
            raw=xe[off:off+160].split(b'\0')[0]
            if raw and all(32<=v<=126 or v in (9,10,13) for v in raw):note+=' ; '+repr(raw.decode())
        out.append(f'{a:08x}  {m} {o}{note}')
    p=W/(hex(f.BeginAddress)+'-annotated.txt');p.write_text('\n'.join(out),encoding='utf8');return dict(function=hex(f.BeginAddress),path=str(p))
targets=[int(s,0) for s in sys.argv[1:]]
for t in targets:
    callers=[]
    for sec in pe.sections:
        if not sec.IMAGE_SCN_MEM_EXECUTE:continue
        b=sec.get_data();i=0
        while True:
            i=b.find(b'\xe8',i)
            if i<0 or i+5>len(b):break
            if sec.VirtualAddress+i+5+struct.unpack_from('<i',b,i+1)[0]==t:callers.append(sec.VirtualAddress+i)
            i+=1
    print(json.dumps(dict(target=dump(t),callers=[dict(call=hex(c),**dump(c)) for c in callers]),indent=2))
