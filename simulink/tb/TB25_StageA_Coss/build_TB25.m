function build_TB25()
%BUILD_TB25  TB25 테스트벤치 모델(TB25_StageA_Coss.slx)을 처음부터 만든다.
%
%   TB01 회로에 두 가지를 더했다: (1) 스위치 셀마다 출력용량 C_oss(파라미터 TB.A.Coss, 사례마다 값만 바꾼다),
%   (2) 배터리 전류 센서(입력 전력 계산용). 손실 = 입력 전력 − 출력 노드로 간 전력 − 저장 에너지 변화.
%   실행: prism_run('build_TB25')  →  prism_run('smoke_TB25')  →  prism_run('run_TB25')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB25_StageA_Coss';
run(fullfile(here, 'TB25_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');
sl_model_new(mdl, 'TB25_init.m');

sl_note(mdl, 'TB25 — Stage A 1위상 RSC + 스위치 출력용량: 영전류 스위칭에서의 하드 스위칭 출력용량 손실', [30 10 980 40], 'title');
sl_note(mdl, sprintf(['검증 목적: 영전류(ZCS)로 끄는 Stage A는 데드타임에 전류가 없어 노드 전압(V_bat/2)을 옮기지 못하고,\n' ...
    '다음 스위치가 켜질 때 출력용량을 하드 스위칭으로 충·방전한다. 위상당 손실 4·Q_oss·V·f_s(선형 C면 4·C·V²·f_s)를 회로에서 확인한다(E31).\n' ...
    '사례: 원설계(150 kHz)와 E31 선택안, 무부하·46.875 A, 출력용량 있음·없음. 손실 = 입력 전력 − 출력 노드 전력 − 저장 에너지 변화.\n' ...
    '판정: T1 무부하 출력용량 손실이 4·C·V²·f와 5 %% 안, T2 46.875 A 손실이 정확해(행렬 지수)와 5 %% 안, T3 출력용량 없는 손실이 E1 모델과 3 %% 안.']), ...
    [30 50 980 125], 'box');

fl = 'fl_lib/Electrical/';
gref = [fl 'Electrical Elements/Electrical Reference'];
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bat', [100 210 140 270], 'Orientation', 'down', 'v0', 'TB.vbat');
sl_add(mdl, gref, 'GND', [100 310 140 340]);
sl_solver(mdl, 'Solver', [30 250 70 280], 'GND', 'V');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_in', [160 150 200 190]);
build_stageA_phase(mdl, 'StageA_Phase1', [240 180 420 340], 1, 'TB.A', 'TB.A.Coss');
sl_add(mdl, gref, 'GND_phase', [190 350 230 380]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_out', [480 235 530 275]);
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_out', [600 260 640 320], 'Orientation', 'down', ...
    'c', 'TB.Cout', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vout0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_Cout', [600 350 640 380]);
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load', [700 260 740 320], 'Orientation', 'up');
sl_add(mdl, gref, 'GND_load', [700 350 740 380]);
sl_add(mdl, 'simulink/Sources/Constant', 'Iload_ref', [620 190 680 210], 'Value', 'TB.Iload');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'Iload_PS', [700 190 730 210]);
sl_line(mdl, 'Iload_ref/1', 'Iload_PS/1');
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_out', [800 260 840 320], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_vout', [800 350 840 380]);

sl_pc(mdl, 'V_bat', 'p', 'I_in', 'p');
sl_pc(mdl, 'I_in', 'n', 'StageA_Phase1', 'VIN');       % 배터리 전류 i_in (배터리 → 위상)
sl_pc(mdl, 'V_bat', 'n', 'GND', 'V');
sl_pc(mdl, 'StageA_Phase1', 'GND', 'GND_phase', 'V');
sl_pc(mdl, 'StageA_Phase1', 'VOUT', 'I_out', 'p');
sl_pc(mdl, 'I_out', 'n', 'C_out', 'p');
sl_pc(mdl, 'C_out', 'n', 'GND_Cout', 'V');
sl_pc(mdl, 'Iload_PS', 'output', 'I_load', 'iT');
sl_pc(mdl, 'I_load', 'tail', 'C_out', 'p');
sl_pc(mdl, 'I_load', 'head', 'GND_load', 'V');
sl_pc(mdl, 'V_out', 'p', 'C_out', 'p');
sl_pc(mdl, 'V_out', 'n', 'GND_vout', 'V');
sl_meas(mdl, 'I_in', 'I', 'iin', [160 420]);
sl_meas(mdl, 'I_out', 'I', 'io',   [480 420]);
sl_meas(mdl, 'V_out', 'V', 'vout', [800 420]);
sl_note(mdl, sprintf('배터리 800 V(이상 전압원)\n+ 입력 전류 센서'), [40 390 220 420]);
sl_note(mdl, sprintf('출력(V_A 노드): C_out 400 µF ∥ 부하(사례: 0 또는 46.875 A)'), [560 150 960 170]);

gs = [mdl '/Gate_StageA'];
add_block('built-in/Subsystem', gs, 'Position', [240 480 420 540], 'BackgroundColor', 'yellow');
sl_add(gs, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', 'TB.dt');
sl_add(gs, 'simulink/Sources/Constant', 'gate_prm', [30 100 110 120], 'Value', 'TB.gate_prm');
sl_add(gs, 'simulink/Sources/Constant', 'gate_en',  [30 150 110 170], 'Value', 'TB.gate_en');
sl_add(gs, 'simulink/Sources/Constant', 'gate_off', [30 200 110 220], 'Value', 'TB.gate_off');
sl_mfunc(gs, 'StageA_Gate', [240 70 380 230], 'prism_gate_stageA.m');
sl_line(gs, 'Clock/1', 'StageA_Gate/1');
sl_line(gs, 'gate_prm/1', 'StageA_Gate/2');
sl_line(gs, 'gate_en/1', 'StageA_Gate/3');
sl_line(gs, 'gate_off/1', 'StageA_Gate/4');
sl_add(gs, 'simulink/Signal Routing/Demux', 'Demux', [440 70 450 230], 'Outputs', '[1 1 1 1 28]');
sl_line(gs, 'StageA_Gate/1', 'Demux/1');
for s = 1:4
    tag = sprintf('gA_P1_S%d', s);
    sl_add(gs, 'simulink/Signal Routing/Goto', tag, [510 60+35*(s-1) 620 80+35*(s-1)], 'GotoTag', tag, 'TagVisibility', 'global');
    sl_line(gs, sprintf('Demux/%d', s), [tag '/1']);
end
sl_add(gs, 'simulink/Sinks/Terminator', 'unused_phases', [510 210 530 230]);
sl_line(gs, 'Demux/5', 'unused_phases/1');
sl_add(gs, 'simulink/Signal Routing/Goto', 't', [120 25 200 45], 'GotoTag', 't', 'TagVisibility', 'global');
sl_line(gs, 'Clock/1', 't/1');
sl_note(gs, sprintf(['고정 타이밍 게이트(TB01과 같음): 전반주기 [t_d, T/2) S1·S3, 후반주기 [T/2+t_d, T) S2·S4\n' ...
    'T = 1/(0.98·f_r)(사례의 L_r·C_fly로 정함), t_d = 100 ns. 코드: ctrl/prism_gate_stageA.m']), [30 270 620 310], 'box');

ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [1000 190 1120 350], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_ResonantCurrent', {'iA_P1', 'gA_P1_S1', 'gA_P1_S2'}; ...
     'Scope_Voltages', {'vCf_P1', 'vout'}; ...
     'Scope_Currents', {'iin', 'io'}}, ...
    {'t', 't'; 'iA_P1', 'iC'; 'vCf_P1', 'vC'; 'vout', 'vout'; 'io', 'io'; 'iin', 'iin'; 'gA_P1_S1', 'g1'; 'gA_P1_S2', 'g2'});
sl_note(mdl, sprintf('계측: Scope 3개 + To Workspace(판정용)\n손실 = V_bat·mean(i_in) − mean(v_out·i_o) − ΔE/Δt'), [980 390 1290 420]);
sl_note(mdl, sprintf(['파라미터(TB25_init.m, 사례 ref/TB25_cases.json)\n' ...
    'L_r·C_fly·R_ds·C_oss는 사례 값(원설계: 144.1 nH·7.8125 µF·6 mΩ). 경로 저항 = 2·R_ds + 4 mΩ\n' ...
    '스위치 셀: 이상 스위치 + 바디 다이오드(Vf 0.9 V) + 출력용량 C_oss(등가 선형)\n' ...
    'Simscape 지역 해석기: 후진 오일러, 2.5 ns / Simulink: 고정 간격 이산, 2.5 ns']), [30 580 760 660], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
end
