"""Recompile the v1.0.2 installer around the unchanged verified EXE delta."""
from pathlib import Path
import hashlib,json,shutil,subprocess

R=Path(__file__).resolve().parents[1]
OLD=R/'Build/FullBackend-v101/Package'
OUT=R/'Build/FullBackend-v102/Package'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    if OUT.exists():shutil.rmtree(OUT)
    support=OUT/'Support';patches=support/'Patches';patches.mkdir(parents=True)
    source_patch=OLD/'Support/Patches/exe-v103.krpatch.gz'
    shutil.copy2(source_patch,patches/source_patch.name)
    manifest=json.loads((OLD/'Support/manifest.json').read_text(encoding='utf8'))
    assert manifest['scope']=='native-exe' and len(manifest['files'])==1
    manifest['version']='1.0.2'
    assert sha(patches/source_patch.name)==manifest['files'][0]['patchSha256']
    (support/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    logo=R/'Assets/Installer/UnleashedRecompiledLogo.png'
    shutil.copy2(logo,support/'InstallerLogo.png')
    compiler=Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe')
    subprocess.run([str(compiler),'/nologo','/target:winexe','/platform:x64',
        '/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll','/reference:System.Web.Extensions.dll',
        '/resource:'+str(support/'manifest.json')+',KoreanFullManifest',
        '/resource:'+str(logo)+',UnleashedRecompiledLogo','/out:'+str(OUT/'KoreanFullSetup.exe'),
        str(R/'Scripts/KoreanSupportSetup_v102.cs'),str(R/'Scripts/KoreanSupportEngine.cs')],check=True)
    print(json.dumps({'version':manifest['version'],'setup_sha256':sha(OUT/'KoreanFullSetup.exe'),
        'patch_sha256':sha(patches/source_patch.name),'patched_exe_sha256':manifest['files'][0]['patchedSha256']},indent=2))

if __name__=='__main__':main()
