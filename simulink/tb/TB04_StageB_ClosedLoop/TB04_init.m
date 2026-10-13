%TB04_INIT  TB04(Stage B 폐루프) 초기화: 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   사례는 기본 작업공간 변수 TB04_case로 고른다(없으면 'A_640V_15to25kW').
%     A_640V_15to25kW : 배터리 640 V, 버스 부하 15 → 25 kW(Tier-1 대표, 경로·필터 전류가 가장 큰 쪽)
%     B_788V_0to10kW  : 배터리 788 V, 0 → 10 kW(경부하, 직렬전압 약 6 V → DAB 링크전류 수 A의 저전류 구간)
%   초기조건과 제어기 초기상태는 검증 모델과 똑같이 시작하도록 ref/TB04_<사례>_init.json(검증 모델의 평형점)에서 읽는다.
%   회로: Stage A는 이상 전압원 V_bat/2와 경로 R = 13.2 mΩ(Stage A 출력저항 포함), L = 1.5 µH로 둔다(검증 모델과 같음).

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));

if evalin('base', 'exist(''TB04_case'', ''var'')')
    caseName = evalin('base', 'TB04_case');
else
    caseName = 'A_640V_15to25kW';
end
R0 = jsondecode(fileread(fullfile(tbDir, 'ref', ['TB04_' caseName '_init.json'])));
P = prism_hub_params(struct('vbat', R0.vbat, 'P0', R0.P0, 'P1', R0.P1, 't_step', R0.t_step, 't_end', R0.t_end));

TB = struct();
TB.name  = 'TB04_StageB_ClosedLoop';
TB.case  = caseName;
TB.dt    = P.sim.dt;                 % 5 ns
TB.Np    = P.sim.Np;                 % 제어주기당 간격 수(1000)
TB.vbat  = R0.vbat;
TB.VA    = R0.vbat/2;                % 이상 Stage A 출력(무부하)
TB.Rpath = 0.0132;                   % 경로 저항(Stage A 출력저항 10.2 mΩ + 배선 3 mΩ)
TB.Lpath = 1.5e-6;
TB.Cb    = 400e-6;

TB.B = P.B;                          % Cs Lh Rh Clink Ldab Rdab n fs td_h td_d Coss_h Ron Vf
TB.B.Goff   = 1e-8;
TB.B.Rd     = P.B.Ron;               % 바디 다이오드 도통 저항
TB.B.Goffd  = 1e-8;
TB.B.Coss_d = 100e-12;               % DAB 소자 출력용량(TB03과 같은 값)

x0 = R0.x0;                          % [i_p v_s v_bus i_h v_link i_L(평균모델)]
TB.ip0 = x0(1); TB.vs0 = x0(2); TB.vb0 = x0(3); TB.ih0 = x0(4); TB.vl0 = x0(5);
m0 = R0.u0(1); il0 = R0.u0(2);

TB.P0 = R0.P0; TB.P1 = R0.P1; TB.t_step = R0.t_step; TB.t_end = R0.t_end;
TB.vmin = P.load.vmin;

% 제어기·게이트·손실 모델 상수
TB.ctrl_prm  = P.ctrl_prm;
TB.ctrl_tab  = P.ctrl_tab;
TB.ctrl_init = [R0.q0 0 m0 il0];     % [버스전압 적분 q, 링크 PI 적분, 직전 변조율, 직전 링크전류 지령]
TB.smp       = [TB.dt TB.Np];
TB.delay_steps = P.delay_steps;      % 5 µs
TB.uc0       = [m0; R0.ph0];         % 첫 지령이 도착하기 전 PWM 비교값·DAB 위상
TB.gate_prm  = P.gateB_prm;
TB.gate_init = [m0 R0.ph0 il0];
TB.loss_prm  = [TB.dt TB.Np R0.eta TB.B.Rdab];
TB.ploss0    = R0.ploss0;

assignin('base', 'P', P);
assignin('base', 'TB', TB);
