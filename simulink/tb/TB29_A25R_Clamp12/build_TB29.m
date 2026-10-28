function build_TB29()
%BUILD_TB29  TB29 테스트벤치 모델(TB29_A25R_Clamp12.slx)을 처음부터 만든다.
%
%   TB28 회로와 같다(클램프 저항 값만 ref의 1.2 Ω, E37 Q2). TB28 설명: TB21(충전 중 R2 기본형: 충전 중 정지·V_A 클램프)의 Stage A를 설계 A25R(25 kHz, 스위치 셀 출력용량, C_A 2.4 mF)로 바꾸고,
%   게이트를 A25R 게이트(ctrl/prism_gate_stageA_zcpf.m: 모듈 관리기·셰딩·모듈 고장 처리, 충전 요청 chg_req, 위상 동작 여부 en_A)로 바꿨다.
%   충전 중 R2 기본형: 배터리 ← Stage A 4모듈(8위상, 역방향) ← V_A 노드 ← 400–500 V급 충전기(전류원)
%                                                       V_A → 배선 → 400 V 버스(감쇠기, 정전력 부하) → 조정형 Stage C → 48 V
%   구성
%     V_bat ── StageA_Module1–4(A25, VIN·GND·VOUT 병렬) ── I_Aout ── V_A 노드(C_A 2.4 mF)
%       ∥ Charger(제어 전류원)  ∥ Clamp_VA(R_clamp 1.2 Ω + 스위치 셀, I_clamp)
%       ── R_path 3 mΩ ── L_path 1.5 µH ── I_path ── 버스(C_bus 400 µF, R_dmp–C_dmp, I_load400) ── I_in ── StageC_Regulated ── 48 V
%     Test_Conditions(prism_tb28_profile): 충전기 전류, 400 V·48 V 부하 전력, Stage A 위상 동작 여부(사건 = 게이트 차단), 충전 요청
%     Gate_StageA(A25R: 영교차 추종 + 모듈 관리기·셰딩·모듈 고장 처리, 동작 여부 en_A, 충전 요청 chg_req) · Clamp_Control(prism_va_clamp)
%     · Controller_StageC → Gate_StageC
%   실행: prism_run('build_TB29')  →  prism_run('smoke_TB29')  →  prism_run('run_TB29')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB29_A25R_Clamp12';
evalin('base', 'clear TB29_case TB29_tend');
run(fullfile(here, 'TB29_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');
sl_model_new(mdl, 'TB29_init.m');
TBb = evalin('base', 'TB');

sl_note(mdl, 'TB29 — TB28 회로(A25R 충전 중 정지)의 V_A 클램프 저항을 1.2 Ω로(부품 정격 2차 E37: 클램프 스위치 온도·전류 대책)', ...
    [30 10 1700 40], 'title');
sl_note(mdl, sprintf(['검증 목적: 부품 정격 2차(E37)에서 V_A 클램프 스위치(1200 V IGBT 모듈)의 전류·온도를 맞추려고 클램프 저항을 1 → 1.2 Ω로 바꿨다\n' ...
    '(468 V에서 390 A, 충전기 375 A보다 커야 함). 모델(E26 사건 32개)에서는 V_A ≤ 470 V였다. 같은 TB28 회로에서 클램프 동작, 48 V, Stage A를 다시 확인한다.\n' ...
    '사례: A 920 V 경로 상실(충전기 3 ms 유지), B 640 V 경로 상실(충전기 3 ms 유지, E37에서 IGBT 온도가 가장 높았던 사건과 같은 팩·부하)']), ...
    [30 50 1700 150], 'box');

% ---- 전력 회로 -------------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
gref = [fl 'Electrical Elements/Electrical Reference'];
y0 = 200;
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bat', [60 y0+80 100 y0+140], 'Orientation', 'down', 'v0', 'TB.vbat');
sl_add(mdl, gref, 'GND', [60 y0+200 100 y0+230]);
sl_solver(mdl, 'Solver', [10 y0+150 50 y0+180], 'GND', 'V', 3);   % 고정 비용(모드 반복 3회)
for m = 1:4                                                  % Stage A 4모듈(위상 2m−1, 2m), 세로로 배치
    ym = y0 + 20 + 230*(m - 1);
    build_stageA_module(mdl, sprintf('StageA_Module%d', m), [160 ym 320 ym+200], m, 'TB.A', 'TB.A.Coss');
end
for k = 1:8                                                  % (TB24) 위상별 C_fly 초기 전압
    set_param(sprintf('%s/StageA_Module%d/StageA_Phase%d/C_fly', mdl, ceil(k/2), k), 'vc', sprintf('TB.vC0_ph(%d)', k));
end
sl_add(mdl, gref, 'GND_A', [200 y0+950 240 y0+980]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_Aout', [370 y0+5 420 y0+45]);
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_A', [460 y0+80 500 y0+140], 'Orientation', 'down', ...
    'c', 'TB.A.CA', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vA0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_CA', [460 y0+200 500 y0+230]);
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_A', [530 y0+80 570 y0+140], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_VA', [530 y0+200 570 y0+230]);
% 충전기(제어 전류원): GND → 전류원 → V_A 노드(주입)
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'Charger', [460 y0+330 500 y0+390], 'Orientation', 'up');
sl_add(mdl, gref, 'GND_chg', [460 y0+430 500 y0+460]);
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'ich_PS', [530 y0+350 560 y0+370], 'Orientation', 'left');
% V_A 클램프: V_A → R_clamp → I_clamp → 스위치 셀(D → S) → GND
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_clamp', [620 y0+300 660 y0+340], 'Orientation', 'down', 'R', 'TB.Rclamp');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_clamp', [620 y0+360 660 y0+400], 'Orientation', 'down');
sl_switch_cell(mdl, 'S_clamp', [610 y0+420 670 y0+480], struct('tag', 'g_clamp', 'label', 'S_clamp', 'Ron', '1e-3', ...
    'Goff', '1e-8', 'Vf', '2', 'Rd', '1e-3', 'Goffd', '1e-8', 'Coss', '', 'orient', 'down'));
sl_add(mdl, gref, 'GND_cl', [620 y0+510 660 y0+540]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_path', [700 y0+15 750 y0+35], 'R', 'TB.Rpath');
sl_add(mdl, [fl 'Electrical Elements/Inductor'], 'L_path', [780 y0+15 830 y0+35], 'l', 'TB.Lpath', 'r', '0', ...
    'i_L_specify', 'on', 'i_L', 'TB.iw0', 'i_L_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_path', [860 y0+5 910 y0+45]);
% 400 V 버스
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_bus', [960 y0+80 1000 y0+140], 'Orientation', 'down', ...
    'c', 'TB.Cb', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vb0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_Cb', [960 y0+200 1000 y0+230]);
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_bus', [1030 y0+80 1070 y0+140], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_Vb', [1030 y0+200 1070 y0+230]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_dmp', [1100 y0+70 1140 y0+110], 'Orientation', 'down', 'R', 'TB.Rdmp');
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_dmp', [1100 y0+130 1140 y0+170], 'Orientation', 'down', ...
    'c', 'TB.Cdmp', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vb0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_dmp', [1100 y0+200 1140 y0+230]);
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load400', [1180 y0+80 1220 y0+140], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iload400_PS', [1190 y0+40 1220 y0+60]);
sl_add(mdl, gref, 'GND_load', [1180 y0+200 1220 y0+230]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_in', [1260 y0+5 1310 y0+45]);
build_stageC_reg(mdl, 'StageC_Regulated', [1360 y0 1660 y0+280], 'TB');
sl_add(mdl, gref, 'GND_C', [1360 y0+310 1400 y0+340]);
% 48 V 쪽(정전력 부하, 배터리 가지 1 MΩ = 없음)
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_o', [1720 y0+80 1760 y0+140], 'Orientation', 'down');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_bat', [1800 y0+5 1850 y0+45]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_bat', [1880 y0+15 1940 y0+35], 'R', 'TB.Rbat');
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bat48', [1970 y0+80 2010 y0+140], 'Orientation', 'down', 'v0', 'TB.OCV');
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load48', [2060 y0+80 2100 y0+140], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iload48_PS', [2070 y0+40 2100 y0+60]);

sl_pc(mdl, 'V_bat', 'n', 'GND', 'V');
for m = 1:4                                                  % 4모듈 병렬: VIN = 배터리 +, GND = 배터리 −, VOUT = V_A
    mn = sprintf('StageA_Module%d', m);
    sl_pc(mdl, 'V_bat', 'p', mn, 'VIN');
    sl_pc(mdl, mn, 'GND', 'GND_A', 'V');
    sl_pc(mdl, mn, 'VOUT', 'I_Aout', 'p');                   % Stage A 출력전류(4모듈 합): 모듈 → V_A(충전 중 음수)
end
sl_pc(mdl, 'I_Aout', 'n', 'C_A', 'p');
sl_pc(mdl, 'C_A', 'n', 'GND_CA', 'V');
sl_pc(mdl, 'V_A', 'p', 'C_A', 'p');
sl_pc(mdl, 'V_A', 'n', 'GND_VA', 'V');
sl_pc(mdl, 'Charger', 'tail', 'GND_chg', 'V');
sl_pc(mdl, 'Charger', 'head', 'C_A', 'p');
sl_pc(mdl, 'ich_PS', 'output', 'Charger', 'iT');
sl_pc(mdl, 'R_clamp', 'p', 'C_A', 'p');
sl_pc(mdl, 'R_clamp', 'n', 'I_clamp', 'p');                  % 클램프 전류 + : V_A → R → 스위치 → GND
sl_pc(mdl, 'I_clamp', 'n', 'S_clamp', 'D');
sl_pc(mdl, 'S_clamp', 'S', 'GND_cl', 'V');
sl_pc(mdl, 'C_A', 'p', 'R_path', 'p');
sl_pc(mdl, 'R_path', 'n', 'L_path', 'p');
sl_pc(mdl, 'L_path', 'n', 'I_path', 'p');
sl_pc(mdl, 'I_path', 'n', 'C_bus', 'p');
sl_pc(mdl, 'C_bus', 'n', 'GND_Cb', 'V');
sl_pc(mdl, 'V_bus', 'p', 'C_bus', 'p');
sl_pc(mdl, 'V_bus', 'n', 'GND_Vb', 'V');
sl_pc(mdl, 'R_dmp', 'p', 'C_bus', 'p');
sl_pc(mdl, 'R_dmp', 'n', 'C_dmp', 'p');
sl_pc(mdl, 'C_dmp', 'n', 'GND_dmp', 'V');
sl_pc(mdl, 'I_load400', 'tail', 'C_bus', 'p');
sl_pc(mdl, 'I_load400', 'head', 'GND_load', 'V');
sl_pc(mdl, 'iload400_PS', 'output', 'I_load400', 'iT');
sl_pc(mdl, 'C_bus', 'p', 'I_in', 'p');
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
sl_meas(mdl, 'I_Aout',  'I', 'iAo',   [370 y0+600]);
sl_meas(mdl, 'V_A',     'V', 'vA',    [530 y0+600]);
sl_meas(mdl, 'I_clamp', 'I', 'icl',   [700 y0+600]);
sl_meas(mdl, 'I_path',  'I', 'ipath', [860 y0+600]);
sl_meas(mdl, 'V_bus',   'V', 'vbus',  [1030 y0+600]);
sl_meas(mdl, 'I_in',    'I', 'iin',   [1260 y0+600]);
sl_meas(mdl, 'V_o',     'V', 'vo',    [1720 y0+600]);
sl_meas(mdl, 'I_bat',   'I', 'ibat',  [1880 y0+600]);
sl_note(mdl, sprintf('배터리(이상 전압원)\nV_bat = %.0f V', TBb.vbat), [30 y0+290 160 y0+320]);
sl_note(mdl, sprintf('V_A 노드(충전 포트), C_A 2.4 mF(A25R)'), [440 y0-40 700 y0-20]);
sl_note(mdl, sprintf(['400–500 V급 충전기: 스스로 전류를 제어하는 전류원\n' ...
    '지령 = Test_Conditions(ctrl/prism_tb20_profile.m)\n' ...
    '비상 정지: 3 ms 안에 5 A 이하 → 차량 접촉기 개방(전류 0)']), [440 y0+470 760 y0+520]);
sl_note(mdl, sprintf(['V_A 클램프(E26, E37): 1.2 Ω + 스위치\n' ...
    'V_A ≥ 468 V 켬, ≤ 463 V 끔, 지연 1 µs\n' ...
    '(920 V 충전의 정상 V_A 약 461 V 위, B_470 아래)']), [690 y0+400 960 y0+460]);
sl_note(mdl, sprintf('Stage A 4모듈(8위상, A25, 스위치마다 C_oss %.2f nF) 병렬: 충전 요청 중 모두 동작(역방향 375 A), T/16 인터리빙. 사건 때 게이트 차단(en_A) 또는 모듈 고장', 1e9*TBb.A.Coss), ...
    [160 y0+990 900 y0+1020]);
sl_note(mdl, sprintf('배선 3 mΩ·1.5 µH'), [700 y0+50 840 y0+70]);
sl_note(mdl, sprintf(['400 V 보조버스(R2 기본형: V_A를 따름)\n' ...
    'C_b 400 µF ∥ RC 감쇠기 48.6 mΩ + 1.6 mF ∥ 정전력 부하 Q/max(v, 200 V)']), [940 y0-50 1340 y0-20]);
sl_note(mdl, sprintf('48 V 전원망(절연측): 정전력 부하 P/max(v_o, 10 V)'), [1700 y0-40 2100 y0-20]);

% ---- 시험 조건 -------------------------------------------------------------------------------------------
ts = [mdl '/Test_Conditions'];
add_block('built-in/Subsystem', ts, 'Position', [1180 60 1320 120], 'BackgroundColor', 'lightBlue');
sl_add(ts, 'simulink/Sources/Digital Clock', 'Clock', [30 40 80 70], 'SampleTime', 'TB.dt');
sl_add(ts, 'simulink/Signal Routing/Goto', 't', [120 75 160 95], 'GotoTag', 't', 'TagVisibility', 'global');
sl_line(ts, 'Clock/1', 't/1');
sl_add(ts, 'simulink/Sources/Constant', 'prof', [30 100 130 120], 'Value', 'TB.prof');
sl_mfunc(ts, 'Profile', [180 40 300 130], 'prism_tb28_profile.m');
sl_line(ts, 'Clock/1', 'Profile/1');
sl_line(ts, 'prof/1', 'Profile/2');
sl_add(ts, 'simulink/Signal Routing/Demux', 'split', [330 40 335 130], 'Outputs', '[1 1 1 8 1]');
sl_line(ts, 'Profile/1', 'split/1');
sl_add(ts, 'simulink/Signal Routing/Goto', 'ich', [380 20 460 40], 'GotoTag', 'ich', 'TagVisibility', 'global');
sl_add(ts, 'simulink/Signal Routing/Goto', 'p400', [380 55 460 75], 'GotoTag', 'p400', 'TagVisibility', 'global');
sl_add(ts, 'simulink/Signal Routing/Goto', 'p_load', [380 90 460 110], 'GotoTag', 'p_load', 'TagVisibility', 'global');
sl_add(ts, 'simulink/Signal Routing/Goto', 'en_A', [380 125 460 145], 'GotoTag', 'en_A', 'TagVisibility', 'global');
sl_line(ts, 'split/1', 'ich/1');
sl_line(ts, 'split/2', 'p400/1');
sl_line(ts, 'split/3', 'p_load/1');
sl_line(ts, 'split/4', 'en_A/1');
sl_add(ts, 'simulink/Signal Routing/Goto', 'chg_req', [380 155 460 175], 'GotoTag', 'chg_req', 'TagVisibility', 'global');
sl_line(ts, 'split/5', 'chg_req/1');
add_block('simulink/Sinks/Out1', [ts '/i_ch'], 'Position', [470 0 500 15]);
sl_line(ts, 'split/1', 'i_ch/1');
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
sl_line(ts, 'split/2', 'Q_over_v/1');
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
sl_line(ts, 'split/3', 'P_over_v/1');
sl_line(ts, 'v_floor/1', 'P_over_v/2');
sl_line(ts, 'P_over_v/1', 'iload/1');
sl_line(ts, 'P_over_v/1', 'i_load48/1');
sl_note(ts, sprintf(['시험 조건(시험 장치, ctrl/prism_tb28_profile.m): TB.prof = [t_I(6) I(6) t_ev mask(8) Q P t_chg_on t_chg_off]\n' ...
    '충전기 전류 i_ch(구간 선형, 비상 정지·접촉기 개방 포함), 400 V 부하 Q, 48 V 부하 P, Stage A 위상 동작 여부 en_A(t ≥ t_ev에서 mask),\n' ...
    '충전 요청 chg_req(t_chg_on ≤ t < t_chg_off, 충전기 전류를 올리기 전에 Stage A 모듈을 모두 켬).\n' ...
    '정전력 부하 전류 i = Q/max(v_bus, 200 V), P/max(v_o, 10 V). 전압은 시작 표본 보호 후 한 간격 지연(대수 루프 방지).']), ...
    [30 450 760 500], 'box');
sl_line(mdl, 'Test_Conditions/1', 'ich_PS/1');
sl_line(mdl, 'Test_Conditions/2', 'iload400_PS/1');
sl_line(mdl, 'Test_Conditions/3', 'iload48_PS/1');

% ---- 제어·게이트 ---------------------------------------------------------------------------------
yc = 1250;
build_stageA_gate_zcp(mdl, [160 yc 340 yc+80], 'TB', 1:8, struct('mgr', true, 'chgTag', 'chg_req', 'enTag', 'en_A', ...
    'gateFile', 'prism_gate_stageA_zcpf.m'));
% V_A 클램프 제어
cc = [mdl '/Clamp_Control'];
add_block('built-in/Subsystem', cc, 'Position', [620 yc 800 yc+80], 'BackgroundColor', 'yellow');
sl_add(cc, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', 'TB.dt');
sl_add(cc, 'simulink/Signal Routing/From', 'vA_from', [30 80 110 100], 'GotoTag', 'vA');
sl_add(cc, 'simulink/Discrete/Unit Delay', 'vA_z1', [140 75 170 105], 'SampleTime', 'TB.dt', 'InitialCondition', 'TB.vA0');
sl_line(cc, 'vA_from/1', 'vA_z1/1');
sl_startup_guard(cc, 'Startup_guard', [200 70 230 140], 'TB.vA0', 'TB', [100 160 180 180]);
sl_line(cc, 'vA_z1/1', 'Startup_guard/1');
sl_line(cc, 'Clock/1', 'Startup_guard/2');
sl_add(cc, 'simulink/Sources/Constant', 'clamp_prm', [100 200 200 220], 'Value', 'TB.clamp_prm');
sl_mfunc(cc, 'VA_Clamp', [280 40 420 220], 'prism_va_clamp.m');
sl_line(cc, 'Clock/1', 'VA_Clamp/1');
sl_line(cc, 'Startup_guard/1', 'VA_Clamp/2');
sl_line(cc, 'clamp_prm/1', 'VA_Clamp/3');
sl_add(cc, 'simulink/Signal Routing/Goto', 'g_clamp', [470 60 550 80], 'GotoTag', 'g_clamp', 'TagVisibility', 'global');
sl_add(cc, 'simulink/Signal Routing/Goto', 'clamp_st', [470 160 550 180], 'GotoTag', 'clamp_st', 'TagVisibility', 'global');
sl_line(cc, 'VA_Clamp/1', 'g_clamp/1');
sl_line(cc, 'VA_Clamp/2', 'clamp_st/1');
sl_note(cc, sprintf(['V_A 클램프 비교기(ctrl/prism_va_clamp.m, 검증 코드 E26과 같은 논리): V_A ≥ v_on 켬, ≤ v_off 끔(켜진 동안 v_A > v_off이면 유지),\n' ...
    '요청이 n_delay 간격(1 µs) 이어지면 상태를 바꾼다. 측정은 한 간격 지연과 시작 표본 보호를 거친다.']), [30 250 760 290], 'box');

cs = [mdl '/Controller_StageC'];
add_block('built-in/Subsystem', cs, 'Position', [1360 yc 1540 yc+80], 'BackgroundColor', 'yellow');
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
sl_note(cs, sprintf(['조정형 Stage C 제어기(검증 코드 E22 control과 같은 알고리즘·게인, 표본 10 µs, 계산 지연 1주기, TB16과 같음)\n' ...
    '전류 PI 적분은 평형값에서 시작(prm(27), TB17과 같음). 입력 v_bus는 실제 버스.']), [30 330 760 380], 'box');

gs = [mdl '/Gate_StageC'];
add_block('built-in/Subsystem', gs, 'Position', [1620 yc 1800 yc+80], 'BackgroundColor', 'yellow');
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
sl_note(gs, sprintf(['게이트: 벅 100 kHz 중앙 정렬 PWM(데드타임 50 ns) + CLLC 250 kHz 공진점(TB15·TB16과 같음).\n' ...
    'CLLC 데드타임: 1차가 보낼 때 %.0f ns, 2차가 보낼 때 %.0f ns. |P*| < %.0f W: 두 브리지 같은 위상(2차 %.0f ns).'], ...
    1e9*TBb.gate_prm(5), 1e9*TBb.gate_prm(6), TBb.P_in, 1e9*TBb.gate_prm(7)), [30 360 760 400], 'box');
sl_note(mdl, sprintf(['제어부: Gate_StageA(A25R: 영교차 추종 + 모듈 관리기·셰딩·모듈 고장 처리, 동작 여부 en_A, 충전 요청 chg_req, 상태 stA_mgr)\n' ...
    '· Clamp_Control(태그 g_clamp) · Controller_StageC → Gate_StageC\n' ...
    '각 게이트는 전역 태그로 스위치 셀에 전달된다.']), [160 yc+100 1400 yc+130]);

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [2200 y0 2320 y0+280], 'BackgroundColor', 'lightBlue');
logs = {'t', 'tA', '', ''};
for k = 1:8
    logs(end+1, :) = {sprintf('iA_P%d', k), sprintf('iA%d', k), '', 'single'}; %#ok<AGROW>
    logs(end+1, :) = {sprintf('stA_P%d', k), sprintf('st%d', k), '', 'int8'}; %#ok<AGROW>
end
logs = [logs; {'t', 't', '4', ''; 'vA', 'vA', '4', 'single'; 'iAo', 'iAo', '4', 'single'; 'icl', 'icl', '4', 'single'; ...
    'ich', 'ich', '4', 'single'; 'g_clamp', 'gcl', '4', 'int8'; 'ipath', 'ipath', '4', 'single'; 'vbus', 'vbus', '4', 'single'; ...
    'iin', 'iin', '4', 'single'; 'iL', 'iL', '4', 'single'; 'vI', 'vI', '4', 'single'; 'vo', 'vo', '4', 'single'; ...
    'ix', 'ix', '4', 'single'; 'iload', 'iload', '4', 'single'; 'ir2', 'ir2', '4', 'single'; 'vleg1', 'vleg1', '4', 'single'; ...
    'vlegs1', 'vlegs1', '4', 'single'; 'gC_Q1', 'gq1', '4', 'int8'; 'gC_Q2', 'gq2', '4', 'int8'; 'gC_S1', 'gs1', '4', 'int8'; ...
    'gC_S2', 'gs2', '4', 'int8'; 'ucC', 'uc', '4000', ''; 'stA_mgr', 'mgr', '4', 'single'; 'chg_req', 'chg', '4', 'int8'}];
sl_probe_panel(ms, 30, 30, ...
    {'Scope_StageA', {'iA_P1', 'iA_P3', 'iA_P5', 'iA_P7', 'vA', 'stA_mgr'}; ...
     'Scope_Charger_Clamp', {'ich', 'iAo', 'icl', 'g_clamp'}; ...
     'Scope_Bus', {'vbus', 'p400', 'iin'}; ...
     'Scope_48V', {'vo', 'ix', 'p_load'}; ...
     'Scope_CLLC', {'ir1', 'im', 'ir2'}; ...
     'Scope_Controller', {'ucC'}}, logs);
sl_note(mdl, sprintf(['계측: Scope 6개(Stage A, 충전기·클램프, 버스, 48 V, CLLC, 제어기)\n' ...
    '+ To Workspace(Stage A 위상 전류·구간 2.5 ns, 나머지 10 ns, Stage C 제어 10 µs)']), [2180 y0+300 2520 y0+340]);

sl_note(mdl, sprintf(['파라미터(TB29_init.m ← ref/TB29_<사례>_init.json = 검증 코드 E26·E22·E35 모델, ref/make_ref_TB29.py)\n' ...
    'Stage A(A25R): 4모듈 × 2위상, C_fly 46.875 µF, L_r 864.6 nH(f_r0 25 kHz), R_ds 5.27 mΩ, V_f 4.5 V, C_oss(스위치) %.2f nF, 데드타임 100 ns,\n' ...
    '         영교차 검출 0.5 A·지연 20 ns, 관리기·셰딩 문턱 E32, C_A 2.4 mF\n' ...
    '버스: 배선 3 mΩ·1.5 µH, C_b 400 µF, RC 감쇠기 48.6 mΩ + 1.6 mF. V_A 클램프 1.2 Ω + 스위치(1 mΩ), 468/463 V, 지연 1 µs\n' ...
    'Stage C: TB15·TB16과 같음(벅 204 µH·100 kHz, CLLC 4.8:1·250 kHz, L_m %.1f µH, C_o 2.2 mF)\n' ...
    '해석기: Simscape 지역 해석기 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회), Stage C 제어 표본 10 µs'], 1e9*TBb.A.Coss, 1e6*TBb.C.Lm), ...
    [30 yc+160 1500 yc+240], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
if ~exist(fullfile(here, 'results'), 'dir'), mkdir(fullfile(here, 'results')); end
sl_export_png({mdl, [mdl '/StageA_Module1'], [mdl '/StageC_Regulated'], [mdl '/Gate_StageA'], [mdl '/Clamp_Control'], ...
    [mdl '/Controller_StageC'], [mdl '/Test_Conditions']}, fullfile(here, 'results'));
end
