# v1.0.2 모드 호환 조사

조사일: 2026-09-13. 파일 구조와 생성 결과를 검사했으며 실제 게임 화면 검수는 배포 전 별도로 필요합니다.

## UnleasHD

- 조사본: UnleasHD 1.4.2, 모드 ID `pupsi.UnleasHD`
- 배포 페이지: <https://gamebanana.com/wips/91543>
- 다운로드 ZIP SHA-256: `46354048a2c7910461e6b5d4447f9f8432f725ca7b02d298ba360e8533c23414`
- 충돌 파일: `MainMod/Languages/English/+WorldMap`
- 충돌 원인: `mat_worldmap_en_001.dds`와 `mat_worldmap_en_002.dds`에 영어 지명·스테이지명이 이미지로 들어 있습니다. 한국어 패치의 문자열 표와는 별개라서 모드 순서만 바꾸면 한국어 저해상도 또는 영어 고해상도 중 하나만 남습니다.
- 해결: UnleasHD와 같은 2배 해상도에서 한국어 지명과 스테이지명을 다시 렌더링한 선택형 `+WorldMap` 호환 아카이브를 추가했습니다. 아카이브 압축 해제·재압축 및 DDS 재열기를 검증했습니다.

## Crimson Carnival over Eggmanland

- 조사본: 1.1
- 배포 페이지: <https://gamebanana.com/mods/593279>
- 다운로드 ZIP SHA-256: `50d05661cbba88735fe55b8bd2d8b6b30d4ae2b9965093924cd8e89b578d6bd8`
- 충돌 원인: `+Town_EggManBase_Common`과 `+WorldMap`에 자체 `StageList_list.fco`를 넣어 새 액트명 표를 제공합니다.
- 결론: 기존 번역을 덮는 단순 충돌이 아니라 제3자 모드가 추가한 이름입니다. v1.0.2의 UnleasHD 호환 범위에는 포함하지 않았습니다.

## Windmill Isle Act 5

- 조사본: 1.1
- 배포 페이지: <https://gamebanana.com/mods/618194>
- 실제 배포 RAR SHA-256: `d317de4c7393e8192856acfba39a0913fecb8ae1cfd3fdeee1f6d19748047ea9`
- 충돌 원인: `Main/Languages/English/+SonicActionCommon`과 `+WorldMap`에 자체 `StageList_list.fco`를 넣습니다. 시간대별 `+WorldMap`과 `+Town_MykonosETF`에는 새 스테이지 이미지도 포함됩니다.
- 결론: 추가 액트 전용 번역·이미지 작업이 필요한 별도 호환 범위라서 v1.0.2에는 포함하지 않았습니다.
