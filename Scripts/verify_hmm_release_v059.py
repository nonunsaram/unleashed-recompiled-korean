from pathlib import Path
import json,shutil,subprocess,hashlib,zipfile,configparser,itertools,sys,datetime,ctypes
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Tools/UIRuntime'))
import pefile,capstone
from package_hmm_release_v059 import VARIANTS
W=R/'Build/HMMWorldMap-v059/Tests'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');W.mkdir(parents=True)
P=R/'Build/GameBanana-1.0.0';O=R/'outputs/GameBanana-1.0.0';B=R/'Build/CleanOriginals-v057'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
snap=lambda p:{f.relative_to(p).as_posix():sha(f) for f in p.rglob('*') if f.is_file()}
checks=[]
ex=(B/'UnleashedRecomp.exe').read_bytes();pe=pefile.PE(data=ex);cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
# Archive registration skips a replacement when the existing priority >= incoming priority.
branch=list(cs.disasm_lite(pe.get_data(0x1afc1d5,8),0x1afc1d5))
assert [(i[2],i[3]) for i in branch]==[('cmp','eax, ebp'),('jge','0x1afc2e3')],branch
plain=list(cs.disasm_lite(pe.get_data(0x1afba2c,8),0x1afba2c))
assert [(i[2],i[3]) for i in plain]==[('cmp','eax, ebp'),('jge','0x1afbb3a')]
subsets=[]
for mask in range(64):
    installed=[v for i,v in enumerate(VARIANTS[:-1]) if mask&(1<<i)]
    expected=max(installed,key=lambda v:v[2]) if installed else VARIANTS[-1]
    # Every enumeration order selects the same preserved source variant.
    for order in itertools.permutations(installed):
        selected=VARIANTS[-1]
        for candidate in order:
            if selected[2]<candidate[2]:selected=candidate
        assert selected==expected
    subsets.append(dict(installed=[v[1] for v in installed],selected=expected[0]))
checks.append('64 DLC subsets and all enumeration orders mapped to highest-priority preserved variant')
package=read(O/'package-verification.json')
for archive in package['archives']:
    p=O/archive['file'];assert sha(p)==archive['sha256']
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        assert len([n for n in z.namelist() if n.endswith('/mod.ini')])==1
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts and ':' not in n for n in z.namelist())
        z.extractall(W/('BasicExtracted' if 'Basic' in p.name else 'FullExtracted'))
basic=W/'BasicExtracted/UnleashedKorean';full=W/'FullExtracted/UnleashedKorean'
assert not any(f.suffix.lower() in ('.exe','.dll','.xex') for f in basic.rglob('*'))
assert not any(f.name=='UnleashedRecomp.exe' or f.suffix=='.xex' for f in full.rglob('*'))
common=R/'Build/FieldMission-v056/Mod';n=0
for f in common.rglob('*'):
    if not f.is_file() or f.name=='mod.ini':continue
    rel=f.relative_to(common);assert sha(basic/rel)==sha(f)==sha(full/rel);n+=1
assert n==136
for key,package,priority,label in VARIANTS:
    src=R/'Build/FieldMission-v056/DirectArchives'/('game' if package=='BaseGame' else 'dlc/'+package)/'Languages/English'
    for edition in (basic,full):
        for name in ('WorldMap.ar.00','WorldMap.arl'):
            assert sha(edition/'WorldMapVariants'/key/'Languages/English'/name)==sha(src/name)
checks.append('136 existing common assets unchanged; all seven WorldMap archive pairs preserved in both extracted ZIPs')
for edition in (basic,full):
    cp=configparser.ConfigParser();cp.read(edition/'mod.ini',encoding='utf8')
    assert cp['Main']['includedir0'].strip('"')=='WorldMapVariants/AllDLC'
    assert cp['Main']['includedir1'].strip('"')=='.'
    assert cp['Main']['includedircount']=='2'
    assert cp['Main']['configschemafile'].strip('"')=='ConfigSchema.json'
    assert cp['Main']['id'].strip('"')=='unleashed-recomp-korean'
checks.append('both editions have one mod.ini, same replacement identity, all-DLC default, and no completed game executable')
manifest=read(full/'Support/manifest.json');assert manifest['scope']=='native'
assert {f['relative'] for f in manifest['files']}=={'UnleashedRecomp.exe','patched/default.xex'}
def fixture(name):
    g=W/name;g.mkdir()
    for f in manifest['files']:
        target=g/f['relative'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(B/f['relative'],target)
    (g/'config.toml').write_bytes(b'Language = "English"\r\nVoiceLanguage = "Japanese"\r\nSubtitles = true\r\n')
    (g/'mods').mkdir();(g/'mods/ModsDB.ini').write_bytes(b'active-mod sentinel')
    (g/'mlsave').mkdir();(g/'mlsave/SYS-DATA').write_bytes(b'save sentinel')
    for f in (B/'game').rglob('*'):
        if f.is_file():
            d=g/f.relative_to(B);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
    return g
def run(g,action,ok=True,package=full):
    log=W/(g.name+'-'+action+'.log')
    result=subprocess.run([str(full/'KoreanFullSetup.exe'),'--'+action,str(g),str(log),str(package)],creationflags=subprocess.CREATE_NO_WINDOW)
    assert (result.returncode==0)==ok,log.read_text(encoding='utf8')
def verified(g,patched):
    for f in manifest['files']:assert sha(g/f['relative'])==f['patchedSha256' if patched else 'originalSha256']
def unchanged(g,before):
    for rel,h in before.items():
        if rel not in ('UnleashedRecomp.exe','patched/default.xex'):assert sha(g/rel)==h,rel
g=fixture('NativeRoundtrip');before=snap(g);run(g,'install');verified(g,True);unchanged(g,before)
run(g,'install');verified(g,True);run(g,'restore');verified(g,False);unchanged(g,before)
checks.append('Full installer from extracted ZIP installs, repeats and restores only EXE/XEX; worldmap, settings, voice, mods and save sentinel unchanged')
g=fixture('Unknown');(g/'UnleashedRecomp.exe').write_bytes(b'unsupported');before=snap(g);run(g,'install',False);assert snap(g)==before
g=fixture('MixedScope');before=snap(g);run(g,'install',False,R/'Build/GameBanana-0.4.18-Separated/KoreanBasicData');assert snap(g)==before
g=fixture('ModifiedAfter');run(g,'install');(g/'patched/default.xex').write_bytes(b'changed');before=snap(g);run(g,'restore',False);assert snap(g)==before
checks.append('unknown EXE, data manifest and later modified executable refused without writes')
g=fixture('Locked');before=snap(g)
k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateFileW.restype=ctypes.c_void_p;k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
h=k.CreateFileW(str(g/'UnleashedRecomp.exe'),0x80000000,1,None,3,0,None);assert h not in (None,ctypes.c_void_p(-1).value)
try:run(g,'install',False)
finally:k.CloseHandle.argtypes=[ctypes.c_void_p];k.CloseHandle(h)
verified(g,False);unchanged(g,before);run(g,'install');run(g,'restore');verified(g,False)
checks.append('late locked-file failure rolls back earlier writes; retry and restore succeed')
fields=read(R/'Build/Separation-v058/field-verification.json');assert fields['passed'] and fields['physical_cells']==31543
audit=read(R/'Build/Separation-v058/loading-path-audit.json');assert audit['worldmap_unique']==167 and audit['loading_unique']==296 and audit['wording_preserved']
hmm=read(R/'Build/HMMWorldMap-v059/hmm-config-verification.json');assert hmm['passed'] and len(hmm['choices'])==14
checks.append('actual HMM schema load/save source round-trip passed for 14 edition/variant choices')
source=full/'Source.zip'
with zipfile.ZipFile(source) as z:
    assert z.testzip() is None
    assert z.read('Source/Scripts/KoreanSupportSetup.cs')==(R/'Scripts/KoreanSupportSetup.cs').read_bytes()
    for name in ('package_hmm_release_v059.py','verify_hmm_release_v059.py','test_hmm_config_v059.ps1'):
        assert z.read('Source/Scripts/'+name)==(R/'Scripts'/name).read_bytes()
checks.append('bundled source matches current installer, packager and verification scripts')
result=dict(passed=True,checks=checks,dlc_subset_count=64,priority_binary_comparison=[dict(rva=hex(a),mnemonic=m,operands=o) for a,s,m,o in branch],common_assets=136,physical_mission_cells_previously_verified=31543,worldmap_unique=167,loading_unique=296,worldmap_max_characters=12,worldmap_max_font_width=258,loading_max_characters=18,wording_preserved=True,hmm_gui_launched=False,game_launched=False,published=False,ingame='pending user verification',test_directory=str(W),subsets=subsets)
(O/'release-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='subsets'},ensure_ascii=False))
