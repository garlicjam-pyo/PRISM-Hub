function h = build_stageB(sys, name, pos, T, opt)
%BUILD_STAGEB  Stage B 직렬 부분전력 조정기 전력단 서브시스템을 만든다.
%
%   h = build_stageB(sys, 'StageB_Regulator', [x1 y1 x2 y2], 'TB')
%   h = build_stageB(..., struct('CossP', 'TB.B.Coss_dp', 'CossS', 'TB.B.Coss_ds'))
%       DAB 1차(400 V 버스 측)·2차(100 V 링크 측) 소자 출력용량을 따로 준다(TB04B).
%       생략하면 두 브리지 모개 [T '.B.Coss_d'](TB03·TB04와 같은 값)를 쓴다.
%       opt.Xfmr(변압기 블록 이름), opt.DabNote(설명 주석의 DAB 정격)도 줄 수 있다(TB08 창 조정 모듈: 4.6:1, ≤ 4 kW).
%       opt.Brake(링크 제동 저항 값 식, 예 'TB.Rbrk')를 주면 링크에 제동 저항과 스위치를 더한다(TB09, 태그 gBrk, 계측 ibrk).
%
%   외부 포트: SER(왼쪽, 직렬 포트 입력 = 경로 쪽 노드 N1), BUS(오른쪽, 400 V 버스 = N2), GND(오른쪽, 버스 기준)
%   구성(노드 N1, N2 = BUS, LINK+, LINK−)
%     C_s           N1(−) – N2(+)            직렬 커패시터. v_bus = v_N1 + v_s
%     H-브리지      LINK± → 레그 A, B         유니폴라 PWM, 스위치 셀 C_oss 1 nF
%     L_h, R_h      레그 A → N2,  레그 B → N1  필터. C_s 전류 = i_h − i_p
%     C_link        LINK+ – LINK−            부유 100 V 링크(2 mF)
%     DAB           BUS/GND → 1차 풀브리지 → L_dab → 이상 변압기 n:1(기본 4:1) → 2차 풀브리지 → LINK±
%   계측 태그: vs(C_s 전압), ih(필터전류), vlink, iL(누설 전류, 1차), ilink(2차 브리지 → 링크 직류전류)
%   T : 시험 구조체 이름(문자열, 예 'TB'). 필드 B(소자값), vs0, ih0, vl0(초기조건)

if nargin < 5, opt = struct(); end
if ~isfield(opt, 'CossP'), opt.CossP = [T '.B.Coss_d']; end
if ~isfield(opt, 'CossS'), opt.CossS = [T '.B.Coss_d']; end
if ~isfield(opt, 'CossNote'), opt.CossNote = 'DAB C_oss 100 pF'; end   % 전력단 설명 주석에 적을 DAB 출력용량
if ~isfield(opt, 'Xfmr'), opt.Xfmr = 'Xfmr_4to1'; end                  % 변압기 블록 이름(권선비를 드러낸다, TB08: Xfmr_4p6to1)
if ~isfield(opt, 'DabNote'), opt.DabNote = '처리전력 ≤ 8 kW'; end        % 전력단 설명 주석의 DAB 정격
sb = [sys '/' name];
h = add_block('built-in/Subsystem', sb, 'Position', pos);
fl = 'fl_lib/Electrical/';
add_block('nesl_utility/Connection Port', [sb '/SER'], 'Position', [30 100 60 120],    'Side', 'Left',  'Port', '1');
add_block('nesl_utility/Connection Port', [sb '/BUS'], 'Position', [1290 100 1320 120], 'Side', 'Right', 'Port', '2');
add_block('nesl_utility/Connection Port', [sb '/GND'], 'Position', [1290 640 1320 660], 'Side', 'Right', 'Port', '3');

% ---- 직렬 포트: C_s와 전압 센서 -----------------------------------------------------------------
sl_add(sb, [fl 'Electrical Elements/Capacitor'], 'C_s', [560 90 620 130], 'Orientation', 'left', ...
    'c', [T '.B.Cs'], 'r', '1e-6', 'vc_specify', 'on', 'vc', [T '.vs0'], 'vc_priority', 'High');
sl_add(sb, [fl 'Electrical Sensors/Voltage Sensor'], 'V_s', [560 10 620 50], 'Orientation', 'left');
sl_pc(sb, 'C_s', 'n', 'SER', 'port');
sl_pc(sb, 'C_s', 'p', 'BUS', 'port');
sl_pc(sb, 'V_s', 'n', 'SER', 'port');
sl_pc(sb, 'V_s', 'p', 'BUS', 'port');

% ---- H-브리지와 필터 ----------------------------------------------------------------------------
build_hbridge(sb, 'HBridge', [300 230 460 390], [T '.B']);
sl_add(sb, [fl 'Electrical Sensors/Current Sensor'], 'I_h', [520 280 570 320]);
sl_add(sb, [fl 'Electrical Elements/Inductor'], 'L_h', [620 285 680 315], 'l', [T '.B.Lh'], 'r', [T '.B.Rh'], ...
    'i_L_specify', 'on', 'i_L', [T '.ih0'], 'i_L_priority', 'High');
sl_pc(sb, 'HBridge', 'A', 'I_h', 'p');                 % i_h 양의 방향: 레그 A → L_h → N2
sl_pc(sb, 'I_h', 'n', 'L_h', 'p');
sl_pc(sb, 'L_h', 'n', 'BUS', 'port');
sl_pc(sb, 'HBridge', 'B', 'SER', 'port');

% ---- 부유 링크 -----------------------------------------------------------------------------------
sl_add(sb, [fl 'Electrical Elements/Capacitor'], 'C_link', [180 260 220 320], 'Orientation', 'down', ...
    'c', [T '.B.Clink'], 'r', '1e-6', 'vc_specify', 'on', 'vc', [T '.vl0'], 'vc_priority', 'High');
sl_add(sb, [fl 'Electrical Sensors/Voltage Sensor'], 'V_link', [110 260 150 320], 'Orientation', 'down');
sl_pc(sb, 'C_link', 'p', 'HBridge', 'LINK_P');
sl_pc(sb, 'C_link', 'n', 'HBridge', 'LINK_N');
sl_pc(sb, 'V_link', 'p', 'C_link', 'p');
sl_pc(sb, 'V_link', 'n', 'C_link', 'n');

% ---- 절연 DAB ------------------------------------------------------------------------------------
build_fullbridge(sb, 'DAB_Secondary', [260 480 420 640], [T '.B'], ...
    {'S1_leg1_high', 'S2_leg1_low', 'S3_leg2_high', 'S4_leg2_low'}, {'gD_S1', 'gD_S2', 'gD_S3', 'gD_S4'}, opt.CossS, ...
    sprintf('DAB 2차 풀브리지(100 V 링크 측): 상태 +1 → S1·S4, −1 → S2·S3. 2차 에지 = 1차 에지 + δ'));
sl_add(sb, [fl 'Electrical Sensors/Current Sensor'], 'I_link', [150 400 200 440], 'Orientation', 'left');
sl_add(sb, [fl 'Electrical Elements/Ideal Transformer'], opt.Xfmr, [520 520 580 600], 'n', [T '.B.n']);
sl_add(sb, [fl 'Electrical Sensors/Current Sensor'], 'I_Ldab', [640 510 690 550], 'Orientation', 'left');
sl_add(sb, [fl 'Electrical Elements/Inductor'], 'L_dab', [740 515 800 545], 'Orientation', 'left', ...
    'l', [T '.B.Ldab'], 'r', [T '.B.Rdab'], 'i_L_specify', 'on', 'i_L', '0', 'i_L_priority', 'High');
build_fullbridge(sb, 'DAB_Primary', [900 480 1060 640], [T '.B'], ...
    {'P1_leg1_high', 'P2_leg1_low', 'P3_leg2_high', 'P4_leg2_low'}, {'gD_P1', 'gD_P2', 'gD_P3', 'gD_P4'}, opt.CossP, ...
    sprintf('DAB 1차 풀브리지(400 V 버스 측): 50 %% 구형파, 상태 +1 → P1·P4, −1 → P2·P3'));
set_param([sb '/DAB_Primary'], 'Orientation', 'left');     % 직류 측(버스)을 오른쪽에 둔다
sl_pc(sb, 'DAB_Secondary', 'DC_P', 'I_link', 'p');         % 링크 직류전류 양의 방향: 2차 브리지 → 링크(+)
sl_pc(sb, 'I_link', 'n', 'C_link', 'p');
sl_pc(sb, 'DAB_Secondary', 'DC_N', 'C_link', 'n');
sl_pc(sb, 'DAB_Secondary', 'AC1', opt.Xfmr, 'p2');
sl_pc(sb, 'DAB_Secondary', 'AC2', opt.Xfmr, 'n2');
sl_pc(sb, 'DAB_Primary', 'AC1', 'L_dab', 'p');             % i_L 양의 방향: 1차 레그 1 → L_dab → 변압기 1+
sl_pc(sb, 'L_dab', 'n', 'I_Ldab', 'p');
sl_pc(sb, 'I_Ldab', 'n', opt.Xfmr, 'p1');
sl_pc(sb, opt.Xfmr, 'n1', 'DAB_Primary', 'AC2');
sl_pc(sb, 'DAB_Primary', 'DC_P', 'BUS', 'port');
sl_pc(sb, 'DAB_Primary', 'DC_N', 'GND', 'port');

% ---- (선택) 링크 제동 저항: 링크(+) → 전류 센서 → R_brk → 스위치 → 링크(−), 게이트 태그 gBrk (TB09) ----------------
if isfield(opt, 'Brake') && ~isempty(opt.Brake)
    sl_add(sb, [fl 'Electrical Sensors/Current Sensor'], 'I_brk', [170 145 220 185]);
    sl_add(sb, [fl 'Electrical Elements/Resistor'], 'R_brk', [245 155 295 175], 'R', opt.Brake);
    sl_switch_cell(sb, 'S_BRK', [320 140 400 190], struct('tag', 'gBrk', 'label', 'BRK', 'Ron', [T '.B.Ron'], ...
        'Goff', [T '.B.Goff'], 'Vf', [T '.B.Vf'], 'Rd', [T '.B.Rd'], 'Goffd', [T '.B.Goffd'], 'Coss', '', 'orient', 'right'));
    sl_pc(sb, 'C_link', 'p', 'I_brk', 'p');                % 제동 전류 양의 방향: 링크(+) → 저항
    sl_pc(sb, 'I_brk', 'n', 'R_brk', 'p');
    sl_pc(sb, 'R_brk', 'n', 'S_BRK', 'D');
    sl_pc(sb, 'S_BRK', 'S', 'C_link', 'n');
    sl_meas(sb, 'I_brk', 'I', 'ibrk', [1160 720]);
    sl_note(sb, sprintf('링크 제동 저항(선택, R2 보호): 강등 중 링크전압을 빨리 낮추거나\nDAB 고장 때 링크를 110 V 아래로 붙잡는다(게이트 gBrk)'), [430 140 760 175]);
end

% ---- 계측 태그 -----------------------------------------------------------------------------------
sl_meas(sb, 'V_s',    'V', 'vs',    [560 720]);
sl_meas(sb, 'I_h',    'I', 'ih',    [760 720]);
sl_meas(sb, 'V_link', 'V', 'vlink', [100 720]);
sl_meas(sb, 'I_link', 'I', 'ilink', [300 720]);
sl_meas(sb, 'I_Ldab', 'I', 'iL',    [960 720]);

sl_note(sb, sprintf(['Stage B 직렬 부분전력 조정기: v_bus = V_A − R·i_p − L·di_p/dt + v_s.\n' ...
    'H-브리지가 부유 링크(100 V)로 직렬전압 v_s(±90 V)를 만들고, DAB가 그 링크 전력을 버스와 교환한다(%s).\n' ...
    '스위치 셀: H-브리지 C_oss 1 nF, %s, 데드타임 50 ns(H)·100 ns(DAB). 게이트는 전역 태그 gB_*, gD_*'], opt.DabNote, opt.CossNote), ...
    [30 790 1100 850], 'box');
set_param(h, 'BackgroundColor', 'white');
end
