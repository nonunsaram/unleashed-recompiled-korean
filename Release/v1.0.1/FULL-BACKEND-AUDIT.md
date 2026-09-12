# v1.0.1 Full 백엔드 감사·설계·검증

## 결론

v1.0.0의 XEX 패치는 도전과제 번역을 담당하므로 그대로 삭제하면 번역이 사라진다. v1.0.1은 그 기능을 Windows EXE의 공통 도전과제 문자열 호출로 옮겼다. 새 설치·복원 엔진과 manifest는 EXE만 처리하며 XEX 경로를 읽거나 쓰지 않는다. XEX가 없거나 다른 내용이어도 패처의 설치·복원 결과는 동일하다. 게임 자체의 데이터·업데이트 호환성 검사는 공식 게임의 책임으로 남는다.

사용자는 별도 테스트 환경의 **새 EXE + 검증된 원본 XEX + HMM 한국어 데이터** 조합에서 옵션, 화면/음성 언어, 도전과제, 게임 시작·자막, 일시정지·버튼 안내가 정상이라고 확인했다. HMM 연결 전에는 게임 본문이 영어이고 옵션·도전과제만 한국어인 것도 확인했다. 이는 데이터 모드와 EXE 번역이 각각 적용된다는 결과와 일치한다.

현재 지원 EXE는 공식 **Windows x64 v1.0.3 한 빌드**다. XEX 변종 때문에 거부되는 문제를 없앤 것이지 모든 Windows EXE·게임 버전·개인 빌드에 강제 적용하는 기능은 아니다. 실제 다른 지역/디지털 XEX 전부를 확보하여 플레이 검증한 것은 아니다.

## 확인한 원본 소스

Unleashed Recompiled 기준 커밋: `cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c`.

- [공식 저장소](https://github.com/hedge-dev/UnleashedRecomp)
- [installer.cpp](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/install/installer.cpp): 파일별 알려진 XXH3 해시 검사, 업데이트 적용, game/update 호환성 검사.
- [game.cpp](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/install/hashes/game.cpp), [update.cpp](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/install/hashes/update.cpp): XEX/XEXP 각각 4개 해시.
- [EU GoD 해시 추가 커밋](https://github.com/hedge-dev/UnleashedRecomp/commit/8915b06a95ad95e1eac3ebe41ccc87efebfbd2dc): `Add EU GoD game and Title Update hashes (#543)`.
- [main.cpp](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/main.cpp): `LdrLoadModule`에서 XEX 리소스로 `g_xdbfWrapper` 초기화.
- [achievement_menu.cpp](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/ui/achievement_menu.cpp), [achievement_overlay.cpp](https://github.com/hedge-dev/UnleashedRecomp/blob/cf829a9eca8fb680fba4b0409ddeb6ca92f22e3c/UnleashedRecomp/ui/achievement_overlay.cpp): 메뉴는 `GetAchievements`, 알림은 `GetAchievement` 사용.
- [XDBFWrapper](https://github.com/hedge-dev/XenonRecomp/blob/c5bfd90d87f2ed0db8cff5c19ea3aff0e161e527/XenonUtils/xdbf_wrapper.cpp): 두 경로 모두 `GetString(language, id)`로 이름·해제 설명·잠금 설명 조회. 이 커밋은 기준 upstream의 XenonRecomp 서브모듈 커밋이다.
- [XexPatcher](https://github.com/hedge-dev/XenonRecomp/blob/c5bfd90d87f2ed0db8cff5c19ea3aff0e161e527/XenonUtils/xex_patcher.cpp): 헤더 범위 및 복호화한 원본 이미지 키의 일치를 검사한다. `skipData` 검사 성공 뒤 실제 적용에서는 블록 digest 등도 검증한다.

공식 목록의 해시는 한국어 패처의 SHA-256과 다른 **XXH3-64** 값이다.

| 파일 | 공식 목록의 XXH3-64 (hex) |
|---|---|
| default.xex | 8bcb38256ac205c2, c031ce0a3d7b711f, ffc355823a2facd5, ce647662e98bc9d6 |
| default.xexp | 5ff46f14fe37f375, d7b0eff3610d0caf, f6a6b701caac8b99, 3988350ef56cd3d9 |

각 목록에 있다고 해서 임의의 16조합을 모두 허용하는 것은 아니다. 공식 호환성 판정은 `checkGameUpdateCompatibility` → `XexPatcher::apply(..., true)`를 따른다. 다른 지역의 게임 파일을 새로 다운로드하지 않았으므로 모든 조합의 결과 해시표는 만들지 않았다. v1.0.1은 이 조합을 다시 구현하거나 XEX 변종별 delta를 만들 필요가 없다.

## v1.0.0 산출물 추적

`build_native_korean_resources.py`는 50개 도전과제의 150개 한국어 필드를 `Translation/achievements-ko.json`에서 읽는다. `achievements-source.json`의 문자열 ID를 사용해 XEX의 영어 XDBF 문자열 테이블을 생성한다. 기존 문자열 테이블을 직접 늘리지 않고 확인된 빈 공간에 새 테이블을 놓고 리소스 크기·테이블 엔트리·빈 공간 엔트리를 갱신한다.

`patch_mission_loading_resource_v054.py`는 `StageLoad_list\0`를 XEX 파일 오프셋 `0x2525c0`(게스트 주소 `0x8224e5c0`)에 추가한다. 현재 `build_native_korean_exe.py`의 로딩 변경은 `calls=[]`, `shared_explicit_newlines=True`로 원래 `StageList_list`를 사용한다. `build_field_mission_v056.ps1`의 HMM 데이터는 두 문구표를 같은 내용으로 만든다. 이 이름 추가는 현재 로딩 경로의 필수 요소가 아니다.

생성 결과는 `Build/Korean Full UI Playtest/Native`를 거쳐 v056 Native 산출물로 이어진다. `build_clean_release_deltas_v057.py`는 `Build/CleanOriginals-v057`의 원본과 v056 Native를 비교해 custom delta를 만든다. v058 분리 패키지의 `KoreanOptionalUI/Support`를 v059 패키저가 Full에 복사한다. v1.0.0 Full manifest에는 XEX `00.krpatch.gz`, EXE `01.krpatch.gz`가 들어 있다.

| 파일/단계 | SHA-256 |
|---|---|
| 원본 Windows EXE | b22c40e97510a122476028d0462bc6dbc93abb124431e39680ae8dd463eba687 |
| v1.0.0 한국어 EXE | df253ffafab22583b8088c92a034e1023787132465e6f8f05de28e46a41bf9c9 |
| v1.0.1 한국어 EXE | 18de8cedca10c5d0a3a5521c9f4a8795e06200ea2b07ea33ea0243081eca74fa |
| 로컬 원본 patched/default.xex | 8940eef6cdbf8585a58991fe5a7c7bfb4bc1b041c1628bc2757adcdd7a11b520 |
| v1.0.0 한국어 patched/default.xex | 90ce58984e84753bb5719eaaddfc32377f6b8493787733f4a42223455ca0dd28 |

로컬 XEX 21,970,944바이트 두 파일을 비교했으며 실제로 다른 바이트는 6,449개다. 가까운 변경을 묶은 범위(끝 제외)는 다음과 같다. 묶음 안에는 동일한 바이트가 일부 포함된다.

| 파일 오프셋 | 의미 |
|---|---|
| 0x2185–0x2188 | XEX 리소스 크기 필드 |
| 0x2525c0–0x2525ce | 과거 StageLoad_list 이름 |
| 0x14620ff–0x1462106 | 영어 XDBF 테이블의 오프셋·길이 |
| 0x1462161–0x1462164 | XDBF 빈 공간 엔트리 |
| 0x14f1360–0x14f2dd1 | 새 영어 슬롯 문자열 테이블의 한국어 내용 |

EXE에는 이미 네이티브 UI 188개 대응표의 번역 hook과 한국어 글꼴·도전과제 버튼 가이드 처리가 있다. 그러나 기존 EXE 번역표는 XDBF 도전과제 이름·설명 조회를 대체하지 않았다. 중복이 아니라 **글꼴/메뉴는 EXE, 도전과제 문구는 XEX**로 나뉜 구조였다.

## 새 EXE 구현

`build_native_korean_exe_v101.py`는 검증된 v1.0.0 한국어 EXE에 읽기/실행 전용 `.krach` 섹션을 추가한다. 150개 한국어 문자열과 ID 표를 넣고 `GetAchievements`(RVA 0x290910)와 `GetAchievement`(0x291200) 안의 `GetString` 호출을 각각 3곳씩 변경한다.

새 dispatcher는 영어 슬롯이며 알려진 ID인 경우에만 기존 `std::string` 생성자(RVA 0xcbf90)로 tail call한다. 그 외에는 원래 `GetString`(0x290770)으로 tail call한다. 게스트 메모리·XEX·이미지·점수·도전과제 해제 여부·음성 설정은 변경하지 않는다. 스택과 nonvolatile register를 바꾸지 않는 leaf 코드이며 원래 함수 본문과 unwind 정보도 보존한다. 새 절대 포인터 relocation이 필요하지 않은 RIP 상대 참조를 사용한다.

실제 dispatcher 기계어를 독립 실행하여 150개 번역 ID, 7개 fallback 언어 값, 미등록 ID 2개를 검사했다. 생성자/원래 조회 함수는 이 단위 검사에서 stub으로 대체했으므로 실제 게임의 메모리 수명·화면 확인은 별도의 사용자 플레이 결과로 구분한다.

## 백엔드 재설계와 발견한 위험

| 이전 구조의 위험·제약 | 새 처리 |
|---|---|
| 한 종류 XEX SHA만 허용, 오류에 Windows EXE 버전 요구 | XEX 의존성 제거. EXE 해시만 검사 |
| 파일이 여러 개여서 프로세스 종료 시 부분 적용 가능 | EXE 한 파일, 검증된 원본 저장 후 원자적 교체 |
| 변경 가능한 외부 manifest/state의 해시에 의존 | 설치 EXE에 manifest 내장. 외부 manifest도 내장본과 일치해야 설치 가능 |
| 백업 state의 gameRoot가 폴더 이동을 거부 | 백업 파일의 실제 해시·길이로 판정. state 경로에 의존하지 않음 |
| config가 없으면 원본 복원까지 막힘 | 설치 시만 읽기 전용 검사. 복원은 config/Support 불필요 |
| 루트 config만 조회 | 공식 portable/AppData 경로 규칙 사용 |
| 텍스트 경로 검사만으로 junction/hard link를 막지 못함 | 쓰기 경로의 reparse point와 파일 hard link 거부 |
| 동시 설치기가 같은 백업·파일을 바꿀 가능성 | 게임 루트별 mutex, 선택한 게임의 실행 여부 검사 |
| delta 산술 overflow·과다 해제 위험 | 크기 제한, checked 산술, 제어/차이/추가 데이터의 정확한 소비 검사 |
| 백업 내용·다른 EXE를 덮어쓰는 위험 | 손상된 백업/미지원 EXE는 중단. 원본 백업 덮어쓰기 금지 |
| v1.0.0에서 새 EXE로 직접 덮어쓰면 과거 XEX 변경이 남음 | 이전 Full EXE를 인식하면 이전 도구로 전체 복원 후 업그레이드 안내 |

v1.0.0 config 변경 상수/함수는 실제로 호출되지 않았다. 새 도구도 설정·음성·세이브·HMM 활성 모드를 쓰지 않는다. Basic은 설치 도구를 포함하거나 호출하지 않는다.

백업은 `korean-native-backup/Original/UnleashedRecomp.exe`에 원자적으로 생성하고 저장 완료를 확인한다. 임시 EXE도 저장·해시 검사 후 `File.Replace`로 교체한다. 정상 예외 시 교체 직전 EXE로 rollback하고 결과 해시를 확인한다. 강제 종료 후에는 원본 백업과 현재 EXE의 알려진 해시로 재설치/복원할 수 있다. 복원 권한을 주는 state 파일이나 경로를 외부 입력으로 읽지 않는다.

복구 자체를 막는 디스크/권한/다른 프로그램 변경이 발생하면 자동 복구 성공을 주장하지 않고 복구 파일 위치를 알린다. 저장 매체 고장·악성 동시 파일 교체·모든 파일 시스템에 대한 절대적인 무결성 보장을 뜻하지 않는다.

## EXE 완성본 교체 방식 검토

GPL-3.0은 조건을 충족하면 수정된 바이너리 배포를 허용한다. 다만 저작권·라이선스 고지와 대응 소스 제공 조건 등을 충족해야 한다. 현재 GPL 원문과 몇 개 변경 소스가 있다는 사실만으로 수정 EXE 전체에 대한 의무가 자동으로 충족된다고 단정할 수 없다. [GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html)의 대응 소스 및 object code 배포 설명을 참고했다.

완성 EXE 교체도 원본 식별·백업·복원·다른 패치 거부가 필요해 안전성 문제를 자동 해결하지 않는다. 이번에는 약 90MB 완성 EXE 대신 약 14.6MB delta를 유지하고, 사용자 게임 파일에서 메모리 내 완성본을 검증한 뒤 원자적으로 교체한다. delta도 라이선스 의무를 면제하는 수단은 아니다. 변경 생성 소스·번역 입력·manifest·빌드 절차를 Source.zip에 포함하며 완성된 게임 EXE/XEX는 배포하지 않는다.

## 검증과 재현

- `test_full_backend_v101.py`: 게임 없는 모의 CLI 38개 검사. 설치·재설치·복원, 설정 누락/키 오류, 잘못된 EXE, 손상된 백업/manifest/delta, 다른 패치, 폴더 이동, hard link, EXE 잠금, mutex, 진단을 포함한다.
- 실패 주입 5지점과 강제 종료 4지점에서 원본 보호, rollback, 재시도/복원을 검사했다. `TEST_FAULTS`는 테스트 빌드에만 정의하며 배포 빌드에는 존재하지 않는다.
- `test_full_release_v101.py`: 실제 크기의 공식/한국어 EXE와 배포 delta를 모의 게임 폴더에서 설치·재설치·복원했다. XEX 없음/임의 변종 sentinel/원본 XEX 모두 동일하게 처리하며 XEX·설정·음성·모드·세이브 sentinel을 보존한다. 실제 v1.0.0 도구의 설치·복원 후 v1.0.1 전환도 검사한다.
- 공식 v1.0.0 ZIP과 실제 작업용 원본 EXE/XEX/config는 작업 전 SHA-256과 대조한다. 실제 세이브는 테스트 입력으로 사용하지 않고 별도 테스트 폴더를 사용한다.
- 원본 XEX 테스트: 기존 실제 게임 폴더를 바꾸는 대신 별도 실행 폴더에 필요한 데이터를 복사하고, 해시가 검증된 원본 XEX와 새 EXE 및 HMM 번역 데이터를 배치했다. 사용자 세이브를 덮어쓰지 않았다.

| 화면 검증 항목 | 확인 상태 |
|---|---|
| 옵션·화면 언어·음성 언어 | 사용자 정상 확인 |
| 도전과제 메뉴 이름·설명 | 사용자 정상 확인 |
| 게임 시작·대사·자막 | 사용자 정상 확인 |
| 일시정지·버튼 가이드 | 사용자 정상 확인 |
| 월드맵·미션 선택/설명·미션 로딩 | 사용자 실기 검수에서 정상 확인 (2026-09-12) |
| 새 도전과제 해제 알림 | 공통 문자열 경로 정적/기계어 검사. 사용자 요청으로 추가 실기 검수 생략, 미확인 유지 |
| 다른 지역/디지털 XEX 전부의 실제 플레이 | 미확인. XEX 파일 비접근·해시 거부 제거는 자동 검사 |

이 기록은 검사 범위를 공개하기 위한 것이며 모든 잠재 버그가 없다는 보증이 아니다. 남은 실제 화면 검증을 완료한 뒤 최종 배포 여부를 판단한다. 패키징은 로컬 파일 생성만 수행하며 외부 게시를 자동 수행하지 않는다.

이번 번역 개정의 EXE는 기존 검수 후보에 웨어혹 문구·문자열 길이와 누락된 혹 글리프를 추가 보정한 빌드입니다. 이전 후보 실기 결과와 새 번역 리소스의 자동 검증은 구분하며, 상세 내용은 TRANSLATION-AND-COMPATIBILITY-AUDIT.md를 참조합니다.
