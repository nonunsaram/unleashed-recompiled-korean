# 공개 소스 선별 기록

이 문서는 v1.0.0 공개 저장소에 무엇을 넣고 뺐는지, 그 이유를 기록합니다. 작업용 프로젝트 전체를 GitHub에 올리지 않고 이 전용 트리만 게시하는 것이 전제입니다.

## 포함

- `Scripts/KoreanSupportSetup.cs`: Full 배포판의 설치·복원 도구 소스
- `Scripts/package_hmm_release_v059.py`, `test_hmm_config_v059.ps1`, `verify_hmm_release_v059.py`: v1.0.0의 최종 패키징 및 검증 진입점
- v054~v058 네이티브·미션 생성/검증 스크립트: 최종 v059 입력이 만들어진 경로를 감사하고 재구성하기 위한 현행 제작 소스
- `Translation/`의 최종 번역 카탈로그: 대사·자막·UI·도전과제와 네이티브 UI 대응 정보
- `Build/PlayableModWork/common-atlas.json`: 줄바꿈 및 글꼴 폭 계산에 필요한 소형 메트릭 입력
- `Tools/Fonts/LINESeedKR-*.ttf`: 네이티브 한국어 글꼴 생성에 실제 사용하는 재배포 가능 입력
- `Assets/Installer/UnleashedRecompiledLogo.png`: Full 설치 도구 컴파일에 포함되는 리소스
- `Patches/`: 정확한 upstream 커밋용 패치와 변경 후 파일 사본
- `Licenses/`: GPL-3.0, OFL, bsdiff4 BSD, 샌드박스 어그로체 조건
- `Release/SHA256SUMS.txt`: GameBanana 공식 배포 파일 두 개의 무결성 기준

## 제외

- 프로젝트 루트의 약 7.8GB ISO와 `Installer Sources/`: 게임 본편 또는 그 링크/복사본
- `Sonic Unleashed DLC Pack [Xbox 360]/`, `Update File/`: DLC와 업데이트
- `UnleashedRecomp-Windows/`: 설치된 게임, EXE/XEX, 설정과 사용자 환경
- `Analysis/`, `QA Saves/`, `korean-smoke-test/`, `SpreadsheetBuild/`: 분석 자료, 세이브, 검수/중간 산출물
- `Tools/`의 실행 파일·런타임·캐시: 제3자 바이너리와 로컬 도구 환경. OFL 글꼴만 별도 선별
- `Build/` 전체(명시적으로 포함한 `common-atlas.json` 제외): 생성된 게임 아카이브, 네이티브 바이너리, 테스트 픽스처와 로그
- `outputs/`의 ZIP, 펼친 모드 폴더, `Source.zip`, 미리보기와 검증 작업 경로: 릴리스 산출물은 GitHub에 올리지 않고 GameBanana 공식 배포처에서만 게시
- `Build/PlayableModWork/common-input.json`(155,412,696바이트)과 `mission-fields-v056-input.json`(80,032,466바이트): GitHub 대용량 제한과 원본 게임 데이터 노출을 피하기 위해 제외
- upstream 전체 복제와 `.git`: 정확한 기준 커밋, 적용 가능한 패치, 변경된 파일과 재현 문서로 대체
- `__pycache__/`, 패키지 캐시, 임시 파일, 빌드 출력

## 제외한 과거 패키징 코드

기존 `Source.zip`에 누적되어 있던 다음 코드는 과거 0.4.x 배포 구조를 만들기 위한 것이며 v1.0.0의 현재 구조를 설명하지 않으므로 제외했습니다.

- `assemble_gamebanana_release.py`
- `package_gamebanana_release.py`
- `test_gamebanana_setup.py`
- `package_clean_release_v057.py`
- `package_separated_release_v058.py`
- `test_separated_release_v058.py`
- `build_gamebanana_deltas.py`

이전 단계 번호가 붙은 나머지 스크립트는 단순 역사 보존이 아니라 v1.0.0용 최종 자산과 패치를 만드는 입력 단계이므로 포함했습니다.

## 알려진 한계와 결정 필요 사항

1. 번역 카탈로그에는 대조·위치 식별에 필요한 일본어/영어 원문 일부가 포함됩니다. 저작권자가 작성한 한국어 번역 기여분만 MIT 범위이며, 게임 원문·식별자·제3자 권리는 허락하지 않습니다.
2. 프로젝트 전용 코드·문서·한국어 번역 기여분은 MIT로 공개합니다. GPL/OFL 등 제3자 조건과 섞지 않으며, 게임 원문·에셋·상표에는 이용 허락을 부여하지 않습니다.
3. 게임 추출물을 제외했기 때문에 배포 ZIP의 완전한 원클릭 재현 빌드는 제공하지 않습니다. 변경 소스, 설치 도구와 제작 단계는 검토할 수 있습니다.
4. 설치 도구 로고는 프로젝트 식별용으로 포함했으며, 관련 상표에 대한 별도 이용 허락을 부여하지 않습니다.

## v1.0.1 추가

Full 백엔드(`KoreanSupportEngine.cs`), EXE 도전과제 번역 생성기, delta/설치기 빌드, 모의 실패·실제 파일·ZIP 검증 스크립트, 한·영 설치 안내 및 감사 기록을 포함합니다. 이전 설치기 원문은 `Scripts/legacy`에 보존합니다. 내장용 `Release/v1.0.1/manifest.json`은 해시·길이·경로만 포함하며 게임 데이터는 없습니다. 로컬 게임·진행된 QA 세이브·검수 실행 폴더와 테스트 바이너리는 계속 제외합니다.


## v1.0.4 추가

로고 처리·설정·패키징·검증 소스, 프랑사랑단 제공 한국어 로고 원본, 로고 출처와 검증 기록을 포함합니다. 이전에 제외한 시험 제작 로고는 계속 제외합니다. UnleasHD의 생성 타이틀 아카이브·DDS는 Git에 넣지 않으며 출처와 고정 커밋을 기록합니다.
