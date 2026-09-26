"""Create a local-only, integrity-checked v1.0.5 review ZIP."""
from __future__ import annotations
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'Build/Development-v105-Review/UnleashedKorean'
ZIP=ROOT/'outputs/UnleashedRecompiled-Korean-1.0.5-Review.zip'
META=ROOT/'Build/Development-v105-Review/package.json'
VERIFY=ROOT/'Build/Development-v105-Review/verification.json'

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    report=json.loads(VERIFY.read_text(encoding='utf8'))
    assert report['passed'] and not report['gameplayVerified'] and not report['publicRelease']
    if ZIP.exists():
        assert META.is_file() and sha(ZIP)==json.loads(META.read_text(encoding='utf8'))['sha256'], 'Refusing to overwrite an unrecognized ZIP'
    files=sorted(p for p in MOD.rglob('*') if p.is_file())
    with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in files:archive.write(path,'UnleashedKorean/'+path.relative_to(MOD).as_posix())
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None and len(archive.namelist())==len(files)
    result={'file':str(ZIP),'bytes':ZIP.stat().st_size,'sha256':sha(ZIP),'files':len(files),'publicRelease':False}
    META.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
