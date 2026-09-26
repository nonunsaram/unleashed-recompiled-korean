"""Package a local-only Basic review7 playtest ZIP."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'Build/Development-v105g-Playtest/UnleashedKorean'
OUT=ROOT/'outputs/UnleashedRecompiled-Korean-1.0.5-Review7-LocalPlaytest.zip'
META=ROOT/'Build/Development-v105g-Playtest/package.json'


def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def main()->None:
    verification=json.loads((MOD.parent/'verification.json').read_text(encoding='utf8'))
    assert verification['passed'] and not verification['gameplayVerified'] and not verification['publicRelease']
    assert not OUT.exists() and not META.exists()
    files=sorted(p for p in MOD.rglob('*') if p.is_file())
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in files:archive.write(path,'UnleashedKorean/'+path.relative_to(MOD).as_posix())
    with zipfile.ZipFile(OUT) as archive:
        assert archive.testzip() is None and len(archive.namelist())==len(files)
    result={'file':str(OUT),'bytes':OUT.stat().st_size,'sha256':sha(OUT),
            'files':len(files),'edition':'Basic','publicRelease':False}
    META.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
