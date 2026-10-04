"""Real historical delta migration tests, exclusively in new disposable folders.
No game or historical installer is launched; a compiled helper materializes fixtures
from hash-verified original bytes and the archived deltas.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, uuid, zipfile
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('package',type=Path);p.add_argument('work',type=Path);a=p.parse_args()
    source=Path(__file__).resolve().parents[1];w=a.work/('real-v106-'+uuid.uuid4().hex);w.mkdir(parents=True)
    clean=a.project/'Build/CleanOriginals-v057';checks=[]
    m=json.loads((a.package/'Support/manifest.json').read_text(encoding='utf8'));spec=m['files'][0]
    assert sha(clean/'UnleashedRecomp.exe')==spec['originalSha256']
    assert sha(clean/'patched/default.xex')==m['legacyXex']['originalSha256']
    helper=w/'Fixture.cs';helper.write_text('''using System; using System.IO; using System.Reflection;
class Fixture { static int Main(string[] a) {
var spec=SupportEngine.Json.Deserialize<PatchFile>(File.ReadAllText(a[2]));
var original=File.ReadAllBytes(a[0]); if(SupportEngine.Hash(original)!=spec.originalSha256)throw new Exception("original hash");
var packed=File.ReadAllBytes(a[1]); if(SupportEngine.Hash(packed)!=spec.patchSha256)throw new Exception("patch hash");
var method=typeof(SupportEngine).GetMethod("Apply",BindingFlags.Static|BindingFlags.NonPublic);
var bytes=(byte[])method.Invoke(null,new object[]{original,packed,spec});
if(SupportEngine.Hash(bytes)!=spec.patchedSha256)throw new Exception("output hash");File.WriteAllBytes(a[3],bytes);return 0;
}}''')
    exe=w/'Fixture.exe';subprocess.run(['C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe','/nologo','/target:exe','/reference:System.Web.Extensions.dll','/out:'+str(exe),str(helper),str(source/'Scripts/KoreanSupportEngine.cs')],check=True)
    fixtures={};fixture_hashes={}
    for version,folder in [('v100','GameBanana-1.0.0'),('early-v101','GameBanana-1.0.1'),('reviewed-v101','GameBanana-1.0.1-Reviewed')]:
        zpath=next((a.project/'outputs'/folder).glob('*Full.zip'));out=w/version;out.mkdir()
        with zipfile.ZipFile(zpath) as z:
            old=json.loads(z.read('UnleashedKorean/Support/manifest.json'))
            for f in old['files']:
                rel=f['relative'];dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True)
                patch=out/(Path(rel).name+'.gz');patch.write_bytes(z.read('UnleashedKorean/'+f['patch']))
                contract=out/(Path(rel).name+'.json');contract.write_text(json.dumps(f))
                subprocess.run([str(exe),str(clean/rel),str(patch),str(contract),str(dest)],check=True)
                assert sha(dest)==f['patchedSha256']
        fixtures[version]=out
        fixture_hashes[version]={'zipSha256':sha(zpath),'exeSha256':sha(out/'UnleashedRecomp.exe'),'exeBytes':(out/'UnleashedRecomp.exe').stat().st_size}
    def fixture(name,variant=None):
        g=w/name;g.mkdir();shutil.copy2((fixtures[variant] if variant else clean)/'UnleashedRecomp.exe',g/'UnleashedRecomp.exe')
        (g/'patched').mkdir();shutil.copy2((fixtures['v100'] if variant=='v100' else clean)/'patched/default.xex',g/'patched/default.xex')
        (g/'portable.txt').write_bytes(b'');(g/'config.toml').write_bytes(b'[System]\nLanguage = "English"\nVoiceLanguage = "Japanese"\nSubtitles = true\n')
        (g/'mods').mkdir();(g/'mods/ModsDB.ini').write_bytes(b'other mods preserved');(g/'save').mkdir();(g/'save/SYS-DATA').write_bytes(b'save preserved')
        if variant:
            for rel in ('UnleashedRecomp.exe','patched/default.xex'):
                dst=g/'korean-native-backup/Original'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(clean/rel,dst)
            (g/'korean-native-backup/state.json').write_text('{"files":[{"relative":"patched/default.xex"}]}')
        return g
    def snapshot(g):return {p.relative_to(g).as_posix():sha(p) for p in g.rglob('*') if p.is_file()}
    def run(g,action='install',package=a.package,ok=True):
        log=w/(uuid.uuid4().hex+'.log')
        r=subprocess.run([str(a.package/'KoreanFullSetup.exe'),'--'+action,str(g),str(log),str(package)],creationflags=subprocess.CREATE_NO_WINDOW)
        msg=log.read_text(encoding='utf8') if log.exists() else ''
        assert (r.returncode==0)==ok,msg
    def passed(name):checks.append(name);print('PASS '+name,flush=True)
    for variant in (None,*fixtures):
        g=fixture('roundtrip-'+str(variant),variant);before=snapshot(g)
        run(g);assert sha(g/'UnleashedRecomp.exe')==spec['patchedSha256'];assert sha(g/'patched/default.xex')==m['legacyXex']['originalSha256']
        run(g);run(g,'restore');assert sha(g/'UnleashedRecomp.exe')==spec['originalSha256']
        run(g);assert sha(g/'UnleashedRecomp.exe')==spec['patchedSha256']
        for rel,digest in before.items():
            if rel not in ('UnleashedRecomp.exe','patched/default.xex'):assert sha(g/rel)==digest,rel
        passed(str(variant)+' install/reapply/restore/reapply and sentinel preservation')
    g=fixture('v100-direct-restore','v100');run(g,'restore',w/'absent');assert sha(g/'UnleashedRecomp.exe')==spec['originalSha256'];assert sha(g/'patched/default.xex')==m['legacyXex']['originalSha256'];passed('v100 standalone EXE+XEX restore')
    for variant in fixtures:
        for bad in ('missing-backup','bad-backup','unknown-exe'):
            g=fixture(variant+'-'+bad,variant)
            target=g/('UnleashedRecomp.exe' if bad=='unknown-exe' else 'korean-native-backup/Original/UnleashedRecomp.exe')
            if bad=='missing-backup':target.unlink()
            else:target.write_bytes(b'unsupported')
            before=snapshot(g);run(g,ok=False);assert snapshot(g)==before;run(g,'restore',ok=False);assert snapshot(g)==before
            passed(variant+' '+bad+' no writes')
    for bad in ('missing','corrupt','unknown'):
        g=fixture('v100-xex-'+bad,'v100');target=g/('patched/default.xex' if bad=='unknown' else 'korean-native-backup/Original/patched/default.xex')
        if bad=='missing':target.unlink()
        else:target.write_bytes(b'unsupported XEX')
        before=snapshot(g);run(g,ok=False);assert snapshot(g)==before;run(g,'restore',ok=False);assert snapshot(g)==before;passed('v100 XEX '+bad+' no writes')
    for name,data in [('changed-version',(a.package/'Support/manifest.json').read_bytes().replace(b'1.0.6',b'1.0.7')),('whitespace',(a.package/'Support/manifest.json').read_bytes()+b' '),('invalid-json',b'{}')]:
        bad=w/name;(bad/'Support').mkdir(parents=True);(bad/'Support/manifest.json').write_bytes(data)
        g=fixture('game-'+name);before=snapshot(g);run(g,package=bad,ok=False);assert snapshot(g)==before
        result=subprocess.run(['pwsh','-NoProfile','-File',str(source/'Scripts/Verify-InstallerManifest.ps1'),'-Installer',str(a.package/'KoreanFullSetup.exe'),'-Manifest',str(bad/'Support/manifest.json')],capture_output=True)
        assert result.returncode!=0;passed('runtime and static manifest rejection '+name)
    report={'passed':True,'count':len(checks),'checks':checks,'historicalFixtures':fixture_hashes,'installerSha256':sha(a.package/'KoreanFullSetup.exe'),'actual_game_launched':False}
    (w/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(w)
if __name__=='__main__':main()
