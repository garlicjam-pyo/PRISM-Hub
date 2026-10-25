# R2 통합 회로(E23·TB16·TB17) 근거 (2026-10-25)

R2 기본형과 R2-W460 창 조정 모듈 강등을 실제 Stage A·조정형 Stage C와 한 회로에서 확인한 근거 파일이다.

- **평균모델**: `submission/verification_code`의 `E23_r2_integrated.py`다. 아래 E23 파일은 그 실행 결과(`results/E23`)를 옮긴 것이다.
- **회로 모델**: [TB16](../../simulink/tb/TB16_R2_Base/README.md)이다. 아래 TB 파일은 결과 요약을 옮긴 것이다.
- **그림·파형**: 응답 그림과 파형은 각 TB의 `results/`에 있다.

| 파일 | 내용 |
|---|---|
| E23/base.json | 사례 3개의 평균모델 판정(48 V, 버스 범위·안정, Stage C 전류)과 Stage A 기준값(E1 영교차 추종 2위상, 사건 전·끝) |
| E23/zbus.json | C\_A·R\_A를 넣은 버스 임피던스와 Stage C 입력 임피던스(5 kW, 270·504 V), C\_A를 뺀 E22 T7 버스와 비교 |
| E23/E23_r2_integrated.png | 사례 응답(48 V, 버스·V\_A, Stage C 입력), 임피던스 |
| TB16/ | TB16 요약 3사례(txt·json), 기준값 요약(`TB16_ref_summary.json`) |

| 항목 | 결과 |
|---|---|
| E23 base | 3/3. v\_o 44.31–48.18(Stage C 0.1 → 5 kW, 270 V)·48.00–48.03(400 V 부하 15 → 25 kW)·47.75–50.91 V(Stage C 5 → −3 kW). 버스 변동 ≤ 0.83 V, 끝 진동 ≤ 0.0001 V |
| E23 zbus | 최소 여유 49.3 dB(270 V, 3 kHz). C\_A를 뺀 E22 T7은 49.1 dB였다 |
| TB16 | **3/3 통과.** v\_o 회로 44.16–48.19·48.00–48.04·47.73–50.73 V(E23과 최저·최고 0.18 V 안, 끝 0.000 V). 버스 E23과 끝 0.016 V 안. Stage A ZCS ≤ 2.27 %(E1 ≤ 3.80 %), V\_A − E1 ≤ 0.09 V. Stage C V\_ds ≤ 0.21 V |

E23은 Stage A를 정적 등가(V\_bat/2 + 10.2 mΩ)로 둔 평균모델이다. TB16은 Stage A 공진 스위치드 커패시터 2위상과 조정형 Stage C를 소자 수준으로 넣은 회로다(Simscape Electrical, 후진 오일러 2.5 ns, 고정 비용).
