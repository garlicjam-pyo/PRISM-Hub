# A25R 영향 재확인(E36·TB28) 근거 (2026-10-28)

Stage A를 25 kHz 설계 A25R(C\_A 2.4 mF)로 바꾼 뒤, 150 kHz 설계로 계산했던 이전 결론(E15·E25·E18 손실·가치, E16·E23·E26·E29 동특성)을 다시 계산하고, 충전기 급정지(새 사례)와 충전 중 정지·V\_A 클램프 회로(TB28)를 확인한 근거 파일이다. 문서는 [docs/41](../../docs/41_A25R_영향_재확인_E36_TB28.md)이다.

- **검증 코드**: `submission/verification_code/python/E36_a25r_impact.py`. 판정 기준은 실행 전에 커밋했다. 아래 E36 파일은 실행 결과(`results/E36`)를 옮긴 것이다.
- **회로 모델**: [TB28](../../simulink/tb/TB28_A25R_Charging_Stop/README.md)(TB21 회로의 Stage A·게이트·C\_A를 A25R로).

| 파일 | 내용 |
|---|---|
| E36/a25\_grid.json, a25\_grid\_Rpass\_x2.json | A25 손실·V\_A 강하 표(E32 사양 격자 + 사양 밖 540·580·960·1010 V), 수동소자 저항 2배 격자 |
| E36/e15\_comparison.json | L1: 기준 구조 손실·정격 비교와 H5 판정(A25R) |
| E36/e25\_comparison.json, e25\_statements.json, e25\_motor\_boost.png | L2: 보조·충전 손실, 모터 승압, 손익분기, 감도, 결론 문장 대조 |
| E36/e18\_R1\_value\_map.json, e18\_A25R\_value\_map.json, e18\_compare.json, 그림 2개 | L3: 가치 지도(R1 표·A25R 표)와 바뀐 칸 |
| E36/e16\_static·concurrent·transition·sequence.json | D1: 충전 중 보조버스(R\_A 9.0 mΩ) |
| E36/e23\_base.json, e23\_zbus.json | D2: R2 기본형 버스·48 V, 버스 임피던스(R\_A 9.0 mΩ, C\_A 2.4 mF) |
| E36/e26\_noclamp.json | D3: 클램프 없는 충전 중 정지 8사건(C\_A 2.4 mF) |
| E36/e29\_failsafe\_F2.json | D4: 이중 고장 F2 4사례(C\_A 2.4 mF) |
| E36/dropout.json | D5: 충전기 급정지 6사례 |
| E36/E36\_run0\_e26.log, E36\_run1.log, E36\_run2.log | 실행 기록(e26 / e29·e23·tables·e15·e25·e18 / dropout·e16) |
| TB28/ | 회로 4사례 요약, 실행 기록(빌드·짧은 실행·본 실행), TB27 회로도 주석 정정 빌드 기록 |

| 항목 | 결과(괄호는 150 kHz 설계의 원 시험) |
|---|---|
| L1 E15 | H5 기각 유지. 주행 대표 ④ 94.4(85.0) W, ③′ 123.4(114.1) W, ① 114.6 W. 충전 ④ 586(497) W(800 V) |
| L2 E25 | 결론 문장 4개 중 1개 바뀜: 920 V 충전 ④ 639 W > 모터 승압 하한 633 W. 손익분기 상저항 2.46(1.31) mΩ |
| L3 E18 | 바뀐 칸 2개: 216s·사양 팩 B\_420의 최선 W410 → ①. B\_470 최선은 그대로 |
| D1 E16 | 통과(정적, 동시 운전 538, 모드 전환 240, 전체 순서 30) |
| D2 E23 | 통과(48 V 3/3, 버스 임피던스 최소 여유 49.9 dB) |
| D3 E26 | 470 V 도달 R2 640 V 1.72(0.90) ms, R2-W 640 V 0.95(0.16) ms |
| D4 E29 F2 | **0/4(1/4)**: 경로전류 소멸 5 ms 안 안 됨, 직렬 ≤ 120 V 3사례 불통과 |
| D5 급정지 | 6/6 |
| TB28 | 4/4: 클램프 440.2 J(E26 441.5 J), V\_A ≤ 468.12 V, 강제 차단 ≤ 62.3 A → 50 µs 뒤 0 A |
