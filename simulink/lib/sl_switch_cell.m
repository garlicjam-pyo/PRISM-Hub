function h = sl_switch_cell(sys, name, pos, c)
%SL_SWITCH_CELL  스위치 셀(전력 반도체 1개) 서브시스템을 만든다.
%
%   h = sl_switch_cell(sys, 'S1_VIN_A', [x1 y1 x2 y2], c)
%
%   셀 구성(Simscape Foundation 소자만 사용 — 릴리스·툴박스 의존성 최소화)
%     D ── [Switch: R_on, G_off] ── S       게이트 신호 > 0.5 이면 도통
%     D ──|<── S  역병렬(바디) 다이오드      애노드 = S, 캐소드 = D  (Vf, R_d)
%     D ──||── S  출력용량 C_oss(선택)      데드타임 동안 레그 노드 전압을 정한다
%   게이트는 신호선 대신 전역 Goto/From 태그(c.tag)로 받는다. 회로도에는 전력 배선만 보이고,
%   어느 게이트 신호를 쓰는지는 셀 아이콘에 태그 이름으로 표시된다.
%
%   c 필드
%     tag    게이트 태그 이름(예 'gA_P1_S1')
%     label  아이콘 표시 이름(예 'S1')
%     Ron, Goff, Vf, Rd, Goffd  : 마스크 파라미터 값(문자열 식, 예 'TB.A.Rds')
%     Coss   : 출력용량 식(문자열). 빈 값('')이면 출력용량을 넣지 않는다.
%     orient : 셀 방향 'right'(D 왼쪽, S 오른쪽, 기본) | 'left' | 'up' | 'down'

if ~isfield(c, 'orient'), c.orient = 'right'; end
if ~isfield(c, 'Coss'),   c.Coss = ''; end
cell = [sys '/' name];
h = add_block('built-in/Subsystem', cell, 'Position', pos);

% ---- 내부 블록 ------------------------------------------------------------------------
add_block('nesl_utility/Connection Port', [cell '/D'], 'Position', [30 100 60 120], 'Side', 'Left');
add_block('nesl_utility/Connection Port', [cell '/S'], 'Position', [470 100 500 120], 'Side', 'Right');
add_block('simulink/Signal Routing/From', [cell '/Gate'], 'Position', [30 30 150 50], 'GotoTag', c.tag);
add_block('nesl_utility/Simulink-PS Converter', [cell '/Gate_PS'], 'Position', [190 30 220 50]);
try   % 게이트는 구간별 상수 신호: 필터 없이 그대로 쓴다
    set_param([cell '/Gate_PS'], 'FilteringAndDerivatives', 'zero');
catch
end
add_block('fl_lib/Electrical/Electrical Elements/Switch', [cell '/SW'], 'Position', [250 85 310 135], ...
    'R_closed', 'Ron', 'G_open', 'Goff', 'Threshold', '0.5');
add_block('fl_lib/Electrical/Electrical Elements/Diode', [cell '/D_body'], 'Position', [250 170 310 210], ...
    'Orientation', 'left', 'Vf', 'Vf', 'Ron', 'Rd', 'Goff', 'Goffd');
add_line(cell, 'Gate/1', 'Gate_PS/1');
simscape.addConnection([cell '/Gate_PS'], 'output', [cell '/SW'], 'vT');
simscape.addConnection([cell '/D'], 'port', [cell '/SW'], 'p');
simscape.addConnection([cell '/SW'], 'n', [cell '/S'], 'port');
simscape.addConnection([cell '/D_body'], 'n', [cell '/D'], 'port');   % 캐소드 = 드레인
simscape.addConnection([cell '/D_body'], 'p', [cell '/S'], 'port');   % 애노드 = 소스
if ~isempty(c.Coss)
    add_block('fl_lib/Electrical/Electrical Elements/Capacitor', [cell '/C_oss'], 'Position', [250 240 310 280], ...
        'c', 'Coss', 'r', '1e-6');
    simscape.addConnection([cell '/C_oss'], 'p', [cell '/D'], 'port');
    simscape.addConnection([cell '/C_oss'], 'n', [cell '/S'], 'port');
end
nt = Simulink.Annotation([cell '/note']);
nt.Text = sprintf(['스위치 셀: 이상 스위치(R_on, G_off) + 역병렬 바디 다이오드(Vf, R_d)%s\n' ...
                   '게이트: 전역 태그 "%s" (> 0.5 이면 도통)'], ...
                   ternary(isempty(c.Coss), '', ' + 출력용량 C_oss'), c.tag);
nt.Position = [30 300 500 340];
nt.Interpreter = 'off';

% ---- 마스크: 소자 파라미터를 셀 대화상자에서 보고 바꿀 수 있게 한다 -----------------------
mk = Simulink.Mask.create(cell);
mk.Type = 'PRISM-Hub switch cell';
mk.Description = sprintf('전력 반도체 스위치 셀 %s. 게이트 태그 %s.', c.label, c.tag);
mk.addParameter('Type', 'edit', 'Name', 'Ron',   'Prompt', '도통 저항 R_on [Ohm]',          'Value', c.Ron);
mk.addParameter('Type', 'edit', 'Name', 'Goff',  'Prompt', '차단 컨덕턴스 G_off [S]',       'Value', c.Goff);
mk.addParameter('Type', 'edit', 'Name', 'Vf',    'Prompt', '다이오드 순방향 전압 Vf [V]',    'Value', c.Vf);
mk.addParameter('Type', 'edit', 'Name', 'Rd',    'Prompt', '다이오드 도통 저항 R_d [Ohm]',   'Value', c.Rd);
mk.addParameter('Type', 'edit', 'Name', 'Goffd', 'Prompt', '다이오드 차단 컨덕턴스 [S]',     'Value', c.Goffd);
if ~isempty(c.Coss)
    mk.addParameter('Type', 'edit', 'Name', 'Coss', 'Prompt', '출력용량 C_oss [F]', 'Value', c.Coss);
end
mk.IconUnits = 'normalized';
% 아이콘: 스위치 + 바디 다이오드(애노드 S → 캐소드 D). 아이콘은 블록 방향을 따라 회전하지 않으므로,
% 기준 그림(D 왼쪽, S 오른쪽)의 좌표 (x: D→S, y: 수직)를 블록 방향에 맞게 변환해 그린다.
switch c.orient
    case 'left',  TX = @(x, y) 1 - x; TY = @(x, y) y;        % D 오른쪽, S 왼쪽
    case 'down',  TX = @(x, y) y;     TY = @(x, y) 1 - x;    % D 위, S 아래
    case 'up',    TX = @(x, y) y;     TY = @(x, y) x;        % D 아래, S 위
    otherwise,    TX = @(x, y) x;     TY = @(x, y) y;        % D 왼쪽, S 오른쪽
end
v2s = @(v) ['[' sprintf('%.2f ', v) ']'];
seg = @(x, y) sprintf('%s,%s', v2s(TX(x, y)), v2s(TY(x, y)));
cmd = sprintf('plot(%s,%s,%s);\nplot(%s,%s);\nplot(%s,%s);\n', ...
    seg([0.05 0.35], [0.50 0.50]), seg([0.35 0.65], [0.50 0.74]), seg([0.65 0.95], [0.50 0.50]), ...   % 스위치
    seg([0.20 0.20 0.42], [0.50 0.20 0.20]), seg([0.58 0.80 0.80], [0.20 0.20 0.50]), ...              % 다이오드 연결선
    seg([0.42 0.58 0.58 0.42], [0.20 0.10 0.30 0.20]), seg([0.42 0.42], [0.10 0.30]));                 % 다이오드
if any(strcmp(c.orient, {'right', 'left'}))      % 가로 셀만 아이콘 안에 이름 표시(세로 셀은 블록 이름으로 충분)
    cmd = [cmd sprintf('text(0.5,0.80,''%s'',''horizontalAlignment'',''center'',''texmode'',''off'');\n', c.label)];
end
mk.Display = [cmd 'port_label(''LConn'',1,''D'');' newline 'port_label(''RConn'',1,''S'');'];
set_param(h, 'Orientation', c.orient, 'BackgroundColor', 'lightBlue', ...
    'AttributesFormatString', ['gate: ' c.tag]);   % 블록 이름 아래에 게이트 태그 표시
end

function s = ternary(cond, a, b)
if cond, s = a; else, s = b; end
end
