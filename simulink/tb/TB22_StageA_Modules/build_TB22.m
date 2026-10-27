function build_TB22()
%BUILD_TB22  TB22 테스트벤치 모델(TB22_StageA_Modules.slx)을 처음부터 만든다.
%
%   Stage A 4모듈 경부하 운전: 배터리 → Stage A 모듈 1–4(8위상, 영교차 추종 + 모듈 관리기 + 모듈별 위상 셰딩 + 방향 반전 처리)
%   → V_A 노드(C_A 400 µF, 충전기 전류원) → 배선 3 mΩ·1.5 µH → 400 V 버스(C_b 400 µF ∥ RC 감쇠기 48.6 mΩ + 1.6 mF ∥ 정전력 부하)
%   구성
%     V_bat(이상 전압원) ── StageA_Module1–4(VIN·GND·VOUT 병렬) ── I_Aout ── C_A ──┬── I_VA(충전기 등 직접 전류, 시험 조건) ── GND
%                                                                                  └── R_path ── L_path ── I_path ── 버스(C_bus, R_dmp–C_dmp, I_load400)
%     Test_Conditions: 버스 정전력 부하 P(t), V_A 직접 전류 I_VA(t)(구간 선형), 충전 요청 chg(t)(ctrl/prism_tb22_profile.m)
%     Gate_StageA: ctrl/prism_gate_stageA_zcpm.m(검증 코드 E28 model_stage_a.mgr_step과 같은 논리)
%   실행: prism_run('build_TB22')  →  prism_run('run_TB22')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB22_StageA_Modules';
evalin('base', 'clear TB22_case TB22_ref TB22_tend');
run(fullfile(here, 'TB22_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');
sl_model_new(mdl, 'TB22_init.m');
TBb = evalin('base', 'TB');

sl_note(mdl, 'TB22 — Stage A 4모듈 경부하 운전: 모듈 관리기 + 모듈별 위상 셰딩 + 방향 반전 처리 게이트, R2 버스, V_A 노드 충전기', [30 10 1500 40], 'title');
sl_note(mdl, sprintf(['검증 목적: Stage A는 모듈 4개(위상 8개)다. 주행 중 보조부하는 모듈 하나나 둘이면 되고, 400–500 V급 충전(375 A)에는 넷이 모두 필요하다.\n' ...
    '모듈 관리기는 전체 출력전류로 동작 모듈 수를 정하고(추가는 바로, 줄임은 1 ms 지속 뒤 자연 턴오프로), 충전 요청이 오면 충전기 전류가 오르기 전에\n' ...
    '모든 모듈을 켠다. 동작 모듈마다 경부하 위상 셰딩(E24)을 한다. 회로에서 (T1) 모든 턴오프의 영전류, (T2) 위상 첨두 ≤ 정격점 첨두,\n' ...
    '(T3) V_A가 전부 켬과 1 V 안, (T4) 모듈 수 전환이 예상대로이고 반복·취소가 없는지 본다. 기준: 검증 코드 E28(사례 MA·MB·MC·MF)']), ...
    [30 50 1500 120], 'box');

% ---- 전력 회로 -------------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
gref = [fl 'Electrical Elements/Electrical Reference'];
y0 = 200;
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
for m = 1:4
    mn = sprintf('StageA_Module%d', m);
    sl_pc(mdl, 'V_bat', 'p', mn, 'VIN');
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
sl_meas(mdl, 'V_A',    'V', 'vA',    [530 y0+600]);
sl_meas(mdl, 'I_path', 'I', 'ipath', [860 y0+600]);
sl_meas(mdl, 'V_bus',  'V', 'vbus',  [1030 y0+600]);
sl_note(mdl, sprintf('배터리(이상 전압원)\nV_bat = %.0f V', TBb.vbat), [30 y0+290 160 y0+320]);
sl_note(mdl, sprintf('Stage A 4모듈(위상 1–8), 모듈마다 C_fly 7.8125 µF·L_r 144.1 nH × 2위상'), [160 y0-30 520 y0-10]);
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
build_stageA_gate_zcp(mdl, [160 yc 340 yc+80], 'TB', 1:8, struct('mgr', true, 'chgTag', 'chg_req'));
pg = TBb.gateA_zcpm_prm;
sl_note(mdl, sprintf(['제어부: Gate_StageA = 영교차 추종(방향 반전 처리) + 모듈 관리기 + 모듈별 위상 셰딩(ctrl/prism_gate_stageA_zcpm.m).\n' ...
    '모듈 추가: |I| > 동작 수 × %.0f A, 위상 |i| > %.0f A, 또는 충전 요청(추가 뒤 %.0f µs 막음). 줄임: ceil(|I|/%.0f A) < 동작 수가 %.1f ms 지속.\n' ...
    '위상 셰딩: |I_m| < %.0f A가 %.0f µs → 위상 하나, |I_m| > %.0f A 또는 |i| > %.0f A → 둘. 태그 gA_P*_S*, stA_P*, stA_mgr'], ...
    pg(13), pg(15), 1e6*pg(17)*TBb.dt, pg(14), 1e3*pg(16)*TBb.dt, max(pg(8), 15), 1e6*pg(12)*TBb.dt, pg(9), pg(10)), ...
    [380 yc+10 1400 yc+70]);

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [1400 y0 1520 y0+280], 'BackgroundColor', 'lightBlue');
logs = cell(0, 4);
for k = 1:8
    logs(end+1, :) = {sprintf('iA_P%d', k), sprintf('iA%d', k), '', 'single'}; %#ok<AGROW>
    logs(end+1, :) = {sprintf('stA_P%d', k), sprintf('st%d', k), '', 'int8'}; %#ok<AGROW>
end
logs = [logs; {'t', 't4', '4', ''; 'stA_mgr', 'mgr', '4', 'single'; 'vA', 'vA', '4', ''; 'iAo', 'iAo', '4', 'single'; ...
    'ipath', 'ipath', '4', 'single'; 'vbus', 'vbus', '4', ''; 'iVA', 'iVA', '4', 'single'; 'p400', 'p400', '4', 'single'; ...
    'chg_req', 'chg', '4', 'int8'}];
sl_probe_panel(ms, 30, 30, ...
    {'Scope_StageA', {'iA_P1', 'iA_P3', 'iA_P5', 'iA_P7', 'stA_mgr'}; ...
     'Scope_Node', {'vA', 'iAo', 'iVA', 'chg_req'}; ...
     'Scope_Bus', {'vbus', 'ipath', 'p400'}}, logs);
sl_note(mdl, sprintf(['계측: Scope 3개(Stage A 위상 전류·관리기 상태, V_A 노드·충전 요청, 버스)\n' ...
    '+ To Workspace(Stage A 위상 전류·구간 2.5 ns, 나머지 10 ns)']), [1380 y0+300 1700 y0+330]);

sl_note(mdl, sprintf(['파라미터(TB22_init.m ← ref/TB22_<사례>_init.json = 검증 코드 E28, Stage A는 prism_hub_params = E1 설계값)\n' ...
    'Stage A: 4모듈 × 2위상, C_fly 7.8125 µF, L_r 144.1 nH(f_r0 150 kHz), 데드타임 100 ns, 영교차 검출 0.5 A·지연 20 ns(무장 2.5 A,\n' ...
    '         무장 못 한 반주기는 공칭 도통시간 t_on에서 끔), C_A 400 µF, 멈춘 모듈의 C_fly = V_bat/2\n' ...
    '버스: 배선 3 mΩ·1.5 µH, C_b 400 µF, RC 감쇠기 48.6 mΩ + 1.6 mF(E23·TB16과 같음). 해석기: 후진 오일러 2.5 ns(고정 비용, 모드 반복 3회)']), ...
    [30 yc+130 1400 yc+200], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
if ~exist(fullfile(here, 'results'), 'dir'), mkdir(fullfile(here, 'results')); end
sl_export_png({mdl, [mdl '/StageA_Module1'], [mdl '/Gate_StageA'], [mdl '/Test_Conditions']}, fullfile(here, 'results'));
end
