from pathlib import Path
import sys,struct,re,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Tools/UIRuntime'))
import pefile,capstone
d=(R/'UnleashedRecomp-Windows/UnleashedRecomp.exe').read_bytes();p=pefile.PE(data=d);base=p.OPTIONAL_HEADER.ImageBase
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
def dis(rva,n=160):return list(cs.disasm_lite(d[p.get_offset_from_rva(rva):p.get_offset_from_rva(rva)+n],rva))
vtables=[]
for m in re.finditer(rb'\.\?AV\?\$ConfigDef@[^\0]+\0',d):
    td=m.start()-16;tdrva=p.get_rva_from_offset(td);start=0
    while True:
        off=d.find(struct.pack('<I',tdrva),start)
        if off<0:break
        start=off+4;col=off-12
        if col<0:continue
        h=struct.unpack_from('<6I',d,col)
        if h[0]!=1 or h[1]!=0 or h[5]!=p.get_rva_from_offset(col):continue
        colva=base+p.get_rva_from_offset(col);vref=d.find(struct.pack('<Q',colva))
        if vref<0:continue
        funcs=[struct.unpack_from('<Q',d,vref+8+i*8)[0]-base for i in range(16)]
        if not all(0<x<0x2ac9000 for x in funcs):continue
        vtables.append({'type':m[0].decode().strip('\0'),'rva':p.get_rva_from_offset(vref+8),'functions':funcs})
(R/'Build/NativeUIWork/config-vtables.json').write_text(json.dumps(vtables,indent=2))
print('Config vtables',len(vtables),flush=True)
samples={hex(a):dis(a,240) for a in [0xc74f0,0xcbf90]+([vtables[0]['functions'][i] for i in [6,7,10,11]] if vtables else [])}
(R/'Build/NativeUIWork/hook-disassembly.json').write_text(json.dumps(samples,indent=2))
for a,s in samples.items():print(a,s,flush=True)
