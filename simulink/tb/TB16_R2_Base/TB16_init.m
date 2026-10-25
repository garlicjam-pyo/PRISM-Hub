%TB16_INIT  TB16(R2 기본형 통합: Stage A 1모듈 + 400 V 버스·감쇠기·정전력 부하 + 조정형 Stage C) 초기화: 경로, 시험 조건 TB.
%
%   사례: 기본 작업공간 변수 TB16_case(없으면 'A_540V_Cstep'). 버스·Stage C 값, 초기조건, 제어 파라미터는
%   ref/TB16_<사례>_init.json(검증 코드 E23 = E22 평균모델 + 버스 회로, ref/make_ref_TB16.py)에서 읽는다.
%   Stage A: prism_hub_params(검증 코드 E1과 같은 설계값) 모듈 1(2위상), 영교차 추종 게이트(TB06과 같음).
%   Stage C: TB15와 같다(L_m 33 µH, 데드타임 1차 100·2차 40 ns, 경부하 두 브리지 구동 < 0.6 kW·2차 90 ns).
%   버스(R2 기본형, Stage B 없음): V_A 노드 C_A 400 µF → 배선 3 mΩ·1.5 µH → C_b 400 µF ∥ RC 감쇠기 48.6 mΩ + 1.6 mF
%   ∥ 400 V 정전력 부하 ∥ Stage C 입력. 48 V 쪽은 정전력 부하(배터리 없음).
%   해석기: Simscape 지역 해석기 후진 오일러 2.5 ns(Stage C 공진망 간격, TB05), 고정 비용(모드 반복 3회).
%   Stage A는 주기 정상상태에서 시작하지 않으므로(C_fly = V_bat/2, 공진전류 0) 사건은 2 ms에 둔다(TB06은 1 ms 이후 판정).

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');
if evalin('base', 'exist(''TB16_case'', ''var'')')
    caseName = evalin('base', 'TB16_case');
else
    caseName = 'A_540V_Cstep';
end
R0 = jsondecode(fileread(fullfile(refDir, ['TB16_' caseName '_init.json'])));

TB = struct();
TB.name = 'TB16_R2_Base';
TB.case = caseName;
TB.dt = 2.5e-9;
TB.t_end = R0.t_end;
TB.t_event = R0.t_event;
TB.vbat = R0.vbat;

% ---- Stage A(모듈 1, 위상 1·2) -------------------------------------------------------------------------
P = prism_hub_params(struct('dt', TB.dt));        % Stage A 부품값만 쓴다(Stage B·Stage C 값은 쓰지 않음)
TB.A       = P.A;
TB.A.Goff  = 1e-8;  TB.A.Rd = P.A.Rds;  TB.A.Goffd = 1e-8;
TB.A.vC0   = TB.vbat/2;                           % 플라잉 커패시터 초기 = V_bat/2
TB.A.CA    = R0.bus.CA;                           % V_A 노드 출력 커패시터 400 µF
t_on  = 0.5/P.A.fr0 - P.A.td;                     % 공칭 도통시간(E1과 같은 정의)
TB.gateA_zcp_prm = [TB.dt, round(P.A.td/TB.dt), round(0.80*t_on/TB.dt), round(1.12*t_on/TB.dt), ...
                    round(20e-9/TB.dt), 0.5];     % [dt n_dead n_min n_max n_det(20 ns) i_thr 0.5 A](TB06과 같음)
TB.gateA_en  = [1 1 0 0 0 0 0 0];
Thalf = round(0.5/P.A.fr0/TB.dt);
TB.gateA_off = [0 round(Thalf/2) 0 0 0 0 0 0];   % 위상 2는 T/4 늦게(인터리빙)

% ---- 400 V 버스(R2 기본형) -------------------------------------------------------------------------------
TB.Rpath = R0.bus.RW;  TB.Lpath = R0.bus.LW;  TB.Cb = R0.bus.CB;
TB.Rdmp = R0.bus.RD;   TB.Cdmp = R0.bus.CD;
TB.vA0 = R0.vA0;  TB.vb0 = R0.vb0;  TB.iw0 = R0.iw0;   % E23 평형점(Stage A 정적 등가)
TB.vmin_q = R0.bus.vmin_q;                         % 400 V 정전력 부하 i = Q/max(v_bus, 200 V)

% ---- Stage C(TB15와 같음) --------------------------------------------------------------------------------
TB.SB = struct('Ron', R0.Ron_b, 'Goff', 1e-8, 'Vf', 2.5, 'Rd', R0.Ron_b, 'Goffd', 1e-8, 'Coss', R0.Coss_b);   % 벅 레그
TB.CP = struct('Ron', R0.Ron_p, 'Goff', 1e-8, 'Vf', 0.05, 'Rd', R0.Ron_p, 'Goffd', 1e-8, 'Coss', R0.Coss_p);  % CLLC 1차
TB.CS = struct('Ron', R0.Ron_s, 'Goff', 1e-8, 'Vf', 0.05, 'Rd', R0.Ron_s, 'Goffd', 1e-8, 'Coss', R0.Coss_s);  % CLLC 2차
n = R0.n;
TB.C = struct('n', n, 'Lr1', R0.Lr, 'Cr1', R0.Cr, 'Lm', R0.Lm, 'Lr2', R0.Lr/n^2, 'Cr2', R0.Cr*n^2, ...
              'Rw1', R0.Rw/2, 'Rw2', R0.Rw/2/n^2, 'Co', R0.CO, 'CI', R0.CI, 'L', R0.L, 'RL', R0.RL);
TB.x0 = R0.x0(:)';                                 % [i_L v_I v_o i_x](E23 평형점)
TB.bat_on = 0; TB.OCV = R0.OCV; TB.Rbat = 1e6;     % 배터리 없음(가지를 1 MΩ으로 끊음)
TB.vmin_cpl = 10;                                  % 48 V 정전력 부하 i = P/max(v_o, 10 V)

% ---- 시험 조건(구간 선형): [t_Q(4) Q(4) t_P(4) P(4)] → prism_tb14_profile 출력 [Q; P] ----------------------
pad = @(v) [v(:)' repmat(v(end), 1, 4 - numel(v))];
tQ = pad(R0.tQ); QQ = pad(R0.QQ); tP = pad(R0.tP); PP = pad(R0.PP);
TB.prof = [tQ QQ tP PP];
TB.band = R0.band(:)';

% ---- 제어 ----------------------------------------------------------------------------------------------
ctl = R0.ctl(:)';
iL0 = TB.x0(1);
mode0 = 1; if iL0 < 0, mode0 = -1; end
p0 = PP(1);
if abs(p0) < R0.P_in, mode0 = 2; end              % 시작 전력이 두 브리지 구동 문턱 아래
TB.ctl_prm = [ctl R0.Vref TB.dt TB.bat_on 0 R0.d0 mode0 iL0 n R0.P_in R0.P_out];   % 26개
TB.gate_prm = [TB.dt 1/R0.fb R0.td_b 1/R0.fr R0.td_p R0.td_s R0.td_sb];
TB.P_in = R0.P_in; TB.P_out = R0.P_out;
vo0 = TB.x0(3);
TB.meas0 = [TB.vb0 iL0 TB.x0(2) vo0 p0/vo0 0];
TB.guard_t = 1.5*TB.dt;
TB.pulse_rating_secondary = R0.pulse_rating_secondary;

assignin('base', 'P', P);
assignin('base', 'TB', TB);
