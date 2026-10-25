%TB18_INIT  TB18(Stage A 경부하 위상 셰딩: 모듈 1 + 셰딩 게이트 + R2 버스 + V_A 노드 충전기 전류) 초기화: 경로, 시험 조건 TB.
%
%   사례: 기본 작업공간 변수 TB18_case(없으면 'F_1008V_bus_25_5_25kW'). 기준값은 ref/TB18_<사례>_init.json(검증 코드 E24).
%   선택: 기본 작업공간 변수 TB18_shed(0이면 셰딩 없음: I_off = −1로 두어 멈추지 않는다. 같은 회로·게이트로 비교 실행)
%   Stage A: prism_hub_params(E1과 같은 설계값) 모듈 1(2위상), C_fly = V_bat/2·공진전류 0에서 시작(TB16과 같음).
%   버스(E23·TB16과 같음): V_A 노드 C_A 400 µF → 배선 3 mΩ·1.5 µH → C_b 400 µF ∥ RC 감쇠기 48.6 mΩ + 1.6 mF ∥ 정전력 부하.
%   V_A 노드에는 충전기 등 직접 전류원(I_VA > 0이면 빼고, < 0이면 주입)을 둔다.
%   해석기: Simscape 지역 해석기 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회).

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');
caseName = 'F_1008V_bus_25_5_25kW';
if evalin('base', 'exist(''TB18_case'', ''var'')'), caseName = evalin('base', 'TB18_case'); end
shedOn = 1;
if evalin('base', 'exist(''TB18_shed'', ''var'')'), shedOn = evalin('base', 'TB18_shed'); end
R0 = jsondecode(fileread(fullfile(refDir, ['TB18_' caseName '_init.json'])));

TB = struct();
TB.name = 'TB18_StageA_Shedding';
TB.case = caseName;
TB.shed_on = shedOn;
TB.dt = 2.5e-9;
TB.t_end = R0.t_end;
TB.t0 = R0.t0;                                    % 판정 시작(Stage A 시작 과도 뒤)
TB.vbat = R0.vbat;

% ---- Stage A(모듈 1, 위상 1·2, TB16과 같음) ---------------------------------------------------------------
P = prism_hub_params(struct('dt', TB.dt));
TB.A       = P.A;
TB.A.Goff  = 1e-8;  TB.A.Rd = P.A.Rds;  TB.A.Goffd = 1e-8;
TB.A.vC0   = TB.vbat/2;
TB.A.CA    = R0.CA;
t_on  = 0.5/P.A.fr0 - P.A.td;
zcp = [TB.dt, round(P.A.td/TB.dt), round(0.80*t_on/TB.dt), round(1.12*t_on/TB.dt), round(20e-9/TB.dt), 0.5];
TB.gateA_zcp_prm = zcp;
sh = R0.shed;
Ioff = sh.I_off; if ~shedOn, Ioff = -1; end       % 셰딩 없음: |If| < −1은 없으므로 멈추지 않는다
TB.gateA_zcps_prm = [zcp, Ioff, sh.I_on, sh.Ipk_on, TB.dt/sh.tau, round(sh.t_dwell/TB.dt), sh.keep + 1, sh.sh + 1];
TB.gateA_en  = [1 1 0 0 0 0 0 0];
Thalf = round(0.5/P.A.fr0/TB.dt);
TB.gateA_off = [0 round(Thalf/2) 0 0 0 0 0 0];   % 위상 2는 T/4 늦게(인터리빙)

% ---- 버스(E23·TB16과 같음) -----------------------------------------------------------------------------
TB.Rpath = R0.bus.Rw;  TB.Lpath = R0.bus.Lw;  TB.Cb = R0.bus.Cb;
TB.Rdmp = R0.bus.Rd;   TB.Cdmp = R0.bus.Cd;   TB.vmin_q = R0.bus.vmin;
TB.vA0 = R0.vA0;  TB.vb0 = R0.vb0;  TB.iw0 = R0.iw0;

% ---- 시험 조건: [t_P(6) P(6) t_I(6) I(6)] → prism_tb18_profile 출력 [P; I_VA] --------------------------------
TB.prof = [R0.tP(:)' R0.PP(:)' R0.tI(:)' R0.II(:)'];
TB.rated_pk = R0.rated_pk;  TB.i_abs = R0.i_abs;
TB.n_shed = R0.n_shed;  TB.n_ret = R0.n_ret;
TB.guard_t = 1.5*TB.dt;

assignin('base', 'P', P);
assignin('base', 'TB', TB);
