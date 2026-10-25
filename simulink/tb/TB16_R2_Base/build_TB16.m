function build_TB16()
%BUILD_TB16  TB16 테스트벤치 모델(TB16_R2_Base.slx)을 처음부터 만든다.
%
%   R2 기본형 통합(Stage B 없음): 배터리 → Stage A 모듈 1(2위상, 영교차 추종) → V_A 노드(C_A 400 µF) → 배선 3 mΩ·1.5 µH
%   → 400 V 버스(C_b 400 µF ∥ RC 감쇠기 48.6 mΩ + 1.6 mF ∥ 400 V 정전력 부하) → 조정형 Stage C(TB15와 같음) → 48 V 정전력 부하
%   구성
%     V_bat(이상 전압원) ── StageA_Module1 ── I_Aout ── C_A ── R_path ── L_path ── I_path ── 버스(C_bus, R_dmp–C_dmp, I_load400)
%     ── I_in ── StageC_Regulated ── 48 V(V_o, 배터리 가지 1 MΩ, I_load48)
%     Test_Conditions: 400 V 부하 전력 Q(t)·48 V 부하 전력 P(t)(구간 선형, ctrl/prism_tb14_profile.m), 정전력 부하 전류
%     Gate_StageA(영교차 추종, TB06과 같음) · Controller_StageC → Gate_StageC(TB15와 같음)
%   실행: prism_run('build_TB16')  →  prism_run('run_TB16')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB16_R2_Base';
evalin('base', 'clear TB16_case');
run(fullfile(here, 'TB16_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');
sl_model_new(mdl, 'TB16_init.m');
TBb = evalin('base', 'TB');

sl_note(mdl, 'TB16 — R2 기본형 통합 회로: Stage A 모듈 1 + 400 V 버스(감쇠기) + 조정형 Stage C 5 kW(Stage B 없음)', [30 10 1500 40], 'title');

% ---- 전력 회로 -------------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
gref = [fl 'Electrical Elements/Electrical Reference'];
y0 = 200;
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bat', [60 y0+80 100 y0+140], 'Orientation', 'down', 'v0', 'TB.vbat');
sl_add(mdl, gref, 'GND', [60 y0+200 100 y0+230]);
sl_solver(mdl, 'Solver', [10 y0+150 50 y0+180], 'GND', 'V', 3);   % 고정 비용(모드 반복 3회)
build_stageA_module(mdl, 'StageA_Module1', [160 y0+20 320 y0+220], 1, 'TB.A');
sl_add(mdl, gref, 'GND_A', [160 y0+250 200 y0+280]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_Aout', [370 y0+5 420 y0+45]);
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_A', [460 y0+80 500 y0+140], 'Orientation', 'down', ...
    'c', 'TB.A.CA', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vA0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_CA', [460 y0+200 500 y0+230]);
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_A', [530 y0+80 570 y0+140], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_VA', [530 y0+200 570 y0+230]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_path', [600 y0+15 650 y0+35], 'R', 'TB.Rpath');
sl_add(mdl, [fl 'Electrical Elements/Inductor'], 'L_path', [680 y0+15 730 y0+35], 'l', 'TB.Lpath', 'r', '0', ...
    'i_L_specify', 'on', 'i_L', 'TB.iw0', 'i_L_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_path', [760 y0+5 810 y0+45]);
% 400 V 버스
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_bus', [860 y0+80 900 y0+140], 'Orientation', 'down', ...
    'c', 'TB.Cb', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vb0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_Cb', [860 y0+200 900 y0+230]);
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_bus', [930 y0+80 970 y0+140], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_Vb', [930 y0+200 970 y0+230]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_dmp', [1000 y0+70 1040 y0+110], 'Orientation', 'down', 'R', 'TB.Rdmp');
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_dmp', [1000 y0+130 1040 y0+170], 'Orientation', 'down', ...
    'c', 'TB.Cdmp', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vb0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_dmp', [1000 y0+200 1040 y0+230]);
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load400', [1080 y0+80 1120 y0+140], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iload400_PS', [1090 y0+40 1120 y0+60]);
sl_add(mdl, gref, 'GND_load', [1080 y0+200 1120 y0+230]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_in', [1160 y0+5 1210 y0+45]);
build_stageC_reg(mdl, 'StageC_Regulated', [1260 y0 1560 y0+280], 'TB');
sl_add(mdl, gref, 'GND_C', [1260 y0+310 1300 y0+340]);
% 48 V 쪽
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_o', [1620 y0+80 1660 y0+140], 'Orientation', 'down');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_bat', [1700 y0+5 1750 y0+45]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_bat', [1780 y0+15 1840 y0+35], 'R', 'TB.Rbat');
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bat48', [1870 y0+80 1910 y0+140], 'Orientation', 'down', 'v0', 'TB.OCV');
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load48', [1960 y0+80 2000 y0+140], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iload48_PS', [1970 y0+40 2000 y0+60]);

sl_pc(mdl, 'V_bat', 'p', 'StageA_Module1', 'VIN');
sl_pc(mdl, 'V_bat', 'n', 'GND', 'V');
sl_pc(mdl, 'StageA_Module1', 'GND', 'GND_A', 'V');
sl_pc(mdl, 'StageA_Module1', 'VOUT', 'I_Aout', 'p');     % Stage A 출력전류: 모듈 → V_A 노드
sl_pc(mdl, 'I_Aout', 'n', 'C_A', 'p');
sl_pc(mdl, 'C_A', 'n', 'GND_CA', 'V');
sl_pc(mdl, 'V_A', 'p', 'C_A', 'p');
sl_pc(mdl, 'V_A', 'n', 'GND_VA', 'V');
sl_pc(mdl, 'C_A', 'p', 'R_path', 'p');
sl_pc(mdl, 'R_path', 'n', 'L_path', 'p');
sl_pc(mdl, 'L_path', 'n', 'I_path', 'p');                % 배선 전류 + : V_A → 버스
sl_pc(mdl, 'I_path', 'n', 'C_bus', 'p');
sl_pc(mdl, 'C_bus', 'n', 'GND_Cb', 'V');
sl_pc(mdl, 'V_bus', 'p', 'C_bus', 'p');
sl_pc(mdl, 'V_bus', 'n', 'GND_Vb', 'V');
sl_pc(mdl, 'R_dmp', 'p', 'C_bus', 'p');                  % RC 감쇠기: 버스 → R_d → C_d → GND
sl_pc(mdl, 'R_dmp', 'n', 'C_dmp', 'p');
sl_pc(mdl, 'C_dmp', 'n', 'GND_dmp', 'V');
sl_pc(mdl, 'I_load400', 'tail', 'C_bus', 'p');           % 400 V 부하 전류: 버스 → 전류원 → GND
sl_pc(mdl, 'I_load400', 'head', 'GND_load', 'V');
sl_pc(mdl, 'iload400_PS', 'output', 'I_load400', 'iT');
sl_pc(mdl, 'C_bus', 'p', 'I_in', 'p');                   % Stage C 입력전류 + : 버스 → Stage C
sl_pc(mdl, 'I_in', 'n', 'StageC_Regulated', 'DC_P');
sl_pc(mdl, 'StageC_Regulated', 'DC_N', 'GND_C', 'V');
sl_pc(mdl, 'V_o', 'p', 'StageC_Regulated', 'VO_P');
sl_pc(mdl, 'V_o', 'n', 'StageC_Regulated', 'VO_N');
sl_pc(mdl, 'I_bat', 'p', 'StageC_Regulated', 'VO_P');
sl_pc(mdl, 'I_bat', 'n', 'R_bat', 'p');
sl_pc(mdl, 'R_bat', 'n', 'V_bat48', 'p');
sl_pc(mdl, 'V_bat48', 'n', 'StageC_Regulated', 'VO_N');
sl_pc(mdl, 'I_load48', 'tail', 'StageC_Regulated', 'VO_P');
sl_pc(mdl, 'I_load48', 'head', 'StageC_Regulated', 'VO_N');
sl_pc(mdl, 'iload48_PS', 'output', 'I_load48', 'iT');
sl_meas(mdl, 'I_Aout', 'I', 'iAo',  [370 y0+380]);
sl_meas(mdl, 'V_A',    'V', 'vA',   [530 y0+380]);
sl_meas(mdl, 'I_path', 'I', 'ipath', [760 y0+380]);
sl_meas(mdl, 'V_bus',  'V', 'vbus', [930 y0+380]);
sl_meas(mdl, 'I_in',   'I', 'iin',  [1160 y0+380]);
sl_meas(mdl, 'V_o',    'V', 'vo',   [1620 y0+380]);
sl_meas(mdl, 'I_bat',  'I', 'ibat', [1780 y0+380]);
sl_note(mdl, sprintf('배터리(이상 전압원)\nV_bat = %.0f V', TBb.vbat), [30 y0+290 160 y0+320]);
sl_note(mdl, sprintf('V_A 노드(충전 포트), C_A 400 µF'), [440 y0-40 700 y0-20]);
sl_note(mdl, sprintf('배선 3 mΩ·1.5 µH\n(Stage A 출력저항은 회로에서 생김)'), [600 y0+50 840 y0+80]);
sl_note(mdl, sprintf(['400 V 보조버스(R2 기본형: V_A를 그대로 따름)\n' ...
    'C_b 400 µF ∥ RC 감쇠기 48.6 mΩ + 1.6 mF ∥ 정전력 부하 Q/max(v, 200 V)']), [840 y0-50 1240 y0-20]);
sl_note(mdl, sprintf('48 V 전원망(절연측): 정전력 부하 P/max(v_o, 10 V), 배터리 가지 1 MΩ(없음)'), [1600 y0-40 2050 y0-20]);

% ---- 시험 조건: 400 V 부하 전력 Q(t), 48 V 부하 전력 P(t), 정전력 부하 전류 ---------------------------------
ts = [mdl '/Test_Conditions'];
add_block('built-in/Subsystem', ts, 'Position', [1080 60 1220 120], 'BackgroundColor', 'lightBlue');
sl_add(ts, 'simulink/Sources/Digital Clock', 'Clock', [30 40 80 70], 'SampleTime', 'TB.dt');
sl_add(ts, 'simulink/Signal Routing/Goto', 't', [120 75 160 95], 'GotoTag', 't', 'TagVisibility', 'global');
sl_line(ts, 'Clock/1', 't/1');
sl_add(ts, 'simulink/Sources/Constant', 'prof', [30 100 130 120], 'Value', 'TB.prof');
sl_mfunc(ts, 'Profile', [180 40 300 130], 'prism_tb14_profile.m');
sl_line(ts, 'Clock/1', 'Profile/1');
sl_line(ts, 'prof/1', 'Profile/2');
sl_add(ts, 'simulink/Signal Routing/Demux', 'split', [330 40 335 130], 'Outputs', '2');
sl_line(ts, 'Profile/1', 'split/1');
sl_add(ts, 'simulink/Signal Routing/Goto', 'p400', [380 30 460 50], 'GotoTag', 'p400', 'TagVisibility', 'global');
sl_add(ts, 'simulink/Signal Routing/Goto', 'p_load', [380 120 460 140], 'GotoTag', 'p_load', 'TagVisibility', 'global');
sl_line(ts, 'split/1', 'p400/1');
sl_line(ts, 'split/2', 'p_load/1');
% 400 V 정전력 부하 전류 = Q/max(v_bus, 200 V)
sl_add(ts, 'simulink/Signal Routing/From', 'vb_from', [30 180 110 200], 'GotoTag', 'vbus');
sl_add(ts, 'simulink/Signal Routing/From', 't_from1', [30 220 110 240], 'GotoTag', 't');
sl_startup_guard(ts, 'Guard_vbus', [150 175 190 245], 'TB.vb0', 'TB', [30 260 110 280]);
sl_line(ts, 'vb_from/1', 'Guard_vbus/1');
sl_line(ts, 't_from1/1', 'Guard_vbus/2');
sl_add(ts, 'simulink/Discrete/Unit Delay', 'vb_z1', [220 195 250 225], 'SampleTime', 'TB.dt');
sl_add(ts, 'simulink/Sources/Constant', 'vmin_q', [220 250 280 270], 'Value', 'TB.vmin_q');
sl_add(ts, 'simulink/Math Operations/MinMax', 'vb_floor', [310 200 340 250], 'Function', 'max', 'Inputs', '2');
sl_add(ts, 'simulink/Math Operations/Divide', 'Q_over_v', [380 160 420 240]);
sl_add(ts, 'simulink/Signal Routing/Goto', 'iload400', [460 210 540 230], 'GotoTag', 'iload400', 'TagVisibility', 'global');
add_block('simulink/Sinks/Out1', [ts '/i_load400'], 'Position', [470 170 500 190]);
sl_line(ts, 'Guard_vbus/1', 'vb_z1/1');
sl_line(ts, 'vb_z1/1', 'vb_floor/1');
sl_line(ts, 'vmin_q/1', 'vb_floor/2');
sl_line(ts, 'split/1', 'Q_over_v/1');
sl_line(ts, 'vb_floor/1', 'Q_over_v/2');
sl_line(ts, 'Q_over_v/1', 'iload400/1');
sl_line(ts, 'Q_over_v/1', 'i_load400/1');
% 48 V 정전력 부하 전류 = P/max(v_o, 10 V)
sl_add(ts, 'simulink/Signal Routing/From', 'vo_from', [30 330 110 350], 'GotoTag', 'vo');
sl_add(ts, 'simulink/Signal Routing/From', 't_from2', [30 370 110 390], 'GotoTag', 't');
sl_startup_guard(ts, 'Guard_vo', [150 325 190 395], 'TB.x0(3)', 'TB', [30 410 110 430]);
sl_line(ts, 'vo_from/1', 'Guard_vo/1');
sl_line(ts, 't_from2/1', 'Guard_vo/2');
sl_add(ts, 'simulink/Discrete/Unit Delay', 'vo_z1', [220 345 250 375], 'SampleTime', 'TB.dt');
sl_add(ts, 'simulink/Sources/Constant', 'v_min', [220 400 280 420], 'Value', 'TB.vmin_cpl');
sl_add(ts, 'simulink/Math Operations/MinMax', 'v_floor', [310 350 340 400], 'Function', 'max', 'Inputs', '2');
sl_add(ts, 'simulink/Math Operations/Divide', 'P_over_v', [380 310 420 390]);
sl_add(ts, 'simulink/Signal Routing/Goto', 'iload', [460 360 540 380], 'GotoTag', 'iload', 'TagVisibility', 'global');
add_block('simulink/Sinks/Out1', [ts '/i_load48'], 'Position', [470 320 500 340]);
sl_line(ts, 'Guard_vo/1', 'vo_z1/1');
sl_line(ts, 'vo_z1/1', 'v_floor/1');
sl_line(ts, 'v_min/1', 'v_floor/2');
sl_line(ts, 'split/2', 'P_over_v/1');
sl_line(ts, 'v_floor/1', 'P_over_v/2');
sl_line(ts, 'P_over_v/1', 'iload/1');
sl_line(ts, 'P_over_v/1', 'i_load48/1');
sl_note(ts, sprintf(['시험 조건(시험 장치): 400 V 부하 전력 Q(t)와 48 V 부하 전력 P(t)는 구간 선형(TB.prof = [t_Q Q t_P P]).\n' ...
    '정전력 부하 전류 i = Q/max(v_bus, 200 V), P/max(v_o, 10 V). 전압은 시작 표본 보호 후 한 간격 지연(대수 루프 방지).']), ...
    [30 450 700 490], 'box');
sl_line(mdl, 'Test_Conditions/1', 'iload400_PS/1');
sl_line(mdl, 'Test_Conditions/2', 'iload48_PS/1');

% ---- 제어·게이트 ---------------------------------------------------------------------------------
yc = 700;
build_stageA_gate_zcp(mdl, [160 yc 340 yc+80], 'TB', [1 2]);

cs = [mdl '/Controller_StageC'];
add_block('built-in/Subsystem', cs, 'Position', [1260 yc 1440 yc+80], 'BackgroundColor', 'yellow');
sl_add(cs, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', 'TB.dt');
tg = {'vbus', 'iL', 'vI', 'vo', 'iload', 'ibat'};
for k = 1:6
    sl_add(cs, 'simulink/Signal Routing/From', ['from_' tg{k}], [30 70+30*(k-1) 110 90+30*(k-1)], 'GotoTag', tg{k});
end
sl_add(cs, 'simulink/Signal Routing/Mux', 'meas_mux', [140 65 145 245], 'Inputs', '6');
for k = 1:6, sl_line(cs, sprintf('from_%s/1', tg{k}), sprintf('meas_mux/%d', k)); end
sl_add(cs, 'simulink/Discrete/Unit Delay', 'meas_z1', [170 140 200 170], 'SampleTime', 'TB.dt', 'InitialCondition', 'TB.meas0');
sl_line(cs, 'meas_mux/1', 'meas_z1/1');
sl_startup_guard(cs, 'Startup_guard', [230 130 270 210], 'TB.meas0', 'TB', [150 250 240 270]);
sl_line(cs, 'meas_z1/1', 'Startup_guard/1');
sl_line(cs, 'Clock/1', 'Startup_guard/2');
sl_add(cs, 'simulink/Sources/Constant', 'ctl_prm', [30 290 130 310], 'Value', 'TB.ctl_prm');
sl_mfunc(cs, 'StageC_Controller', [310 40 470 260], 'prism_stageC_reg_ctrl.m');
sl_line(cs, 'Clock/1', 'StageC_Controller/1');
sl_line(cs, 'Startup_guard/1', 'StageC_Controller/2');
sl_line(cs, 'ctl_prm/1', 'StageC_Controller/3');
sl_add(cs, 'simulink/Signal Routing/Goto', 'uc', [510 140 580 160], 'GotoTag', 'ucC', 'TagVisibility', 'global');
sl_line(cs, 'StageC_Controller/1', 'uc/1');
sl_note(cs, sprintf(['조정형 Stage C 제어기(검증 코드 E22 control과 같은 알고리즘·게인, 표본 10 µs, 계산 지연 1주기, TB15와 같음)\n' ...
    '입력 v_bus는 실제 버스(R2 기본형: V_A − 배선 강하). 출력: [d; 모드(+1·−1 보내는 쪽, 2 두 브리지); i_L 지령; 선택]']), ...
    [30 330 760 380], 'box');

gs = [mdl '/Gate_StageC'];
add_block('built-in/Subsystem', gs, 'Position', [1520 yc 1700 yc+80], 'BackgroundColor', 'yellow');
sl_add(gs, 'simulink/Sources/Digital Clock', 'Clock', [30 30 80 60], 'SampleTime', 'TB.dt');
sl_add(gs, 'simulink/Signal Routing/From', 'uc_from', [30 80 110 100], 'GotoTag', 'ucC');
sl_add(gs, 'simulink/Signal Routing/Selector', 'u_sel', [130 80 150 100], 'IndexParamArray', {'[1 2]'}, 'InputPortWidth', '4');
sl_add(gs, 'simulink/Sources/Constant', 'gate_prm', [30 130 130 150], 'Value', 'TB.gate_prm');
sl_mfunc(gs, 'StageC_Gate', [190 30 330 160], 'prism_gate_stageC_reg.m');
sl_line(gs, 'uc_from/1', 'u_sel/1');
sl_line(gs, 'Clock/1', 'StageC_Gate/1');
sl_line(gs, 'u_sel/1', 'StageC_Gate/2');
sl_line(gs, 'gate_prm/1', 'StageC_Gate/3');
sl_add(gs, 'simulink/Signal Routing/Demux', 'Demux', [380 20 390 330], 'Outputs', '10');
sl_line(gs, 'StageC_Gate/1', 'Demux/1');
tags = {'gS_BH', 'gS_BL', 'gC_Q1', 'gC_Q2', 'gC_Q3', 'gC_Q4', 'gC_S1', 'gC_S2', 'gC_S3', 'gC_S4'};
for s = 1:10
    sl_add(gs, 'simulink/Signal Routing/Goto', tags{s}, [440 15+31*(s-1) 520 35+31*(s-1)], 'GotoTag', tags{s}, 'TagVisibility', 'global', ...
        'ShowName', 'off');
    sl_line(gs, sprintf('Demux/%d', s), [tags{s} '/1']);
end
sl_note(gs, sprintf(['게이트: 벅 100 kHz 중앙 정렬 PWM(데드타임 50 ns, 골에서 제어 표본) + CLLC 250 kHz 공진점(TB15와 같음).\n' ...
    'CLLC 데드타임: 1차가 보낼 때 %.0f ns, 2차가 보낼 때 %.0f ns. |P*| < %.0f W: 두 브리지 같은 위상(2차 %.0f ns).'], ...
    1e9*TBb.gate_prm(5), 1e9*TBb.gate_prm(6), TBb.P_in, 1e9*TBb.gate_prm(7)), [30 360 760 400], 'box');
sl_note(mdl, sprintf(['제어부: Gate_StageA(영교차 추종, 태그 gA_P1_*·gA_P2_*, TB06과 같음) · Controller_StageC → Gate_StageC\n' ...
    '(태그 gS_BH·gS_BL 벅, gC_Q1–Q4 1차, gC_S1–S4 2차). 각 게이트는 전역 태그로 스위치 셀에 전달된다.']), [160 yc+100 1300 yc+130]);

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [2100 y0 2220 y0+280], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_StageA', {'iA_P1', 'iA_P2', 'vA'}; ...
     'Scope_Bus', {'vbus', 'p400', 'iin'}; ...
     'Scope_48V', {'vo', 'ix', 'p_load'}; ...
     'Scope_Buck', {'iL', 'vI'}; ...
     'Scope_CLLC', {'ir1', 'im', 'ir2'}; ...
     'Scope_Legs', {'vleg1', 'vlegs1'}; ...
     'Scope_Controller', {'ucC'}}, ...
    {'t', 'tA', ''; 'iA_P1', 'iA1', ''; 'iA_P2', 'iA2', ''; 'stA_P1', 'st1', ''; 'stA_P2', 'st2', ''; ...
     't', 't', '4'; 'vA', 'vA', '4'; 'iAo', 'iAo', '4'; 'ipath', 'ipath', '4'; 'vbus', 'vbus', '4'; 'iin', 'iin', '4'; ...
     'p400', 'p400', '4'; 'iL', 'iL', '4'; 'vI', 'vI', '4'; 'vo', 'vo', '4'; 'ix', 'ix', '4'; 'ibat', 'ibat', '4'; ...
     'iload', 'iload', '4'; 'ir1', 'ir1', '4'; 'im', 'im', '4'; 'ir2', 'ir2', '4'; 'vleg1', 'vleg1', '4'; 'vlegs1', 'vlegs1', '4'; ...
     'gC_Q1', 'gq1', '4'; 'gC_Q2', 'gq2', '4'; 'gC_S1', 'gs1', '4'; 'gC_S2', 'gs2', '4'; 'ucC', 'uc', '4000'});
sl_note(mdl, sprintf(['계측: Scope 7개(Stage A, 버스, 48 V, 벅, CLLC 공진, 레그 노드, 제어기)\n' ...
    '+ To Workspace(Stage A 위상 전류·구간 2.5 ns, 나머지 10 ns, 제어기 출력 10 µs)']), [2080 y0+300 2420 y0+340]);

sl_note(mdl, sprintf(['파라미터(TB16_init.m ← ref/TB16_<사례>_init.json = 검증 코드 E23, Stage A는 prism_hub_params = E1 설계값)\n' ...
    'Stage A: C_fly 7.8125 µF, L_r 144.1 nH(f_r0 150 kHz), R_ds 6 mΩ(750 V SiC 2병렬), 데드타임 100 ns, 영교차 검출 0.5 A·지연 20 ns, C_A 400 µF\n' ...
    '버스: 배선 3 mΩ·1.5 µH, C_b 400 µF, RC 감쇠기 48.6 mΩ + 1.6 mF(E15 ④·TB08–TB13과 같음)\n' ...
    'Stage C: 벅 204 µH·C_I 20 µF·100 kHz, CLLC 4.8:1·L_r 2.19 µH·C_r 184.9 nF·L_m %.1f µH·250 kHz, C_o 2.2 mF(TB15와 같음)\n' ...
    '해석기: Simscape 지역 해석기 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회), Stage C 제어 표본 10 µs'], 1e6*TBb.C.Lm), ...
    [30 yc+160 1500 yc+250], 'box');
sl_note(mdl, sprintf(['검증 목적: R2 기본형에서는 Stage B 없이 400 V 버스가 V_A를 따른다. 조정형 Stage C(TB14·TB15)는 이상 버스 전원으로 확인했다.\n' ...
    '실제 Stage A(공진 스위치드 커패시터 + C_A)와 버스 감쇠기·400 V 부하가 있는 버스에서 (1) 48 V 조정, (2) 버스 안정·범위,\n' ...
    '(3) Stage C가 끌어가는 전류(100 kHz 맥동 포함)에서 Stage A 영전류 스위칭이 유지되는지 확인한다. 기준: E23(평균모델)·E1(Stage A).\n' ...
    '사례: A 540 V(V_A 270 V) Stage C 0.1 → 5 kW, B 806 V 400 V 부하 15 → 25 kW(Stage C 3 kW), C 907 V Stage C 5 → −3 kW(400 V 부하 10 kW)']), ...
    [30 yc+260 1500 yc+330], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
sl_export_png({mdl, [mdl '/StageA_Module1'], [mdl '/StageC_Regulated'], [mdl '/Gate_StageA'], [mdl '/Controller_StageC'], ...
    [mdl '/Gate_StageC'], [mdl '/Test_Conditions']}, fullfile(here, 'results'));
end
