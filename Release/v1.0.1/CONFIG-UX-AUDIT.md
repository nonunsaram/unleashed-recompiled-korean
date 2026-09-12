# v1.0.1 config UX 조사 및 검증

## 조사 결과

기준 upstream: `cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c` (v1.0.3).

- [main.cpp](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/main.cpp): 시작 중 `Config::Load()` 호출. 최초 게임 데이터 설치 완료 후에만 생성되는 파일이 아니다.
- [config.cpp](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/user/config.cpp): `GetConfigPath()`는 `GetUserPath()/config.toml`. `Load()`는 파일이 없으면 즉시 `Save()`하고 반환한다. 실행 전에는 파일이 없어도 정상이며 저장 실패 시 생성되지 않을 수 있다. 파일 존재 자체가 게임 데이터 설치 완료를 증명하지 않는다.
- [paths.cpp](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/user/paths.cpp), [paths.h](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/user/paths.h): EXE 옆 `portable.txt`가 있으면 EXE 폴더, 없으면 Windows Roaming AppData의 `UnleashedRecomp` 폴더. 작업 디렉터리를 기준으로 config를 찾지 않는다. 비활성 경로의 config로 대체하지 않는다.

현재 v1.0.0 `KoreanSupportSetup.cs`에는 `Language="English"`, `Subtitles=true` 상수와 `SetConfig`, `ConfigValue`, `configBefore`가 남아 있었지만 호출·저장 경로가 없다. 실제 config 변경 값은 **없으며**, config 복원도 하지 않는다. 과거 `test_gamebanana_setup.py`는 0.4.14용으로 현재 동작의 증거가 아니다. 현재 패키징 문서도 사용자가 English/자막을 설정하도록 안내한다.

따라서 게임 루트 config를 직접 수정할 필요는 없다. v1.0.1은 읽기 전용 검사를 유지하고 올바른 실제 경로를 탐색한다. 사용하지 않는 변경 함수를 제거했다. 최종 백엔드에서는 `configBefore`와 기존 state 역직렬화도 제거했다. 설치 전 값은 설정을 전혀 쓰지 않으므로 정확히 유지되고, 설치 후 사용자가 변경한 값도 복원 시 유지된다. 음성 언어는 변경하지 않는다.

## 구현 범위 (최종 EXE 전용 백엔드 기준)

EXE 없음, 활성 config 없음, `[System]`의 Language/Subtitles 누락·중복·미지원 값에 별도 오류를 표시한다. 이 검사는 전체 TOML 파서가 아니며 모든 구문 손상을 판별한다고 보장하지 않는다. upstream 저장 형식의 필수 설정을 검사하며 임의 key 삽입이나 config 재작성을 하지 않는다. 최종 구현은 `KoreanSupportEngine.cs`로 분리했고 XEX 접근을 제거했다. EXE 선택과 직접 입력 모두 부모 폴더를 사용한다. 설정 파일은 게임과 같은 사용자 경로에서 찾고 EXE 백업은 게임 루트를 기준으로 찾는다. 원본 복원은 설정이 없어도 가능하다.

## 검증

`python Scripts/test_full_backend_v101.py`

가짜 EXE와 자체 생성 delta를 사용하며 게임 파일은 사용하지 않는다. 결과는 `Build/FullBackend-Tests-*/verification.json`에 남는다. 초기 config 전용 검사를 포함한 전체 백엔드 모의 검사 38개가 통과했다. 설정 관련 검증 범위:

1. 최초 실행 전 config 없음: 구체적인 실행·종료 안내, 쓰기 없이 중단.
2. 올바른 config: 설치·재설치·복원 성공, EXE 해시 확인.
3. EXE 없는 폴더: 별도 오류, 쓰기 없이 중단.
4. Language 또는 Subtitles 누락, 다른 섹션, 중복 키, 미지원 값: 쓰기 없이 중단.
5. config의 원래 바이트(BOM·주석·음성 포함) 보존, 설치 이후 바꾼 설정도 복원 시 보존. 모드·세이브 sentinel 보존.
6. Basic: 패키징 소스에서 Full에만 설치 도구를 배치함을 검사. Basic의 HMM 실행 검증은 별도 필요.
7. portable/nonportable 경로 선택 확인. 실제 AppData config는 읽거나 수정하지 않았다.

추가된 EXE/XEX 감사, 실제 파일 설치·복원 및 사용자 게임 실행 결과는 [FULL-BACKEND-AUDIT.md](FULL-BACKEND-AUDIT.md)를 따른다. 설정 검사를 통과했다는 사실만으로 게임 데이터 설치가 완료되었거나 모든 구간이 정상임을 보장하지 않는다.

## 패키징

`Scripts/package_hmm_release_v101.py`는 검증된 Basic 데이터와 새 EXE 전용 설치 도구를 결합한다. Full README는 이 폴더의 README-KO.md와 README-EN.md를 복사한다. 기존 v059 및 v1.0.0 ZIP은 변경하지 않는다.
