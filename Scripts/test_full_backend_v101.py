"""Synthetic end-to-end fault tests of the compiled installer (no game input)."""
from pathlib import Path
import sys, json, struct, gzip, hashlib, subprocess, shutil, ctypes, os, uuid

R=Path(__file__).resolve().parents[1]
W=R/'Build'/('FullBackend-Tests-'+uuid.uuid4().hex)
P=W/'package';(P/'Support/Patches').mkdir(parents=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
old=b'synthetic original executable'; new=b'synthetic translated executable'; prior=b'synthetic v1.0.0 executable'
packed=gzip.compress(b'URKRDP1\0'+struct.pack('<7q',len(old),len(new),24,0,0,len(new),0)+new,mtime=0)
(P/'Support/Patches/test.krpatch.gz').write_bytes(packed)
spec={'relative':'UnleashedRecomp.exe','originalSha256':sha(old),'patchedSha256':sha(new),'originalLength':len(old),'patchedLength':len(new),'patch':'Support/Patches/test.krpatch.gz','patchSha256':sha(packed),'previousPatchedSha256':[sha(prior)]}
manifest={'schemaVersion':2,'version':'1.0.1-test','scope':'native-exe','files':[spec]}
(P/'Support/manifest.json').write_text(json.dumps(manifest),encoding='utf8')
setup=P/'KoreanFullSetup.exe'
cmd=['C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe','/nologo','/target:winexe','/platform:x64','/define:TEST_FAULTS',
     '/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll','/reference:System.Web.Extensions.dll',
     '/resource:'+str(P/'Support/manifest.json')+',KoreanFullManifest','/out:'+str(setup),
     str(R/'Scripts/KoreanSupportSetup.cs'),str(R/'Scripts/KoreanSupportEngine.cs')]
subprocess.run(cmd,check=True)
valid=b'\xef\xbb\xbf[System]\r\nLanguage = "Japanese" # original\r\nVoiceLanguage = "Japanese"\r\nSubtitles = false\r\n[Video]\r\nWidth = 1920\r\n'
checks=[]
def fixture(name,config=valid,exe=old):
    g=W/name;g.mkdir();(g/'UnleashedRecomp.exe').write_bytes(exe);(g/'portable.txt').write_bytes(b'')
    if config is not None:(g/'config.toml').write_bytes(config)
    (g/'patched').mkdir();(g/'patched/default.xex').write_bytes(b'arbitrary unsupported XEX variant must be untouched')
    (g/'mods').mkdir();(g/'mods/ModsDB.ini').write_bytes(b'other enabled mods');(g/'save').mkdir();(g/'save/SYS-DATA').write_bytes(b'save sentinel')
    return g
def run(g,action='install',ok=True,env=None,package=P,selection=None):
    log=W/(uuid.uuid4().hex+'.log')
    result=subprocess.run([str(setup),'--'+action,str(selection or g),str(log),str(package)],env={**os.environ,**(env or {})},creationflags=subprocess.CREATE_NO_WINDOW)
    text=log.read_text(encoding='utf8') if log.exists() else ''
    assert (result.returncode==0)==ok,(result.returncode,text)
    return text
def snap(g):return {p.relative_to(g).as_posix():sha(p.read_bytes()) for p in g.rglob('*') if p.is_file()}
def unchanged(g,before):assert snap(g)==before
def reject(name,config,phrase):
    g=fixture(name,config);before=snap(g);text=run(g,ok=False);assert phrase in text,text;unchanged(g,before);checks.append(name)
reject('no-config',None,'초기 설정을 완료한 뒤 게임을 종료')
reject('missing-language',valid.replace(b'Language = "Japanese" # original\r\n',b''),'Language 항목이 없거나')
reject('missing-subtitles',valid.replace(b'Subtitles = false\r\n',b''),'Subtitles 항목이 없거나')
reject('duplicate-key',valid.replace(b'[Video]',b'Language = "English"\r\n[Video]'),'중복')
reject('invalid-value',valid.replace(b'Subtitles = false',b'Subtitles = broken'),'값이 예상과 다릅니다')
reject('wrong-section',valid.replace(b'[System]',b'[Other]'),'Language 항목이 없거나')
g=fixture('missing-exe');(g/'UnleashedRecomp.exe').unlink();before=snap(g);assert '선택한 게임 폴더에서' in run(g,ok=False);unchanged(g,before);checks.append('missing-exe')
g=fixture('unknown-exe',exe=b'unknown');before=snap(g);assert 'SHA-256' in run(g,ok=False);unchanged(g,before);checks.append('unknown-exe')
g=fixture('normal');before=snap(g);run(g,selection=g/'UnleashedRecomp.exe');assert (g/'UnleashedRecomp.exe').read_bytes()==new
backup=g/'korean-native-backup/Original/UnleashedRecomp.exe';assert backup.read_bytes()==old
run(g);assert backup.read_bytes()==old
(g/'config.toml').write_bytes(valid.replace(b'1920',b'2560'));later=(g/'config.toml').read_bytes()
run(g,'restore',package=W/'absent-package');assert (g/'UnleashedRecomp.exe').read_bytes()==old and (g/'config.toml').read_bytes()==later
for rel,digest in before.items():
    if rel not in ('UnleashedRecomp.exe','config.toml'):assert sha((g/rel).read_bytes())==digest
checks.append('install-reinstall-restore-config-voice-mods-save-XEX-preserved')
run(g);(g/'config.toml').unlink();run(g,'restore');checks.append('restore-without-config-or-package')
g=fixture('v100-upgrade',exe=prior);backup=g/'korean-native-backup/Original/UnleashedRecomp.exe';backup.parent.mkdir(parents=True);backup.write_bytes(old)
(g/'korean-native-backup/state.json').write_text('{"gameRoot":"old location","files":[{"relative":"patched/default.xex"}]}')
before=snap(g);assert '이전 Full판 설치 도구' in run(g,ok=False);unchanged(g,before)
assert '이전 Full판 설치 도구' in run(g,'restore',ok=False);unchanged(g,before)
# Simulate complete old-edition restoration; the real-binary suite uses the old tool.
(g/'UnleashedRecomp.exe').write_bytes(old)
run(g);run(g,'restore');checks.append('v100-requires-old-restore-before-upgrade')
g=fixture('moved-game');run(g);moved=W/'moved-game-new';g.rename(moved);run(moved,'restore');checks.append('moved-game-restore')
g=fixture('patched-no-backup',exe=new);before=snap(g);assert '원본 백업' in run(g,ok=False);unchanged(g,before);checks.append('patched-no-backup')
g=fixture('corrupt-backup');backup=g/'korean-native-backup/Original/UnleashedRecomp.exe';backup.parent.mkdir(parents=True);backup.write_bytes(b'corrupt');before=snap(g);assert '백업 검증 실패' in run(g,ok=False);unchanged(g,before);checks.append('corrupt-backup')
g=fixture('other-mod-after-install');run(g);(g/'UnleashedRecomp.exe').write_bytes(b'other patch');before=snap(g);run(g,'restore',ok=False);unchanged(g,before);checks.append('other-mod-restore-refused')
for name,file in [('bad-manifest','Support/manifest.json'),('bad-delta','Support/Patches/test.krpatch.gz')]:
    bad=W/name;shutil.copytree(P,bad);(bad/file).write_bytes(b'corrupt');g=fixture(name+'-game');before=snap(g);run(g,ok=False,package=bad);unchanged(g,before);checks.append(name)
for point in ('backup','staged','before-swap','after-swap','verified'):
    g=fixture('fail-'+point);run(g,ok=False,env={'URKR_TEST_FAIL':point});assert (g/'UnleashedRecomp.exe').read_bytes()==old
    assert (g/'config.toml').read_bytes()==valid
    run(g);run(g,'restore');checks.append('rollback-and-retry-'+point)
for point in ('backup','staged','after-swap','verified'):
    g=fixture('crash-'+point);run(g,ok=False,env={'URKR_TEST_CRASH':point});run(g,'restore',package=W/'missing');assert (g/'UnleashedRecomp.exe').read_bytes()==old;checks.append('process-crash-recovery-'+point)
for point in ('backup','staged','before-swap','after-swap','verified'):
    g=fixture('restore-fail-'+point);run(g)
    run(g,'restore',ok=False,env={'URKR_TEST_FAIL':point})
    assert (g/'UnleashedRecomp.exe').read_bytes()==new and (g/'config.toml').read_bytes()==valid
    run(g,'restore');assert (g/'UnleashedRecomp.exe').read_bytes()==old
    checks.append('restore-rollback-and-retry-'+point)
g=fixture('restore-crash');run(g);run(g,'restore',ok=False,env={'URKR_TEST_CRASH':'after-swap'});run(g,'restore');assert (g/'UnleashedRecomp.exe').read_bytes()==old;checks.append('restore-crash-recovery')
g=fixture('tampered-state');d=g/'korean-native-backup';d.mkdir();(d/'state.json').write_text('{"gameRoot":"elsewhere","files":[{"relative":"../save/SYS-DATA"}]}');before=snap(g)
run(g);run(g,'restore')
for rel,h in before.items():assert sha((g/rel).read_bytes())==h
checks.append('mutable-legacy-state-never-authorizes-writes')
g=fixture('hardlink');(g/'UnleashedRecomp.exe').unlink();os.link(W/'normal/UnleashedRecomp.exe',g/'UnleashedRecomp.exe');before=snap(g);assert '하드 링크' in run(g,ok=False);unchanged(g,before);checks.append('hardlink-refused')
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.restype=ctypes.c_void_p;k.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
k.CloseHandle.argtypes=[ctypes.c_void_p]
g=fixture('locked-exe');before=snap(g);handle=k.CreateFileW(str(g/'UnleashedRecomp.exe'),0x80000000,0,None,3,0,None);assert handle!=ctypes.c_void_p(-1).value
try:run(g,ok=False)
finally:k.CloseHandle(handle)
unchanged(g,before);checks.append('locked-exe-no-writes')
g=fixture('concurrent');before=snap(g);key=sha(str(g).upper().encode())
k.CreateMutexW.restype=ctypes.c_void_p;k.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p]
k.ReleaseMutex.argtypes=[ctypes.c_void_p]
handle=k.CreateMutexW(None,True,'Local\\UnleashedKoreanFull-'+key);assert handle
try:assert '다른 Full 설치 도구' in run(g,ok=False)
finally:k.ReleaseMutex(handle);k.CloseHandle(handle)
unchanged(g,before);checks.append('concurrent-installer-refused')
g=fixture('diagnosis');before=snap(g);assert '읽기 전용 진단' in run(g,'diagnose');unchanged(g,before);checks.append('read-only-diagnosis')
# A direct path probe does not read the real AppData configuration.
probe=W/'PathProbe.cs';probe.write_text('''using System; public class PathProbe { public static int Main(string[] args) {
string actual=SupportEngine.ResolveConfigPath(args[0]);
string expected=System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),"UnleashedRecomp","config.toml");
return actual==expected ? 0 : 1; } }''')
probe_exe=W/'PathProbe.exe'
subprocess.run([cmd[0],'/nologo','/target:exe','/main:PathProbe','/reference:System.Web.Extensions.dll','/out:'+str(probe_exe),str(probe),str(R/'Scripts/KoreanSupportEngine.cs')],check=True)
(g/'portable.txt').unlink();subprocess.run([str(probe_exe),str(g)],check=True)
checks.append('nonportable-config-path-ignores-stale-root-config')
report={'passed':True,'checks':checks,'count':len(checks),'actual_game_launched':False}
(W/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2));print(W)
