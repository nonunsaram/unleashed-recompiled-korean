# 빌드 안내

v1.0.1은 EXE만 처리하는 새 백엔드입니다. [Full 백엔드 감사](Release/v1.0.1/FULL-BACKEND-AUDIT.md)에 조사 근거와 검증 범위를 기록했습니다. 아래 v1.0.0 제작 단계는 기존 입력을 설명하는 역사 자료이며, 현행 진입점은 아래 v1.0.1 절차를 사용하세요.

이 저장소는 v1.0.0 제작에 사용한 번역·설치 도구·패치 소스를 공개하고 변경 지점을 재현할 수 있게 구성했습니다. 게임에서 추출한 데이터와 완성된 게임 바이너리는 포함하지 않습니다. 따라서 아래 절차는 두 범위로 나뉩니다.

1. 공개 트리만으로 가능한 작업: JSON 검사, 설치 도구 컴파일, Unleashed Recompiled 소스 패치 적용 확인, 공개 파일 안전성 검사
2. 사용자가 직접 준비한 게임 추출물이 필요한 작업: 글꼴/텍스트 리소스 생성, EXE/XEX 차이 패치 생성, HMM용 Basic/Full ZIP 재패키징

## 대상과 기준 버전

- 한국어 패치: `1.0.1`
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

Windows에 포함된 64비트 .NET Framework C# 컴파일러를 사용합니다. UI와 엔진 두 파일 및 검증 manifest를 함께 컴파일해야 합니다. `DATA_SUPPORT`와 `TEST_FAULTS`는 배포 빌드에 정의하지 않습니다.

```powershell
New-Item -ItemType Directory -Force .\out | Out-Null
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" `
  /nologo /target:winexe /platform:x64 `
  /reference:System.Windows.Forms.dll `
  /reference:System.Drawing.dll `
  /reference:System.Web.Extensions.dll `
  /resource:.\Assets\Installer\UnleashedRecompiledLogo.png,UnleashedRecompiledLogo `
  /resource:.\Release\v1.0.1\manifest.json,KoreanFullManifest `
  /out:.\out\KoreanFullSetup.exe `
  .\Scripts\KoreanSupportSetup.cs .\Scripts\KoreanSupportEngine.cs
```

`out/`과 생성된 실행 파일은 `.gitignore` 대상입니다. 이 컴파일은 설치 도구 자체만 만들며 설치용 `Support/manifest.json` 및 차이 패치는 생성하지 않습니다.

## v1.0.1 작업·검증 순서

Python 3.12 및 `pefile`, `capstone`, `keystone-engine`, `bsdiff4`가 필요합니다. 공개 소스만으로 가능한 모의 설치 검사는 `python Scripts/test_full_backend_v101.py`입니다. 결과는 새 `Build/FullBackend-Tests-*` 폴더에 남습니다. 공개 배포 트리 검사는 이 테스트 산출물을 포함하지 않는 깨끗한 소스 트리에서 실행하세요.

로컬 게임/검증된 v1.0.0 제작 입력이 있을 때:

1. `python Scripts/build_native_korean_exe_v101.py` — 보존된 v056 한국어 EXE에 도전과제 호출 변경을 추가. 원본 XEX를 읽거나 쓰지 않음.
2. `python Scripts/build_full_backend_v101.py` — 공식 원본 EXE → 새 EXE delta 생성·검사, manifest 내장 설치 도구 컴파일.
3. `python Scripts/test_full_release_v101.py` — 실제 크기 EXE를 별도 폴더에서 설치·재설치·복원. 기존 v1.0.0 도구를 이용한 전환도 검사.
4. `python Scripts/package_hmm_release_v101.py` — 체크섬을 확인한 v1.0.0 Basic ZIP의 데이터를 유지하고 새 Full 도구/문서를 결합. 출력 폴더가 이미 있으면 중단하며 `--output`으로 새 경로 지정 가능.
5. `python Scripts/verify_package_v101.py` — 최종 ZIP, 내장 소스, 데이터 보존 및 추출한 설치 도구의 실제 설치·복원을 검사.

필수 로컬 입력은 `Build/CleanOriginals-v057/UnleashedRecomp.exe`, `Build/FieldMission-v056/Native/UnleashedRecomp.exe`, 기존 v1.0.0 Basic/Full ZIP, 전환 검사에 사용하는 원본 XEX와 기존 Full 도구입니다. 이 입력은 Git으로 배포하지 않습니다. `build_native_korean_exe_v101.py`는 기존 한국어 EXE의 해시를 고정하고 있으므로 앞 단계의 임의 산출물로 대체하지 마세요.

출력은 `Build/FullBackend-v101`, `outputs/GameBanana-1.0.1`이며 실제 게임 설치 폴더를 수정하지 않습니다. `Scripts/package_hmm_release_v059.py` 및 이전 단계는 v1.0.0 당시 코드로 보존했으며 현행 두 파일 엔진을 컴파일하는 진입점이 아닙니다. 과거 설치기 소스는 `Scripts/legacy/KoreanSupportSetup-v100.cs`에 따로 보존합니다.

복원은 설치 도구의 내장 manifest와 게임 폴더의 검증된 EXE 백업만 사용합니다. `Support/manifest.json`을 임의로 수정해 지원 대상을 늘릴 수 없습니다. 지원 빌드를 추가하려면 정확한 원본과 결과를 검증하고 manifest·설치 도구를 함께 다시 생성해야 합니다.

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

현행 배포 파일은 1.0.2 Basic·Full ZIP과 SHA256SUMS.txt입니다. ZIP은 GameBanana에 게시하며 저장소에 커밋하지 않습니다. GitHub에는 소스와 설명서, [`Release/v1.0.2/manifest.json`](Release/v1.0.2/manifest.json), 검증 결과 및 [`Release/SHA256SUMS.txt`](Release/SHA256SUMS.txt)를 게시합니다. 새 수정 배포는 이전 ZIP을 보관하고 검증한 새 파일과 체크섬을 함께 교체합니다.

## 재현성 한계

공개된 패치와 변경 소스는 Unleashed Recompiled 코드 변경을 재현할 수 있고, 설치 도구 소스도 독립적으로 컴파일할 수 있습니다. 그러나 게임 추출물을 배포하지 않으므로 공개 저장소만으로 v1.0.0 ZIP을 비트 단위로 완전히 재생성하는 것은 지원하지 않습니다. 이 문서는 법률 자문이 아니며, 원본 게임 자료와 제3자 구성요소를 재배포하기 전에는 각 조건을 별도로 확인해야 합니다.

## v1.0.1 번역 개정 빌드

`review_translation_v101.py`는 현재 번역과 변경 목록을 검증하고, 합법적으로 준비한 `Catalog-Reviewed/all-lines.json`이 있으면 실제 리소스 위치 입력을 만듭니다. `build_translation_resources_v101.ps1`은 검증된 v1.0.0 Basic 아카이브에 새 대사를 적용하며, 공통 글꼴 metric과 원본 일본어 컷씬 FCO/FTE/DDS가 필요합니다. `subtitle_resource_functions.ps1`과 `patch_opening_atlas.py`는 자막 글꼴·메시지 직렬화를 담당합니다.

```powershell
python Scripts/review_translation_v101.py
pwsh -NoProfile -File Scripts/build_translation_resources_v101.ps1
python Scripts/build_native_korean_exe_v101.py
python Scripts/build_full_backend_v101.py
python Scripts/verify_translation_review_v101.py
python Scripts/package_hmm_release_v101.py --output outputs/GameBanana-1.0.1-Reviewed
python Scripts/verify_package_v101.py --output outputs/GameBanana-1.0.1-Reviewed
```

최신 패키징은 `Build/Translation-v101/resource-verification.json`의 원본·결과 해시와 일치하는 34개 아카이브 파일만 교체합니다. 과거 Basic ZIP을 그대로 복사하는 것만으로는 이번 번역 수정이 들어가지 않습니다. 출력 폴더가 이미 있으면 다른 이름을 사용하여 기존 후보를 보존하세요.

`extend_native_font_v101.py`는 보존된 EXE의 글꼴 스냅샷/텍스처에 누락된 혹을 추가합니다. Python의 numpy, Pillow, scipy, zstandard와 LINE Seed KR Regular/Bold가 필요합니다. 기존 글꼴을 통째로 다시 배치하지 않습니다.


## v1.0.2 영문 자막 수정 배포 (2026-09-14)

사용자가 확인한 `Dr.`·`Excellent!` 수정본을 같은 버전에 반영합니다. [자막 점검 및 생성 순서](Translation/review/latin-baseline/README-KO.md)의 1–9단계를 완료한 뒤 `package_hmm_release_v102.py`, `verify_package_v102.py`를 실행합니다. 기존 출력 폴더는 먼저 보관해야 합니다. 자막 생성 중간 결과와 게임 원본은 Git에 포함하지 않습니다.

패키징은 기존 1.0.2 번역 변경 뒤에 검증된 자막 16개 묶음을 덮어씌웁니다. 이전 리소스 해시, 수정본 해시, Basic/Full 일치 및 인게임에서 확인한 HMM 설치본과의 일치를 검사합니다. 버전은 1.0.2이며 manifest의 revision은 `20260914-subtitle-baseline`으로 구분합니다. 이전 릴리스 소스는 커밋 `c3cd9f0`에 남아 있습니다. ZIP은 GameBanana 업로드용이고 GitHub에는 소스·설명서·체크섬을 게시합니다.
