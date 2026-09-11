# 빌드 안내

이 저장소는 v1.0.0 제작에 사용한 번역·설치 도구·패치 소스를 공개하고 변경 지점을 재현할 수 있게 구성했습니다. 게임에서 추출한 데이터와 완성된 게임 바이너리는 포함하지 않습니다. 따라서 아래 절차는 두 범위로 나뉩니다.

1. 공개 트리만으로 가능한 작업: JSON 검사, 설치 도구 컴파일, Unleashed Recompiled 소스 패치 적용 확인, 공개 파일 안전성 검사
2. 사용자가 직접 준비한 게임 추출물이 필요한 작업: 글꼴/텍스트 리소스 생성, EXE/XEX 차이 패치 생성, HMM용 Basic/Full ZIP 재패키징

## 대상과 기준 버전

- 한국어 패치: `1.0.0`
- 대상: Unleashed Recompiled `1.0.3` Windows x64
- upstream 저장소: <https://github.com/hedge-dev/UnleashedRecomp>
- upstream 기준 커밋: `cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c`
- 소스 변경: [`Patches/unleashed-recomp-v1.0.3-korean.patch`](Patches/unleashed-recomp-v1.0.3-korean.patch)

## 공개 트리 검사

Windows PowerShell에서 저장소 루트를 기준으로 실행합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\validate_public_tree.ps1
```

이 검사는 JSON 구문, 100 MiB 초과 파일, 금지된 게임/빌드 파일 형식, ZIP 혼입, 재분석 지점, 개인 로컬 경로와 일반적인 비밀키 형식을 확인합니다.

## Unleashed Recompiled 소스 변경 재현

```powershell
git clone --recursive https://github.com/hedge-dev/UnleashedRecomp.git
Set-Location UnleashedRecomp
git checkout cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c
git submodule update --init --recursive
git apply --check ..\unleashed-recompiled-korean\Patches\unleashed-recomp-v1.0.3-korean.patch
git apply ..\unleashed-recompiled-korean\Patches\unleashed-recomp-v1.0.3-korean.patch
```

패치는 다음 두 파일만 변경합니다.

- `UnleashedRecomp/ui/button_guide.cpp`: 한국어 `도전과제` 안내의 렌더링 품질·색상 보정
- `UnleashedRecomp/user/config.cpp`: 영어 텍스트 슬롯을 한국어로 표시하되 음성 언어와 저장 값은 유지

검토 편의를 위해 패치 적용 후의 파일도 `Patches/modified/`에 함께 두었습니다. 패치가 적용 기준이며, 두 사본은 패치 결과와 바이트 단위로 일치해야 합니다. upstream 자체의 빌드는 upstream의 `docs/BUILDING.md`를 따르세요.

## 전체판 설치 도구 컴파일

Windows에 포함된 64비트 .NET Framework C# 컴파일러를 사용합니다. `DATA_SUPPORT` 기호를 정의하면 현재 v1.0.0의 범위를 벗어나므로 정의하지 않습니다.

```powershell
New-Item -ItemType Directory -Force .\out | Out-Null
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" `
  /nologo /target:winexe /platform:x64 `
  /reference:System.Windows.Forms.dll `
  /reference:System.Drawing.dll `
  /reference:System.Web.Extensions.dll `
  /resource:.\Assets\Installer\UnleashedRecompiledLogo.png,UnleashedRecompiledLogo `
  /out:.\out\KoreanFullSetup.exe `
  .\Scripts\KoreanSupportSetup.cs
```

`out/`과 생성된 실행 파일은 `.gitignore` 대상입니다. 이 컴파일은 설치 도구 자체만 만들며 설치용 `Support/manifest.json` 및 차이 패치는 생성하지 않습니다.

## 번역 및 네이티브 리소스 단계

핵심 입력은 `Translation/`, `Tools/Fonts/`, `Build/PlayableModWork/common-atlas.json`에 있습니다. 관련 단계는 다음과 같습니다.

1. `Scripts/build_native_korean_resources.py`
2. `Scripts/build_native_korean_exe.py`
3. `Scripts/prepare_mission_loading_v054.py`
4. `Scripts/build_mission_loading_v054.ps1`
5. `Scripts/prepare_field_mission_v056.py`
6. `Scripts/build_field_mission_v056.ps1`
7. `Scripts/build_clean_release_deltas_v057.py`
8. `Scripts/package_hmm_release_v059.py`
9. `Scripts/test_hmm_config_v059.ps1`
10. `Scripts/verify_hmm_release_v059.py`

이 스크립트들은 릴리스 제작 당시의 단계명과 디렉터리를 그대로 보존한 감사 가능한 소스입니다. 일부는 이전 단계에서 만든 `Build/` 산출물을 입력으로 사용하므로 새 체크아웃에서 곧바로 연속 실행되는 독립 빌드 시스템은 아닙니다.

필요한 Python 패키지에는 `bsdiff4` 1.2.6, `pefile`, `capstone`, `keystone-engine`, `numpy`, `Pillow`, `scipy`, `zstandard`가 포함됩니다. PowerShell 단계는 Converse/Amicitia 계열 라이브러리와 HedgeArcPack을 사용합니다. HedgeModManager 설정 검사는 별도의 HedgeModManager 소스가 필요합니다. 이 도구와 라이브러리는 이 저장소에 번들하지 않았습니다.

## 의도적으로 제외한 필수 비공개 입력

다음 파일은 원본 게임에서 추출된 대량 데이터이거나 그 파생 입력이므로 GitHub에 올리지 않습니다.

- `Build/PlayableModWork/common-input.json` — 155,412,696바이트
- `Build/PlayableModWork/mission-fields-v056-input.json` — 80,032,466바이트
- `Build/FieldMission-v056/` 및 이전 단계의 생성된 게임 아카이브
- `Build/GameBanana-0.4.18-Separated/`의 생성된 모드/패치 산출물
- 사용자의 `UnleashedRecomp.exe`, `patched/default.xex`, DLC 및 업데이트 파일

이 입력을 재구성하려면 합법적으로 보유한 게임·DLC에서 직접 추출해야 합니다. 서로 다른 게임 버전이나 해시를 억지로 통과시키지 마세요. 스크립트의 원본 SHA-256 검사는 지원 범위를 고정하고 잘못된 파일 수정을 막기 위한 장치입니다.

## 릴리스 산출물 확인

공식 v1.0.0 Release에는 다음 세 파일만 첨부합니다.

- `UnleashedRecompiled-Korean-1.0.0-Basic.zip`
- `UnleashedRecompiled-Korean-1.0.0-Full.zip`
- `SHA256SUMS.txt`

ZIP은 저장소에 커밋하지 않습니다. 기존 검증된 ZIP을 다시 빌드하거나 수정하지 않고 그대로 업로드하며, 업로드 후 내려받은 파일을 [`Release/SHA256SUMS.txt`](Release/SHA256SUMS.txt)와 다시 대조합니다.

## 재현성 한계

공개된 패치와 변경 소스는 Unleashed Recompiled 코드 변경을 재현할 수 있고, 설치 도구 소스도 독립적으로 컴파일할 수 있습니다. 그러나 게임 추출물을 배포하지 않으므로 공개 저장소만으로 v1.0.0 ZIP을 비트 단위로 완전히 재생성하는 것은 지원하지 않습니다. 이 문서는 법률 자문이 아니며, 원본 게임 자료와 제3자 구성요소를 재배포하기 전에는 각 조건을 별도로 확인해야 합니다.
