from pathlib import Path
import sys,json,hashlib,struct,bz2,gzip
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'Tools/ReleaseRuntime'))
import bsdiff4
O=R/'Build/GameBanana-0.4.17/UnleashedKorean';D=O/'Support/Patches';D.mkdir(parents=True,exist_ok=True)
P=R/'Build/FieldMission-v056';B=R/'Build/CleanOriginals-v057'
sha=lambda b:hashlib.sha256(b).hexdigest()
def offtin(b):
    n=int.from_bytes(b,'little')
    return -(n&0x7fffffffffffffff) if n>>63 else n
import shutil
previous=R/'Build/GameBanana-0.4.15/UnleashedKorean'
cache={f['relative']:f for f in json.loads((previous/'Support/manifest.json').read_text())['files']}
files=[]
for folder in ['Native','DirectArchives']:
    for f in sorted((P/folder).rglob('*')):
        if not f.is_file():continue
        rel=f.relative_to(P/folder).as_posix();source=B/rel
        old=source.read_bytes();new=f.read_bytes()
        prior=cache.get(rel)
        if prior and prior['originalSha256']==sha(old) and prior['patchedSha256']==sha(new):
            name=f'{len(files):02}.krpatch.gz';shutil.copy2(previous/prior['patch'],D/name);entry=dict(prior);entry['patch']='Support/Patches/'+name;files.append(entry);print(rel,': verified unchanged patch reused',flush=True);continue
        patch=bsdiff4.diff(old,new)
        assert bsdiff4.patch(old,patch)==new
        nc=offtin(patch[8:16]);nd=offtin(patch[16:24]);size=offtin(patch[24:32]);assert size==len(new)
        control=bz2.decompress(patch[32:32+nc]);diff=bz2.decompress(patch[32+nc:32+nc+nd]);extra=bz2.decompress(patch[32+nc+nd:])
        control=b''.join(struct.pack('<q',offtin(control[i:i+8])) for i in range(0,len(control),8))
        raw=b'URKRDP1\0'+struct.pack('<4q',len(old),len(new),len(control),len(diff))+control+diff+extra
        payload=gzip.compress(raw,compresslevel=9,mtime=0);name=f'{len(files):02}.krpatch.gz';(D/name).write_bytes(payload)
        files.append({'relative':rel,'optional':rel.startswith('dlc/'),'originalSha256':sha(old),'patchedSha256':sha(new),'originalLength':len(old),'patchedLength':len(new),'patch':'Support/Patches/'+name,'patchSha256':sha(payload)})
        print(rel,':',len(old),'->',len(new),'patch',len(payload),flush=True)
(O/'Support/manifest.json').write_text(json.dumps({'version':'0.4.17','gameVersion':'Unleashed Recompiled v1.0.3 Windows x64','files':files},ensure_ascii=False,indent=2),encoding='utf8')
print('Patch set complete:',len(files),'files',flush=True)
