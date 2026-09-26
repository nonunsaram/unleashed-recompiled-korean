"""Package and install review15, changing only the opening logo and notes."""
from pathlib import Path
import configparser
import csv
import hashlib
import json
import shutil
import subprocess
import zipfile

import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'Build/OPLogoInvestigation'
LOGO=WORK/'OriginalBased/OPmovie_titlelogo_KR_World.dds'
SOURCE=ROOT/'Build/Development-v105n-Playtest/UnleashedKorean'
STAGE=ROOT/'Build/Development-v105o-Playtest/UnleashedKorean'
MOD=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
BACKUP=ROOT/'Build/HMM-Backup-v105o-20260926'
REPORT=ROOT/'Build/HMM-Install-v105o-Playtest/verification.json'
ZIP=ROOT/'outputs/UnleashedRecompiled-Korean-1.0.5-Review15-LocalPlaytest.zip'
TEXTURES={Path(f'TitleLogos/Custom/Loading/OPmovie_titlelogo_{lang}.dds')
          for lang in ('EN','JP')}
FILES=TEXTURES|{Path('mod.ini'),Path('README-1.0.5-REVIEW-KO.md')}
NOTE=('\n오프닝의 소닉 월드 어드벤처 로고 상단에서 수평으로 잘린 흰 테두리와 '
      '지구 왼쪽 윤곽을 수정했습니다. 원본 로고의 실제 곡선을 따라 빛 번짐을 '
      '복원했으며, 한글 문구의 크기와 위치는 유지했습니다. 게임용 DDS를 다시 '
      '열어 검증했으며 실제 게임 재생 확인은 별도입니다.\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    return {p.relative_to(root):sha(p) for p in root.rglob('*') if p.is_file()}


def revise_notes(folder):
    path=folder/'mod.ini'
    raw=path.read_text(encoding='utf-8-sig')
    assert raw.count('Version="1.0.5-review14"')==1
    path.write_text(raw.replace('Version="1.0.5-review14"',
                               'Version="1.0.5-review15"'),encoding='utf8')
    path=folder/'README-1.0.5-REVIEW-KO.md'
    raw=path.read_text(encoding='utf8')
    assert raw.startswith('# 한국어 패치 1.0.5-review14 플레이 테스트 후보')
    path.write_text(raw.replace('# 한국어 패치 1.0.5-review14 플레이 테스트 후보',
                                '# 한국어 패치 1.0.5-review15 플레이 테스트 후보',1)+NOTE,
                    encoding='utf8')


def verify_changes(before,folder):
    after=snapshot(folder)
    assert set(before)==set(after)
    assert {p for p in before if before[p]!=after[p]}==FILES
    assert all(sha(folder/p)==sha(LOGO) for p in TEXTURES)


def main():
    build=json.loads((LOGO.parent/'verification.json').read_text(encoding='utf8'))
    assert build['passed'] and build['globeLeftArcRestored']
    assert build['uneditedDxtBlocksIdentical'] and sha(LOGO)==build['outputSha256']
    assert not any(p.exists() for p in (STAGE,ZIP,BACKUP,REPORT))
    tasks=subprocess.check_output(['tasklist','/FO','CSV','/NH']).decode(errors='replace')
    running=[row[:2] for row in csv.reader(tasks.splitlines())
             if row and any(n in row[0].lower() for n in ('hedgemodmanager','unleashedrecomp'))]
    assert not running, f'Game/HMM is running: {running}'
    before=snapshot(SOURCE)
    installed=snapshot(MOD)
    # Ensure the expected review14 textures are the ones being repaired.
    old_logo=WORK/'ContourFix/Before/OPmovie_titlelogo_KR_World.dds'
    assert all(before[p]==installed[p]==sha(old_logo) for p in TEXTURES)
    db=ROOT/'UnleashedRecomp-Windows/mods/ModsDB.ini'
    db_hash=sha(db)
    old_config=configparser.ConfigParser(interpolation=None)
    old_config.read(MOD/'mod.ini',encoding='utf-8-sig')
    assert old_config['Main']['IncludeDir3'].strip('"')=='TitleLogos/Custom'

    shutil.copytree(SOURCE,STAGE)
    for p in TEXTURES:
        shutil.copy2(LOGO,STAGE/p)
    revise_notes(STAGE)
    verify_changes(before,STAGE)
    with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(STAGE.rglob('*')):
            if p.is_file():z.write(p,'UnleashedKorean/'+p.relative_to(STAGE).as_posix())
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None and len(z.namelist())==len(before)
        for p in TEXTURES:
            assert z.read('UnleashedKorean/'+p.as_posix())==LOGO.read_bytes()
    package={'passed':True,'version':'1.0.5-review15','edition':'Basic',
             'zip':str(ZIP),'zipSha256':sha(ZIP),'onlyOpeningTexturesAndNotesChanged':True,
             'gameplayVerified':False,'publicRelease':False}
    (STAGE.parent/'verification.json').write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

    for p in FILES:
        (BACKUP/p).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(MOD/p,BACKUP/p)
    try:
        for p in TEXTURES:shutil.copy2(LOGO,MOD/p)
        revise_notes(MOD)
        verify_changes(installed,MOD)
        assert sha(db)==db_hash
        new_config=configparser.ConfigParser(interpolation=None)
        new_config.read(MOD/'mod.ini',encoding='utf-8-sig')
        for section in old_config:
            for key,value in old_config[section].items():
                if (section,key)!=('Desc','version'):
                    assert new_config[section][key]==value
        result={'passed':True,'version':'1.0.5-review15','edition':'Full',
                'installedMod':str(MOD),'backup':str(BACKUP),
                'changedFiles':sorted(p.as_posix() for p in FILES),
                'otherFilesVerifiedIdentical':len(installed)-len(FILES),
                'settingsAndLoadOrderPreserved':True,'logoSha256':sha(LOGO),
                'gameplayVerified':False,'publicRelease':False}
        REPORT.parent.mkdir(parents=True)
        REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    except Exception:
        for p in FILES:shutil.copy2(BACKUP/p,MOD/p)
        raise

    # Render the installed, decoded DDS, so the preview matches the asset
    # actually loaded by the selected HMM logo option.
    new=Image.open(MOD/next(iter(TEXTURES))).convert('RGBA')
    canvas=Image.new('RGB',new.size,'#202838')
    canvas.paste(new,mask=new.getchannel('A'))
    canvas.save(WORK/'ContourFix/installed-preview.png')
    comparison=Image.new('RGB',(1120,350),'#202838')
    draw=ImageDraw.Draw(comparison)
    for i,(label,path) in enumerate((('BEFORE',old_logo),('AFTER - INSTALLED',MOD/next(iter(TEXTURES))))):
        im=Image.open(path).convert('RGBA')
        bg=Image.new('RGB',im.size,'#202838');bg.paste(im,mask=im.getchannel('A'))
        comparison.paste(bg.crop((355,215,915,525)),(i*560,30))
        draw.text((i*560+12,10),label,fill='white')
    comparison.save(WORK/'ContourFix/before-after.png')
    previous=np.array(Image.open(old_logo).convert('RGBA'))
    previous_step=int(np.abs(np.diff(previous[235:258,620:696,3].astype(np.int16),axis=0)).max())
    print(json.dumps({'package':package,'installation':result,
                      'topAlphaStepBefore':previous_step,'topAlphaStepAfter':build['topEdgeMaxAlphaStep']},ensure_ascii=False))


if __name__=='__main__':main()
