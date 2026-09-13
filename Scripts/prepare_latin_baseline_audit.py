"""Inventory and bounded extraction of shipped subtitle resources; no game writes."""
from pathlib import Path
import hashlib,json,re,shutil
from bounded_archive_tool import unpack
R=Path(__file__).resolve().parents[1]
W=R/'Build/LatinBaseline-Audit'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    W.mkdir(exist_ok=True)
    rows=[]; inventory=[]
    for p in sorted((R/'Translation').glob('*-all.json')):
        d=read(p)
        for row in d.get('items',[]):
            clean=re.sub(r'\{GLYPH:\d+\}','',row.get('korean',''))
            if re.search(r'[A-Za-z0-9]',clean):rows.append({'catalog':p.name,**row})
    (W/'latin-rows.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
    cut={x['translation_key']:x for x in read(R/'Translation/cutscenes-all.json')['items']}
    expected=[{**x,'korean':cut[x['translation_key']]['korean']} for x in read(R/'Analysis/Full-Text-Extraction/Catalog-Reviewed/all-lines.json') if x['translation_key'] in cut]
    (W/'cutscene-expected.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2),encoding='utf8')
    roots={'v100':R/'Build/GameBanana-1.0.0/Basic/UnleashedKorean','v102':R/'Build/GameBanana-v102-20260913-222451/Basic/UnleashedKorean'}
    for version,root in roots.items():
        for ar in sorted((root/'Inspire/subtitle/English').glob('*.ar.00')):
            assert ar.stat().st_size<32*1024*1024
            digest=sha(ar);cache=W/'Extracted'/digest;folder=cache/ar.name[:-6];marker=cache/'members.json'
            if marker.exists():
                for m in read(marker):assert sha(folder/m['name'])==m['sha256']
            else:
                cache.mkdir(parents=True,exist_ok=True)
                for src in ar.parent.glob(ar.name[:-6]+'.ar*'):shutil.copy2(src,cache/src.name)
                unpack(cache/ar.name)
                files=[{'name':p.name,'sha256':sha(p)} for p in folder.iterdir() if p.is_file()]
                marker.write_text(json.dumps(files,indent=2),encoding='utf8')
            inventory.append({'version':version,'archive':ar.name[1:-6],'source':str(ar),'sha256':digest,'folder':str(folder)})
        print(version,'inventoried',len([x for x in inventory if x['version']==version]),flush=True)
    (W/'archive-index.json').write_text(json.dumps(inventory,indent=2),encoding='utf8')
    print(json.dumps({'latinRows':len(rows),'cutscenePhysicalRows':len(expected),'archives':len(inventory),'uniqueExtracts':len({x['sha256'] for x in inventory})}))
if __name__=='__main__':main()
