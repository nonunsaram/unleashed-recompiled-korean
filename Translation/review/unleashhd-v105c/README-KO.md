# UnleasHD 1.4.2 1440p 호환 우선순위 수정

2026-09-25 플레이 화면에서는 숫자가 선명하고 `TIME`, `SCORE`, `SPEED`, `RINGS`, `RING ENERGY`가 흐렸다. 1.0.5-review2에는 고해상도 아카이브가 포함돼 있었지만, `mod.ini`의 `IncludeDir1="."`이 `IncludeDir2="Compatibility/UnleasHD-1.4.2"`보다 앞에 있었다. [Unleashed Recompiled 모드 로더](https://github.com/hedge-dev/UnleashedRecomp/blob/main/UnleashedRecomp/mod/mod_loader.cpp)는 모드와 IncludeDir을 순서대로 순회하며 `+*.arl` 및 `+*.ar`을 불러온다. 먼저 읽은 저해상도 한국어 텍스처가 남은 것이 화면과 일치한다.

1.0.5-review3에서는 `IncludeDir1`을 UnleasHD 호환 경로, `IncludeDir2`를 기본 모드 경로로 교체했다. HMM 설정 스키마의 호환 옵션도 `IncludeDir1`을 제어하도록 변경했다. 월드맵 DLC 선택과 전체판 설치 파일은 유지한다.

## 고해상도 한국어 UI 범위

- 14개 아카이브의 UI 텍스처 43개를 호환 레이어에서 먼저 읽는다.
- 일반 UI의 한국어 문구 122개가 담긴 15개 텍스처는 UnleasHD 크기에 맞춰 다시 그린 기존 결과를 사용한다. 상점 `구매`·`판매`도 여기에 포함된다.
- 나머지 영문 UI 텍스처 28개는 설치된 UnleasHD 1.4.2의 원본 고해상도 파일이다.
- 월드맵 한국어 문구 27개를 담은 기존 고해상도 텍스처 2개도 호환 레이어에 보존돼 있다.
- HUD 예시 텍스처는 128×128에서 256×256으로, 상점 텍스처는 256×128에서 512×256으로 바뀐다.

새 설정과 파일은 정적으로 검증했으나 게임 화면에서 선명도가 개선됐는지는 재실행 후 다시 확인해야 한다. 한국어 글꼴 아틀라스 15개와 테일즈 이벤트 이미지 2개는 별도 고해상도 재작업 대상이다. 현재 시험 ZIP은 UnleasHD 자산을 포함한 로컬 검토용이며 공개 재배포용이 아니다.
