# 19. Simulink 스위칭 모델 구현 — 작업 인계 (2026-10-12 중단 시점)

이 문서는 중단한 작업을 다음 세션에서 그대로 이어 가기 위한 인계 기록이다. 진행 상태, 정해 둔 설계 결정, 회로 결선, 남은 위험, 재개 순서를 적었다. 부록에는 작성을 마친 코드 3개의 전문을 실었다(이 문서만으로 복원할 수 있게).

## 1. 목표와 제약

- **목표**: 제출용 형태의 Simulink(Simscape Electrical) 스위칭 모델. Stage A·B·C를 모두 스위칭 회로로 구성하고, 서브시스템·스위치 셀·Scope·주석으로 구조가 눈에 보이게 한다.
- **실행 제약**: 사용자 PC에서는 아무것도 실행하지 않는다(사용자 지시 "실행은 하지 말아줘"). 빌드 스크립트와 제어·게이트 코드를 작성해 파일로 전달하고, MATLAB 실행은 사용자가 직접 한다. MATLAB 없이 확인할 수 있는 부분은 작업 공간에서 Octave로 Python 검증 코드와 대조한다.
- **사용자 환경**: MATLAB R2024b, Simscape Electrical 있음.
- **문서 규칙**: 정식·제출 문서에는 저장소 주소나 경로를 넣지 않는다. 한국어로 쓰고, 아키텍처·검증 범위·검증이 필요한 이유를 중심으로 쓴다.

## 2. 진행 상태

| 항목 | 파일(패키지 기준) | 상태 |
|---|---|---|
| 파라미터·초기조건 | `prism_hub_params.m` | 작성, Octave 실행 확인(평형점, 데드타임 교정표가 Python과 일치). **부하 정의 수정 필요(3.4절)** |
| Stage B 제어기 | `ctrl/prism_stageB_controller.m` | 작성, Python 대조 전. **수정 1건 필요(3.2절)** |
| Stage B 게이트 생성기 | `ctrl/prism_gate_stageB.m` | 작성, 시험 전 |
| Stage A 게이트 생성기 | `ctrl/prism_gate_stageA.m` | 미작성(사양은 3.5절) |
| Stage C 게이트 생성기 | `ctrl/prism_gate_stageC.m` | 미작성(사양은 3.6절) |
| Octave 대조 시험 | `test/` | 미작성(계획은 6절) |
| 모델 빌드 스크립트 | `build_prism_hub_model.m` | 미작성(구조는 4·5절) |
| 실행 스크립트·설명서 | `run_prism_hub_case.m`, `README.md` | 미작성 |

## 3. 정해 둔 설계 결정

### 3.1 시간 구조(단일 속도)
- 모든 이산 블록과 Simscape 지역 해석기를 같은 간격 dt = 5 ns로 돌린다(Simulink 고정 간격 이산 해석기, 단일 태스킹). 다중 속도와 Rate Transition은 쓰지 않는다.
- 제어기 MATLAB Function도 dt마다 호출하되, 함수 안에서 k = round(t/dt), mod(k, Np) == 0일 때만 계산하고 나머지는 직전 출력을 유지한다(Np = 1000). 반송파 최댓값에서 표본하는 Python 모델과 같다.
- 제어기 출력 → Delay 블록(delay_steps = Np, 초기값 [I.m; I.ph]) → 게이트 생성기. Python의 전달지연 lag(기본 5 µs)와 같다.
- 게이트 생성기는 링크전류 주기 평균을 kin == Np−1에서 확정하므로, 다음 표본(kin == 0)의 제어기는 직전 주기 평균을 읽는다. Python은 간격 끝 값을, Simulink는 간격 시작 값을 누적하므로 dt 하나만큼 어긋난다(무시 가능).
- 실행 시간 부담: 6 ms는 120만 단계다. 처음에는 t_end 3–4 ms로 돌리고, 미리보기용으로 dt = 10 ns를 허용한다(데드타임 50·100 ns가 여전히 정수 간격).

### 3.2 제어기 수정 필요 사항(발견, 미반영)
- Python은 반주기 중심에서 위상을 적용할 때 그 시점의 측정 버스전압 vb_m으로 예측 전류 ip_c0·ip_c1을 계산한다. 따라서 다음 표본에서 쓰는 il_pred는 **직전 표본의 버스전압** 기준이다.
- 현재 MATLAB 제어기는 현재 표본의 vb로 il_pred를 계산한다. persistent `vb_prev`(첫 호출에서 y(3)로 초기화)를 두고 `ipred(ph_c0, vb_prev, …)`, `ipred(ph_c1, vb_prev, …)`로 바꾼 뒤 갱신 끝에서 `vb_prev = vb`로 둔다.
- 초기값 대응: Python의 il_meas = 초기 링크전류, il_pred = ipred(ph0), dph = 0은 게이트 생성기 초기값(il_avg = init(3), lat0 = lat1 = ph0)과 맞는다.

### 3.3 게이트 양자화
- H-브리지: 에지를 dt 격자에서 비교로 정한다(Python은 간격 안의 정확한 위치). 레그 듀티 분해능은 2dt/T = 0.2 %다. 실제 DSP의 PWM 카운터와 같은 성격이므로 차이로 기록만 한다.
- DAB: 예정 에지를 가장 가까운 간격에 반올림해 실행하고, 실제 실행 시각으로 A를 갱신하므로 직류 편류가 누적되지 않는다.

### 3.4 부하 정의(수정 필요)
- 400 V 보조버스 연속정격 25 kW에는 Stage C 입력이 포함된다(요구사항 문서 3.3절).
- 현재 파라미터는 정전력 부하(5 → 25 kW) 위에 Stage C 3 kW를 더해, 스텝 후 총부하가 28 kW로 정격을 넘는다.
- 수정안: `P0`, `P1`을 **버스 총부하**로 정의하고, 정전력 부하 = 총부하 − Stage C 입력 추정(P_o/0.97)으로 둔다. 기본 사례는 Tier-1 대표 스텝인 788 V, 15 → 25 kW(E12의 15 → 25 kW 사례와 같은 총부하)로 한다. 평형점은 총부하로 계산한다.

### 3.5 Stage A 게이트(고정 타이밍) 사양
- 위상당 4개 소자 S1–S4, 8위상(4모듈 × 2위상), 출력 32개.
- τ = mod(t − off, T), T = 1/f_s(f_s = 0.98 f_r0 ≈ 147 kHz). 전반주기: 데드타임 t_d(100 ns) 뒤 S1·S3 켬. 후반주기: 데드타임 뒤 S2·S4 켬. 켜짐 폭은 T/2 − t_d다(기존 TB-A1 하네스와 같은 타이밍).
- 인터리빙 오프셋 off = (동작 위상 순번) × T/(2N), 동작 위상만 마스크(P.gateA_en, P.gateA_off는 이미 계산됨).

### 3.6 Stage C 게이트 사양
- 250 kHz 고정, 50 % 상보 구형파, 데드타임 50 ns. 1차 풀브리지 Q1·Q4 / Q2·Q3. enable = 0이면 모두 끔. 2차는 다이오드 정류(동기정류 근사).

### 3.7 소자 구성
- 스위치 셀 서브시스템: Foundation `Switch`(파라미터 `R_closed`, `G_open`, `Threshold`) + 역병렬 `Diode` + 출력용량 `Capacitor` + `Simulink-PS Converter`. ee_lib 경로에 의존하지 않는다.
- H-브리지 출력용량 1 nF/소자(선형), DAB 소자에는 **100 pF**를 넣는다. Python 모델에는 DAB 출력용량이 없지만, 영전류 구간에서 열린 브리지 노드가 개방 컨덕턴스만으로 정해지는 수치 문제를 피하려는 것이다(차이로 기록).
- Stage C 정류: 다이오드 Ron 1 mΩ 정도, Vf는 작게. Python E10은 이상 동기정류이므로 출력이 약간 낮게 나올 수 있다.
- 정전력 부하: `Controlled Current Source`, i = P/max(v_bus, 50 V), 대수 루프를 피하려고 단위 지연을 둔다.
- 커패시터 초기전압: Initial Targets(`*_specify`, `*_priority`)로 평형점 값을 준다.
- MATLAB Function 내용 주입: `rt = sfroot; ch = rt.find('-isa','Stateflow.EMChart','Path',blk); ch.Script = fileread(...)`.
- 신호 배선: Goto/From 전역 태그. Scope 01–06(안): 01 Stage A(플라잉 커패시터 전류, V_A), 02 Stage B 주경로(i_p, v_s, v_bus), 03 H-브리지(i_h, v_link, PWM 비교값), 04 DAB(i_L, 링크전류, 위상), 05 Stage C(공진전류, 48 V), 06 제어 내부(m, 링크전류 지령, 전류지령, ρ̂, ε̂).

## 4. 회로 결선(빌드 스크립트 기준)

**Stage A, 위상당**(노드 VIN, A, B, VA, GND): S1 VIN→A, S2 A→VA, S3 VA→B, S4 B→GND, A–(R_misc)–Lr–Cfly–B 직렬. 전반주기 S1·S3로 Cfly가 출력과 직렬 충전, 후반주기 S2·S4로 방전. 배터리 = DC 전압원 + C_in 100 µF, V_A 노드에 C_out 400 µF(Python 모델에는 없는 추가 소자).

**Stage B 주경로**(노드 VA, N1, N2, BUS): VA → L_path 1.5 µH, R_path 3 mΩ → N1. C_s 100 µF는 N1(−)–N2(+). N2 = BUS(C_b 400 µF). 이렇게 두면 v_bus = v_N1 + v_s이고 C_s 전류 = i_h − i_p이다.

**H-브리지**(부유 링크 LINK+/LINK−, C_link 2 mF): 레그 A 노드 → L_h 5 µH, R_h 2 mΩ → N2, 레그 B 노드 → N1. 상측 소자는 LINK+–레그 노드, 하측은 레그 노드–LINK−.

**DAB**: BUS/GND → 1차 풀브리지 P1–P4 → L_dab 11.1 µH, R_dab 0.02 Ω → 이상 변압기 4:1 → 2차 풀브리지 S1–S4 → LINK+/LINK−. 상태 +1이면 1·4번 켬(1·2번 = 레그 1, 3·4번 = 레그 2, 홀수 = 상측).

**Stage C**: BUS/GND → 1차 풀브리지 Q1–Q4 → C_r1 36.8 nF → L_r1 11 µH → 변압기 1차(L_m 66 µH 병렬) → 이상 변압기 25/3:1 → L_r2 = L_r1/n², C_r2 = C_r1·n² → 다이오드 브리지 → C_o 470 µF ∥ R_load(48²/3 kW).

**계측**: i_p(주경로), i_h(L_h), i_L(L_dab), 링크전류(2차 브리지 → LINK+ 직류), v_s(N2−N1), v_bus, v_link, V_A, 플라잉 커패시터 전류, Stage C 공진전류, v_48.

## 5. 남은 위험과 확인 사항

1. **Simscape 포트 번호**: R2024b에는 포트 이름으로 잇는 `simscape.addConnection`이 없다(R2025a 도입). 따라서 `add_line`의 LConn/RConn 번호를 써야 한다. R, L, C, Diode, Electrical Reference는 LConn1 = +, RConn1 = −로 확실하지만, Switch의 제어 입력과 Current/Voltage Sensor의 출력 포트 위치는 확실하지 않다.
   - 대책: 빌드 스크립트에 포트 판별 도우미를 둔다(후보 포트에 차례로 연결을 시도하고, 끝에서 모델 갱신(update diagram)으로 결선 오류를 잡아 보고). 실패한 연결은 "수동 처리 목록"과 넷리스트로 출력한다.
   - R2025a 이상이면 `simscape.addConnection`(포트 이름 p, n 등)을 쓰도록 버전 분기한다.
2. **빌드 스크립트는 MATLAB에서 한 번도 실행되지 않았다.** 첫 실행은 사용자가 하며, 오류 메시지를 받아 고치는 반복이 필요하다.
3. **해석기 수렴**: 지역 해석기(Backward Euler, 5 ns)는 다이오드·스위치 모드 반복이 필요하다. 처음에는 고정 비용(fixed cost) 옵션을 끈다.
4. **실행 시간**: 3.1절 참고.
5. **검증 모델과의 차이**(README에 적을 것): 에지 양자화, DAB 출력용량 100 pF, C_out(V_A) 추가, Stage A 실제 스위칭 리플, DAB 손실 4 %(η = 0.96) 전류원 미포함(Simscape 회로 손실만), Stage C 다이오드 정류.

## 6. 재개 순서

1. 제어기에 3.2절 수정 반영. 파라미터에 3.4절 부하 정의 반영.
2. `ctrl/prism_gate_stageA.m`, `ctrl/prism_gate_stageC.m` 작성(3.5·3.6절).
3. Octave 대조 시험(`test/`):
   - 제어기: 임의 상태 다수에서 Python의 `_controller`, ρ̂·ε̂ 갱신, `_phase_ff`, `_ipred`, `deadtime_error_tab`과 출력 비교(1e-9 수준 일치 목표).
   - Stage B 게이트: H-브리지 듀티·데드타임 간격 수 확인. DAB는 버스·링크 전압을 고정한 이상 DAB(L_dab만)에 게이트를 넣고 위상 계단에서 직류 편류 ≈ 0, 정상상태 링크전류가 SPS 식과 맞는지 확인.
   - Stage A·C 게이트: 켜짐 폭, 데드타임, 인터리빙 오프셋 확인.
4. `build_prism_hub_model.m` 작성(4절 결선, 3.7절 구성, 5절 대책).
5. `run_prism_hub_case.m`, `README.md`(한국어: 구조, 결선표, 사용법, 기대 기준값, 알려진 위험) 작성.
6. 정적 점검(Octave 구문 검사, 시험) 후 파일로 전달. 사용자 PC 폴더에 복사할 때는 먼저 묻는다. 실행은 하지 않는다.

**참고할 기존 자료**: 검증 코드 패키지의 `python/model_stage_b_switching.py`(제어기·게이트 원본 알고리즘), `python/E10_stage_c_cllc.py`(Stage C), `matlab/build_rsc_phase.m`(Stage A 넷리스트·Simscape 빌드 선례), `matlab/build_pprc_average_tb.m`(MATLAB Function 내용 주입 방식), docs/04(Simulink 검증 대조표).

---

## 부록 A. prism_hub_params.m (작성 완료)

```matlab
function P = prism_hub_params(cs)
%PRISM_HUB_PARAMS  PRISM-Hub 스위칭 Simulink 모델의 파라미터·초기조건.
%
%   P = prism_hub_params()            기본 사례(788 V, 5 → 25 kW)
%   P = prism_hub_params(cs)          사례 구조체 cs의 필드로 기본값을 바꾼다.
%       cs.vbat      배터리 전압 [V]
%       cs.P0, cs.P1 400 V 보조부하(정전력) 스텝 전·후 [W]
%       cs.t_step    스텝 시각 [s]   (DAB 전류비 추정이 학습되도록 2 ms 이상 권장)
%       cs.t_end     시뮬레이션 종료 시각 [s]
%       cs.delay_extra 모델 밖 추가 지연 [s] (Tier 시험 +3.0 µs)
%       cs.stageA_modules  동작하는 Stage A 모듈 [1×4 논리] (주행 모드는 모듈 1만)
%       cs.stageC_enable   Stage C(48 V) 동작 여부
%
%   모델(PRISM_Hub_switching.slx)의 InitFcn이 이 함수를 불러 기본 작업공간에 P를 만든다.
%   부품값은 검증 코드(E1·E5–E14)와 같은 설계값이다. 제어기는 공칭값만 알고, 회로는 이 값으로 동작한다.

if nargin < 1, cs = struct(); end

%% ---------------- 시뮬레이션 공통 ----------------------------------------------------
S.dt         = 5e-9;        % 기본 적분 간격 = 게이트 생성 간격 = Simscape 지역 해석기 간격 [s]
S.Ts         = 5e-6;        % Stage B 제어주기(200 kHz, 반송파 최댓값에서 표본) [s]
S.vbat       = 788;
S.P0         = 5000;
S.P1         = 25000;
S.t_step     = 2e-3;
S.t_end      = 6e-3;
S.delay_extra = 0;
S.stageA_modules = [1 0 0 0];
S.stageC_enable  = 1;
fn = fieldnames(cs);
for k = 1:numel(fn), S.(fn{k}) = cs.(fn{k}); end
S.Np = round(S.Ts/S.dt);                         % 제어주기당 적분 간격 수(1000)
P.sim = S;

%% ---------------- Stage A: 2:1 공진 스위치드 커패시터(RSC), 4모듈 × 2위상 ----------------
A.Nmod   = 4;  A.Nph = 2;                        % 모듈 수, 모듈당 위상 수
A.Cfly   = 7.8125e-6;                            % 플라잉 커패시터 [F]
A.Lr     = 1.441e-7;                             % 공진 인덕턴스 [H]  → f_r0 ≈ 150 kHz
A.Rds    = 6e-3;                                 % 스위치 도통저항(750 V SiC 2병렬) [Ω]
A.ESR    = 1.5e-3;  A.RL = 1e-3;  A.Rmisc = 1.5e-3;
A.Vf     = 0.9;                                  % 바디 다이오드 순방향 전압 [V]
A.td     = 100e-9;                               % 데드타임 [s]
A.fr0    = 1/(2*pi*sqrt(A.Lr*A.Cfly));
A.fs     = 0.98*A.fr0;                           % 고정 타이밍(설계값 f_s/f_r = 0.98)
A.Cin    = 100e-6;                               % 배터리 측 입력 커패시터 [F]
A.Cout   = 400e-6;                               % V_A 노드(충전 포트) 출력 커패시터 [F]
A.Rout_est = 10.2e-3;                            % 1모듈 등가 출력저항(설계 추정, 초기조건용) [Ω]
A.modules = logical(S.stageA_modules(:)');
P.A = A;

%% ---------------- Stage B: 직렬 부분전력 조정기 ------------------------------------------
B.Lpath  = 1.5e-6;     B.Rpath = 3e-3;           % V_A → 직렬 포트 배선(Stage A 출력저항은 회로에서 생김)
B.Cs     = 100e-6;                               % 직렬 포트 커패시터
B.Cb     = 400e-6;                               % 400 V 보조버스 커패시터
B.Lh     = 5e-6;       B.Rh   = 2e-3;            % H-브리지 LC 필터
B.Clink  = 2e-3;                                 % 부유 링크 커패시터(100 V)
B.Ldab   = 11.1e-6;    B.Rdab = 0.02;            % DAB 누설 인덕턴스·권선저항(1차 환산)
B.n      = 4;                                    % DAB 권선비 4:1
B.fs     = 200e3;
B.td_h   = 50e-9;      B.td_d = 100e-9;          % H-브리지·DAB 데드타임
B.Coss_h = 1e-9;                                 % H-브리지 스위치 출력용량(선형) [F]
B.Ron    = 1e-4;                                 % 스위치 도통저항(경로 저항은 R_h·R_dab에 포함)
B.Vf     = 1e-3;                                 % 다이오드 순방향 전압(검증 모델은 이상 클램프)
B.R_dab_link = 0;                                % (예비)
P.B = B;

%% ---------------- Stage C: 대칭 CLLC 400 → 48 V, 3 kW ------------------------------------
C.n    = 25/3;                                   % 권선비
C.Lr1  = 11.0e-6;  C.Cr1 = 36.8e-9;              % 1차 공진망
C.Lm   = 66e-6;                                  % 자화 인덕턴스
C.Lr2  = C.Lr1/C.n^2;  C.Cr2 = C.Cr1*C.n^2;      % 2차 공진망(대칭, 1차 환산이 1차와 같음)
C.fs   = 250e3;                                  % 공진점 고정 주파수
C.td   = 50e-9;
C.Coss = 100e-12;
C.Co   = 470e-6;
C.Po   = 3000;
C.enable = logical(S.stageC_enable);
C.Rload = 48^2/C.Po;
if ~C.enable, C.Rload = 1e6; end
C.Ron  = 5e-3;   C.Vf = 0.05;                    % 1차 스위치·2차 정류 다이오드(동기정류 근사)
P.C = C;

%% ---------------- 부하 -----------------------------------------------------------------
L.P0 = S.P0;  L.P1 = S.P1;  L.t_step = S.t_step;
L.vmin = 50;                                     % 정전력 부하 전류 계산의 하한 전압(기동 보호)
P.load = L;

%% ---------------- Stage B 제어기(채택 설계) -------------------------------------------
% 공칭 파라미터(제어기 내부 모델). 경로 저항 R = 13.2 mΩ은 Stage A 출력저항 포함값이다.
cp = struct('L',1.5e-6,'Cs',100e-6,'Cb',400e-6,'R',0.0132,'Lh',5e-6,'Rh',0.002,'Clink',0.002, ...
            'Ts',S.Ts,'vref',400,'vlink',100,'mmax',0.95,'refmax',84,'link_max',80,'power_max',8000, ...
            'link_bw',1000,'itau',10e-6,'Ldab',11.1e-6,'fs',200e3,'turns',4,'phmax',pi/3);
K = [-1.5813581402097892, 1.1112552918606937, 1.539757867322121, 0.6419266519985994, -12686.999839382896];
est = struct('lmin',0.9,'gain',0.05,'min_A',40,'eps_gain',0.2,'eps_max',10);
comp = struct('scale',0.6,'from_A',20,'full_A',80,'Vtab',100,'enable',1);
P.cp = cp;  P.K = K;  P.est = est;  P.comp = comp;
% 제어기 상수 벡터(MATLAB Function 블록 입력). 순서는 ctrl/prism_stageB_controller.m 머리말 참고.
P.ctrl_prm = [cp.L cp.Cs cp.Cb cp.R cp.Lh cp.Rh cp.Clink cp.Ts cp.vref cp.vlink cp.mmax cp.refmax ...
              cp.link_max cp.power_max cp.link_bw cp.itau cp.Ldab cp.fs cp.turns cp.phmax K ...
              est.lmin est.gain est.min_A est.eps_gain est.eps_max ...
              comp.scale comp.from_A comp.full_A comp.Vtab 5 1 comp.enable];
% H-브리지 데드타임 교정표(전류별 상승 전이 한 번의 전압·시간 손실, 선형 출력용량 1 nF, 링크 100 V)
[ig, eg] = deadtime_table_linear(B.td_h, B.Coss_h, comp.Vtab);
P.ctrl_tab = [ig; eg];

%% ---------------- 초기조건: 평균모델 평형점 --------------------------------------------
Pc = C.Po * C.enable;                            % Stage C가 버스에서 가져가는 전력(근사)
[x0, u0] = stageB_equilibrium(S.vbat, S.P0 + Pc, cp);
ip0 = x0(1);
I.ip   = ip0;
I.VA   = S.vbat/2 - A.Rout_est*ip0;              % V_A 노드(Stage A 출력)
I.vs   = cp.vref - I.VA + B.Rpath*ip0;           % 직렬 포트(경로 저항 강하 포함)
I.vbus = cp.vref;
I.ih   = ip0;
I.vlink = cp.vlink;
I.m    = (I.vs + cp.Rh*I.ih)/cp.vlink;
I.il   = I.m*I.ih;
I.vcfly = S.vbat/2;
I.v48  = 48*cp.vref/400;
I.q    = -(ip0 + K(1:4)*[ip0; I.vs; cp.vref; I.ih])/K(5);
I.ph   = phase_ff(I.il, cp.vref, cp, est.lmin);
I.u0   = u0;
P.init = I;
P.ctrl_init = [I.q 0 I.m I.il];

%% ---------------- 게이트 생성기 상수 ---------------------------------------------------
dly = round((S.Ts + S.delay_extra)/S.dt);        % 계산 후 적용까지 지연(기본 1 제어주기 = 5 µs)
P.gateB_prm = [S.dt S.Np round(B.td_h/S.dt) round(B.td_d/S.dt) 1/B.fs];
P.gateB_init = [I.m I.ph I.il];                  % 초기 PWM 비교값, 초기 위상, 초기 링크전류(주기 평균 기록 초기값)
P.delay_steps = dly;
act = find(kron(A.modules, ones(1, A.Nph)));     % 동작 위상 번호(1–8)
offs = zeros(1, A.Nmod*A.Nph);
offs(act) = (0:numel(act)-1) * (1/A.fs) / (2*numel(act));   % 인터리빙 오프셋 T/(2N)
P.gateA_prm = [S.dt 1/A.fs A.td A.Nmod*A.Nph];
P.gateA_en  = double(kron(A.modules, ones(1, A.Nph)));
P.gateA_off = offs;
P.gateC_prm = [S.dt 1/C.fs C.td double(C.enable)];
end

%% =======================================================================================
function [x, u] = stageB_equilibrium(vbat, power, cp)
% 평균모델 평형점(model_stage_b.equilibrium과 같은 식). DAB 효율 0.96.
eta = 0.96;
plink = @(ip) (cp.vref - vbat/2 + cp.R*ip + cp.Rh*ip).*ip;
pin = @(pl) pl/eta.*(pl >= 0) + pl*eta.*(pl < 0);
balance = @(ip) cp.vref*ip - power - pin(plink(ip));
ip = fzero(balance, [-500 500]);
vs = cp.vref - vbat/2 + cp.R*ip;
m = (vs + cp.Rh*ip)/cp.vlink;
x = [ip vs cp.vref ip cp.vlink m*ip];
u = [m m*ip];
end

function ph = phase_ff(il, vb, cp, lbasis)
% 링크전류 → SPS 위상(누설 인덕턴스를 공칭의 lbasis배로 가정)
k = cp.turns*max(vb, 1)/(2*pi*cp.fs*cp.Ldab*lbasis);
a = min(abs(il)/(pi*k/4), 1);
ph = min(pi/2*(1 - sqrt(1 - a)), cp.phmax);
if il < 0, ph = -ph; end
end

function [ig, eg] = deadtime_table_linear(td, C, V)
% 데드타임 교정표: 레그 노드를 0 V에서 시작해 dv/dt = −i/C_node(0–V 클램프)로 데드타임 동안 적분하고
% 잃는 전압·시간 ∫(V − v)dt를 구한다(C_node = 두 스위치 출력용량의 합 = 2C). 검증 코드와 같은 계산.
ig = [-logspace(2, -2, 81), 0, logspace(-2, 2, 81)];
n = 2000; h = td/n;
v = zeros(size(ig)); lost = zeros(size(ig));
cn = 2*C;
for s = 1:n                                      % 용량이 일정하므로 중점법 = 오일러
    vn = min(max(v + h*(-ig/cn), 0), V);
    lost = lost + (V - 0.5*(v + vn))*h;
    v = vn;
end
eg = lost;
end
```

## 부록 B. ctrl/prism_stageB_controller.m (작성 완료, 3.2절 수정 미반영)

```matlab
function [u, dg] = prism_stageB_controller(y, prm, init, tab)
%#codegen
%PRISM_STAGEB_CONTROLLER  Stage B 채택 제어기 1회 계산(제어주기 5 µs, 반송파 최댓값에서 표본).
%
%  검증 코드(model_stage_b_switching.run_core의 제어 부분)와 같은 법칙이다.
%   (1) 1주기 예측: 고속 상태 [i_p, v_s, i_h]를 직전 변조율로 5 µs 앞까지 공칭 모델로 적분(중점법 5단계)
%   (2) 상태궤환 + 버스전압 적분 → 브리지 전류지령(±84 A 포화, 역포화 보정)
%   (3) 내부 전류 법칙 → 변조율 m(±0.95)
%   (4) 링크전압 PI + 소비전류 앞먹임 → DAB 링크전류 지령(정격 80 A·8 kW·SPS 한계)
%   (5) DAB 링크전류 → 위상: 누설 인덕턴스 −10 % 기준 앞먹임 + 측정 전류비 ρ̂ 보정 + 저전류 가산 보정 ε̂
%   (6) H-브리지 데드타임 보상: 교정표 × 전류 스케줄 κ(20 A 이하 0.6 → 80 A 1.0)
%
%  입력
%   y    = [i_p v_s v_bus i_h v_link V_bat i_link_avg ph_c0 ph_c1]  (표본값)
%          i_link_avg : 직전 제어주기의 DAB 링크 직류전류 평균(측정)
%          ph_c0/ph_c1: 그 주기의 두 반주기 중심에서 적용된 유효 위상(게이트 생성기가 기록)
%   prm  = 상수 벡터(prism_hub_params의 P.ctrl_prm)
%           1 L  2 Cs  3 Cb  4 R  5 Lh  6 Rh  7 Clink  8 Ts  9 vref  10 vlink  11 mmax  12 refmax
%          13 link_max  14 power_max  15 link_bw  16 inner_tau  17 Ldab  18 fs  19 turns  20 phmax
%          21–25 K  26 lmin(0.9)  27 ρ̂ 이득  28 ρ̂ 최소 전류  29 ε̂ 이득  30 ε̂ 상한
%          31 κ 경부하 비율  32 κ 시작 전류  33 κ 1 도달 전류  34 교정표 기준 링크전압  35 예측 단계 수
%          36 예측 사용(1)  37 데드타임 보상 사용(1)
%   init = [q0 q_link0 m0 i_link0]   (평형점에서 시작: 적분기가 지령 = i_p가 되도록)
%   tab  = [i_grid; E(i)]            데드타임 교정표(전류별 상승 전이 한 번의 전압·시간 손실)
%  출력
%   u  = [PWM 비교값(데드타임 보상 후); DAB 유효 위상 지령 rad]
%   dg = [m 지령(보상 전); 링크전류 지령; 브리지 전류지령; ρ̂; ε̂; 예측 링크전류]

persistent q qlink mprev rho epsA started
if isempty(started)
    q = init(1); qlink = init(2); mprev = init(3); rho = 1; epsA = 0; started = 1;
end

L = prm(1); Cs = prm(2); R = prm(4); Lh = prm(5); Rh = prm(6); Clink = prm(7); Ts = prm(8);
vref = prm(9); vlink = prm(10); mmax = prm(11); refmax = prm(12);
link_max = prm(13); power_max = prm(14); link_bw = prm(15); itau = prm(16);
Ldab = prm(17); fs = prm(18); turns = prm(19); phmax = prm(20);
K = prm(21:25);
lmin = prm(26); est_g = prm(27); est_min = prm(28); eps_g = prm(29); eps_max = prm(30);
k_scale = prm(31); k_from = prm(32); k_full = prm(33); Vtab = prm(34); nsub = prm(35);

ip = y(1); vs = y(2); vb = y(3); ih = y(4); vl = y(5); vbat = y(6);
il_meas = y(7); ph_c0 = y(8); ph_c1 = y(9);

% ---- (1) 1주기 예측 -----------------------------------------------------------------
sip = ip; svs = vs; sih = ih;
if prm(36) > 0.5
    m = mprev; h = Ts/nsub;
    for s = 1:nsub
        a1 = (vbat/2 - R*sip + svs - vb)/L;
        a2 = (sih - sip)/Cs;
        a3 = (m*vl - svs - Rh*sih)/Lh;
        mp = sip + 0.5*h*a1;  mv = svs + 0.5*h*a2;  mh = sih + 0.5*h*a3;
        b1 = (vbat/2 - R*mp + mv - vb)/L;
        b2 = (mh - mp)/Cs;
        b3 = (m*vl - mv - Rh*mh)/Lh;
        sip = sip + h*b1;  svs = svs + h*b2;  sih = sih + h*b3;
    end
end
% ---- (2) 상태궤환 + 적분 -----------------------------------------------------------
raw  = -(K(1)*sip + K(2)*svs + K(3)*vb + K(4)*sih) - K(5)*q;
iref = min(refmax, max(-refmax, raw));
q = q + Ts*(vref - vb) + 0.1*(iref - raw)/(-K(5));
% ---- (3) 내부 전류 법칙 → 변조율 ---------------------------------------------------
vlx = max(vl, 1);                                % (보상 계산용 하한)
mraw = (svs + Rh*sih + Lh/itau*(iref - sih))/vl;
mcmd = min(mmax, max(-mmax, mraw));
% ---- (4) 링크전압 PI + 앞먹임 → DAB 링크전류 지령 ---------------------------------
w = 2*pi*link_bw;
rawlink = mcmd*sih + Clink*(2*0.7*w*(vlink - vl) + w*w*qlink);
sps = max(vb, 0)*turns*phmax*(1 - phmax/pi)/(2*pi*fs*Ldab);
lim = min(min(link_max, sps), power_max/max(vl, 1e-9));
icmd = min(lim, max(-lim, rawlink));
qlink = qlink + Ts*(vlink - vl) + 0.1*(icmd - rawlink)/(Clink*w*w);
mprev = mcmd;
% ---- (5) DAB 전류비·저전류 보정 → 위상 ----------------------------------------------
il_pred = 0.5*(ipred(ph_c0, vb, turns, fs, Ldab, lmin) + ipred(ph_c1, vb, turns, fs, Ldab, lmin));
dph = abs(ph_c1 - ph_c0);
if abs(il_pred) >= est_min && il_meas*il_pred > 0 && dph < 0.035
    rho = rho + est_g*(il_meas/il_pred - rho);
    rho = min(max(rho, 0.75), 1.25);
end
if eps_g > 0
    if abs(il_pred) < est_min && dph < 0.035
        epsA = epsA + eps_g*((il_meas - rho*il_pred) - epsA);
    elseif abs(il_pred) >= est_min
        epsA = epsA - eps_g*epsA;
    end
    epsA = min(max(epsA, -eps_max), eps_max);
end
ph_new = phase_ff((icmd - epsA)/rho, vb, turns, fs, Ldab, lmin, phmax);
% ---- (6) H-브리지 데드타임 보상 ----------------------------------------------------
m_pwm = mcmd;
if prm(37) > 0.5
    kap = k_scale + (1 - k_scale)*min(max((abs(sih) - k_from)/max(k_full - k_from, 1e-9), 0), 1);
    m_pwm = mcmd - kap*dt_error_tab(mcmd, sih, vlx, Lh, fs, tab, Vtab)/vlx;
end
u  = [m_pwm; ph_new];
dg = [mcmd; icmd; iref; rho; epsA; il_pred];
end

% ======================================================================================
function i = ipred(ph, vb, turns, fs, Ldab, lb)
% 위상 ph에서 SPS 식이 주는 링크전류(누설 인덕턴스 = 공칭의 lb배 가정)
k = turns*max(vb, 1)/(2*pi*fs*Ldab*lb);
i = k*ph*(1 - abs(ph)/pi);
end

function ph = phase_ff(il, vb, turns, fs, Ldab, lb, phmax)
% 링크전류 → SPS 위상 앞먹임(|φ| ≤ φ_max)
k = turns*max(vb, 1)/(2*pi*fs*Ldab*lb);
a = min(abs(il)/(pi*k/4), 1);
ph = min(pi/2*(1 - sqrt(1 - a)), phmax);
if il < 0, ph = -ph; end
end

function d = dt_error_tab(m, i, V, Lh, f, tab, Vtab)
% 유니폴라 PWM 한 주기의 브리지 평균 전압오차 [V]: 리플 극값 전류에서의 전이별 손실을 교정표에서 읽는다.
sg = 1;
if m < 0, m = -m; i = -i; sg = -1; end
r = V*m*(1 - m)/(4*Lh*f);
imin = i - r; imax = i + r;
d = sg*2*(tab_interp(-imax, tab) - tab_interp(imin, tab))*(V/Vtab)*f;
end

function e = tab_interp(x, tab)
% 선형 보간(범위 밖은 끝값) — numpy.interp와 같음
n = size(tab, 2);
if x <= tab(1, 1), e = tab(2, 1); return; end
if x >= tab(1, n), e = tab(2, n); return; end
lo = 1; hi = n;
while hi - lo > 1
    mid = floor((lo + hi)/2);
    if tab(1, mid) <= x, lo = mid; else, hi = mid; end
end
w = (x - tab(1, lo))/(tab(1, hi) - tab(1, lo));
e = tab(2, lo) + w*(tab(2, hi) - tab(2, lo));
end
```

## 부록 C. ctrl/prism_gate_stageB.m (작성 완료, 시험 전)

```matlab
function [g, aux] = prism_gate_stageB(t, uc, ilink, prm, init)
%#codegen
%PRISM_GATE_STAGEB  Stage B 게이트 생성기(적분 간격 dt = 5 ns마다 실행).
%
%  H-브리지 : 유니폴라 PWM. 삼각 반송파 c(t)는 제어주기 시작(표본 시점)에서 +1, 반주기에서 −1.
%             레그 A 상측 목표 = (m > c), 레그 B 상측 목표 = (−m > c). 목표가 바뀌면 두 소자를 데드타임 동안
%             끄고(출력용량 충방전·다이오드 도통은 회로가 정함) 새 소자를 켠다.
%  DAB      : 50 % 구형파 두 풀브리지, 단일 위상천이. 에지는 반송파 반주기 중심 c_j에 대칭(1차 c_j − δ/2,
%             2차 c_j + δ/2, δ = φ·T/2π)으로 놓고, 지령은 도착 후 첫 반주기 중심에서 반영한다.
%             전이 반주기의 위상차를 이전·새 위상의 평균으로 두는 갱신(A ← −A + 2Δ, Δ = (A + δ_new)/2)으로
%             위상이 바뀔 때 변압기 직류 편류가 생기지 않게 한다(검증 코드와 같은 알고리즘).
%             에지 시각은 dt 격자에 반올림하고, 실제 실행 시각으로 다음 반주기의 A를 계산한다.
%  링크전류 : DAB 2차 브리지가 링크로 보내는 직류전류를 제어주기마다 평균해 다음 표본에 넘긴다.
%
%  입력  t      시뮬레이션 시각(Digital Clock, dt 간격)
%        uc     [PWM 비교값; DAB 유효 위상 rad]  (제어기 출력, 전달지연 뒤)
%        ilink  DAB 2차 브리지 → 링크 직류전류 [A](순시)
%        prm    [dt Np td_h(간격 수) td_d(간격 수) T]
%        init   [PWM 비교값 초기값, 위상 초기값, 링크전류 초기값]
%  출력  g      [A상측 A하측 B상측 B하측 | P1 P2 P3 P4 | S1 S2 S3 S4]  (1 = 켬)
%               DAB 브리지: 상태 +1 → 1·4번 켬, −1 → 2·3번 켬(1·2번이 레그 1, 3·4번이 레그 2, 홀수 = 상측)
%        aux    [링크전류 주기 평균; 그 주기 두 반주기 중심의 위상 φ_c0, φ_c1; 반송파; 1차 상태; 2차 상태]

persistent started kA kB tgtA tgtB A ph_tgt p_t s_t p_h s_h p_j s_j p_state s_state p_te s_te ...
           acc il_avg phc0 phc1 lat0 lat1
dt = prm(1); Np = prm(2); ndh = prm(3); ndd = prm(4); T = prm(5);
Nh = round(Np/2);
k  = round(t/dt);                     % 적분 간격 번호(0부터)
t0 = k*dt;

if isempty(started)
    started = 1;
    m0 = init(1); ph0 = init(2);
    c0 = 1;                            % k = 0의 반송파
    tgtA = double(m0 > c0); tgtB = double(-m0 > c0);
    kA = -1e9; kB = -1e9;              % 데드타임 없이 시작
    ph_tgt = ph0;
    d0 = ph0/(2*pi)*T;
    A = d0;
    p_t = [1e30 1e30]; s_t = [1e30 1e30]; p_h = [0 0]; s_h = [0 0];
    p_te = -1; s_te = -1;
    if d0 > 0
        p_j = 1; p_h(1) = -d0/2; p_state = 1;  s_j = 0; s_state = -1;
    elseif d0 < 0
        s_j = 1; s_h(1) = d0/2;  s_state = 1;  p_j = 0; p_state = -1;
    else
        p_j = 0; s_j = 0; p_state = -1; s_state = -1;
    end
    acc = 0; il_avg = init(3); phc0 = ph0; phc1 = ph0; lat0 = ph0; lat1 = ph0;
end

m = uc(1);
ph_tgt = uc(2);

% ---------------- H-브리지 유니폴라 PWM -------------------------------------------------
kin = mod(k, Np);
c = 4*abs(kin/Np - 0.5) - 1;
nA = double(m > c); nB = double(-m > c);
if nA ~= tgtA, tgtA = nA; kA = k; end
if nB ~= tgtB, tgtB = nB; kB = k; end
okA = (k - kA) >= ndh; okB = (k - kB) >= ndh;
gA_hi = double(okA && tgtA == 1); gA_lo = double(okA && tgtA == 0);
gB_hi = double(okB && tgtB == 1); gB_lo = double(okB && tgtB == 0);

% ---------------- DAB 위상 갱신(반주기 중심) --------------------------------------------
if mod(k, Nh) == 0
    j = k/Nh; cj = t0;
    if j >= 1
        jm = mod(j - 1, 2) + 1;
        A = -A + 2*(s_h(jm) - p_h(jm));
    end
    dtg = ph_tgt/(2*pi)*T;
    D = 0.5*(A + dtg);
    jj = mod(j, 2) + 1;
    p_done = p_j > j; s_done = s_j > j;
    if p_done && ~s_done
        s_t(jj) = max(cj, p_h(jj) + D);
    elseif s_done && ~p_done
        p_t(jj) = max(cj, s_h(jj) - D);
    elseif ~p_done && ~s_done
        if D >= 0
            p_t(jj) = cj; s_t(jj) = cj + D;
        else
            s_t(jj) = cj; p_t(jj) = cj - D;
        end
    end
    if p_done, tpj = p_h(jj); else, tpj = p_t(jj); end
    if s_done, tsj = s_h(jj); else, tsj = s_t(jj); end
    D1 = 0.5*(-A + 2*(tsj - tpj) + dtg);
    cn = (j + 1)*Nh*dt;
    p_t(3 - jj) = cn - D1/2; s_t(3 - jj) = cn + D1/2;
    if mod(j, 2) == 0, phc0 = ph_tgt; else, phc1 = ph_tgt; end
end
% ---------------- DAB 에지 실행(가장 가까운 간격에 반올림) ------------------------------
sp = mod(p_j, 2) + 1;
if p_t(sp) < t0 + 0.5*dt
    if mod(p_j, 2) == 0, p_state = 1; else, p_state = -1; end
    p_te = t0; p_h(sp) = t0; p_t(sp) = 1e30; p_j = p_j + 1;
end
ss = mod(s_j, 2) + 1;
if s_t(ss) < t0 + 0.5*dt
    if mod(s_j, 2) == 0, s_state = 1; else, s_state = -1; end
    s_te = t0; s_h(ss) = t0; s_t(ss) = 1e30; s_j = s_j + 1;
end
p_ok = (t0 - p_te) >= ndd*dt - 0.5*dt;
s_ok = (t0 - s_te) >= ndd*dt - 0.5*dt;
gP = [0 0 0 0]; gS = [0 0 0 0];
if p_ok
    if p_state > 0, gP = [1 0 0 1]; else, gP = [0 1 1 0]; end
end
if s_ok
    if s_state > 0, gS = [1 0 0 1]; else, gS = [0 1 1 0]; end
end

% ---------------- 링크전류 주기 평균(표본 직전 간격에서 확정) -------------------------
acc = acc + ilink;
if kin == Np - 1
    il_avg = acc/Np; acc = 0;
    lat0 = phc0; lat1 = phc1;
end

g = [gA_hi gA_lo gB_hi gB_lo gP gS]';
aux = [il_avg; lat0; lat1; c; p_state; s_state];
end
```
