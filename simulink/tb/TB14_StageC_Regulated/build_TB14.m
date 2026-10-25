function build_TB14()
%BUILD_TB14  TB14 테스트벤치 모델(TB14_StageC_Regulated.slx)을 처음부터 만든다.
%
%   R2 기본형의 조정형 Stage C 5 kW(검증 코드 E22): 넓은 입력(270–504 V)에서 48 V 전원망을 조정하고 배터리 충전·회생을
%   다루는 동기 벅 + CLLC 직류변압기를 소자 수준 회로로 확인한다.
%   구성
%     V_bus(제어 전압원, 시험 조건 지령) ── 입력전류 센서 ── StageC_Regulated(벅 → C_I → CLLC 4.8:1 → C_o) ──┬── 48 V 배터리(OCV + R_b, 선택)
%                                                                                                       └── 정전력 부하(제어 전류원, P/v_o)
%     Test_Conditions: 버스 전압 지령·부하 전력(구간 선형, ctrl/prism_tb14_profile.m), 정전력 부하 전류
%     Controller_StageC: 측정 6개(시작 표본 보호, 한 간격 지연) → ctrl/prism_stageC_reg_ctrl.m(10 µs 표본)
%     Gate_StageC: ctrl/prism_gate_stageC_reg.m → 게이트 10개(gS_BH, gS_BL, gC_Q1–Q4, gC_S1–S4)
%   실행: prism_run('build_TB14')  →  prism_run('run_TB14')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB14_StageC_Regulated';
evalin('base', 'clear TB14_case');
run(fullfile(here, 'TB14_init.m'));
sl_model_new(mdl, 'TB14_init.m');

sl_note(mdl, 'TB14 — 조정형 Stage C 5 kW(R2 기본형): 동기 벅 + CLLC 직류변압기, 입력 270–504 V → 48 V 전원망(배터리·회생)', [30 10 1300 40], 'title');

% ---- 전력 회로 ----------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
sl_add(mdl, [fl 'Electrical Sources/Controlled Voltage Source'], 'V_bus', [70 230 110 290], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'vbus_PS', [20 180 50 200]);
sl_add(mdl, [fl 'Electrical Elements/Electrical Reference'], 'GND', [70 440 110 470]);
sl_solver(mdl, 'Solver', [10 360 50 390], 'GND', 'V', 3);   % 고정 비용(모드 반복 3회): 가변 비용 대비 결과는 results/solver_probe
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_in', [160 150 210 190]);
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_bus_meas', [150 240 190 300], 'Orientation', 'down');
build_stageC_reg(mdl, 'StageC_Regulated', [300 140 600 420], 'TB');
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_o', [700 240 740 300], 'Orientation', 'down');
% 48 V 배터리(OCV + R_b), 전류 + = 충전
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_bat', [800 150 850 190]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_bat', [880 160 940 180], 'R', 'TB.Rbat');
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bat48', [970 230 1010 290], 'Orientation', 'down', 'v0', 'TB.OCV');
% 정전력 부하
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load', [1080 240 1120 300], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iload_PS', [1090 200 1120 220]);

sl_pc(mdl, 'vbus_PS', 'output', 'V_bus', 'vT');
sl_pc(mdl, 'V_bus', 'n', 'GND', 'V');
sl_pc(mdl, 'V_bus', 'p', 'I_in', 'p');                      % 입력전류 + : 버스 → Stage C
sl_pc(mdl, 'I_in', 'n', 'StageC_Regulated', 'DC_P');
sl_pc(mdl, 'StageC_Regulated', 'DC_N', 'GND', 'V');
sl_pc(mdl, 'V_bus_meas', 'p', 'I_in', 'n');
sl_pc(mdl, 'V_bus_meas', 'n', 'GND', 'V');
sl_pc(mdl, 'V_o', 'p', 'StageC_Regulated', 'VO_P');
sl_pc(mdl, 'V_o', 'n', 'StageC_Regulated', 'VO_N');
sl_pc(mdl, 'I_bat', 'p', 'StageC_Regulated', 'VO_P');
sl_pc(mdl, 'I_bat', 'n', 'R_bat', 'p');
sl_pc(mdl, 'R_bat', 'n', 'V_bat48', 'p');
sl_pc(mdl, 'V_bat48', 'n', 'StageC_Regulated', 'VO_N');
sl_pc(mdl, 'I_load', 'tail', 'StageC_Regulated', 'VO_P');  % 부하전류: VO_P → 전류원 → VO_N
sl_pc(mdl, 'I_load', 'head', 'StageC_Regulated', 'VO_N');
sl_pc(mdl, 'iload_PS', 'output', 'I_load', 'iT');
sl_meas(mdl, 'V_bus_meas', 'V', 'vbus', [90 520]);
sl_meas(mdl, 'I_in', 'I', 'iin', [320 520]);
sl_meas(mdl, 'V_o', 'V', 'vo', [660 520]);
sl_meas(mdl, 'I_bat', 'I', 'ibat', [900 520]);
sl_note(mdl, sprintf('보조버스 V_A(이상 제어 전압원)\n시험 조건의 버스 지령을 따른다'), [20 310 230 340]);
sl_note(mdl, sprintf('48 V 전원망(절연측): C_o는 Stage C 안,\n배터리 OCV + R_b(없는 사례는 R_b = 1 MΩ), 정전력 부하 P/v_o'), [760 320 1180 350]);

% ---- 시험 조건: 버스 지령, 부하 전력, 정전력 부하 전류 --------------------------------------------------------
ts = [mdl '/Test_Conditions'];
add_block('built-in/Subsystem', ts, 'Position', [1080 60 1220 120], 'BackgroundColor', 'lightBlue');
sl_add(ts, 'simulink/Sources/Digital Clock', 'Clock', [30 40 80 70], 'SampleTime', 'TB.dt');
sl_add(ts, 'simulink/Sources/Constant', 'prof', [30 100 130 120], 'Value', 'TB.prof');
sl_mfunc(ts, 'Profile', [180 40 300 130], 'prism_tb14_profile.m');
sl_line(ts, 'Clock/1', 'Profile/1');
sl_line(ts, 'prof/1', 'Profile/2');
sl_add(ts, 'simulink/Signal Routing/Demux', 'split', [330 40 335 130], 'Outputs', '2');
sl_line(ts, 'Profile/1', 'split/1');
sl_add(ts, 'simulink/Signal Routing/Goto', 'vbus_cmd', [380 30 460 50], 'GotoTag', 'vbus_cmd', 'TagVisibility', 'global');
sl_add(ts, 'simulink/Signal Routing/Goto', 'p_load', [380 120 460 140], 'GotoTag', 'p_load', 'TagVisibility', 'global');
sl_line(ts, 'split/1', 'vbus_cmd/1');
sl_line(ts, 'split/2', 'p_load/1');
sl_add(ts, 'simulink/Signal Routing/From', 'vo_from', [30 180 110 200], 'GotoTag', 'vo');
sl_add(ts, 'simulink/Signal Routing/From', 't_from', [30 220 110 240], 'GotoTag', 't14');
sl_add(ts, 'simulink/Signal Routing/Goto', 't14', [120 75 160 95], 'GotoTag', 't14', 'TagVisibility', 'global');
sl_line(ts, 'Clock/1', 't14/1');
sl_startup_guard(ts, 'Startup_guard', [150 175 190 245], 'TB.x0(3)', 'TB', [120 260 190 280]);
sl_line(ts, 'vo_from/1', 'Startup_guard/1');
sl_line(ts, 't_from/1', 'Startup_guard/2');
sl_add(ts, 'simulink/Discrete/Unit Delay', 'vo_z1', [220 195 250 225], 'SampleTime', 'TB.dt');
sl_add(ts, 'simulink/Sources/Constant', 'v_min', [220 250 280 270], 'Value', 'TB.vmin_cpl');
sl_add(ts, 'simulink/Math Operations/MinMax', 'v_floor', [310 200 340 250], 'Function', 'max', 'Inputs', '2');
sl_add(ts, 'simulink/Math Operations/Divide', 'P_over_v', [380 150 420 230]);
sl_add(ts, 'simulink/Signal Routing/Goto', 'iload', [460 180 540 200], 'GotoTag', 'iload', 'TagVisibility', 'global');
add_block('simulink/Sinks/Out1', [ts '/i_load'], 'Position', [470 230 500 250]);
add_block('simulink/Sinks/Out1', [ts '/v_bus_cmd'], 'Position', [470 60 500 80]);
sl_line(ts, 'Startup_guard/1', 'vo_z1/1');
sl_line(ts, 'vo_z1/1', 'v_floor/1');
sl_line(ts, 'v_min/1', 'v_floor/2');
sl_line(ts, 'split/2', 'P_over_v/1');
sl_line(ts, 'v_floor/1', 'P_over_v/2');
sl_line(ts, 'P_over_v/1', 'iload/1');
sl_line(ts, 'P_over_v/1', 'i_load/1');
sl_line(ts, 'split/1', 'v_bus_cmd/1');
sl_note(ts, sprintf(['시험 조건(제어기 밖의 시험 장치): 버스 지령 v_bus(t)와 48 V 부하 전력 P(t)는 구간 선형(TB.prof).\n' ...
    '정전력 부하 전류 i = P/max(v_o, 10 V), v_o는 시작 표본 보호 후 한 간격 지연(회로–Simulink 대수 루프 방지).']), [30 300 640 340], 'box');
sl_line(mdl, 'Test_Conditions/1', 'iload_PS/1');
sl_line(mdl, 'Test_Conditions/2', 'vbus_PS/1');

% ---- 제어부 ----------------------------------------------------------------------------------------
cs = [mdl '/Controller_StageC'];
add_block('built-in/Subsystem', cs, 'Position', [300 600 480 680], 'BackgroundColor', 'yellow');
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
sl_note(cs, sprintf(['조정형 Stage C 제어기(검증 코드 E22 control과 같은 알고리즘·게인, 표본 10 µs, 계산 지연 1주기)\n' ...
    '출력전류 지령 = min(48 V 전압 PI + 부하전류 앞먹임, 충전전류 루프, 과도 130 A → 2 ms 뒤 105 A) → 인덕터 전류 PI → 듀티\n' ...
    '출력: [d; 보내는 쪽(+1 1차, −1 2차); i_L 지령; 선택]']), [30 330 700 380], 'box');

gs = [mdl '/Gate_StageC'];
add_block('built-in/Subsystem', gs, 'Position', [560 600 740 680], 'BackgroundColor', 'yellow');
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
TBb = evalin('base', 'TB');
sl_note(gs, sprintf(['게이트: 벅 100 kHz 중앙 정렬 PWM(데드타임 50 ns, 골에서 제어 표본) + CLLC 250 kHz 공진점.\n' ...
    'CLLC 데드타임은 보내는 쪽별: 1차가 보낼 때 %.0f ns, 2차가 보낼 때 %.0f ns(E22 zvs, 레그 출력용량 모델의 통과 창 가운데).\n' ...
    'CLLC는 보내는 쪽 브리지만 스위칭(제어기 출력, 주기 시작에서만 바꿈), 받는 쪽은 꺼 두고 다이오드 정류.'], ...
    1e9*TBb.gate_prm(5), 1e9*TBb.gate_prm(6)), [30 360 700 410], 'box');
sl_note(mdl, sprintf('제어부: Controller_StageC → Gate_StageC → 전역 태그 gS_BH·gS_BL(벅), gC_Q1–Q4(1차), gC_S1–S4(2차)'), [300 690 1000 710]);

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [1280 140 1400 420], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_48V', {'vo', 'ix', 'ibat'}; ...
     'Scope_Buck', {'vbus', 'iL', 'vI'}; ...
     'Scope_CLLC', {'ir1', 'im', 'ir2'}; ...
     'Scope_Legs', {'vleg1', 'vlegs1', 'vswb'}; ...
     'Scope_Controller', {'ucC'}}, ...
    {'t14', 't', '4'; 'vbus', 'vbus', '4'; 'iin', 'iin', '4'; 'iL', 'iL', '4'; 'vI', 'vI', '4'; 'vo', 'vo', '4'; 'ix', 'ix', '4'; ...
     'ibat', 'ibat', '4'; 'iload', 'iload', '4'; 'ir1', 'ir1', '4'; 'im', 'im', '4'; 'ir2', 'ir2', '4'; 'vleg1', 'vleg1', '4'; ...
     'vlegs1', 'vlegs1', '4'; 'gC_Q1', 'gq1', '4'; 'gC_Q2', 'gq2', '4'; 'gC_S1', 'gs1', '4'; 'gC_S2', 'gs2', '4'; ...
     'ucC', 'uc', '4000'});
sl_note(mdl, sprintf('계측: Scope 5개(48 V, 벅, CLLC 공진, 레그 노드, 제어기)\n+ To Workspace(10 ns 간격, 제어기 출력 10 µs)'), [1260 445 1560 475]);

sl_note(mdl, sprintf(['파라미터(TB14_init.m ← ref/TB14_<사례>_init.json = 검증 코드 E22): 벅 L_b 204 µH(DCR 15 mΩ), C_I 20 µF, 100 kHz;\n' ...
    'CLLC n 4.8, L_r 2.19 µH, C_r 184.9 nF, L_m %.1f µH(E22 zvs), 250 kHz, 데드타임 1차 %.0f ns·2차 %.0f ns; C_o 2.2 mF;\n' ...
    '소자 650 V GaN 2병렬(벅·1차), 150 V GaN 2병렬(2차). 해석기: Simscape 지역 해석기 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회), 제어 표본 10 µs'], ...
    1e6*TBb.C.Lm, 1e9*TBb.gate_prm(5), 1e9*TBb.gate_prm(6)), [30 760 1300 830], 'box');
sl_note(mdl, sprintf(['검증 목적: R2 기본형에서 400 V 버스는 V_A(270–504 V)를 그대로 따르므로 48 V는 Stage C가 조정해야 한다. 평균모델(E22)에서 정한\n' ...
    '동기 벅 + 공진점 CLLC 직류변압기와 제어가 소자 수준 회로에서도 48 V를 지키는지, CLLC가 양방향에서 ZVS·이득 1을 유지하는지 확인한다.\n' ...
    '사례: A 400 V 4 kW/ms 부하 증가, B 270 V 0.1 → 5 kW 계단, C 504 V 5 → −3 kW 계단(회생), D 버스 454 → 504 V 계단, E 배터리 연결 0.1 → 5 kW 계단,\n' ...
    'F 400 V −3 → −0.3 kW, G 270 V −3 → −0.1 kW(역방향 경부하: E22 gain에서 찾은 DCX 이득 상승을 회로에서 확인)']), ...
    [30 840 1300 915], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
sl_export_png({mdl, [mdl '/StageC_Regulated'], [mdl '/Controller_StageC'], [mdl '/Gate_StageC'], [mdl '/Test_Conditions']}, ...
    fullfile(here, 'results'));
end
