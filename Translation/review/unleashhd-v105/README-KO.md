# UnleasHD 1.4.2 (1440p) UI 호환 검토

## 원인

기존 한국어 패치는 `Compatibility/UnleasHD-1.4.2` 옵션에서 월드맵의 고해상도 텍스처 두 개만 제공했습니다. 기본 한국어 레이어는 `mat_playscreen_en_001.dds`, `mat_playscreen_en_002.dds`, `mat_result_en_001.dds` 같은 영문 전용 UI 아틀라스까지 원래 해상도로 덮어쓰고 있었습니다. `mat_status_en_001.dds`에는 한국어 `종료` 한 부분만 있는데 전체 저해상도 아틀라스가 들어 있어 `SPEED`, `RING ENERGY`도 흐려졌습니다. 숫자는 별도 이미지에 있어 선명할 수 있습니다.

## 수정

설치된 UnleasHD 1.4.2 1440p의 UI 아틀라스를 바탕으로 14개 아카이브에 겹치는 텍스처 43개만 고해상도로 구성했습니다. 한국어 표기가 있는 15개에는 기존 149개 라벨 자료 중 해당 라벨을 원본 해상도 비율에 맞게 다시 그렸습니다. 영문만 있는 28개는 UnleasHD 원본 바이트를 그대로 복사했습니다. 기존 월드맵 호환 텍스처 두 개도 유지했습니다. 전체 UnleasHD 모드의 모델·효과·설정은 포함하지 않았습니다.

새 호환 파일은 `Build/Development-v105-Review/UnleashedKorean/Compatibility/UnleasHD-1.4.2`에 있습니다. 생성 방법은 `Scripts/build_unleashhd_ui_compat_v105.py`, 사용한 전체 라벨 스냅샷은 `ui-textures-ko-v104-full.json`, 텍스처별 SHA-256·크기·아카이브 왕복 검증은 `Build/UnleasHD-Compatibility-v105-HUD2/verification.json`에 있습니다. `ui-check.png`로 문제 제보에 나온 HUD와 결과 화면의 이미지를 확인했습니다.

## 적용 범위와 확인 사항

- 대상: UnleasHD **1.4.2 1440p**. 다른 해상도판은 별도 자산으로 다시 생성·검증해야 합니다.
- 모드 매니저에서 한국어 패치를 UnleasHD보다 위에 두고 `UnleasHD 호환`을 선택한 뒤 저장하고 게임을 다시 시작합니다.
- 아카이브 14개와 텍스처 43개의 정적 검사 및 팩/언팩 왕복 검증을 통과했습니다. 게임 내 실제 장면은 아직 확인하지 않았습니다.
- 전체 DDS 겹침 대조에서 17개가 남습니다. 15개는 한국어 글꼴 아틀라스이고 2개는 한국어로 번역된 테일즈 이벤트 이미지라 영문 HD 파일로 덮으면 번역이 사라집니다. 자세한 목록은 `residual-conflicts.json`에 있습니다. 따라서 모든 시각 요소의 충돌 해제까지 검증된 상태는 아닙니다.
- 공개 재배포 전에는 UnleasHD 제작진의 자산 사용 조건을 확인해야 합니다. 이번 산출물은 설치된 모드에서 만든 로컬 검토 후보입니다.
