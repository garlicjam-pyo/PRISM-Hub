function h = build_hbridge(sys, name, pos, B)
%BUILD_HBRIDGE  Stage B 4상한 H-브리지(풀브리지) 서브시스템을 만든다.
%
%   h = build_hbridge(sys, 'StageB_HBridge', [x1 y1 x2 y2], 'TB.B')
%
%   외부 포트: LINK_P, LINK_N(부유 100 V 링크), A, B(레그 노드 = 브리지 출력)
%   레그 A: QA_high(LINK_P → A), QA_low(A → LINK_N)      레그 B: QB_high(LINK_P → B), QB_low(B → LINK_N)
%   유니폴라 PWM에서 브리지 출력 v_AB = v_A − v_B 는 +V, 0, −V 세 단계를 가진다.
%   스위치 셀마다 출력용량 C_oss(선형 1 nF)를 넣어, 데드타임(50 ns) 동안 레그 노드 전압이
%   필터 전류로 충방전되는 과정(부분 영전압 스위칭)을 회로가 직접 계산하게 한다.
%   게이트 태그: gB_AH, gB_AL, gB_BH, gB_BL.   계측 태그: vA_node(레그 A 노드 − LINK_N)
%
%   B : 파라미터 구조체 이름(문자열, 예 'TB.B'). 필드 Ron Goff Vf Rd Goffd Coss_h.

hb = [sys '/' name];
h = add_block('built-in/Subsystem', hb, 'Position', pos);
add_block('nesl_utility/Connection Port', [hb '/LINK_P'], 'Position', [30 60 60 80],   'Side', 'Left',  'Port', '1');
add_block('nesl_utility/Connection Port', [hb '/LINK_N'], 'Position', [30 400 60 420], 'Side', 'Left',  'Port', '2');
add_block('nesl_utility/Connection Port', [hb '/A'],      'Position', [300 225 330 245], 'Side', 'Right', 'Port', '3');   % 레그 A 노드 옆
add_block('nesl_utility/Connection Port', [hb '/B'],      'Position', [560 225 590 245], 'Side', 'Right', 'Port', '4');   % 레그 B 노드 옆

c = struct('Ron', [B '.Ron'], 'Goff', [B '.Goff'], 'Vf', [B '.Vf'], 'Rd', [B '.Rd'], 'Goffd', [B '.Goffd'], ...
           'Coss', [B '.Coss_h'], 'orient', 'down');
c.tag = 'gB_AH'; c.label = 'QA_H'; sl_switch_cell(hb, 'QA_high', [200 110 260 200], c);
c.tag = 'gB_AL'; c.label = 'QA_L'; sl_switch_cell(hb, 'QA_low',  [200 280 260 370], c);
c.tag = 'gB_BH'; c.label = 'QB_H'; sl_switch_cell(hb, 'QB_high', [440 110 500 200], c);
c.tag = 'gB_BL'; c.label = 'QB_L'; sl_switch_cell(hb, 'QB_low',  [440 280 500 370], c);

sl_pc(hb, 'LINK_P', 'port', 'QA_high', 'D');
sl_pc(hb, 'LINK_P', 'port', 'QB_high', 'D');
sl_pc(hb, 'QA_high', 'S', 'QA_low', 'D');      % 레그 A 노드
sl_pc(hb, 'QB_high', 'S', 'QB_low', 'D');      % 레그 B 노드
sl_pc(hb, 'QA_low', 'S', 'LINK_N', 'port');
sl_pc(hb, 'QB_low', 'S', 'LINK_N', 'port');
sl_pc(hb, 'QA_high', 'S', 'A', 'port');
sl_pc(hb, 'QB_high', 'S', 'B', 'port');

% 레그 A 노드 전압(데드타임 중 전이 관찰용)
sl_add(hb, 'fl_lib/Electrical/Electrical Sensors/Voltage Sensor', 'V_nodeA', [100 260 140 320], 'Orientation', 'down');
sl_pc(hb, 'V_nodeA', 'p', 'QA_low', 'D');
sl_pc(hb, 'V_nodeA', 'n', 'LINK_N', 'port');
sl_meas(hb, 'V_nodeA', 'V', 'vA_node', [100 460]);

sl_note(hb, sprintf(['Stage B H-브리지(4상한): 레그 A = QA_high/QA_low, 레그 B = QB_high/QB_low\n' ...
    '유니폴라 PWM 200 kHz, 데드타임 50 ns, 셀마다 C_oss 1 nF(레그 노드 등가 2 nF)\n' ...
    '출력 v_AB = v_A − v_B → L_h 필터 → 직렬 커패시터(직렬 포트)']), [30 520 640 580], 'box');
set_param(h, 'BackgroundColor', 'white');
end
