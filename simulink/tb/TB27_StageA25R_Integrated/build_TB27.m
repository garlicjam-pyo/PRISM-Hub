function build_TB27()
%BUILD_TB27  TB27 테스트벤치 모델(TB27_StageA25R_Integrated.slx)을 처음부터 만든다.
%
%   Stage A 25 kHz 설계 수정안(A25R = A25 + C_A 2.4 mF, docs/38·E35)의 4모듈 회로(TB26과 같은 결선, C_A 값은 TB.A.CA): TB24 회로(배터리 → Stage A 모듈 1–4 → V_A 노드 → 배선 → 400 V 버스,
%   모듈 관리기·셰딩·고장 처리 게이트 ctrl/prism_gate_stageA_zcpf.m)에 세 가지를 바꿨다.
%   (1) Stage A 소자값을 A25로(L_r 864.6 nH, C_fly 46.875 µF, R_ds 5.27 mΩ, V_f 4.5 V), (2) 스위치 셀마다 출력용량(등가 선형 C_oss),
%   (3) 배터리 전류 센서와 전력 적분(Stage A 손실 = 배터리 전력 − V_A 쪽 출력 전력, 하드 턴온 전류 펄스를 놓치지 않도록 간격마다 적분).
%   실행: prism_run('build_TB27')  →  prism_run('smoke_TB27')  →  prism_run('run_TB27')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB27_StageA25R_Integrated';
evalin('base', 'clear TB27_case TB27_tend');
run(fullfile(here, 'TB27_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');
sl_model_new(mdl, 'TB27_init.m');
TBb = evalin('base', 'TB');

sl_note(mdl, 'TB27 — Stage A 25 kHz 설계 수정안(A25R: C_A 2.4 mF) 4모듈 + 스위치 출력용량: 모듈 관리기·셰딩·고장 처리, R2 버스, V_A 노드 충전기', [30 10 1500 40], 'title');
sl_note(mdl, sprintf(['검증 목적: E31에서 Stage A 출력용량 손실이 모델보다 한 자릿수 커 공진주파수를 25 kHz로 낮췄다(A25, 위치당 C4MS008075U2 2병렬).\n' ...
    'A25는 과도 판정을 대부분 통과하지 못했고(E33·TB26), C_A를 6배(2.4 mF)로 한 수정안 A25R이 모델에서 통과했다(E35). 같은 판정을 회로에서 확인한다.\n' ...
    '판정: (C1) 턴오프 영전류, (C2) 위상 첨두 ≤ 한도, (C3) V_A, (C4) 동작 모듈 수(모델과 같은 사건 수·끝 수), (C5, 정상상태 사례만) Stage A 손실\n' ...
    '(배터리 전력 − V_A 쪽 출력, 실제 주기 × 20 창)이 모델과 10 %% 안. 사례: 충전 중 모듈 고장(FF), 느린 충전 시작·종료(MC), Tier-1 계단(MA), 정격 충전 정상상태(SC)']), ...
    [30 50 1500 120], 'box');

% ---- 전력 회로 -------------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
gref = [fl 'Electrical Elements/Electrical Reference'];
y0 = 200;
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bat', [60 y0+80 100 y0+140], 'Orientation', 'down', 'v0', 'TB.vbat');
sl_add(mdl, gref, 'GND', [60 y0+200 100 y0+230]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_bat', [100 y0+5 140 y0+45]);   % (TB27) 배터리 전류(4모듈 합)
sl_solver(mdl, 'Solver', [10 y0+150 50 y0+180], 'GND', 'V', 3);   % 고정 비용(모드 반복 3회)
for m = 1:4                                                  % Stage A 4모듈(위상 2m−1, 2m), 세로로 배치
    ym = y0 + 20 + 230*(m - 1);
    build_stageA_module(mdl, sprintf('StageA_Module%d', m), [160 ym 320 ym+200], m, 'TB.A', 'TB.A.Coss');
end
for k = 1:8                                                  % (TB24) 위상별 C_fly 초기 전압(멈춘 모듈 V_bat/2 − 5 V)
    set_param(sprintf('%s/StageA_Module%d/StageA_Phase%d/C_fly', mdl, ceil(k/2), k), 'vc', sprintf('TB.vC0_ph(%d)', k));
end
sl_add(mdl, gref, 'GND_A', [200 y0+950 240 y0+980]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_Aout', [370 y0+5 420 y0+45]);
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_A', [460 y0+80 500 y0+140], 'Orientation', 'down', ...
    'c', 'TB.A.CA', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vA0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_CA', [460 y0+200 500 y0+230]);
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_A', [530 y0+80 570 y0+140], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_VA', [530 y0+200 570 y0+230]);
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_VA', [600 y0+80 640 y0+140], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iVA_PS', [610 y0+40 640 y0+60]);
sl_add(mdl, gref, 'GND_IVA', [600 y0+200 640 y0+230]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_path', [700 y0+15 750 y0+35], 'R', 'TB.Rpath');
sl_add(mdl, [fl 'Electrical Elements/Inductor'], 'L_path', [780 y0+15 830 y0+35], 'l', 'TB.Lpath', 'r', '0', ...
    'i_L_specify', 'on', 'i_L', 'TB.iw0', 'i_L_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_path', [860 y0+5 910 y0+45]);
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

sl_pc(mdl, 'V_bat', 'n', 'GND', 'V');
sl_pc(mdl, 'V_bat', 'p', 'I_bat', 'p');
for m = 1:4
    mn = sprintf('StageA_Module%d', m);
    sl_pc(mdl, 'I_bat', 'n', mn, 'VIN');
    sl_pc(mdl, mn, 'GND', 'GND_A', 'V');
    sl_pc(mdl, mn, 'VOUT', 'I_Aout', 'p');                   % Stage A 출력전류(4모듈 합): 모듈 → V_A(충전 중 음수)
end
sl_pc(mdl, 'I_Aout', 'n', 'C_A', 'p');
sl_pc(mdl, 'C_A', 'n', 'GND_CA', 'V');
sl_pc(mdl, 'V_A', 'p', 'C_A', 'p');
sl_pc(mdl, 'V_A', 'n', 'GND_VA', 'V');
sl_pc(mdl, 'I_VA', 'tail', 'C_A', 'p');                      % V_A 직접 전류: V_A → 전류원 → GND(음수면 충전기 주입)
sl_pc(mdl, 'I_VA', 'head', 'GND_IVA', 'V');
sl_pc(mdl, 'iVA_PS', 'output', 'I_VA', 'iT');
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
sl_meas(mdl, 'I_Aout', 'I', 'iAo',   [370 y0+600]);
sl_meas(mdl, 'I_bat',  'I', 'ibat',  [100 y0+600]);
sl_meas(mdl, 'V_A',    'V', 'vA',    [530 y0+600]);
sl_meas(mdl, 'I_path', 'I', 'ipath', [860 y0+600]);
sl_meas(mdl, 'V_bus',  'V', 'vbus',  [1030 y0+600]);
sl_note(mdl, sprintf('배터리(이상 전압원)\nV_bat = %.0f V', TBb.vbat), [30 y0+290 160 y0+320]);
sl_note(mdl, sprintf('Stage A 4모듈(위상 1–8, A25), 모듈마다 C_fly 46.875 µF·L_r 864.6 nH × 2위상, 스위치마다 C_oss %.2f nF', 1e9*TBb.A.Coss), [160 y0-30 620 y0-10]);
sl_note(mdl, sprintf('V_A 노드(충전 포트), C_A 400 µF, 충전기 등 직접 전류 I_VA'), [440 y0-60 760 y0-40]);
sl_note(mdl, sprintf('배선 3 mΩ·1.5 µH'), [700 y0+50 840 y0+70]);
sl_note(mdl, sprintf(['400 V 보조버스(R2, E23·TB16과 같음)\n' ...
    'C_b 400 µF ∥ RC 감쇠기 48.6 mΩ + 1.6 mF ∥ 정전력 부하 P/max(v, 200 V)']), [940 y0-50 1300 y0-20]);

% ---- 시험 조건: 버스 정전력 부하 P(t), V_A 직접 전류 I_VA(t), 충전 요청 chg(t) -------------------------------
ts = [mdl '/Test_Conditions'];
add_block('built-in/Subsystem', ts, 'Position', [1180 60 1320 140], 'BackgroundColor', 'lightBlue');
sl_add(ts, 'simulink/Sources/Digital Clock', 'Clock', [30 40 80 70], 'SampleTime', 'TB.dt');
sl_add(ts, 'simulink/Signal Routing/Goto', 't', [120 75 160 95], 'GotoTag', 't', 'TagVisibility', 'global');
sl_line(ts, 'Clock/1', 't/1');
sl_add(ts, 'simulink/Sources/Constant', 'prof', [30 100 130 120], 'Value', 'TB.prof');
sl_mfunc(ts, 'Profile', [180 40 300 130], 'prism_tb22_profile.m');
sl_line(ts, 'Clock/1', 'Profile/1');
sl_line(ts, 'prof/1', 'Profile/2');
sl_add(ts, 'simulink/Signal Routing/Demux', 'split', [330 40 335 130], 'Outputs', '3');
sl_line(ts, 'Profile/1', 'split/1');
sl_add(ts, 'simulink/Signal Routing/Goto', 'p400', [380 30 460 50], 'GotoTag', 'p400', 'TagVisibility', 'global');
sl_add(ts, 'simulink/Signal Routing/Goto', 'iVA', [380 120 460 140], 'GotoTag', 'iVA', 'TagVisibility', 'global');
sl_add(ts, 'simulink/Signal Routing/Goto', 'chg_req', [380 300 460 320], 'GotoTag', 'chg_req', 'TagVisibility', 'global');
sl_line(ts, 'split/1', 'p400/1');
sl_line(ts, 'split/2', 'iVA/1');
sl_line(ts, 'split/3', 'chg_req/1');
add_block('simulink/Sinks/Out1', [ts '/i_VA'], 'Position', [470 150 500 170]);
sl_line(ts, 'split/2', 'i_VA/1');
sl_add(ts, 'simulink/Signal Routing/From', 'vb_from', [30 180 110 200], 'GotoTag', 'vbus');
sl_add(ts, 'simulink/Signal Routing/From', 't_from1', [30 220 110 240], 'GotoTag', 't');
sl_startup_guard(ts, 'Guard_vbus', [150 175 190 245], 'TB.vb0', 'TB', [30 260 110 280]);
sl_line(ts, 'vb_from/1', 'Guard_vbus/1');
sl_line(ts, 't_from1/1', 'Guard_vbus/2');
sl_add(ts, 'simulink/Discrete/Unit Delay', 'vb_z1', [220 195 250 225], 'SampleTime', 'TB.dt');
sl_add(ts, 'simulink/Sources/Constant', 'vmin_q', [220 250 280 270], 'Value', 'TB.vmin_q');
sl_add(ts, 'simulink/Math Operations/MinMax', 'vb_floor', [310 200 340 250], 'Function', 'max', 'Inputs', '2');
sl_add(ts, 'simulink/Math Operations/Divide', 'P_over_v', [380 190 420 270]);
add_block('simulink/Sinks/Out1', [ts '/i_load400'], 'Position', [470 220 500 240]);
sl_line(ts, 'Guard_vbus/1', 'vb_z1/1');
sl_line(ts, 'vb_z1/1', 'vb_floor/1');
sl_line(ts, 'vmin_q/1', 'vb_floor/2');
sl_line(ts, 'split/1', 'P_over_v/1');
sl_line(ts, 'vb_floor/1', 'P_over_v/2');
sl_line(ts, 'P_over_v/1', 'i_load400/1');
sl_note(ts, sprintf(['시험 조건(시험 장치): 버스 정전력 부하 전력 P(t)와 V_A 노드 직접 전류 I_VA(t)는 구간 선형(각 6점), 충전 요청 chg는 구간\n' ...
    '[t_on, t_off)에서 1(TB.prof = [t_P P t_I I t_on t_off]). 정전력 부하 전류 i = P/max(v_bus, 200 V). 버스 전압은 시작 표본 보호 후\n' ...
    '한 간격 지연(대수 루프 방지). 충전 요청은 차량 충전 제어기가 충전기 전류를 올리기 전에 보내는 신호다.']), [30 340 760 390], 'box');
sl_line(mdl, 'Test_Conditions/1', 'iVA_PS/1');
sl_line(mdl, 'Test_Conditions/2', 'iload400_PS/1');

% ---- 게이트 -------------------------------------------------------------------------------------
yc = 1250;
build_stageA_gate_zcp(mdl, [160 yc 340 yc+80], 'TB', 1:8, struct('mgr', true, 'chgTag', 'chg_req', 'gateFile', 'prism_gate_stageA_zcpf.m'));
pg = TBb.gateA_zcpm_prm;
sl_note(mdl, sprintf(['제어부: Gate_StageA = 영교차 추종(방향 반전 처리) + 모듈 관리기 + 모듈별 위상 셰딩 + 모듈 고장 처리(ctrl/prism_gate_stageA_zcpf.m).\n' ...
    '고장: 모듈 %d(0 = 없음), %.2f ms(간격 %d) → 그 모듈 위상을 바로 멈추고 후보에서 뺌, 동작 모듈이 0이면 다음 건전 모듈을 바로 시작.\n' ...
    '모듈 추가: |I| > 동작 수 × %.0f A, 위상 |i| > %.0f A, 또는 충전 요청(추가 뒤 %.0f µs 막음). 줄임: ceil(|I|/%.0f A) < 동작 수가 %.1f ms 지속.\n' ...
    '동작 모듈은 건전 모듈 가운데 번호가 작은 것부터. 태그 gA_P*_S*, stA_P*, stA_mgr'], ...
    pg(22), 1e3*pg(23)*TBb.dt, pg(23), pg(13), pg(15), 1e6*pg(17)*TBb.dt, pg(14), 1e3*pg(16)*TBb.dt), ...
    [380 yc+10 1400 yc+80]);

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [1400 y0 1520 y0+280], 'BackgroundColor', 'lightBlue');
logs = cell(0, 4);
for k = 1:8
    logs(end+1, :) = {sprintf('iA_P%d', k), sprintf('iA%d', k), '', 'single'}; %#ok<AGROW>
    logs(end+1, :) = {sprintf('stA_P%d', k), sprintf('st%d', k), '', 'int8'}; %#ok<AGROW>
end
% (TB27) 손실 계산용 적분: q_bat = ∫ i_bat dt, e_out = ∫ v_A·i_Aout dt(간격마다, 하드 턴온 펄스 포함)
sl_add(ms, 'simulink/Signal Routing/From', 'ibat_f', [30 420 110 440], 'GotoTag', 'ibat');
sl_add(ms, 'simulink/Signal Routing/From', 'vA_f', [30 460 110 480], 'GotoTag', 'vA');
sl_add(ms, 'simulink/Signal Routing/From', 'iAo_f', [30 500 110 520], 'GotoTag', 'iAo');
sl_add(ms, 'simulink/Discrete/Discrete-Time Integrator', 'q_bat_int', [170 415 220 445], 'gainval', '1', 'SampleTime', 'TB.dt', ...
    'IntegratorMethod', 'Integration: Forward Euler');
sl_add(ms, 'simulink/Math Operations/Product', 'p_out', [150 465 180 515]);
sl_add(ms, 'simulink/Discrete/Discrete-Time Integrator', 'e_out_int', [220 475 270 505], 'gainval', '1', 'SampleTime', 'TB.dt', ...
    'IntegratorMethod', 'Integration: Forward Euler');
sl_line(ms, 'ibat_f/1', 'q_bat_int/1');
sl_line(ms, 'vA_f/1', 'p_out/1'); sl_line(ms, 'iAo_f/1', 'p_out/2'); sl_line(ms, 'p_out/1', 'e_out_int/1');
sl_add(ms, 'simulink/Signal Routing/Goto', 'q_bat', [270 420 330 440], 'GotoTag', 'q_bat', 'TagVisibility', 'global');
sl_add(ms, 'simulink/Signal Routing/Goto', 'e_out', [300 480 360 500], 'GotoTag', 'e_out', 'TagVisibility', 'global');
sl_line(ms, 'q_bat_int/1', 'q_bat/1'); sl_line(ms, 'e_out_int/1', 'e_out/1');
logs = [logs; {'t', 't4', '4', ''; 'stA_mgr', 'mgr', '4', 'single'; 'vA', 'vA', '4', ''; 'iAo', 'iAo', '4', 'single'; ...
    'q_bat', 'qbat', '4', ''; 'e_out', 'eout', '4', ''; ...
    'ipath', 'ipath', '4', 'single'; 'vbus', 'vbus', '4', ''; 'iVA', 'iVA', '4', 'single'; 'p400', 'p400', '4', 'single'; ...
    'chg_req', 'chg', '4', 'int8'}];
sl_probe_panel(ms, 30, 30, ...
    {'Scope_StageA', {'iA_P1', 'iA_P3', 'iA_P5', 'iA_P7', 'stA_mgr'}; ...
     'Scope_Node', {'vA', 'iAo', 'iVA', 'chg_req'}; ...
     'Scope_Bus', {'vbus', 'ipath', 'p400'}}, logs);
sl_note(mdl, sprintf(['계측: Scope 3개(Stage A 위상 전류·관리기 상태, V_A 노드·충전 요청, 버스)\n' ...
    '+ To Workspace(Stage A 위상 전류·구간 2.5 ns, 나머지 10 ns), 배터리 전하·출력 에너지 적분(간격마다)']), [1380 y0+300 1700 y0+330]);

sl_note(mdl, sprintf(['파라미터(TB27_init.m ← ref/TB27_<사례>_init.json = 검증 코드 E35, A25R)\n' ...
    'Stage A: 4모듈 × 2위상, C_fly 46.875 µF, L_r 864.6 nH(f_r0 25 kHz), R_ds 5.27 mΩ, V_f 4.5 V, C_oss(스위치) %.2f nF, 데드타임 100 ns,\n' ...
    '         영교차 검출 0.5 A·지연 20 ns(무장 2.5 A, 무장 못 한 반주기는 부호 없는 영교차), C_A 400 µF, 멈춘 모듈 C_fly = V_bat/2 − 5 V\n' ...
    '버스: 배선 3 mΩ·1.5 µH, C_b 400 µF, RC 감쇠기 48.6 mΩ + 1.6 mF. 해석기: 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회)'], 1e9*TBb.A.Coss), ...
    [30 yc+130 1400 yc+200], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
if ~exist(fullfile(here, 'results'), 'dir'), mkdir(fullfile(here, 'results')); end
sl_export_png({mdl, [mdl '/StageA_Module1'], [mdl '/Gate_StageA'], [mdl '/Test_Conditions']}, fullfile(here, 'results'));
end
