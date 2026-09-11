# 제작 스크립트

## v1.0.0 최종 단계

- `package_hmm_release_v059.py`: Basic/Full 구조와 HMM 설정을 조립한 최종 패키징 진입점
- `test_hmm_config_v059.ps1`: HMM 설정 스키마의 선택값 왕복 검사
- `verify_hmm_release_v059.py`: ZIP 구조, DLC 우선순위, 설치·복원·거부·롤백 동작 검사
- `KoreanSupportSetup.cs`: Full 전용 EXE/XEX 설치·복원 도구
- `inspect_dlc_archives_v059.ps1`, `inspect_loading_binary_v059.py`, `disassemble_reference_v059.py`: 최종 DLC/바이너리 정적 검사

## 최종 입력 생성 단계

v054~v058 이름의 나머지 파일은 미션 로딩, 필드 설명, 네이티브 리소스와 검증된 차이 패치를 만드는 데 사용했습니다. 단계 번호는 릴리스 역사 표기가 아니라 최종 v1.0.0 입력의 제작 계보를 보존하기 위해 유지합니다.

스크립트의 경로는 저장소 루트를 기준으로 하며, 일부는 의도적으로 제외된 개인 게임 추출물 및 생성된 `Build/` 단계에 의존합니다. 실행 전 [BUILDING.md](../BUILDING.md)의 재현성 한계와 요구 입력을 확인하세요.
