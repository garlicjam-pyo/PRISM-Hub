function build_bus_loads(sys, posLoad, posLoss, T, opt)
%BUILD_BUS_LOADS  400 V 버스의 부하 계산 서브시스템 두 개를 만든다(출력은 전류 지령 신호).
%
%   Load_CPL       : 정전력 부하. P(t) = P0(t < t_step), P1(t ≥ t_step) → i = P / max(v_bus, v_min)
%                    v_bus는 한 간격 지연해 쓴다(회로 ↔ Simulink 사이 대수 루프 방지).
%   DAB_Loss_Model : DAB 손실 등가 전류(ctrl/prism_dab_loss.m, 검증 모델과 같은 방향별 효율 0.96 손실)
%   두 출력은 최상위에서 Simulink-PS 변환기 → 제어 전류원(버스 → GND)으로 들어간다.
%   두 모델 모두 회로 측정값을 시작 표본 보호(sl_startup_guard)를 거쳐 쓴다.
%   T : 시험 구조체 이름. 필드 dt P0 P1 t_step vmin loss_prm ploss0 guard_t vb0 loss_meas0
%   opt.ShedTag·ShedIndex·ShedWidth (선택, TB09): 400 V 부하 분리 신호가 1이면 P = T.Pc(분리 뒤 남는 부하)
%   opt.Sals (선택, TB23): 상태기계 s(opt.ShedIndex)의 비트 명령으로 등급별 계약 응답(ctrl/prism_sals_loads.m, T.sals_prm)

if nargin < 5, opt = struct(); end
ld = [sys '/Load_CPL'];
add_block('built-in/Subsystem', ld, 'Position', posLoad, 'BackgroundColor', 'lightBlue');
if isfield(opt, 'Sals') && opt.Sals   % (TB23) 등급별 계약 응답: 상태기계 비트 명령 → ctrl/prism_sals_loads.m(파라미터 T.sals_prm)
    sl_add(ld, 'simulink/Signal Routing/From', 'sup_from', [30 20 100 40], 'GotoTag', opt.ShedTag);
    sl_add(ld, 'simulink/Signal Routing/Selector', 'code_sel', [115 20 135 40], 'IndexParamArray', {num2str(opt.ShedIndex)}, ...
        'InputPortWidth', num2str(opt.ShedWidth));
    sl_line(ld, 'sup_from/1', 'code_sel/1');
    sl_add(ld, 'simulink/Signal Routing/From', 'vbus_from', [30 70 110 90], 'GotoTag', 'vbus');
    sl_add(ld, 'simulink/Signal Routing/From', 't_from', [30 110 110 130], 'GotoTag', 't');
    sl_startup_guard(ld, 'Startup_guard', [150 65 190 135], [T '.vb0'], T, [120 150 190 170]);
    sl_add(ld, 'simulink/Discrete/Unit Delay', 'vbus_z1', [220 85 250 115], 'SampleTime', [T '.dt']);
    sl_add(ld, 'simulink/Sources/Constant', 'sals_prm', [30 190 130 210], 'Value', [T '.sals_prm']);
    sl_mfunc(ld, 'SALS_Loads', [300 20 440 200], 'prism_sals_loads.m');
    sl_line(ld, 'vbus_from/1', 'Startup_guard/1');
    sl_line(ld, 't_from/1', 'Startup_guard/2');
    sl_line(ld, 'Startup_guard/1', 'vbus_z1/1');
    sl_line(ld, 't_from/1', 'SALS_Loads/1');
    sl_line(ld, 'vbus_z1/1', 'SALS_Loads/2');
    sl_line(ld, 'code_sel/1', 'SALS_Loads/3');
    sl_line(ld, 'sals_prm/1', 'SALS_Loads/4');
    add_block('simulink/Sinks/Out1', [ld '/i_load'], 'Position', [500 60 530 80]);
    sl_add(ld, 'simulink/Signal Routing/Goto', 'p_load', [480 140 560 160], 'GotoTag', 'p_load', 'TagVisibility', 'global');
    sl_line(ld, 'SALS_Loads/1', 'i_load/1');
    sl_line(ld, 'SALS_Loads/2', 'p_load/1');
    sl_note(ld, sprintf(['등급별 계약 응답(ctrl/prism_sals_loads.m): 상태기계 s(10) 비트(1 접촉기 열림, 2 SALS 감발, 4 되돌림, 8 Stage C 회생 차단)\n' ...
        '→ M0(Stage C·V2L)·M1(컴프레서)·D(PTC·배터리 히터) 전력, 메시지 지연·손실·워치독, i = P/max(v_bus, v_min), 250 V 아래 차단']), ...
        [30 240 640 270], 'box');
elseif isfield(opt, 'ShedTag')      % (TB09) 400 V 부하 분리: 상태기계 신호(태그 opt.ShedTag의 opt.ShedIndex번째)가 1이면 P = T.Pc
    sl_add(ld, 'simulink/Sources/Constant', 'P_on', [30 20 90 40], 'Value', [T '.P0']);
    sl_add(ld, 'simulink/Sources/Constant', 'P_shed', [30 80 90 100], 'Value', [T '.Pc']);
    sl_add(ld, 'simulink/Signal Routing/From', 'shed_from', [30 50 100 70], 'GotoTag', opt.ShedTag);
    sl_add(ld, 'simulink/Signal Routing/Selector', 'shed_sel', [115 50 135 70], 'IndexParamArray', {num2str(opt.ShedIndex)}, ...
        'InputPortWidth', num2str(opt.ShedWidth));
    sl_add(ld, 'simulink/Signal Routing/Switch', 'P_profile', [160 20 200 100], 'Criteria', 'u2 > Threshold', 'Threshold', '0.5');
    sl_line(ld, 'P_shed/1', 'P_profile/1');
    sl_line(ld, 'shed_from/1', 'shed_sel/1');
    sl_line(ld, 'shed_sel/1', 'P_profile/2');
    sl_line(ld, 'P_on/1', 'P_profile/3');
else
    sl_add(ld, 'simulink/Sources/Step', 'P_profile', [30 30 80 70], 'Time', [T '.t_step'], ...
        'Before', [T '.P0'], 'After', [T '.P1'], 'SampleTime', [T '.dt']);
end
if ~(isfield(opt, 'Sals') && opt.Sals)
posG = [120 10 200 30]; if isfield(opt, 'ShedTag'), posG = [230 0 310 20]; end
sl_add(ld, 'simulink/Signal Routing/Goto', 'p_load', posG, 'GotoTag', 'p_load', 'TagVisibility', 'global');
sl_add(ld, 'simulink/Signal Routing/From', 'vbus_from', [30 110 110 130], 'GotoTag', 'vbus');
sl_add(ld, 'simulink/Signal Routing/From', 't_from', [30 150 110 170], 'GotoTag', 't');
sl_startup_guard(ld, 'Startup_guard', [150 105 190 175], [T '.vb0'], T, [120 190 190 210]);
sl_add(ld, 'simulink/Discrete/Unit Delay', 'vbus_z1', [220 125 250 155], 'SampleTime', [T '.dt']);
sl_add(ld, 'simulink/Sources/Constant', 'v_min', [220 190 280 210], 'Value', [T '.vmin']);
sl_add(ld, 'simulink/Math Operations/MinMax', 'v_floor', [310 130 340 180], 'Function', 'max', 'Inputs', '2');
sl_add(ld, 'simulink/Math Operations/Divide', 'P_over_v', [380 50 420 150]);
add_block('simulink/Sinks/Out1', [ld '/i_load'], 'Position', [460 90 490 110]);
sl_line(ld, 'P_profile/1', 'p_load/1');
sl_line(ld, 'P_profile/1', 'P_over_v/1');
sl_line(ld, 'vbus_from/1', 'Startup_guard/1');
sl_line(ld, 't_from/1', 'Startup_guard/2');
sl_line(ld, 'Startup_guard/1', 'vbus_z1/1');
sl_line(ld, 'vbus_z1/1', 'v_floor/1');
sl_line(ld, 'v_min/1', 'v_floor/2');
sl_line(ld, 'v_floor/1', 'P_over_v/2');
sl_line(ld, 'P_over_v/1', 'i_load/1');
sl_note(ld, sprintf('정전력 부하: i = P(t)/max(v_bus, v_min). v_bus는 시작 표본 보호 후 한 간격 지연'), [30 240 480 260]);
end

ls = [sys '/DAB_Loss_Model'];
add_block('built-in/Subsystem', ls, 'Position', posLoss, 'BackgroundColor', 'lightBlue');
sl_add(ls, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', [T '.dt']);
tg = {'vlink', 'ilink', 'iL', 'vbus'};
for k = 1:4
    sl_add(ls, 'simulink/Signal Routing/From', ['from_' tg{k}], [30 70+30*(k-1) 110 90+30*(k-1)], 'GotoTag', tg{k});
end
% 측정 4개 → 시작 표본 보호 → 손실 계산 함수 입력
sl_add(ls, 'simulink/Signal Routing/Mux', 'meas_mux', [130 65 135 175], 'Inputs', '4');
for k = 1:4, sl_line(ls, sprintf('from_%s/1', tg{k}), sprintf('meas_mux/%d', k)); end
sl_startup_guard(ls, 'Startup_guard', [160 90 195 150], [T '.loss_meas0'], T, [140 200 230 220]);
sl_line(ls, 'meas_mux/1', 'Startup_guard/1');
sl_line(ls, 'Clock/1', 'Startup_guard/2');
sl_add(ls, 'simulink/Signal Routing/Demux', 'meas_split', [230 65 235 175], 'Outputs', '4');
sl_line(ls, 'Startup_guard/1', 'meas_split/1');
sl_add(ls, 'simulink/Sources/Constant', 'loss_prm', [30 250 130 270], 'Value', [T '.loss_prm']);
sl_add(ls, 'simulink/Sources/Constant', 'ploss0',   [30 290 130 310], 'Value', [T '.ploss0']);
sl_mfunc(ls, 'DAB_Loss', [280 40 420 260], 'prism_dab_loss.m');
sl_line(ls, 'Clock/1', 'DAB_Loss/1');
for k = 1:4, sl_line(ls, sprintf('meas_split/%d', k), sprintf('DAB_Loss/%d', k + 1)); end
sl_line(ls, 'loss_prm/1', 'DAB_Loss/6');
sl_line(ls, 'ploss0/1', 'DAB_Loss/7');
sl_add(ls, 'simulink/Discrete/Unit Delay', 'iloss_z1', [460 135 490 165], 'SampleTime', [T '.dt']);
add_block('simulink/Sinks/Out1', [ls '/i_loss'], 'Position', [530 140 560 160]);
sl_line(ls, 'DAB_Loss/1', 'iloss_z1/1');
sl_line(ls, 'iloss_z1/1', 'i_loss/1');
sl_note(ls, sprintf(['DAB 손실 등가: 직전 주기 평균 링크전력 p̄로 P_loss = (1/η − 1)max(p̄,0) + (1 − η)max(−p̄,0) − R_dab·mean(i_L²)\n' ...
    '(η = 0.96, 검증 모델과 같음)을 버스 전류 P_loss/v_bus로 끈다. 회로의 R_dab 손실은 빼서 중복을 막는다.']), [30 330 700 370], 'box');
end
