function h = build_fullbridge(sys, name, pos, B, cellNames, tags, CossExpr, noteText)
%BUILD_FULLBRIDGE  풀브리지(2레그) 서브시스템을 만든다(DAB 1차·2차 브리지, Stage C 1차 브리지에 공용).
%
%   h = build_fullbridge(sys, 'DAB_Primary', [x1 y1 x2 y2], 'TB.B', ...
%                        {'P1_leg1_high','P2_leg1_low','P3_leg2_high','P4_leg2_low'}, ...
%                        {'gD_P1','gD_P2','gD_P3','gD_P4'}, 'TB.B.Coss_d', '설명')
%
%   외부 포트: DC_P, DC_N(직류 측), AC1(레그 1 노드), AC2(레그 2 노드)
%   스위치 번호: 1 = 레그 1 상측(DC_P → AC1), 2 = 레그 1 하측(AC1 → DC_N),
%                3 = 레그 2 상측(DC_P → AC2), 4 = 레그 2 하측(AC2 → DC_N)
%   게이트 생성기의 브리지 상태 +1 → 1·4번 켬(v_AC1 − v_AC2 = +V_dc), −1 → 2·3번 켬(−V_dc).
%   B : 파라미터 구조체 이름(문자열). 필드 Ron Goff Vf Rd Goffd.   CossExpr: 출력용량 식('' = 없음)

fb = [sys '/' name];
h = add_block('built-in/Subsystem', fb, 'Position', pos);
add_block('nesl_utility/Connection Port', [fb '/DC_P'], 'Position', [30 60 60 80],    'Side', 'Left',  'Port', '1');
add_block('nesl_utility/Connection Port', [fb '/DC_N'], 'Position', [30 400 60 420],   'Side', 'Left',  'Port', '2');
add_block('nesl_utility/Connection Port', [fb '/AC1'],  'Position', [300 225 330 245], 'Side', 'Right', 'Port', '3');
add_block('nesl_utility/Connection Port', [fb '/AC2'],  'Position', [560 225 590 245], 'Side', 'Right', 'Port', '4');

c = struct('Ron', [B '.Ron'], 'Goff', [B '.Goff'], 'Vf', [B '.Vf'], 'Rd', [B '.Rd'], 'Goffd', [B '.Goffd'], ...
           'Coss', CossExpr, 'orient', 'down');
xy = {[200 110 260 200], [200 280 260 370], [440 110 500 200], [440 280 500 370]};
for k = 1:4
    c.tag = tags{k}; c.label = cellNames{k};
    sl_switch_cell(fb, cellNames{k}, xy{k}, c);
end
sl_pc(fb, 'DC_P', 'port', cellNames{1}, 'D');
sl_pc(fb, 'DC_P', 'port', cellNames{3}, 'D');
sl_pc(fb, cellNames{1}, 'S', cellNames{2}, 'D');   % 레그 1 노드
sl_pc(fb, cellNames{3}, 'S', cellNames{4}, 'D');   % 레그 2 노드
sl_pc(fb, cellNames{2}, 'S', 'DC_N', 'port');
sl_pc(fb, cellNames{4}, 'S', 'DC_N', 'port');
sl_pc(fb, cellNames{1}, 'S', 'AC1', 'port');
sl_pc(fb, cellNames{3}, 'S', 'AC2', 'port');
sl_note(fb, noteText, [30 470 640 530], 'box');
set_param(h, 'BackgroundColor', 'white');
end
