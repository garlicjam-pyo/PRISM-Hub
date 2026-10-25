%TB15_INIT  TB15(조정형 Stage C의 경부하 두 브리지 구동: 동기 벅 + CLLC 직류변압기, 48 V 정전력 부하) 초기화: 경로, 시험 조건 TB.
%
%   사례: 기본 작업공간 변수 TB15_case(없으면 'F_400V_rev_light'). 회로 값·초기조건·제어 파라미터는
%   ref/TB15_<사례>_init.json(검증 코드 E22의 선택 설계·제어, ref/make_ref_TB15.py)에서 읽는다.
%   소자: 벅 650 V GaN(GS66516T) 2병렬, CLLC 1차 650 V GaN 2병렬, 2차 150 V GaN(EPC2305) 2병렬(R_on은 125 °C 값).
%   CLLC의 받는 쪽 브리지는 역병렬 다이오드(Vf 50 mV, R_d = R_on)로 도통 = 이상 동기정류 근사(E22 dcx와 같음).
%   L_m과 CLLC 데드타임(보내는 쪽별 td_p·td_s)은 E22 zvs(레그 출력용량 모델)로 정한 값이다(TB14와 같음).
%   TB14와 다른 것: 출력 전력 지령 |P*| < P_in이면 두 브리지를 같은 위상으로 구동하고(2차 데드타임 td_sb), > P_out이면 보내는
%   쪽 하나로 돌아간다(E22 both). TB14 사례 F·G에서 역방향 경부하의 DCX 이득 상승을 확인한 뒤의 대책이다.
%   벅 레그의 데드타임 도통은 GaN 역방향 도통 2.5 V로 둔다.
%   해석기: Simscape 지역 해석기 후진 오일러, 간격 2.5 ns(TB05에서 정한 250 kHz 공진망 간격), 고정 비용(모드 반복 3회, TB08–TB13과 같음).
%   가변 비용(TB05와 같음)은 사례 A 4.5 ms에 약 24분 걸려, 사례 A를 두 방식으로 비교해 고정 비용을 확인했다(results/solver_probe).
%   제어 표본 10 µs.

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
refDir = fullfile(tbDir, 'ref');
if evalin('base', 'exist(''TB15_case'', ''var'')')
    caseName = evalin('base', 'TB15_case');
else
    caseName = 'F_400V_rev_light';
end
R0 = jsondecode(fileread(fullfile(refDir, ['TB15_' caseName '_init.json'])));

TB = struct();
TB.name = 'TB15_StageC_LightLoad';
TB.case = caseName;
TB.dt = 2.5e-9;
TB.t_end = R0.t_end;
TB.t_event = R0.t_event;

% ---- 소자 ----------------------------------------------------------------------------------------------
TB.SB = struct('Ron', R0.Ron_b, 'Goff', 1e-8, 'Vf', 2.5, 'Rd', R0.Ron_b, 'Goffd', 1e-8, 'Coss', R0.Coss_b);   % 벅 레그
TB.CP = struct('Ron', R0.Ron_p, 'Goff', 1e-8, 'Vf', 0.05, 'Rd', R0.Ron_p, 'Goffd', 1e-8, 'Coss', R0.Coss_p);  % CLLC 1차
TB.CS = struct('Ron', R0.Ron_s, 'Goff', 1e-8, 'Vf', 0.05, 'Rd', R0.Ron_s, 'Goffd', 1e-8, 'Coss', R0.Coss_s);  % CLLC 2차
n = R0.n;
TB.C = struct('n', n, 'Lr1', R0.Lr, 'Cr1', R0.Cr, 'Lm', R0.Lm, 'Lr2', R0.Lr/n^2, 'Cr2', R0.Cr*n^2, ...
              'Rw1', R0.Rw/2, 'Rw2', R0.Rw/2/n^2, 'Co', R0.CO, 'CI', R0.CI, 'L', R0.L, 'RL', R0.RL);
TB.x0 = R0.x0(:)';                                   % [i_L v_I v_o i_x] 초기(E22 평형점)

% ---- 48 V 쪽: 배터리(있으면), 정전력 부하 ------------------------------------------------------------------
TB.bat_on = R0.bat_on;
TB.OCV = R0.OCV;
TB.Rbat = R0.Rbat;
if TB.bat_on < 0.5, TB.Rbat = 1e6; end               % 배터리 없음: 가지를 1 MΩ으로 끊는다
TB.vmin_cpl = 10;                                    % 정전력 부하 i = P/max(v_o, 10 V)

% ---- 시험 조건(구간 선형) -------------------------------------------------------------------------------
pad = @(v) [v(:)' repmat(v(end), 1, 4 - numel(v))];
tV = pad(R0.tV); VV = pad(R0.VV); tP = pad(R0.tP); PP = pad(R0.PP);
TB.prof = [tV VV tP PP];

% ---- 제어 ----------------------------------------------------------------------------------------------
ctl = R0.ctl(:)';
iL0 = TB.x0(1);
mode0 = 1; if iL0 < 0, mode0 = -1; end
p0 = PP(1);
if abs(p0) < R0.P_in, mode0 = 2; end                % 시작 전력이 문턱 아래면 두 브리지 구동에서 시작
TB.ctl_prm = [ctl R0.Vref TB.dt TB.bat_on 0 R0.d0 mode0 iL0 n R0.P_in R0.P_out];   % 26개(prism_stageC_reg_ctrl.m 머리말)
TB.gate_prm = [TB.dt 1/R0.fb R0.td_b 1/R0.fr R0.td_p R0.td_s R0.td_sb];   % CLLC 데드타임: td_p, td_s(E22 zvs), 두 브리지 구동 2차 td_sb(E22 both)
TB.P_in = R0.P_in; TB.P_out = R0.P_out;
p0 = PP(1); vo0 = TB.x0(3);
ib0 = 0; if TB.bat_on > 0.5, ib0 = (vo0 - TB.OCV)/R0.Rbat; end
TB.meas0 = [VV(1) iL0 TB.x0(2) vo0 p0/vo0 ib0];
TB.guard_t = 1.5*TB.dt;
TB.pulse_rating_secondary = R0.pulse_rating_secondary;

assignin('base', 'TB', TB);
