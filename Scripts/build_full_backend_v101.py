"""Build the EXE-only Full utility and delta in a new, private output directory."""
from pathlib import Path
import sys, json, hashlib, struct, bz2, gzip, subprocess, shutil

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'Tools/ReleaseRuntime'))
import bsdiff4

def build():
    out=R/'Build/FullBackend-v101/Package'
    support=out/'Support'; patches=support/'Patches';patches.mkdir(parents=True,exist_ok=True)
    old=(R/'Build/CleanOriginals-v057/UnleashedRecomp.exe').read_bytes()
    new=(R/'Build/FullBackend-v101/Native/UnleashedRecomp.exe').read_bytes()
    sha=lambda b:hashlib.sha256(b).hexdigest()
    assert sha(old)=='b22c40e97510a122476028d0462bc6dbc93abb124431e39680ae8dd463eba687'
    report=json.loads((out.parent/'native-report.json').read_text())
    assert sha(new)==report['patched_sha256'] and report['native_dispatch_test']['passed']
    delta=bsdiff4.diff(old,new)
    assert bsdiff4.patch(old,delta)==new
    def number(b):
        n=int.from_bytes(b,'little');return -(n&0x7fffffffffffffff) if n>>63 else n
    nc=number(delta[8:16]);nd=number(delta[16:24])
    controls=bz2.decompress(delta[32:32+nc]);diff=bz2.decompress(delta[32+nc:32+nc+nd]);extra=bz2.decompress(delta[32+nc+nd:])
    controls=b''.join(struct.pack('<q',number(controls[i:i+8])) for i in range(0,len(controls),8))
    packed=gzip.compress(b'URKRDP1\0'+struct.pack('<4q',len(old),len(new),len(controls),len(diff))+controls+diff+extra,mtime=0)
    (patches/'exe-v103.krpatch.gz').write_bytes(packed)
    manifest={'schemaVersion':2,'version':'1.0.1','gameVersion':'Unleashed Recompiled v1.0.3 Windows x64','scope':'native-exe','files':[{
        'relative':'UnleashedRecomp.exe','originalSha256':sha(old),'patchedSha256':sha(new),
        'previousPatchedSha256':[report['source_sha256']],
        'originalLength':len(old),'patchedLength':len(new),'patch':'Support/Patches/exe-v103.krpatch.gz','patchSha256':sha(packed)}]}
    (support/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    compiler=Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe')
    logo=R/'Assets/Installer/UnleashedRecompiledLogo.png'
    subprocess.run([str(compiler),'/nologo','/target:winexe','/platform:x64',
        '/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll','/reference:System.Web.Extensions.dll',
        '/resource:'+str(support/'manifest.json')+',KoreanFullManifest',
        '/resource:'+str(logo)+',UnleashedRecompiledLogo','/out:'+str(out/'KoreanFullSetup.exe'),
        str(R/'Scripts/KoreanSupportSetup.cs'),str(R/'Scripts/KoreanSupportEngine.cs')],check=True)
    shutil.copy2(logo,support/'InstallerLogo.png')
    print(json.dumps({'output':str(out),'exe_sha256':sha(new),'setup_sha256':sha((out/'KoreanFullSetup.exe').read_bytes()),'patch_bytes':len(packed)}))

if __name__=='__main__':build()
