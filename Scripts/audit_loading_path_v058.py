from pathlib import Path
import json,hashlib,struct,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Tools/UIRuntime'))
import pefile,capstone
G=R/'UnleashedRecomp-Windows';B=R/'Build/CleanOriginals-v057';D=R/'Build/Separation-v058'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
xex=(B/'patched/default.xex').read_bytes();exe=(B/'UnleashedRecomp.exe').read_bytes();pe=pefile.PE(data=exe)
off=xex.index(b'StageList_list\0');addr=off-0x4000+0x82000000
ref=struct.pack('<I',addr);positions=[];i=0
while True:
    i=exe.find(ref,i)
    if i<0:break
    positions.append(pe.get_rva_from_offset(i));i+=4
assert len(positions)==8
loading=[p for p in positions if 0x4cb490<=p<0x4ccb60];assert len(loading)==3
dis=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
instructions=[dict(rva=hex(p-4),instructions=[x.mnemonic+' '+x.op_str for x in dis.disasm(pe.get_data(p-4,8),p-4)]) for p in loading]
patched=(R/'Build/FieldMission-v056/Native/UnleashedRecomp.exe').read_bytes();pp=pefile.PE(data=patched)
assert all(pp.get_data(p,4)==ref for p in positions),'Optional EXE still redirects loading'
inp=json.loads((R/'Build/PlayableModWork/mission-fields-v056-input.json').read_text(encoding='utf8'))
atlas=json.loads((R/'Build/PlayableModWork/common-atlas.json').read_text(encoding='utf8'));width={v['character']:v['rect'][2]-v['rect'][0] for v in atlas}
unique={};indices=set()
for g in inp:
    for r in g['rows']:
        if r['cell'] not in ('Worldmap','Explanation','Hint') or not r['korean']:continue
        unique[(r['translation_key'],r['cell'])]=r
        if r['cell']=='Worldmap':indices.add(r['cell_index'])
world=[r for r in unique.values() if r['cell']=='Worldmap'];load=[r for r in unique.values() if r['cell']!='Worldmap']
assert len(world)==167 and len(load)==296
assert all(len(line)<=12 and sum(width[c] for c in line)<=260 for r in world for line in r['korean'].splitlines())
assert all(len(line)<=18 for r in load for line in r['korean'].splitlines())
assert all(len(r['korean'].splitlines())<=3 for r in unique.values())
prior=json.loads((R/'Build/PlayableModWork/common-input.json').read_text(encoding='utf8'))
before={r['line_id']:r for g in prior for r in g['rows']}
assert all(' '.join(r['korean'].split())==' '.join(before[r['line_id']]['korean'].split()) for r in unique.values())
manifest=json.loads((R/'Build/GameBanana-0.4.18-Separated/KoreanBasicData/Support/manifest.json').read_text())
files=[]
for f in manifest['files']:
    assert sha(B/f['relative'])==f['originalSha256']
    assert sha(R/'Build/FieldMission-v056/DirectArchives'/f['relative'])==f['patchedSha256']
    files.append(dict(relative=f['relative'],current=sha(G/f['relative']),clean=f['originalSha256'],target=f['patchedSha256']))
mod=G/'mods/KoreanFullUITranslation';mismatches=[];matched=0
for f in (R/'Build/FieldMission-v056/Mod').rglob('*'):
    if not f.is_file() or f.name=='mod.ini':continue
    p=mod/f.relative_to(R/'Build/FieldMission-v056/Mod')
    if not p.exists() or sha(f)!=sha(p):mismatches.append(str(p))
    else:matched+=1
assert not mismatches,mismatches
overrides=[str(p.relative_to(mod)) for p in mod.rglob('*') if 'worldmap' in p.name.lower()]
assert not overrides,overrides
result=dict(original_exe_sha256=sha(B/'UnleashedRecomp.exe'),current_exe_sha256=sha(G/'UnleashedRecomp.exe'),current_xex_sha256=sha(G/'patched/default.xex'),stage_list_address=hex(addr),stage_list_xex_offset=hex(off),original_loading_references=instructions,other_stage_list_references=5,optional_exe_preserves_all_eight_references=True,worldmap_unique=167,loading_unique=296,worldmap_cell_indices=sorted(indices),worldmap_max_width=max(sum(width[c] for c in l) for r in world for l in r['korean'].splitlines()),wording_preserved=True,active_mod_assets_matched=matched,worldmap_mod_overrides=overrides,files=files,game_launched=False,interpretation='Static binary and source inspection; no runtime file trace collected')
(D/'loading-path-audit.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='files'}))
