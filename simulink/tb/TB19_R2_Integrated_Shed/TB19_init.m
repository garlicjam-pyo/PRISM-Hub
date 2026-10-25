%TB19_INIT  TB19(R2-W460 통합 강등 + Stage A 경부하 위상 셰딩) 초기화: 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   TB17_init.m과 같다(Stage A 모듈 1 + 창 조정 Stage B(H-브리지 개방 강등, TB13) + 조정형 Stage C, 고장 1.5 ms).
%   다른 것: Stage A 게이트가 경부하 위상 셰딩 게이트(ctrl/prism_gate_stageA_zcps.m, 검증 코드 E24·TB18과 같은 문턱)다.
%     TB.gateA_zcps_prm = [영교차 추종 6개, I_off 15 A, I_on 22 A, I_pk,on 36 A, dt/τ(τ 2 µs), 지속 100 µs, 남는 위상 1, 멈추는 위상 2]
%   사례: 기본 작업공간 변수 TB19_case(없으면 'A_1008V_hbopen'). 기준값은 ref/TB19_<사례>_*.json(TB17과 같음 + Stage A 셰딩 기준)

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');

if evalin('base', 'exist(''TB19_case'', ''var'')')
    caseName = evalin('base', 'TB19_case');
else
    caseName = 'A_1008V_hbopen';
end
R0 = jsondecode(fileread(fullfile(refDir, ['TB19_' caseName '_init.json'])));
cs = struct('vbat', R0.vbat, 'P0', R0.P0, 'P1', R0.P0, 't_step', 1e30, 't_end', R0.t_end);
cs.dt = 2.5e-9;                      % TB08–TB16과 같은 판정 격자
P = prism_hub_params(cs);            % Stage A(P.A)·Stage B(P.B) 설계값, 제어 파라미터(버스 전체 부하 25 kW 기준, TB13과 같음)

TB = struct();
TB.name  = 'TB19_R2_Integrated';
TB.case  = caseName;
TB.event = R0.event;
TB.dt    = P.sim.dt;
TB.Np    = P.sim.Np;
TB.vbat  = R0.vbat;
TB.t_end = R0.t_end;
TB.t_event = R0.t_event;
TB.VW    = R0.VW;
TB.upper = R0.upper;
TB.Prated = R0.dab_rated_W;
TB.VA    = R0.vbat/2;                % 판정·그림의 기준선(이상 V_A)

% ---- Stage A(모듈 1, 위상 1·2, TB16과 같음) ---------------------------------------------------------------
TB.A       = P.A;
TB.A.Goff  = 1e-8;  TB.A.Rd = P.A.Rds;  TB.A.Goffd = 1e-8;
TB.A.vC0   = TB.vbat/2;                           % 플라잉 커패시터 초기 = V_bat/2
TB.A.CA    = R0.CA;                               % V_A 노드 출력 커패시터 400 µF
t_on  = 0.5/P.A.fr0 - P.A.td;
TB.gateA_zcp_prm = [TB.dt, round(P.A.td/TB.dt), round(0.80*t_on/TB.dt), round(1.12*t_on/TB.dt), ...
                    round(20e-9/TB.dt), 0.5];     % [dt n_dead n_min n_max n_det(20 ns) i_thr 0.5 A](TB06·TB16과 같음)
SH = jsondecode(fileread(fullfile(refDir, 'TB19_shed.json')));   % E24 셰딩 파라미터(keep·sh는 0부터)
TB.gateA_zcps_prm = [TB.gateA_zcp_prm, SH.I_off, SH.I_on, SH.Ipk_on, TB.dt/SH.tau, round(SH.t_dwell/TB.dt), SH.keep + 1, SH.sh + 1];
TB.rated_pk_A = SH.rated_pk; TB.i_abs = SH.i_abs;   % Stage A 위상 정격 첨두(76.4 A). TB.rated_pk는 DAB 정격점 첨두(아래)
TB.gateA_en  = [1 1 0 0 0 0 0 0];
Thalf = round(0.5/P.A.fr0/TB.dt);
TB.gateA_off = [0 round(Thalf/2) 0 0 0 0 0 0];   % 위상 2는 T/4 늦게(인터리빙)

% ---- 경로·버스 ---------------------------------------------------------------------------------------------
TB.Rpath = R0.RW;                    % 배선 3 mΩ(Stage A 출력저항은 회로에서)
TB.Lpath = R0.LW;                    % 1.5 µH
TB.Cb    = 400e-6;

% ---- Stage B 부품(TB13과 같음) ------------------------------------------------------------------------------
TB.B = P.B;
TB.B.n      = R0.turns;              % 4.6:1
TB.B.Ldab   = R0.Ldab;               % 14.68 µH
TB.B.Goff   = 1e-8;
TB.B.Vf     = R0.Vd;                 % 2.0 V: 꺼진 GaN의 역방향 도통
TB.B.Rd     = 1e-4;
TB.B.Goffd  = 1e-8;
TB.B.Coss_dp = 335e-12;
TB.B.Coss_ds = 1371e-12;
TB.B.Coss_d = TB.B.Coss_dp;
TB.Rbyp_cell = R0.R_bypass/2;
TB.Vf_byp  = 1.4;
TB.Rd_byp  = TB.Rbyp_cell;
TB.R_open  = 1e6;
TB.Rbrk    = R0.Rbrk;                % 링크 제동 저항 3 Ω
TB.Rdmp    = R0.Rdmp;                % 버스 RC 감쇠기 48.6 mΩ
TB.Cdmp    = R0.Cdmp;                % 1.6 mF

% ---- 초기조건(E17 평형점, TB13과 같음) + V_A 노드 ---------------------------------------------------------------
x0 = R0.x0;
TB.ip0 = x0(1); TB.vs0 = x0(2); TB.vb0 = x0(3); TB.ih0 = x0(4); TB.vl0 = x0(5);
TB.vcd0 = R0.vcd0;
TB.vA0  = TB.vbat/2 - R0.RA*TB.ip0;  % Stage A 정적 등가(E23): V_A = V_bat/2 − R_A·i_p
TB.st0  = R0.st0;
TB.byp0 = double(R0.st0 ~= 3);
m0 = R0.u0(1); il0 = R0.u0(2);
TB.P0 = R0.P400;                     % 400 V 정전력 부하(Load_CPL): 20 kW
TB.Pc = R0.Pc;                       % 분리 뒤 400 V 부하 0 W(남는 부하는 Stage C 회로)
TB.P1 = TB.P0; TB.t_step = 1e30;
TB.vmin = P.load.vmin;

% ---- Stage B 제어기 + 상태기계 + 보호(TB13과 같음, 고장 시각만 1.5 ms) -----------------------------------------------
prm = P.ctrl_prm;
prm(9)  = TB.VW;
prm(14) = TB.Prated;
prm(17) = R0.Ldab;
prm(19) = R0.turns;
TB.ctrl_prm  = prm;
TB.ctrl_tab  = P.ctrl_tab;
TB.ctrl_init = [R0.q0 0 m0 il0];
TB.smp       = [TB.dt TB.Np];
TB.delay_steps = P.delay_steps;
TB.uc0       = [m0; 0];
TB.gate_prm  = P.gateB_prm;
TB.gate_init = [m0 0 il0];
TB.loss_prm  = [TB.dt TB.Np R0.eta TB.B.Rdab];
TB.ploss0    = 0;
TB.sup_prm   = R0.sup_prm(:)';
ET = jsondecode(fileread(fullfile(refDir, 'TB19_eps_table.json')));
TB.eps_prm   = R0.eps_prm(:)';
TB.eps_d     = ET.d;
TB.eps_phi   = ET.phi;
TB.eps_pk    = ET.pk;
TB.pk_max    = R0.pk_max;
TB.rated_pk  = R0.rated_pk;
TB.prot_prm  = [TB.dt R0.prot_prm(:)'];

% ---- Stage C(TB15·TB16과 같음) ---------------------------------------------------------------------------------
TB.SB = struct('Ron', R0.Ron_b, 'Goff', 1e-8, 'Vf', 2.5, 'Rd', R0.Ron_b, 'Goffd', 1e-8, 'Coss', R0.Coss_b);
TB.CP = struct('Ron', R0.Ron_p, 'Goff', 1e-8, 'Vf', 0.05, 'Rd', R0.Ron_p, 'Goffd', 1e-8, 'Coss', R0.Coss_p);
TB.CS = struct('Ron', R0.Ron_s, 'Goff', 1e-8, 'Vf', 0.05, 'Rd', R0.Ron_s, 'Goffd', 1e-8, 'Coss', R0.Coss_s);
n = R0.n;
TB.C = struct('n', n, 'Lr1', R0.Lr, 'Cr1', R0.Cr, 'Lm', R0.Lm, 'Lr2', R0.Lr/n^2, 'Cr2', R0.Cr*n^2, ...
              'Rw1', R0.Rw/2, 'Rw2', R0.Rw/2/n^2, 'Co', R0.CO, 'CI', R0.CI, 'L', R0.L, 'RL', R0.RL);
TB.x0 = R0.xC0(:)';                  % Stage C [i_L v_I v_o i_x](버스 460 V, 48 V 부하 P48의 평형)
TB.bat_on = 0; TB.OCV = R0.OCV; TB.Rbat = 1e6;    % 48 V 배터리 없음(가지를 1 MΩ으로 끊음)
TB.vmin_cpl = 10;
TB.P48 = R0.P48;                     % 48 V 정전력 부하(Stage C 입력 5 kW = E17 P_C)
TB.band = R0.band(:)';               % 48 V ±2 %(강등 내내)
ctl = R0.ctl(:)';
iL0 = TB.x0(1);
TB.ctl_prm_C = [ctl R0.Vref TB.dt TB.bat_on 0 R0.d0 1 iL0 n R0.P_in R0.P_out R0.Ii0];   % 27개(모드 1: 1차가 보냄,
                                     % 27번 = 전류 PI 적분 시작값(평형): 4.9 kW에서 시작하므로 시작 과도를 없앤다)
TB.gate_prm_C = [TB.dt 1/R0.fb R0.td_b 1/R0.fr R0.td_p R0.td_s R0.td_sb];
TB.P_in = R0.P_in; TB.P_out = R0.P_out;
TB.measC0 = [TB.vb0 iL0 TB.x0(2) TB.x0(3) TB.P48/TB.x0(3) 0];
TB.pulse_rating_secondary = R0.pulse_rating_secondary;

TB.guard_t    = 1.5*TB.dt;
TB.meas0      = [TB.ip0 TB.vs0 TB.vb0 TB.ih0 TB.vl0];
TB.loss_meas0 = [TB.vl0 il0 0 TB.vb0];

assignin('base', 'P', P);
assignin('base', 'TB', TB);
