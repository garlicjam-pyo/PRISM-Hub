# Stage A 25 kHz 설계(A25) 재검증과 수정안(A25R)(E32·E33·TB26·E35·TB27) 근거 (2026-10-28)

docs/37 7.3절의 선택지 가운데 (나) 25 kHz(위치당 C4MS008075U2 2병렬, L\_r 864.6 nH, C\_fly 46.875 µF)를 골랐다. 이 설계의 정상상태·문턱·손실(E32), 동특성(E33), 회로(TB26)를 다시 판정했다. 이어서 C\_A를 2.4 mF로 키운 수정안(A25R)을 설계 단계(E35\_design)에서 고르고 판정(E35, TB27)한 근거 파일이다. 문서는 [docs/38](../../docs/38_StageA25_재검증_E32_E33_TB26.md)·[docs/40](../../docs/40_StageA25R_수정안_E35_TB27.md)이다.

- **검증 코드**: `submission/verification_code`의 `model_stage_a.py`(설계 묶음 `set_design('A25')`), `E32_stage_a_25k.py`, `E33_stage_a_25k_dynamics.py`, `E33_diag_transient.py`(실행 뒤 진단)다. 아래 E32·E33 파일은 실행 결과(`results/E32`, `results/E33`)를 옮긴 것이다.
- **회로 모델**: [TB26](../../simulink/tb/TB26_StageA25_Integrated/README.md)(Stage A 4모듈 + 스위치 출력용량)다.

| 파일 | 내용 |
|---|---|
| E32/design.json | 모듈(2위상·위상 하나) 손실·첨두·턴오프 비율, 손실 교차 |
| E32/rated.json | 정격 충전점(375 A) 위상 첨두 → P\_rated(공칭 74.5 A, 표본 1–3 86.5–102.8 A) |
| E32/thresholds.json | 셰딩·모듈 관리기 문턱과 시간 상수(150 kHz 값 포함) |
| E32/loss.json, loss\_run2\_D0lookupbug.json | ④ 보조·충전 손실, 모델 일관성 D0. 두 번째 파일은 D0 표 열쇠 오류가 있던 실행의 결과(보관) |
| E32/E32\_run.log, E32\_stage\_a\_25k.png | 실행 기록(1차 loss 집계 오류 → 2차 → D0 열쇠 수정 3차), 그림 |
| E33/static.json, transient.json, slow.json, fault.json | 정상 운전점 72점, 과도 7사례 × 2, 느린 충전 3사례 × 2, 모듈 고장 8사례 × 2 |
| E33/diag\_transient.json, E33\_diag\_transient.log | 실행 뒤 진단(C\_A 6배, 관리기 시간 상수 150 kHz 값) |
| E33/E33\_run.log, E33\_stage\_a\_25k\_dynamics.png | 실행 기록, 그림 |
| TB26/ | 회로 3사례 요약, 실행 기록(게이트 대조·빌드·짧은 실행·본 실행), 손실 판정 진단(TB26\_loss\_diag.json) |
| E35\_design/ | 설계 단계(판정 아님) dev–dev4 결과와 실행 기록: 충전 중 셰딩 정지, 관리기 시간 상수, 인터리빙 맞춤 시작, C\_A 6배, Tier-1 계단 |
| E35/ | A25R 판정: static, transient(요구 안), beyond(요구 밖, 정보), fault, clamp(E26 사건 32개, C\_A 2.4 mF), 실행 기록 |
| TB27/ | 회로 4사례 요약과 실행 기록 |

| 항목 | 결과 |
|---|---|
| E32 손실 | ④ 보조 94.4 W(⑤ 114.6, ⑥ 70.1 W), 충전 640/800/920 V 520/586/639 W(모터 승압 하한 571/607/633 W) |
| E32 문턱 | 셰딩 20/30 A(순시 53 A), 모듈 70/60/66 A, 시간 상수 6배 |
| E33 static | 공칭 33/36, 표본 1 31/36(정격 충전점 시작 과도 첨두, 표본 1의 130 A 모듈 수) |
| E33 transient | 공칭 1/7, 표본 1 1/7 |
| E33 slow | 0/3, 0/3(충전 요구 갱신 불성립) |
| E33 fault | 16/16 |
| 진단 | 느린 충전은 C\_A 6배 또는 관리기 시간 상수 150 kHz 값이면 통과, 부하 계단(MA)은 둘 다 불통과 |
| TB26 | 3사례 불통과. 동특성 C1–C4 판정은 모델과 모두 같음(첨두 차 ≤ 1.6 A, V\_A 차 ≤ 0.18 V). C5 손실 대조는 저장 에너지 미보정으로 판정 불가(진단) |
| E35 A25R | 요구 안 과도 12/12, 고장 16/16, static 33/36·36/36, 요구 밖 0/12(정보), 클램프 5.8–8.7 kHz(보수 145–193 °C, P5 불통과) |
| TB27 | 4/4 통과, 정격 충전 손실 회로 510.5 W·모델 495.8 W(+3.0 %) |
