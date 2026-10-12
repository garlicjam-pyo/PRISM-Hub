function h = build_stageA_phase(sys, name, pos, k, A)
%BUILD_STAGEA_PHASE  Stage A 한 위상(2:1 공진 스위치드 커패시터) 서브시스템을 만든다.
%
%   h = build_stageA_phase(sys, 'StageA_Phase1', [x1 y1 x2 y2], 1, 'TB.A')
%
%   외부 포트: VIN(배터리 +), GND(배터리 −), VOUT(V_A 노드 = 2:1 출력)
%   내부 결선(노드 VIN, A, B, VOUT, GND)
%     S1: VIN → A      S2: A → VOUT      S3: VOUT → B      S4: B → GND
%     A ─ R_misc ─ L_r ─ (전류 센서 i_C) ─ C_fly ─ B          (공진 직렬 경로)
%   전반주기(S1·S3): VIN → A → L_r → C_fly → B → VOUT   (C_fly가 출력과 직렬로 충전)
%   후반주기(S2·S4): GND → B → C_fly → L_r → A → VOUT   (C_fly가 출력으로 방전)
%   두 경로 모두 스위치 2개를 지나므로 경로 저항 = 2·R_ds + ESR + R_L + R_misc(설계 16 mΩ).
%
%   k : 위상 번호(1–8). 게이트 태그 gA_P<k>_S<n>, 계측 태그 iA_P<k>(공진전류), vCf_P<k>(C_fly 전압).
%   A : 파라미터 구조체 이름(문자열, 예 'TB.A'). 필드 Rds Goff Vf Rd Goffd Lr RL Cfly ESR Rmisc vC0.

ph = [sys '/' name];
h = add_block('built-in/Subsystem', ph, 'Position', pos);

% ---- 외부 포트 -------------------------------------------------------------------------
add_block('nesl_utility/Connection Port', [ph '/VIN'],  'Position', [30 100 60 120],  'Side', 'Left',  'Port', '1');
add_block('nesl_utility/Connection Port', [ph '/GND'],  'Position', [30 520 60 540],  'Side', 'Left',  'Port', '2');
add_block('nesl_utility/Connection Port', [ph '/VOUT'], 'Position', [700 310 730 330], 'Side', 'Right', 'Port', '3');

% ---- 스위치 셀 4개 ------------------------------------------------------------------------
c = struct('Ron', [A '.Rds'], 'Goff', [A '.Goff'], 'Vf', [A '.Vf'], 'Rd', [A '.Rd'], 'Goffd', [A '.Goffd'], 'Coss', '');
c.tag = sprintf('gA_P%d_S1', k); c.label = 'S1'; c.orient = 'right';
sl_switch_cell(ph, 'S1_VIN_A',  [130 80 250 140], c);
c.tag = sprintf('gA_P%d_S2', k); c.label = 'S2'; c.orient = 'right';
sl_switch_cell(ph, 'S2_A_VOUT', [440 80 560 140], c);
c.tag = sprintf('gA_P%d_S3', k); c.label = 'S3'; c.orient = 'left';
sl_switch_cell(ph, 'S3_VOUT_B', [440 500 560 560], c);
c.tag = sprintf('gA_P%d_S4', k); c.label = 'S4'; c.orient = 'left';
sl_switch_cell(ph, 'S4_B_GND',  [130 500 250 560], c);

% ---- 공진 직렬 경로(A → B, 세로 배치) --------------------------------------------------------
fl = 'fl_lib/Electrical/Electrical Elements/';
sl_add(ph, [fl 'Resistor'],  'R_misc', [320 170 350 210], 'Orientation', 'down', 'R', [A '.Rmisc']);
sl_add(ph, [fl 'Inductor'],  'L_r',    [320 240 350 280], 'Orientation', 'down', 'l', [A '.Lr'], 'r', [A '.RL'], ...
    'i_L_specify', 'on', 'i_L', '0', 'i_L_priority', 'High');
sl_add(ph, 'fl_lib/Electrical/Electrical Sensors/Current Sensor', 'I_Cfly', [320 310 350 350], 'Orientation', 'down');
sl_add(ph, [fl 'Capacitor'], 'C_fly',  [320 390 350 430], 'Orientation', 'down', 'c', [A '.Cfly'], 'r', [A '.ESR'], ...
    'vc_specify', 'on', 'vc', [A '.vC0'], 'vc_priority', 'High');
sl_add(ph, 'fl_lib/Electrical/Electrical Sensors/Voltage Sensor', 'V_Cfly', [390 390 420 430], 'Orientation', 'down');

% ---- 결선 ---------------------------------------------------------------------------------
sl_pc(ph, 'VIN', 'port', 'S1_VIN_A', 'D');
sl_pc(ph, 'S1_VIN_A', 'S', 'S2_A_VOUT', 'D');          % 노드 A
sl_pc(ph, 'S1_VIN_A', 'S', 'R_misc', 'p');
sl_pc(ph, 'R_misc', 'n', 'L_r', 'p');
sl_pc(ph, 'L_r', 'n', 'I_Cfly', 'p');                  % i_C 양의 방향: A → B
sl_pc(ph, 'I_Cfly', 'n', 'C_fly', 'p');
sl_pc(ph, 'C_fly', 'n', 'S4_B_GND', 'D');              % 노드 B
sl_pc(ph, 'C_fly', 'n', 'S3_VOUT_B', 'S');
sl_pc(ph, 'S4_B_GND', 'S', 'GND', 'port');
sl_pc(ph, 'S2_A_VOUT', 'S', 'VOUT', 'port');
sl_pc(ph, 'S3_VOUT_B', 'D', 'VOUT', 'port');
sl_pc(ph, 'V_Cfly', 'p', 'C_fly', 'p');
sl_pc(ph, 'V_Cfly', 'n', 'C_fly', 'n');

% ---- 계측(전역 태그) ------------------------------------------------------------------------
sl_meas(ph, 'I_Cfly', 'I', sprintf('iA_P%d', k),  [560 230]);
sl_meas(ph, 'V_Cfly', 'V', sprintf('vCf_P%d', k), [560 400]);

% ---- 주석 ---------------------------------------------------------------------------------
sl_note(ph, sprintf(['Stage A 위상 %d — 2:1 공진 스위치드 커패시터\n' ...
    '전반주기 S1·S3: VIN → A → L_r → C_fly → B → VOUT (C_fly 직렬 충전)\n' ...
    '후반주기 S2·S4: GND → B → C_fly → L_r → A → VOUT (C_fly 방전)\n' ...
    '경로 저항 = 2·R_ds + ESR + R_L + R_misc, 공진 f_r0 = 1/(2π√(L_r·C_fly)) ≈ 150 kHz'], k), ...
    [30 600 700 680], 'box');
set_param(h, 'BackgroundColor', 'white');
end
