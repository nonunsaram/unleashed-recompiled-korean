"""Prepare a read-only review of the currently installed and packaged subtitles."""
from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];W=R/'Build/CutsceneFullReview-20260914'
def main():
    W.mkdir(exist_ok=True)
    read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    L=R/'Build/LatinBaseline-Audit'
    fixed={x['archive']:x for x in read(L/'packing-verification.json')['archives']};index=[]
    with zipfile.ZipFile(R/'outputs/GameBanana-1.0.2/UnleashedRecompiled-Korean-1.0.2-Basic.zip') as z:
        for e in read(L/'archive-index.json'):
            if e['version']!='v102':continue
            a=e['archive'];name='+'+a+'.ar.00';rel='Inspire/subtitle/English/'+name
            digest=next(x['sha256'] for x in fixed[a]['parts'] if x['name']==name) if a in fixed else e['sha256']
            assert sha(R/'UnleashedRecomp-Windows/mods/UnleashedKorean'/rel)==digest
            assert hashlib.sha256(z.read('UnleashedKorean/'+rel)).hexdigest()==digest
            folder=L/'Roundtrip'/a/('+'+a) if a in fixed else Path(e['folder'])
            original=Path(e['folder'])
            for m in read(original.parent/'members.json'):
                source=L/'FixedWork'/('+'+a)/m['name'] if a in fixed else original/m['name']
                assert sha(folder/m['name'])==sha(source)
            index.append({'archive':a,'folder':str(folder),'originalFolder':str(original),'sha256':digest,'fixed':a in fixed})
    (W/'index.json').write_text(json.dumps(index,indent=2),encoding='utf8')
    print('Verified 43 installed and packaged subtitle archives against audited extraction.')
if __name__=='__main__':main()

