function build_stageB_control(sys, posCtrl, posGate, T, opt)
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
%   opt.r2 = true (선택, TB08 R2 창 조정 모듈)
%     Controller_StageB에 모드 시퀀서(ctrl/prism_r2_sequence.m, 상수 T.seq_prm)를 더한다. 출력 [V_ref; 재초기화; 모드]는
%     태그 r2_seq로 내보내고, V_ref·재초기화는 제어기 입력 y(10)·y(11)로 넣는다(ctrl/prism_ctrl_sampler_r2.m).
%     Gate_StageB에는 게이트 재정의(ctrl/prism_r2_gate.m)를 넣어 모드에 따라 DAB 정지·영벡터·바이패스를 만들고,
%     바이패스 게이트를 태그 gByp로 내보낸다. opt를 주지 않으면 이전과 같은 모델을 만든다.
%   opt.r2b = true (선택, TB09 R2 보호 상태기계)
%     시퀀서 대신 R2_Supervisor(ctrl/prism_r2_sup_sampler.m + prism_r2_supervisor.m, 상수 T.sup_prm)를 넣고, 지령 12개를
%     태그 r2_sup로 내보낸다. 제어기는 ctrl/prism_ctrl_sampler_r2b.m. Gate_StageB에는 보호 게이트 재정의
%     (ctrl/prism_r2_gate_b.m, 상수 T.prot_prm)를 넣어 게이트 14개(gByp, gBrk 포함)와 고장 신호 r2_flags를 낸다.

if nargin < 5, opt = struct(); end
r2c = isfield(opt, 'r2c') && opt.r2c;          % (TB10) r2b + DAB 고장 모드 변조(EPS) 게이트
r2b = (isfield(opt, 'r2b') && opt.r2b) || r2c;  % (TB09) 측정 기반 보호 상태기계(시퀀서 대신)
r2 = (isfield(opt, 'r2') && opt.r2) || r2b;
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
if r2b  % [측정 5 | V_bat | 링크전류 평균 | φ_c0 | φ_c1 | V_ref | 재초기화 | 브리지 모드 | 조향 m | DAB 모드 | 보조 지령]
    sl_add(cs, 'simulink/Signal Routing/Mux', 'y_mux', [330 60 335 300], 'Inputs', '11');
elseif r2   % [측정 5 | V_bat | 링크전류 평균 | φ_c0 | φ_c1 | V_ref | 재초기화]
    sl_add(cs, 'simulink/Signal Routing/Mux', 'y_mux', [330 60 335 240], 'Inputs', '7');
else    % [측정 5 | V_bat | 링크전류 평균 | φ_c0 | φ_c1]
    sl_add(cs, 'simulink/Signal Routing/Mux', 'y_mux', [330 60 335 200], 'Inputs', '5');
end
sl_line(cs, 'Startup_guard/1', 'y_mux/1');
sl_line(cs, 'V_bat/1', 'y_mux/2');
sl_line(cs, 'aux_from/1', 'aux_split/1');
for k = 1:3, sl_line(cs, sprintf('aux_split/%d', k), sprintf('y_mux/%d', 2 + k)); end
sl_line(cs, 'aux_split/4', 'aux_unused/1');
sl_add(cs, 'simulink/Sources/Constant', 'ctrl_prm',  [350 167 440 187], 'Value', [T '.ctrl_prm']);
sl_add(cs, 'simulink/Sources/Constant', 'ctrl_init', [350 213 440 233], 'Value', [T '.ctrl_init']);
sl_add(cs, 'simulink/Sources/Constant', 'ctrl_tab',  [350 260 440 280], 'Value', [T '.ctrl_tab']);
sl_add(cs, 'simulink/Sources/Constant', 'smp',       [350 307 440 327], 'Value', [T '.smp']);
if r2b
    % 보호 상태기계: 측정값·고장 신호로 운전 상태를 정하고 지령 12개를 낸다(태그 r2_sup → 게이트 재정의·부하·바이패스)
    set_param([cs '/aux_unused'], 'ShowName', 'off');
    sl_add(cs, 'simulink/Sources/Digital Clock', 'Clock_sup', [30 480 80 510], 'SampleTime', [T '.dt']);
    sl_add(cs, 'simulink/Signal Routing/From', 'flags_from', [30 525 110 545], 'GotoTag', 'r2_flags');
    sl_add(cs, 'simulink/Sources/Constant', 'sup_prm', [30 560 130 580], 'Value', [T '.sup_prm']);
    sl_add(cs, 'simulink/Sources/Constant', 'sup_smp', [30 595 130 615], 'Value', [T '.smp']);
    sl_mfunc(cs, 'R2_Supervisor', [170 470 290 625], {'prism_r2_sup_sampler.m', 'prism_r2_supervisor.m'});
    sl_line(cs, 'Clock_sup/1', 'R2_Supervisor/1');
    sl_add(cs, 'simulink/Discrete/Unit Delay', 'sup_meas_z1', [120 440 150 465], 'SampleTime', [T '.dt'], ...
        'InitialCondition', [T '.meas0''']);                          % 회로 ↔ 상태기계 대수 루프 방지(한 간격 지연)
    sl_add(cs, 'simulink/Signal Routing/Goto', 'meas_g', [255 108 305 124], 'GotoTag', 'meas_g', 'ShowName', 'off', ...
        'Orientation', 'left');                                     % 기동 보호 위(입력이 오른쪽을 향하게)
    sl_add(cs, 'simulink/Signal Routing/From', 'meas_g_from', [30 442 100 462], 'GotoTag', 'meas_g', 'ShowName', 'off');
    sl_line(cs, 'Startup_guard/1', 'meas_g/1');                     % 측정값(기동 보호 뒤)을 지역 태그로 넘겨 긴 배선을 피한다
    sl_line(cs, 'meas_g_from/1', 'sup_meas_z1/1');
    sl_line(cs, 'sup_meas_z1/1', 'R2_Supervisor/2');
    sl_line(cs, 'flags_from/1', 'R2_Supervisor/3');
    sl_line(cs, 'sup_prm/1', 'R2_Supervisor/4');
    sl_line(cs, 'sup_smp/1', 'R2_Supervisor/5');
    sl_add(cs, 'simulink/Signal Routing/Goto', 'r2_sup', [330 640 410 660], 'GotoTag', 'r2_sup', 'TagVisibility', 'global');
    sl_line(cs, 'R2_Supervisor/1', 'r2_sup/1');
    sl_add(cs, 'simulink/Signal Routing/Demux', 'sup_split', [320 470 325 625], 'Outputs', '[1 1 1 1 1 1 6]');
    sl_line(cs, 'R2_Supervisor/1', 'sup_split/1');
    sl_add(cs, 'simulink/Sinks/Terminator', 'sup_rest', [345 605 365 625], 'ShowName', 'off');
    for k = 1:6, sl_line(cs, sprintf('sup_split/%d', k), sprintf('y_mux/%d', 5 + k)); end
    sl_line(cs, 'sup_split/7', 'sup_rest/1');
    sl_mfunc(cs, 'Adopted_Controller', [460 60 640 340], {'prism_ctrl_sampler_r2b.m', 'prism_stageB_controller.m'});
    sl_note(cs, sprintf(['R2 보호 상태기계(TB09): R2_Supervisor가 5 µs마다 측정값·고장 신호(r2_flags)로 상태를 정한다(ctrl/prism_r2_supervisor.m,\n' ...
        '검증 코드 E17과 같은 논리). 지령: V_ref, 재초기화, 브리지 모드, 조향 변조율, DAB 모드, 보조 링크전류 지령(→ 제어기),\n' ...
        '바이패스 소프트 저항·주 스위치, 제동 저항, 400 V 부하 분리, 상태 번호, 검출 원인(→ 태그 r2_sup)']), [460 380 1150 440], 'box');
elseif r2
    % 모드 시퀀서: 시각표에 따른 버스 기준전압 램프·제어기 재초기화·운전 모드(태그 r2_seq → 게이트 재정의)
    set_param([cs '/aux_unused'], 'ShowName', 'off');              % 종단 블록 이름은 숨긴다(아래 모드 시퀀서와 겹침 방지)
    sl_add(cs, 'simulink/Sources/Digital Clock', 'Clock_seq', [30 480 80 510], 'SampleTime', [T '.dt']);
    sl_add(cs, 'simulink/Sources/Constant', 'seq_prm', [30 530 130 550], 'Value', [T '.seq_prm']);
    sl_mfunc(cs, 'R2_Sequence', [160 470 270 560], 'prism_r2_sequence.m');
    sl_line(cs, 'Clock_seq/1', 'R2_Sequence/1');
    sl_line(cs, 'seq_prm/1', 'R2_Sequence/2');
    sl_add(cs, 'simulink/Signal Routing/Goto', 'r2_seq', [320 585 400 605], 'GotoTag', 'r2_seq', 'TagVisibility', 'global');
    sl_line(cs, 'R2_Sequence/1', 'r2_seq/1');
    sl_add(cs, 'simulink/Signal Routing/Demux', 'seq_split', [300 470 305 560], 'Outputs', '3');
    sl_line(cs, 'R2_Sequence/1', 'seq_split/1');
    sl_add(cs, 'simulink/Sinks/Terminator', 'mode_unused', [330 535 350 555], 'ShowName', 'off');
    sl_line(cs, 'seq_split/1', 'y_mux/6');
    sl_line(cs, 'seq_split/2', 'y_mux/7');
    sl_line(cs, 'seq_split/3', 'mode_unused/1');
    sl_mfunc(cs, 'Adopted_Controller', [460 60 640 340], {'prism_ctrl_sampler_r2.m', 'prism_stageB_controller.m'});
    sl_note(cs, sprintf(['R2 창 조정 모듈(TB08): R2_Sequence가 시각표(TB.seq_prm)대로 버스 기준전압 V_ref 램프, 제어기 무충격 재초기화,\n' ...
        '운전 모드(0 제어, 1 DAB 고장, 2 영벡터, 3 바이패스, 4 바이패스 + 영벡터)를 낸다. 코드: ctrl/prism_r2_sequence.m,\n' ...
        'ctrl/prism_ctrl_sampler_r2.m(V_ref·재초기화를 입력으로 받는 표본화 실행기). 제어 법칙은 prism_stageB_controller.m 그대로']), ...
        [460 380 1150 440], 'box');
else
    sl_mfunc(cs, 'Adopted_Controller', [460 60 640 340], {'prism_ctrl_sampler.m', 'prism_stageB_controller.m'});
end
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
    [30 450 + 190*r2 + 80*r2b 900 510 + 190*r2 + 80*r2b], 'box');   % R2에서는 모드 시퀀서 아래로 내린다

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
if r2c
    sl_mfunc(gs, 'StageB_Gate', [260 60 400 280], 'prism_gate_stageB_e.m');   % SPS 생성기 + 1차 레그 2 지연(EPS)
else
    sl_mfunc(gs, 'StageB_Gate', [260 60 400 280], 'prism_gate_stageB.m');
end
sl_line(gs, 'Clock/1', 't/1');
sl_line(gs, 'Clock/1', 'StageB_Gate/1');
sl_line(gs, 'uc_from/1', 'StageB_Gate/2');
sl_line(gs, 'ilink_from/1', 'ilink_z1/1');
sl_line(gs, 'ilink_z1/1', 'Startup_guard/1');
sl_line(gs, 'Clock/1', 'Startup_guard/2');
sl_line(gs, 'Startup_guard/1', 'StageB_Gate/3');
sl_line(gs, 'gate_prm/1', 'StageB_Gate/4');
sl_line(gs, 'gate_init/1', 'StageB_Gate/5');
gt = {'gB_AH', 'gB_AL', 'gB_BH', 'gB_BL', 'gD_P1', 'gD_P2', 'gD_P3', 'gD_P4', 'gD_S1', 'gD_S2', 'gD_S3', 'gD_S4'};
if r2b  % 보호 게이트 재정의(하드웨어 비교기, 고장 주입, 모드) → 14개 태그(바이패스 gByp, 제동 저항 gBrk 포함)
    sl_add(gs, 'simulink/Signal Routing/From', 'sup_from', [260 310 340 330], 'GotoTag', 'r2_sup');
    sl_add(gs, 'simulink/Signal Routing/Selector', 'sup_sel', [360 310 380 330], 'IndexParamArray', {'[3 5 8 9 11]'}, ...
        'InputPortWidth', '12');
    sl_line(gs, 'sup_from/1', 'sup_sel/1');
    mt = {'ip', 'ih', 'vlink', 'vs', 'vbus'};
    for k = 1:5
        sl_add(gs, 'simulink/Signal Routing/From', ['cmp_' mt{k}], [260 350+25*(k-1) 330 366+25*(k-1)], 'GotoTag', mt{k}, 'ShowName', 'off');
    end
    sl_add(gs, 'simulink/Signal Routing/Mux', 'cmp_mux', [350 350 355 470], 'Inputs', '5');
    for k = 1:5, sl_line(gs, sprintf('cmp_%s/1', mt{k}), sprintf('cmp_mux/%d', k)); end
    sl_add(gs, 'simulink/Discrete/Unit Delay', 'cmp_z1', [375 395 405 425], 'SampleTime', [T '.dt'], ...
        'InitialCondition', sprintf('[%s.ip0 %s.ih0 %s.vl0 %s.vs0 %s.vb0]''', T, T, T, T, T));   % 대수 루프 방지(한 간격 = 비교기 지연에 포함)
    sl_line(gs, 'cmp_mux/1', 'cmp_z1/1');
    sl_add(gs, 'simulink/Sources/Constant', 'prot_prm', [260 495 360 515], 'Value', [T '.prot_prm']);   % cmp_mux 이름표 아래
    sl_mfunc(gs, 'R2_Gate_Protect', [440 60 540 500], 'prism_r2_gate_b.m');
    sl_line(gs, 'Clock/1', 'R2_Gate_Protect/1');
    sl_line(gs, 'StageB_Gate/1', 'R2_Gate_Protect/2');
    sl_line(gs, 'sup_sel/1', 'R2_Gate_Protect/3');
    sl_line(gs, 'cmp_z1/1', 'R2_Gate_Protect/4');
    sl_line(gs, 'prot_prm/1', 'R2_Gate_Protect/5');
    sl_add(gs, 'simulink/Signal Routing/Demux', 'Demux', [580 50 590 440], 'Outputs', '14');
    sl_line(gs, 'R2_Gate_Protect/1', 'Demux/1');
    sl_add(gs, 'simulink/Discrete/Unit Delay', 'flags_z1', [580 470 610 500], 'SampleTime', [T '.dt']);
    sl_add(gs, 'simulink/Signal Routing/Goto', 'r2_flags', [640 475 720 495], 'GotoTag', 'r2_flags', 'TagVisibility', 'global');
    sl_line(gs, 'R2_Gate_Protect/2', 'flags_z1/1');
    sl_line(gs, 'flags_z1/1', 'r2_flags/1');
    gt{13} = 'gByp'; gt{14} = 'gBrk';
    x0 = 640;
    if r2c   % DAB 고장 모드 변조 지령(상태 9–11, DAB 모드 1): 상태기계 보조 지령 + 측정(한 간격 지연) → [켬; φ; D1]
        y0 = 560;   % 보호 게이트 묶음(y ≤ 515) 아래에 따로 두고, 생성기 입력 6은 지역 태그 dab_eps로 잇는다(선 겹침 방지)
        sl_add(gs, 'simulink/Signal Routing/From', 'eps_sup', [20 y0 80 y0+16], 'GotoTag', 'r2_sup', 'ShowName', 'off');
        sl_add(gs, 'simulink/Signal Routing/From', 'eps_vb', [20 y0+35 80 y0+51], 'GotoTag', 'vbus', 'ShowName', 'off');
        sl_add(gs, 'simulink/Signal Routing/From', 'eps_vl', [20 y0+60 80 y0+76], 'GotoTag', 'vlink', 'ShowName', 'off');
        sl_add(gs, 'simulink/Signal Routing/Mux', 'eps_mux', [100 y0+33 105 y0+78], 'Inputs', '2', 'ShowName', 'off');
        sl_add(gs, 'simulink/Discrete/Unit Delay', 'eps_z1', [120 y0+43 145 y0+67], 'SampleTime', [T '.dt'], ...
            'InitialCondition', sprintf('[%s.vb0 %s.vl0]''', T, T), 'ShowName', 'off');      % 대수 루프 방지
        sl_add(gs, 'simulink/Sources/Constant', 'eps_prm', [20 y0+95 95 y0+111], 'Value', [T '.eps_prm'], 'ShowName', 'off');   % 값(TB.eps_*)이 블록 안에 보임
        sl_add(gs, 'simulink/Sources/Constant', 'eps_d',   [20 y0+125 95 y0+141], 'Value', [T '.eps_d'], 'ShowName', 'off');
        sl_add(gs, 'simulink/Sources/Constant', 'eps_phi', [20 y0+155 95 y0+171], 'Value', [T '.eps_phi'], 'ShowName', 'off');
        sl_add(gs, 'simulink/Sources/Constant', 'eps_pk',  [20 y0+185 95 y0+201], 'Value', [T '.eps_pk'], 'ShowName', 'off');
        sl_mfunc(gs, 'DAB_EPS_Map', [180 y0 340 y0+205], 'prism_dab_eps_map.m');   % 함수 이름이 포트 이름과 겹치지 않게 넓게
        sl_add(gs, 'simulink/Signal Routing/Goto', 'eps_to', [370 y0+95 440 y0+111], 'GotoTag', 'dab_eps', 'ShowName', 'off');
        sl_add(gs, 'simulink/Signal Routing/From', 'eps_from', [190 254 245 270], 'GotoTag', 'dab_eps', 'ShowName', 'off');
        sl_line(gs, 'eps_vb/1', 'eps_mux/1'); sl_line(gs, 'eps_vl/1', 'eps_mux/2'); sl_line(gs, 'eps_mux/1', 'eps_z1/1');
        sl_line(gs, 'eps_sup/1', 'DAB_EPS_Map/1'); sl_line(gs, 'eps_z1/1', 'DAB_EPS_Map/2');
        sl_line(gs, 'eps_prm/1', 'DAB_EPS_Map/3'); sl_line(gs, 'eps_d/1', 'DAB_EPS_Map/4');
        sl_line(gs, 'eps_phi/1', 'DAB_EPS_Map/5'); sl_line(gs, 'eps_pk/1', 'DAB_EPS_Map/6');
        sl_line(gs, 'DAB_EPS_Map/1', 'eps_to/1');
        sl_line(gs, 'eps_from/1', 'StageB_Gate/6');
    end
elseif r2   % 게이트 재정의(모드: DAB 정지·영벡터·바이패스) → 13개 태그(바이패스 게이트 gByp 포함)
    sl_add(gs, 'simulink/Signal Routing/From', 'seq_from', [260 310 340 330], 'GotoTag', 'r2_seq');
    sl_add(gs, 'simulink/Signal Routing/Demux', 'seq_split', [360 300 365 360], 'Outputs', '3');
    sl_add(gs, 'simulink/Sinks/Terminator', 'seq_unused1', [390 290 410 310], 'ShowName', 'off');
    sl_add(gs, 'simulink/Sinks/Terminator', 'seq_unused2', [390 315 410 335], 'ShowName', 'off');
    sl_line(gs, 'seq_from/1', 'seq_split/1');
    sl_line(gs, 'seq_split/1', 'seq_unused1/1');
    sl_line(gs, 'seq_split/2', 'seq_unused2/1');
    sl_mfunc(gs, 'R2_Gate_Override', [440 60 540 360], 'prism_r2_gate.m');
    sl_line(gs, 'StageB_Gate/1', 'R2_Gate_Override/1');
    sl_line(gs, 'seq_split/3', 'R2_Gate_Override/2');
    sl_add(gs, 'simulink/Signal Routing/Demux', 'Demux', [580 50 590 410], 'Outputs', '13');
    sl_line(gs, 'R2_Gate_Override/1', 'Demux/1');
    gt{13} = 'gByp';
    x0 = 640;
else
    sl_add(gs, 'simulink/Signal Routing/Demux', 'Demux', [460 50 470 380], 'Outputs', '12');
    sl_line(gs, 'StageB_Gate/1', 'Demux/1');
    x0 = 520;
end
for s = 1:numel(gt)
    sl_add(gs, 'simulink/Signal Routing/Goto', gt{s}, [x0 48+27*(s-1) x0+90 64+27*(s-1)], 'GotoTag', gt{s}, 'TagVisibility', 'global', ...
        'ShowName', 'off');   % 태그 이름이 블록 안에 보이므로 블록 이름은 숨긴다(겹침 방지)
    sl_line(gs, sprintf('Demux/%d', s), [gt{s} '/1']);
end
sl_add(gs, 'simulink/Signal Routing/Goto', 'gate_aux', [460 420 + 100*r2b 560 440 + 100*r2b], 'GotoTag', 'gate_aux', 'TagVisibility', 'global');
sl_line(gs, 'StageB_Gate/2', 'gate_aux/1');
if r2c, gfile = 'prism_gate_stageB_e.m'; else, gfile = 'prism_gate_stageB.m'; end
sl_note(gs, sprintf(['H-브리지: 유니폴라 PWM 200 kHz(반송파는 표본 시점에서 최댓값), 데드타임 50 ns.\n' ...
    'DAB: 반송파 반주기 중심에 대칭인 1·2차 에지(δ = φT/2π), 전이 반주기 평균 위상 갱신(직류 편류 방지), 데드타임 100 ns.\n' ...
    '링크전류 주기 평균을 표본 직전에 확정해 제어기의 ρ̂·ε̂ 추정에 넘긴다(aux). 코드: ctrl/%s(블록 안에 복사)'], gfile), ...
    [30 460 + 100*r2b + 260*r2c 800 520 + 100*r2b + 260*r2c], 'box');
if r2c
    sl_note(gs, sprintf(['DAB 고장 모드 변조(TB10, ctrl/prism_dab_eps_map.m → ctrl/prism_gate_stageB_e.m): H-브리지 강등(상태 9–11)에서 보조 링크전류 지령을\n' ...
        '1차 내부 위상천이(EPS) 지령 [φ; D1]으로 바꾼다(검증 코드 dab_modulation.py의 첨두 최소표, 첨두 ≤ 1.5 × 정격점). 레그 2를 D1·T/2 늦춰\n' ...
        '1차 전압에 영구간을 넣는다. 그 밖의 상태에서는 SPS 생성기와 같다(eps = 0). 지령은 지역 태그 dab_eps로 생성기 입력 6에 간다']), ...
        [30 1010 800 1060], 'box');
end
if r2b
    sl_note(gs, sprintf(['R2 보호 게이트 재정의(ctrl/prism_r2_gate_b.m, 적분 간격마다): 하드웨어 비교기(|i_p|·|i_h| > 110 A, v_link > 115 V,\n' ...
        '|v_s| > 100 V, 정상 조정 중 v_bus > 부품 상한, 1.2 µs 지속 → H-브리지 차단 래치), 고장 주입(H-브리지 개방·DAB 정지),\n' ...
        '브리지 모드(제어·영벡터·차단·조향), DAB 정지, 바이패스 주 스위치 gByp, 제동 저항 gBrk. 신호 r2_flags는 한 간격 지연해 상태기계로']), ...
        [30 640 + 260*r2c 800 690 + 260*r2c], 'box');
elseif r2
    sl_note(gs, sprintf(['R2 게이트 재정의(ctrl/prism_r2_gate.m): 모드 1 DAB 게이트 끔, 2 영벡터(A·B 하측 켬)·DAB 끔, 3 바이패스 켬·전 소자 끔,\n' ...
        '4 바이패스 + 영벡터. 게이트 구동기 수준의 재정의라 제어기 전달지연(5 µs)을 거치지 않는다. 바이패스 게이트 태그 gByp']), ...
        [30 540 800 580], 'box');
end
end
