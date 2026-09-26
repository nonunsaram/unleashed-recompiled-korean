"""Verify the v1.0.5 local review mod only changes the intended resources."""
from __future__ import annotations
import configparser
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BEFORE=ROOT/'Build/Development-v104-Final/UnleashedKorean'
AFTER=ROOT/'Build/Development-v105-Review/UnleashedKorean'
OUT=ROOT/'Build/Development-v105-Review/verification.json'

def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def inventory(root): return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file()}

def main():
    before,after=inventory(BEFORE),inventory(AFTER)
    wang=read(ROOT/'Translation/review/proper-name-audit-v105/resource-verification.json')
    edits=read(ROOT/'Translation/review/proper-name-audit-v105/wang-edits.json')
    hd=read(ROOT/'Build/UnleasHD-Compatibility-v105-HUD2/verification.json')
    residual=read(ROOT/'Translation/review/unleashhd-v105/residual-conflicts.json')
    assert residual['passed'] and residual['remainingKoreanDdsOverlaps']==17
    assert wang['passed'] and wang['physical_cells']==70 and wang['archive_count']==20
    assert len(edits['catalog_entries'])==7
    assert hd['passed'] and (hd['archiveCount'],hd['textureCount'],hd['translatedTextureCount'],hd['unmodifiedHdTextureCount'])==(14,43,15,28)
    groups={}
    variants={'BaseGame':'BaseGame','Apotos & Shamar Adventure Pack':'ApotosShamar','Chun-nan Adventure Pack':'ChunNan','Empire City & Adabat Adventure Pack':'AllDLC','Holoska Adventure Pack':'Holoska','Mazuri Adventure Pack':'Mazuri','Spagonia Adventure Pack':'Spagonia'}
    for group in wang['archives']:
        name=group['archive'];stem='WorldMap' if name=='WorldMap' else '+'+name
        parent=(f"WorldMapVariants/{variants[group['package']]}/Languages/English" if name=='WorldMap' else 'Languages/English')
        groups[(parent,stem)]=group
    allowed={'mod.ini','ConfigSchema.json','README-KO.md','README-EN.md','MODS-KO.md'}
    for parent,stem in groups:
        allowed|={n for n in before if n.startswith(parent+'/'+stem+'.ar.') or n==parent+'/'+stem+'.arl'}
    hd_dir=ROOT/'Build/UnleasHD-Compatibility-v105-HUD2/Overlay/Languages/English'
    new_hd={'Compatibility/UnleasHD-1.4.2/Languages/English/'+p.name:p for p in hd_dir.iterdir() if p.is_file()}
    assert len(new_hd)==29
    assert set(after)-set(before)==set(new_hd)|{'README-1.0.5-REVIEW-KO.md','NAME-AUDIT-KO.md','NAME-RECOMMENDATIONS-KO.md','NAME-REGIONS-113.csv'}
    assert not set(before)-set(after)
    for rel,path in new_hd.items(): assert sha(after[rel])==sha(path),rel
    changes=[]
    for rel in before:
        if sha(before[rel])!=sha(after[rel]):
            assert rel in allowed,rel
            changes.append(rel)
    assert any(x.startswith('Languages/English/+Town_China_Common') for x in changes)
    assert any(x.startswith('WorldMapVariants/AllDLC/') for x in changes)
    ini=configparser.ConfigParser(interpolation=None);ini.read(AFTER/'mod.ini',encoding='utf-8-sig')
    assert ini['Desc']['Version'].strip('"')=='1.0.5-review'
    assert ini['Main']['IncludeDir2'].strip('"')=='Compatibility/None'
    schema=read(AFTER/'ConfigSchema.json')
    options=[x for g in schema['Groups'] for x in g['Elements'] if x['Name']=='IncludeDir2']
    assert len(options)==1
    choices=schema['Enums'][options[0]['Type']]
    assert any(x['Value']=='Compatibility/UnleasHD-1.4.2' for x in choices)
    report={'passed':True,'candidate':str(AFTER),'catalogEntriesChanged':7,'wangPhysicalCells':70,
            'wangArchives':20,'hdArchiveCount':14,'hdTextureCount':43,'hdUnmodifiedSourceTextures':28,
            'hdTranslatedTextures':15,'remainingTranslatedDdsOverlaps':17,'newHdArchiveFiles':len(new_hd),'changedExistingFiles':len(changes),
            'unrelatedExistingFilesPreserved':len(before)-len(changes),'gameplayVerified':False,
            'publicRelease':False}
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
