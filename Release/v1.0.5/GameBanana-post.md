# 소닉 언리쉬드 한국어 패치 1.0.5

대사·자막·월드맵·미션 선택 설명·미션 로딩과 게임 내 UI를 한국어로 번역한 비공식 패치입니다.

## 기본판과 전체판

- **기본판**: 일부 UI를 제외한 게임 내 한국어화. HMM으로 설치하며 게임 EXE와 원래 게임 파일을 수정하지 않습니다.
- **전체판**: 기본판 전체 + 옵션·도전과제 등 EXE에 포함된 UI. HMM 설치 후 `KoreanFullSetup.exe`로 추가 적용합니다. EXE 한국어화는 **공식 Windows x64 v1.0.3**을 지원합니다.

전체판에는 기본판 내용이 포함되어 있습니다. 둘 중 하나만 설치하고 이전 한국어 모드는 중복 활성화하지 마세요.

## 설치

**기본판**

1. HedgeModManager(HMM)을 설치합니다.
2. GameBanana의 `unleashedrecompiled-korean-105-basic.zip`을 HMM 1-Click Install로 설치합니다. 수동 설치 시 ZIP의 `UnleashedKorean` 폴더를 게임의 `mods` 폴더에 넣습니다.
3. HMM에서 한국어 패치를 체크하고 저장합니다.

**전체판**

1. HMM으로 `unleashedrecompiled-korean-105-full.zip`을 설치합니다. 수동 설치 방법은 기본판과 같습니다.
2. **게임을 한 번 실행했다가 종료합니다.** 초기 설정 파일이 생성되어 있어야 합니다.
3. 설치한 모드 폴더의 `KoreanFullSetup.exe`를 실행합니다.
4. `UnleashedRecomp.exe`를 선택하고 **.exe 한국어화 적용**을 누릅니다.
5. HMM에서 한국어 패치를 체크하고 저장합니다.

## 게임·모드 설정

화면 언어는 **English**, 자막은 **켜기**로 설정해 주세요. 음성은 자유롭게 선택할 수 있으며, 번역은 일본어를 기준으로 했습니다.

HMM의 한국어 패치 톱니바퀴에서 다음 항목을 설정합니다.

- **설치한 DLC**: 설치한 DLC 중 목록에서 가장 위의 항목을 선택합니다. 전체 DLC를 설치했다면 기본값을 유지하고, DLC가 없으면 **DLC 없음**을 선택합니다.
- **업스케일 한국어 이미지**: 기본값은 **끄기 — 기본 한국어 UI**입니다. 고해상도 한국어 UI를 사용하려면 **켜기 — 독립 업스케일 / UnleasHD 1440p 호환**을 선택합니다. **UnleasHD 없이도 사용할 수 있습니다.**
- **타이틀·오프닝 로고**: 원하는 로고를 선택합니다. **게임 기본값**은 게임 또는 다른 모드의 로고를 사용합니다.

설정을 저장한 뒤 게임을 완전히 종료하고 다시 실행해 주세요.

## 권장 모드 구성과 순서

1. **Korean Translation / 한국어 패치**
2. **UnleasHD (1440p)**

UnleasHD는 별도로 설치하는 선택 모드입니다. 함께 사용하면 한국어 패치의 **업스케일 한국어 이미지**를 켜고, 두 모드의 DLC 설정을 실제 설치 구성에 맞춰 주세요.

**1.0.5에서는 UnleasHD 모드의 모든 에셋을 제외했습니다.** UnleasHD 원본 이미지와 이를 수정한 파생 이미지 모두 포함하지 않습니다. 게임 원본과 직접 만든 한국어 자료만 사용하며, 한국어가 들어가는 이미지만 독립 업스케일 또는 자체 렌더링으로 제공합니다. 번역하지 않은 UI는 아래 모드 또는 게임 원본이 제공합니다. 배경·캐릭터·사물은 변경하지 않습니다.

## 제거

기본판은 HMM에서 해제합니다. 전체판은 `KoreanFullSetup.exe`의 **.exe 원본 복원**을 실행한 뒤 HMM에서 해제합니다. EXE만 복원하고 모드를 유지하면 기본판 범위의 한국어화가 유지됩니다. `korean-native-backup` 폴더를 보관해 주세요.

같은 텍스트·글꼴·UI를 수정하는 모드는 함께 사용하지 않는 편을 권장합니다.

## 확인 사항과 출처

사용자 인게임 확인을 완료했습니다. 한국어 패치와 UnleasHD를 함께 사용하는 구성 및 UnleasHD를 끈 상태의 독립 업스케일 한국어 UI를 확인했습니다. 모든 하드웨어·모드 조합을 보증하는 것은 아닙니다. 번역이나 표시 문제는 화면과 지역·미션 이름을 함께 알려 주세요.

완성된 게임 EXE/XEX를 배포하지 않으며, 전체판은 사용자의 실행 파일을 확인한 뒤 변경분만 적용합니다. 라이선스는 각 ZIP의 `Licenses`에, 수정 가능한 번역·설치 도구·제작 스크립트는 전체판의 `Source.zip`에 포함됩니다. 게임 원본 자료는 소스에 포함하지 않습니다.

Credits: nonunsaram / GPT-6 Astra · 한국어 로고: **프랑사랑단** · Unleashed Recompiled: hedge-dev · HedgeModManager: hedge-dev / SuperSonic16 · Fonts: LINE Seed KR, 샌드박스 어그로체 · 게임 원본 기반 업스케일: Real-ESRGAN x4plus-anime.

---

# Unleashed Recompiled Korean Translation 1.0.5

Choose one edition. Basic translates dialogue, subtitles, world-map and mission text, and in-game UI through HMM without modifying the game executable. Full includes Basic plus executable-based options and achievements UI, supporting official Windows x64 v1.0.3.

## Installation

1. Install either `unleashedrecompiled-korean-105-basic.zip` or `unleashedrecompiled-korean-105-full.zip` through HMM. For manual installation, extract `UnleashedKorean` into the game's `mods` directory.
2. Full only: run the game once and close it, run `KoreanFullSetup.exe` inside the mod directory, select `UnleashedRecomp.exe`, and click **.exe 한국어화 적용**.
3. Enable the Korean mod and save in HMM. Use English text and enable subtitles. Any voice language can be used; the translation is based on Japanese.

## Configuration

Select the installed DLC and preferred title/opening logo in the HMM mod settings. The default DLC setting is All DLC. With partial DLC, select the highest listed installed DLC; with none, select DLC 없음.

**업스케일 한국어 이미지** is off by default. Turn it on for independently upscaled Korean UI, either standalone or alongside separately installed UnleasHD 1440p. Save settings and fully restart the game.

Recommended mod order:

1. Korean Translation
2. UnleasHD (1440p)

**All UnleasHD assets have been removed from this patch**, including original and modified UnleasHD images. Images use game originals and our own Korean artwork. Only Korean-containing images receive the optional upscale or custom rendering. Other UI comes from the lower-priority mod or game. Backgrounds, characters and objects are unchanged.

## Removal and credits

Disable Basic in HMM. For Full, click **.exe 원본 복원** before disabling the mod; retain `korean-native-backup`. Restoring only the EXE while keeping the mod enabled retains Basic coverage. Do not enable multiple versions of the Korean patch.

User playtesting confirmed the UnleasHD combination and standalone upscaled Korean UI. Licenses are included in both editions; editable translation, installer and production sources are in Full's `Source.zip`. Original game assets and finished game executables are not included in that source archive. This is an unofficial patch.

Credits: nonunsaram / GPT-6 Astra; Korean logo: 프랑사랑단; Unleashed Recompiled: hedge-dev; HMM: hedge-dev / SuperSonic16; Fonts: LINE Seed KR and SB Aggro; original-game upscaling: Real-ESRGAN x4plus-anime.
