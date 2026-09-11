"""Exercise wrapper branches with controlled stand-ins for the game's allocator and constructor."""
from pathlib import Path
import sys,json,ctypes,struct
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Tools/UIRuntime'))
import pefile
from keystone import Ks,KS_ARCH_X86,KS_MODE_64
W=R/'Build/NativeUIWork';report=json.loads((W/'native-exe-report.json').read_text());pe=pefile.PE(str(R/'Build/Korean Full UI Playtest/Native/UnleashedRecomp.exe'))
ks=Ks(KS_ARCH_X86,KS_MODE_64);k=ctypes.WinDLL('kernel32');k.VirtualAlloc.restype=ctypes.c_void_p;k.VirtualAlloc.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_ulong,ctypes.c_ulong]
mem=k.VirtualAlloc(None,pe.OPTIONAL_HEADER.SizeOfImage+65536,0x3000,0x40);assert mem
section=pe.sections[-1];ctypes.memmove(mem+section.VirtualAddress,section.get_data(),section.SizeOfRawData)
def code(rva,text):
 b=bytes(ks.asm(text,rva)[0]);ctypes.memmove(mem+rva,b,len(b))
scratch=mem+pe.OPTIONAL_HEADER.SizeOfImage;free_log=scratch+512
code(0x2998adc,f'mov rax,{free_log}; mov [rax],rcx; mov [rax+8],rdx; ret')
code(0xcbf90,'mov rax,rcx; mov [rcx],rdx; xor r8d,r8d; count: cmp byte ptr [rdx+r8],0; je done; inc r8; jmp count; done: mov [rcx+16],r8; mov qword ptr [rcx+24],32; ret')
cases=0
for hook in report['hooks']:
 code(hook['trampoline'],'mov rax,rdx; ret')
 fn=ctypes.WINFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p)(mem+hook['wrapper'])
 for english,expected,capacity in [('Select','확인',15),('Master Volume','전체 음량',31),('Untranslated sentinel','Untranslated sentinel',31),('Select','확인',5000)]:
  obj=ctypes.create_string_buffer(32);e=ctypes.create_string_buffer(len(english)+64);ep=ctypes.addressof(e)+16;ctypes.memmove(ep,english.encode()+b'\0',len(english)+1)
  struct.pack_into('<Q',e,8,ctypes.addressof(e))
  if capacity<16:ctypes.memmove(obj,english.encode()+b'\0',len(english)+1)
  else:struct.pack_into('<Q',obj,0,ep)
  struct.pack_into('<QQ',obj,16,len(english),capacity);ctypes.memset(free_log,0,16)
  ptr=fn(None,ctypes.addressof(obj));ln=ctypes.c_uint64.from_address(ptr+16).value;cap=ctypes.c_uint64.from_address(ptr+24).value
  p=ctypes.c_uint64.from_address(ptr).value if cap>=16 else ptr
  assert ctypes.string_at(p,ln).decode()==expected
  freed=ctypes.c_uint64.from_address(free_log).value
  should_free=hook['owned'] and expected!=english and capacity>=16
  assert bool(freed)==should_free
  if should_free:
   assert freed==(ctypes.addressof(e) if capacity>=4095 else ep)
   assert ctypes.c_uint64.from_address(free_log+8).value==capacity+1+(39 if capacity>=4095 else 0)
  cases+=1
vt=json.loads((W/'config-vtables.json').read_text())
language=next(v for v in vt if v['type']=='.?AV?$ConfigDef@W4ELanguage@@$0A@@@')
voice=next(v for v in vt if v['type']=='.?AV?$ConfigDef@W4EVoiceLanguage@@$0A@@@')
h=next(h for h in report['hooks'] if h['target']==language['functions'][10])
fn=ctypes.WINFUNCTYPE(ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p)(mem+h['wrapper'])
context_cases=0
for v in (language,voice):
 for english in ('ENGLISH','JAPANESE','Untranslated sentinel'):
  for capacity in (15,31):
   if len(english)>15 and capacity==15:continue
   expected='한국어' if v is language and english=='ENGLISH' else '영어' if english=='ENGLISH' else '일본어' if english=='JAPANESE' else english
   context=ctypes.c_uint64(mem+v['rva']);obj=ctypes.create_string_buffer(32);payload=ctypes.create_string_buffer(english.encode())
   if capacity==15:ctypes.memmove(obj,english.encode()+b'\0',len(english)+1)
   else:struct.pack_into('<Q',obj,0,ctypes.addressof(payload))
   struct.pack_into('<QQ',obj,16,len(english),capacity)
   ptr=fn(ctypes.byref(context),ctypes.addressof(obj));ln=ctypes.c_uint64.from_address(ptr+16).value;cap=ctypes.c_uint64.from_address(ptr+24).value
   data=ctypes.c_uint64.from_address(ptr).value if cap>=16 else ptr
   assert ctypes.string_at(data,ln).decode()==expected,(v['type'],english)
   context_cases+=1
k.VirtualFree.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_ulong];k.VirtualFree(mem,0,0x8000)
(W/'wrapper-test-report.json').write_text(json.dumps({'cases':cases,'language_context_cases':context_cases,'passed':True,'scope':'isolated wrapper control flow, SSO/heap/aligned heap/untranslated paths and text/voice language isolation; not game runtime'},indent=2));print('Passed wrapper cases:',cases,'language context:',context_cases)
