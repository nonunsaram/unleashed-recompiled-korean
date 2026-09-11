# Unleashed Recompiled 한국어 패치

**공식 배포처: [GameBanana](https://gamebanana.com/mods/715787)** · 이 GitHub 저장소는 소스 코드와 제작 기록을 공개하는 곳이며, GitHub Releases에는 배포 ZIP을 올리지 않습니다.

**Unleashed Recompiled v1.0.3 Windows x64**용 비공식 한국어 패치의 소스 저장소입니다. 게임 본편, 업데이트, DLC, 완성된 게임 실행 파일은 포함하지 않습니다.

## 배포판

| 구분 | 적용 범위 | 설치 방식 |
| --- | --- | --- |
| 기본판 (Basic) | 대사, 자막, 월드맵, 미션 선택 설명, 미션 로딩, 게임 내 이미지 UI | HedgeModManager로 설치한 뒤 모드를 체크하고 저장 |
| 전체판 (Full) | 기본판 전체 + 옵션·도전과제 등 실행 파일에 포함된 UI | HMM 설치 후 모드 폴더의 `KoreanFullSetup.exe`로 추가 적용 |

두 배포판은 함께 설치하지 않습니다. 전체판에는 기본판의 내용이 모두 들어 있습니다. 설치 파일은 [GameBanana 공식 배포 페이지](https://gamebanana.com/mods/715787)에서 받고, 기준 SHA-256 값은 [`Release/SHA256SUMS.txt`](Release/SHA256SUMS.txt)에서 확인할 수 있습니다.

## 설치

### 기본판

1. Basic ZIP을 HedgeModManager(HMM)에 추가합니다.
2. 한국어 패치를 체크하고 저장합니다. 이전 한국어 패치는 함께 활성화하지 않습니다.
3. 게임의 화면 언어를 **English**, 자막을 **켜기**로 설정합니다. 음성 언어는 원하는 설정을 유지할 수 있습니다.

모든 DLC를 설치했다면 기본 설정을 사용합니다. 일부 DLC만 설치했다면 HMM의 모드 설정에서 설치한 팩 중 목록의 가장 위 항목을 선택하고, DLC가 없다면 `DLC 없음`을 선택합니다. 이 설정은 번역 문구표만 고르며 DLC를 추가하지 않습니다.

### 전체판

1. Full ZIP을 HMM에 설치하고 게임을 종료합니다.
2. HMM에서 모드 폴더를 열고 `KoreanFullSetup.exe`를 실행합니다.
3. 게임 폴더의 `UnleashedRecomp.exe`를 선택한 뒤 **.exe 한국어화 적용**을 누릅니다.
4. HMM에서 한국어 패치가 체크·저장되었는지 확인합니다.

전체판 설치 도구는 지원되는 v1.0.3 파일의 해시를 확인하고 EXE/XEX만 백업·변경합니다. 제거하거나 기본판으로 바꾸기 전에는 게임을 종료하고 설치 도구에서 **.exe 원본 복원**을 실행한 뒤 HMM에서 모드를 해제하세요. 복원에 필요한 `korean-native-backup` 폴더를 보관해야 합니다.

## 저장소 내용

- `Translation/`: v1.0.0 번역 카탈로그와 네이티브 UI 대응표
- `Scripts/`: 설치 도구, 현재 v059 패키징·검증 코드, 해당 결과를 만든 네이티브·미션 빌드 단계
- `Patches/`: Unleashed Recompiled v1.0.3 소스 변경 패치와 변경된 두 파일
- `Tools/Fonts/`: LINE Seed KR 글꼴 빌드 입력
- `Assets/Installer/`: 전체판 설치 도구에 포함되는 로고
- `Licenses/`: 구성요소별 라이선스 원문
- `Release/`: GameBanana 공식 배포 파일의 이름과 체크섬만 기록하며 ZIP 자체는 Git으로 추적하지 않음

빌드 전에는 [BUILDING.md](BUILDING.md)를 읽어 주세요. 원본 게임에서 추출한 입력과 일부 도구는 저작권 및 용량 문제로 저장소에 포함하지 않았으므로, 현재 공개 트리만으로 배포 ZIP을 완전히 재생성할 수는 없습니다. 포함·제외 기준은 [SOURCE_SELECTION.md](SOURCE_SELECTION.md)에 기록되어 있습니다.

## 크레딧과 권리

- 한국어 패치: nonunsaram
- 제작 보조: GPT-6 Astra
- Unleashed Recompiled: hedge-dev
- HedgeModManager: hedge-dev / SuperSonic16
- 글꼴: LINE Seed KR, 샌드박스 어그로체

직접 제작한 코드·문서·한국어 번역 기여분은 MIT로 재사용할 수 있습니다. Unleashed Recompiled 관련 변경 소스는 GPL-3.0, 글꼴은 OFL 등 각각의 조건을 따릅니다. 범위와 예외는 [LICENSE.md](LICENSE.md)와 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)를 확인해 주세요. Sonic the Hedgehog와 관련 명칭·상표·게임 자료의 권리는 각 권리자에게 있습니다.

## English summary

This repository contains source material for the unofficial Korean translation patch for **Unleashed Recompiled v1.0.3, Windows x64**. The official distribution channel for installable packages is [GameBanana](https://gamebanana.com/mods/715787); GitHub Releases are intentionally not used. Basic installs through HedgeModManager and does not patch the game executable. Full includes Basic plus executable-based UI translation through `KoreanFullSetup.exe`. Install only one edition; restore Full's EXE changes before removing it or switching to Basic. No game, update, DLC, completed EXE/XEX, or extracted game archive is included. The project's original code, documentation, and Korean translation contributions are MIT-licensed within the scope stated in [LICENSE.md](LICENSE.md); third-party components retain their own terms.
