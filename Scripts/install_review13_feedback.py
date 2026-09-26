"""Install review13 feedback while preserving Full-edition and user settings."""
from __future__ import annotations
import configparser,hashlib,json,shutil
from pathlib import Path
import psutil

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'Build/Development-v105m-Playtest/UnleashedKorean'
PREVIOUS=ROOT/'Build/Development-v105l-Playtest/UnleashedKorean'
FULL=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
BACKUP=ROOT/'Build/HMM-Backup-v105m-20260925'
REPORT=ROOT/'Build/HMM-Install-v105m-Playtest/verification.json'
BUILD=ROOT/'Build/Development-v105m-Playtest/verification.json'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ini(path):
    c=configparser.ConfigParser(interpolation=None);c.read(path,encoding='utf-8-sig');return c

def main():
    assert STAGE.is_dir() and PREVIOUS.is_dir() and FULL.is_dir()
    assert not BACKUP.exists() and not REPORT.exists()
    processes=[(p.name(),p.pid) for p in psutil.process_iter()
               if any(x in p.name().lower() for x in ('hedgemodmanager','unleashedrecomp'))]
    assert not processes,f'Close game/HMM before installing: {processes}'
    build=json.loads(BUILD.read_text(encoding='utf8'))
    assert build['passed'] and build['version']=='1.0.5-review13'
    proposed={Path(p) for a in build['archiveDetails'] for p in a['archiveFiles']}
    proposed|={Path('TitleLogos/Custom/Loading/OPmovie_titlelogo_EN.dds'),
               Path('TitleLogos/Custom/Loading/OPmovie_titlelogo_JP.dds')}
    changed={p for p in proposed if sha(STAGE/p)!=sha(PREVIOUS/p)}
    assert len(changed)==32,len(changed)
    files=changed|{Path('README-1.0.5-REVIEW-KO.md'),Path('mod.ini')}
    old=ini(FULL/'mod.ini')
    assert old['Desc']['Version'].strip('"')=='1.0.5-review12'
    assert '전체판' in old['Desc']['Title']
    assert old['Main']['IncludeDir1'].strip('"')=='Compatibility/UnleasHD-1.4.2'
    assert old['Main']['IncludeDir3'].strip('"')=='TitleLogos/Custom'
    for p in changed:
        assert (FULL/p).is_file() and sha(FULL/p)==sha(PREVIOUS/p),p
    fixed={p:sha(FULL/p) for p in (
        Path('ConfigSchema.json'),Path('KoreanFullSetup.exe'),
        Path('TitleLogos/Korean/Loading/OPmovie_titlelogo_EN.dds'),
        Path('TitleLogos/Korean/+Title.ar.00'),
        Path('TitleLogos/Custom/+Title.ar.00'))}
    for p in files:
        target=BACKUP/p;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(FULL/p,target)
    try:
        for p in changed:shutil.copy2(STAGE/p,FULL/p)
        ini_file=FULL/'mod.ini';raw=ini_file.read_text(encoding='utf-8-sig')
        assert raw.count('Version="1.0.5-review12"')==1
        ini_file.write_text(raw.replace('Version="1.0.5-review12"','Version="1.0.5-review13"',1),encoding='utf8')
        readme=FULL/'README-1.0.5-REVIEW-KO.md';raw=readme.read_text(encoding='utf8')
        assert raw.startswith('# 한국어 패치 1.0.5-review12 플레이 테스트 후보')
        raw=raw.replace('# 한국어 패치 1.0.5-review12 플레이 테스트 후보',
                        '# 한국어 패치 1.0.5-review13 플레이 테스트 후보',1)
        raw+='\n월드 어드벤처 오프닝 문구를 원본 가로 비율로 바꾸고 로고 윗선을 복원했습니다. '
        raw+='HD 컷신 영문·숫자·문장부호 178개를 한글과 같은 기준선에 맞췄습니다.\n'
        readme.write_text(raw,encoding='utf8')
        assert all(sha(FULL/p)==sha(STAGE/p) for p in changed)
        assert all(sha(FULL/p)==v for p,v in fixed.items())
        new=ini(FULL/'mod.ini')
        for section in old.sections():
            for key,val in old[section].items():
                if section=='Desc' and key=='version':continue
                assert new[section][key]==val,(section,key)
        report={'passed':True,'version':'1.0.5-review13','edition':'Full',
                'installedMod':str(FULL),'backup':str(BACKUP),
                'archivePartsChanged':len(changed)-2,'openingTexturesChanged':2,
                'selectedLogo':new['Main']['IncludeDir3'].strip('"'),
                'otherSettingsAndAssetsPreserved':True,'gameplayVerified':False,'publicRelease':False}
        REPORT.parent.mkdir(parents=True)
        REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(json.dumps(report,ensure_ascii=False))
    except Exception:
        for p in files:shutil.copy2(BACKUP/p,FULL/p)
        raise
if __name__=='__main__':main()
