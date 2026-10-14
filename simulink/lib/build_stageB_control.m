function build_stageB_control(sys, posCtrl, posGate, T)
%BUILD_STAGEB_CONTROL  Stage B 제어부 두 서브시스템(Controller_StageB, Gate_StageB)을 만든다.
%
%   build_stageB_control(sys, [x1 y1 x2 y2], [x1 y1 x2 y2], 'TB')
%
%   Controller_StageB
%     계측 태그(ip, vs, vbus, ih, vlink) → 시작 표본 보호(sl_startup_guard) + V_bat + 게이트 생성기 보조 출력
%     (링크전류 주기 평균, 두 반주기 중심 위상)
%     → 채택 제어기(ctrl/prism_ctrl_sampler.m + prism_stageB_controller.m, 5 µs마다 계산)
%     → 전달지연 Delay(T.delay_steps = 1000 간격 = 5 µs) → 태그 uc = [PWM 비교값; DAB 위상]
%     제어기 내부값은 태그 ctrl_dg = [m 지령; 링크전류 지령; 브리지 전류지령; ρ̂; ε̂; 예측 링크전류]
%   Gate_StageB
%     uc, 측정 링크전류(한 간격 지연, 시작 표본 보호) → 게이트 생성기(ctrl/prism_gate_stageB.m)
%     → 게이트 태그 gB_AH gB_AL gB_BH gB_BL(H-브리지), gD_P1–P4(DAB 1차), gD_S1–S4(DAB 2차)
%     보조 출력 태그 gate_aux = [링크전류 주기 평균; φ_c0; φ_c1; 반송파; 1차 상태; 2차 상태], 시각 태그 t
%   T : 시험 구조체 이름(문자열). 필드 dt vbat ctrl_prm ctrl_init ctrl_tab smp delay_steps uc0 gate_prm gate_init
%       guard_t(시작 표본 보호 시각) meas0([i_p v_s v_bus i_h v_link] 평형값)

% ======================= 제어기 ==========================================================
cs = [sys '/Controller_StageB'];
add_block('built-in/Subsystem', cs, 'Position', posCtrl, 'BackgroundColor', 'orange');
sl_add(cs, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', [T '.dt']);
tags = {'ip', 'vs', 'vbus', 'ih', 'vlink'};
for k = 1:5
    sl_add(cs, 'simulink/Signal Routing/From', ['meas_' tags{k}], [30 70+40*(k-1) 120 90+40*(k-1)], 'GotoTag', tags{k});
end
% 회로 측정값 5개 → 시작 표본 보호(t < 1.5 dt 동안 평형점 값) → 제어기 입력 벡터
sl_add(cs, 'simulink/Signal Routing/Mux', 'meas_mux', [150 65 155 255], 'Inputs', '5');
for k = 1:5, sl_line(cs, sprintf('meas_%s/1', tags{k}), sprintf('meas_mux/%d', k)); end
sl_startup_guard(cs, 'Startup_guard', [250 130 290 220], [T '.meas0'], T, [165 197 240 213]);
sl_line(cs, 'meas_mux/1', 'Startup_guard/1');
sl_line(cs, 'Clock/1', 'Startup_guard/2');
sl_add(cs, 'simulink/Sources/Constant', 'V_bat', [30 300 120 320], 'Value', [T '.vbat']);
sl_add(cs, 'simulink/Signal Routing/From', 'aux_from', [30 340 120 360], 'GotoTag', 'gate_aux');
sl_add(cs, 'simulink/Signal Routing/Demux', 'aux_split', [150 330 155 410], 'Outputs', '[1 1 1 3]');
sl_add(cs, 'simulink/Sinks/Terminator', 'aux_unused', [190 400 210 420]);
sl_add(cs, 'simulink/Signal Routing/Mux', 'y_mux', [330 60 335 200], 'Inputs', '5');   % [측정 5 | V_bat | 링크전류 평균 | φ_c0 | φ_c1]
sl_line(cs, 'Startup_guard/1', 'y_mux/1');
sl_line(cs, 'V_bat/1', 'y_mux/2');
sl_line(cs, 'aux_from/1', 'aux_split/1');
for k = 1:3, sl_line(cs, sprintf('aux_split/%d', k), sprintf('y_mux/%d', 2 + k)); end
sl_line(cs, 'aux_split/4', 'aux_unused/1');
sl_add(cs, 'simulink/Sources/Constant', 'ctrl_prm',  [350 167 440 187], 'Value', [T '.ctrl_prm']);
sl_add(cs, 'simulink/Sources/Constant', 'ctrl_init', [350 213 440 233], 'Value', [T '.ctrl_init']);
sl_add(cs, 'simulink/Sources/Constant', 'ctrl_tab',  [350 260 440 280], 'Value', [T '.ctrl_tab']);
sl_add(cs, 'simulink/Sources/Constant', 'smp',       [350 307 440 327], 'Value', [T '.smp']);
sl_mfunc(cs, 'Adopted_Controller', [460 60 640 340], {'prism_ctrl_sampler.m', 'prism_stageB_controller.m'});
sl_line(cs, 'Clock/1', 'Adopted_Controller/1');
sl_line(cs, 'y_mux/1', 'Adopted_Controller/2');
sl_line(cs, 'ctrl_prm/1', 'Adopted_Controller/3');
sl_line(cs, 'ctrl_init/1', 'Adopted_Controller/4');
sl_line(cs, 'ctrl_tab/1', 'Adopted_Controller/5');
sl_line(cs, 'smp/1', 'Adopted_Controller/6');
% 전달지연 5 µs: 지령 두 성분(PWM 비교값, DAB 위상)을 나눠 각각 1000 간격 지연한다
% (Delay 블록의 초기값을 성분마다 스칼라로 줄 수 있어, 첫 지령이 도착하기 전에는 평형점 값이 게이트에 들어간다)
sl_add(cs, 'simulink/Signal Routing/Demux', 'u_split', [680 85 685 165], 'Outputs', '2');
sl_line(cs, 'Adopted_Controller/1', 'u_split/1');
sl_add(cs, 'simulink/Discrete/Delay', 'Transport_delay_5us_m', [720 65 790 105], ...
    'DelayLength', [T '.delay_steps'], 'InitialCondition', [T '.uc0(1)'], 'SampleTime', '-1');
sl_add(cs, 'simulink/Discrete/Delay', 'Transport_delay_5us_phase', [720 145 790 185], ...
    'DelayLength', [T '.delay_steps'], 'InitialCondition', [T '.uc0(2)'], 'SampleTime', '-1');
sl_line(cs, 'u_split/1', 'Transport_delay_5us_m/1');
sl_line(cs, 'u_split/2', 'Transport_delay_5us_phase/1');
sl_add(cs, 'simulink/Signal Routing/Mux', 'u_join', [820 85 825 165], 'Inputs', '2');
sl_line(cs, 'Transport_delay_5us_m/1', 'u_join/1');
sl_line(cs, 'Transport_delay_5us_phase/1', 'u_join/2');
sl_add(cs, 'simulink/Signal Routing/Goto', 'uc', [860 115 940 135], 'GotoTag', 'uc', 'TagVisibility', 'global');
sl_line(cs, 'u_join/1', 'uc/1');
sl_add(cs, 'simulink/Signal Routing/Goto', 'ctrl_dg', [700 250 800 270], 'GotoTag', 'ctrl_dg', 'TagVisibility', 'global');
sl_line(cs, 'Adopted_Controller/2', 'ctrl_dg/1');
sl_note(cs, sprintf(['채택 제어기(5 µs마다, 반송파 최댓값 표본): 1주기 예측 → 상태궤환 + 버스전압 적분(전류지령 ±84 A) → 내부 전류 법칙(m ±0.95)\n' ...
    '→ 링크전압 PI(1 kHz) + 앞먹임 → DAB 위상(L −10 %% 기준 + ρ̂·ε̂ 보정) → H-브리지 데드타임 보상(κ 0.6 → 1.0).\n' ...
    '코드: ctrl/prism_ctrl_sampler.m + ctrl/prism_stageB_controller.m(블록 안에 복사). 계산 결과는 5 µs 뒤 게이트에 적용된다.']), ...
    [30 450 900 510], 'box');

% ======================= 게이트 생성기 =====================================================
gs = [sys '/Gate_StageB'];
add_block('built-in/Subsystem', gs, 'Position', posGate, 'BackgroundColor', 'yellow');
sl_add(gs, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', [T '.dt']);
sl_add(gs, 'simulink/Signal Routing/Goto', 't', [120 25 200 45], 'GotoTag', 't', 'TagVisibility', 'global');
sl_add(gs, 'simulink/Signal Routing/From', 'uc_from', [30 90 110 110], 'GotoTag', 'uc');
sl_add(gs, 'simulink/Signal Routing/From', 'ilink_from', [30 140 110 160], 'GotoTag', 'ilink');
sl_add(gs, 'simulink/Discrete/Unit Delay', 'ilink_z1', [140 135 170 165], 'SampleTime', [T '.dt']);
sl_add(gs, 'simulink/Sources/Constant', 'gate_prm',  [30 290 130 310], 'Value', [T '.gate_prm']);
sl_add(gs, 'simulink/Sources/Constant', 'gate_init', [30 330 130 350], 'Value', [T '.gate_init']);
sl_startup_guard(gs, 'Startup_guard', [190 125 220 215], [T '.gate_init(3)'], T, [60 190 160 210]);   % 링크전류 시작 표본 보호
sl_mfunc(gs, 'StageB_Gate', [260 60 400 280], 'prism_gate_stageB.m');
sl_line(gs, 'Clock/1', 't/1');
sl_line(gs, 'Clock/1', 'StageB_Gate/1');
sl_line(gs, 'uc_from/1', 'StageB_Gate/2');
sl_line(gs, 'ilink_from/1', 'ilink_z1/1');
sl_line(gs, 'ilink_z1/1', 'Startup_guard/1');
sl_line(gs, 'Clock/1', 'Startup_guard/2');
sl_line(gs, 'Startup_guard/1', 'StageB_Gate/3');
sl_line(gs, 'gate_prm/1', 'StageB_Gate/4');
sl_line(gs, 'gate_init/1', 'StageB_Gate/5');
sl_add(gs, 'simulink/Signal Routing/Demux', 'Demux', [460 50 470 380], 'Outputs', '12');
sl_line(gs, 'StageB_Gate/1', 'Demux/1');
gt = {'gB_AH', 'gB_AL', 'gB_BH', 'gB_BL', 'gD_P1', 'gD_P2', 'gD_P3', 'gD_P4', 'gD_S1', 'gD_S2', 'gD_S3', 'gD_S4'};
for s = 1:12
    sl_add(gs, 'simulink/Signal Routing/Goto', gt{s}, [520 48+27*(s-1) 610 64+27*(s-1)], 'GotoTag', gt{s}, 'TagVisibility', 'global', ...
        'ShowName', 'off');   % 태그 이름이 블록 안에 보이므로 블록 이름은 숨긴다(겹침 방지)
    sl_line(gs, sprintf('Demux/%d', s), [gt{s} '/1']);
end
sl_add(gs, 'simulink/Signal Routing/Goto', 'gate_aux', [460 400 560 420], 'GotoTag', 'gate_aux', 'TagVisibility', 'global');
sl_line(gs, 'StageB_Gate/2', 'gate_aux/1');
sl_note(gs, sprintf(['H-브리지: 유니폴라 PWM 200 kHz(반송파는 표본 시점에서 최댓값), 데드타임 50 ns.\n' ...
    'DAB: 반송파 반주기 중심에 대칭인 1·2차 에지(δ = φT/2π), 전이 반주기 평균 위상 갱신(직류 편류 방지), 데드타임 100 ns.\n' ...
    '링크전류 주기 평균을 표본 직전에 확정해 제어기의 ρ̂·ε̂ 추정에 넘긴다(aux). 코드: ctrl/prism_gate_stageB.m(블록 안에 복사)']), ...
    [30 450 800 510], 'box');
end
