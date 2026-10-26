%TB20_INIT  TB20(충전 중 R2 기본형: Stage A 4모듈 + 충전기 + 400 V 버스·감쇠기 + 조정형 Stage C + V_A 클램프) 초기화.
%
%   사례: 기본 작업공간 변수 TB20_case(없으면 'A_920V_pathloss'). 기준값·초기조건·시험 조건은
%   ref/TB20_<사례>_init.json(검증 코드 E26 run_event + E22 run_avg, ref/make_ref_TB20.py)에서 읽는다.
%   Stage A: prism_hub_params(E1과 같은 설계값) 4모듈(8위상), 영교차 추종 게이트(TB07과 같은 T/16 인터리빙).
%            위상 동작 여부는 시험 조건(prism_tb20_profile)이 사건 시각부터 바꾼다(게이트 차단 = 고장 차단).
%   버스(R2 기본형): V_A 노드 C_A 400 µF ∥ 충전기(전류원) ∥ V_A 클램프(1 Ω + 스위치, 468/463 V, 1 µs) → 배선 3 mΩ·1.5 µH
%                   → C_b 400 µF ∥ RC 감쇠기 48.6 mΩ + 1.6 mF ∥ 400 V 정전력 부하 ∥ 조정형 Stage C(TB15·TB16과 같음).
%   해석기: Simscape 지역 해석기 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회).

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');
if evalin('base', 'exist(''TB20_case'', ''var'')')
    caseName = evalin('base', 'TB20_case');
else
    caseName = 'A_920V_pathloss';
end
R0 = jsondecode(fileread(fullfile(refDir, ['TB20_' caseName '_init.json'])));

TB = struct();
TB.name = 'TB20_R2_Charging_Stop';
TB.case = caseName;
TB.dt = 2.5e-9;
TB.t_end = R0.t_end;
TB.t_event = R0.t_ev;
TB.vbat = R0.vbat;

% ---- Stage A(4모듈, 위상 1–8) ---------------------------------------------------------------------------
P = prism_hub_params(struct('dt', TB.dt));        % Stage A 부품값만 쓴다
TB.A       = P.A;
TB.A.Goff  = 1e-8;  TB.A.Rd = P.A.Rds;  TB.A.Goffd = 1e-8;
TB.A.vC0   = TB.vbat/2;                           % 플라잉 커패시터 초기 = V_bat/2
TB.A.CA    = R0.bus.CA;                           % V_A 노드 400 µF
t_on  = 0.5/P.A.fr0 - P.A.td;
TB.gateA_zcp_prm = [TB.dt, round(P.A.td/TB.dt), round(0.80*t_on/TB.dt), round(1.12*t_on/TB.dt), ...
                    round(20e-9/TB.dt), 0.5];     % TB06·TB07과 같음
TB.gateA_en  = ones(1, 8);                        % (게이트는 태그 en_A로 받음, 이 값은 쓰지 않음)
Thalf = round(0.5/P.A.fr0/TB.dt);
TB.gateA_off = round((0:7)*Thalf/8);              % 8위상 인터리빙 T/16(TB07과 같음)
TB.rated_pk_A = R0.rated_pk;  TB.pk_lim = R0.pk_lim;  TB.i_abs = 1.0;

% ---- 버스(R2 기본형)·충전기·클램프 --------------------------------------------------------------------------
TB.Rpath = R0.bus.RW;  TB.Lpath = R0.bus.LW;  TB.Cb = R0.bus.CB;
TB.Rdmp = R0.bus.RD;   TB.Cdmp = R0.bus.CD;
TB.vA0 = R0.vA0;  TB.vb0 = R0.vb0;  TB.iw0 = R0.iw0;   % E26 평형점(Stage A 정적 등가)
TB.vmin_q = R0.bus.vmin_q;
TB.Rclamp = R0.clamp.R;
TB.clamp_prm = [TB.dt, R0.clamp.von, R0.clamp.voff, round(R0.clamp.delay/TB.dt)];
TB.v_lim = R0.v_lim;

% ---- Stage C(TB15·TB16과 같음) ------------------------------------------------------------------------------
TB.SB = struct('Ron', R0.Ron_b, 'Goff', 1e-8, 'Vf', 2.5, 'Rd', R0.Ron_b, 'Goffd', 1e-8, 'Coss', R0.Coss_b);
TB.CP = struct('Ron', R0.Ron_p, 'Goff', 1e-8, 'Vf', 0.05, 'Rd', R0.Ron_p, 'Goffd', 1e-8, 'Coss', R0.Coss_p);
TB.CS = struct('Ron', R0.Ron_s, 'Goff', 1e-8, 'Vf', 0.05, 'Rd', R0.Ron_s, 'Goffd', 1e-8, 'Coss', R0.Coss_s);
n = R0.n;
TB.C = struct('n', n, 'Lr1', R0.Lr, 'Cr1', R0.Cr, 'Lm', R0.Lm, 'Lr2', R0.Lr/n^2, 'Cr2', R0.Cr*n^2, ...
              'Rw1', R0.Rw/2, 'Rw2', R0.Rw/2/n^2, 'Co', R0.CO, 'CI', R0.CI, 'L', R0.L, 'RL', R0.RL);
TB.x0 = R0.x0(:)';
TB.bat_on = 0; TB.OCV = R0.OCV; TB.Rbat = 1e6;     % 48 V 배터리 없음
TB.vmin_cpl = 10;

% ---- 시험 조건: [t_I(6) I(6) t_ev mask(8) Q P] → prism_tb20_profile 출력 [i_ch; Q; P; en(8)] -------------------
TB.prof = [R0.tI(:)' R0.II(:)' R0.t_ev R0.mask(:)' R0.Q R0.P];
TB.band = R0.band(:)';

% ---- Stage C 제어(TB16과 같음, PI 적분 평형 시작 = TB17과 같음) ------------------------------------------------
ctl = R0.ctl(:)';
iL0 = TB.x0(1);
mode0 = 1; if iL0 < 0, mode0 = -1; end
p0 = R0.P;
if abs(p0) < R0.P_in, mode0 = 2; end
TB.ctl_prm = [ctl R0.Vref TB.dt TB.bat_on 0 R0.d0 mode0 iL0 n R0.P_in R0.P_out R0.Ii0];   % 27개(마지막 = 전류 PI 적분 시작값, TB17과 같음)
TB.gate_prm = [TB.dt 1/R0.fb R0.td_b 1/R0.fr R0.td_p R0.td_s R0.td_sb];
TB.P_in = R0.P_in; TB.P_out = R0.P_out;
vo0 = TB.x0(3);
TB.meas0 = [TB.vb0 iL0 TB.x0(2) vo0 p0/vo0 0];
TB.guard_t = 1.5*TB.dt;
TB.pulse_rating_secondary = R0.pulse_rating_secondary;

assignin('base', 'P', P);
assignin('base', 'TB', TB);
