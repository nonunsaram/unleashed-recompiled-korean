# Korean Translation / 한국어 패치 v1.0.1

Unleashed Recompiled v1.0.3 Windows x64용 비공식 한국어 패치입니다.

- **Basic:** HMM에 설치 → 한국어 패치 체크·저장. 대사·자막·월드맵·미션 설명·로딩 번역이 포함됩니다. 별도 EXE 설치 도구가 필요 없습니다.
- **Full:** Basic의 모든 내용 + 옵션·도전과제 등 네이티브 UI. **Basic을 먼저 설치할 필요는 없습니다.**

## v1.0.1 수정 내역

- 도전과제·옵션 설명의 웨어혹 표기 14곳 수정.
- 칩의 원문 이름형 자기 지칭 33항목 및 지역별 중복 대사 수정.
- 소닉 영어 대사 재검사 및 No Reason의 Hey! 한 곳 수정.
- XEX 검사·수정 제거, 실제 설정 저장 경로 자동 탐색, Basic 선행 설치 오해를 막는 오류 안내.
- Denoised와 함께 사용하면 한국어 모드를 맨 위에 배치하도록 안내. 현재 해당 모드는 제작자가 비공개로 전환하여 조합 재현은 미완료.

v1.0.1 Full은 Windows EXE만 패치합니다. 도전과제 번역을 EXE로 옮겨 XEX 변종 때문에 설치가 거부되던 원인을 제거했습니다. 설치·재설치·복원과 중간 실패 복구를 다시 구현했고, 설정·음성 언어·세이브·다른 모드 체크 상태는 변경하지 않습니다.

**Full 설치:** 게임을 한 번 실행해 초기 설정 완료 → Full ZIP을 HMM에 설치 → 게임 종료 → 모드 폴더의 `KoreanFullSetup.exe` 실행 → 게임의 `UnleashedRecomp.exe` 선택 → **.exe 한국어화 적용** → HMM 체크·저장.

**이전 v1.0.0 Full 사용자:** 먼저 이전 도구로 **.exe 원본 복원**을 실행한 후 새 Full을 설치하세요. 이전 Full의 변경을 남기지 않기 위한 전환 절차입니다. 기존 백업은 삭제하지 마세요.

화면 언어는 English, 자막은 켜기로 설정합니다. 음성은 원하는 언어를 유지하세요. 모든 DLC가 있으면 기본 모드 설정을 사용하고, 일부만 있으면 설치한 팩 중 목록의 가장 위 항목을 고릅니다. DLC가 없으면 DLC 없음을 선택합니다.

Full 제거·Basic 전환 전에는 새 도구의 **.exe 원본 복원**을 실행하세요. 게임 폴더의 `korean-native-backup`을 보관해야 합니다. 다른 버전·플랫폼·개인 빌드 EXE는 지원 범위에 포함되지 않습니다.

게임·업데이트·DLC·완성된 게임 실행 파일은 포함하지 않습니다. 자세한 안내는 ZIP의 README-KO.md / README-EN.md, 출처·라이선스는 Licenses, 검증 소스는 Source.zip에 있습니다.

제작 nonunsaram · 제작 보조 GPT-6 Astra · Unleashed Recompiled hedge-dev · HedgeModManager hedge-dev / SuperSonic16 · Fonts LINE Seed KR, 샌드박스 어그로체.

English: Choose Basic or Full. Basic installs through HMM alone. Full includes Basic and now patches only the verified Windows v1.0.3 EXE; it never modifies the XEX. Launch the game once and finish initial setup, install Full through HMM, close the game, then run KoreanFullSetup.exe from the mod folder. Upgrading from v1.0.0 Full requires restoring with the old utility first. Choose English text and enable subtitles; keep your preferred voice language. Restore the EXE before removing Full or switching to Basic.
