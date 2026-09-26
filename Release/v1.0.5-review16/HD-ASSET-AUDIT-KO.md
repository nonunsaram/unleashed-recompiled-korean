# review16 중복 제거와 UnleasHD 허락 요청 범위

2026-09-26 · 로컬 검토 후보. 공개 배포 허락을 받은 버전이 아닙니다.

## 제외한 것 / 유지한 것

- 제외: 무수정 HD UI 28개와 영어·일본어 원본 타이틀 그림 4개. 경로별 파일 수이며, 동일 그림의 중복 경로를 포함합니다.
- 함께 제외: 해당 HD UI를 가리던 게임 원본 복사본 28개. 28개 모두 번역되지 않은 원본 게임 파일과 바이트 단위로 같음을 확인했습니다.
- 유지: 한국어 HD UI 15개, 월드맵 UI 2개, 대화 이름표 1개, DLC 미리보기 수정본 1개, 한국어 추가 타이틀 그림 4개. 총 **23개 경로**의 UnleasHD 파생 그림이며, 정확한 목록은 CSV에 있습니다.
- 유지: 직접 만든 한국어 글꼴·자막과 게임 원본 기반 한국어 오프닝 로고. 모든 유지 리소스는 review15와 동일합니다.

## 아래에 UnleasHD를 놓았을 때

HMM에서 한국어 패치를 위에, UnleasHD 1.4.2 1440p를 아래에 놓고 **한국어 UI 해상도 → UnleasHD UI (1440p용)**을 선택합니다. 번역용 수정본은 한국어 패치가 제공하고, 제외한 무수정 UI는 아래 HD 모드가 제공합니다. 실제 설치된 HD 모드에서 32개 공급 파일을 추출해 존재·내용·크기를 확인했습니다. DLC 7가지와 로고 5가지의 파일 우선순위 조합도 확인했습니다.

같은 이미지 파일은 두 모드의 픽셀이 자동 합성되지 않습니다. 따라서 한국어가 들어간 수정본은 계속 필요하며, 이번에 그것을 제거하지 않았습니다. 영어·일본어 원본 로고는 이미지 없이 장면 선택만 남겼습니다. 아래 HD 모드가 없으면 게임 원본이 제공하고, 있으면 해당 HD 모드의 로고 해상도를 따릅니다. 현재 1440p판은 로고 2048×1024, 발광 1280×1280입니다. 종전 패키지의 원본 로고 복사본은 4K판에서 가져온 3072×1536 / 1920×1920이었습니다.

이 검사는 파일과 로더 구조에 대한 검사입니다. 실제 게임의 모든 화면을 플레이 검증했다는 의미는 아닙니다. 기존 일본어 글자 페이지 15장의 추가 검증은 사용자 지시에 따라 생략합니다.

## DM 문장 수정

“The Korean patch does not include any other HD textures”는 피해야 합니다. 한국어 문구 수정 외에 DLC 미리보기 수정본과 한국어 추가 타이틀 그림도 포함되기 때문입니다. 다음처럼 1.0.5-review16에만 한정해 쓰면 범위가 명확합니다.

> For the v1.0.5 review16 candidate, I have removed the unchanged UnleasHD texture copies. The remaining UnleasHD-derived graphics are the Korean-edited UI, nameplate and optional Korean title-logo atlases, plus a world-map preview atlas with a DLC-preview correction. Other UnleasHD graphics are loaded from the separately installed mod. I can provide the exact list of these 23 file instances for review.

기존 공개 1.0.4 파일은 이 작업으로 변경하지 않았습니다. 그 버전에는 무수정 HD 원본 로고와 수정본이 모두 남아 있으므로, 기존 배포 건에 대한 허락 요청·사과는 계속 필요합니다.
