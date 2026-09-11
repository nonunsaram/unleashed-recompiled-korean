from pathlib import Path
import sys,struct,json,hashlib,re,ctypes
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Tools/UIRuntime'))
import pefile,capstone
from keystone import Ks,KS_ARCH_X86,KS_MODE_64
W=R/'Build/NativeUIWork';O=R/'Build/Korean Full UI Playtest/Native'
original_path=R/'UnleashedRecomp-Windows/korean-mod-backup-v040/UnleashedRecomp.exe'
if not original_path.exists():original_path=R/'UnleashedRecomp-Windows/UnleashedRecomp.exe'
raw=original_path.read_bytes();original_hash=hashlib.sha256(raw).hexdigest()
assert original_hash=='b22c40e97510a122476028d0462bc6dbc93abb124431e39680ae8dd463eba687', 'Unsupported source executable'
pe=pefile.PE(data=raw);b=bytearray(raw);cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
ks=Ks(KS_ARCH_X86,KS_MODE_64)
align=lambda n,a:(n+a-1)//a*a
va=align(pe.sections[-1].VirtualAddress+pe.sections[-1].Misc_VirtualSize,pe.OPTIONAL_HEADER.SectionAlignment)
blob=bytearray();patches=[]
def add(data,a=16):
    blob.extend(bytes((-len(blob))%a));v=va+len(blob);blob.extend(data);return v
def asm(code,addr):return bytes(ks.asm(code,addr)[0])
def write(rva,data):
    off=pe.get_offset_from_rva(rva);before=bytes(b[off:off+len(data)]);b[off:off+len(data)]=data
    patches.append({'rva':rva,'before':before.hex(),'after':data.hex()})
rows=json.loads((R/'Translation/review/remaining-ui/native-ui-comparison.json').read_text(encoding='utf8'))
ko=json.loads((R/'Translation/native-ui-ko.json').read_text(encoding='utf8'));assert len(rows)==len(ko)==188
mapping={}
for row,k in zip(rows,ko):
    en=row['english']
    if not en or en==k:continue
    if en in mapping:assert mapping[en]==k
    mapping[en]=k
table=add(bytes(64*len(mapping)));entries=[]
for i,(en,k) in enumerate(mapping.items()):
    ev=add(en.encode()+b'\0',1);kv=add(k.encode()+b'\0',1);size=len(k.encode());off=table-va+i*64
    struct.pack_into('<4I',blob,off,ev-va,len(en.encode()),kv-va,size)
    struct.pack_into('<QQ',blob,off+32,size,max(size,16));entries.append((en,k,table+i*64+16))
# Only volatile registers are touched; the returned MSVC string object is immutable except its ASLR pointer.
helper=add(bytes(256));helper_code=asm(f'''
lea r8, [rip + {table-(helper+7)}]
mov r9d, {len(mapping)}
next_entry:
cmp edx, dword ptr [r8+4]
jne advance_entry
lea r10, [rip + base_label]
base_label:
sub r10, {0}
mov eax, dword ptr [r8]
lea r10, [rip + section_base]
add r10, rax
xor r11d, r11d
compare_char:
cmp r11, rdx
je found
mov al, byte ptr [rcx+r11]
cmp al, byte ptr [r10+r11]
jne advance_entry
inc r11
jmp compare_char
advance_entry:
add r8, 64
dec r9d
jnz next_entry
xor eax,eax
ret
found:
mov eax, dword ptr [r8+8]
lea r10, [rip + section_base]
add rax,r10
mov qword ptr [r8+16],rax
lea rax,[r8+16]
ret
section_base:
''',helper)
# Replace symbolic end-label references with actual section base, using instruction-level relocations.
hc=bytearray(helper_code)
for ins in cs.disasm(helper_code,helper):
    if ins.mnemonic=='lea' and 'rip' in ins.op_str and ins.address!=helper:
        # The first temporary lea is harmless but also resolves to the section base.
        struct.pack_into('<i',hc,ins.address-helper+ins.disp_offset,va-(ins.address+ins.size))
blob[helper-va:helper-va+len(hc)]=hc
hooks=[];unwinds=[]
vt=json.loads((W/'config-vtables.json').read_text())
language_vtable=next(v for v in vt if v['type']=='.?AV?$ConfigDef@W4ELanguage@@$0A@@@')
language_value_target=language_vtable['functions'][10]
english_object=next(obj for en,k,obj in entries if en=='ENGLISH' and k=='영어')
language_label=json.loads((R/'Translation/native-ui-display-overrides.json').read_text(encoding='utf8'))['text_language_english']
language_label_rva=add(language_label.encode()+b'\0',1)
def hook(target,owned):
    off=pe.get_offset_from_rva(target);insns=[];n=0
    for ins in cs.disasm(raw[off:off+32],target):
        assert not any(op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP for op in ins.operands)
        assert not ins.group(capstone.CS_GRP_JUMP) and not ins.group(capstone.CS_GRP_CALL)
        insns.append(ins);n+=ins.size
        if n>=5:break
    tramp=add(raw[off:off+n]+bytes(5));blob[tramp-va+n:tramp-va+n+5]=asm(f'jmp {target+n}',tramp+n)
    wrapper=add(bytes(256))
    if owned:
        code=f'''push rbx
push rsi
sub rsp, 0x28
call {tramp}
mov rbx,rax
mov rdx,[rax+16]
mov rcx,rax
cmp qword ptr [rax+24],16
jb owned_lookup
mov rcx,[rax]
owned_lookup:
call {helper}
test rax,rax
jz owned_done
mov rsi,[rax]
mov rdx,[rbx+24]
cmp rdx,16
jb construct
mov rcx,[rbx]
inc rdx
cmp rdx,4096
jb free_old
mov rcx,[rcx-8]
add rdx,39
free_old:
call 0x2998adc
construct:
mov rcx,rbx
mov rdx,rsi
call 0xcbf90
owned_done:
mov rax,rbx
add rsp,0x28
pop rsi
pop rbx
ret'''
        unwind=bytes([1,6,3,0,6,0x42,2,0x60,1,0x30,0,0])
    else:
        code=f'''push rbx
sub rsp,0x20
call {tramp}
mov rbx,rax
mov rdx,[rax+16]
mov rcx,rax
cmp qword ptr [rax+24],16
jb general_lookup
mov rcx,[rax]
general_lookup:
call {helper}
test rax,rax
cmovz rax,rbx
add rsp,0x20
pop rbx
ret'''
        unwind=bytes([1,5,2,0,5,0x32,1,0x30])
    if target==language_value_target:
        # Language and VoiceLanguage share this compiled method. Preserve the
        # object's vtable identity across the original call and change only
        # the English text-language display, never the English voice label.
        code=code.replace(f'call {tramp}',f'''xor eax,eax
test rcx,rcx
jz context_ready
mov rax,[rcx]
lea r10,[rip+0]
cmp rax,r10
sete al
context_ready:
mov byte ptr [rsp+0x20],al
call {tramp}''',1)
        code=code.replace('mov rsi,[rax]', '''mov rsi,[rax]
cmp byte ptr [rsp+0x20],0
je label_ready
lea r10,[rip+0]
cmp rax,r10
jne label_ready
lea rsi,[rip+0]
label_ready:''',1)
    enc=bytearray(asm(code,wrapper));assert len(enc)<=256
    if target==language_value_target:
        refs=[language_vtable['rva'],english_object,language_label_rva]
        for ins in cs.disasm(enc,wrapper):
            if ins.mnemonic=='lea' and 'rip' in ins.op_str:
                struct.pack_into('<i',enc,ins.address-wrapper+ins.disp_offset,refs.pop(0)-(ins.address+ins.size))
        assert not refs
    blob[wrapper-va:wrapper-va+len(enc)]=enc
    uv=add(unwind,4);unwinds.append((wrapper,wrapper+len(enc),uv))
    write(target,asm(f'jmp {wrapper}',target)+b'\x90'*(n-5));hooks.append({'target':target,'wrapper':wrapper,'trampoline':tramp,'bytes':n,'owned':owned})
hook(0xc74f0,False)
vt=json.loads((W/'config-vtables.json').read_text())
for t in sorted({v['functions'][i] for v in vt for i in [6,7,10,11]}):hook(t,True)
# 0.4.10: the Korean pause achievement guide already has a complete SDF fill.
# Suppress only its additional 127-alpha white pass; retain the 720p filtering,
# outline, layout, and every other button guide's original drawing behavior.
guide_target=0x14e5b2
assert raw[pe.get_offset_from_rva(guide_target):pe.get_offset_from_rva(guide_target)+9]==bytes.fromhex('4885db0f8489000000')
guide_wrapper=add(bytes(256))
guide_text='도전과제'.encode()+b'\0'
guide_code='test rbx,rbx\njz matched\n'
for j,v in enumerate(guide_text):guide_code+=f'cmp byte ptr [rbx+{j}],{v}\njne original\n'
guide_code+='matched:\njmp 0x14e644\noriginal:\njmp 0x14e5bb'
guide_bytes=asm(guide_code,guide_wrapper)
assert len(guide_bytes)<=256
blob[guide_wrapper-va:guide_wrapper-va+len(guide_bytes)]=guide_bytes
write(guide_target,asm(f'jmp {guide_wrapper}',guide_target)+b'\x90'*4)
# This block runs within DrawGuide's existing stack frame. Clone its full
# unwind operations with zero prologue offsets for correct asynchronous unwind.
guide_function=next(e for e in pe.DIRECTORY_ENTRY_EXCEPTION if e.struct.BeginAddress==0x14e170)
ui=guide_function.unwindinfo
unwind=bytearray(raw[pe.get_offset_from_rva(guide_function.struct.UnwindData):pe.get_offset_from_rva(guide_function.struct.UnwindData)+4+2*((ui.CountOfCodes+1)&~1)])
assert unwind[0]==1 and unwind[3]==0
unwind[1]=0
j=0
while j<unwind[2]:
    off=4+2*j;unwind[off]=0;op=unwind[off+1]&15;info=unwind[off+1]>>4
    j+= (2 if info==0 else 3) if op==1 else 2 if op in (4,8) else 3 if op in (5,9) else 1
assert j==unwind[2]
uv=add(unwind,4);unwinds.append((guide_wrapper,guide_wrapper+len(guide_bytes),uv))
guide_patch={'target':guide_target,'wrapper':guide_wrapper,'size':len(guide_bytes),'skip_target':0x14e644,'original_target':0x14e5bb,'text':'도전과제','scope':'only the extra low-quality white fill pass; base fill, outline, filtering and placement unchanged'}
# 0.4.11: avoid resampling this small Hangul label through the simulated
# 720p text grid. Draw at the user's actual resolution via the existing High
# path. The icon, glyph metrics, outline and all other labels stay unchanged.
quality_target=0x14e50d
assert raw[pe.get_offset_from_rva(quality_target):pe.get_offset_from_rva(quality_target)+5]==bytes.fromhex('4585f67444')
quality_wrapper=add(bytes(256))
quality_code='test rbx,rbx\njz original\n'
for j,v in enumerate(guide_text):quality_code+=f'cmp byte ptr [rbx+{j}],{v}\njne original\n'
quality_code+='jmp 0x14e512\noriginal:\ntest r14d,r14d\njz low\njmp 0x14e512\nlow:\njmp 0x14e556'
quality_bytes=asm(quality_code,quality_wrapper);assert len(quality_bytes)<=256
blob[quality_wrapper-va:quality_wrapper-va+len(quality_bytes)]=quality_bytes
write(quality_target,asm(f'jmp {quality_wrapper}',quality_target))
unwinds.append((quality_wrapper,quality_wrapper+len(quality_bytes),uv))
quality_patch={'target':quality_target,'wrapper':quality_wrapper,'size':len(quality_bytes),'high_target':0x14e512,'low_target':0x14e556,'text':'도전과제','scope':'native-resolution text only for the Korean achievement guide; other labels preserve the requested quality'}
# 0.4.13: tint only the Korean achievement button guide light gray.
color_target=0x14e546
assert raw[pe.get_offset_from_rva(color_target):pe.get_offset_from_rva(color_target)+6]==bytes.fromhex('41b9ffffffff')
color_wrapper=add(bytes(256))
color_code='mov r9d,0xffffffff\ntest rbx,rbx\njz original\n'
for j,v in enumerate(guide_text):color_code+=f'cmp byte ptr [rbx+{j}],{v}\njne original\n'
color_code+='mov r9d,0xffdce0e0\noriginal:\njmp 0x14e54c'
color_bytes=asm(color_code,color_wrapper);assert len(color_bytes)<=256
blob[color_wrapper-va:color_wrapper-va+len(color_bytes)]=color_bytes
write(color_target,asm(f'jmp {color_wrapper}',color_target)+b'\x90')
unwinds.append((color_wrapper,color_wrapper+len(color_bytes),uv))
color_patch={'target':color_target,'wrapper':color_wrapper,'size':len(color_bytes),'return_target':0x14e54c,'rgba':[224,224,220,255],'text':'도전과제'}
# 0.4.15: both screens use original StageList with explicit newline glyphs.
loading_patch={'resource':'StageList_list','shared_explicit_newlines':True,'calls':[]}
# Original resources stay in place; only verified references and lengths are updated.
snapshot=(W/'korean-font-snapshot.zst').read_bytes();texture=(W/'korean-font.zst').read_bytes()
sv=add(snapshot);tv=add(texture)
for inst,target,old in [(0xfa9f4,sv,53638368),(0xd0fa8,tv,53702528)]:
    off=pe.get_offset_from_rva(inst);assert inst+7+struct.unpack_from('<i',raw,off+3)[0]==old
    write(inst+3,struct.pack('<i',target-inst-7))
for loc,old,new in [(0xfa9f0,64147,len(snapshot)),(0xd0fa4,5679357,len(texture))]:
    assert struct.unpack_from('<I',raw,pe.get_offset_from_rva(loc))[0]==old;write(loc,struct.pack('<I',new))
size_rva=0xfa8b2+7+0x323c6bf
assert struct.unpack_from('<Q',raw,pe.get_offset_from_rva(size_rva))[0]==2143908
write(size_rva,struct.pack('<Q',(W/'korean-font-snapshot.bin').stat().st_size))
for loc in [0xd0e7e,0xd0e8c,0xd0fb5,0xd0fc7]:
    assert struct.unpack_from('<I',raw,pe.get_offset_from_rva(loc))[0]==16777364
    write(loc,struct.pack('<I',(W/'korean-font.dds').stat().st_size))
# Extend the exception table for wrapper stack unwinding.
ex=pe.OPTIONAL_HEADER.DATA_DIRECTORY[3];old_ex=raw[pe.get_offset_from_rva(ex.VirtualAddress):pe.get_offset_from_rva(ex.VirtualAddress)+ex.Size]
runtime=[struct.unpack_from('<3I',old_ex,i) for i in range(0,len(old_ex),12)]+unwinds
new_ex=b''.join(struct.pack('<3I',*v) for v in sorted(runtime));exva=add(new_ex,4)
struct.pack_into('<II',b,ex.get_file_offset(),exva,len(new_ex))
header=pe.sections[-1].get_file_offset()+40
assert header+40<=pe.OPTIONAL_HEADER.SizeOfHeaders and not any(b[header:header+40])
fileoff=align(len(b),pe.OPTIONAL_HEADER.FileAlignment);rawsize=align(len(blob),pe.OPTIONAL_HEADER.FileAlignment)
struct.pack_into('<8s6I2HI',b,header,b'.krui\0\0\0',len(blob),va,rawsize,fileoff,0,0,0,0,0xe0000060)
struct.pack_into('<H',b,pe.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),len(pe.sections)+1)
struct.pack_into('<I',b,pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),align(va+len(blob),pe.OPTIONAL_HEADER.SectionAlignment))
struct.pack_into('<I',b,pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfCode'),pe.OPTIONAL_HEADER.SizeOfCode+rawsize)
b.extend(bytes(fileoff-len(b)));b.extend(blob);b.extend(bytes(rawsize-len(blob)))
out=O/'UnleashedRecomp.exe';out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b)
check=pefile.PE(data=b);assert check.sections[-1].VirtualAddress==va
for h in hooks:
    i=next(cs.disasm(b[pe.get_offset_from_rva(h['target']):][:5],h['target']))
    assert i.mnemonic=='jmp' and i.operands[0].imm==h['wrapper']
# Execute the standalone lookup in this build process, without launching or controlling the game.
k32=ctypes.WinDLL('kernel32',use_last_error=True);k32.VirtualAlloc.restype=ctypes.c_void_p
k32.VirtualAlloc.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_ulong,ctypes.c_ulong]
mem=k32.VirtualAlloc(None,len(blob),0x3000,0x40);assert mem
ctypes.memmove(mem,bytes(blob),len(blob));fn=ctypes.WINFUNCTYPE(ctypes.c_void_p,ctypes.c_char_p,ctypes.c_size_t)(mem+helper-va)
for en,k,obj in entries:
    enb=en.encode();ptr=fn(enb,len(enb));assert ptr==mem+obj-va
    data=ctypes.c_void_p.from_address(ptr).value;ln=ctypes.c_uint64.from_address(ptr+16).value
    assert ctypes.string_at(data,ln).decode()==k
assert not fn(b'Untranslated sentinel',21)
k32.VirtualFree.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_ulong];k32.VirtualFree(mem,0,0x8000)
report={'original_exe_sha256':original_hash,'patched_exe_sha256':hashlib.sha256(b).hexdigest(),'translation_entries':len(mapping),'hooks':hooks,'section_rva':va,'patches':patches,'achievement_guide_patch':guide_patch,'achievement_guide_quality_patch':quality_patch,'achievement_guide_color_patch':color_patch,'mission_loading_patch':loading_patch,'standalone_lookup_verified':True,'game_runtime_test':'user playtest pending'}
(W/'native-exe-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('hooks','patches')}),flush=True)
