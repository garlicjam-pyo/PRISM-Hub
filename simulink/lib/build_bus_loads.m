function build_bus_loads(sys, posLoad, posLoss, T)
%BUILD_BUS_LOADS  400 V 버스의 부하 계산 서브시스템 두 개를 만든다(출력은 전류 지령 신호).
%
%   Load_CPL       : 정전력 부하. P(t) = P0(t < t_step), P1(t ≥ t_step) → i = P / max(v_bus, v_min)
%                    v_bus는 한 간격 지연해 쓴다(회로 ↔ Simulink 사이 대수 루프 방지).
%   DAB_Loss_Model : DAB 손실 등가 전류(ctrl/prism_dab_loss.m, 검증 모델과 같은 방향별 효율 0.96 손실)
%   두 출력은 최상위에서 Simulink-PS 변환기 → 제어 전류원(버스 → GND)으로 들어간다.
%   T : 시험 구조체 이름. 필드 dt P0 P1 t_step vmin loss_prm ploss0

ld = [sys '/Load_CPL'];
add_block('built-in/Subsystem', ld, 'Position', posLoad, 'BackgroundColor', 'lightBlue');
sl_add(ld, 'simulink/Sources/Step', 'P_profile', [30 30 80 70], 'Time', [T '.t_step'], ...
    'Before', [T '.P0'], 'After', [T '.P1'], 'SampleTime', [T '.dt']);
sl_add(ld, 'simulink/Signal Routing/Goto', 'p_load', [120 10 200 30], 'GotoTag', 'p_load', 'TagVisibility', 'global');
sl_add(ld, 'simulink/Signal Routing/From', 'vbus_from', [30 110 110 130], 'GotoTag', 'vbus');
sl_add(ld, 'simulink/Discrete/Unit Delay', 'vbus_z1', [140 105 170 135], 'SampleTime', [T '.dt']);
sl_add(ld, 'simulink/Sources/Constant', 'v_min', [140 160 200 180], 'Value', [T '.vmin']);
sl_add(ld, 'simulink/Math Operations/MinMax', 'v_floor', [230 110 260 160], 'Function', 'max', 'Inputs', '2');
sl_add(ld, 'simulink/Math Operations/Divide', 'P_over_v', [300 40 340 140]);
add_block('simulink/Sinks/Out1', [ld '/i_load'], 'Position', [390 80 420 100]);
sl_line(ld, 'P_profile/1', 'p_load/1');
sl_line(ld, 'P_profile/1', 'P_over_v/1');
sl_line(ld, 'vbus_from/1', 'vbus_z1/1');
sl_line(ld, 'vbus_z1/1', 'v_floor/1');
sl_line(ld, 'v_min/1', 'v_floor/2');
sl_line(ld, 'v_floor/1', 'P_over_v/2');
sl_line(ld, 'P_over_v/1', 'i_load/1');
sl_note(ld, sprintf('정전력 부하: i = P(t)/max(v_bus, %s)', 'v_min'), [30 200 400 220]);

ls = [sys '/DAB_Loss_Model'];
add_block('built-in/Subsystem', ls, 'Position', posLoss, 'BackgroundColor', 'lightBlue');
sl_add(ls, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', [T '.dt']);
tg = {'vlink', 'ilink', 'iL', 'vbus'};
for k = 1:4
    sl_add(ls, 'simulink/Signal Routing/From', ['from_' tg{k}], [30 70+30*(k-1) 110 90+30*(k-1)], 'GotoTag', tg{k});
end
sl_add(ls, 'simulink/Sources/Constant', 'loss_prm', [30 200 130 220], 'Value', [T '.loss_prm']);
sl_add(ls, 'simulink/Sources/Constant', 'ploss0',   [30 240 130 260], 'Value', [T '.ploss0']);
sl_mfunc(ls, 'DAB_Loss', [200 40 340 260], 'prism_dab_loss.m');
sl_line(ls, 'Clock/1', 'DAB_Loss/1');
for k = 1:4, sl_line(ls, sprintf('from_%s/1', tg{k}), sprintf('DAB_Loss/%d', k + 1)); end
sl_line(ls, 'loss_prm/1', 'DAB_Loss/6');
sl_line(ls, 'ploss0/1', 'DAB_Loss/7');
sl_add(ls, 'simulink/Discrete/Unit Delay', 'iloss_z1', [380 135 410 165], 'SampleTime', [T '.dt']);
add_block('simulink/Sinks/Out1', [ls '/i_loss'], 'Position', [450 140 480 160]);
sl_line(ls, 'DAB_Loss/1', 'iloss_z1/1');
sl_line(ls, 'iloss_z1/1', 'i_loss/1');
sl_note(ls, sprintf(['DAB 손실 등가: 직전 주기 평균 링크전력 p̄로 P_loss = (1/η − 1)max(p̄,0) + (1 − η)max(−p̄,0) − R_dab·mean(i_L²)\n' ...
    '(η = 0.96, 검증 모델과 같음)을 버스 전류 P_loss/v_bus로 끈다. 회로의 R_dab 손실은 빼서 중복을 막는다.']), [30 290 700 330], 'box');
end
