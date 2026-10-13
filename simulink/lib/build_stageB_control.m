function build_stageB_control(sys, posCtrl, posGate, T)
%BUILD_STAGEB_CONTROL  Stage B 제어부 두 서브시스템(Controller_StageB, Gate_StageB)을 만든다.
%
%   build_stageB_control(sys, [x1 y1 x2 y2], [x1 y1 x2 y2], 'TB')
%
%   Controller_StageB
%     계측 태그(ip, vs, vbus, ih, vlink) + V_bat + 게이트 생성기 보조 출력(링크전류 주기 평균, 두 반주기 중심 위상)
%     → 채택 제어기(ctrl/prism_ctrl_sampler.m + prism_stageB_controller.m, 5 µs마다 계산)
%     → 전달지연 Delay(T.delay_steps = 1000 간격 = 5 µs) → 태그 uc = [PWM 비교값; DAB 위상]
%     제어기 내부값은 태그 ctrl_dg = [m 지령; 링크전류 지령; 브리지 전류지령; ρ̂; ε̂; 예측 링크전류]
%   Gate_StageB
%     uc, 측정 링크전류(한 간격 지연) → 게이트 생성기(ctrl/prism_gate_stageB.m)
%     → 게이트 태그 gB_AH gB_AL gB_BH gB_BL(H-브리지), gD_P1–P4(DAB 1차), gD_S1–S4(DAB 2차)
%     보조 출력 태그 gate_aux = [링크전류 주기 평균; φ_c0; φ_c1; 반송파; 1차 상태; 2차 상태], 시각 태그 t
%   T : 시험 구조체 이름(문자열). 필드 dt vbat ctrl_prm ctrl_init ctrl_tab smp delay_steps uc0 gate_prm gate_init

% ======================= 제어기 ==========================================================
cs = [sys '/Controller_StageB'];
add_block('built-in/Subsystem', cs, 'Position', posCtrl, 'BackgroundColor', 'orange');
sl_add(cs, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', [T '.dt']);
tags = {'ip', 'vs', 'vbus', 'ih', 'vlink'};
for k = 1:5
    sl_add(cs, 'simulink/Signal Routing/From', ['meas_' tags{k}], [30 70+30*(k-1) 120 90+30*(k-1)], 'GotoTag', tags{k});
end
sl_add(cs, 'simulink/Sources/Constant', 'V_bat', [30 220 120 240], 'Value', [T '.vbat']);
sl_add(cs, 'simulink/Signal Routing/From', 'aux_from', [30 260 120 280], 'GotoTag', 'gate_aux');
sl_add(cs, 'simulink/Signal Routing/Demux', 'aux_split', [150 250 155 330], 'Outputs', '[1 1 1 3]');
sl_add(cs, 'simulink/Sinks/Terminator', 'aux_unused', [190 320 210 340]);
sl_add(cs, 'simulink/Signal Routing/Mux', 'y_mux', [260 60 265 330], 'Inputs', '9');
for k = 1:5, sl_line(cs, sprintf('meas_%s/1', tags{k}), sprintf('y_mux/%d', k)); end
sl_line(cs, 'V_bat/1', 'y_mux/6');
sl_line(cs, 'aux_from/1', 'aux_split/1');
for k = 1:3, sl_line(cs, sprintf('aux_split/%d', k), sprintf('y_mux/%d', 6 + k)); end
sl_line(cs, 'aux_split/4', 'aux_unused/1');
sl_add(cs, 'simulink/Sources/Constant', 'ctrl_prm',  [300 360 400 380], 'Value', [T '.ctrl_prm']);
sl_add(cs, 'simulink/Sources/Constant', 'ctrl_init', [300 400 400 420], 'Value', [T '.ctrl_init']);
sl_add(cs, 'simulink/Sources/Constant', 'ctrl_tab',  [300 440 400 460], 'Value', [T '.ctrl_tab']);
sl_add(cs, 'simulink/Sources/Constant', 'smp',       [300 480 400 500], 'Value', [T '.smp']);
sl_mfunc(cs, 'Adopted_Controller', [460 60 640 340], {'prism_ctrl_sampler.m', 'prism_stageB_controller.m'});
sl_line(cs, 'Clock/1', 'Adopted_Controller/1');
sl_line(cs, 'y_mux/1', 'Adopted_Controller/2');
sl_line(cs, 'ctrl_prm/1', 'Adopted_Controller/3');
sl_line(cs, 'ctrl_init/1', 'Adopted_Controller/4');
sl_line(cs, 'ctrl_tab/1', 'Adopted_Controller/5');
sl_line(cs, 'smp/1', 'Adopted_Controller/6');
sl_add(cs, 'simulink/Discrete/Delay', 'Transport_delay_5us', [700 100 760 150], ...
    'DelayLength', [T '.delay_steps'], 'InitialCondition', [T '.uc0'], 'SampleTime', '-1');
sl_line(cs, 'Adopted_Controller/1', 'Transport_delay_5us/1');
sl_add(cs, 'simulink/Signal Routing/Goto', 'uc', [800 115 880 135], 'GotoTag', 'uc', 'TagVisibility', 'global');
sl_line(cs, 'Transport_delay_5us/1', 'uc/1');
sl_add(cs, 'simulink/Signal Routing/Goto', 'ctrl_dg', [700 250 800 270], 'GotoTag', 'ctrl_dg', 'TagVisibility', 'global');
sl_line(cs, 'Adopted_Controller/2', 'ctrl_dg/1');
sl_note(cs, sprintf(['채택 제어기(5 µs마다, 반송파 최댓값 표본): 1주기 예측 → 상태궤환 + 버스전압 적분(전류지령 ±84 A) → 내부 전류 법칙(m ±0.95)\n' ...
    '→ 링크전압 PI(1 kHz) + 앞먹임 → DAB 위상(L −10 %% 기준 + ρ̂·ε̂ 보정) → H-브리지 데드타임 보상(κ 0.6 → 1.0).\n' ...
    '코드: ctrl/prism_ctrl_sampler.m + ctrl/prism_stageB_controller.m(블록 안에 복사). 계산 결과는 5 µs 뒤 게이트에 적용된다.']), ...
    [30 530 900 590], 'box');

% ======================= 게이트 생성기 =====================================================
gs = [sys '/Gate_StageB'];
add_block('built-in/Subsystem', gs, 'Position', posGate, 'BackgroundColor', 'yellow');
sl_add(gs, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', [T '.dt']);
sl_add(gs, 'simulink/Signal Routing/Goto', 't', [120 25 200 45], 'GotoTag', 't', 'TagVisibility', 'global');
sl_add(gs, 'simulink/Signal Routing/From', 'uc_from', [30 90 110 110], 'GotoTag', 'uc');
sl_add(gs, 'simulink/Signal Routing/From', 'ilink_from', [30 140 110 160], 'GotoTag', 'ilink');
sl_add(gs, 'simulink/Discrete/Unit Delay', 'ilink_z1', [140 135 170 165], 'SampleTime', [T '.dt']);
sl_add(gs, 'simulink/Sources/Constant', 'gate_prm',  [30 190 130 210], 'Value', [T '.gate_prm']);
sl_add(gs, 'simulink/Sources/Constant', 'gate_init', [30 240 130 260], 'Value', [T '.gate_init']);
sl_mfunc(gs, 'StageB_Gate', [260 60 400 280], 'prism_gate_stageB.m');
sl_line(gs, 'Clock/1', 't/1');
sl_line(gs, 'Clock/1', 'StageB_Gate/1');
sl_line(gs, 'uc_from/1', 'StageB_Gate/2');
sl_line(gs, 'ilink_from/1', 'ilink_z1/1');
sl_line(gs, 'ilink_z1/1', 'StageB_Gate/3');
sl_line(gs, 'gate_prm/1', 'StageB_Gate/4');
sl_line(gs, 'gate_init/1', 'StageB_Gate/5');
sl_add(gs, 'simulink/Signal Routing/Demux', 'Demux', [460 50 470 380], 'Outputs', '12');
sl_line(gs, 'StageB_Gate/1', 'Demux/1');
gt = {'gB_AH', 'gB_AL', 'gB_BH', 'gB_BL', 'gD_P1', 'gD_P2', 'gD_P3', 'gD_P4', 'gD_S1', 'gD_S2', 'gD_S3', 'gD_S4'};
for s = 1:12
    sl_add(gs, 'simulink/Signal Routing/Goto', gt{s}, [520 48+27*(s-1) 610 64+27*(s-1)], 'GotoTag', gt{s}, 'TagVisibility', 'global');
    sl_line(gs, sprintf('Demux/%d', s), [gt{s} '/1']);
end
sl_add(gs, 'simulink/Signal Routing/Goto', 'gate_aux', [460 400 560 420], 'GotoTag', 'gate_aux', 'TagVisibility', 'global');
sl_line(gs, 'StageB_Gate/2', 'gate_aux/1');
sl_note(gs, sprintf(['H-브리지: 유니폴라 PWM 200 kHz(반송파는 표본 시점에서 최댓값), 데드타임 50 ns.\n' ...
    'DAB: 반송파 반주기 중심에 대칭인 1·2차 에지(δ = φT/2π), 전이 반주기 평균 위상 갱신(직류 편류 방지), 데드타임 100 ns.\n' ...
    '링크전류 주기 평균을 표본 직전에 확정해 제어기의 ρ̂·ε̂ 추정에 넘긴다(aux). 코드: ctrl/prism_gate_stageB.m(블록 안에 복사)']), ...
    [30 450 800 510], 'box');
end
