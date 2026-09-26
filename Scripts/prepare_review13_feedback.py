"""Build review13 from review12 with restored World border and common ASCII baseline."""
from __future__ import annotations
import hashlib,json,shutil,zipfile
from collections import defaultdict
from pathlib import Path
import prepare_review12_feedback as pack

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Build/Development-v105l-Playtest/UnleashedKorean'
OUT=ROOT/'Build/Development-v105m-Playtest/UnleashedKorean'
WORK=ROOT/'Build/Review13-Feedback/ArchiveWork'
REPORT=ROOT/'Build/Review13-Feedback/cutscene-ascii-verification.json'
GLYPHS=ROOT/'Build/Review13-Feedback/HdCutsceneAsciiPages'
LOGO=ROOT/'Build/OPLogoInvestigation/OriginalBased/OPmovie_titlelogo_KR_World.dds'
ZIP=ROOT/'outputs/UnleashedRecompiled-Korean-1.0.5-Review13-LocalPlaytest.zip'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert SOURCE.is_dir() and GLYPHS.is_dir() and LOGO.is_file()
    assert not OUT.exists() and not WORK.exists() and not ZIP.exists()
    font=json.loads(REPORT.read_text(encoding='utf8'))
    assert font['passed'] and font['asciiGlyphsAligned']==178 and font['pagesChanged']==43
    opening=json.loads((LOGO.parent/'verification.json').read_text(encoding='utf8'))
    assert opening['passed'] and opening['outsideRectangleIdenticalToOriginal']
    shutil.copytree(SOURCE,OUT)
    for lang in ('EN','JP'):
        destination=OUT/'TitleLogos/Custom/Loading'/f'OPmovie_titlelogo_{lang}.dds'
        shutil.copy2(LOGO,destination)
        assert sha(destination)==sha(LOGO)
    pack.OUT=OUT;pack.WORK=WORK
    jobs=defaultdict(dict)
    for row in font['files']:
        if row['sourceSha256']!=row['outputSha256']:
            jobs[row['archive']][row['texture']]=GLYPHS/row['archive']/row['texture']
    assert sum(map(len,jobs.values()))==32
    relative=Path('Compatibility/UnleasHD-1.4.2/Inspire/subtitle/English')
    results=[]
    for archive,files in sorted(jobs.items()):
        stem='+'+archive
        area,folder=pack.job_dir(relative,stem)
        before={p.name:sha(p) for p in folder.iterdir() if p.is_file()}
        for name,source in files.items():
            assert name in before and source.is_file()
            shutil.copy2(source,folder/name)
        results.append(pack.finish(relative,stem,area,folder,before,set(files)))
    ini=OUT/'mod.ini';raw=ini.read_text(encoding='utf-8-sig')
    assert raw.count('Version="1.0.5-review12"')==1
    ini.write_text(raw.replace('Version="1.0.5-review12"','Version="1.0.5-review13"',1),encoding='utf8')
    readme=OUT/'README-1.0.5-REVIEW-KO.md';raw=readme.read_text(encoding='utf8')
    assert raw.startswith('# 한국어 패치 1.0.5-review12 플레이 테스트 후보')
    raw=raw.replace('# 한국어 패치 1.0.5-review12 플레이 테스트 후보',
                    '# 한국어 패치 1.0.5-review13 플레이 테스트 후보',1)
    raw+='\n월드 어드벤처 오프닝 문구의 원본 가로 비율과 영문 로고 윗선을 복원했습니다. '
    raw+='HD 컷신의 영문·숫자·문장부호 178개를 한글과 같은 기준선에 맞췄습니다. '
    raw+='Excellent!, Dr., 쉼표·따옴표·물음표를 실제 게임 화면에서 확인해 주십시오.\n'
    readme.write_text(raw,encoding='utf8')
    before={p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}
    after={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()}
    allowed={p for a in results for p in a['archiveFiles']}
    allowed|={'TitleLogos/Custom/Loading/OPmovie_titlelogo_EN.dds',
              'TitleLogos/Custom/Loading/OPmovie_titlelogo_JP.dds',
              'mod.ini','README-1.0.5-REVIEW-KO.md'}
    assert set(after)==set(before)
    changed={p for p in after if after[p]!=before[p]}
    assert changed<=allowed,(changed-allowed)
    assert {'mod.ini','README-1.0.5-REVIEW-KO.md',
            'TitleLogos/Custom/Loading/OPmovie_titlelogo_EN.dds',
            'TitleLogos/Custom/Loading/OPmovie_titlelogo_JP.dds'}<=changed
    files=sorted(p for p in OUT.rglob('*') if p.is_file())
    with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:z.write(p,'UnleashedKorean/'+p.relative_to(OUT).as_posix())
    with zipfile.ZipFile(ZIP) as z:assert z.testzip() is None and len(z.namelist())==len(files)
    report={'passed':True,'version':'1.0.5-review13','edition':'Basic',
            'worldCaptionNativeWidth':210,'worldTopBorderRestored':True,
            'asciiGlyphsAligned':178,'asciiPagesChanged':32,'asciiPagesAlreadyAligned':11,'archivesUpdated':len(results),
            'archiveDetails':results,'otherAssetsPreserved':True,
            'zip':str(ZIP),'zipSha256':sha(ZIP),'gameplayVerified':False,'publicRelease':False}
    (OUT.parent/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('archiveDetails','zipSha256')},ensure_ascii=False))
if __name__=='__main__':main()
