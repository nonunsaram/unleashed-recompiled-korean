"""Install reviewed review12 changes into the selected Full HMM mod, with rollback."""
from __future__ import annotations
import configparser,hashlib,json,shutil
from pathlib import Path
import psutil

ROOT=Path(__file__).resolve().parents[1]
NEW=ROOT/'Build/Development-v105l-Playtest/UnleashedKorean'
OLD=ROOT/'Build/Development-v105k-Playtest/UnleashedKorean'
FULL=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
BACKUP=ROOT/'Build/HMM-Backup-v105l-20260925'
REPORT=ROOT/'Build/HMM-Install-v105l-Playtest/verification.json'
BUILD=ROOT/'Build/Development-v105l-Playtest/verification.json'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ini(path):
    c=configparser.ConfigParser(interpolation=None);c.read(path,encoding='utf-8-sig');return c

def main():
    assert NEW.is_dir() and OLD.is_dir() and FULL.is_dir() and not BACKUP.exists() and not REPORT.exists()
    running=[(p.name(),p.pid) for p in psutil.process_iter() if any(x in p.name().lower() for x in ('hedgemodmanager','unleashedrecomp'))]
    assert not running,f'Please close game/HMM: {running}'
    build=json.loads(BUILD.read_text(encoding='utf8'))
    assert build['passed'] and build['version']=='1.0.5-review12'
    files={Path(p) for a in build['archiveDetails'] for p in a['archiveFiles']}
    files|={Path('TitleLogos/Custom/Loading/OPmovie_titlelogo_EN.dds'),
            Path('TitleLogos/Custom/Loading/OPmovie_titlelogo_JP.dds'),
            Path('README-1.0.5-REVIEW-KO.md'),Path('mod.ini')}
    assert len(files)==58,len(files)
    current=ini(FULL/'mod.ini');candidate=ini(NEW/'mod.ini')
    assert current['Desc']['Version'].strip('"')=='1.0.5-review11'
    assert candidate['Desc']['Version'].strip('"')=='1.0.5-review12'

    for file in files:
        assert (FULL/file).is_file() and (NEW/file).is_file()
        if file not in (Path('mod.ini'),Path('README-1.0.5-REVIEW-KO.md')):
            assert sha(FULL/file)==sha(OLD/file),file
    fixed={p:sha(FULL/p) for p in (
        Path('ConfigSchema.json'),Path('KoreanFullSetup.exe'),
        Path('TitleLogos/Korean/Loading/OPmovie_titlelogo_EN.dds'),
        Path('TitleLogos/Korean/+Title.ar.00'),
        Path('TitleLogos/Custom/+Title.ar.00'))}
    for file in files:
        dst=BACKUP/file;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(FULL/file,dst)
    try:
        for file in files-{Path('mod.ini'),Path('README-1.0.5-REVIEW-KO.md')}:
            shutil.copy2(NEW/file,FULL/file)
        ini_file=FULL/'mod.ini'
        raw=ini_file.read_text(encoding='utf-8-sig')
        assert raw.count('Version="1.0.5-review11"')==1
        ini_file.write_text(raw.replace('Version="1.0.5-review11"','Version="1.0.5-review12"',1),encoding='utf8')
        readme=FULL/'README-1.0.5-REVIEW-KO.md'
        raw=readme.read_text(encoding='utf8')
        assert raw.startswith('# 한국어 패치 1.0.5-review11 플레이 테스트 후보')
        raw=raw.replace('# 한국어 패치 1.0.5-review11 플레이 테스트 후보',
                        '# 한국어 패치 1.0.5-review12 플레이 테스트 후보',1)
        raw+='\n월드 어드벤처 오프닝 한국어 문구를 타이틀 화면 비율로 줄였습니다. '
        raw+='HD 미디어룸의 한글 테두리를 보강하고 HD 메뉴 그림 15장을 BC7로 압축했습니다. '
        raw+='HD 컷신 자막의 영문·문장부호 103개도 다시 그렸습니다.\n'
        readme.write_text(raw,encoding='utf8')
        assert all(sha(FULL/p)==sha(NEW/p) for p in files-{Path('mod.ini'),Path('README-1.0.5-REVIEW-KO.md')})
        assert all(sha(FULL/p)==v for p,v in fixed.items())
        installed=ini(FULL/'mod.ini')
        assert installed['Main']['IncludeDir3']==current['Main']['IncludeDir3']
        report={'passed':True,'version':'1.0.5-review12','edition':'Full',
                'installedMod':str(FULL),'backup':str(BACKUP),'filesChanged':len(files),
                'selectedLogo':installed['Main']['IncludeDir3'].strip('"'),
                'unchangedAssetsPreserved':True,'gameplayVerified':False,'publicRelease':False}
        REPORT.parent.mkdir(parents=True)
        REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print(json.dumps(report,ensure_ascii=False))
    except Exception:
        for file in files:shutil.copy2(BACKUP/file,FULL/file)
        raise
if __name__=='__main__':main()
