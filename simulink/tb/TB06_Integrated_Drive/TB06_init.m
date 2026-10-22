%TB06_INIT  TB06(통합 회로 모델, 주행 모드) 초기화: 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   회로: 배터리(이상 전압원) → Stage A 모듈 1(2위상 RSC, 영교차 추종 게이트) → V_A 노드(C_A 400 µF)
%         → 경로(3 mΩ, 1.5 µH) → Stage B(TB04B와 같은 회로·채택 제어기, DAB 후보 소자 출력용량)
%         → 400 V 버스(C_b 400 µF) ∥ Stage C(대칭 CLLC 3 kW → 48 V 저항부하) ∥ 정전력 부하 ∥ DAB 손실 등가
%   사례: 기본 작업공간 변수 TB06_case(없으면 'A_640V_15to25kW'). 부하 P0, P1은 버스 총부하(Stage C 입력 포함)이며,
%         정전력 부하 = 총부하 − Stage C 입력 추정(TB05 3 kW, 5 ns: 2994 W)이다.
%   기준값: ref/TB06_<사례>_init.json·_rec.csv·_wave.csv(E12, Stage A 등가 전원), _stageA.json(E1, 2위상)
%   선택: 기본 작업공간 변수 TB06_opts(구조체) — dt(적분 간격, 기본 5 ns)
%
%   초기조건(평형점 근처): 경로전류·직렬전압·버스·링크는 E12 평형점, V_A = V_bat/2 − R_A·i_p(R_A = Stage A 1모듈 등가
%   출력저항 추정 10.2 mΩ), C_fly = V_bat/2, 공진 인덕터 전류 0, Stage C 공진망 0·출력 47.68 V(TB05 5 ns 정상값).
%   Stage A·Stage C는 정확한 주기 정상상태에서 시작하지 않으므로 처음 1 ms는 판정에서 뺀다(부하 계단은 2 ms).

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');

if evalin('base', 'exist(''TB06_case'', ''var'')')
    caseName = evalin('base', 'TB06_case');
else
    caseName = 'A_640V_15to25kW';
end
ov = struct();
if evalin('base', 'exist(''TB06_opts'', ''var'')'), ov = evalin('base', 'TB06_opts'); end
R0 = jsondecode(fileread(fullfile(refDir, ['TB06_' caseName '_init.json'])));
cs = struct('vbat', R0.vbat, 'P0', R0.P0, 'P1', R0.P1, 't_step', R0.t_step, 't_end', R0.t_end, ...
    'stageA_modules', [1 0 0 0], 'stageC_enable', 1);
cs.dt = 5e-9;                        % 통합 모델 적분 간격(= 게이트 격자). 정상상태 리플은 정보로만 기록(TB04B)
if isfield(ov, 'dt'), cs.dt = ov.dt; end
P = prism_hub_params(cs);

TB = struct();
TB.name  = 'TB06_Integrated_Drive';
TB.case  = caseName;
TB.dt    = P.sim.dt;
TB.Np    = P.sim.Np;
TB.vbat  = R0.vbat;
TB.t_eval = 1e-3;                    % 판정 시작 시각(초기 정착 구간 제외)

% ---- Stage A: 모듈 1(위상 1·2), 영교차 추종 -----------------------------------------------------
TB.A       = P.A;
TB.A.Goff  = 1e-8;  TB.A.Rd = P.A.Rds;  TB.A.Goffd = 1e-8;
TB.A.vC0   = TB.vbat/2;
TB.A.CA    = P.A.Cout;               % V_A 노드 출력 커패시터 400 µF
TB.A.RA    = P.A.Rout_est;           % 1모듈 등가 출력저항 추정(초기 V_A 계산용)
t_on  = 0.5/P.A.fr0 - P.A.td;        % 공칭 도통시간(검증 모델 E1과 같은 정의)
TB.gateA_zcp_prm = [TB.dt, round(P.A.td/TB.dt), round(0.80*t_on/TB.dt), round(1.12*t_on/TB.dt), ...
                    round(20e-9/TB.dt), 0.5];          % [dt n_dead n_min n_max n_det(검출 지연 20 ns) i_thr 0.5 A]
TB.gateA_en  = [1 1 0 0 0 0 0 0];
Thalf = round(0.5/P.A.fr0/TB.dt);                     % 공칭 반주기(간격 수)
TB.gateA_off = [0 round(Thalf/2) 0 0 0 0 0 0];       % 위상 2는 반주기/2(= T/4) 늦게 시작(인터리빙)

% ---- 경로와 Stage B ---------------------------------------------------------------------------
TB.Rpath = P.B.Rpath;                % 배선 3 mΩ(Stage A 출력저항은 회로에서 생긴다)
TB.Lpath = P.B.Lpath;
TB.Cb    = P.B.Cb;
TB.B = P.B;
TB.B.Goff   = 1e-8;  TB.B.Rd = P.B.Ron;  TB.B.Goffd = 1e-8;
TB.B.Coss_dp = 335e-12;              % DAB 1차 소자 C_o(tr)(TB04B, 650 V GaN)
TB.B.Coss_ds = 1371e-12;             % DAB 2차 소자 C_oss(tr)(TB04B, 150 V GaN)
TB.B.Coss_d  = TB.B.Coss_dp;

x0 = R0.x0;
TB.ip0 = x0(1); TB.vs0 = x0(2); TB.vb0 = x0(3); TB.ih0 = x0(4); TB.vl0 = x0(5);
TB.vA0 = TB.vbat/2 - TB.A.RA*TB.ip0;
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

% ---- Stage C -------------------------------------------------------------------------------------
TB.C = P.C;
TB.C.Goff = 1e-8;  TB.C.Rd = P.C.Ron;  TB.C.Goffd = 1e-8;
TB.C.Vf_rect = 1e-3;  TB.C.Ron_rect = 1e-4;          % 동기정류 근사(TB05와 같음)
TB.Po_C  = 3000;                     % 48 V 출력 정격
TB.RL_C  = 48^2/TB.Po_C;             % 48 V 저항부하
TB.vo0   = 47.68;                    % 출력 초기전압(TB05 3 kW, 5 ns 정상값 47.683 V)
TB.Pc_in = 2994;                     % Stage C 입력전력 추정(TB05 3 kW, 5 ns: 2994 W, 수치 감쇠 등가 손실 포함)
TB.gateC_prm = [TB.dt 1/P.C.fs P.C.td 1];
TB.vo_TB05 = 47.683;                 % TB05 3 kW 정상 출력, 같은 적분 간격(5 ns 47.683 V, 2.5 ns 47.833 V) — 일관성 비교 기준
if abs(TB.dt - 2.5e-9) < 1e-12, TB.vo_TB05 = 47.833; end

% ---- 버스 부하 ------------------------------------------------------------------------------------
TB.P0tot = R0.P0;  TB.P1tot = R0.P1;
TB.P0 = R0.P0 - TB.Pc_in;            % 정전력 부하 = 총부하 − Stage C 입력 추정
TB.P1 = R0.P1 - TB.Pc_in;
TB.t_step = R0.t_step;  TB.t_end = R0.t_end;
TB.vmin = P.load.vmin;

TB.guard_t    = 1.5*TB.dt;           % 시작 표본 보호(lib/sl_startup_guard.m)
TB.meas0      = [TB.ip0 TB.vs0 TB.vb0 TB.ih0 TB.vl0];
TB.loss_meas0 = [TB.vl0 il0 0 TB.vb0];

assignin('base', 'P', P);
assignin('base', 'TB', TB);
