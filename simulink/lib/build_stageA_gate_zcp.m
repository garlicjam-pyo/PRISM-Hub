function build_stageA_gate_zcp(sys, pos, T, phases)
%BUILD_STAGEA_GATE_ZCP  Stage A 영교차 추종 게이트 생성기 서브시스템(Gate_StageA)을 만든다.
%
%   build_stageA_gate_zcp(sys, [x1 y1 x2 y2], 'TB', [1 2])
%
%   구성: 동작 위상의 공진전류 태그 iA_P<k> → Mux(정지 위상은 0) → 한 간격 지연(회로 ↔ 게이트 대수 루프 방지)
%         → 시작 표본 보호(t < 1.5 dt 동안 0) → ctrl/prism_gate_stageA_zcp.m(블록 안에 복사)
%         → 게이트 태그 gA_P<k>_S1–S4, 구간 태그 stA_P<k>(0 데드타임, 1 충전, 2 방전)
%   T      : 시험 구조체 이름(문자열). 필드 dt, gateA_zcp_prm, gateA_en, gateA_off, guard_t
%   phases : 동작 위상 번호(예 [1 2] = 모듈 1)

gs = [sys '/Gate_StageA'];
add_block('built-in/Subsystem', gs, 'Position', pos, 'BackgroundColor', 'yellow');
sl_add(gs, 'simulink/Sources/Digital Clock', 'Clock', [30 20 80 50], 'SampleTime', [T '.dt']);
np = numel(phases);
% 위상 전류 측정 → 8×1 벡터(정지 위상 0). 8위상 모두 동작하면 정지 위상 상수를 두지 않는다.
nin = np + (np < 8);
sl_add(gs, 'simulink/Signal Routing/Mux', 'iC_mux', [190 70 195 70+40*nin], 'Inputs', num2str(nin));
for j = 1:np
    tg = sprintf('iA_P%d', phases(j));
    sl_add(gs, 'simulink/Signal Routing/From', ['from_' tg], [30 70+40*(j-1) 120 90+40*(j-1)], 'GotoTag', tg);
    sl_line(gs, sprintf('from_%s/1', tg), sprintf('iC_mux/%d', j));
end
if np < 8
    sl_add(gs, 'simulink/Sources/Constant', 'idle_phases', [30 70+40*np 120 90+40*np], 'Value', sprintf('zeros(%d,1)', 8 - np));
    sl_line(gs, 'idle_phases/1', sprintf('iC_mux/%d', np + 1));
end
sl_add(gs, 'simulink/Discrete/Unit Delay', 'iC_z1', [230 95 260 125], 'SampleTime', [T '.dt']);
sl_line(gs, 'iC_mux/1', 'iC_z1/1');
sl_startup_guard(gs, 'Startup_guard', [290 90 320 160], 'zeros(8,1)', T, [190 250 280 270]);
sl_line(gs, 'iC_z1/1', 'Startup_guard/1');
sl_line(gs, 'Clock/1', 'Startup_guard/2');
sl_add(gs, 'simulink/Sources/Constant', 'zcp_prm', [230 300 330 320], 'Value', [T '.gateA_zcp_prm']);
sl_add(gs, 'simulink/Sources/Constant', 'phase_en', [230 340 330 360], 'Value', [T '.gateA_en']);
sl_add(gs, 'simulink/Sources/Constant', 'phase_off', [230 380 330 400], 'Value', [T '.gateA_off']);
sl_mfunc(gs, 'StageA_ZCP_Gate', [380 60 540 420], 'prism_gate_stageA_zcp.m');
sl_line(gs, 'Clock/1', 'StageA_ZCP_Gate/1');
sl_line(gs, 'Startup_guard/1', 'StageA_ZCP_Gate/2');
sl_line(gs, 'zcp_prm/1', 'StageA_ZCP_Gate/3');
sl_line(gs, 'phase_en/1', 'StageA_ZCP_Gate/4');
sl_line(gs, 'phase_off/1', 'StageA_ZCP_Gate/5');
% 게이트 32개 → 동작 위상의 태그(앞뒤 정지 위상 묶음은 종단). 동작 위상은 연속 번호라고 가정한다(모듈 단위).
p1 = phases(1); assert(isequal(phases(:)', p1:p1 + np - 1), 'phases must be contiguous');
gsz = [4*(p1 - 1), ones(1, 4*np), 4*(8 - p1 - np + 1)];
ssz = [p1 - 1, ones(1, np), 8 - p1 - np + 1];
[gsz, gi] = drop_empty(gsz, 4*(p1 - 1) > 0, 4*(8 - p1 - np + 1) > 0);
[ssz, si] = drop_empty(ssz, p1 - 1 > 0, 8 - p1 - np + 1 > 0);
sl_add(gs, 'simulink/Signal Routing/Demux', 'gate_demux', [600 40 610 40+30*numel(gsz)], 'Outputs', mat2str(gsz));
sl_line(gs, 'StageA_ZCP_Gate/1', 'gate_demux/1');
for j = 1:np
    for s = 1:4
        tg = sprintf('gA_P%d_S%d', phases(j), s);
        y = 35 + 30*(4*(j-1) + s - 1);
        sl_add(gs, 'simulink/Signal Routing/Goto', tg, [660 y 760 y+20], 'GotoTag', tg, 'TagVisibility', 'global', 'ShowName', 'off');
        sl_line(gs, sprintf('gate_demux/%d', gi(1) + 4*(j-1) + s), [tg '/1']);
    end
end
for e = gi(2:end)
    nm = sprintf('idle_gates_%d', e);
    y = 35 + 30*(4*np + (e > 1)*0);                 % 마지막 출력(정지 위상 묶음) 옆
    sl_add(gs, 'simulink/Sinks/Terminator', nm, [660 y 680 y+20]);
    sl_line(gs, sprintf('gate_demux/%d', e), [nm '/1']);
end
% 위상별 구간(평가용)
ys = 110 + 30*numel(gsz);                          % 게이트 Demux 아래
sl_add(gs, 'simulink/Signal Routing/Demux', 'state_demux', [600 ys 610 ys+30*numel(ssz)], 'Outputs', mat2str(ssz));
sl_line(gs, 'StageA_ZCP_Gate/2', 'state_demux/1');
for j = 1:np
    tg = sprintf('stA_P%d', phases(j));
    y = ys + 30*(j-1);
    sl_add(gs, 'simulink/Signal Routing/Goto', tg, [660 y 760 y+20], 'GotoTag', tg, 'TagVisibility', 'global', 'ShowName', 'off');
    sl_line(gs, sprintf('state_demux/%d', si(1) + j), [tg '/1']);
end
for e = si(2:end)
    nm = sprintf('idle_states_%d', e);
    sl_add(gs, 'simulink/Sinks/Terminator', nm, [660 ys+30*np 680 ys+20+30*np]);
    sl_line(gs, sprintf('state_demux/%d', e), [nm '/1']);
end
sl_note(gs, sprintf(['영교차 추종(자기발진) 게이트: 데드타임 100 ns 뒤 다음 구간(S1·S3 충전 ↔ S2·S4 방전) 시작,\n' ...
    '공진전류가 펄스 부호 기준으로 i_thr 아래로 돌아오면 검출 지연 뒤 끈다. 블랭킹·보호 창은 공칭 도통시간의 0.80–1.12배.\n' ...
    '측정 전류는 한 간격 지연(5 ns)과 시작 표본 보호를 거친다. 코드: ctrl/prism_gate_stageA_zcp.m(블록 안에 복사)']), ...
    [30 ys+30*numel(ssz)+40 820 ys+30*numel(ssz)+90], 'box');
end

function [sz, idx] = drop_empty(sz, hasLead, hasTail)
% Demux 출력 크기 벡터에서 크기 0인 앞뒤 묶음을 지운다.
% idx(1) = 동작 위상 앞 오프셋(앞 묶음이 있으면 1), idx(2:end) = 종단할 출력 번호
lead = sz(1); tail = sz(end); mid = sz(2:end-1);
sz = mid; idx = 0; term = [];
if hasLead, sz = [lead, sz]; idx = 1; term(end+1) = 1; end
if hasTail, sz = [sz, tail]; term(end+1) = numel(sz); end
idx = [idx, term];
end
