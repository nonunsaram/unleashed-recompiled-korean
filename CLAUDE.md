# Review16 release rules — read before any packaging / 패키징 전에 반드시 읽을 것

이 규칙은 Unleashed Recompiled 한국어 패치 1.0.5-review16과 그 최종 패키징에 적용됩니다. 경로는 프로젝트 루트 `E:/Vibecoding/Unleashed Recomp KR Project` 기준입니다. 공개 저장소는 그 안의 `publish/unleashed-recompiled-korean`입니다.
These rules apply to the Korean patch 1.0.5-review16 for Unleashed Recompiled and its final packaging. Paths are relative to the project root `E:/Vibecoding/Unleashed Recomp KR Project`; the public repository is `publish/unleashed-recompiled-korean` inside it.

## 금지 / Do not

1. **`Scripts/prepare_review16_hd_deduplication.py`를 실행하지 마세요.** 이 스크립트는 v105o에서 개발 폴더를 다시 만들며, 제외한 DLC 미리보기 수정본을 되살립니다. 스크립트 자체도 `ALLOW_REVIEW16_REBUILD=1` 없이는 아무것도 쓰지 않고 종료합니다.
   **Do not run `Scripts/prepare_review16_hd_deduplication.py`.** It rebuilds the development folder from v105o and brings back the excluded DLC preview correction. It exits without writing anything unless `ALLOW_REVIEW16_REBUILD=1` is set.
2. **현재 기준 개발 폴더는 `Build/Development-v105p-Playtest/UnleashedKorean`입니다.** 다시 생성하거나 다른 폴더(v105o 등)로 바꾸지 말고 그대로 사용하세요.
   **The current development folder is `Build/Development-v105p-Playtest/UnleashedKorean`.** Use it as is; do not regenerate it or switch to another folder (v105o or older).
3. **`Compatibility/UnleasHD-1.4.2/+WorldMap.ar.00`, `Compatibility/UnleasHD-1.4.2/+WorldMap.arl`, `mat_stage_ss_082.dds`는 어떤 경로로도 패키지에 넣지 마세요.** 백업 폴더(`Build/Review16-DropPreview-Work/removed-from-dev`, `.../previous`, `Build/Review16-DocFix-Work/previous`)나 이전 ZIP에서 복사하지 마세요. `Compatibility/UnleasHD-1.4.2/Languages/English/+WorldMap.*`은 한국어 월드맵 UI로 별개 파일이므로 유지합니다.
   **Never package `Compatibility/UnleasHD-1.4.2/+WorldMap.ar.00`, `Compatibility/UnleasHD-1.4.2/+WorldMap.arl` or `mat_stage_ss_082.dds` by any route**, including copies from the backup folders or older ZIPs. `Compatibility/UnleasHD-1.4.2/Languages/English/+WorldMap.*` is the Korean world-map UI, a different file, and stays.
4. **`UnleasHD-permission-texture-list.csv`는 22행 / 20종이 기준입니다.** 행을 추가하거나 UnleasHD 유래 텍스처를 새로 넣지 마세요. 새로 넣어야 한다고 판단되면 **작업을 멈추고 사용자에게 먼저 물으세요.**
   **`UnleasHD-permission-texture-list.csv` is fixed at 22 rows / 20 distinct files.** Do not add rows or any new UnleasHD-derived texture. If one seems necessary, **stop and ask the user first.**
5. **UnleasHD 제작진의 허락은 아직 받지 않았습니다.** 허락 전에는 GameBanana에 업로드하거나 기존 GameBanana 파일을 교체하지 말고, GitHub Releases에도 ZIP을 올리지 마세요.
   **UnleasHD permission has not been granted yet.** Until it is, do not upload to GameBanana, do not replace existing GameBanana files, and do not attach ZIPs to GitHub Releases.

## 패키징 절차 / Packaging

- 패키징 직후 `python Scripts/check_release_guard.py <Basic.zip> <Full.zip> Build/Development-v105p-Playtest/UnleashedKorean`을 실행하세요. 종료 코드가 0이 아니면 결과물을 쓰지 말고 사용자에게 보고하세요. `Scripts/package_review16_candidate.py`는 이 검사를 자동으로 실행하고, 실패한 ZIP의 이름에 `-FAILED`를 붙인 뒤 중단합니다.
  Right after packaging, run `python Scripts/check_release_guard.py <Basic.zip> <Full.zip> Build/Development-v105p-Playtest/UnleashedKorean`. A non-zero exit means the output must not be used; report it to the user. `Scripts/package_review16_candidate.py` runs this check automatically and renames failed ZIPs to `*-FAILED.zip` before stopping.
- 검사 기준 데이터 `Scripts/release_guard_data.py`(해시·이름만 포함)는 사용자의 승인 없이 고치지 마세요. 설치된 UnleasHD가 바뀌어 검사가 실패하면 데이터를 고치지 말고 사용자에게 알리세요.
  Do not edit `Scripts/release_guard_data.py` (hashes and names only) without the user's approval. If the installed UnleasHD changes and the check fails, tell the user instead of updating the data.
- 게임 텍스처와 아카이브 내용은 바꾸지 마세요. 문서만 고칠 때도 아카이브 내부 리소스 1,079개가 이전 ZIP과 바이트 단위로 같은지 확인하세요.
  Do not change game textures or archive contents. Even for documentation-only changes, confirm that the 1,079 archive members are byte-identical to the previous ZIP.
- GitHub에는 문서·CSV·스크립트만 커밋하세요. ZIP, DDS, `.ar`/`.arl`, 게임·UnleasHD 자산은 커밋하지 마세요.
  Commit only documents, CSV and scripts to GitHub; never ZIPs, DDS, `.ar`/`.arl`, or game/UnleasHD assets.
