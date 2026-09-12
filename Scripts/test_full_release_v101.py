"""Real EXE/delta install tests in disposable folders; never launch or modify the game."""
from pathlib import Path
import argparse, json, hashlib, subprocess, shutil, uuid, os

R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main(package):
    package=Path(package).resolve();setup=package/'KoreanFullSetup.exe'
    manifest=json.loads((package/'Support/manifest.json').read_text())
    assert manifest['schemaVersion']==2 and manifest['scope']=='native-exe' and len(manifest['files'])==1
    spec=manifest['files'][0];assert spec['relative']=='UnleashedRecomp.exe'
    w=R/'Build'/('FullRelease-v101-Test-'+uuid.uuid4().hex);w.mkdir()
    clean=R/'Build/CleanOriginals-v057';legacy=R/'Build/GameBanana-1.0.0/Full/UnleashedKorean'
    checks=[]
    def fixture(name,xex=None):
        g=w/name;g.mkdir();shutil.copy2(clean/'UnleashedRecomp.exe',g/'UnleashedRecomp.exe')
        (g/'portable.txt').write_bytes(b'')
        (g/'config.toml').write_bytes(b'[System]\r\nLanguage = "English"\r\nVoiceLanguage = "Japanese"\r\nSubtitles = true\r\n')
        (g/'mods').mkdir();(g/'mods/ModsDB.ini').write_bytes(b'unchanged enabled mods')
        (g/'save').mkdir();(g/'save/SYS-DATA').write_bytes(b'unchanged save sentinel')
        if xex is not None:
            (g/'patched').mkdir();(g/'patched/default.xex').write_bytes(xex)
        return g
    def snapshot(g):return {p.relative_to(g).as_posix():sha(p) for p in g.rglob('*') if p.is_file()}
    def run(g,action='install',which=package,okay=True,env=None):
        log=w/(uuid.uuid4().hex+'.log')
        r=subprocess.run([str(which/'KoreanFullSetup.exe'),'--'+action,str(g),str(log),str(which)],env={**os.environ,**(env or {})},creationflags=subprocess.CREATE_NO_WINDOW)
        message=log.read_text(encoding='utf8');assert (r.returncode==0)==okay,message
        return message
    def preserved(g,before):
        for rel,digest in before.items():
            if rel!='UnleashedRecomp.exe':assert sha(g/rel)==digest,rel
    def passed(name):checks.append(name);print('PASS '+name,flush=True)
    # No XEX, arbitrary other variant, stock XEX, and legacy translated XEX all
    # remain outside the new installer's read/write contract.
    for name,xex in [('no-xex',None),('unrelated-xex',b'unknown variant sentinel'),('stock-xex',(clean/'patched/default.xex').read_bytes())]:
        g=fixture(name,xex);before=snapshot(g);run(g);assert sha(g/'UnleashedRecomp.exe')==spec['patchedSha256'];preserved(g,before)
        run(g,env={'URKR_TEST_FAIL':'after-swap','URKR_TEST_CRASH':'backup'}) # Production has no fault-injection hooks.
        run(g,'restore');assert sha(g/'UnleashedRecomp.exe')==spec['originalSha256'];preserved(g,before)
        assert sha(g/'korean-native-backup/Original/UnleashedRecomp.exe')==spec['originalSha256']
        passed(name+' install/reinstall/restore')
    g=fixture('legacy-upgrade',(clean/'patched/default.xex').read_bytes());before=snapshot(g)
    run(g,which=legacy)
    old_state=snapshot(g)
    assert '이전 Full판 설치 도구' in run(g,okay=False)
    assert snapshot(g)==old_state
    run(g,'restore',which=legacy)
    assert sha(g/'UnleashedRecomp.exe')==spec['originalSha256'];preserved(g,before)
    run(g);run(g,'restore');preserved(g,before)
    passed('v1.0.0 install -> guarded upgrade -> old full restore -> v1.0.1 install/restore')
    g=fixture('portable-restorer');run(g)
    standalone=w/'standalone';standalone.mkdir();shutil.copy2(setup,standalone/'KoreanFullSetup.exe')
    (g/'config.toml').unlink();run(g,'restore',which=standalone)
    assert sha(g/'UnleashedRecomp.exe')==spec['originalSha256'];passed('standalone restore without Support/config')
    # Confirm a rejected manifest cannot authorize a different output.
    bad=w/'corrupt-package';shutil.copytree(package,bad)
    (bad/'Support/manifest.json').write_text('{}')
    g=fixture('bad-package');before=snapshot(g);run(g,which=bad,okay=False);assert snapshot(g)==before
    passed('production embedded-manifest mismatch no writes')
    report={'passed':True,'checks':checks,'setup_sha256':sha(setup),'game_exe_sha256':spec['patchedSha256'],'actual_game_launched':False}
    (w/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(w)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--package',default=str(R/'Build/FullBackend-v101/Package'))
    main(parser.parse_args().package)
