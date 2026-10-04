# 1.0.5 이미지 출처와 검증

UnleasHD 원본/파생 이미지를 제외하고 게임 원본과 직접 만든 한국어 자료만 사용합니다. 독립 이미지 20종을 22곳에 배치합니다. 최종 이미지 해시는 Independent-image-provenance.csv/json에 기록했습니다.

게임 원본 그림은 realesrgan-x4plus-anime 기반입니다. 월드맵 한국어 텍스트 2종은 투명 캔버스에서 자체 글꼴로 다시 렌더링하고 바이트 일치를 확인했습니다. 이 자체 이미지가 과거 CSV에도 실렸다는 이유로 UnleasHD 이미지로 취급하지 않습니다. 원본 UnleasHD 이미지 해시와는 겹치지 않습니다.

최종 PRESS START, SEGA·저작권, NEW 표시는 자체 벡터 렌더링입니다. Scripts/render_independent_final_ui.py의 네 출력은 승인된 렌더링과 픽셀 단위로 일치합니다. 한국어 로고 발광은 게임 원본 밝기 마스크의 부드러운 확대와 자체 한국어 발광을 합성했습니다. 기존 자체 제작 한글 글꼴·자막은 유지했습니다.

release-record.json은 승인된 설치본의 모든 AR/ARL/DDS 해시와 UnleasHD·기존 파생본 금지 해시를 보관합니다. verify_independent_release.py는 실제 ZIP을 풀어 1,079개 아카이브 내부 리소스, 전체 리소스 파일 해시, 금지 이미지, ARL 크기, 옵션 70개 조합의 경로, 전체판 설치 도구/변경분 및 소스 ZIP을 검사합니다. 실제 ZIP 검사 결과는 verification.json에 기록합니다.

이 최종 패키징은 승인된 설치본의 리소스를 그대로 사용합니다. 이전 review16의 고정 CSV·검사 데이터·개발 폴더를 다시 생성하거나 변경하지 않습니다. review16 전용 검사는 UnleasHD 파생본을 전제로 하므로 독립 최종판에는 위 별도 검증기를 사용합니다.
