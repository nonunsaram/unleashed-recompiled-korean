"""Decode every final-candidate archive with bounded tools; inspect every shipped DDS."""
from pathlib import Path
import json,shutil,hashlib
from PIL import Image
from bounded_archive_tool import unpack
from release_contract_v104 import R,verify_folder
W=R/'Build/FinalAudit-v104';D=R/'Build/Development-v104-Final/UnleashedKorean'
def main():
    verify_folder(D);records=[];dds=[];members=[]
    for i,source in enumerate(sorted(D.rglob('*.ar.00'))):
        rel=source.relative_to(D);stem=source.name[:-6];dest=W/'Archives'/rel.parent/stem
        dest.mkdir(parents=True,exist_ok=True)
        for p in source.parent.glob(stem+'.ar*'):shutil.copy2(p,dest/p.name)
        unpack(dest/source.name)
        folder=dest/stem;assert folder.is_dir(),source
        files=sorted(p for p in folder.rglob('*') if p.is_file());assert files,source
        for p in files:
            item={'archive':rel.as_posix(),'member':p.relative_to(folder).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};members.append(item)
            if p.suffix.lower()=='.dds':
                im=Image.open(p);im.load();assert im.width>0 and im.height>0
                dds.append({'file':str(p),'size':[im.width,im.height],'mode':im.mode})
        records.append({'archive':rel.as_posix(),'folder':str(folder),'memberCount':len(files)})
        if (i+1)%10==0:print('Decoded archives:',i+1,flush=True)
    (W/'archive-index.json').write_text(json.dumps(records,indent=2),encoding='utf8')
    (W/'members.json').write_text(json.dumps(members,indent=2),encoding='utf8')
    (W/'dds.json').write_text(json.dumps(dds,indent=2),encoding='utf8')
    result={'passed':True,'archivesDecoded':len(records),'membersHashed':len(members),'ddsDecoded':len(dds),'resourceContractPassed':True}
    (W/'payload-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
if __name__=='__main__':main()
