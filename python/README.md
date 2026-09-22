# python/ — 검증용 원본 계산 스크립트

초기 모델을 Python으로 작성한 뒤 MATLAB으로 이식했다. `results/`에는 이전 버전 결과도 있으므로 현재 코드의 검증 완료를 의미하지 않는다.

2026-09-22 수정: `tb_a_array.py`, `tb_b_pprc2.py`와 `pprc_model.py`, `tb_s2_b3.py`의 충전 함수. 최신 회귀시험은 저장소 루트에서 `python python/validate_review_fixes.py`로 실행하며 결과는 `validation/2026-09-22/`에 저장된다. SALS·WP4.5·TB-S3~5·TB-B3 및 PI 참고 모델은 아직 수정된 공통 plant로 이전하지 않았다. 이들의 기존 성능 수치는 재검증 대상이다.

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
| tb_s3_s5.py | (tb_b_pprc.m 확장 예정) | TB-S3/S4/S5 시스템 시나리오 | `python tb_s3_s5.py` |
| tb_a1_ringing.py | — | 소자 피크 전압(턴온 에지·L_pkg 스윕) | `python tb_a1_ringing.py` |
| sals_montecarlo.py | — | SALS 최악값 창 몬테카를로 300회 | `python sals_montecarlo.py` |
| wp45_predictor.py | — | 합성 데이터·분위수 GBM 예측기·폐루프 | `python wp45_predictor.py` (sklearn) |

의존성: numpy, scipy, matplotlib. 그림은 `../docs/fig/`에 저장된다.
