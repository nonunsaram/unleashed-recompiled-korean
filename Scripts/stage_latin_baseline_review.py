"""Pack and round-trip the isolated review; optionally install with backups."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,re,os
from bounded_archive_tool import unpack
R=Path(__file__).resolve().parents[1];W=R/'Build/LatinBaseline-Audit'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',action='store_true');args=parser.parse_args()
    assert read(W/'fixed-verification.json')['passed'] and read(W/'metadata-verification.json')['passed']
    released={str(p):sha(p) for p in (R/'outputs/GameBanana-1.0.2').glob('*.zip')}
    originals={x['archive']:x for x in read(W/'archive-index.json') if x['version']=='v102'}
    out=W/'Packed';out.mkdir(exist_ok=True);results=[]
    for job in read(W/'fix-jobs.json'):
        original=Path(originals[job['archive']]['folder']);fixed=Path(job['folder'])
        # Renderer intermediates must never enter the mod archives.
        names={p.name for p in original.iterdir() if p.is_file()}
        changed=[]
        for name in names:
            p=fixed/name;assert p.is_file() and p.stat().st_size>0
            if sha(p)!=sha(original/name):
                assert p.suffix in ('.fco','.fte') or re.search(r'_\d{3}\.dds$',name),name
                changed.append(name)
        packedfolder=out/fixed.name
        packedfolder.mkdir(exist_ok=True)
        assert not ({p.name for p in packedfolder.iterdir()}-names)
        for name in names:shutil.copy2(fixed/name,packedfolder/name)
        subprocess.run([str(R/'Tools/HedgeArcPack/HedgeArcPack.exe'),str(packedfolder)],input='hh\n',text=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=30)
        parts=sorted(out.glob(fixed.name+'.ar*'));assert any(p.name.endswith('.ar.00') for p in parts)
        verify=W/'Roundtrip'/job['archive'];verify.mkdir(parents=True,exist_ok=True)
        for p in parts:shutil.copy2(p,verify/p.name)
        unpack(verify/(fixed.name+'.ar.00'))
        decoded=verify/fixed.name
        assert {p.name for p in decoded.iterdir()}==names
        for name in names:assert sha(decoded/name)==sha(fixed/name),name
        results.append({'archive':job['archive'],'changedMembers':sorted(changed),'parts':[{'name':p.name,'sha256':sha(p)} for p in parts]})
    assert released=={str(p):sha(p) for p in (R/'outputs/GameBanana-1.0.2').glob('*.zip')}
    report={'passed':True,'archives':results,'releasePackagesUnchanged':True,'installed':False}
    (W/'packing-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    if args.install:
        target=R/'UnleashedRecomp-Windows/mods/UnleashedKorean/Inspire/subtitle/English'
        backup=W/'InstalledBefore';backup.mkdir(exist_ok=True)
        plans=[]
        # Verify ALL targets and preserve ALL originals before the first replacement.
        for result in results:
            original=Path(originals[result['archive']]['source']).parent
            for part in result['parts']:
                name=part['name'];dest=target/name;old=sha(dest);new=part['sha256']
                assert old in (sha(original/name),new),('Unexpected installed modification',name)
                if old!=new:
                    saved=backup/name
                    if saved.exists():assert sha(saved)==old
                    else:shutil.copy2(dest,saved)
                plans.append({'name':name,'beforeSha256':sha(backup/name) if (backup/name).exists() else old,'afterSha256':new})
        (W/'install-backup.json').write_text(json.dumps(plans,indent=2),encoding='utf8')
        for item in plans:
            dest=target/item['name'];temp=target/(item['name']+'.tmp')
            shutil.copy2(out/item['name'],temp);assert sha(temp)==item['afterSha256'];os.replace(temp,dest)
        for item in plans:assert sha(target/item['name'])==item['afterSha256']
        report['installed']=True;report['installedFiles']=len(plans)
        (W/'packing-verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({'archives':len(results),'roundtripPassed':True,'installed':report['installed'],'releasedZipsUnchanged':True}))
if __name__=='__main__':main()
