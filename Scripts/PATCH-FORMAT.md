# URKRDP1

Gzip 스트림 안에 다음 데이터를 저장합니다.

1. 8바이트 매직 `URKRDP1` + NUL
2. little-endian signed 64-bit 값 4개: 원본 크기, 대상 크기, control 바이트 수, difference 바이트 수
3. `(add length, extra length, old-position adjustment)` 형식의 control triple
4. difference 바이트와 extra 바이트

표준 BSDIFF의 바이트 덧셈 의미를 사용합니다. 입력, 출력 및 압축된 패치의 SHA-256은 배포판의 `Support/manifest.json`에 기록되며 설치 전에 검증됩니다. 이 형식은 데이터 차이만 담고 실행할 명령은 포함하지 않습니다.
