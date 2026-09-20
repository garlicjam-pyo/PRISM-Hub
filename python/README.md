# python/ — 검증용 원본 계산 스크립트

MATLAB 스크립트와 동일한 수식·모델을 먼저 Python으로 실행해 결과를 확정한 뒤 MATLAB으로 이식했다. 결과 JSON은 `results/`.

| 스크립트 | 대응 MATLAB | 내용 | 실행 |
|---|---|---|---|
| calc.py | prism_design_params.m | 3장 수치 설계·스윕, fig1–7 | `python calc.py` |
| tb_a1_sim.py | tb_a1_rsc_phase.m | TB-A1 단상 셀 | `python tb_a1_sim.py` |
| tb_a_array.py | tb_a_array.m | 8위상 어레이, 자기발진 ZC, MC/A2/A3/A4 | `python tb_a_array.py mc` / `a2` / `a3` / `a4` |
| tb_b_pprc.py | (참고) | PI 단독 설계·주파수응답 | 모듈로 사용 |
| tb_b_pprc2.py | tb_b_pprc.m | 상태궤환 PPRC, TB-B2/TB-S1 | `python tb_b_pprc2.py` |
| tb_s6_sals.py | tb_s6_sals.m | anti-windup/캡 축소(A), SALS 강건 LP 부하 셰이핑(B) | `python tb_s6_sals.py A` / `B` |
| tb_c1_cllc.py | tb_c1_cllc.m | CLLC 스위칭, 이득·ZVS·손실 | `python tb_c1_cllc.py` |
| tb_c2_cllc_bidir.py | (tb_c1_cllc.m 확장 예정) | CLLC 양방향 전환, f_s 편이 전류 제한 | `python tb_c2_cllc_bidir.py` |
| tb_s2_b3.py | (tb_b_pprc.m 확장 예정) | 150 kW CC-CV, 바이패스 전이 | `python tb_s2_b3.py` |
| wp45_predictor.py | — | 합성 데이터·분위수 GBM 예측기·폐루프 | `python wp45_predictor.py` (sklearn) |

의존성: numpy, scipy, matplotlib. 그림은 `../docs/fig/`에 저장된다.
