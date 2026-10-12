function sl_meas(sys, sensor, outPort, tag, pos)
%SL_MEAS  센서의 물리 신호를 Simulink 신호로 바꿔 전역 Goto 태그로 내보낸다.
%
%   sl_meas(sys, 'I_Lr', 'I', 'iC', [x y])     % sys/I_Lr 의 I 출력 → PS-Simulink → Goto 'iC'
%
%   계측 신호는 태그로 모아 Scope·To Workspace가 From 블록으로 받는다(회로도와 계측부 분리).

x = pos(1); y = pos(2);
cv = sprintf('%s_PS2SL', tag);
add_block('nesl_utility/PS-Simulink Converter', [sys '/' cv], 'Position', [x y x+30 y+20]);
add_block('simulink/Signal Routing/Goto', [sys '/' tag], 'Position', [x+60 y x+150 y+20], ...
    'GotoTag', tag, 'TagVisibility', 'global');
simscape.addConnection([sys '/' sensor], outPort, [sys '/' cv], 'input');
add_line(sys, [cv '/1'], [tag '/1']);
end
