"""Build the two install choices without modifying the game installation."""
from pathlib import Path
import json,shutil,subprocess,zipfile,hashlib,xml.etree.ElementTree as ET

R=Path(__file__).resolve().parents[1]
W=R/'Build/GameBanana-1.0.0'
O=R/'outputs/GameBanana-1.0.0'
ASSETS=R/'Build/FieldMission-v056'
OLD=R/'Build/GameBanana-0.4.18-Separated'
LOGO=R/'Assets/Installer/UnleashedRecompiledLogo.png'
VERSION='1.0.0'
VARIANTS=[
    ('AllDLC','Empire City & Adabat Adventure Pack',80,'전체 DLC / 엠파이어 시티·아다바트'),
    ('ApotosShamar','Apotos & Shamar Adventure Pack',60,'아포토스·샤마르'),
    ('Holoska','Holoska Adventure Pack',50,'홀로스카'),
    ('Mazuri','Mazuri Adventure Pack',40,'마주리'),
    ('Spagonia','Spagonia Adventure Pack',30,'스파고니아'),
    ('ChunNan','Chun-nan Adventure Pack',10,'춘난'),
    ('BaseGame','BaseGame',0,'DLC 없음'),
]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def make_ini(edition):
    description='대사·자막·월드맵·미션 선택·미션 로딩 한국어화. 전체 DLC 설치는 기본 설정으로 사용합니다.' if edition=='기본판' else '기본판 전체 + 옵션·도전과제 UI. 모드 폴더의 KoreanFullSetup.exe에서 .exe 한국어화 적용을 누르세요.'
    return f'''[Desc]
Author="nonunsaram"
Title="Korean Translation / 한국어 패치 — {edition}"
Version="{VERSION}"
Description="{description}"
Date="2026-09-10"
[Main]
ID="unleashed-recomp-korean"
IncludeDir0="WorldMapVariants/AllDLC"
IncludeDir1="."
IncludeDirCount=2
DependsCount=0
DLLFile=""
CodeFile=""
ConfigSchemaFile="ConfigSchema.json"
'''

def build():
    W.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
    basic=W/'Basic/UnleashedKorean';full=W/'Full/UnleashedKorean'
    shutil.copytree(ASSETS/'Mod',basic,dirs_exist_ok=True)
    shutil.copytree(OLD/'UnleashedKorean/Licenses',basic/'Licenses',dirs_exist_ok=True)
    manifests=[]
    for key,package,priority,title in VARIANTS:
        rel='game' if package=='BaseGame' else 'dlc/'+package
        source=ASSETS/'DirectArchives'/rel/'Languages/English'
        dest=basic/'WorldMapVariants'/key/'Languages/English';dest.mkdir(parents=True,exist_ok=True)
        files=[]
        for name in ['WorldMap.ar.00','WorldMap.arl']:
            shutil.copy2(source/name,dest/name)
            files.append(dict(name=name,sha256=sha(dest/name)))
        if package!='BaseGame':
            xml=R/'UnleashedRecomp-Windows/dlc'/package/'DLC.xml'
            assert int(ET.parse(xml).findtext('Priority'))==priority
        manifests.append(dict(key=key,package=package,priority=priority,files=files))
    schema={
        'IniFile':'mod.ini',
        'Groups':[{'Name':'Main','DisplayName':'DLC 구성','Elements':[{
            'Name':'IncludeDir0','DisplayName':'설치한 DLC',
            'Description':['모든 DLC를 설치했다면 기본값을 그대로 사용하세요.',
                '일부만 설치했다면, 설치한 팩 중 이 목록에서 가장 위에 있는 항목을 선택하세요.',
                '예: 춘난과 마주리만 설치했다면 마주리. DLC가 없으면 DLC 없음.',
                '번역 문구표만 선택하며 DLC를 추가하거나 게임 진행을 바꾸지 않습니다.'],
            'Type':'WorldMapVariant','DefaultValue':'WorldMapVariants/AllDLC','Value':'WorldMapVariants/AllDLC'
        }]}],
        'Enums':{'WorldMapVariant':[{'DisplayName':title,'Value':'WorldMapVariants/'+key,
            'Description':['설치한 팩 중 목록에서 가장 위에 있는 항목을 선택하세요.']} for key,package,priority,title in VARIANTS]}
    }
    (basic/'ConfigSchema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2),encoding='utf8')
    (basic/'mod.ini').write_text(make_ini('기본판'),encoding='utf8')
    (basic/'DLC-variants.json').write_text(json.dumps(manifests,ensure_ascii=False,indent=2),encoding='utf8')
    basic_readme='''# 한국어 패치 1.0.0 — 기본판

제작 nonunsaram · 제작 보조 GPT-6 Astra · Unleashed Recompiled v1.0.3 Windows x64

대사·자막·월드맵·미션 선택 설명·미션 로딩·게임 내 이미지 UI를 한국어화합니다.
게임 EXE와 XEX, 원래 게임 데이터 파일을 수정하지 않습니다. 옵션·도전과제 등 EXE에 포함된 UI까지 적용하려면 전체판을 선택하세요.

## 설치

1. GameBanana의 HMM 원클릭 설치를 사용하거나 이 ZIP을 HedgeModManager에 추가합니다.
2. 한국어 패치를 체크하고 저장합니다. 이전 한국어 모드는 함께 활성화하지 마세요.
3. 게임 화면 언어를 English로 설정하고 자막을 켭니다. 음성 언어는 원하는 설정을 유지하세요.

**모든 DLC가 설치되어 있다면 추가 설정이나 별도 설치 프로그램은 필요하지 않습니다.**
일부 DLC만 설치했다면 HMM의 이 모드 설정 → 설치한 DLC에서, 설치한 팩 중 목록의 가장 위 항목을 선택하고 저장하세요. DLC가 없으면 DLC 없음을 선택합니다. 예를 들어 춘난과 마주리만 있으면 마주리입니다.
DLC를 추가하거나 제거하면 이 선택도 확인하세요. 모드는 설치되어 있지 않은 DLC를 추가하지 않습니다.

## 제거·전환

HMM에서 체크를 해제하면 기본판이 적용되지 않습니다. 기본판과 전체판은 둘 중 하나만 사용하세요.
전체판에서 기본판으로 돌아올 때는 전체판 도구로 EXE·UI를 먼저 복원하세요.

월드맵 오른쪽 설명은 최대 12자·글꼴 폭 260 이내, 로딩 목표·설명은 공백 포함 18자를 기준으로 구분했습니다. 기존 번역의 의미·숫자·조건은 유지했습니다.
파일 구조와 설치·복원 동작을 검증한 1.0.0 배포본입니다. 잘못된 번역이나 표시를 발견하면 해당 화면과 지역·미션 이름을 함께 알려 주세요.
같은 글꼴·텍스트·UI 파일을 바꾸는 모드와 충돌할 수 있습니다. 출처와 글꼴 라이선스는 Licenses 폴더를 확인하세요.
비공식 한국어 패치이며 게임 본편·업데이트·DLC는 포함하지 않습니다.
'''
    (basic/'README-KO.md').write_text(basic_readme,encoding='utf8')
    (basic/'README-EN.md').write_text('''# Korean Translation 1.0.0 — Basic

Install this ZIP through HedgeModManager, enable the mod and save. Select English text and enable subtitles in the game; keep your preferred voice language.
All DLC installed: use the default mod configuration. No separate setup program is needed. If only some DLC is installed, open the mod configuration and choose the first installed pack from the list, or No DLC. The order is Empire City & Adabat, Apotos & Shamar, Holoska, Mazuri, Spagonia, Chun-nan, No DLC.
Includes dialogue, subtitles, world map, mission descriptions and loading text. It does not modify the game executable or original game files. Full adds the executable-based UI through its included setup utility. Install only one edition. Restore executable changes through Full before switching back to Basic.
Version 1.0.0 for Windows x64 v1.0.3. Package structure and installation behavior have been verified. Credits and font licenses: Licenses/.
''',encoding='utf8')
    shutil.copytree(basic,full,dirs_exist_ok=True)
    (full/'mod.ini').write_text(make_ini('전체판'),encoding='utf8')
    shutil.copytree(OLD/'KoreanOptionalUI/Support',full/'Support',dirs_exist_ok=True)
    manifest=json.loads((full/'Support/manifest.json').read_text())
    assert manifest['scope']=='native' and {f['relative'] for f in manifest['files']}=={'UnleashedRecomp.exe','patched/default.xex'}
    manifest['version']=VERSION
    (full/'Support/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    shutil.copy2(LOGO,full/'Support/InstallerLogo.png')
    cs=R/'Scripts/KoreanSupportSetup.cs'
    compiler='C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    subprocess.run([compiler,'/nologo','/target:winexe','/platform:x64','/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll','/reference:System.Web.Extensions.dll','/resource:'+str(LOGO)+',UnleashedRecompiledLogo','/out:'+str(full/'KoreanFullSetup.exe'),str(cs)],check=True)
    full_readme='''# 한국어 패치 1.0.0 — 전체판

기본판의 모든 번역과, 옵션·도전과제 등 EXE에 포함된 UI의 한국어화를 함께 제공합니다. 기본판 ZIP을 따로 받을 필요가 없습니다.

## 설치

1. 이 ZIP을 HMM으로 설치합니다. 다른 한국어 모드는 함께 활성화하지 마세요.
2. 게임을 종료합니다. HMM에서 모드 폴더를 열고 KoreanFullSetup.exe를 실행합니다.
3. 게임의 UnleashedRecomp.exe를 선택한 뒤 **.exe 한국어화 적용**을 누릅니다.
4. HMM에서 한국어 패치가 체크·저장되었는지 확인합니다.
5. 게임의 화면 언어 English, 자막 켜기를 확인합니다. 음성은 원하는 언어를 유지하세요.

모든 DLC가 설치되어 있으면 HMM 기본 설정을 사용합니다. 일부만 있으면 모드 설정의 DLC 목록에서 설치한 팩 중 가장 위 항목을 선택하세요. DLC가 없으면 DLC 없음입니다.
전체판의 추가 도구는 공식 Windows x64 v1.0.3의 EXE/XEX만 처리합니다. 원본 해시를 확인하고 백업한 다음 변경분을 적용합니다. 게임 월드맵 데이터·설정·음성·세이브·모드 체크 상태는 변경하지 않습니다.
기본판과 전체판의 대사·월드맵·로딩 데이터는 같습니다. EXE 추가 적용을 생략하면 기본판 범위로 동작합니다.

## 복원·제거

게임 종료 → KoreanFullSetup.exe → **.exe 원본 복원**. HMM 모드를 유지하면 월드맵·미션 로딩 등 기본 한국어화는 계속 적용됩니다.
완전히 제거하려면 이후 HMM에서도 한국어 패치를 해제하세요. HMM 해제만으로 EXE가 복원되지는 않습니다.
게임 폴더의 korean-native-backup은 복원에 필요하므로 보관하세요. 설치 후 다른 내용으로 변경된 파일은 덮어쓰지 않습니다.

제작 nonunsaram · 제작 보조 GPT-6 Astra · 기본 번역 범위·줄바꿈·호환성 안내는 BASIC-README-KO.md에 있습니다.
설치 도구와 패치 제작 소스: Source.zip. 출처·라이선스: Licenses 및 Support/Licenses.
게임·완성된 게임 EXE/XEX는 배포하지 않습니다. 이 도구는 본인 게임 파일에 변경분을 적용합니다.
'''
    (full/'BASIC-README-KO.md').write_text(basic_readme,encoding='utf8')
    (full/'README-KO.md').write_text(full_readme,encoding='utf8')
    (full/'README-EN.md').write_text('''# Korean Translation 1.0.0 — Full

Includes everything in Basic; do not install both. Install through HMM, then close the game. Open the mod folder, run KoreanFullSetup.exe, select UnleashedRecomp.exe and click .exe 한국어화 적용. Confirm that the mod is enabled and saved in HMM before playing. Official v1.0.3 Windows x64 only.
All DLC uses the default configuration. For partial/no DLC, use the mod configuration and select the first installed pack listed, or No DLC. Choose English text and enable subtitles; voice settings are preserved.
The setup utility backs up and patches only EXE/XEX. Click .exe 원본 복원 before removing the mod or switching to Basic. Restoring EXE/UI leaves HMM translation assets installed. Keep korean-native-backup for recovery.
Source.zip contains source and licenses. No completed game executable, game or DLC is included. File/install checks are separate from in-game validation.
''',encoding='utf8')
    source=full/'Source.zip'
    replacements=['KoreanSupportSetup.cs','package_hmm_release_v059.py','test_hmm_config_v059.ps1','verify_hmm_release_v059.py','inspect_dlc_archives_v059.ps1','inspect_loading_binary_v059.py','disassemble_reference_v059.py']
    with zipfile.ZipFile(R/'outputs/GameBanana-0.4.18-Separated/UnleashedRecompiled-Korean-0.4.18-Source.zip') as old,zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n in old.namelist():
            if n not in ['Source/Scripts/'+s for s in replacements] and n not in ('Source/BUILD-0.4.18.md','Source/README.md'):z.writestr(n,old.read(n))
        for s in replacements:
            path=R/'Scripts'/s
            if path.exists():z.write(path,'Source/Scripts/'+s)
        z.write(LOGO,'Source/Assets/InstallerLogo.png')
        z.writestr('Source/BUILD-1.0.0.md','Current packaging entry: Scripts/package_hmm_release_v059.py. Requires v056 translated assets and verified v057/v058 native deltas; original game files are not included. The other release packaging scripts are historical. Full setup is compiled from KoreanSupportSetup.cs WITHOUT DATA_SUPPORT. Basic has no setup executable. HMM ConfigSchema.json selects a preserved WorldMap variant by writing Main.IncludeDir0 in mod.ini. Replace Assets/Installer/UnleashedRecompiledLogo.png to update the setup logo.\n')
        z.writestr('Source/README.md','''# Korean Translation 1.0.0 source

This release has two installation choices: Basic and Full. Basic includes world-map and mission-loading translations in HMM. Full includes the same HMM assets and a setup utility that patches EXE/XEX only. There is no separate Basic-Data download.

Current packaging and verification entry points are package_hmm_release_v059.py, test_hmm_config_v059.ps1 and verify_hmm_release_v059.py. Earlier packaging scripts are retained as historical development source; they do not describe the current release structure. Read BUILD-1.0.0.md before rebuilding.

Existing translated v056 assets are preserved without merging conflicting DLC tables. Seven WorldMap variants match the original game's DLC priority choices. All DLC is the HMM default; partial/no DLC is selected through ConfigSchema.json. The default full setup build must not define DATA_SUPPORT.

The supplied translations, font build inputs, native patch sources, installer source and licenses support further editing. Rebuilding archives requires the user's own game extraction and the tools named in the scripts. Original game/DLC archives and completed game EXE/XEX files are not included.
''')
    post='''# Korean Translation / 한국어 패치

**제작 nonunsaram · 버전 1.0.0 · Unleashed Recompiled v1.0.3 Windows x64**

소닉 언리쉬드의 대사·자막·월드맵·미션 선택 설명·미션 로딩과 게임 내 UI를 한국어로 번역했습니다. 두 버전 중 하나를 선택하세요.

| 다운로드 | 적용 범위 | 설치 방법 |
|---|---|---|
| **기본판 — UnleashedRecompiled-Korean-1.0.0-Basic.zip** | 대사·자막·월드맵·미션 선택·미션 로딩·게임 내 이미지 UI | HMM 1-Click 설치 → 체크·저장 |
| **전체판 — UnleashedRecompiled-Korean-1.0.0-Full.zip** | 기본판 전체 + 옵션·도전과제 등 EXE에 포함된 UI | HMM 설치 → KoreanFullSetup.exe로 추가 적용 → HMM 체크·저장 |

**월드맵과 미션 로딩은 기본판에 포함됩니다. 기본판은 게임 EXE와 원래 게임 파일을 수정하지 않으며 별도 데이터 설치 프로그램이 필요하지 않습니다.**
전체판에는 기본판 내용도 들어 있으므로 두 버전을 중복 설치하지 마세요. 전체판의 EXE 추가 적용은 게임을 종료한 상태에서 진행합니다.

### 전체판 설치 순서

1. Full.zip을 HMM에 설치합니다.
2. 게임을 종료하고 모드 폴더의 KoreanFullSetup.exe를 실행합니다.
3. UnleashedRecomp.exe를 선택하고 **.exe 한국어화 적용**을 누릅니다.
4. HMM에서 한국어 패치를 체크·저장한 뒤 플레이합니다.

## 게임 설정과 DLC

화면 언어는 English, 자막은 켜기로 설정해 주세요. 음성은 원하는 언어를 사용하시면 됩니다.
**모든 DLC가 설치되어 있으면 기본 설정 그대로 사용하세요.** 일부만 설치했다면 HMM의 모드 설정에서 설치한 DLC 중 목록의 가장 위 항목을 선택하세요. DLC가 없으면 DLC 없음입니다. DLC 자체는 이 패치에 포함되지 않습니다.
월드맵의 좁은 오른쪽 설명과 미션 로딩은 서로 다른 문구 항목과 줄바꿈 기준을 사용합니다.

## 제거

기본판은 HMM에서 해제하면 됩니다. 전체판은 KoreanFullSetup.exe에서 **.exe 원본 복원**을 누른 뒤 HMM에서 해제하세요. EXE만 복원하고 모드를 유지하면 기본판 범위의 한국어화가 유지됩니다. korean-native-backup 폴더를 보관하세요.
같은 텍스트·글꼴·UI를 수정하는 모드는 함께 사용하지 않는 편을 권장합니다. 이전 한국어 모드를 중복 활성화하지 마세요.

## 안내와 출처

파일 구조와 설치·복원 동작을 검증한 1.0.0 배포본입니다. 잘못된 번역이나 표시를 발견하면 해당 화면과 지역·미션 이름을 함께 알려 주세요.
전체판의 실행 파일 지원은 공식 Windows x64 v1.0.3용입니다. 완성된 게임 EXE/XEX를 배포하지 않고 사용자의 파일을 확인한 뒤 변경분만 적용합니다.
Credits: nonunsaram · 제작 보조: GPT-6 Astra · Unleashed Recompiled: hedge-dev · HedgeModManager: hedge-dev / SuperSonic16 · Fonts: LINE Seed KR, 샌드박스 어그로체.
라이선스는 각 ZIP에, 수정 가능한 소스는 전체판의 Source.zip에 포함되어 있습니다. 비공식 패치입니다.

English: Choose one edition. Basic installs through HMM and includes world-map and mission-loading translation without modifying the game executable. Full includes Basic plus executable-based options/achievements UI; run KoreanFullSetup.exe in the mod folder, select UnleashedRecomp.exe and click .exe 한국어화 적용. Confirm the mod is enabled and saved in HMM before playing. Choose English text and enable subtitles. All DLC uses the default configuration; partial/no DLC can be selected in the HMM mod configuration. Click .exe 원본 복원 before removing Full. Version 1.0.0 for Windows x64 v1.0.3.
'''
    (O/'GameBanana-post.md').write_text(post,encoding='utf8')
    (O/'Upload-guide-KO.md').write_text('''# GameBanana 업로드 안내

제목: Korean Translation / 한국어 패치
제작자: nonunsaram
버전: 1.0.0
대상 게임: Unleashed Recompiled
본문: GameBanana-post.md 전체

## 다운로드는 두 개만 등록합니다

1. UnleashedRecompiled-Korean-1.0.0-Basic.zip — 기본판: EXE 수정 없이 월드맵·미션 로딩 포함. 기본 다운로드 및 HMM 원클릭 대상으로 지정하세요.
2. UnleashedRecompiled-Korean-1.0.0-Full.zip — 전체판: 기본판 전체 + 옵션·도전과제 등 EXE UI. HMM으로 설치한 뒤 포함된 KoreanFullSetup.exe의 추가 적용이 필요합니다. 기본판과 중복 설치하지 않는다고 표시하세요.

Source.zip은 전체판 안에 포함되어 있으므로 별도 설치 선택지로 등록하지 않습니다. 예전 Basic-Data / Optional-UI / Optional-Support 파일은 올리지 마세요.
SHA256SUMS.txt는 다운로드 무결성 확인용이며 설치 파일이 아닙니다.

## 게시 전 마지막 확인

현재 작업에서는 게임을 실행하지 않았습니다. 준비한 실제 게임에서 월드맵 오른쪽 설명·미션 로딩·보스 설명을 확인하고 실제 플레이 스크린샷을 첨부해 주세요. 전체판 EXE/UI는 이전 번역 변경분을 유지하며 설치·복원 검사를 별도로 기록합니다.
게시 후 GameBanana가 생성하는 원클릭 버튼이 Basic.zip과 올바른 게임을 가리키는지 확인하세요. 게시 전에는 사이트의 실제 파일 ID가 없어 원격 원클릭 링크를 검증할 수 없습니다. 임의 파일 ID나 다운로드 링크는 만들지 않았습니다.
게임·DLC·완성된 게임 실행 파일은 포함하지 않습니다. 자동 게시를 수행하지 않았습니다.
''',encoding='utf8')
    archives=[]
    for edition,root in [('Basic',basic),('Full',full)]:
        path=O/f'UnleashedRecompiled-Korean-{VERSION}-{edition}.zip'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for f in sorted(root.rglob('*')):
                if f.is_file():z.write(f,'UnleashedKorean/'+f.relative_to(root).as_posix())
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            assert len([n for n in z.namelist() if n.endswith('/mod.ini')])==1
            for f in root.rglob('*'):
                if f.is_file():assert z.read('UnleashedKorean/'+f.relative_to(root).as_posix())==f.read_bytes()
        archives.append(dict(file=path.name,sha256=sha(path),bytes=path.stat().st_size))
    (O/'SHA256SUMS.txt').write_text(''.join(a['sha256']+'  '+a['file']+'\n' for a in archives),encoding='ascii')
    preview=O/'KoreanFullSetup-preview.png'
    subprocess.run([str(full/'KoreanFullSetup.exe'),'--preview',str(preview)],check=True)
    exploded=True
    try:
        shutil.copytree(full,O/'UnleashedKorean',dirs_exist_ok=True)
    except shutil.Error as error:
        exploded=False
        print('Warning: skipped the open file in the convenience copy:',error)
    (O/'package-verification.json').write_text(json.dumps(dict(version=VERSION,install_downloads=2,archives=archives,worldmap_variants=manifests,basic_has_setup_executable=False,exploded_full_folder=exploded,setup_preview=preview.name,game_launched=False,published=False),indent=2),encoding='utf8')
    print(json.dumps(archives))

if __name__=='__main__':build()
