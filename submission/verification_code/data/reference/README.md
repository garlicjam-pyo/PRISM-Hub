# 고정 기준(회귀 확인용)

E28 `regress`는 모듈 관리기를 쓰지 않는 경로가 이전 시험의 저장 결과와 같은지 확인한다. 그 "이전 결과"는 다시 실행하면 바뀌는 앞 시험 출력이 아니라 고정된 기준이어야 하므로 여기에 둔다(2026-10-29 정리 전에는 저장소의 `validation/`에서 읽었다).

| 파일 | 원본 | 쓰는 곳 |
|---|---|---|
| `E24_transient.json` | E24 transient 결과(2026-10-26, 근거 사본 validation/2026-10-26-stage-a-shedding/E24/transient.json) | E28 regress |
| `E27_repro.json` | E27 repro 결과(2026-10-27, 근거 사본 validation/2026-10-27-zcp-reversal/E27/repro.json) | E28 regress |
