function build_TB02()
%BUILD_TB02  TB02 테스트벤치 모델(TB02_StageB_HBridge.slx)을 처음부터 만든다.
%
%   구성
%     링크 전압원 100 V ── StageB_HBridge(스위치 셀 4개, C_oss 포함) ── L_h ── 전류 센서 ── R_load ── V_set
%     Gate_StageB: Stage B 게이트 생성기(ctrl/prism_gate_stageB.m)의 H-브리지 부분(비교값 m 고정, DAB 출력 미사용)
%     Measurements: v_AB, i_h, 레그 A 노드 전압, 게이트 → Scope + To Workspace
%   실행: prism_run('build_TB02')  →  prism_run('run_TB02')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB02_StageB_HBridge';
run(fullfile(here, 'TB02_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');
sl_model_new(mdl, 'TB02_init.m');

sl_note(mdl, 'TB02 — Stage B H-브리지 + L_h 필터(개루프): 데드타임 전압오차와 교정표 대조', [30 10 900 40], 'title');
sl_note(mdl, sprintf(['검증 목적: 채택 제어기는 H-브리지 데드타임 전압오차를 전류별 교정표로 계산해 변조율에서 뺀다(κ 배).\n' ...
    '이 표가 실제 소자 회로(스위치 + 바디 다이오드 + 출력용량 1 nF)의 평균 전압오차와 같은지, 영전류 부근(부분 영전압 스위칭)부터\n' ...
    '대전류(하드 스위칭)까지 양·음 전류에서 확인한다. 게이트는 제어기와 같은 Stage B 게이트 생성기로 만든다.\n' ...
    '판정: 사례마다 |ΔV_회로 − ΔV_표| ≤ 0.1 V + 5 %%·|ΔV_표|  (ΔV = 평균 v_AB − 이상 평균값, 최대 오차 2V·t_d·f = 2 V)']), ...
    [30 50 1000 130], 'box');

% ---- 전력 회로 -------------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
gref = [fl 'Electrical Elements/Electrical Reference'];
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_link', [90 200 130 260], 'Orientation', 'down', 'v0', 'TB.Vlink');
sl_add(mdl, gref, 'GND', [90 300 130 330]);
sl_solver(mdl, 'Solver', [20 240 60 270], 'GND', 'V');
build_hbridge(mdl, 'StageB_HBridge', [220 170 400 330], 'TB.B');
sl_add(mdl, [fl 'Electrical Elements/Inductor'], 'L_h', [470 190 530 220], 'l', 'TB.B.Lh', 'r', 'TB.B.Rh', ...
    'i_L_specify', 'on', 'i_L', 'TB.i0', 'i_L_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_h', [570 185 620 225]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_load', [690 230 730 290], 'Orientation', 'down', 'R', 'TB.Rload');
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_set', [690 320 730 380], 'Orientation', 'down', 'v0', 'TB.Vset');
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_AB', [460 270 500 330], 'Orientation', 'down');

sl_pc(mdl, 'V_link', 'p', 'StageB_HBridge', 'LINK_P');
sl_pc(mdl, 'V_link', 'n', 'StageB_HBridge', 'LINK_N');
sl_pc(mdl, 'V_link', 'n', 'GND', 'V');
sl_pc(mdl, 'StageB_HBridge', 'A', 'L_h', 'p');
sl_pc(mdl, 'L_h', 'n', 'I_h', 'p');                 % i_h 양의 방향: 레그 A → L_h → 부하 → 레그 B
sl_pc(mdl, 'I_h', 'n', 'R_load', 'p');
sl_pc(mdl, 'R_load', 'n', 'V_set', 'p');
sl_pc(mdl, 'V_set', 'n', 'StageB_HBridge', 'B');
sl_pc(mdl, 'V_AB', 'p', 'StageB_HBridge', 'A');
sl_pc(mdl, 'V_AB', 'n', 'StageB_HBridge', 'B');
sl_meas(mdl, 'I_h', 'I', 'ih', [570 430]);
sl_meas(mdl, 'V_AB', 'V', 'vAB', [460 480]);
sl_note(mdl, sprintf('링크 100 V\n(이상 전압원)'), [40 350 200 380]);
sl_note(mdl, sprintf('부하: R_load 0.5 Ω + V_set\nV_set = m·V_link − i_목표·R_load'), [750 300 1000 340]);

% ---- 게이트 생성기 ---------------------------------------------------------------------------
gs = [mdl '/Gate_StageB'];
add_block('built-in/Subsystem', gs, 'Position', [220 520 400 580], 'BackgroundColor', 'yellow');
sl_add(gs, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', 'TB.dt');
sl_add(gs, 'simulink/Signal Routing/Goto', 't', [120 25 200 45], 'GotoTag', 't', 'TagVisibility', 'global');
sl_add(gs, 'simulink/Sources/Constant', 'uc_m_phase', [30 90 130 110], 'Value', '[TB.m; 0]');
sl_add(gs, 'simulink/Sources/Constant', 'ilink_meas', [30 140 130 160], 'Value', '0');
sl_add(gs, 'simulink/Sources/Constant', 'gate_prm',   [30 190 130 210], 'Value', 'TB.gate_prm');
sl_add(gs, 'simulink/Sources/Constant', 'gate_init',  [30 240 130 260], 'Value', 'TB.gate_init');
sl_mfunc(gs, 'StageB_Gate', [240 70 380 260], 'prism_gate_stageB.m');
sl_line(gs, 'Clock/1', 'StageB_Gate/1');
sl_line(gs, 'Clock/1', 't/1');
sl_line(gs, 'uc_m_phase/1', 'StageB_Gate/2');
sl_line(gs, 'ilink_meas/1', 'StageB_Gate/3');
sl_line(gs, 'gate_prm/1', 'StageB_Gate/4');
sl_line(gs, 'gate_init/1', 'StageB_Gate/5');
sl_add(gs, 'simulink/Signal Routing/Demux', 'Demux', [440 70 450 230], 'Outputs', '[1 1 1 1 8]');
sl_line(gs, 'StageB_Gate/1', 'Demux/1');
tags = {'gB_AH', 'gB_AL', 'gB_BH', 'gB_BL'};
for s = 1:4
    sl_add(gs, 'simulink/Signal Routing/Goto', tags{s}, [510 60+35*(s-1) 610 80+35*(s-1)], 'GotoTag', tags{s}, 'TagVisibility', 'global');
    sl_line(gs, sprintf('Demux/%d', s), [tags{s} '/1']);
end
sl_add(gs, 'simulink/Sinks/Terminator', 'DAB_gates_unused', [510 210 530 230]);
sl_line(gs, 'Demux/5', 'DAB_gates_unused/1');
sl_add(gs, 'simulink/Sinks/Terminator', 'aux_unused', [440 250 460 270]);
sl_line(gs, 'StageB_Gate/2', 'aux_unused/1');
sl_note(gs, sprintf(['Stage B 게이트 생성기(ctrl/prism_gate_stageB.m, 블록 안에 복사): 유니폴라 PWM, 반송파 200 kHz(표본 시점 최댓값)\n' ...
    '레그 A 상측 목표 = (m > c), 레그 B 상측 목표 = (−m > c). 목표가 바뀌면 두 소자를 끄고 50 ns 뒤 새 소자를 켠다.\n' ...
    '이 시험에서는 DAB 게이트 출력(5–12번)을 쓰지 않는다.']), [30 300 700 350], 'box');

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [880 170 1000 330], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_BridgeVoltage', {'vAB', 'vA_node'}; ...
     'Scope_FilterCurrent', {'ih'}; ...
     'Scope_GatesLegA', {'gB_AH', 'gB_AL'}}, ...
    {'t', 't'; 'vAB', 'vAB'; 'ih', 'ih'; 'vA_node', 'vA'; 'gB_AH', 'gAH'; 'gB_AL', 'gAL'});
sl_note(mdl, sprintf('계측: Scope 3개(브리지 전압, 필터전류, 레그 A 게이트)\n+ To Workspace(판정용)'), [860 350 1140 380]);

sl_note(mdl, sprintf(['파라미터(TB02_init.m → prism_hub_params.m)\n' ...
    'L_h 5 µH, R_h 2 mΩ, f_s 200 kHz, 데드타임 50 ns, C_oss 1 nF/소자, R_on 0.1 mΩ, 다이오드 Vf 1 mV\n' ...
    '사례 15개: m = 0.5에서 −60 … +60 A, m = 0.2·−0.5에서 ±20 A. 사례마다 30주기 계산, 마지막 10주기 평가']), ...
    [30 640 800 700], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
end
