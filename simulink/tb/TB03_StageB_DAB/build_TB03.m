function build_TB03()
%BUILD_TB03  TB03 테스트벤치 모델(TB03_StageB_DAB.slx)을 처음부터 만든다.
%
%   구성
%     V_bus 400 V ── DAB_Primary(풀브리지) ── L_dab ── 이상 변압기 4:1 ── DAB_Secondary(풀브리지) ── 링크 전류 센서 ── V_link 100 V
%     Gate_StageB: Stage B 게이트 생성기의 DAB 부분(위상 계단 입력, 측정 링크전류의 주기 평균 출력)
%     Measurements: 누설 전류 i_L, 링크 직류전류, 브리지 전압, 위상 지령, 게이트 생성기 보조 출력
%   실행: prism_run('build_TB03')  →  prism_run('run_TB03')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB03_StageB_DAB';
run(fullfile(here, 'TB03_init.m'));
warning('off', 'Simulink:Engine:MdlFileShadowing');
sl_model_new(mdl, 'TB03_init.m');

sl_note(mdl, 'TB03 — Stage B 절연 DAB(개루프): 위상 계단 응답, 직류 편류, 데드타임 영역', [30 10 900 40], 'title');
sl_note(mdl, sprintf(['검증 목적: DAB 링크전류가 위상 앞먹임의 근거인 SPS 식을 따르는지, 위상을 바꿀 때 변압기 전류에 직류 편류가 생기지 않는지\n' ...
    '(게이트 생성기의 반주기 중심 대칭 에지 + 전이 반주기 평균 위상 갱신), E12에서 찾은 데드타임 영역(δ < 2t_d)이 회로에서도 나타나는지 확인한다.\n' ...
    '조건: V_bus 400 V, V_link 100 V(정합), 위상 0.4 → 0.8 → −0.5 → 0.15 → 0.08 rad(100 µs마다).\n' ...
    '기준: 검증 모델(E12 스위칭 ODE의 DAB 부분, ref/make_ref_TB03.py). 판정: SPS 영역(δ ≥ 2t_d) 정상 링크전류가 검증 모델 ±(1 A + 2 %%)·SPS 식 ±(1.5 A + 3 %%),\n' ...
    '부호 반전 직후 직류 편류 크기가 검증 모델 ±1 A, 정상 단계 편류 ≤ 0.5 A, 게이트 생성기 주기 평균 오차 ≤ 0.1 A. 데드타임 영역(δ < 2t_d)은 C_oss 민감도와 함께 정보로 기록']), ...
    [30 50 1050 130], 'box');

% ---- 전력 회로 -------------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
gref = [fl 'Electrical Elements/Electrical Reference'];
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_bus', [90 200 130 260], 'Orientation', 'down', 'v0', 'TB.Vbus');
sl_add(mdl, gref, 'GND', [90 300 130 330]);
sl_solver(mdl, 'Solver', [20 240 60 270], 'GND', 'V');
build_fullbridge(mdl, 'DAB_Primary', [200 170 360 330], 'TB.B', {'P1_leg1_high', 'P2_leg1_low', 'P3_leg2_high', 'P4_leg2_low'}, ...
    {'gD_P1', 'gD_P2', 'gD_P3', 'gD_P4'}, 'TB.B.Coss_d', ...
    sprintf('DAB 1차 풀브리지(400 V 버스 측): 50 %% 구형파, 상태 +1 → P1·P4, −1 → P2·P3\n데드타임 100 ns, C_oss 100 pF(수치 안정용)'));
sl_add(mdl, [fl 'Electrical Elements/Inductor'], 'L_dab', [420 190 480 220], 'l', 'TB.B.Ldab', 'r', 'TB.B.Rdab', ...
    'i_L_specify', 'on', 'i_L', '0', 'i_L_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_Ldab', [510 185 560 225]);
sl_add(mdl, [fl 'Electrical Elements/Ideal Transformer'], 'Xfmr_4to1', [600 210 660 290], 'n', 'TB.B.n');
build_fullbridge(mdl, 'DAB_Secondary', [880 170 1040 330], 'TB.B', {'S1_leg1_high', 'S2_leg1_low', 'S3_leg2_high', 'S4_leg2_low'}, ...
    {'gD_S1', 'gD_S2', 'gD_S3', 'gD_S4'}, 'TB.B.Coss_d', ...
    sprintf('DAB 2차 풀브리지(100 V 링크 측): 상태 +1 → S1·S4, −1 → S2·S3\n2차 에지 = 1차 에지 + δ (δ = φ·T/2π)'));
set_param([mdl '/DAB_Secondary'], 'Orientation', 'left');      % 직류 측(링크)을 오른쪽에 둔다
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_link', [1100 185 1150 225]);
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_link', [1200 230 1240 290], 'Orientation', 'down', 'v0', 'TB.Vlink');
sl_add(mdl, gref, 'GND_link', [1200 330 1240 360]);
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_pri', [420 270 460 330], 'Orientation', 'down');

sl_pc(mdl, 'V_bus', 'p', 'DAB_Primary', 'DC_P');
sl_pc(mdl, 'V_bus', 'n', 'DAB_Primary', 'DC_N');
sl_pc(mdl, 'V_bus', 'n', 'GND', 'V');
sl_pc(mdl, 'DAB_Primary', 'AC1', 'L_dab', 'p');
sl_pc(mdl, 'L_dab', 'n', 'I_Ldab', 'p');              % i_L 양의 방향: 1차 레그 1 → L_dab → 변압기 1+
sl_pc(mdl, 'I_Ldab', 'n', 'Xfmr_4to1', 'p1');
sl_pc(mdl, 'Xfmr_4to1', 'n1', 'DAB_Primary', 'AC2');
sl_pc(mdl, 'Xfmr_4to1', 'p2', 'DAB_Secondary', 'AC1');
sl_pc(mdl, 'Xfmr_4to1', 'n2', 'DAB_Secondary', 'AC2');
sl_pc(mdl, 'DAB_Secondary', 'DC_P', 'I_link', 'p');   % 링크 직류전류 양의 방향: 2차 브리지 → 링크(+)
sl_pc(mdl, 'I_link', 'n', 'V_link', 'p');
sl_pc(mdl, 'DAB_Secondary', 'DC_N', 'V_link', 'n');
sl_pc(mdl, 'V_link', 'n', 'GND_link', 'V');
sl_pc(mdl, 'V_pri', 'p', 'DAB_Primary', 'AC1');
sl_pc(mdl, 'V_pri', 'n', 'DAB_Primary', 'AC2');
sl_meas(mdl, 'I_Ldab', 'I', 'iL',    [510 430]);
sl_meas(mdl, 'I_link', 'I', 'ilink', [1100 430]);
sl_meas(mdl, 'V_pri',  'V', 'vpri',  [420 480]);
sl_note(mdl, sprintf('버스 400 V\n(이상 전압원)'), [40 350 200 380]);
sl_note(mdl, sprintf('링크 100 V\n(이상 전압원, 정합 V_bus = n·V_link)'), [1180 370 1400 400]);
sl_note(mdl, sprintf('누설 L_dab 11.1 µH\nR_dab 0.02 Ω'), [420 140 560 170]);

% ---- 게이트 생성기 ---------------------------------------------------------------------------
gs = [mdl '/Gate_StageB'];
add_block('built-in/Subsystem', gs, 'Position', [200 560 380 620], 'BackgroundColor', 'yellow');
sl_add(gs, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', 'TB.dt');
sl_add(gs, 'simulink/Signal Routing/Goto', 't', [120 25 200 45], 'GotoTag', 't', 'TagVisibility', 'global');
sl_add(gs, 'simulink/Lookup Tables/1-D Lookup Table', 'Phase_steps', [120 80 180 120], ...
    'Table', 'TB.ph_steps', 'BreakpointsForDimension1', 'TB.t_steps', 'InterpMethod', 'Flat', 'ExtrapMethod', 'Clip');
sl_add(gs, 'simulink/Sources/Constant', 'm_unused', [30 140 80 160], 'Value', '0');
sl_add(gs, 'simulink/Signal Routing/Mux', 'uc', [210 100 215 160], 'Inputs', '2');
sl_add(gs, 'simulink/Signal Routing/From', 'ilink_from', [30 190 110 210], 'GotoTag', 'ilink');
sl_add(gs, 'simulink/Discrete/Unit Delay', 'ilink_z1', [140 185 170 215], 'SampleTime', 'TB.dt');
sl_add(gs, 'simulink/Sources/Constant', 'gate_prm',  [30 240 130 260], 'Value', 'TB.gate_prm');
sl_add(gs, 'simulink/Sources/Constant', 'gate_init', [30 290 130 310], 'Value', 'TB.gate_init');
sl_mfunc(gs, 'StageB_Gate', [260 70 400 310], 'prism_gate_stageB.m');
sl_line(gs, 'Clock/1', 't/1');
sl_line(gs, 'Clock/1', 'Phase_steps/1');
sl_line(gs, 'Clock/1', 'StageB_Gate/1');
sl_line(gs, 'm_unused/1', 'uc/1');
sl_line(gs, 'Phase_steps/1', 'uc/2');
sl_line(gs, 'uc/1', 'StageB_Gate/2');
sl_line(gs, 'ilink_from/1', 'ilink_z1/1');
sl_line(gs, 'ilink_z1/1', 'StageB_Gate/3');
sl_line(gs, 'gate_prm/1', 'StageB_Gate/4');
sl_line(gs, 'gate_init/1', 'StageB_Gate/5');
sl_add(gs, 'simulink/Signal Routing/Goto', 'ph_cmd', [260 20 340 40], 'GotoTag', 'ph_cmd', 'TagVisibility', 'global');
sl_line(gs, 'Phase_steps/1', 'ph_cmd/1');
sl_add(gs, 'simulink/Signal Routing/Demux', 'Demux', [460 70 470 330], 'Outputs', '[4 1 1 1 1 1 1 1 1]');
sl_line(gs, 'StageB_Gate/1', 'Demux/1');
sl_add(gs, 'simulink/Sinks/Terminator', 'Hbridge_unused', [520 60 540 80]);
sl_line(gs, 'Demux/1', 'Hbridge_unused/1');
tags = {'gD_P1', 'gD_P2', 'gD_P3', 'gD_P4', 'gD_S1', 'gD_S2', 'gD_S3', 'gD_S4'};
for s = 1:8
    sl_add(gs, 'simulink/Signal Routing/Goto', tags{s}, [520 95+28*(s-1) 610 113+28*(s-1)], 'GotoTag', tags{s}, 'TagVisibility', 'global');
    sl_line(gs, sprintf('Demux/%d', s + 1), [tags{s} '/1']);
end
sl_add(gs, 'simulink/Signal Routing/Goto', 'gate_aux', [460 350 560 370], 'GotoTag', 'gate_aux', 'TagVisibility', 'global');
sl_line(gs, 'StageB_Gate/2', 'gate_aux/1');
sl_note(gs, sprintf(['DAB 에지: 반송파 반주기 중심 c_j에 대칭(1차 c_j − δ/2, 2차 c_j + δ/2). 지령은 도착 후 첫 반주기 중심에서 반영하고,\n' ...
    '전이 반주기의 위상차를 이전·새 위상의 평균으로 둔다(A ← −A + 2Δ) → 직류 편류 없음. 링크전류는 주기 평균을 표본 직전에 확정(aux 1).\n' ...
    '측정 링크전류는 대수 루프를 피하려고 한 간격(5 ns) 지연해 넣는다. H-브리지 게이트(1–4번)는 이 시험에서 쓰지 않는다.']), ...
    [30 390 760 450], 'box');

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [1300 170 1420 330], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_DAB_current', {'iL', 'ilink'}; ...
     'Scope_Phase', {'ph_cmd'}; ...
     'Scope_Primary_voltage', {'vpri'}}, ...
    {'t', 't'; 'iL', 'iL'; 'ilink', 'ilink'; 'vpri', 'vpri'; 'ph_cmd', 'ph'; 'gate_aux', 'aux'});
sl_note(mdl, sprintf('계측: Scope 3개 + To Workspace(판정용)'), [1320 345 1560 365]);

sl_note(mdl, sprintf(['파라미터(TB03_init.m → prism_hub_params.m)\n' ...
    'n = 4, f_s 200 kHz, L_dab 11.1 µH, R_dab 0.02 Ω, 데드타임 100 ns, R_on 0.1 mΩ, C_oss 100 pF\n' ...
    'SPS 링크전류 I = n·V_bus·φ(1 − |φ|/π)/(2π f_s L_dab), k = 114.7 A/rad']), [30 680 800 740], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
end
