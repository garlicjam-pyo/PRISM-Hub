%TB26_INIT  TB26(Stage A 25 kHz 설계 A25: 4모듈 + 스위치 출력용량 + 모듈 관리기·셰딩·고장 처리 + R2 버스 + V_A 노드 충전기) 초기화.
%
%   사례: 기본 작업공간 변수 TB26_case(없으면 'FF25_800V_charge_m1'). 기준값은 ref/TB26_<사례>_init.json(검증 코드 E33, A25).
%   Stage A(A25, docs/37·E32): 위치당 C4MS008075U2 2병렬(R_ds 125 °C 5.27 mΩ), L_r 864.6 nH, C_fly 46.875 µF(f_r0 25 kHz),
%     바디 다이오드 V_f 4.5 V, 스위치 셀 출력용량 = 등가 선형 C_oss(V_bat/2)(TB25와 같은 방식), 데드타임 100 ns.
%   게이트: ctrl/prism_gate_stageA_zcpf.m(TB24와 같은 함수), 파라미터는 E32 문턱(셰딩 I_off 20·I_on 30·Ipk_on 53 A, 관리기
%     Im_up 70·Im_dn 60·Ipk_m 66 A, 시간 상수 150 kHz 값의 6배). 고장 모듈 0이면 고장 없음.
%   버스(E23·TB16·TB22·TB24와 같음): C_A 400 µF → 배선 3 mΩ·1.5 µH → C_b 400 µF ∥ RC 감쇠기 ∥ 정전력 부하.
%   해석기: Simscape 지역 해석기 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회).

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');
caseName = 'FF25_800V_charge_m1';
if evalin('base', 'exist(''TB26_case'', ''var'')'), caseName = evalin('base', 'TB26_case'); end
R0 = jsondecode(fileread(fullfile(refDir, ['TB26_' caseName '_init.json'])));

TB = struct();
TB.name = 'TB26_StageA25_Integrated';
TB.case = caseName;
TB.kind = R0.kind;
TB.dt = 2.5e-9;
TB.t_end = R0.t_end;
if evalin('base', 'exist(''TB26_tend'', ''var'')'), TB.t_end = evalin('base', 'TB26_tend'); end   % (smoke)
TB.t0 = R0.t0;
TB.vbat = R0.vbat;

% ---- Stage A(A25) -------------------------------------------------------------------------------
P = prism_hub_params(struct('dt', TB.dt));
TB.A       = P.A;
TB.A.Lr    = R0.A.Lr;  TB.A.Cfly = R0.A.Cfly;  TB.A.Rds = R0.A.Rds;  TB.A.Vf = R0.A.Vf;
TB.A.ESR   = R0.A.ESR; TB.A.RL = R0.A.RL;  TB.A.Rmisc = R0.A.Rmisc;
TB.A.fr0   = 1/(2*pi*sqrt(TB.A.Lr*TB.A.Cfly));
TB.A.Goff  = 1e-8;  TB.A.Rd = TB.A.Rds;  TB.A.Goffd = 1e-8;
TB.A.Coss  = R0.A.Coss;                           % 스위치 셀마다 등가 선형 출력용량 [F]
TB.A.vC0   = TB.vbat/2;
TB.vC0_ph  = R0.vC0(:)';
TB.A.CA    = R0.CA;
TB.gateA_zcpm_prm = R0.gate_prm(:)';              % 파라미터 23개(make_ref_TB26.py가 회로 간격으로 계산)
TB.gateA_en  = ones(1, 8);
TB.gateA_off = R0.gate_off(:)';
TB.fault_module = R0.fault_module;  TB.t_fault = R0.t_fault;

% ---- 버스 --------------------------------------------------------------------------------------
TB.Rpath = R0.bus.Rw;  TB.Lpath = R0.bus.Lw;  TB.Cb = R0.bus.Cb;
TB.Rdmp = R0.bus.Rd;   TB.Cdmp = R0.bus.Cd;   TB.vmin_q = R0.bus.vmin;
TB.vA0 = R0.vA0;  TB.vb0 = R0.vb0;  TB.iw0 = R0.iw0;

% ---- 시험 조건: [t_P(6) P(6) t_I(6) I(6) t_chg_on t_chg_off] -------------------------------------------
TB.prof = [R0.tP(:)' R0.PP(:)' R0.tI(:)' R0.II(:)' R0.chg(:)'];
TB.P_rated = R0.P_rated;  TB.pk_limit = R0.pk_limit;  TB.i_abs = R0.i_abs;
TB.dv_A = R0.dv_A;  TB.v_b470 = R0.v_b470;  TB.n_end = R0.n_end;
TB.T = 1/TB.A.fr0;
TB.guard_t = 1.5*TB.dt;

assignin('base', 'P', P);
assignin('base', 'TB', TB);
