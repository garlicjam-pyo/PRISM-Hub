function build_TB05()
%BUILD_TB05  TB05 테스트벤치 모델(TB05_StageC_CLLC.slx)을 처음부터 만든다.
%
%   구성
%     V_in 400 V(이상 전압원) ── 입력전류 센서 ── StageC_CLLC(1차 풀브리지 → C_r1·L_r1 → 25/3:1 변압기(L_m)
%     → L_r2·C_r2 → 정류 브리지 → C_o) ── 출력전류 센서 ── R_load(48²/P_o)
%     Gate_StageC: 250 kHz 고정, 50 % 상보 + 데드타임 50 ns → 게이트 태그 gC_Q1–gC_Q4
%     Measurements: Scope 3개 + To Workspace(판정용)
%   실행: prism_run('build_TB05')  →  prism_run('run_TB05')  (부하 3000, 1500, 300 W)

here = fileparts(mfilename('fullpath'));
mdl  = 'TB05_StageC_CLLC';
evalin('base', 'clear TB_override');
run(fullfile(here, 'TB05_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');
sl_model_new(mdl, 'TB05_init.m');

sl_note(mdl, 'TB05 — Stage C 대칭 CLLC(400 V → 48 V, 개루프): 고정이득·공진전류·영전압 스위칭', [30 10 1000 40], 'title');
sl_note(mdl, sprintf(['검증 목적: 공진점 고정 주파수(250 kHz)로 운전하는 대칭 CLLC가 부하와 무관하게 이득 ≈ 1(48 V)을 내고, 1차·2차 공진전류와\n' ...
    '자화 전류가 검증 모델(E10 스위칭 ODE)과 같으며, 1차 스위치가 데드타임 50 ns 안에 영전압 스위칭(ZVS)을 이루는지 확인한다.\n' ...
    '사례: 입력 400 V, 부하 3 kW(정격)·1.5 kW·0.3 kW, 공진망 0·출력 48 V에서 시작(검증 모델과 같음). 마지막 10주기로 판정.\n' ...
    '판정: 출력전압 검증 모델 ±0.3 V, 이득 1 ± 3 %%, 1차·2차 RMS 전류 ±3 %%, 자화 전류 첨두 ±5 %%, 스위칭 순간 전류 ±10 %%, 켜짐 직전 V_ds ≤ 5 %% V_in']), ...
    [30 50 1100 120], 'box');

% ---- 전력 회로 ----------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_in', [70 230 110 290], 'Orientation', 'down', 'v0', 'TB.Vin');
sl_add(mdl, [fl 'Electrical Elements/Electrical Reference'], 'GND', [70 440 110 470]);
sl_solver(mdl, 'Solver', [10 360 50 390], 'GND', 'V');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_in', [160 150 210 190]);
build_stageC(mdl, 'StageC_CLLC', [300 150 560 400], 'TB');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_o', [640 150 690 190]);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_load', [780 240 820 300], 'Orientation', 'down', 'R', 'TB.RL');
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_o', [870 240 910 300], 'Orientation', 'down');

sl_pc(mdl, 'V_in', 'n', 'GND', 'V');
sl_pc(mdl, 'V_in', 'p', 'I_in', 'p');                  % 입력전류 양의 방향: 전원 → Stage C
sl_pc(mdl, 'I_in', 'n', 'StageC_CLLC', 'DC_P');
sl_pc(mdl, 'StageC_CLLC', 'DC_N', 'GND', 'V');
sl_pc(mdl, 'StageC_CLLC', 'VO_P', 'I_o', 'p');          % 출력전류 양의 방향: Stage C → 부하
sl_pc(mdl, 'I_o', 'n', 'R_load', 'p');
sl_pc(mdl, 'R_load', 'n', 'StageC_CLLC', 'VO_N');
sl_pc(mdl, 'V_o', 'p', 'R_load', 'p');
sl_pc(mdl, 'V_o', 'n', 'R_load', 'n');
sl_meas(mdl, 'I_in', 'I', 'iin', [160 470]);
sl_meas(mdl, 'I_o',  'I', 'io',  [640 470]);
sl_meas(mdl, 'V_o',  'V', 'vo',  [870 470]);
sl_note(mdl, sprintf('400 V 보조버스\n(이상 전압원)'), [40 300 200 330]);
sl_note(mdl, sprintf('48 V 저전압 부하\nR_L = 48²/P_o (절연측)'), [760 320 960 350]);

% ---- 게이트 생성기 ---------------------------------------------------------------------------
gs = [mdl '/Gate_StageC'];
add_block('built-in/Subsystem', gs, 'Position', [300 560 480 620], 'BackgroundColor', 'yellow');
sl_add(gs, 'simulink/Sources/Digital Clock', 'Clock', [30 40 80 70], 'SampleTime', 'TB.dt');
sl_add(gs, 'simulink/Signal Routing/Goto', 't', [120 0 200 20], 'GotoTag', 't', 'TagVisibility', 'global');
sl_add(gs, 'simulink/Sources/Constant', 'gate_prm', [30 120 130 140], 'Value', 'TB.gate_prm');
sl_mfunc(gs, 'StageC_Gate', [180 40 320 150], 'prism_gate_stageC.m');
sl_line(gs, 'Clock/1', 't/1');
sl_line(gs, 'Clock/1', 'StageC_Gate/1');
sl_line(gs, 'gate_prm/1', 'StageC_Gate/2');
sl_add(gs, 'simulink/Signal Routing/Demux', 'Demux', [380 40 390 160], 'Outputs', '4');
sl_line(gs, 'StageC_Gate/1', 'Demux/1');
tags = {'gC_Q1', 'gC_Q2', 'gC_Q3', 'gC_Q4'};
for s = 1:4
    sl_add(gs, 'simulink/Signal Routing/Goto', tags{s}, [440 35+32*(s-1) 530 55+32*(s-1)], 'GotoTag', tags{s}, 'TagVisibility', 'global');
    sl_line(gs, sprintf('Demux/%d', s), [tags{s} '/1']);
end
sl_note(gs, sprintf(['Stage C 게이트: 주기 T = 4 µs(공진점 250 kHz), 전반주기 [t_d, T/2) Q1·Q4, 후반주기 [T/2 + t_d, T) Q2·Q3.\n' ...
    '데드타임 t_d = 50 ns 동안 공진전류가 레그 노드의 C_oss를 충방전해 다음 스위치가 영전압에서 켜진다.\n' ...
    '고정이득 구조이므로 폐루프 제어는 없다(출력전압은 400 V 버스를 Stage B가 조정해 간접적으로 맞춘다).']), ...
    [30 200 760 250], 'box');
sl_note(mdl, sprintf('게이트: Gate_StageC → 전역 태그 gC_Q1–gC_Q4'), [300 630 700 650]);

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [1040 150 1160 400], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_Output', {'vo', 'io'}; ...
     'Scope_Resonant', {'ir1', 'im', 'ir2'}; ...
     'Scope_Primary_leg', {'vleg1', 'vcr1', 'gC_Q1'}}, ...
    {'t', 't'; 'vo', 'vo'; 'io', 'io'; 'iin', 'iin'; 'ir1', 'ir1'; 'im', 'im'; 'ir2', 'ir2'; ...
     'vcr1', 'vcr1'; 'vleg1', 'vleg1'; 'gC_Q1', 'gq1'; 'gC_Q2', 'gq2'});
sl_note(mdl, sprintf('계측: Scope 3개(출력, 공진전류, 1차 레그)\n+ To Workspace(판정용)'), [1020 410 1300 440]);

sl_note(mdl, sprintf(['파라미터(TB05_init.m → prism_hub_params.m, 검증 모델 E10과 같은 설계값)\n' ...
    'n = 25/3, L_r1 11 µH, C_r1 36.8 nF(f_r = 250 kHz), L_m 66 µH, L_r2 = L_r1/n², C_r2 = C_r1·n², C_o 470 µF\n' ...
    '1차 스위치 R_on 5 mΩ, C_oss 100 pF, 데드타임 50 ns. 정류는 동기정류 근사(Vf 1 mV, R_on 0.1 mΩ)\n' ...
    '해석기: Simulink 고정 간격 이산 5 ns, Simscape 지역 해석기 후진 오일러 5 ns']), [30 700 900 770], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
end
