%TB24_INIT  TB24(Stage A 모듈 고장과 모듈 관리기 연동: TB22 회로 + 고장 모듈을 관리기 후보에서 빼는 게이트) 초기화.
%
%   사례: 기본 작업공간 변수 TB24_case(없으면 'FF_800V_charge_m1'). 기준값은 ref/TB24_<사례>_init.json(검증 코드 E30).
%   Stage A: prism_hub_params(E1과 같은 설계값) 4모듈(8위상), 8위상 인터리빙 시작 지연 T/16, 공진전류 0에서 시작.
%            C_fly는 동작 모듈 V_bat/2, 멈춘 모듈 V_bat/2 − 5 V(docs/34 균형 회로 목표, E30과 같음).
%   게이트: ctrl/prism_gate_stageA_zcpf.m(TB22의 zcpm + 모듈 고장 처리). 고장 모듈·간격 번호는 파라미터 22·23번.
%   버스(E23·TB16·TB22와 같음): V_A 노드 C_A 400 µF → 배선 3 mΩ·1.5 µH → C_b 400 µF ∥ RC 감쇠기 48.6 mΩ + 1.6 mF ∥ 정전력 부하.
%   해석기: Simscape 지역 해석기 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회).

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');
caseName = 'FF_800V_charge_m1';
if evalin('base', 'exist(''TB24_case'', ''var'')'), caseName = evalin('base', 'TB24_case'); end
R0 = jsondecode(fileread(fullfile(refDir, ['TB24_' caseName '_init.json'])));

TB = struct();
TB.name = 'TB24_StageA_ModuleFault';
TB.case = caseName;
TB.kind = R0.kind;
TB.dt = 2.5e-9;
TB.t_end = R0.t_end;
if evalin('base', 'exist(''TB24_tend'', ''var'')'), TB.t_end = evalin('base', 'TB24_tend'); end   % (smoke)
TB.t0 = R0.t0;                                    % 판정 시작(Stage A 시작 과도 뒤)
TB.vbat = R0.vbat;

% ---- Stage A(4모듈, 위상 1–8) ---------------------------------------------------------------------------
P = prism_hub_params(struct('dt', TB.dt));
TB.A       = P.A;
TB.A.Goff  = 1e-8;  TB.A.Rd = P.A.Rds;  TB.A.Goffd = 1e-8;
TB.A.vC0   = TB.vbat/2;                           % 위상별 값은 TB.vC0_ph(build_TB24가 C_fly마다 지정)
TB.vC0_ph  = R0.vC0(:)';
TB.A.CA    = R0.CA;
t_on  = 0.5/P.A.fr0 - P.A.td;
zcp = [TB.dt, round(P.A.td/TB.dt), round(0.80*t_on/TB.dt), round(1.12*t_on/TB.dt), round(20e-9/TB.dt), 0.5, 0];
M = R0.mgr;
TB.fault_module = R0.fault_module;  TB.t_fault = R0.t_fault;
TB.gateA_zcpm_prm = [zcp, M.I_off, M.I_on, M.Ipk_on, TB.dt/M.tau, round(M.t_dwell/TB.dt), ...
                     M.Im_up, M.Im_dn, M.Ipk_m, round(M.t_dwell_m/TB.dt), round(M.t_lock/TB.dt), R0.n0, R0.If0, ...
                     round(M.t_hold/TB.dt), TB.dt/M.tau_m, TB.fault_module, round(TB.t_fault/TB.dt)];
TB.gateA_en  = ones(1, 8);
Thalf = round(0.5/P.A.fr0/TB.dt);
TB.gateA_off = round((0:7)*Thalf/8);              % 8위상 인터리빙 T/16(TB07·TB20·TB22와 같음)

% ---- 버스(E23·TB16·TB22와 같음) --------------------------------------------------------------------------
TB.Rpath = R0.bus.Rw;  TB.Lpath = R0.bus.Lw;  TB.Cb = R0.bus.Cb;
TB.Rdmp = R0.bus.Rd;   TB.Cdmp = R0.bus.Cd;   TB.vmin_q = R0.bus.vmin;
TB.vA0 = R0.vA0;  TB.vb0 = R0.vb0;  TB.iw0 = R0.iw0;

% ---- 시험 조건: [t_P(6) P(6) t_I(6) I(6) t_chg_on t_chg_off] → prism_tb22_profile 출력 [P; I_VA; chg] ---------
TB.prof = [R0.tP(:)' R0.PP(:)' R0.tI(:)' R0.II(:)' R0.chg(:)'];
TB.P_rated = R0.P_rated;  TB.pk_limit = R0.pk_limit;  TB.i_abs = R0.i_abs;
TB.dv_A = R0.dv_A;  TB.v_b470 = R0.v_b470;  TB.n_end = R0.n_end;
TB.guard_t = 1.5*TB.dt;

assignin('base', 'P', P);
assignin('base', 'TB', TB);
