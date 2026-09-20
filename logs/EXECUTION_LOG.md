# EXECUTION LOG — PRISM-Hub

각 항목: **실행 내용 → 결과 → 발견/결정**. 시뮬레이션은 Python(검증용 원본)으로 실행했고 동일 계산을 MATLAB 스크립트로 이식했다. 절대 경로는 저장소 상대 경로로 바꾸었다.

---

## 2026-09-05 ~ 09-11 — 제안서 작성 (docs/01)

- 웹 조사 6회(EV DC-DC 토폴로지, OBC/APM 통합, PPP, GaN FCML, 48 V 조널, NN 예측 제어). 400 V 충전 인프라 지배(유럽 800 V 충전기 ≈ 1 %), CLLC+재구성 토폴로지 유망, TAB 다중포트 전류 스트레스 한계, 온보드 허브에 PPP 적용 사례 미확인 → PRISM-Hub 3단 구조 제안.
- 09-11: droop 대응 방향 논의 → "부하 변동에 따른 버스 전압 droop 예측" 채택, 3.6절 ARL 신설, WP4.5·S6·KPI 6–8·리스크 추가, 일정 18주.

## 2026-09-20 — 엔지니어링 설계·검증서 (docs/02)

### 세션 1: 수치 설계 (python/calc.py → docs/fig/fig1–7)
- 참고문헌 검색 9회: Aghabali TTE 2021, Wouters TPEL 2024, Anzola IEEE Access 2020, Zientarski JESTPE, Seeman–Sanders TPEL 2008, Zhao DAB TPEL 2014, Zahid TTE 2015, Jung TPEL 2013, Xie TPEL 2025, Zhao/Blaabjerg TPEL 2021, Vazquez IEM 2014, Wood IEEE PE Mag 2025. **선행기술 발견**: He/Jiang/Nan APEC 2018(STC+PPP, 48 V), Ni et al. APEC 2019(GaN STC+PPVR, EV).
- Stage A f_s 스윕 50–400 kHz → 150 kHz 선정(캡 7.8 µF, L_r 144 nH, 99.69 %). 돌입 3.4 kA(프리차지 필수).
- Stage B ΔV 스윕 648–920 V → +77/−53 V, 최대 4.8 kW → 정격 8 kW. 충전 모드 바이패스 결정(직렬 손실 323 W는 작으나 변압기 3.75배 사이징 회피).
- Stage C: 25:3, Q 0.4, m 6 → L_r 11 µH, C_r 36.8 nF, L_m 66 µH, 이득 ±1 %. 12 V 3권선 불가 → 벅.
- 버스: CPL 안정성 37 nF(트리비얼), droop 유도식 ΔV = ΔI·t_resp/(C_ser + C_bus), f_res 14.5 kHz → (당시 가정) BW 4.8 kHz, t_resp 72 µs, 60 A → 8.7 V.
- Baseline 비교: 충전 손실 4.5 → 0.5 kW, 자기소자 180 → 12.4 kVA, 주행 절감 56 Wh/100 km.
- 자체 검토(9장): 오류 7건 정정(션트 모델 droop 39 V 오류, PPRC 25 % 전제, 3권선, 위상 셰딩 누락, Coss 50 % 계상, 홀드업 기준 오류, 1/√C 스케일).

### 세션 2: TB-A1 (python/tb_a1_sim.py → docs/fig/tba1_*)
- 단상 셀 구분선형 ODE, RK4, 주기당 680 스텝, 300주기.
- 공칭 788 V/46.9 A/f_s = f_r: I_pk 73.7 A, 스윙 20.0 V, 손실 59.1 W, η 99.68 % — 3장 계산 일치. **턴오프 전류 9.2 %** → ZCS 불성립.
- 원인: 데드타임 3 % + 출력캡 공진 이동 1 %. 미세 스윕 0.93–1.05 → 최적 0.975–0.98(2–3.5 %), 창 ±1 %. 공차 ±3–5 % 시 13–24 %, 하드 턴오프 상한 +22–43 W.
- 수치 아티팩트 2건 수정: (a) 출력캡 20 µF(C_fly의 2.6배)로 공진 18 % 이동 → 400 µF; (b) 데드타임 다이오드 영교차 채터링 → 영교차 클램프, 주기 정수 스텝.
- 결정 A-1: f_s = 0.98 f_r = 147 kHz. A-2: 적응형 ZCS 제어 필수. 파라미터 스크립트에 f_r/f_s 분리.
- 산출: matlab/tb_a1_rsc_phase.m, matlab/build_rsc_phase.m.

### 세션 3: WP3-1 / TB-A2 / A3 / A4 (python/tb_a_array.py → docs/fig/wp31_*, tba2_*, tba3_*)
- 8위상 벡터화 모델. 실행 시간 제한으로 단계별 실행(mc / a2 / a3 / a4), 주기당 340 스텝, 50–60주기.
- V1: N=1 재현 — 75.3 A / 4.4 % / 59.6 W (부록 A 일치).
- 몬테카를로 20회(C ±5 %, L ±10 %, R ±10 %): 고정 0.98 → 17/20 실패(최대 38.6 %); ZC 턴오프+공통 주기 0.90 f_r → 0/20, 손실 +10 %; **자기발진(위상별 ZC 주기 추종) → 0/20, 59.4 W**. 결정 B-1.
- 자기발진 로직 결함 발견: 무부하 근처 오검출 토글 → 에너지 역류(프리차지 12.5 ms 후 버스 붕괴). 블랭킹 창 0.80–1.12×공칭으로 해결.
- TB-A2: 모듈 편차 ≤ 1.9 %, 위상 ±10.5 %, 리플 0.21 V, 손실 471 W(V2 PASS), R_out 2.3 mΩ.
- TB-A3: 저항 직결 시 L/R 7 ns 강성으로 발산 → C_in 100 µF 추가(결정 B-2). 피크 15.6 A, t95 13.6 ms. 프리차지 없이 8 kA.
- TB-A4: 1모듈 31.6 W(V3 PASS) vs 8위상 114 W.
- 산출: matlab/tb_a_array.m.

### 세션 4: TB-B2 / TB-S1 (python/tb_b_pprc.py, tb_b_pprc2.py → docs/fig/tbs1_*)
- 평균값 직렬 경로 모델(테브냉 394 V/10.2 mΩ, L_path 1.5 µH, C_ser 100 µF, DAB 지연 10+5 µs, 샘플 5 µs, 포화 ±100 A, CPL 5 kW + 60 A).
- PI 단독: 주파수응답(해석식과 상태공간 대조 일치)에서 최대 f_c 1.8 kHz(공진 Q ≈ 10). 시간 영역 droop 8.6 V, 회복 430 µs.
  - 시뮬 버그 2건 수정: 지령 초기값 이중 계상, pre-boost 조건식 우선순위(v_ref 800 V) — 수정 전 결과 폐기.
- 상태궤환+적분(극배치, scipy place_poles): 부호 규약·플랜트 Vbat/2 누락 수정 후 f_bw 8–10 kHz 안정, droop 4.7 V, 회복 80 µs. L_path 0.5/1.5/3 µH 모두 10 kHz. 결정 C-1.
- 제어 비교: B1 4.5 V, B2 2.1 V, ARL(20 %, +50 µs) 4.7 V, pre-boost 0 V(+8 V 사전 편차).
- 스텝 스윕: 25/60/80/87/95/105 A → 2.0/4.7/6.3/14.6/붕괴/붕괴. **포화 절벽 87.5 A**, pre-boost 무력.
- 캡 축소: s=0.25 불안정(포화·공진 리밋 사이클), s=0.5 B0 7.6 V, s=2 2.7 V.
- 결론: 3.5절 가정(BW 4.8 kHz, ARL 잔여 1.7 V, 캡 1/4) 철회 → ARL 기여 = 포화 예측 회피 + 제약 인지 MPC. 부록 C, 본문 2.4/3.5/KPI 6/9장 갱신.
- 산출: matlab/tb_b_pprc.m.

### 세션 5: 이름·저장소
- 프로젝트명 PRISM-Hub 유지 결정, 제어 계층 ARL → SALS(Saturation-Aware Anticipatory Load Shaping) 개명 검토.
- 저장소 초기 구성(이 로그, README, CHANGELOG).

---

## 미결 항목
- TB-S6 ARL-MPC, TB-C1/C2, TB-B3, TB-S2~S5.
- 설계검증서 본문 2.4·3.5·4.3.3 재작성(현재는 "검증 후 갱신" 주석으로 표시).
- 참고문헌 [21](열관리 부하) 1차 문헌 교체, 선행기술 전수 검색.
- Simulink 모델 실제 생성·배선 확인(build_rsc_phase.m는 미실행).
