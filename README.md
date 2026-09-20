# PRISM-Hub

**P**artial-power **R**egulated, fixed-ratio **I**ntegrated, **S**oft-switched **M**ulti-port **Hub** — 800 V 전기자동차용 통합 DC 전력 허브 (MATLAB/Simulink 시뮬레이션 연구)

> 이 README는 프로젝트의 **현재 상태 요약**이며 지속적으로 갱신된다. 상세 근거는 `docs/`의 두 문서, 재현은 `matlab/`·`python/`, 진행 이력은 `logs/EXECUTION_LOG.md`와 `CHANGELOG.md`를 본다.

최종 갱신: 2026-09-20 | 상태: **WP1 완료, WP3 Stage A 검증 완료, PPRC 제어 검증 완료, ARL-MPC 검증 대기**

---

## 1. 한 줄 요약

배터리 640–920 V를 **2:1 고정비 공진형 스위치드-커패시터**(개루프 ZCS, 150 kW)로 400 V 중간버스에 연결하고, 전압 조정은 **8 kW 부분전력 직렬 셀(절연 DAB)** 하나에 몰아넣으며, 48/12 V는 **고정이득 CLLC**로 공급하는 단일 장치. 400 V 급속충전기는 2:1 고정비만으로 호환된다(충전 모드에서 직렬 셀 바이패스). 제어 측에서는 차량 선행 신호로 부하를 예측해 **직렬 셀의 포화를 회피**하는 계층(ARL → SALS로 개명 검토 중)을 얹는다.

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
| TB-S6 | ARL-MPC (제약 인지) | — | **다음** |
| TB-C1/C2 | CLLC 이득·ZVS·양방향 | — | 대기 |
| TB-B3 | 바이패스 전이 | — | 대기 |
| TB-S2~S5 | 충전 CC-CV, 800 V 충전, V2L, 전압 스윕 | — | 대기 |

## 5. 검증 과정에서 바뀐 결정 (요약)

1. 충전 모드 PPRC 바이패스 → 정격 25 % → 8 kW (5.3 %)
2. 12 V: 3권선 CLLC 불가(0.75턴) → 48→12 V 벅
3. 주행 모드 Stage A 위상 셰딩(1모듈)
4. f_s = 0.98 f_r → 자기발진 ZC 추종(블랭킹 창 0.80–1.12) + C_in 100 µF
5. PPRC 제어: PI 캐스케이드 → 상태궤환 + 적분
6. ARL 기여: "droop 절감·캡 축소" → **"PPRC 포화 예측 회피(부하 셰이핑)" + "제약 인지 MPC"**

## 6. 저장소 구조

```
docs/   01_제안서_EV컨버터_아키텍처.md   상위 제안서 (조사·아키텍처·ARL 개념·WP·KPI·참고문헌 23건)
        02_엔지니어링_설계검증서.md     적용 대상 → 비교 → 수치 검증 → Simulink 가이드 → 테스트벤치 → 검토, 부록 A–C
        fig/                            수치 검증·시뮬레이션 그래프
matlab/ prism_design_params.m           WP1 파라미터 스크립트 (모든 수식) → prism_params.mat
        tb_a1_rsc_phase.m               TB-A1 단상 셀 스위칭 ODE (Simulink 불필요)
        tb_a_array.m                    8위상 어레이, 자기발진 ZC, TB-A2/A3/A4, 몬테카를로
        tb_b_pprc.m                     PPRC 상태궤환 설계(place) + TB-S1 (Control System Toolbox)
        build_rsc_phase.m               Simscape Electrical 모델 자동 생성 (수동 확인 목록 출력)
python/ calc.py, tb_a1_sim.py, tb_a_array.py, tb_b_pprc2.py   위 MATLAB과 동일한 계산의 검증용 원본
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
build_rsc_phase          % Simulink 모델 생성 (실행 전 prism_design_params)
```
```bash
# Python 3.10+ (numpy, scipy, matplotlib)
cd python
python calc.py                 # 3장 수치 설계
python tb_a1_sim.py            # TB-A1
python tb_a_array.py mc|a2|a3|a4
python tb_b_pprc2.py           # TB-B2/S1
```

## 8. 다음 단계

1. TB-S6: ARL-MPC — 제약 |i_dab| ≤ 100 A 명시, s = 0.25·0.5에서 안정화 여부 → 제어 기여 범위 결정
2. TB-C1/C2: CLLC 스위칭 모델(이득·ZVS·양방향 전환)
3. TB-B3, TB-S2: 바이패스 전이, 150 kW CC-CV 충전
4. 설계검증서 2.4·3.5·4.3.3·KPI 6 본문 재작성(부록 C 반영), 제어 계층 명칭 ARL → SALS 결정
5. 선행기술 전수 검색(IEEE Xplore, Google Patents, Espacenet)

## 9. 참고문헌

설계검증서 7장(IEEE TPEL/TTE/JESTPE/Access, IET 등 20건 + 표준·산업자료 3건). 학회지 2건은 선행기술 식별 목적으로만 인용.
