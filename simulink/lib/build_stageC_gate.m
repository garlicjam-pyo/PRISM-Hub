function build_stageC_gate(sys, pos, T)
%BUILD_STAGEC_GATE  Stage C 게이트 생성기 서브시스템(Gate_StageC)을 만든다(TB05와 같은 구성).
%
%   build_stageC_gate(sys, [x1 y1 x2 y2], 'TB')
%   250 kHz 공진점 고정, 50 % 상보 + 데드타임 50 ns(ctrl/prism_gate_stageC.m) → 게이트 태그 gC_Q1–gC_Q4
%   T : 시험 구조체 이름(문자열). 필드 dt, gateC_prm([dt T t_d enable])

gs = [sys '/Gate_StageC'];
add_block('built-in/Subsystem', gs, 'Position', pos, 'BackgroundColor', 'yellow');
sl_add(gs, 'simulink/Sources/Digital Clock', 'Clock', [30 40 80 70], 'SampleTime', [T '.dt']);
sl_add(gs, 'simulink/Sources/Constant', 'gate_prm', [30 120 130 140], 'Value', [T '.gateC_prm']);
sl_mfunc(gs, 'StageC_Gate', [180 40 320 150], 'prism_gate_stageC.m');
sl_line(gs, 'Clock/1', 'StageC_Gate/1');
sl_line(gs, 'gate_prm/1', 'StageC_Gate/2');
sl_add(gs, 'simulink/Signal Routing/Demux', 'Demux', [380 40 390 160], 'Outputs', '4');
sl_line(gs, 'StageC_Gate/1', 'Demux/1');
tags = {'gC_Q1', 'gC_Q2', 'gC_Q3', 'gC_Q4'};
for s = 1:4
    sl_add(gs, 'simulink/Signal Routing/Goto', tags{s}, [440 35+32*(s-1) 530 55+32*(s-1)], 'GotoTag', tags{s}, ...
        'TagVisibility', 'global', 'ShowName', 'off');
    sl_line(gs, sprintf('Demux/%d', s), [tags{s} '/1']);
end
sl_note(gs, sprintf(['Stage C 게이트: 주기 T = 4 µs(공진점 250 kHz), 전반주기 [t_d, T/2) Q1·Q4, 후반주기 [T/2 + t_d, T) Q2·Q3, 데드타임 50 ns.\n' ...
    '고정이득 구조이므로 폐루프 제어는 없다(48 V는 Stage B가 조정한 400 V 버스에서 간접적으로 정해진다).']), ...
    [30 200 760 240], 'box');
end
