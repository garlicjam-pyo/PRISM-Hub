%TB04B_INIT  TB04B(Stage B 폐루프, DAB 소자 출력용량을 후보 소자 값으로) 초기화: 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   TB04와 같은 회로·제어기·사례에서 DAB 1차(400 V 버스 측)와 2차(100 V 링크 측) 소자 출력용량만 따로 준다.
%   TB04는 두 브리지 모두 100 pF(수치 안정용 소값)였고, 25 kW 정상상태 리플이 이 값에 따라 달라졌다(열린 쟁점).
%
%   기본값: 대표 후보 소자의 시간 등가 출력용량 C_o(tr)(데드타임 전이 시간을 같게 주는 선형 용량)
%     1차  650 V GaN  GS66516T(25 mΩ, 60 A)  C_o(tr) = 335 pF (V_DS 0–400 V), C_o(er) = 207 pF
%     2차  150 V GaN  EPC2305 (2.2 mΩ, 133 A) C_oss(tr) = 1371 pF (V_DS 0–75 V), C_oss(er) = 1053 pF
%   (제조사 데이터시트 값. 링크 100 V에서의 C_oss(tr)는 0–75 V 값보다 조금 작다 → 보수적 쪽)
%
%   사례: 기본 작업공간 변수 TB04_case(없으면 'A_640V_15to25kW'). 기준값은 TB04와 같은 검증 모델 결과(../TB04_StageB_ClosedLoop/ref)
%   선택: 기본 작업공간 변수 TB04B_opts(구조체) — dt(적분 간격 = 게이트 시간 분해능), Coss_dp, Coss_ds

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(pkgRoot, 'tb', 'TB04_StageB_ClosedLoop', 'ref');

if evalin('base', 'exist(''TB04_case'', ''var'')')
    caseName = evalin('base', 'TB04_case');
else
    caseName = 'A_640V_15to25kW';
end
ov = struct();
if evalin('base', 'exist(''TB04B_opts'', ''var'')'), ov = evalin('base', 'TB04B_opts'); end
R0 = jsondecode(fileread(fullfile(refDir, ['TB04_' caseName '_init.json'])));
cs = struct('vbat', R0.vbat, 'P0', R0.P0, 'P1', R0.P1, 't_step', R0.t_step, 't_end', R0.t_end);
cs.dt = 2.5e-9;                      % 게이트 시간 분해능 요구(TB04): 판정 기본 2.5 ns
if isfield(ov, 'dt'), cs.dt = ov.dt; end
P = prism_hub_params(cs);

TB = struct();
TB.name  = 'TB04B_StageB_DAB_Coss';
TB.case  = caseName;
TB.dt    = P.sim.dt;                 % 기본 2.5 ns(TB04에서 정한 게이트 시간 분해능 요구)
TB.Np    = P.sim.Np;
TB.vbat  = R0.vbat;
TB.VA    = R0.vbat/2;
TB.Rpath = 0.0132;
TB.Lpath = 1.5e-6;
TB.Cb    = 400e-6;

TB.B = P.B;
TB.B.Goff   = 1e-8;
TB.B.Rd     = P.B.Ron;
TB.B.Goffd  = 1e-8;
TB.B.Coss_dp = 335e-12;              % DAB 1차 소자 C_o(tr), GS66516T
TB.B.Coss_ds = 1371e-12;             % DAB 2차 소자 C_oss(tr), EPC2305
if isfield(ov, 'Coss_dp'), TB.B.Coss_dp = ov.Coss_dp; end
if isfield(ov, 'Coss_ds'), TB.B.Coss_ds = ov.Coss_ds; end
TB.B.Coss_d = TB.B.Coss_dp;          % (공용 빌더의 기본 이름. 이 모델에서는 쓰지 않는다)

x0 = R0.x0;
TB.ip0 = x0(1); TB.vs0 = x0(2); TB.vb0 = x0(3); TB.ih0 = x0(4); TB.vl0 = x0(5);
m0 = R0.u0(1); il0 = R0.u0(2);
TB.P0 = R0.P0; TB.P1 = R0.P1; TB.t_step = R0.t_step; TB.t_end = R0.t_end;
TB.vmin = P.load.vmin;

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

TB.guard_t    = 1.5*TB.dt;           % 시작 표본 보호(lib/sl_startup_guard.m)
TB.meas0      = [TB.ip0 TB.vs0 TB.vb0 TB.ih0 TB.vl0];
TB.loss_meas0 = [TB.vl0 il0 0 TB.vb0];

assignin('base', 'P', P);
assignin('base', 'TB', TB);
