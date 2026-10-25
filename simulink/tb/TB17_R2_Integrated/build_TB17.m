function build_TB17()
%BUILD_TB17  TB17 테스트벤치 모델(TB17_R2_Integrated.slx)을 처음부터 만든다.
%
%   R2-W460 통합 회로: TB13(창 조정 Stage B, 보호 상태기계, H-브리지 개방 강등 P3t)의 이상 V_A와 정전력 등가 Stage C 몫을
%   실제 회로로 바꾼다.
%     V_bat ── StageA_Module1(영교차 추종) ── I_Aout ── C_A ── R_path(3 mΩ) ── L_path ── I_path ──┬── StageB_Regulator ──┬── 400 V 버스
%                                                                                                ├── 바이패스 주 스위치 ───┤
%                                                                                                └── 소프트 투입 저항 ─────┘
%     400 V 버스: C_b ∥ RC 감쇠기 ∥ 400 V 정전력 부하(20 kW, 분리 신호 → 0 W) ∥ DAB 손실 등가 ∥ I_in ── StageC_Regulated ── 48 V(4.9 kW)
%     제어: Gate_StageA(TB16과 같음), Controller_StageB·Gate_StageB(TB13과 같음), Controller_StageC·Gate_StageC(TB15·TB16과 같음)
%   태그 충돌: Stage B의 DAB 누설 인덕터 전류 태그가 'iL'(DAB 손실 등가가 씀)이라 Stage C 벅 인덕터 전류는 'iLb'로 둔다.
%   시각 태그 't'는 Gate_StageB 안의 것 하나만 쓴다.
%   실행: prism_run('build_TB17')  →  prism_run('run_TB17')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB17_R2_Integrated';
evalin('base', 'clear TB17_case');
run(fullfile(here, 'TB17_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');
sl_model_new(mdl, 'TB17_init.m');
TBb = evalin('base', 'TB');

sl_note(mdl, 'TB17 — R2-W460 통합 회로: Stage A 모듈 1 + 창 조정 Stage B(H-브리지 개방 강등) + 조정형 Stage C 5 kW', [30 10 1700 40], 'title');

% ---- Stage A와 경로 --------------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
gref = [fl 'Electrical Elements/Electrical Reference'];
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bat', [40 230 80 290], 'Orientation', 'down', 'v0', 'TB.vbat');
sl_add(mdl, gref, 'GND_bat', [40 440 80 470]);
sl_solver(mdl, 'Solver', [0 360 40 390], 'GND_bat', 'V', 3);     % 고정 비용(모드 반복 3회)
build_stageA_module(mdl, 'StageA_Module1', [120 140 280 340], 1, 'TB.A');
sl_add(mdl, gref, 'GND_A', [120 380 160 410]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_Aout', [320 150 370 190]);
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_A', [400 230 440 290], 'Orientation', 'down', ...
    'c', 'TB.A.CA', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vA0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_CA', [400 440 440 470]);
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_A', [470 230 510 290], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_VA', [470 440 510 470]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_path', [540 160 590 180], 'R', 'TB.Rpath');
sl_add(mdl, [fl 'Electrical Elements/Inductor'], 'L_path', [620 160 670 180], 'l', 'TB.Lpath', 'r', '0', ...
    'i_L_specify', 'on', 'i_L', 'TB.ip0', 'i_L_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_path', [700 150 750 190]);
sl_pc(mdl, 'V_bat', 'p', 'StageA_Module1', 'VIN');
sl_pc(mdl, 'V_bat', 'n', 'GND_bat', 'V');
sl_pc(mdl, 'StageA_Module1', 'GND', 'GND_A', 'V');
sl_pc(mdl, 'StageA_Module1', 'VOUT', 'I_Aout', 'p');
sl_pc(mdl, 'I_Aout', 'n', 'C_A', 'p');
sl_pc(mdl, 'C_A', 'n', 'GND_CA', 'V');
sl_pc(mdl, 'V_A', 'p', 'C_A', 'p');
sl_pc(mdl, 'V_A', 'n', 'GND_VA', 'V');
sl_pc(mdl, 'C_A', 'p', 'R_path', 'p');
sl_pc(mdl, 'R_path', 'n', 'L_path', 'p');
sl_pc(mdl, 'L_path', 'n', 'I_path', 'p');
sl_meas(mdl, 'I_Aout', 'I', 'iAo', [320 520]);
sl_meas(mdl, 'V_A',    'V', 'vA',  [470 520]);
sl_note(mdl, sprintf('배터리(이상 전압원)\nV_bat = %.0f V', TBb.vbat), [20 300 120 330]);
sl_note(mdl, sprintf('V_A 노드(충전 포트), C_A 400 µF'), [330 110 560 130]);
sl_note(mdl, sprintf('배선 3 mΩ·1.5 µH\n(Stage A 출력저항 약 10.2 mΩ는 회로에서 생김)'), [530 190 760 220]);

% ---- Stage B·바이패스·버스(TB13과 같음) ---------------------------------------------------------------
sl_add(mdl, gref, 'GND', [1150 520 1190 550]);
build_stageB(mdl, 'StageB_Regulator', [810 140 1050 380], 'TB', ...
    struct('CossP', 'TB.B.Coss_dp', 'CossS', 'TB.B.Coss_ds', ...
           'CossNote', 'DAB C_oss 1차 335 pF·2차 1371 pF, 소자 역방향 도통 2 V', ...
           'Xfmr', 'Xfmr_4p6to1', 'DabNote', '창 조정 R2-W460: 권선비 4.6:1, 누설 14.68 µH, 정격 4 kW', 'Brake', 'TB.Rbrk'));
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_bus', [1150 240 1190 300], 'Orientation', 'down', ...
    'c', 'TB.Cb', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vb0', 'vc_priority', 'High');
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_dmp', [1080 420 1130 440], 'R', 'TB.Rdmp');
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_dmp', [1150 400 1190 460], 'Orientation', 'down', ...
    'c', 'TB.Cdmp', 'r', '0', 'vc_specify', 'on', 'vc', 'TB.vcd0', 'vc_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_bus', [1230 240 1270 300], 'Orientation', 'down');
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load', [1320 240 1360 300], 'Orientation', 'down');
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_dabloss', [1410 240 1450 300], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iload_PS', [1330 200 1360 220]);
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iloss_PS', [1420 200 1450 220]);
cb = struct('tag', 'gByp', 'Ron', 'TB.Rbyp_cell', 'Goff', 'TB.B.Goff', 'Vf', 'TB.Vf_byp', 'Rd', 'TB.Rd_byp', ...
    'Goffd', 'TB.B.Goffd', 'Coss', '');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_byp', [820 60 870 100]);
sl_switch_cell(mdl, 'S_BYP_1', [910 55 990 105], setfield(setfield(cb, 'label', 'BYP1'), 'orient', 'right')); %#ok<SFLD>
sl_switch_cell(mdl, 'S_BYP_2', [1030 55 1110 105], setfield(setfield(cb, 'label', 'BYP2'), 'orient', 'left'));  %#ok<SFLD>
sl_add(mdl, [fl 'Electrical Elements/Variable Resistor'], 'R_soft', [1090 140 1140 156], 'Rmin', '1e-4');
sl_add(mdl, 'simulink/Signal Routing/From', 'sup_from', [770 115 840 135], 'GotoTag', 'r2_sup', 'ShowName', 'off');
sl_add(mdl, 'simulink/Signal Routing/Selector', 'Rsoft_sel', [855 115 875 135], 'IndexParamArray', {'7'}, 'InputPortWidth', '12');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'Rsoft_PS', [910 115 940 135]);
sl_line(mdl, 'sup_from/1', 'Rsoft_sel/1');
sl_line(mdl, 'Rsoft_sel/1', 'Rsoft_PS/1');
sl_pc(mdl, 'I_path', 'n', 'StageB_Regulator', 'SER');
sl_pc(mdl, 'I_byp', 'p', 'I_path', 'n');
sl_pc(mdl, 'I_byp', 'n', 'S_BYP_1', 'D');
sl_pc(mdl, 'S_BYP_1', 'S', 'S_BYP_2', 'S');
sl_pc(mdl, 'S_BYP_2', 'D', 'C_bus', 'p');
sl_pc(mdl, 'R_soft', 'p', 'I_byp', 'n');
sl_pc(mdl, 'R_soft', 'n', 'C_bus', 'p');
sl_pc(mdl, 'Rsoft_PS', 'output', 'R_soft', 'R');
sl_pc(mdl, 'StageB_Regulator', 'BUS', 'C_bus', 'p');
sl_pc(mdl, 'StageB_Regulator', 'GND', 'GND', 'V');
sl_pc(mdl, 'C_bus', 'n', 'GND', 'V');
sl_pc(mdl, 'R_dmp', 'p', 'C_bus', 'p');
sl_pc(mdl, 'R_dmp', 'n', 'C_dmp', 'p');
sl_pc(mdl, 'C_dmp', 'n', 'GND', 'V');
sl_pc(mdl, 'V_bus', 'p', 'C_bus', 'p');
sl_pc(mdl, 'V_bus', 'n', 'GND', 'V');
sl_pc(mdl, 'I_load', 'tail', 'C_bus', 'p');
sl_pc(mdl, 'I_load', 'head', 'GND', 'V');
sl_pc(mdl, 'I_dabloss', 'tail', 'C_bus', 'p');
sl_pc(mdl, 'I_dabloss', 'head', 'GND', 'V');
sl_pc(mdl, 'iload_PS', 'output', 'I_load', 'iT');
sl_pc(mdl, 'iloss_PS', 'output', 'I_dabloss', 'iT');
sl_meas(mdl, 'I_path', 'I', 'ip',   [700 520]);
sl_meas(mdl, 'V_bus',  'V', 'vbus', [1230 520]);
sl_meas(mdl, 'I_byp',  'I', 'ibyp', [600 70]);
sl_note(mdl, sprintf(['바이패스: 150 V GaN 2병렬 × 역직렬(합계 3.3 mΩ, 역방향 도통 1.4 V), 게이트 gByp\n' ...
    '∥ 소프트 투입 가변 저항 R_soft(상태기계 지령)']), [1130 50 1500 80]);
sl_note(mdl, sprintf(['400 V 보조버스(창 기준 460 V, 상한 B_470): C_b 400 µF ∥ RC 감쇠기 1.6 mF·48.6 mΩ\n' ...
    '∥ 400 V 정전력 부하 %.0f kW(분리 신호 → %.0f W) ∥ DAB 손실 등가 ∥ 조정형 Stage C'], TBb.P0/1e3, TBb.Pc), [1080 470 1560 500]);
build_bus_loads(mdl, [1270 110 1380 160], [1390 110 1500 160], 'TB', struct('ShedTag', 'r2_sup', 'ShedIndex', 10, 'ShedWidth', 12));
sl_line(mdl, 'Load_CPL/1', 'iload_PS/1');
sl_line(mdl, 'DAB_Loss_Model/1', 'iloss_PS/1');

% ---- 조정형 Stage C와 48 V(TB16과 같음, 벅 전류 태그만 iLb) ---------------------------------------------------
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_in', [1520 150 1570 190]);
build_stageC_reg(mdl, 'StageC_Regulated', [1620 140 1920 420], 'TB', struct('iLTag', 'iLb'));
sl_add(mdl, gref, 'GND_C', [1620 450 1660 480]);
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_o', [1980 230 2020 290], 'Orientation', 'down');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_bat', [2060 150 2110 190]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_bat', [2140 160 2200 180], 'R', 'TB.Rbat');
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bat48', [2230 230 2270 290], 'Orientation', 'down', 'v0', 'TB.OCV');
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load48', [2320 230 2360 290], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iload48_PS', [2330 190 2360 210]);
sl_pc(mdl, 'C_bus', 'p', 'I_in', 'p');               % Stage C 입력전류 + : 버스 → Stage C
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
sl_meas(mdl, 'I_in',  'I', 'iin',  [1520 520]);
sl_meas(mdl, 'V_o',   'V', 'vo',   [1980 520]);
sl_meas(mdl, 'I_bat', 'I', 'ibat', [2140 520]);
sl_note(mdl, sprintf('48 V 전원망(절연측): 정전력 부하 %.0f W = Stage C 입력 5 kW(E17 P_C), 배터리 가지 1 MΩ(없음)', TBb.P48), ...
    [1960 110 2420 130]);

% 48 V 정전력 부하 전류 = P48/max(v_o, 10 V)
ld = [mdl '/Load_48V'];
add_block('built-in/Subsystem', ld, 'Position', [2310 40 2430 100], 'BackgroundColor', 'lightBlue');
sl_add(ld, 'simulink/Sources/Constant', 'P48', [30 30 90 50], 'Value', 'TB.P48');
sl_add(ld, 'simulink/Signal Routing/Goto', 'p48', [130 0 210 20], 'GotoTag', 'p48', 'TagVisibility', 'global');
sl_add(ld, 'simulink/Signal Routing/From', 'vo_from', [30 110 110 130], 'GotoTag', 'vo');
sl_add(ld, 'simulink/Signal Routing/From', 't_from', [30 150 110 170], 'GotoTag', 't');
sl_startup_guard(ld, 'Guard_vo', [150 105 190 175], 'TB.x0(3)', 'TB', [120 190 190 210]);
sl_add(ld, 'simulink/Discrete/Unit Delay', 'vo_z1', [220 125 250 155], 'SampleTime', 'TB.dt');
sl_add(ld, 'simulink/Sources/Constant', 'v_min', [220 190 280 210], 'Value', 'TB.vmin_cpl');
sl_add(ld, 'simulink/Math Operations/MinMax', 'v_floor', [310 130 340 180], 'Function', 'max', 'Inputs', '2');
sl_add(ld, 'simulink/Math Operations/Divide', 'P_over_v', [380 50 420 150]);
sl_add(ld, 'simulink/Signal Routing/Goto', 'iload', [460 140 540 160], 'GotoTag', 'iload', 'TagVisibility', 'global');
add_block('simulink/Sinks/Out1', [ld '/i_load48'], 'Position', [470 90 500 110]);
sl_line(ld, 'P48/1', 'p48/1');
sl_line(ld, 'P48/1', 'P_over_v/1');
sl_line(ld, 'vo_from/1', 'Guard_vo/1');
sl_line(ld, 't_from/1', 'Guard_vo/2');
sl_line(ld, 'Guard_vo/1', 'vo_z1/1');
sl_line(ld, 'vo_z1/1', 'v_floor/1');
sl_line(ld, 'v_min/1', 'v_floor/2');
sl_line(ld, 'v_floor/1', 'P_over_v/2');
sl_line(ld, 'P_over_v/1', 'iload/1');
sl_line(ld, 'P_over_v/1', 'i_load48/1');
sl_note(ld, sprintf('48 V 정전력 부하(시험 장치): i = P48/max(v_o, 10 V). v_o는 시작 표본 보호 후 한 간격 지연(대수 루프 방지)'), ...
    [30 240 560 260]);
sl_line(mdl, 'Load_48V/1', 'iload48_PS/1');

% ---- 제어·게이트 -----------------------------------------------------------------------------------
yc = 600;
build_stageA_gate_zcp(mdl, [120 yc 300 yc+80], 'TB', [1 2]);
build_stageB_control(mdl, [480 yc 660 yc+80], [760 yc 940 yc+80], 'TB', struct('r2d', true));   % TB13과 같음(게이트 prism_gate_stageB_f.m)

cs = [mdl '/Controller_StageC'];
add_block('built-in/Subsystem', cs, 'Position', [1620 yc 1800 yc+80], 'BackgroundColor', 'yellow');
sl_add(cs, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', 'TB.dt');
tg = {'vbus', 'iLb', 'vI', 'vo', 'iload', 'ibat'};
for k = 1:6
    sl_add(cs, 'simulink/Signal Routing/From', ['from_' tg{k}], [30 70+30*(k-1) 110 90+30*(k-1)], 'GotoTag', tg{k});
end
sl_add(cs, 'simulink/Signal Routing/Mux', 'meas_mux', [140 65 145 245], 'Inputs', '6');
for k = 1:6, sl_line(cs, sprintf('from_%s/1', tg{k}), sprintf('meas_mux/%d', k)); end
sl_add(cs, 'simulink/Discrete/Unit Delay', 'meas_z1', [170 140 200 170], 'SampleTime', 'TB.dt', 'InitialCondition', 'TB.measC0');
sl_line(cs, 'meas_mux/1', 'meas_z1/1');
sl_startup_guard(cs, 'Startup_guard', [230 130 270 210], 'TB.measC0', 'TB', [150 250 240 270]);
sl_line(cs, 'meas_z1/1', 'Startup_guard/1');
sl_line(cs, 'Clock/1', 'Startup_guard/2');
sl_add(cs, 'simulink/Sources/Constant', 'ctl_prm', [30 290 130 310], 'Value', 'TB.ctl_prm_C');
sl_mfunc(cs, 'StageC_Controller', [310 40 470 260], 'prism_stageC_reg_ctrl.m');
sl_line(cs, 'Clock/1', 'StageC_Controller/1');
sl_line(cs, 'Startup_guard/1', 'StageC_Controller/2');
sl_line(cs, 'ctl_prm/1', 'StageC_Controller/3');
sl_add(cs, 'simulink/Signal Routing/Goto', 'uc', [510 140 580 160], 'GotoTag', 'ucC', 'TagVisibility', 'global');
sl_line(cs, 'StageC_Controller/1', 'uc/1');
sl_note(cs, sprintf(['조정형 Stage C 제어기(검증 코드 E22 control과 같은 알고리즘·게인, 표본 10 µs, 계산 지연 1주기, TB15·TB16과 같음)\n' ...
    '입력 v_bus는 실제 버스(창 조정 중 460 V, 강등 뒤 V_A − 경로 강하). 벅 전류 태그 iLb(Stage B의 iL과 구분)']), ...
    [30 330 760 380], 'box');

gs = [mdl '/Gate_StageC'];
add_block('built-in/Subsystem', gs, 'Position', [1880 yc 2060 yc+80], 'BackgroundColor', 'yellow');
sl_add(gs, 'simulink/Sources/Digital Clock', 'Clock', [30 30 80 60], 'SampleTime', 'TB.dt');
sl_add(gs, 'simulink/Signal Routing/From', 'uc_from', [30 80 110 100], 'GotoTag', 'ucC');
sl_add(gs, 'simulink/Signal Routing/Selector', 'u_sel', [130 80 150 100], 'IndexParamArray', {'[1 2]'}, 'InputPortWidth', '4');
sl_add(gs, 'simulink/Sources/Constant', 'gate_prm', [30 130 130 150], 'Value', 'TB.gate_prm_C');
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
sl_note(gs, sprintf(['게이트: 벅 100 kHz 중앙 정렬 PWM(데드타임 50 ns) + CLLC 250 kHz 공진점(TB15·TB16과 같음).\n' ...
    'CLLC 데드타임: 1차가 보낼 때 %.0f ns, 2차가 보낼 때 %.0f ns. |P*| < %.0f W: 두 브리지 같은 위상(2차 %.0f ns).'], ...
    1e9*TBb.gate_prm_C(5), 1e9*TBb.gate_prm_C(6), TBb.P_in, 1e9*TBb.gate_prm_C(7)), [30 360 760 400], 'box');
sl_note(mdl, sprintf(['제어부: Gate_StageA(영교차 추종, TB06·TB16과 같음) · Controller_StageB(보호 상태기계 R2_Supervisor + 채택 제어기)\n' ...
    '→ Gate_StageB(게이트 생성기 + DAB 고장 모드 변조(EPS) → 보호 게이트 재정의, TB13과 같음) · Controller_StageC → Gate_StageC(TB15·TB16과 같음)']), ...
    [120 yc+100 1800 yc+130]);

% ---- 계측부 ---------------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [2500 140 2620 420], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_StageA', {'iA_P1', 'iA_P2', 'vA'}; ...
     'Scope_Bus', {'vbus', 'p_load', 'iin'}; ...
     'Scope_StageB', {'ip', 'ih', 'ibyp', 'vs'}; ...
     'Scope_Link', {'vlink', 'ilink', 'ibrk', 'iL'}; ...
     'Scope_State', {'r2_sup'}; ...
     'Scope_48V', {'vo', 'ix', 'iLb'}; ...
     'Scope_CLLC', {'ir2', 'vleg1', 'vlegs1'}; ...
     'Scope_Controller', {'ctrl_dg', 'uc', 'ucC'}}, ...
    {'t', 't', '2', ''; 'vbus', 'vbus', '2', 'single'; 'ip', 'ip', '2', 'single'; 'ih', 'ih', '2', 'single'; ...
     'vs', 'vs', '2', 'single'; 'vlink', 'vlink', '2', 'single'; 'ilink', 'ilink', '2', 'single'; 'ibyp', 'ibyp', '2', 'single'; ...
     'ibrk', 'ibrk', '2', 'single'; 'iL', 'iL', '2', 'single'; ...
     'ctrl_dg', 'dg', 'TB.Np', ''; 'uc', 'uc', 'TB.Np', ''; 'r2_sup', 'sup', 'TB.Np', ''; 'r2_flags', 'flags', 'TB.Np', ''; ...
     'iA_P1', 'iA1', '', 'single'; 'iA_P2', 'iA2', '', 'single'; 'stA_P1', 'st1', '', 'int8'; 'stA_P2', 'st2', '', 'int8'; ...
     't', 't4', '4', ''; 'vA', 'vA', '4', 'single'; 'iAo', 'iAo', '4', 'single'; 'iin', 'iin', '4', 'single'; ...
     'iLb', 'iLb', '4', 'single'; 'vI', 'vI', '4', 'single'; 'vo', 'vo', '4', 'single'; 'ix', 'ix', '4', 'single'; ...
     'iload', 'iload', '4', 'single'; 'ir2', 'ir2', '4', 'single'; 'vleg1', 'vleg1', '4', 'single'; 'vlegs1', 'vlegs1', '4', 'single'; ...
     'gC_Q1', 'gq1', '4', 'int8'; 'gC_Q2', 'gq2', '4', 'int8'; 'gC_S1', 'gs1', '4', 'int8'; 'gC_S2', 'gs2', '4', 'int8'; ...
     'ucC', 'ucC', '4000', ''});
sl_note(mdl, sprintf(['계측: Scope 8개(Stage A, 버스, Stage B 전류, 링크·제동, 상태기계, 48 V, CLLC, 제어기)\n' ...
    '+ To Workspace(판정용): Stage A 위상 전류·구간 2.5 ns, Stage B 5 ns, Stage C 10 ns, 상태기계·제어 5 µs, Stage C 제어 10 µs\n' ...
    '(18 ms 모의의 메모리를 줄이려고 아날로그는 single, 게이트·구간은 int8로 저장)']), [2440 440 2900 490]);

sl_note(mdl, sprintf(['파라미터(TB17_init.m ← ref/TB17_<사례>_init.json = 검증 코드 E23 degrade(E17 + E22), Stage A는 prism_hub_params = E1 설계값)\n' ...
    'Stage A: C_fly 7.8125 µF, L_r 144.1 nH(f_r0 150 kHz), 영교차 검출 0.5 A·지연 20 ns, C_A 400 µF(TB16과 같음)\n' ...
    'Stage B·상태기계·보호·EPS 지령표: TB13과 같음(설계 상한 1.387 × 정격점, 400 V 부하 분리·감발 3 ms). 고장 시각 1.5 ms(TB13 0.5 ms)\n' ...
    'Stage C: 벅 204 µH·100 kHz, CLLC 4.8:1·L_m %.1f µH·250 kHz, C_o 2.2 mF(TB15·TB16과 같음), 48 V 부하 %.0f W\n' ...
    '해석기: Simscape 지역 해석기 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회), Stage B 제어 5 µs(전달지연 5 µs), Stage C 제어 10 µs'], ...
    1e6*TBb.C.Lm, TBb.P48), [30 yc+160 1800 yc+250], 'box');
sl_note(mdl, sprintf(['검증 목적: R2-W460 창 조정 모듈의 H-브리지 개방 강등(TB13)은 Stage A를 이상 전압원, Stage C 몫을 정전력 등가로 두고 확인했다.\n' ...
    '실제 Stage A(공진 스위치드 커패시터, 영교차 추종)와 조정형 Stage C를 넣어 (1) 강등 순서와 회로 한계가 그대로인가, (2) 버스가 460 V → 클램프 → 붕괴\n' ...
    '→ V_A로 움직이는 동안 48 V가 ±2 % 안에 유지되는가, (3) Stage A가 전류 급변(약 50 A → 수 A → 강등 뒤 부하)에서 영전류 스위칭을 유지하는가를 본다.\n' ...
    '사례: A 1008 V(V_A 504 V, 강등 뒤 Stage C만), B 930 V(V_A 465 V, 강등 0.5 ms 뒤 400 V 부하 되돌림). 기준: E23 degrade(E17 + E22), E1']), ...
    [30 yc+260 1800 yc+330], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
if ~exist(fullfile(here, 'results'), 'dir'), mkdir(fullfile(here, 'results')); end
sl_export_png({mdl, [mdl '/StageA_Module1'], [mdl '/StageB_Regulator'], [mdl '/StageC_Regulated'], [mdl '/Controller_StageB'], ...
    [mdl '/Gate_StageB'], [mdl '/Controller_StageC'], [mdl '/Load_48V']}, fullfile(here, 'results'));
end
