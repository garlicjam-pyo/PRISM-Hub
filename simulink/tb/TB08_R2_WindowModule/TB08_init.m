%TB08_INIT  TB08(R2 창 조정 Stage B 모듈, 1000 V급 240s 팩·B_470 부품) 초기화: 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   개선 구조 R2에서 Stage B는 V_A가 400 V급 부품 상한을 넘을 때만 버스를 창 기준 V_W로 깎는 선택 모듈이다(docs/23).
%   이 테스트벤치는 1000 V급 팩(배터리 720–1008 V, V_A 최대 504 V)과 B_470 부품의 설계 R2-W460을 회로로 확인한다.
%     창 기준 V_W 460 V, DAB 권선비 4.6:1(= V_W/100), 누설 인덕턴스 11.1 µH·(460/400)² = 14.68 µH,
%     DAB 정격 4.0 kW(정적 최대 링크전력 2.16 kW × 1.8, E19), 바이패스 스위치 3.3 mΩ(150 V GaN 역직렬 2개)
%   채택 제어기의 이득·예측 구조와 Stage B의 나머지 부품값은 TB04B와 같다(DAB 소자 출력용량도 후보 소자 값).
%
%   사례: 기본 작업공간 변수 TB08_case(없으면 'A_1008V_1to25kW'). 기준값은 ref/TB08_<사례>_init.json
%   선택: 기본 작업공간 변수 TB08_opts(구조체) — dt(적분 간격 = 게이트 시간 분해능)

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');

if evalin('base', 'exist(''TB08_case'', ''var'')')
    caseName = evalin('base', 'TB08_case');
else
    caseName = 'A_1008V_1to25kW';
end
ov = struct();
if evalin('base', 'exist(''TB08_opts'', ''var'')'), ov = evalin('base', 'TB08_opts'); end
R0 = jsondecode(fileread(fullfile(refDir, ['TB08_' caseName '_init.json'])));
cs = struct('vbat', R0.vbat, 'P0', R0.P0, 'P1', R0.P1, 't_step', R0.t_step, 't_end', R0.t_end);
cs.dt = 2.5e-9;                      % TB04B와 같은 판정 격자(과도 일치). 정상상태 리플은 정보(요구 격자 0.625 ns, TB04B)
if isfield(ov, 'dt'), cs.dt = ov.dt; end
P = prism_hub_params(cs);

TB = struct();
TB.name  = 'TB08_R2_WindowModule';
TB.case  = caseName;
TB.kind  = R0.kind;                  % 'switching'(창 조정 Tier 사례) 또는 'averaged'(모드 전환·고장 강등)
TB.dt    = P.sim.dt;
TB.Np    = P.sim.Np;
TB.vbat  = R0.vbat;
TB.VA    = R0.vbat/2;                % Stage A 등가: 이상 V_bat/2 + 13.2 mΩ + 1.5 µH(TB04와 같음)
TB.Rpath = 0.0132;
TB.Lpath = 1.5e-6;
TB.Cb    = 400e-6;
TB.VW    = R0.VW;                    % 창 기준전압 460 V
TB.upper = 470;                      % 부품 등급 상한(ISO 21498-1 B_470)
TB.Prated = R0.dab_rated_W;          % DAB 정격 4.0 kW

% ---- Stage B 부품: TB04B와 같고 DAB 권선비·누설 인덕턴스만 창 기준에 맞춘다 --------------------------------
TB.B = P.B;
TB.B.n      = R0.turns;              % 4.6:1
TB.B.Ldab   = R0.Ldab;               % 14.68 µH
TB.B.Goff   = 1e-8;
TB.B.Rd     = P.B.Ron;
TB.B.Goffd  = 1e-8;
TB.B.Coss_dp = 335e-12;              % DAB 1차 소자 C_o(tr), GS66516T(650 V GaN, 버스 460–504 V에서 사용률 ≤ 78 %)
TB.B.Coss_ds = 1371e-12;             % DAB 2차 소자 C_oss(tr), EPC2305
TB.B.Coss_d = TB.B.Coss_dp;
TB.Rbyp_cell = 3.3e-3/2;             % 바이패스 스위치 셀 1개(역직렬 2개 = 3.3 mΩ, E15 R_BYP와 같음)

% ---- 초기조건(검증 모델 평형점 또는 바이패스·영벡터 분담 상태) ------------------------------------------------
x0 = R0.x0;
TB.ip0 = x0(1); TB.vs0 = x0(2); TB.vb0 = x0(3); TB.ih0 = x0(4); TB.vl0 = x0(5);
m0 = R0.u0(1); il0 = R0.u0(2);
TB.P0 = R0.P0; TB.P1 = R0.P1; TB.t_step = R0.t_step; TB.t_end = R0.t_end;
TB.vmin = P.load.vmin;

% ---- 제어기: 기준전압·DAB 정격·누설 인덕턴스·권선비만 창 조정 설계값으로 ---------------------------------------
prm = P.ctrl_prm;
prm(9)  = TB.VW;                     % vref(모드 시퀀서가 y(10)으로 다시 준다)
prm(14) = TB.Prated;                 % power_max: DAB 링크전류 지령 한계 min(80 A, P_rated/v_link, SPS)
prm(17) = R0.Ldab;                   % Ldab(공칭)
prm(19) = R0.turns;                  % turns
TB.ctrl_prm  = prm;
TB.ctrl_tab  = P.ctrl_tab;
TB.ctrl_init = [R0.q0 0 m0 il0];
TB.smp       = [TB.dt TB.Np];
TB.delay_steps = P.delay_steps;
TB.uc0       = [m0; R0.ph0];
TB.gate_prm  = P.gateB_prm;
TB.gate_init = [m0 R0.ph0 il0];
TB.loss_prm  = [TB.dt TB.Np R0.eta TB.B.Rdab];
TB.ploss0    = R0.ploss0;
TB.seq_prm   = R0.seq(:)';           % [t_ramp0 t_ramp1 v_from v_to t_nodab t_zero t_byp t_open t_ctrl mode_init]

TB.guard_t    = 1.5*TB.dt;           % 시작 표본 보호(lib/sl_startup_guard.m)
TB.meas0      = [TB.ip0 TB.vs0 TB.vb0 TB.ih0 TB.vl0];
TB.loss_meas0 = [TB.vl0 il0 0 TB.vb0];

assignin('base', 'P', P);
assignin('base', 'TB', TB);
