# PRISM-Hub

**P**artial-power **R**egulated, fixed-ratio **I**ntegrated, **S**oft-switched **M**ulti-port **Hub** — 800 V 전기자동차용 통합 DC 전력 허브 (MATLAB/Simulink 시뮬레이션 연구)

> 이 README는 프로젝트의 **현재 상태 요약**이며 지속적으로 갱신된다. 상세 근거는 `docs/`의 두 문서, 재현은 `matlab/`·`python/`, 진행 이력은 `logs/EXECUTION_LOG.md`와 `CHANGELOG.md`를 본다.

최종 갱신: 2026-09-21 | 상태: **시뮬레이션 단계 종료 — 부록 A–K, 논문 구조안(docs/03), Simulink 재현 대조표(docs/04). 남은 항목: Simscape 모델 실행(대조표 기준), 선행기술 전수 검색(IEEE Xplore/특허), 논문 집필**

> **독립 검토 추가 (2026-09-21):** 아래 기존 PASS/성능 수치에는 재검증이 필요한 항목이 있습니다. 전력수지, 역방향 ZCS, 충전 중 보조전원 전압, SALS 강건성 및 선행기술을 검토한 [종합 보고서](docs/reviews/2026-09-21/PRISM_Hub_종합검토.md)와 [재현 자료](docs/reviews/2026-09-21/README.md)를 확인하세요. 이번 추가는 검토 기록이며, 회로·제어 코드의 수정 완료를 의미하지 않습니다.

---

## 1. 한 줄 요약

배터리 640–920 V를 **2:1 고정비 공진형 스위치드-커패시터**(개루프 ZCS, 150 kW)로 400 V 중간버스에 연결하고, 전압 조정은 **8 kW 부분전력 직렬 셀(절연 DAB)** 하나에 몰아넣으며, 48/12 V는 **고정이득 CLLC**로 공급하는 단일 장치. 400 V 급속충전기는 2:1 고정비만으로 호환된다(충전 모드에서 직렬 셀 바이패스). 제어 측에서는 차량 선행 신호로 부하를 예측해 **직렬 셀의 포화를 회피**하는 계층 **SALS**(Saturation-Aware Anticipatory Load Shaping, 구 ARL)를 얹는다. 검증 결과 SALS는 선행 신호 → 최악값 창 → 강건 LP(1 ms)의 규칙 기반 스케줄러로 확정되었다. 빠른 시간 스케일의 droop 절감 역할은 없으며, 학습 예측기는 현재 신호 집합에서 지속 예측과 차이가 없어(부록 H) 조건부 역할로 축소했다.

## 2. 아키텍처 (확정판)

```
 배터리 640–920 V ═ Stage A: 2:1 공진 SC 어레이 (4모듈×2위상, 150 kW, 자기발진 ZCS, 750 V SiC) ═╗
                                                                                       ║ V_A = V_bat/2
                 ┌──── Stage B: PPRC 8 kW 절연 DAB, 출력 ±90 V 직렬 삽입, 200 V GaN ────────┤
                 │          [충전 모드: 바이패스]  [제어: 상태궤환+적분, 8–10 kHz]                ║
 400 V 급속충전기 ◄┴─────────── 400 V 버스 (C_bus 400 µF, C_ser 100 µF) ─── 400 V 부하(컴프레서·PTC·V2L)
                                              │
                                   Stage C: CLLC 25:3, 400→48 V, 3 kW 양방향 (f_r 250 kHz 고정)
                                              │
                                    48 V 조널 버스 ─── 4상 벅 48→12 V 1.5 kW
```

| 단 | 핵심 파라미터 | 근거 |
|---|---|---|
| Stage A | f_r 150 kHz, C_fly 7.8 µF/500 V, L_r 144 nH, 스위치 응력 460 V, 위상당 59 W, η 99.68 % | 설계검증서 3.2, 부록 A·B |
| Stage B | ΔV −53~+77 V, 처리 전력 ≤ 4.8 kW(정격 8 kW), L_s 11.1 µH @200 kHz, 직렬 도통 7.8 W | 3.3 |
| Stage C | L_r 11 µH, C_r 36.8 nF, L_m 66 µH, 이득 ±1 % @ ±3 % f_s | 3.4 |
| 버스 | C_bus 400 µF, C_ser 100 µF, L_path 1.5 µH, C_in 100 µF | 3.5, 부록 B·C |

## 3. 기존 구조 대비 이점 (계산값)

| 운전점 | Baseline (풀전력 DAB 부스터 + 독립 APM) | PRISM-Hub |
|---|---|---|
| 400 V 충전 150 kW 손실 | 4.5 kW | 0.5 kW |
| 주행 400 V 보조 5 kW 효율 | 96.5 % | 99.0 % |
| 48 V 3 kW 총합 효율 | 94 % | 96.8 % |
| 자기소자 VA | ≈180 kVA | ≈12.4 kVA |
| 주행 100 km 에너지 절감 | — | ≈56 Wh (0.3 %, 미미함) |

정직한 한계: 회로 원리(고정비 STC + 부분전력 조정) 자체는 선행기술이 있다(Google APEC 2018, NDSU APEC 2019, TPEL 2025). 신규성은 시스템 통합·바이패스 모드·저전압 직렬 소자·예측 포화 회피 제어로 한정한다.

## 4. 검증 현황

| 테스트 | 내용 | 결과 | 판정 |
|---|---|---|---|
| TB-A1 | 단상 셀 ZCS·손실 | f_s = f_r에서 턴오프 9 % → ZCS 창 ±1 % 발견, f_s = 0.98 f_r | PASS (부록 A) |
| WP3-1 | ZCS 제어 몬테카를로 20회 | 고정 타이밍 17/20 실패 → **자기발진 ZC 추종** 0/20 실패, 손실 59.4 W | PASS (부록 B) |
| TB-A2 | 8위상 375 A, 소자 ±10 % | 모듈 편차 ≤ 1.9 %, 손실 471 W (예측 472 W) | PASS |
| TB-A3 | 프리차지 | 20 Ω + C_in 100 µF: 피크 15.6 A, 13.6 ms (없으면 8 kA) | PASS |
| TB-A4 | 위상 셰딩 3 kW | 1모듈 31.6 W (예측 32 W) vs 8위상 114 W | PASS |
| TB-B2 | PPRC 대역폭 | PI 단독 1.8 kHz(공진 Q≈10) → **상태궤환 10 kHz** | 설계 변경 (부록 C) |
| TB-S1 | 60 A 스텝 droop | PI 8.6 V / 상태궤환 4.7 V / B2 2.1 V / ARL-FF 4.7 V | PASS, ARL-FF 무효 |
| TB-S1 | 포화 절벽 | ΔI ≥ 95 A(헤드룸 87.5 A 초과)에서 붕괴 — ff·pre-boost 무력 | ARL 역할 확정 |
| TB-S1 | 캡 축소 | s=0.5 B0 7.6 V, s=0.25 불안정(포화) | 캡 1/4 주장 철회 |
| TB-S6 A | 캡 축소 s=0.25 + anti-windup | 포화 제거해도 불안정 → 원인은 DAB 지연(15 µs)+29 kHz 공진, MPC로 불가 | 캡 축소 주장 완전 철회 (부록 D) |
| TB-S6 B | SALS 부하 셰이핑, 냉시동 110 A 사건 | B0 붕괴 / 반응형 차단 −12.5 % 딥 / HW 150 A 3.9 V / SALS 단순+오차 붕괴 / **SALS 강건+오차 4.0 V** | **PASS — 논문 핵심 표** |
| TB-C1 | CLLC 이득·ZVS·손실 | 이득 0.998, FHA 대비 ≤ 0.5 %, ZVS 3.7–5.9×, η 97.85 % (예측 97.8 %) | PASS (부록 E) |
| TB-S3/S4/S5 | 800 V 충전 중 보조 스텝 / 회생 전환 / 600→920 V 스윕 | 2.0 V / 0.6 V / 버스 396–401 V, 600 V 코너 PPRC 8.4 kW → 디레이팅 규칙 | PASS(조건부, 부록 I) |
| TB-A1x | 소자 피크 전압(링잉) | 턴온 에지 ≥ 20 ns, L_pkg ≤ 10 nH → ≤ 500 V; 5 ns 에지는 600 V 초과 | PASS(설계 규칙, 부록 J) |
| SALS MC | 300 에피소드 | 정격 초과 사건 25 % → SALS 붕괴 0, 지연 중앙값 1 ms·최대 200 ms; 반응형 덤프 딥 22–58 V | PASS (부록 K) |
| TB-C2 | CLLC 양방향 전환 | φ=0 동기 DC 변압기 운전, 90 % 반전 57.5 µs, f_s 편이로 회생 전류 제한 | PASS (부록 G) |
| TB-S2 | 150 kW CC-CV, PPRC 바이패스 | 충전기 단자 331–460 V(창 200–500 V 내), 충전기 자체 루프로 CV 전환, 경로 99.77 % | PASS (부록 F) |
| TB-B3 | 바이패스 전이 | 폐로 점프 0.09 V, 재개방 1.2 V, 전류 피크 13.2 A | PASS (부록 F) |
| WP4.5 | SALS 예측기 학습 | 학습 예측 = 지속 예측(MAE 1.4 vs 1.3 A), q0.9 구간은 서지 미포함 → 폐루프 붕괴; **최악값 창 규칙은 지연 20–190 ms 전부 생존** | 학습 요소 조건부 축소 (부록 H) |
| TB-B3 | 바이패스 전이 | — | 대기 |
| TB-S2~S5 | 충전 CC-CV, 800 V 충전, V2L, 전압 스윕 | — | 대기 |

## 5. 검증 과정에서 바뀐 결정 (요약)

1. 충전 모드 PPRC 바이패스 → 정격 25 % → 8 kW (5.3 %)
2. 12 V: 3권선 CLLC 불가(0.75턴) → 48→12 V 벅
3. 주행 모드 Stage A 위상 셰딩(1모듈)
4. f_s = 0.98 f_r → 자기발진 ZC 추종(블랭킹 창 0.80–1.12) + C_in 100 µF
5. PPRC 제어: PI 캐스케이드 → 상태궤환 + 적분
6. ARL 기여: "droop 절감·캡 축소" → **"PPRC 포화 예측 회피(부하 셰이핑)"** — 제약 인지 MPC 역할도 철회(부록 D)
7. 제어 계층 명칭 ARL → **SALS** 확정 제안; 예측은 점추정·분위수가 아닌 **최악값 창(집합값)** 이어야 함 — 분위수 구간조차 서지를 놓쳐 붕괴(부록 H)
8. 학습(GRU/GBM) 요소: 현재 신호 집합에서는 정당화되지 않음 → 지연 결정 신호가 있을 때 창을 좁히는 용도, 창 폭·서지 계수 온라인 식별로 한정
9. (v1.1 전면 검토) 조정 가능 전류 105 A → min(100 A, 8 kW/ΔV); V_bat < 640 V 보조부하 20 kW 디레이팅; CLLC 양방향은 위상천이가 아닌 동기 운전 + f_s 편이; 4.3 가이드(자기발진 ZC, 상태궤환, SALS LP)로 교체

## 6. 저장소 구조

```
docs/   01_제안서_EV컨버터_아키텍처.md   상위 제안서 (조사·아키텍처·ARL 개념·WP·KPI·참고문헌 23건)
        02_엔지니어링_설계검증서.md     적용 대상 → 비교 → 수치 검증 → Simulink 가이드 → 테스트벤치 → 검토, 부록 A–C
        03_논문_구조안.md               두 편 분리 구조, 기여·그림 목록, 최근접 선행연구
        04_Simulink_검증대조표.md       Simscape 재현 시 대조할 기대값
        fig/                            수치 검증·시뮬레이션 그래프
matlab/ prism_design_params.m           WP1 파라미터 스크립트 (모든 수식) → prism_params.mat
        tb_a1_rsc_phase.m               TB-A1 단상 셀 스위칭 ODE (Simulink 불필요)
        tb_a_array.m                    8위상 어레이, 자기발진 ZC, TB-A2/A3/A4, 몬테카를로
        tb_b_pprc.m                     PPRC 상태궤환 설계(place) + TB-S1 (Control System Toolbox)
        tb_s6_sals.m                    SALS 강건 LP 스케줄러 + 직렬 경로 모델 (Control System·Optimization Toolbox)
        tb_c1_cllc.m                    CLLC 스위칭 ODE, 이득·ZVS
        build_rsc_phase.m               Simscape Electrical 모델 자동 생성 (수동 확인 목록 출력)
python/ calc.py, tb_a1_sim.py, tb_a_array.py, tb_b_pprc2.py, tb_s6_sals.py, tb_c1_cllc.py, tb_c2_cllc_bidir.py, tb_s2_b3.py, wp45_predictor.py
        results/*.json                  실행 결과 원본 수치
logs/   EXECUTION_LOG.md                실행 내역·발견·결정 타임라인
CHANGELOG.md                            문서·설계 변경 이력
```

## 7. 재현 방법

```matlab
% MATLAB (R2025a 권장)
cd matlab
prism_design_params      % 파라미터·스윕 표 출력, prism_params.mat 생성
tb_a1_rsc_phase          % TB-A1 (1~2분)
tb_a_array               % WP3-1/TB-A2/A3/A4 (수 분)
tb_b_pprc                % TB-B2/TB-S1 (Control System Toolbox 필요)
tb_s6_sals               % TB-S6 SALS (Control System + Optimization Toolbox)
tb_c1_cllc               % TB-C1 CLLC
build_rsc_phase          % Simulink 모델 생성 (실행 전 prism_design_params)
```
```bash
# Python 3.10+ (numpy, scipy, matplotlib)
cd python
python calc.py                 # 3장 수치 설계
python tb_a1_sim.py            # TB-A1
python tb_a_array.py mc|a2|a3|a4
python tb_b_pprc2.py           # TB-B2/S1
python tb_s6_sals.py A|B       # TB-S6 (A: anti-windup/캡 축소, B: SALS)
python tb_c1_cllc.py           # TB-C1
python tb_c2_cllc_bidir.py     # TB-C2
python tb_s3_s5.py             # TB-S3/S4/S5
python tb_a1_ringing.py        # TB-A1x 링잉
python sals_montecarlo.py      # SALS 몬테카를로
python tb_s2_b3.py             # TB-S2 / TB-B3
python wp45_predictor.py       # WP4.5 예측기 (sklearn)
```

## 8. 다음 단계

1. Simscape 스위칭 모델 실행 — `docs/04_Simulink_검증대조표.md` 기준으로 재현 확인(사용자 MATLAB 환경)
2. 선행기술 전수 검색(IEEE Xplore, Google Patents, Espacenet) — 검색식은 docs/03 공통 절
3. 논문 집필 — docs/03 구조안(논문 1 토폴로지·시스템, 논문 2 강건 스케줄링)
4. Simulink 모델 실제 생성(build_rsc_phase.m 실행·배선 확인), 스위칭 모델 기반 TB-S1 재검증
5. 선행기술 전수 검색(IEEE Xplore, Google Patents, Espacenet)

## 9. 참고문헌

설계검증서 7장(IEEE TPEL/TTE/JESTPE/Access, IET 등 20건 + 표준·산업자료 3건). 학회지 2건은 선행기술 식별 목적으로만 인용.
