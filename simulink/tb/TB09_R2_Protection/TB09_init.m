%TB09_INIT  TB09(R2 창 조정 모듈의 보호 상태기계, R2-W460) 초기화: 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   TB08의 R2-W460 회로에 E17의 보호 기능을 더한다.
%     - 측정 기반 상태기계(ctrl/prism_r2_supervisor.m): 켬·끔, DAB 고장(링크전압 창), H-브리지 개방(게이트 구동기 고장 신호),
%       하드웨어 비교기 차단 래치(ctrl/prism_r2_gate_b.m)
%     - H-브리지 강등: 다이오드 클램프 유지(DAB 보조 루프가 링크전압으로 버스를 V_W에) → 400 V 부하 분리 → 링크 붕괴 → 소프트 바이패스
%     - 링크 제동 저항 3 Ω(gBrk), 바이패스 소프트 투입 가변 저항(10 Ω → 3.3 mΩ, 경로전류 조절), 버스 RC 감쇠기(1.6 mF·48.6 mΩ, R2 기본형)
%     - (2차) 링크 붕괴 정체 감지, 경로전류 조절 소프트 투입(상태기계 파라미터 51–56)
%     - Stage B 소자의 역방향 도통 전압 V_D 2 V(꺼진 GaN, H-브리지 다이오드 정류의 근거. TB08은 이상 클램프 1 mV)
%   사례: 기본 작업공간 변수 TB09_case(없으면 'A_1008V_hbopen_25kW'). 기준값은 ref/TB09_<사례>_init.json(검증 코드 E17)
%   선택: 기본 작업공간 변수 TB09_opts(구조체) — dt

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');

if evalin('base', 'exist(''TB09_case'', ''var'')')
    caseName = evalin('base', 'TB09_case');
else
    caseName = 'A_1008V_hbopen_25kW';
end
ov = struct();
if evalin('base', 'exist(''TB09_opts'', ''var'')'), ov = evalin('base', 'TB09_opts'); end
R0 = jsondecode(fileread(fullfile(refDir, ['TB09_' caseName '_init.json'])));
cs = struct('vbat', R0.vbat, 'P0', R0.P0, 'P1', R0.P0, 't_step', 1e30, 't_end', R0.t_end);
cs.dt = 2.5e-9;                      % TB08과 같은 판정 격자
if isfield(ov, 'dt'), cs.dt = ov.dt; end
P = prism_hub_params(cs);

TB = struct();
TB.name  = 'TB09_R2_Protection';
TB.case  = caseName;
TB.event = R0.event;
TB.dt    = P.sim.dt;
TB.Np    = P.sim.Np;
TB.vbat  = R0.vbat;
TB.VA    = R0.vbat/2;                % Stage A 등가: 이상 V_bat/2 + 13.2 mΩ + 1.5 µH(TB04·TB08과 같음)
TB.Rpath = 0.0132;
TB.Lpath = 1.5e-6;
TB.Cb    = 400e-6;
TB.VW    = R0.VW;
TB.upper = R0.upper;
TB.Prated = R0.dab_rated_W;

% ---- Stage B 부품: TB08과 같고, 소자 역방향 도통만 꺼진 GaN 값으로 ------------------------------------------
TB.B = P.B;
TB.B.n      = R0.turns;              % 4.6:1
TB.B.Ldab   = R0.Ldab;               % 14.68 µH
TB.B.Goff   = 1e-8;
TB.B.Vf     = R0.Vd;                 % 2.0 V: 꺼진 GaN의 역방향 도통(수십 A). H-브리지가 꺼지면 다이오드 정류기가 된다
TB.B.Rd     = 1e-4;
TB.B.Goffd  = 1e-8;
TB.B.Coss_dp = 335e-12;              % DAB 1차 소자 C_o(tr)(TB04B·TB08과 같음)
TB.B.Coss_ds = 1371e-12;             % DAB 2차 소자 C_oss(tr)
TB.B.Coss_d = TB.B.Coss_dp;
TB.Rbyp_cell = R0.R_bypass/2;        % 바이패스 셀 = EPC2305 2병렬, 역직렬 셀 2개 = 3.3 mΩ
TB.Vf_byp  = 1.4;                    % 바이패스 셀 역방향 도통(EPC2305 V_SD)
TB.Rd_byp  = TB.Rbyp_cell;
TB.R_open  = 1e6;                    % 소프트 투입 가변 저항: 열림
TB.Rbrk    = R0.Rbrk;                % 링크 제동 저항 3 Ω
TB.Rdmp    = R0.Rdmp;                % 버스 RC 감쇠기 48.6 mΩ
TB.Cdmp    = R0.Cdmp;                % 1.6 mF
TB.Pc      = R0.Pc;                  % 400 V 부하 분리 뒤 남는 부하(조정형 Stage C 몫)

% ---- 초기조건 ---------------------------------------------------------------------------------------
x0 = R0.x0;
TB.ip0 = x0(1); TB.vs0 = x0(2); TB.vb0 = x0(3); TB.ih0 = x0(4); TB.vl0 = x0(5);
TB.vcd0 = R0.vcd0;
TB.st0  = R0.st0;
TB.byp0 = double(R0.st0 ~= 3);       % 바이패스로 시작(켬 사례)이면 주 스위치 켬
m0 = R0.u0(1); il0 = R0.u0(2);
TB.P0 = R0.P0; TB.P1 = R0.P0; TB.t_step = 1e30; TB.t_end = R0.t_end;
TB.vmin = P.load.vmin;

% ---- 제어기(TB08과 같음) + 상태기계 + 보호 ------------------------------------------------------------------
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
TB.sup_prm   = R0.sup_prm(:)';                       % 상태기계 파라미터 56개(E17과 같은 값)
TB.prot_prm  = [TB.dt R0.prot_prm(:)'];             % [dt T_HW I_HW VL_HW VS_HW 상한 고장종류 고장시각 T_GDF]

TB.guard_t    = 1.5*TB.dt;
TB.meas0      = [TB.ip0 TB.vs0 TB.vb0 TB.ih0 TB.vl0];
TB.loss_meas0 = [TB.vl0 il0 0 TB.vb0];

assignin('base', 'P', P);
assignin('base', 'TB', TB);
