# Unleashed Recompiled 한국어 패치

소닉 언리쉬드의 대사·자막·월드맵·미션 설명·로딩·게임 내 UI를 한국어로 번역합니다. 현재 버전은 **1.0.6**입니다.

## iPhone / iPad — 한국어 포함 시험판

### 📥 [한국어 포함 iOS IPA 바로 다운로드 — 약 70MB](https://github.com/nonunsaram/unleashed-recompiled-korean/releases/download/ios-r1-ko-basic-1.0.6-test.1/SonicUnleashed-KoreanBasic-1.0.6-R1-Test1-unsigned.ipa)

위 링크를 누르면 앱 설치 파일인 IPA를 바로 받습니다. **한국어 패치가 들어 있으므로 한패 ZIP을 따로 풀거나 설정 파일을 고칠 필요가 없습니다.**

**비공식 시험판입니다.** 앱 빌드와 파일 검사는 완료했지만, 실제 iPhone/iPad에서 실행·한글 표시·플레이가 성공하는지는 아직 검증하지 않았습니다.

### 설치는 네 단계입니다

1. **IPA를 설치하세요.** 위 링크로 파일을 받은 뒤 본인이 사용하는 사이드로딩 도구로 서명하여 설치합니다. 배포 IPA에는 개인 서명이 없습니다.
2. **앱을 한 번 열고 닫으세요.** 앱 이름은 **Sonic Unleashed KO Test**입니다.
3. **본인의 게임 파일을 넣으세요.** 파일 앱에서 시험판 앱의 `UnleashedRecomp` 폴더에 복사합니다. 원본 R1과 같은 `game`, `update`, 선택 사항인 `dlc` 폴더 구조를 사용합니다.
4. **앱을 다시 실행하세요.** 앱이 한국어 패치를 자동으로 적용하고, 설치된 DLC에 맞는 월드맵도 알아서 적용합니다. 사용자가 따로 선택할 필요는 없습니다.

게임 원본과 세이브는 IPA에 포함하지 않습니다. 기존 R1과 별도 앱으로 설치되므로 기존 게임·세이브가 자동으로 넘어오지는 않습니다. 필요한 파일은 시험판 앱에 복사해 주세요.

첫 실행 기본 설정은 **English + 자막 켜기**입니다. 한패가 영어 게임 자산을 한국어로 바꿉니다. 앱 자체의 설정 화면, Windows 전체판의 추가 번역, UnleasHD는 포함하지 않습니다. 원본 R1의 GPU 오류를 해결한 버전도 아닙니다.

[시험판 설명·소스·검사 기록](https://github.com/nonunsaram/unleashed-recompiled-korean/releases/tag/ios-r1-ko-basic-1.0.6-test.1) · [원본 R1용 수동 설치 참고](https://github.com/nonunsaram/unleashed-recompiled-korean/releases/download/ios-r1-ko-basic-1.0.6-test.1/MANUAL-R1-REFERENCE-KO.md)

## Windows — 기본판 / 전체판 1.0.6

### 📥 [한국어 패치 다운로드 — GameBanana](https://gamebanana.com/mods/715787)

- **기본판(Basic)**: HMM으로 설치하는 한국어 모드입니다.
- **전체판(Full)**: 기본판에 더해 EXE의 옵션·도전과제 UI도 한국어로 바꿉니다. 공식 Windows x64 v1.0.3용입니다.

두 에디션 중 하나만 설치하세요. 게임 언어는 **English**, 자막은 **켜기**로 설정합니다.

[설치·설정·제거 안내](Release/v1.0.6/README-KO.md) · [English](Release/v1.0.6/README-EN.md) · [1.0.6 변경 내역](Release/v1.0.6/CHANGELOG-KO.md)

### UnleasHD와 함께 사용할 때

이 한패에는 **UnleasHD 원본·파생 이미지가 없습니다.** 게임 원본과 직접 만든 한국어 자료를 사용하며, 독립 업스케일 한국어 UI는 UnleasHD 없이도 쓸 수 있습니다.

UnleasHD 1440p를 별도로 설치했다면 HMM에서 아래 순서로 놓고, 한국어 패치 설정의 **업스케일 한국어 이미지**를 켜세요.

1. 한국어 패치
2. UnleasHD

## 소스와 제작 자료

이 저장소에는 문서·번역 카탈로그·제작 및 검사 스크립트를 공개합니다. 게임 데이터와 배포 파일은 Git에 커밋하지 않습니다. 전체판 Source.zip에는 수정 가능한 소스가 있으며, iOS 시험판의 변경 소스·패치·라이선스는 해당 릴리즈에 첨부했습니다.

[제작 안내](BUILDING.md) · [라이선스](LICENSE.md) · [제3자 고지](THIRD_PARTY_NOTICES.md)

[Windows 배포 ZIP 해시](Release/v1.0.6/SHA256SUMS.txt) · [검증 결과](Release/v1.0.6/verification.json) · [이미지 출처](Release/v1.0.6/PROVENANCE-KO.md)

1.0.6은 1.0.5와 같은 게임 자산을 사용하며, 설치기 검증과 구버전 전환을 수정했습니다. 이전 `Release` 폴더는 과거 기록입니다. review16 및 independent-anime1440 후보는 현재 최종 배포본이 아닙니다.
