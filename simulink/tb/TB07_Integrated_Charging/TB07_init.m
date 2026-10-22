%TB07_INIT  TB07(통합 회로 모델, 충전 모드) 초기화: 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   회로: 배터리(이상 전압원) → Stage A 4모듈(8위상 RSC, 영교차 추종 게이트) → V_A 노드(C_A 400 µF)
%         ∥ 400 V급 충전기(전류원, 지령 프로파일) → 경로(3 mΩ, 1.5 µH) → Stage B(TB06과 같은 회로·채택 제어기)
%         → 400 V 버스(C_b 400 µF) ∥ Stage C(대칭 CLLC 3 kW → 48 V 저항부하) ∥ 정전력 부하 ∥ DAB 손실 등가
%   사례: 기본 작업공간 변수 TB07_case(없으면 'A_640V_chg_15to25kW').
%         A 640 V, 충전 375 A 일정, 버스 총부하 15 → 25 kW(2 ms)            — 충전 중 동시 운전(Tier-1)
%         B 920 V, 버스 25 kW, 충전 326 A → 0(2 ms, 10 µs, 비상 정지)      — 충전기 해제(Tier-2)
%         C 788 V, 버스 5 kW, 충전 0 → 375 A(2 ms, 10 µs)                  — 충전기 접속(Tier-2)
%   기준값: ref/TB07_<사례>_init.json·_rec.csv·_wave.csv(E16 스위칭 모델: E12 엔진에 충전 경로 전원 적용),
%           _stageA.json(E1, 8위상, 같은 평균 출력전류 = 경로전류 − 충전전류)
%   선택: 기본 작업공간 변수 TB07_opts(구조체) — dt(적분 간격, 기본 5 ns)
%
%   초기조건: 경로·직렬·버스·링크는 E16 기준 모델의 평형점(경로 전원 V_bat/2 + R_A·i_ch, R = R_A + 3 mΩ,
%   R_A = 10.2 mΩ/4), V_A = V_bat/2 + R_A·(i_ch − i_p), C_fly = V_bat/2, 공진 인덕터 전류 0, Stage C는 TB06과 같다.
%   Stage A·Stage C는 정확한 주기 정상상태에서 시작하지 않으므로 처음 1 ms는 판정에서 뺀다(전환·계단은 2 ms).

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');

if evalin('base', 'exist(''TB07_case'', ''var'')')
    caseName = evalin('base', 'TB07_case');
else
    caseName = 'A_640V_chg_15to25kW';
end
ov = struct();
if evalin('base', 'exist(''TB07_opts'', ''var'')'), ov = evalin('base', 'TB07_opts'); end
R0 = jsondecode(fileread(fullfile(refDir, ['TB07_' caseName '_init.json'])));
cs = struct('vbat', R0.vbat, 'P0', R0.P0, 'P1', R0.P1, 't_step', R0.t_step, 't_end', R0.t_end, ...
    'stageA_modules', [1 1 1 1], 'stageC_enable', 1);
cs.dt = 5e-9;
if isfield(ov, 'dt'), cs.dt = ov.dt; end
P = prism_hub_params(cs);              % 제어기 파라미터는 주행과 같다(공칭 경로저항 13.2 mΩ, V_bat 측정값)

TB = struct();
TB.name  = 'TB07_Integrated_Charging';
TB.case  = caseName;
TB.dt    = P.sim.dt;
TB.Np    = P.sim.Np;
TB.vbat  = R0.vbat;
TB.t_eval = 1e-3;                      % 판정 시작 시각(초기 정착 구간 제외)
TB.tier  = R0.tier;                    % 판정 등급(1: 동시 운전, 2: 모드 전환)

% ---- Stage A: 4모듈(위상 1–8), 영교차 추종 ------------------------------------------------------
TB.A       = P.A;
TB.A.Goff  = 1e-8;  TB.A.Rd = P.A.Rds;  TB.A.Goffd = 1e-8;
TB.A.vC0   = TB.vbat/2;
TB.A.CA    = P.A.Cout;                 % V_A 노드 출력 커패시터 400 µF
TB.A.RA    = P.A.Rout_est/4;           % 4모듈 등가 출력저항 추정 2.55 mΩ(초기 V_A 계산용)
t_on  = 0.5/P.A.fr0 - P.A.td;
TB.gateA_zcp_prm = [TB.dt, round(P.A.td/TB.dt), round(0.80*t_on/TB.dt), round(1.12*t_on/TB.dt), ...
                    round(20e-9/TB.dt), 0.5];
TB.gateA_en  = ones(1, 8);
Thalf = round(0.5/P.A.fr0/TB.dt);
TB.gateA_off = round((0:7)*Thalf/8);   % 8위상 인터리빙 T/16(검증 모델 E1과 같은 오프셋 k·T/(2N))

% ---- 충전기 ---------------------------------------------------------------------------------------
TB.chg_prm = R0.chg_prm(:)';           % [i0 i1 t_sw t_ramp] (ctrl/prism_charger_profile.m)
TB.ich0    = TB.chg_prm(1);

% ---- 경로와 Stage B(TB06과 같음) -------------------------------------------------------------------
TB.Rpath = P.B.Rpath;
TB.Lpath = P.B.Lpath;
TB.Cb    = P.B.Cb;
TB.B = P.B;
TB.B.Goff   = 1e-8;  TB.B.Rd = P.B.Ron;  TB.B.Goffd = 1e-8;
TB.B.Coss_dp = 335e-12;
TB.B.Coss_ds = 1371e-12;
TB.B.Coss_d  = TB.B.Coss_dp;

x0 = R0.x0;
TB.ip0 = x0(1); TB.vs0 = x0(2); TB.vb0 = x0(3); TB.ih0 = x0(4); TB.vl0 = x0(5);
TB.vA0 = TB.vbat/2 + TB.A.RA*(TB.ich0 - TB.ip0);
m0 = R0.u0(1); il0 = R0.u0(2);
TB.ctrl_prm  = P.ctrl_prm;
TB.ctrl_tab  = P.ctrl_tab;
TB.ctrl_init = [R0.q0 0 m0 il0];
TB.smp       = [TB.dt TB.Np];
TB.delay_steps = P.delay_steps;
TB.uc0       = [m0; R0.ph0];
TB.gate_prm  = P.gateB_prm;
TB.gate_init = [m0 R0.ph0 il0];
TB.loss_prm  = [TB.dt TB.Np R0.eta TB.B.Rdab];
TB.ploss0    = R0.ploss0;

% ---- Stage C(TB06과 같음) -------------------------------------------------------------------------
TB.C = P.C;
TB.C.Goff = 1e-8;  TB.C.Rd = P.C.Ron;  TB.C.Goffd = 1e-8;
TB.C.Vf_rect = 1e-3;  TB.C.Ron_rect = 1e-4;
TB.Po_C  = 3000;
TB.RL_C  = 48^2/TB.Po_C;
TB.vo0   = 47.68;
TB.Pc_in = 2994;
TB.gateC_prm = [TB.dt 1/P.C.fs P.C.td 1];
TB.vo_TB05 = 47.683;
if abs(TB.dt - 2.5e-9) < 1e-12, TB.vo_TB05 = 47.833; end

% ---- 버스 부하 ------------------------------------------------------------------------------------
TB.P0tot = R0.P0;  TB.P1tot = R0.P1;
TB.P0 = R0.P0 - TB.Pc_in;
TB.P1 = R0.P1 - TB.Pc_in;
TB.t_step = R0.t_step;  TB.t_end = R0.t_end;
TB.vmin = P.load.vmin;

TB.guard_t    = 1.5*TB.dt;
TB.meas0      = [TB.ip0 TB.vs0 TB.vb0 TB.ih0 TB.vl0];
TB.loss_meas0 = [TB.vl0 il0 0 TB.vb0];

assignin('base', 'P', P);
assignin('base', 'TB', TB);
