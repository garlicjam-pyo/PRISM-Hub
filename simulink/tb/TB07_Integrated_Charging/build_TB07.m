function build_TB07()
%BUILD_TB07  TB07 통합 회로 모델(TB07_Integrated_Charging.slx)을 처음부터 만든다.
%
%   충전 모드: 배터리 ← Stage A 4모듈(8위상, 역방향) ← V_A ← 400 V급 충전기(전류원)
%                                                V_A → Stage B → 400 V 버스 → Stage C(48 V)·정전력 부하
%   구성
%     V_bat(이상 전압원) ── StageA_Module1–4(위상 1–8, 스위치 셀 32개, VIN·GND·VOUT 병렬) ── Stage A 출력전류 센서
%     ── V_A 노드(C_A 400 µF) ∥ Charger_400V(제어 전류원, 지령 프로파일) ── R_path 3 mΩ ── L_path 1.5 µH ── 경로전류 센서
%     ── StageB_Regulator(SER → BUS, TB06과 같은 회로) ── 400 V 버스: C_b ∥ 정전력 부하 ∥ DAB 손실 등가 ∥ Stage C
%     Gate_StageA(영교차 추종 8위상) · Charger_Profile · Controller_StageB → Gate_StageB · Gate_StageC
%     Measurements: Scope 7개 + To Workspace(판정용)
%   충전전류는 V_A 노드에서 Stage A로 바로 들어가며 직렬 포트(Stage B)를 지나지 않는다(정격 분리, H1).
%   실행: prism_run('build_TB07')  →  prism_run('run_TB07')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB07_Integrated_Charging';
evalin('base', 'clear TB07_opts');
run(fullfile(here, 'TB07_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');
sl_model_new(mdl, 'TB07_init.m');

sl_note(mdl, 'TB07 — PRISM-Hub 통합 회로 모델(충전 모드): Stage A 4모듈 + 400 V급 충전기 + Stage B + Stage C + 400 V 부하', [30 10 1500 40], 'title');
sl_note(mdl, sprintf(['검증 목적: 400 V급 급속충전 중 보조버스(H3)와 충전전류의 Stage B 비경유(H1)를 회로에서 확인한다.\n' ...
    '  (1) 충전 중 Stage A 4모듈이 만드는 V_A(출력저항 약 1/4)와 충전전류 변화가 Stage B 경로전류·버스전압에 주는 영향 — E16 스위칭 모델과 비교\n' ...
    '      (제어기는 주행과 같은 공칭값 13.2 mΩ을 쓰고 충전 모드를 모른다. 플랜트 경로저항은 약 5.6 mΩ)\n' ...
    '  (2) 충전 대전류(역방향)와 보조 경로전류가 함께 흐를 때 Stage A 8위상 영전류 스위칭과 전류 분담 — E1(8위상)과 비교\n' ...
    '  (3) 충전 중 Stage C 48 V 출력 — TB05와 비교\n' ...
    '사례: A 640 V 충전 375 A, 버스 15 → 25 kW(2 ms) / B 920 V 버스 25 kW, 충전 326 A → 0(2 ms, 10 µs, 비상 정지) / C 788 V 5 kW, 충전 0 → 375 A.\n' ...
    '판정: A Tier-1(경로·필터 ≤ 98 A, 버스 400 ± 8 V), B·C Tier-2(≤ 100 A, 버스 384–416 V), 공통 링크 ≤ 80 A·8 kW·90–110 V, |v_s| ≤ 90 V,\n' ...
    'E16 일치, Stage A ZCS ≤ 5 %% 또는 턴오프 전류 ≤ 2 A, 위상 분담 ≤ 5 %%, 48 V ± 2 %%. 5 ns 정상상태 리플은 정보(TB04B).']), ...
    [30 50 1500 190], 'box');

% ---- 전력 회로 -------------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
gref = [fl 'Electrical Elements/Electrical Reference'];
y0 = 230;                                                    % 주 전력 경로 높이
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bat', [60 y0+80 100 y0+140], 'Orientation', 'down', 'v0', 'TB.vbat');
sl_add(mdl, gref, 'GND', [60 y0+200 100 y0+230]);
sl_solver(mdl, 'Solver', [10 y0+150 50 y0+180], 'GND', 'V', 3);   % 고정 비용(모드 반복 3회)
for m = 1:4                                                  % Stage A 4모듈(위상 2m−1, 2m), 세로로 배치
    ym = y0 + 20 + 230*(m - 1);
    build_stageA_module(mdl, sprintf('StageA_Module%d', m), [160 ym 320 ym+200], m, 'TB.A');
end
sl_add(mdl, gref, 'GND_A', [200 y0+950 240 y0+980]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_Aout', [370 y0+5 420 y0+45]);
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_A', [460 y0+80 500 y0+140], 'Orientation', 'down', ...
    'c', 'TB.A.CA', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vA0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_CA', [460 y0+200 500 y0+230]);
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_A', [530 y0+80 570 y0+140], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_VA', [530 y0+200 570 y0+230]);
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'Charger_400V', [520 y0+340 560 y0+400], 'Orientation', 'up');
sl_add(mdl, gref, 'GND_chg', [520 y0+440 560 y0+470]);
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'ich_PS', [600 y0+360 630 y0+380], 'Orientation', 'left');
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

sl_pc(mdl, 'V_bat', 'n', 'GND', 'V');
for m = 1:4                                                  % 4모듈 병렬: VIN = 배터리 +, GND = 배터리 −, VOUT = V_A
    mn = sprintf('StageA_Module%d', m);
    sl_pc(mdl, 'V_bat', 'p', mn, 'VIN');
    sl_pc(mdl, mn, 'GND', 'GND_A', 'V');
    sl_pc(mdl, mn, 'VOUT', 'I_Aout', 'p');                   % Stage A 출력전류(4모듈 합): 모듈 → V_A 노드(충전 중 음수)
end
sl_pc(mdl, 'I_Aout', 'n', 'C_A', 'p');
sl_pc(mdl, 'C_A', 'n', 'GND_CA', 'V');
sl_pc(mdl, 'V_A', 'p', 'C_A', 'p');
sl_pc(mdl, 'V_A', 'n', 'GND_VA', 'V');
sl_pc(mdl, 'Charger_400V', 'tail', 'GND_chg', 'V');         % 충전기 전류: GND → 전류원 → V_A 노드(주입)
sl_pc(mdl, 'Charger_400V', 'head', 'C_A', 'p');
sl_pc(mdl, 'ich_PS', 'output', 'Charger_400V', 'iT');
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
sl_note(mdl, sprintf(['400 V급 충전기(CCS): 스스로 전류를 제어하는 전류원으로 둔다.\n' ...
    '지령 = Charger_Profile(ctrl/prism_charger_profile.m, TB.chg_prm)\n' ...
    '충전전류는 V_A에서 Stage A로 바로 들어가 직렬 포트를 지나지 않는다']), [600 y0+420 1000 y0+480]);
sl_note(mdl, sprintf('Stage A 4모듈(8위상) 병렬: 충전 중 모두 동작(역방향 최대 375 A), 위상 오프셋 T/16 인터리빙'), [160 y0+990 760 y0+1020]);
sl_note(mdl, sprintf('경로 배선 3 mΩ·1.5 µH\n(Stage A 출력저항은 회로에서 생김)'), [600 y0+50 840 y0+80]);
sl_note(mdl, sprintf('400 V 보조버스: C_b 400 µF ∥ 정전력 부하(총부하 − Stage C 입력 추정) ∥ DAB 손실 등가'), [1180 y0-40 1600 y0-20]);
sl_note(mdl, sprintf('48 V 출력(절연측), R_L = 48²/3 kW'), [1860 y0-40 2120 y0-20]);

% ---- 부하·손실 계산 ----------------------------------------------------------------------------
build_bus_loads(mdl, [1180 110 1290 150], [1310 110 1420 150], 'TB');
sl_line(mdl, 'Load_CPL/1', 'iload_PS/1');
sl_line(mdl, 'DAB_Loss_Model/1', 'iloss_PS/1');

% ---- 제어·게이트 ---------------------------------------------------------------------------------
yc = 760;                                                    % 충전기·Stage A 4모듈 아래로 제어부를 내린다
build_stageA_gate_zcp(mdl, [600 yc+260 780 yc+340], 'TB', 1:8);
% 충전기 전류 지령(시간 프로파일)
cg = [mdl '/Charger_Profile'];
add_block('built-in/Subsystem', cg, 'Position', [680 y0+350 780 y0+390], 'BackgroundColor', 'yellow', 'Orientation', 'left');
sl_add(cg, 'simulink/Sources/Digital Clock', 'Clock', [30 30 80 60], 'SampleTime', 'TB.dt');
sl_add(cg, 'simulink/Sources/Constant', 'chg_prm', [30 90 130 110], 'Value', 'TB.chg_prm');
sl_mfunc(cg, 'Charger_Current', [180 30 320 110], 'prism_charger_profile.m');
add_block('simulink/Sinks/Out1', [cg '/ich'], 'Position', [400 60 430 80]);
sl_add(cg, 'simulink/Signal Routing/Goto', 'ich_tag', [400 110 480 130], 'GotoTag', 'ich', 'TagVisibility', 'global');
sl_line(cg, 'Clock/1', 'Charger_Current/1');
sl_line(cg, 'chg_prm/1', 'Charger_Current/2');
sl_line(cg, 'Charger_Current/1', 'ich/1');
sl_line(cg, 'Charger_Current/1', 'ich_tag/1');
sl_note(cg, sprintf('충전기 출력전류 지령 [i0 i1 t_sw t_ramp]: t_sw부터 t_ramp 동안 i0 → i1 선형'), [30 150 480 180]);
sl_line(mdl, 'Charger_Profile/1', 'ich_PS/1');
build_stageB_control(mdl, [620 yc 800 yc+80], [880 yc 1060 yc+80], 'TB');
build_stageC_gate(mdl, [1600 yc 1780 yc+80], 'TB');
sl_note(mdl, sprintf(['제어부: Gate_StageA(영교차 추종 8위상, 태그 gA_P1_*–gA_P8_*) · Controller_StageB(주행과 같은 공칭값, 5 µs 표본·계산·5 µs 지연)\n' ...
    '→ Gate_StageB(gB_*, gD_*) · Gate_StageC(250 kHz 고정, gC_Q*). 각 게이트는 전역 태그로 스위치 셀에 전달된다.']), [600 yc+100 1700 yc+130]);

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [2180 y0 2300 y0+240], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_StageA', {'iA_P1', 'iA_P3', 'iA_P5', 'iA_P7', 'vA'}; ...
     'Scope_Charger', {'ich', 'iAo'}; ...
     'Scope_Bus', {'vbus', 'p_load'}; ...
     'Scope_StageB', {'ip', 'ih', 'vs'}; ...
     'Scope_Link', {'vlink', 'ilink'}; ...
     'Scope_StageC', {'vo48', 'icin'}; ...
     'Scope_Controller', {'ctrl_dg', 'uc'}}, ...
    {'t', 't', ''; 'vbus', 'vbus', ''; 'ip', 'ip', ''; 'ih', 'ih', ''; 'vs', 'vs', ''; 'vlink', 'vlink', ''; ...
     'ilink', 'ilink', ''; 'iL', 'iL', ''; 'vA', 'vA', ''; 'iAo', 'iAo', ''; ...
     'iA_P1', 'iA1', ''; 'iA_P2', 'iA2', ''; 'iA_P3', 'iA3', ''; 'iA_P4', 'iA4', ''; ...
     'iA_P5', 'iA5', ''; 'iA_P6', 'iA6', ''; 'iA_P7', 'iA7', ''; 'iA_P8', 'iA8', ''; ...
     'stA_P1', 'st1', ''; 'stA_P2', 'st2', ''; 'stA_P3', 'st3', ''; 'stA_P4', 'st4', ''; ...
     'stA_P5', 'st5', ''; 'stA_P6', 'st6', ''; 'stA_P7', 'st7', ''; 'stA_P8', 'st8', ''; ...
     'icin', 'icin', ''; 'vo48', 'vo48', ''; 'ich', 'ich', 'TB.Np'; ...
     'ctrl_dg', 'dg', 'TB.Np'; 'uc', 'uc', 'TB.Np'; 'gate_aux', 'aux', 'TB.Np'});
sl_note(mdl, sprintf('계측: Scope 7개(Stage A, 충전기, 버스, Stage B, 링크, Stage C, 제어기)\n+ To Workspace(판정용, 제어 신호·충전전류는 5 µs마다)'), ...
    [2160 y0+260 2460 y0+290]);

sl_note(mdl, sprintf(['파라미터(TB07_init.m → prism_hub_params.m, 검증 코드와 같은 설계값)\n' ...
    'Stage A: 4모듈 × 2위상, C_fly 7.8125 µF, L_r 144.1 nH(f_r0 150 kHz), R_ds 6 mΩ, ESR 1.5 mΩ, R_L 1 mΩ, R_misc 1.5 mΩ, 데드타임 100 ns, 영교차 검출 0.5 A·지연 20 ns, C_A 400 µF\n' ...
    '충전기: 제어 전류원(지령 TB.chg_prm), 충전 상한 min(375 A, 150 kW/(V_bat/2))\n' ...
    'Stage B: TB04B와 같음(C_s 100 µF, L_h 5 µH, C_link 2 mF, C_b 400 µF, DAB 4:1·200 kHz·11.1 µH, C_oss H-브리지 1 nF·DAB 335/1371 pF), 경로 3 mΩ·1.5 µH\n' ...
    'Stage C: TB05와 같음(25/3, L_r1 11 µH, C_r1 36.8 nF, L_m 66 µH, C_o 470 µF, 250 kHz, 데드타임 50 ns), 48 V 저항부하 0.768 Ω\n' ...
    '해석기: Simulink 고정 간격 이산 TB.dt(5 ns), Simscape 지역 해석기 후진 오일러 TB.dt(고정 비용, 모드 반복 3회). 시작 표본 보호: t < 1.5 dt 동안 측정 입력에 평형점 값']), ...
    [600 yc+380 2100 yc+480], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
end
