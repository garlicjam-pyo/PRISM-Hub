# CHANGELOG

## [0.4.0] — 2026-09-21 (부록 D·E)
- 부록 D: TB-S6 — s=0.25 불안정 원인은 DAB 지연(MPC 불가), SALS 강건 LP 부하 셰이핑이 예측 오차 하에서 HW 대안(PPRC 150 A)과 동등(4 V) — 논문 핵심 표. 제어 계층 SALS 확정 제안, KPI 6 재정의.
- 부록 E: TB-C1 — CLLC 이득 0.998, FHA 대비 ≤ 0.5 %, ZVS 3.7–5.9×, η 97.85 %.
- 추가: python/tb_s6_sals.py, tb_c1_cllc.py, matlab/tb_s6_sals.m, tb_c1_cllc.m, docs/fig/tbs6_sals.png, tbc1_*.png.

## [0.3.0] — 2026-09-20 (설계검증서 부록 B·C)
- 부록 B: Stage A 어레이 검증(WP3-1 몬테카를로, TB-A2/A3/A4). 자기발진 ZC 제어(블랭킹 창) 채택, C_in 100 µF 추가.
- 부록 C: PPRC 제어 검증(TB-B2/TB-S1). 상태궤환+적분 제어기 채택, ARL 기여 재정의(포화 예측 회피·제약 인지 MPC), 캡 1/4 축소 주장 철회.
- 본문 2.4·3.5.3·3.5.5·KPI 6·9장에 "검증 후 갱신" 반영.
- MATLAB: tb_a_array.m, tb_b_pprc.m 추가.

## [0.2.0] — 2026-09-20 (설계검증서 부록 A)
- TB-A1 실행: f_s = f_r에서 ZCS 불성립 발견, f_s = 0.98 f_r, 적응형 ZCS 제어 필수 판정.
- prism_design_params.m에 f_r/f_s 분리, tb_a1_rsc_phase.m, build_rsc_phase.m 추가.

## [0.1.0] — 2026-09-20 (엔지니어링 설계검증서 초판)
- Step 1–9: 적용 대상 결정, 기존 구조 비교, 수치 설계·스윕, Simulink 셀·테스트벤치 가이드, 참고문헌 23건 검증, 자체 검토(정정 7건).
- 설계 변경 4건: 충전 모드 PPRC 바이패스(8 kW), 12 V 벅, 위상 셰딩, PPRC 정격 축소.

## [0.0.2] — 2026-09-11 (제안서 개정)
- 3.6절 ARL(예측 제어 계층) 신설, WP4.5·S6·KPI 6–8·리스크·참고문헌 추가, 일정 18주.

## [0.0.1] — 2026-09-05 (제안서 초판)
- 웹 조사, PRISM-Hub 3단 아키텍처, MATLAB 구현 계획 WP1–6.
