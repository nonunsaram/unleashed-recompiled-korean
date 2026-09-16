"""Create a candidate from the final 1.0.2 release plus explicitly approved later changes."""
from pathlib import Path
import json,shutil,zipfile
from release_contract_v104 import R,BASE,inputs,verify_folder,sha
from configure_features_v104 import configure
D=R/'Build/Development-v104-Final/UnleashedKorean'
def main():
    base,translation,logos=inputs()
    assert not D.exists(),'Preserve existing candidate input'
    D.mkdir(parents=True)
    with zipfile.ZipFile(BASE) as z:
        for n in z.namelist():
            rel=n.removeprefix('UnleashedKorean/')
            assert n.startswith('UnleashedKorean/') and '..' not in Path(rel).parts and ':' not in rel
            if rel.startswith('TitleLogos/'):continue
            if n.endswith('/'): (D/rel).mkdir(parents=True,exist_ok=True);continue
            (D/rel).parent.mkdir(parents=True,exist_ok=True);(D/rel).write_bytes(z.read(n))
    for item in translation['patches']:
        p=R/'Build/Translation-v103/Resources'/item['relative'];assert sha(p.read_bytes())==item['after_sha256']
        shutil.copy2(p,D/item['relative'])
    for name,v in logos['variants'].items():
        out=D/'TitleLogos'/name;out.mkdir(parents=True)
        for file,digest in v['archives'].items():
            p=R/'Build/TitleLogo-Choices/Variants'/name/file;assert sha(p.read_bytes())==digest;shutil.copy2(p,out/file)
    for n in ['mod.ini','ConfigSchema.json']:shutil.copy2(R/'Build/Development-v104/UnleashedKorean'/n,D/n)
    configure(D)
    result=verify_folder(D)
    (D.parent/'cumulative-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result))
if __name__=='__main__':main()
