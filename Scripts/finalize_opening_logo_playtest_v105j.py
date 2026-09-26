"""Replace interim RGBA DDS overlays with source-compatible DXT5 and repack."""

from pathlib import Path
import hashlib
import json
import shutil
import zipfile


ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'Build/OPLogoInvestigation'
STAGED=ROOT/'Build/Development-v105j-Playtest/UnleashedKorean'
INSTALLED=ROOT/'UnleashedRecomp-Windows/mods/UnleashedKorean'
ZIP=ROOT/'outputs/UnleashedRecompiled-Korean-1.0.5-Review10-LocalPlaytest.zip'
STAGED_REPORT=STAGED.parent/'verification.json'
INSTALLED_REPORT=ROOT/'Build/HMM-Install-v105j-Playtest/verification.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    build=json.loads((WORK/'build-report.json').read_text(encoding='utf8'))
    assert STAGED.is_dir() and INSTALLED.is_dir() and ZIP.is_file()
    assert json.loads(STAGED_REPORT.read_text(encoding='utf8'))['passed']
    assert json.loads(INSTALLED_REPORT.read_text(encoding='utf8'))['passed']
    changed=[]
    for variant in ('Korean','Custom'):
        for lang in ('EN','JP'):
            relative=Path('TitleLogos')/variant/'Loading'/f'OPmovie_titlelogo_{lang}.dds'
            source=WORK/'Variants'/variant/'Loading'/relative.name
            data=source.read_bytes()
            assert len(data)==921728 and data[84:88]==b'DXT5'
            assert digest(source)==build[variant][f'{lang}sha256']
            for root in (STAGED,INSTALLED):
                target=root/relative
                old=target.read_bytes()
                assert len(old)==3686528 and old[84:88]!=b'DXT5'
                shutil.copy2(source,target)
                assert digest(target)==digest(source)
            changed.append(relative.as_posix())
    temp=ZIP.with_name(ZIP.stem+'-repack.tmp')
    assert not temp.exists()
    files=sorted(p for p in STAGED.rglob('*') if p.is_file())
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for p in files:
            archive.write(p,'UnleashedKorean/'+p.relative_to(STAGED).as_posix())
    with zipfile.ZipFile(temp) as archive:
        assert archive.testzip() is None and len(archive.namelist())==len(files)
    temp.replace(ZIP)
    staged=json.loads(STAGED_REPORT.read_text(encoding='utf8'))
    staged.update(zipSha256=digest(ZIP),ddsFormat='BC3_UNORM / legacy DXT5',
                  originalDdsFormatMatched=True)
    STAGED_REPORT.write_text(json.dumps(staged,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    installed=json.loads(INSTALLED_REPORT.read_text(encoding='utf8'))
    installed.update(ddsFormat='BC3_UNORM / legacy DXT5',
                     originalDdsFormatMatched=True,
                     verifiedTextureHashes={p:digest(INSTALLED/p) for p in changed})
    INSTALLED_REPORT.write_text(json.dumps(installed,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'passed':True,'textures':changed,'ddsFormat':'DXT5',
                      'basicZipSha256':digest(ZIP),'fullInstalled':True},ensure_ascii=False))


if __name__=='__main__':main()
