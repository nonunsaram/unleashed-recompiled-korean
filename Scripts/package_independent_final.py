"""Package an approved independent staging folder; no artwork is generated here.

Usage: python Scripts/package_independent_final.py STAGING OUTPUT RECORD SOURCE_ROOT
STAGING contains the final approved game resources and release documentation.
RECORD is Release/v1.0.5/release-record.json. SOURCE_ROOT is the public source tree.
"""
import argparse, configparser, io, json, zipfile
from pathlib import Path
from verify_independent_release import game_files, sha, verify_zip

def main():
    p=argparse.ArgumentParser()
    for name in ('staging','output','record','source_root'): p.add_argument(name,type=Path)
    a=p.parse_args(); record=json.loads(a.record.read_text(encoding='utf8'))
    assert game_files(a.staging)==record['approvedGameFiles']
    a.output.mkdir(parents=True,exist_ok=True)
    source=io.BytesIO()
    allowed={'.py','.ps1','.cs','.cpp','.h','.hpp','.json','.csv','.patch','.md','.txt','.ttf','.pdf'}
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
        for directory in ('Scripts','Patches','Translation','Tools','Licenses'):
            for f in sorted((a.source_root/directory).rglob('*')):
                if f.is_file() and f.suffix.lower() in allowed and '__pycache__' not in f.parts:
                    z.write(f,'Source/'+f.relative_to(a.source_root).as_posix())
        for name in ('README.md','BUILDING.md','LICENSE.md','THIRD_PARTY_NOTICES.md'):
            z.write(a.source_root/name,'Source/'+name)
        for f in sorted(a.record.parent.iterdir()):
            if f.suffix.lower() in {'.md','.csv','.json'} and f.name not in {'verification.json','manifest.json'}: z.write(f,'Source/Release/v1.0.5/'+f.name)
    results={}
    for edition in ('Basic','Full'):
        dest=a.output/f'unleashedrecompiled-korean-105-{edition.lower()}.zip'
        assert not dest.exists(),dest
        try:
            with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
                for f in sorted(a.staging.rglob('*')):
                    if not f.is_file():continue
                    rel=f.relative_to(a.staging).as_posix()
                    if rel=='Source.zip':continue
                    if edition=='Basic' and (rel.startswith('Support/') or rel=='KoreanFullSetup.exe'):continue
                    blob=f.read_bytes()
                    if rel=='mod.ini':
                        c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read_string(blob.decode('utf-8-sig'))
                        c['Desc']['Title']='"Korean Translation / 한국어 패치 — '+('전체판' if edition=='Full' else '기본판')+'"'
                        out=io.StringIO();c.write(out,space_around_delimiters=False);blob=out.getvalue().encode('utf8')
                    z.writestr('UnleashedKorean/'+rel,blob)
                if edition=='Full':z.writestr('UnleashedKorean/Source.zip',source.getvalue())
            results[edition]=verify_zip(dest,record,edition)
            results[edition].update(file=dest.name,sha256=sha(dest.read_bytes()),bytes=dest.stat().st_size)
        except Exception:
            if dest.exists():dest.rename(dest.with_name(dest.stem+'-FAILED.zip'))
            raise
    (a.output/'verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (a.output/'SHA256SUMS.txt').write_text(''.join(v['sha256']+'  '+v['file']+'\n' for v in results.values()),encoding='ascii')
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
