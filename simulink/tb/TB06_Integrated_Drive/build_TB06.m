function build_TB06()
%BUILD_TB06  TB06 통합 회로 모델(TB06_Integrated_Drive.slx)을 처음부터 만든다.
%
%   주행 모드: 배터리 → Stage A 모듈 1(2위상) → V_A → Stage B → 400 V 버스 → Stage C(48 V)·정전력 부하
%   구성
%     V_bat(이상 전압원) ── StageA_Module1(위상 1·2, 스위치 셀 8개) ── Stage A 출력전류 센서 ── V_A 노드(C_A 400 µF)
%     ── R_path 3 mΩ ── L_path 1.5 µH ── 경로전류 센서 ── StageB_Regulator(SER → BUS, TB04B와 같은 회로)
%     400 V 버스: C_b ∥ 정전력 부하(Load_CPL) ∥ DAB 손실 등가(DAB_Loss_Model) ∥ Stage C 입력(전류 센서 → StageC_CLLC → 48 V 부하)
%     Gate_StageA(영교차 추종) · Controller_StageB → Gate_StageB · Gate_StageC(250 kHz 고정)
%     Measurements: Scope 6개 + To Workspace(판정용)
%   실행: prism_run('build_TB06')  →  prism_run('run_TB06')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB06_Integrated_Drive';
evalin('base', 'clear TB06_opts');
run(fullfile(here, 'TB06_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');
sl_model_new(mdl, 'TB06_init.m');

sl_note(mdl, 'TB06 — PRISM-Hub 통합 회로 모델(주행 모드): Stage A 모듈 1 + Stage B + Stage C + 400 V 부하', [30 10 1400 40], 'title');
sl_note(mdl, sprintf(['검증 목적: 따로 검증한 세 단(TB01 Stage A, TB04·TB04B Stage B, TB05 Stage C)을 한 회로로 잇고 단 사이 상호작용을 확인한다.\n' ...
    '  (1) Stage A의 실제 출력(공진 SC + C_A)이 Stage B 경로전류·버스전압에 주는 영향 — 등가 전원(V_bat/2, 13.2 mΩ) 검증 모델 E12와 비교\n' ...
    '  (2) Stage B가 끌어가는 경로전류에서 Stage A 영전류 스위칭(영교차 추종)이 유지되는지 — 검증 모델 E1(2위상)과 비교\n' ...
    '  (3) 조정된 버스에서 Stage C 48 V 출력과 입력전류가 버스·Stage B와 함께 동작하는지 — TB05와 비교\n' ...
    '사례(버스 총부하, Stage C 3 kW 포함): A 640 V 15 → 25 kW, B 788 V 5 → 15 kW, C 920 V 25 → 15 kW, 2 ms에 계단, 5 ms까지.\n' ...
    '판정: Tier-1 한계(경로·필터 ≤ 98 A, 링크 ≤ 80 A·8 kW, 링크 90–110 V, |v_s| ≤ 90 V, 버스 400 ± 8 V), E12 일치, Stage A ZCS ≤ 5 %%, 48 V ± 2 %%.\n' ...
    '적분 간격 5 ns(= 게이트 격자)에서는 정상상태 리플이 게이트 양자화 리밋 사이클을 포함하므로 정보로만 기록한다(TB04B: 0.625 ns에서 기준 만족).']), ...
    [30 50 1500 170], 'box');

% ---- 전력 회로 -------------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
gref = [fl 'Electrical Elements/Electrical Reference'];
y0 = 230;                                                    % 주 전력 경로 높이
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
    'i_L_specify', 'on', 'i_L', 'TB.ip0', 'i_L_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_path', [760 y0+5 810 y0+45]);
build_stageB(mdl, 'StageB_Regulator', [860 y0 1100 y0+240], 'TB', ...
    struct('CossP', 'TB.B.Coss_dp', 'CossS', 'TB.B.Coss_ds', 'CossNote', 'DAB C_oss 1차 335 pF·2차 1371 pF(후보 소자 C_o(tr))'));
sl_add(mdl, gref, 'GND_B', [1140 y0+250 1180 y0+280]);
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_bus', [1200 y0+80 1240 y0+140], 'Orientation', 'down', ...
    'c', 'TB.Cb', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vb0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_Cb', [1200 y0+200 1240 y0+230]);
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_bus', [1270 y0+80 1310 y0+140], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_Vb', [1270 y0+200 1310 y0+230]);
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load', [1340 y0+80 1380 y0+140], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_load', [1340 y0+200 1380 y0+230]);
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_dabloss', [1410 y0+80 1450 y0+140], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_loss', [1410 y0+200 1450 y0+230]);
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iload_PS', [1350 y0+40 1380 y0+60]);
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iloss_PS', [1420 y0+40 1450 y0+60]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_Cin', [1490 y0+5 1540 y0+45]);
build_stageC(mdl, 'StageC_CLLC', [1590 y0 1810 y0+240], 'TB');
sl_add(mdl, gref, 'GND_C', [1590 y0+270 1630 y0+300]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_o48', [1860 y0+5 1910 y0+45]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_load48', [1950 y0+80 1990 y0+140], 'Orientation', 'down', 'R', 'TB.RL_C');
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_o48', [2020 y0+80 2060 y0+140], 'Orientation', 'down');

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
sl_pc(mdl, 'L_path', 'n', 'I_path', 'p');                % i_p 양의 방향: V_A → 직렬 포트 → 버스
sl_pc(mdl, 'I_path', 'n', 'StageB_Regulator', 'SER');
sl_pc(mdl, 'StageB_Regulator', 'BUS', 'C_bus', 'p');
sl_pc(mdl, 'StageB_Regulator', 'GND', 'GND_B', 'V');
sl_pc(mdl, 'C_bus', 'n', 'GND_Cb', 'V');
sl_pc(mdl, 'V_bus', 'p', 'C_bus', 'p');
sl_pc(mdl, 'V_bus', 'n', 'GND_Vb', 'V');
sl_pc(mdl, 'I_load', 'tail', 'C_bus', 'p');              % 부하 전류: 버스 → 전류원 → GND
sl_pc(mdl, 'I_load', 'head', 'GND_load', 'V');
sl_pc(mdl, 'I_dabloss', 'tail', 'C_bus', 'p');
sl_pc(mdl, 'I_dabloss', 'head', 'GND_loss', 'V');
sl_pc(mdl, 'iload_PS', 'output', 'I_load', 'iT');
sl_pc(mdl, 'iloss_PS', 'output', 'I_dabloss', 'iT');
sl_pc(mdl, 'StageB_Regulator', 'BUS', 'I_Cin', 'p');     % Stage C 입력전류: 버스 → Stage C
sl_pc(mdl, 'I_Cin', 'n', 'StageC_CLLC', 'DC_P');
sl_pc(mdl, 'StageC_CLLC', 'DC_N', 'GND_C', 'V');
sl_pc(mdl, 'StageC_CLLC', 'VO_P', 'I_o48', 'p');
sl_pc(mdl, 'I_o48', 'n', 'R_load48', 'p');
sl_pc(mdl, 'R_load48', 'n', 'StageC_CLLC', 'VO_N');
sl_pc(mdl, 'V_o48', 'p', 'R_load48', 'p');
sl_pc(mdl, 'V_o48', 'n', 'R_load48', 'n');
sl_meas(mdl, 'I_Aout', 'I', 'iAo',   [370 y0+300]);
sl_meas(mdl, 'V_A',    'V', 'vA',    [530 y0+300]);
sl_meas(mdl, 'I_path', 'I', 'ip',    [760 y0+300]);
sl_meas(mdl, 'V_bus',  'V', 'vbus',  [1270 y0+300]);
sl_meas(mdl, 'I_Cin',  'I', 'icin',  [1490 y0+300]);
sl_meas(mdl, 'I_o48',  'I', 'io48',  [1860 y0+300]);
sl_meas(mdl, 'V_o48',  'V', 'vo48',  [2020 y0+300]);
sl_note(mdl, sprintf('배터리\n(이상 전압원)'), [40 y0+290 160 y0+320]);
sl_note(mdl, sprintf('V_A 노드(충전 포트), C_A 400 µF'), [440 y0-40 700 y0-20]);
sl_note(mdl, sprintf('경로 배선 3 mΩ·1.5 µH\n(Stage A 출력저항은 회로에서 생김)'), [600 y0+50 840 y0+80]);
sl_note(mdl, sprintf('400 V 보조버스: C_b 400 µF ∥ 정전력 부하(총부하 − Stage C 입력 추정) ∥ DAB 손실 등가'), [1180 y0-40 1600 y0-20]);
sl_note(mdl, sprintf('48 V 출력(절연측), R_L = 48²/3 kW'), [1860 y0-40 2120 y0-20]);

% ---- 부하·손실 계산 ----------------------------------------------------------------------------
build_bus_loads(mdl, [1180 110 1290 150], [1310 110 1420 150], 'TB');
sl_line(mdl, 'Load_CPL/1', 'iload_PS/1');
sl_line(mdl, 'DAB_Loss_Model/1', 'iloss_PS/1');

% ---- 제어·게이트 ---------------------------------------------------------------------------------
yc = 640;
build_stageA_gate_zcp(mdl, [160 yc 340 yc+80], 'TB', [1 2]);
build_stageB_control(mdl, [620 yc 800 yc+80], [880 yc 1060 yc+80], 'TB');
build_stageC_gate(mdl, [1600 yc 1780 yc+80], 'TB');
sl_note(mdl, sprintf(['제어부: Gate_StageA(영교차 추종, 태그 gA_P1_*·gA_P2_*) · Controller_StageB(5 µs 표본·계산·5 µs 지연) → Gate_StageB(gB_*, gD_*)\n' ...
    '· Gate_StageC(250 kHz 고정, gC_Q*). 각 게이트는 전역 태그로 스위치 셀에 전달된다.']), [160 yc+100 1300 yc+130]);

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [2180 y0 2300 y0+240], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_StageA', {'iA_P1', 'iA_P2', 'vA'}; ...
     'Scope_Bus', {'vbus', 'p_load'}; ...
     'Scope_StageB', {'ip', 'ih', 'vs'}; ...
     'Scope_Link', {'vlink', 'ilink'}; ...
     'Scope_StageC', {'vo48', 'icin'}; ...
     'Scope_Controller', {'ctrl_dg', 'uc'}}, ...
    {'t', 't', ''; 'vbus', 'vbus', ''; 'ip', 'ip', ''; 'ih', 'ih', ''; 'vs', 'vs', ''; 'vlink', 'vlink', ''; ...
     'ilink', 'ilink', ''; 'iL', 'iL', ''; 'vA', 'vA', ''; 'iAo', 'iAo', ''; 'iA_P1', 'iA1', ''; 'iA_P2', 'iA2', ''; ...
     'stA_P1', 'st1', ''; 'stA_P2', 'st2', ''; 'icin', 'icin', ''; 'vo48', 'vo48', ''; ...
     'ctrl_dg', 'dg', 'TB.Np'; 'uc', 'uc', 'TB.Np'; 'gate_aux', 'aux', 'TB.Np'});
sl_note(mdl, sprintf('계측: Scope 6개(Stage A, 버스, Stage B, 링크, Stage C, 제어기)\n+ To Workspace(판정용, 제어 신호는 5 µs마다)'), ...
    [2160 y0+260 2460 y0+290]);

sl_note(mdl, sprintf(['파라미터(TB06_init.m → prism_hub_params.m, 검증 코드와 같은 설계값)\n' ...
    'Stage A: C_fly 7.8125 µF, L_r 144.1 nH(f_r0 150 kHz), R_ds 6 mΩ, ESR 1.5 mΩ, R_L 1 mΩ, R_misc 1.5 mΩ, 데드타임 100 ns, 영교차 검출 0.5 A·지연 20 ns, C_A 400 µF\n' ...
    'Stage B: TB04B와 같음(C_s 100 µF, L_h 5 µH, C_link 2 mF, C_b 400 µF, DAB 4:1·200 kHz·11.1 µH, C_oss H-브리지 1 nF·DAB 335/1371 pF), 경로 3 mΩ·1.5 µH\n' ...
    'Stage C: TB05와 같음(25/3, L_r1 11 µH, C_r1 36.8 nF, L_m 66 µH, C_o 470 µF, 250 kHz, 데드타임 50 ns), 48 V 저항부하 0.768 Ω\n' ...
    '해석기: Simulink 고정 간격 이산 TB.dt(5 ns), Simscape 지역 해석기 후진 오일러 TB.dt(고정 비용, 모드 반복 3회). 시작 표본 보호: t < 1.5 dt 동안 측정 입력에 평형점 값']), ...
    [30 yc+160 1500 yc+250], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
end
