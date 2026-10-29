%TB32_INIT  TB32(TB30 회로 + 가지를 따로 둔 V_A 클램프: E39 재판정, 가지 저항 모서리 섞임) 초기화. 회로·초기화는 TB30과 같고 클램프 값은 ref에서 읽는다.
%
%   회로: 배터리 → Stage A 4모듈(A25: 위치당 C4MS008075U2 2병렬, L_r 864.6 nH, C_fly 46.875 µF, f_r0 25 kHz, 스위치 셀 출력용량)
%         → V_A 노드(C_A 2.4 mF, 충전기 전류원, V_A 클램프 468/463 V·1 µs, 가지 1 = 작은 저항·강하 0, 가지 2 = 큰 저항 가지 n−1개의 등가·강하 2.05 V) → 배선 → 400 V 버스·감쇠기·정전력 부하
%         → 조정형 Stage C → 48 V(TB21과 같음).
%   게이트: ctrl/prism_gate_stageA_zcpf.m(TB24·TB27과 같음: 영교차 추종 + 모듈 관리기·셰딩 + 모듈 고장 처리), E32 문턱.
%           위상 동작 여부는 시험 조건 태그 en_A(배터리 경로 상실 = 사건 때 8위상 차단), 충전 요청은 태그 chg_req.
%   사례: 기본 작업공간 변수 TB32_case(없으면 'A32_640V_noload_mix'). 기준값·초기조건·시험 조건은 ref/TB32_<사례>_init.json
%         (ref/make_ref_TB32.py = 검증 코드 E26(가지별 클램프 저항)·E22·E35 모델).
%   해석기: Simscape 지역 해석기 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회).

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');
caseName = 'A32_640V_noload_mix';
if evalin('base', 'exist(''TB32_case'', ''var'')'), caseName = evalin('base', 'TB32_case'); end
R0 = jsondecode(fileread(fullfile(refDir, ['TB32_' caseName '_init.json'])));

TB = struct();
TB.name = 'TB32_A25R_ClampMix';
TB.case = caseName;
TB.kind = R0.kind;
TB.dt = 2.5e-9;
TB.t_end = R0.t_end;
if evalin('base', 'exist(''TB32_tend'', ''var'')'), TB.t_end = evalin('base', 'TB32_tend'); end   % (smoke)
TB.t_event = R0.t_ev;
TB.vbat = R0.vbat;

% ---- Stage A(A25R, TB27과 같음) -----------------------------------------------------------------------------
P = prism_hub_params(struct('dt', TB.dt));
TB.A       = P.A;
TB.A.Lr    = R0.A.Lr;  TB.A.Cfly = R0.A.Cfly;  TB.A.Rds = R0.A.Rds;  TB.A.Vf = R0.A.Vf;
TB.A.ESR   = R0.A.ESR; TB.A.RL = R0.A.RL;  TB.A.Rmisc = R0.A.Rmisc;
TB.A.fr0   = 1/(2*pi*sqrt(TB.A.Lr*TB.A.Cfly));
TB.A.Goff  = 1e-8;  TB.A.Rd = TB.A.Rds;  TB.A.Goffd = 1e-8;
TB.A.Coss  = R0.A.Coss;                           % 스위치 셀마다 등가 선형 출력용량 [F]
TB.A.vC0   = TB.vbat/2;
TB.vC0_ph  = R0.vC0(:)';
TB.A.CA    = R0.bus.CA;                           % V_A 노드 2.4 mF
TB.gateA_zcpm_prm = R0.gate_prm(:)';              % 파라미터 23개(make_ref_TB32.py가 회로 간격으로 계산)
TB.gateA_en  = ones(1, 8);                        % (게이트는 태그 en_A로 받음, 이 값은 쓰지 않음)
TB.gateA_off = R0.gate_off(:)';
TB.fault_module = R0.fault_module;  TB.t_fault = R0.t_fault;
TB.P_rated = R0.P_rated;  TB.pk_lim = R0.pk_lim;  TB.i_abs = R0.i_abs;
TB.w_hold = R0.w_hold(:)';
TB.T = 1/TB.A.fr0;

% ---- 버스(R2 기본형)·충전기·클램프(TB21과 같음, C_A만 2.4 mF) ---------------------------------------------------
TB.Rpath = R0.bus.RW;  TB.Lpath = R0.bus.LW;  TB.Cb = R0.bus.CB;
TB.Rdmp = R0.bus.RD;   TB.Cdmp = R0.bus.CD;
TB.vA0 = R0.vA0;  TB.vb0 = R0.vb0;  TB.iw0 = R0.iw0;   % E26 평형점(Stage A 정적 등가)
TB.vmin_q = R0.bus.vmin_q;
TB.Rcl1 = R0.clamp.R1;                            % 가지 1: 작은 저항 모서리 가지 하나
TB.Vdrop1 = R0.clamp.vdrop1;                      %         스위치 강하 0
TB.Rcl2 = R0.clamp.R2;                            % 가지 2: 큰 저항 모서리 가지 n−1개의 등가(R_가지 / (n−1))
TB.Vdrop2 = R0.clamp.vdrop2;                      %         스위치 강하 2.05 V(직렬 직류 전원으로)
TB.n_hi = R0.clamp.n_hi;                          % 가지 2가 나타내는 가지 수(n−1)
TB.clamp_prm = [TB.dt, R0.clamp.von, R0.clamp.voff, round(R0.clamp.delay/TB.dt)];
TB.v_lim = R0.v_lim;

% ---- Stage C(TB15·TB16·TB21과 같음) ------------------------------------------------------------------------------
TB.SB = struct('Ron', R0.Ron_b, 'Goff', 1e-8, 'Vf', 2.5, 'Rd', R0.Ron_b, 'Goffd', 1e-8, 'Coss', R0.Coss_b);
TB.CP = struct('Ron', R0.Ron_p, 'Goff', 1e-8, 'Vf', 0.05, 'Rd', R0.Ron_p, 'Goffd', 1e-8, 'Coss', R0.Coss_p);
TB.CS = struct('Ron', R0.Ron_s, 'Goff', 1e-8, 'Vf', 0.05, 'Rd', R0.Ron_s, 'Goffd', 1e-8, 'Coss', R0.Coss_s);
n = R0.n;
TB.C = struct('n', n, 'Lr1', R0.Lr, 'Cr1', R0.Cr, 'Lm', R0.Lm, 'Lr2', R0.Lr/n^2, 'Cr2', R0.Cr*n^2, ...
              'Rw1', R0.Rw/2, 'Rw2', R0.Rw/2/n^2, 'Co', R0.CO, 'CI', R0.CI, 'L', R0.L, 'RL', R0.RL);
TB.x0 = R0.x0(:)';
TB.bat_on = 0; TB.OCV = R0.OCV; TB.Rbat = 1e6;     % 48 V 배터리 없음
TB.vmin_cpl = 10;

% ---- 시험 조건: [t_I(6) I(6) t_ev mask(8) Q P t_chg_on t_chg_off] → prism_tb28_profile 출력 [i_ch; Q; P; en(8); chg] -----
TB.prof = [R0.tI(:)' R0.II(:)' R0.t_ev R0.mask(:)' R0.Q R0.P R0.chg(:)'];
TB.band = R0.band(:)';

% ---- Stage C 제어(TB16과 같음, PI 적분 평형 시작 = TB17과 같음) ------------------------------------------------
ctl = R0.ctl(:)';
iL0 = TB.x0(1);
mode0 = 1; if iL0 < 0, mode0 = -1; end
p0 = R0.P;
if abs(p0) < R0.P_in, mode0 = 2; end
TB.ctl_prm = [ctl R0.Vref TB.dt TB.bat_on 0 R0.d0 mode0 iL0 n R0.P_in R0.P_out R0.Ii0];
TB.gate_prm = [TB.dt 1/R0.fb R0.td_b 1/R0.fr R0.td_p R0.td_s R0.td_sb];
TB.P_in = R0.P_in; TB.P_out = R0.P_out;
vo0 = TB.x0(3);
TB.meas0 = [TB.vb0 iL0 TB.x0(2) vo0 p0/vo0 0];
TB.guard_t = 1.5*TB.dt;
TB.pulse_rating_secondary = R0.pulse_rating_secondary;

assignin('base', 'P', P);
assignin('base', 'TB', TB);
