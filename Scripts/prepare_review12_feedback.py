"""Build review12 feedback candidate from review11 without replacing unrelated assets."""
from __future__ import annotations
import hashlib,json,shutil,subprocess,zipfile,struct,time
from collections import defaultdict
from pathlib import Path
from PIL import Image
from bounded_archive_tool import unpack
from build_unleashhd_ui_compat_v105 import members

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Build/Development-v105k-Playtest/UnleashedKorean'
OUT=ROOT/'Build/Development-v105l-Playtest/UnleashedKorean'
WORK=ROOT/'Build/Review12-Feedback/ArchiveWork'
LOGO=ROOT/'Build/OPLogoInvestigation/OriginalBased/OPmovie_titlelogo_KR_World.dds'
LATIN=ROOT/'Build/Review12-Feedback/HdCutsceneLatinPages'
LATIN_REPORT=ROOT/'Build/Review12-Feedback/cutscene-latin-verification.json'
HD_REPORT=ROOT/'Build/UnleasHD-Compatibility-v105-HUD2/verification.json'
MEDIA=ROOT/'Build/Review11-Feedback'
TEXCONV=ROOT/'Build/OPLogoInvestigation/Tools/texconv.exe'
PACKER=ROOT/'Tools/HedgeArcPack/HedgeArcPack.exe'
ZIP=ROOT/'outputs/UnleashedRecompiled-Korean-1.0.5-Review12-LocalPlaytest.zip'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def pack(folder):
    subprocess.run([str(PACKER),str(folder)],input='hh\n',text=True,capture_output=True,
                   check=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)

def job_dir(relative,stem):
    area=WORK/relative/stem
    area.mkdir(parents=True)
    current=OUT/relative
    for part in current.glob(stem+'.ar.*'):shutil.copy2(part,area/part.name)
    shutil.copy2(current/(stem+'.arl'),area/(stem+'.arl'))
    unpack(area/(stem+'.ar.00'))
    folder=area/stem
    assert folder.is_dir() and members(area/(stem+'.arl'))=={p.name for p in folder.iterdir() if p.is_file()}
    return area,folder

def finish(relative,stem,area,folder,before,changed):
    assert set(before)=={p.name for p in folder.iterdir() if p.is_file()}
    assert all(sha(folder/name)==digest for name,digest in before.items() if name not in changed)
    assert all(sha(folder/name)!=before[name] for name in changed)
    for oldpart in [area/(stem+'.arl'),*area.glob(stem+'.ar.*')]:oldpart.unlink()
    pack(folder)
    assert members(area/(stem+'.arl'))==set(before)
    destination=OUT/relative
    for oldpart in [destination/(stem+'.arl'),*destination.glob(stem+'.ar.*')]:oldpart.unlink()
    for file in [area/(stem+'.arl'),*sorted(area.glob(stem+'.ar.*'))]:
        shutil.copy2(file,destination/file.name)
    check=WORK/'RoundTrip'/relative/stem
    check.mkdir(parents=True)
    for part in destination.glob(stem+'.ar.*'):shutil.copy2(part,check/part.name)
    shutil.copy2(destination/(stem+'.arl'),check/(stem+'.arl'))
    unpack(check/(stem+'.ar.00'))
    actual=check/stem
    assert {p.name for p in actual.iterdir() if p.is_file()}==set(before)
    assert all((actual/name).is_file() for name in before)
    return {'archive':(relative/stem).as_posix(),'changedMembers':sorted(changed),
            'preservedMembers':len(before)-len(changed),
            'archiveFiles':[str((relative/p.name).as_posix()) for p in [area/(stem+'.arl'),*sorted(area.glob(stem+'.ar.*'))]]}

def encode_bc7(source,output,expected_size):
    encoded=output.parent/'Encoded'/output.name
    encoded.parent.mkdir(parents=True,exist_ok=True)
    result=subprocess.run([str(TEXCONV),'-nologo','-f','BC7_UNORM','-m','1','-y',
                           '-o',str(encoded.parent),str(source)],capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stdout+'\n'+result.stderr)
    candidate=encoded.parent/(source.stem+'.dds')
    assert candidate.is_file(),(source,candidate)
    raw=candidate.read_bytes()
    assert raw[:4]==b'DDS ' and raw[84:88]==b'DX10' and struct.unpack_from('<I',raw,128)[0]==98
    with Image.open(candidate) as image:assert image.size==expected_size
    shutil.copy2(candidate,output)

def main():
    assert SOURCE.is_dir() and LOGO.is_file() and LATIN.is_dir() and TEXCONV.is_file()
    assert not OUT.exists() and not WORK.exists() and not ZIP.exists()
    latin=json.loads(LATIN_REPORT.read_text(encoding='utf8'))
    hd=json.loads(HD_REPORT.read_text(encoding='utf8'))
    assert latin['passed'] and latin['redrawnGlyphs']==103
    jobs=defaultdict(dict)
    for row in hd['textures']:
        if row['labels']:jobs[row['archive']][row['file']]=row
    assert len(jobs)==9 and sum(map(len,jobs.values()))==15
    shutil.copytree(SOURCE,OUT)
    for language in ('EN','JP'):
        target=OUT/'TitleLogos/Custom/Loading'/f'OPmovie_titlelogo_{language}.dds'
        shutil.copy2(LOGO,target)
        assert sha(target)==sha(LOGO)
    results=[];old_bytes=0;new_bytes=0
    relative=Path('Compatibility/UnleasHD-1.4.2/Languages/English')
    for archive,files in sorted(jobs.items()):
        stem='+'+archive
        area,folder=job_dir(relative,stem)
        before={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
        for name,row in files.items():
            assert name in before
            old=folder/name
            old_blob=old.read_bytes()
            assert old_blob[:4]==b'DDS ' and old_blob[84:88]!=b'DX10'
            old_bytes+=len(old_blob)
            if archive=='Town_Labo_Common':
                source=area/'Inputs'/(old.stem+'.png')
                source.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(MEDIA/(name+'.png'),source)
            else:source=old
            replacement=area/'Replacement'/name
            replacement.parent.mkdir(parents=True,exist_ok=True)
            encode_bc7(source,replacement,tuple(row['size']))
            new_bytes+=replacement.stat().st_size
            shutil.copy2(replacement,old)
        results.append(finish(relative,stem,area,folder,before,set(files)))
    assert new_bytes<old_bytes*.3
    cut_jobs=defaultdict(dict)
    for row in latin['files']:
        cut_jobs[row['archive']][row['texture']]=LATIN/row['archive']/row['texture']
    assert sum(map(len,cut_jobs.values()))==latin['pagesChanged']
    relative=Path('Compatibility/UnleasHD-1.4.2/Inspire/subtitle/English')
    for archive,files in sorted(cut_jobs.items()):
        stem='+'+archive
        area,folder=job_dir(relative,stem)
        before={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
        for name,source in files.items():
            assert name in before
            shutil.copy2(source,folder/name)
        results.append(finish(relative,stem,area,folder,before,set(files)))
    ini=OUT/'mod.ini';raw=ini.read_text(encoding='utf-8-sig')
    assert raw.count('Version="1.0.5-review11"')==1
    ini.write_text(raw.replace('Version="1.0.5-review11"','Version="1.0.5-review12"',1),encoding='utf8')
    readme=OUT/'README-1.0.5-REVIEW-KO.md';raw=readme.read_text(encoding='utf8')
    assert raw.startswith('# 한국어 패치 1.0.5-review11 플레이 테스트 후보')
    raw=raw.replace('# 한국어 패치 1.0.5-review11 플레이 테스트 후보',
                    '# 한국어 패치 1.0.5-review12 플레이 테스트 후보',1)
    raw+='\n월드 어드벤처 오프닝 한글 문구를 타이틀 화면 비율로 줄였습니다. '
    raw+='HD 미디어룸의 한글 글씨에 어두운 테두리를 더하고, 한글 HD 메뉴 그림 15장을 원본과 같은 BC7 압축 형식으로 바꿨습니다. '
    raw+='HD 컷신 자막에서 확대된 영문·문장부호 103개를 다시 그렸습니다. 실제 화면 확인 후 최종 배포할 예정입니다.\n'
    readme.write_text(raw,encoding='utf8')
    files=sorted(p for p in OUT.rglob('*') if p.is_file())
    with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:z.write(p,'UnleashedKorean/'+p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(ZIP) as z:assert z.testzip() is None and len(z.namelist())==len(files)
    report={'passed':True,'version':'1.0.5-review12','edition':'Basic',
            'openingWorldLogoSha256':sha(LOGO),'unleashedLogoPreserved':True,
            'hdUiCompressedTextures':15,'hdUiBeforeBytes':old_bytes,'hdUiAfterBytes':new_bytes,
            'hdUiReductionPercent':round((1-new_bytes/old_bytes)*100,1),
            'hdCutsceneRedrawnLatinPunctuation':103,'hdCutscenePagesChanged':latin['pagesChanged'],
            'archivesUpdated':len(results),'archiveDetails':results,
            'zip':str(ZIP),'zipSha256':sha(ZIP),'gameplayVerified':False,'publicRelease':False}
    (OUT.parent/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('archiveDetails','openingWorldLogoSha256','zipSha256')},ensure_ascii=False))
if __name__=='__main__':main()
