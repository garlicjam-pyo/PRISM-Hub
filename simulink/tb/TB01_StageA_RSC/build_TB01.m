function build_TB01()
%BUILD_TB01  TB01 테스트벤치 모델(TB01_StageA_RSC.slx)을 처음부터 만든다.
%
%   구성
%     배터리(이상 전압원 788 V) ── StageA_Phase1(스위치 셀 4개 + L_r + C_fly) ── 출력전류 센서 ── C_out ∥ 전류 부하
%     Gate_StageA: 고정 타이밍 게이트 생성기(MATLAB Function, ctrl/prism_gate_stageA.m) → 전역 게이트 태그
%     Measurements: 계측 태그 → Scope 3개 + To Workspace(후처리용)
%   실행: prism_run('build_TB01')  →  prism_run('run_TB01')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB01_StageA_RSC';
run(fullfile(here, 'TB01_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');   % 같은 이름의 기존 .slx를 다시 만들 때의 경고
sl_model_new(mdl, 'TB01_init.m');

% ---- 제목·설명 -----------------------------------------------------------------------------
sl_note(mdl, 'TB01 — Stage A 1위상 2:1 공진 스위치드 커패시터(RSC), 고정 타이밍 f_s = 0.98·f_r0', [30 10 900 40], 'title');
sl_note(mdl, sprintf(['검증 목적: 소자 수준 회로(Simscape)에서 Stage A 한 위상의 공진 전류와 영전류 스위칭(ZCS) 품질이\n' ...
    '스위칭 ODE 검증 모델(E1 공칭 사례)과 같은지 확인한다.\n' ...
    '조건: 788 V 입력, 출력 46.875 A(375 A/8위상), C_out 400 µF, 데드타임 100 ns, 50주기 계산, 마지막 10주기 평가.\n' ...
    '판정: 피크·실효 전류 ±3 %%, 평균 출력전류 ±1 %%, 출력전압 ±0.5 V, C_fly 리플 ±5 %%, ZCS 비율 ±0.5 %%p(턴오프 순간 기준) (기준: ref/TB01_ref_python.json)']), ...
    [30 50 900 125], 'box');

% ---- 전력 회로 -------------------------------------------------------------------------------
% 접지는 소자마다 지역 접지 기호(Electrical Reference)로 둔다. 모두 같은 노드(GND)이며, 긴 접지 배선을 없애 회로도를 읽기 쉽게 한다.
fl = 'fl_lib/Electrical/';
gref = [fl 'Electrical Elements/Electrical Reference'];
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bat', [100 210 140 270], 'Orientation', 'down', 'v0', 'TB.vbat');
sl_add(mdl, gref, 'GND', [100 310 140 340]);
sl_solver(mdl, 'Solver', [30 250 70 280], 'GND', 'V');
build_stageA_phase(mdl, 'StageA_Phase1', [240 180 420 340], 1, 'TB.A');
sl_add(mdl, gref, 'GND_phase', [190 350 230 380]);
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_out', [480 235 530 275]);
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_out', [600 260 640 320], 'Orientation', 'down', ...
    'c', 'TB.Cout', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vout0', 'vc_priority', 'High');
sl_add(mdl, gref, 'GND_Cout', [600 350 640 380]);
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load', [700 260 740 320], 'Orientation', 'up');   % tail(위) = 출력 노드, head(아래) = GND
sl_add(mdl, gref, 'GND_load', [700 350 740 380]);
sl_add(mdl, 'simulink/Sources/Constant', 'Iload_ref', [620 190 680 210], 'Value', 'TB.Iload');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'Iload_PS', [700 190 730 210]);
sl_line(mdl, 'Iload_ref/1', 'Iload_PS/1');
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_out', [800 260 840 320], 'Orientation', 'down');
sl_add(mdl, gref, 'GND_vout', [800 350 840 380]);

sl_pc(mdl, 'V_bat', 'p', 'StageA_Phase1', 'VIN');
sl_pc(mdl, 'V_bat', 'n', 'GND', 'V');
sl_pc(mdl, 'StageA_Phase1', 'GND', 'GND_phase', 'V');
sl_pc(mdl, 'StageA_Phase1', 'VOUT', 'I_out', 'p');     % 위상 출력전류 i_o (위상 → 출력 노드)
sl_pc(mdl, 'I_out', 'n', 'C_out', 'p');
sl_pc(mdl, 'C_out', 'n', 'GND_Cout', 'V');
sl_pc(mdl, 'Iload_PS', 'output', 'I_load', 'iT');
sl_pc(mdl, 'I_load', 'tail', 'C_out', 'p');            % 부하 전류: 출력 노드 → 전류원 → GND
sl_pc(mdl, 'I_load', 'head', 'GND_load', 'V');
sl_pc(mdl, 'V_out', 'p', 'C_out', 'p');
sl_pc(mdl, 'V_out', 'n', 'GND_vout', 'V');
sl_meas(mdl, 'I_out', 'I', 'io',   [480 420]);
sl_meas(mdl, 'V_out', 'V', 'vout', [800 420]);
sl_note(mdl, sprintf('배터리 788 V\n(이상 전압원)'), [40 390 200 420]);
sl_note(mdl, sprintf('출력(V_A 노드): C_out 400 µF ∥ 부하 46.875 A(이상 전류 부하)'), [560 150 960 170]);

% ---- 게이트 생성기 ---------------------------------------------------------------------------
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
sl_note(gs, sprintf(['고정 타이밍 게이트: 전반주기 [t_d, T/2) S1·S3, 후반주기 [T/2+t_d, T) S2·S4\n' ...
    'T = 1/(0.98·f_r0), t_d = 100 ns. 코드: ctrl/prism_gate_stageA.m (블록 안에 복사됨)']), [30 270 620 310], 'box');

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [1000 190 1120 350], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_ResonantCurrent', {'iA_P1', 'gA_P1_S1', 'gA_P1_S2'}; ...
     'Scope_Voltages', {'vCf_P1', 'vout'}; ...
     'Scope_OutputCurrent', {'io'}}, ...
    {'t', 't'; 'iA_P1', 'iC'; 'vCf_P1', 'vC'; 'vout', 'vout'; 'io', 'io'; 'gA_P1_S1', 'g1'; 'gA_P1_S2', 'g2'});
sl_note(mdl, sprintf('계측: Scope 3개(공진전류·게이트, 전압, 출력전류)\n+ To Workspace(판정용)'), [980 390 1240 420]);

% ---- 파라미터 표 -------------------------------------------------------------------------------
sl_note(mdl, sprintf(['파라미터(TB01_init.m → prism_hub_params.m)\n' ...
    'C_fly 7.8125 µF, L_r 144.1 nH → f_r0 = 150.0 kHz, f_s = 147.0 kHz\n' ...
    'R_ds 6 mΩ(×2), ESR 1.5 mΩ, R_L 1 mΩ, R_misc 1.5 mΩ, 바디 다이오드 Vf 0.9 V\n' ...
    'Simscape 지역 해석기: 후진 오일러, 5 ns / Simulink: 고정 간격 이산, 5 ns']), [30 580 700 660], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
% 결선·파라미터 검사(모델 갱신). 오류가 있으면 여기서 멈춘다.
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
end
