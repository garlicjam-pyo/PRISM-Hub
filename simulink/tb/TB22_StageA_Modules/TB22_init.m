%TB22_INIT  TB22(Stage A 4모듈 경부하 운전: 모듈 관리기 + 모듈별 위상 셰딩 + 무장 전 부호 없는 영교차 검출 게이트, R2 버스, V_A 노드 충전기) 초기화.
%
%   사례: 기본 작업공간 변수 TB22_case(없으면 'MC_800V_charge_prestart'). 기준값은 ref/TB22_<사례>_init.json(검증 코드 E28).
%   선택: 기본 작업공간 변수 TB22_ref(1이면 전부 켬 비교 실행: 충전 요청을 처음부터 끝까지 켜 모듈 4개를 모두 동작시키고,
%         I_off = −1로 위상 셰딩을 끈다. 같은 회로·게이트 함수로 T3 기준 V_A를 만든다)
%   Stage A: prism_hub_params(E1과 같은 설계값) 4모듈(8위상), 8위상 인터리빙 시작 지연 T/16, C_fly = V_bat/2(멈춘 모듈 포함)·공진전류 0에서 시작.
%   버스(E23·TB16·TB18과 같음): V_A 노드 C_A 400 µF → 배선 3 mΩ·1.5 µH → C_b 400 µF ∥ RC 감쇠기 48.6 mΩ + 1.6 mF ∥ 정전력 부하.
%   해석기: Simscape 지역 해석기 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회).

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');
caseName = 'MC_800V_charge_prestart';
if evalin('base', 'exist(''TB22_case'', ''var'')'), caseName = evalin('base', 'TB22_case'); end
refRun = 0;
if evalin('base', 'exist(''TB22_ref'', ''var'')'), refRun = evalin('base', 'TB22_ref'); end
R0 = jsondecode(fileread(fullfile(refDir, ['TB22_' caseName '_init.json'])));

TB = struct();
TB.name = 'TB22_StageA_Modules';
TB.case = caseName;
TB.ref_run = refRun;
TB.dt = 2.5e-9;
TB.t_end = R0.t_end;
if evalin('base', 'exist(''TB22_tend'', ''var'')'), TB.t_end = evalin('base', 'TB22_tend'); end   % (smoke)
TB.t0 = R0.t0;                                    % 판정 시작(Stage A 시작 과도 뒤)
TB.vbat = R0.vbat;

% ---- Stage A(4모듈, 위상 1–8) ---------------------------------------------------------------------------
P = prism_hub_params(struct('dt', TB.dt));
TB.A       = P.A;
TB.A.Goff  = 1e-8;  TB.A.Rd = P.A.Rds;  TB.A.Goffd = 1e-8;
TB.A.vC0   = TB.vbat/2;                           % 멈춘 모듈도 V_bat/2(균형 회로가 정한 전압, E28 restart)
TB.A.CA    = R0.CA;
t_on  = 0.5/P.A.fr0 - P.A.td;
zcp = [TB.dt, round(P.A.td/TB.dt), round(0.80*t_on/TB.dt), round(1.12*t_on/TB.dt), round(20e-9/TB.dt), 0.5, 0];
%      7번째 0 = 무장하지 못한 반주기를 부호 없는 영교차(|i| < i_thr, 블랭킹 뒤)에서 끔(E28). E27·TB21의 n_nom 방식은 쓰지 않는다
M = R0.mgr;
Ioff = M.I_off; n0 = R0.n0; chg = R0.chg(:)';
if refRun, Ioff = -1; n0 = 4; chg = [0 1]; end   % 전부 켬: 충전 요청 계속 → 모듈 4개, 위상 셰딩 없음
TB.gateA_zcpm_prm = [zcp, Ioff, M.I_on, M.Ipk_on, TB.dt/M.tau, round(M.t_dwell/TB.dt), ...
                     M.Im_up, M.Im_dn, M.Ipk_m, round(M.t_dwell_m/TB.dt), round(M.t_lock/TB.dt), n0, R0.If0, ...
                     round(M.t_hold/TB.dt), TB.dt/M.tau_m];
TB.gateA_en  = ones(1, 8);
Thalf = round(0.5/P.A.fr0/TB.dt);
TB.gateA_off = round((0:7)*Thalf/8);              % 8위상 인터리빙 T/16(TB07·TB20과 같음)

% ---- 버스(E23·TB16과 같음) -----------------------------------------------------------------------------
TB.Rpath = R0.bus.Rw;  TB.Lpath = R0.bus.Lw;  TB.Cb = R0.bus.Cb;
TB.Rdmp = R0.bus.Rd;   TB.Cdmp = R0.bus.Cd;   TB.vmin_q = R0.bus.vmin;
if refRun
    TB.vA0 = R0.vA0_ref;  TB.vb0 = R0.vb0_ref;  TB.iw0 = R0.iw0_ref;
else
    TB.vA0 = R0.vA0;  TB.vb0 = R0.vb0;  TB.iw0 = R0.iw0;
end

% ---- 시험 조건: [t_P(6) P(6) t_I(6) I(6) t_chg_on t_chg_off] → prism_tb22_profile 출력 [P; I_VA; chg] ---------
TB.prof = [R0.tP(:)' R0.PP(:)' R0.tI(:)' R0.II(:)' chg];
TB.P_rated = R0.P_rated;  TB.i_abs = R0.i_abs;  TB.dv_tol = R0.dv_tol;
TB.n_end = R0.n_end;  TB.add_max = R0.add_max;  TB.rem_max = R0.rem_max;
TB.guard_t = 1.5*TB.dt;

assignin('base', 'P', P);
assignin('base', 'TB', TB);
