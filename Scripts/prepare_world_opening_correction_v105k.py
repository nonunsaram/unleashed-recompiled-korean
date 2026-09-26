"""Package review11 with the original-based World Adventure opening logo."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import shutil
import zipfile


ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Build/Development-v105j-Playtest/UnleashedKorean'
OUTPUT=ROOT/'Build/Development-v105k-Playtest/UnleashedKorean'
CORRECTED=ROOT/'Build/OPLogoInvestigation/OriginalBased/OPmovie_titlelogo_KR_World.dds'
ZIP=ROOT/'outputs/UnleashedRecompiled-Korean-1.0.5-Review11-LocalPlaytest.zip'


def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main()->None:
    report=json.loads((CORRECTED.parent/'verification.json').read_text(encoding='utf8'))
    assert report['passed'] and report['outsideRectangleIdenticalToOriginal']
    assert SOURCE.is_dir() and not OUTPUT.exists() and not ZIP.exists()
    assert digest(CORRECTED)==report['outputSha256']
    shutil.copytree(SOURCE,OUTPUT)
    targets=[]
    for language in ('EN','JP'):
        rel=Path('TitleLogos/Custom/Loading')/f'OPmovie_titlelogo_{language}.dds'
        target=OUTPUT/rel
        assert target.is_file()
        shutil.copy2(CORRECTED,target)
        assert digest(target)==digest(CORRECTED)
        targets.append(rel.as_posix())
    ini=OUTPUT/'mod.ini'
    contents=ini.read_text(encoding='utf-8-sig')
    assert contents.count('Version="1.0.5-review10"')==1
    ini.write_text(contents.replace('Version="1.0.5-review10"',
        'Version="1.0.5-review11"',1),encoding='utf8')
    readme=OUTPUT/'README-1.0.5-REVIEW-KO.md'
    contents=readme.read_text(encoding='utf8')
    assert contents.startswith('# 한국어 패치 1.0.5-review10 플레이 테스트 후보')
    contents=contents.replace('# 한국어 패치 1.0.5-review10 플레이 테스트 후보',
        '# 한국어 패치 1.0.5-review11 플레이 테스트 후보',1)
    contents += ('\n월드 어드벤처 오프닝 로고를 원본 영상용 DDS의 영어 글자와 지구 그림을 '
                 '그대로 보존하고 일본어 제목 부분만 한국어로 교체했습니다. '
                 '검은 테두리가 겹쳐 보이던 이전 합성본은 사용하지 않습니다.\n')
    readme.write_text(contents,encoding='utf8')
    before={p.relative_to(SOURCE).as_posix():digest(p) for p in SOURCE.rglob('*') if p.is_file()}
    after={p.relative_to(OUTPUT).as_posix():digest(p) for p in OUTPUT.rglob('*') if p.is_file()}
    allowed=set(targets)|{'mod.ini','README-1.0.5-REVIEW-KO.md'}
    assert {p for p in after if after[p]!=before.get(p)}==allowed
    assert all(after[p]==h for p,h in before.items() if p not in allowed)
    files=sorted(p for p in OUTPUT.rglob('*') if p.is_file())
    with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for p in files:archive.write(p,'UnleashedKorean/'+p.relative_to(OUTPUT).as_posix())
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None and len(archive.namelist())==len(files)
    result={'passed':True,'version':'1.0.5-review11','edition':'Basic',
            'correctedAssets':targets,'sourcePixelsUnchangedOutsideCaption':True,
            'zip':str(ZIP),'zipSha256':digest(ZIP),
            'gameplayVerified':False,'publicRelease':False}
    (OUTPUT.parent/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
