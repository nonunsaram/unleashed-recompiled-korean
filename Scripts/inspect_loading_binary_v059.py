from pathlib import Path
import struct,sys,json,bisect
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Tools/UIRuntime'))
import pefile,capstone
W=R/'Build/HMMWorldMap-v059/Binary';W.mkdir(parents=True,exist_ok=True)
xe=(R/'Build/CleanOriginals-v057/patched/default.xex').read_bytes();ex=(R/'Build/CleanOriginals-v057/UnleashedRecomp.exe').read_bytes();pe=pefile.PE(data=ex)
funcs=pe.DIRECTORY_ENTRY_EXCEPTION;starts=[e.struct.BeginAddress for e in funcs]
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
report=[]
for name in ['DLC.xml','Priority','WorldMap','StageList_list','StageList','NameTag','Explanation','Worldmap','Hint']:
    raw=name.encode()+b'\0';off=0
    while True:
        off=xe.find(raw,off)
        if off<0:break
        if off>0x400000:break
        address=off-0x4000+0x82000000;needle=struct.pack('<I',address);j=0;refs=[]
        while True:
            j=ex.find(needle,j)
            if j<0:break
            try:rva=pe.get_rva_from_offset(j)
            except: j+=4;continue
            sec=pe.get_section_by_rva(rva)
            if sec and sec.IMAGE_SCN_MEM_EXECUTE:
                i=bisect.bisect_right(starts,rva)-1
                f=funcs[i].struct
                if f.BeginAddress<=rva<f.EndAddress:
                    refs.append(dict(rva=hex(rva),function=hex(f.BeginAddress)))
                    path=W/(hex(f.BeginAddress)+'.txt')
                    if not path.exists():
                        data=pe.get_data(f.BeginAddress,f.EndAddress-f.BeginAddress)
                        path.write_text('\n'.join(f'{a:08x}  {m} {o}' for a,s,m,o in cs.disasm_lite(data,f.BeginAddress)),encoding='utf8')
            j+=4
        report.append(dict(string=name,guest=hex(address),refs=refs));off+=len(raw)
(W/'xrefs.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
