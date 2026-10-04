"""Prepare a new v1.0.6 staging tree from the verified v1.0.5 Full ZIP.
Never edit an installed game. Requires private prior ZIP and asset-free record.
"""
import argparse, hashlib, json, subprocess, zipfile
from pathlib import Path
SHA='8065c839b859d3df7ef8e48db98a2b2be552f12daf5923d90b99f11124748bf1'
def main():
    p=argparse.ArgumentParser()
    for name in ('prior_zip','prior_record','staging','record'):p.add_argument(name,type=Path)
    a=p.parse_args();source=Path(__file__).resolve().parents[1]
    assert hashlib.sha256(a.prior_zip.read_bytes()).hexdigest()==SHA,'Unexpected prior release'
    assert not a.staging.exists(),'Preserve existing staging'
    with zipfile.ZipFile(a.prior_zip) as z:
        assert z.testzip() is None
        for n in z.namelist():
            assert n.startswith('UnleashedKorean/') and '..' not in Path(n).parts and '\\' not in n
            rel=n[len('UnleashedKorean/'):]
            if not rel or n.endswith('/') or rel=='Source.zip':continue
            dest=a.staging/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(n))
    mpath=a.staging/'Support/manifest.json';m=json.loads(mpath.read_text(encoding='utf8'));m['version']='1.0.6'
    m['files'][0]['upgradePatchedSha256']=['18de8cedca10c5d0a3a5521c9f4a8795e06200ea2b07ea33ea0243081eca74fa']
    m['legacyXex']={'relative':'patched/default.xex','originalSha256':'8940eef6cdbf8585a58991fe5a7c7bfb4bc1b041c1628bc2757adcdd7a11b520','patchedSha256':'90ce58984e84753bb5719eaaddfc32377f6b8493787733f4a42223455ca0dd28','originalLength':21970944,'patchedLength':21970944}
    mpath.write_text(json.dumps(m,indent=2)+'\n',encoding='utf8')
    ini=a.staging/'mod.ini';text=ini.read_text(encoding='utf-8-sig');assert 'Version="1.0.5"' in text
    ini.write_text(text.replace('Version="1.0.5"','Version="1.0.6"'),encoding='utf8')
    for name in ('README-KO.md','README-EN.md','CHANGELOG-KO.md','TESTING-KO.md'):
        (a.staging/name).write_bytes((a.record.parent/name).read_bytes())
    compiler=Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe')
    subprocess.run([str(compiler),'/nologo','/target:winexe','/platform:x64',
        '/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll','/reference:System.Web.Extensions.dll',
        '/resource:'+str(mpath)+',KoreanFullManifest',
        '/resource:'+str(a.staging/'Support/InstallerLogo.png')+',UnleashedRecompiledLogo',
        '/out:'+str(a.staging/'KoreanFullSetup.exe'),str(source/'Scripts/KoreanSupportSetup_v106.cs'),str(source/'Scripts/KoreanSupportEngine.cs')],check=True)
    subprocess.run(['pwsh','-NoProfile','-File',str(source/'Scripts/Verify-InstallerManifest.ps1'),'-Installer',str(a.staging/'KoreanFullSetup.exe'),'-Manifest',str(mpath)],check=True)
    record=json.loads(a.prior_record.read_text(encoding='utf8'));record['version']='1.0.6'
    record['baseReleaseSha256']=SHA
    record['installerPayload']={rel:hashlib.sha256((a.staging/rel).read_bytes()).hexdigest() for rel in (*record['installerPayload'],'Support/manifest.json')}
    record['gameplayVerifiedByUser']=False
    record['gameplayConfigurationsInheritedFrom']='1.0.5; game assets and EXE delta unchanged; 1.0.6 installer tested on copies'
    a.record.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(a.staging)
if __name__=='__main__':main()
