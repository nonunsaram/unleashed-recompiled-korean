# 기여 안내

오역·표시 문제는 GameBanana 댓글 또는 GitHub Issue로 알려 주세요. 재현에 필요한 화면, 지역·미션 이름, Basic/Full 구분, 설치한 DLC 구성을 함께 적으면 확인이 빨라집니다.

Pull Request를 보내기 전에는 다음을 지켜 주세요.

- 게임 본편, 업데이트, DLC, EXE/XEX, 세이브 또는 추출된 게임 아카이브를 첨부하지 않습니다.
- 번역 카탈로그의 `translation_key`, 위치 식별자와 JSON 구조를 임의로 바꾸지 않습니다.
- Full 전용 변경은 Unleashed Recompiled v1.0.3 Windows x64의 지원 해시 범위를 유지합니다.
- `KoreanSupportSetup.cs`의 백업·해시 검사·복원 보호를 약화시키지 않습니다.
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\Scripts\validate_public_tree.ps1`을 실행합니다.

제3자 자료를 추가할 때에는 출처와 적용 조건을 함께 제출해야 합니다. 직접 제작한 새 코드·문서·한국어 번역 기여분은 기존 MIT 범위와 호환되어야 하며, GPL·OFL 등 다른 조건의 자료에는 해당 조건을 정확히 표시해 주세요. 재배포 전에는 [LICENSE.md](LICENSE.md)를 확인해 주세요.
