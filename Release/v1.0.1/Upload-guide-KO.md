# v1.0.1 GameBanana 버전업 안내

새 모드 페이지를 만들지 말고 기존 [한국어 패치 페이지](https://gamebanana.com/mods/715787)를 업데이트합니다. GameBanana 공식 안내는 [Adding Files and Update Submissions](https://gamebanana.com/wikis/2317)입니다.

## 1. 업로드할 파일 확인

- `UnleashedRecompiled-Korean-1.0.1-Basic.zip`
  - SHA-256: `54d4eacc85f4b80bbe996cb6db23dae5094e31d20cf0f36c199d3d115009d0f`
- `UnleashedRecompiled-Korean-1.0.1-Full.zip`
  - SHA-256: `ae8348ff3c90dfa2f251ae53f46440e88e9e7830071aad9fa73be62a18950b49`

`SHA256SUMS.txt`는 업로드 후 검사용입니다. GitHub에는 소스와 검증 기록만 두고 배포 ZIP은 GameBanana에 올립니다.

## 2. 기존 모드에 새 파일 추가

1. 로그인한 상태로 기존 모드 페이지를 엽니다.
2. 페이지 위쪽의 `Admin`에서 `Edit`을 선택합니다.
3. 편집 화면의 `Media` 탭으로 이동합니다.
4. `Files`에서 `Select Files`를 눌러 v1.0.1 Basic과 Full ZIP을 올립니다.
5. 파일별 버전 입력란에는 `1.0.1`을 적습니다.
6. 설명은 다음처럼 구분합니다.
   - Basic: `기본판 | HMM 원클릭 설치 | EXE 수정 없음`
   - Full: `전체판 | Windows x64 v1.0.3 EXE UI 추가 패치 | Basic 포함`
7. 새 파일 두 개가 보이는 것을 확인한 뒤 기존 v1.0.0 Basic과 Full의 `Archived`를 체크합니다.
8. 페이지 아래의 `Save`를 누릅니다.

GameBanana는 활성 상태로 보이는 파일이 최소 하나 있어야 합니다. 새 파일 업로드가 끝나기 전에 기존 파일을 모두 Archived로 만들지 마세요. v1.0.0 Full은 기존 사용자의 원본 복원에 필요할 수 있으므로 삭제하지 말고 Archived 상태로 보존하는 편이 안전합니다.

## 3. 모드 본문 수정

1. 다시 `Edit`으로 들어갑니다.
2. 기존 설명을 `GameBanana-post.md`의 내용으로 교체합니다.
3. 저장합니다.

현재 Mod 편집기의 `Technical` 탭에는 별도의 Version 항목이 없습니다. 이 탭의 Tags, Installation Instructions, Requirements는 버전업을 위해 수정할 필요가 없습니다. 버전은 다음 단계의 `Add Update` 창에 입력합니다.

본문 첫부분에서 다음 두 문장을 눈에 띄게 유지합니다.

- 신규 Full 설치에는 Basic 선행 설치가 필요 없습니다. 게임 첫 실행·초기 설정·종료 후 Full 도구를 실행합니다.
- 기존 v1.0.0 Full 사용자는 이전 도구의 원본 복원을 먼저 실행한 뒤 업그레이드합니다.

## 4. Update 글 등록

파일과 본문을 먼저 저장한 다음 편집 화면 밖으로 나와 기존 모드 페이지 상단의 `Updates`를 누릅니다. Updates 화면의 `Add Update`를 선택합니다.

- Title: `v1.0.1 — Full 설치기 재작성 및 번역 수정`
- Version: `1.0.1`
- Changelog: `CHANGELOG-KO.md`의 사용자용 변경 내역
- Files: 새 v1.0.1 Basic과 Full 두 파일 모두 선택
- `This update is significant`: 이번 변경은 설치기 재작성과 번역 수정이 포함되므로 체크 유지

모든 항목을 확인한 뒤 `Save`를 누릅니다. Update 글만 먼저 만들면 새 파일이 연결되지 않으므로 파일 업로드와 저장을 먼저 끝냅니다.

## 5. 게시 후 확인

- Updates 목록에 버전 `1.0.1`이 표시되는지 확인합니다.
- 새 Basic과 Full이 일반 파일 목록에 보이고 v1.0.0은 Archived 안에 있는지 확인합니다.
- 두 새 파일의 Manual Download와 HMM 1-Click Install이 각각 올바른 파일을 가리키는지 확인합니다.
- 내려받은 파일의 SHA-256이 위 값 및 `SHA256SUMS.txt`와 일치하는지 확인합니다.
- Full 지원 범위는 공식 Windows x64 v1.0.3 EXE입니다. XEX나 다른 버전·플랫폼도 지원한다고 표시하지 않습니다.

검증 범위는 `FULL-BACKEND-AUDIT.md`와 `TRANSLATION-AND-COMPATIBILITY-AUDIT.md`에 기록되어 있습니다. 도전과제 해금 알림 실기는 이번 검수 범위에서 제외했고, Denoised 조합은 해당 모드가 비공개라 재현하지 못했습니다.
