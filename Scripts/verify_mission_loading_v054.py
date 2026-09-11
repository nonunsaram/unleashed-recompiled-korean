from pathlib import Path
import json,sys,ctypes,struct,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Tools/UIRuntime'))
import pefile
D=R/'Translation/review/mission-loading-v054'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
report=read(R/'Build/NativeUIWork/native-exe-report.json');g=report['mission_loading_patch']
patched=(R/'Build/Korean Full UI Playtest/Native/UnleashedRecomp.exe').read_bytes()
pe=pefile.PE(data=patched)
original=(R/'UnleashedRecomp-Windows/korean-mod-backup-v040/UnleashedRecomp.exe').read_bytes();op=pefile.PE(data=original)
reference=struct.pack('<I',g['original_resource_address']);new=struct.pack('<I',g['resource_address'])
positions=[];pos=0
while True:
    pos=original.find(reference,pos)
    if pos<0:break
    positions.append(op.get_rva_from_offset(pos));pos+=4
assert len(positions)==8
assert set(v for v in positions if g['function_rva']<=v<0x4ccb60)=={t+4 for t in g['calls']}
for rva in positions:assert pe.get_data(rva,4)==(new if rva-4 in g['calls'] else reference)
# Execute each patched instruction against a dummy emulated PPC register bank.
k=ctypes.WinDLL('kernel32');k.VirtualAlloc.restype=ctypes.c_void_p
k.VirtualAlloc.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_ulong,ctypes.c_ulong]
mem=k.VirtualAlloc(None,4096,0x3000,0x40);assert mem
for target in g['calls']:
    instruction=pe.get_data(target,8)
    assert instruction==bytes.fromhex('48c74610')+new
    code=bytes.fromhex('564889ce')+instruction+bytes.fromhex('5ec3')
    ctypes.memmove(mem,code,len(code));registers=(ctypes.c_uint64*4)(1,2,3,4)
    ctypes.WINFUNCTYPE(None,ctypes.c_void_p)(mem)(ctypes.addressof(registers))
    assert list(registers)==[1,2,0xffffffff00000000|g['resource_address'],4]
k.VirtualFree.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_ulong];k.VirtualFree(mem,0,0x8000)
xex=(R/'Build/Korean Full UI Playtest/Native/patched/default.xex').read_bytes()
headers=dict(struct.unpack_from('>II',xex,24+8*i) for i in range(struct.unpack_from('>I',xex,20)[0]))
assert struct.unpack_from('>H',xex,headers[0x3ff]+6)[0]==0 # LdrLoadModule copies the whole uncompressed image, including padding.
offset=0x4000+g['resource_address']-0x82000000
assert xex[offset:offset+15]==b'StageLoad_list\0'
assert xex[0x4000+g['original_resource_address']-0x82000000:][:15]==b'StageList_list\0'
wrapping=read(D/'wrapping.json');entries=wrapping['entries']
for e in entries:
    assert ' '.join(e['before'].split())==' '.join(e['after'].split())
    assert all(len(line)<=18 for line in e['after'].splitlines())
archives=read(D/'archive-verification.json');assert archives['passed'] and len(archives['archives'])==20
result={'passed':True,'loading_call_sites_executed':3,'other_stage_list_references_unchanged':5,'unique_objectives_and_descriptions':len(entries),'maximum_line_length_including_spaces':max(len(line) for e in entries for line in e['after'].splitlines()),'maximum_resulting_lines':max(len(e['after'].splitlines()) for e in entries),'wording_preserved':True,'archives_verified':20,'original_archive_files_unchanged':True,'physical_cells_verified':sum(a['verified_cells'] for a in archives['archives']),'physical_cells_rewrapped':sum(a['rewrapped_cells'] for a in archives['archives']),'game_runtime_test':'user playtest pending'}
(D/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
