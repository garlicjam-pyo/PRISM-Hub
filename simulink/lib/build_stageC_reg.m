function h = build_stageC_reg(sys, name, pos, T, opt)
%BUILD_STAGEC_REG  조정형 Stage C 전력단(동기 벅 + 중간 커패시터 + 양방향 CLLC 직류변압기) 서브시스템을 만든다(TB14).
%
%   h = build_stageC_reg(sys, 'StageC_Regulated', [x1 y1 x2 y2], 'TB')
%
%   외부 포트: DC_P, DC_N(왼쪽, 400 V 버스 = V_A 범위 270–504 V), VO_P, VO_N(오른쪽, 절연된 48 V 전원망)
%   구성(검증 코드 E22의 선택 구조)
%     동기 벅 레그(상측 SB_H·하측 SB_L, 650 V GaN 2병렬) → L_b(DCR 포함) → C_I(중간전압 V_I 173–253 V)
%     → 1차 풀브리지(Q1–Q4, 650 V GaN 2병렬) → C_r1 → L_r1 → 이상 변압기 n:1(1차에 L_m) → L_r2 → C_r2
%     → 2차 풀브리지(S1–S4, 150 V GaN 2병렬) → 출력전류 센서 → C_o
%   CLLC는 공진점(250 kHz) 고정 주파수의 직류변압기로, 보내는 쪽 브리지만 스위칭하고 받는 쪽은 역병렬 다이오드로 도통한다
%   (다이오드 Vf 50 mV·R_d = R_on: 이상 동기정류 근사). 전력 방향은 제어기가 정한다(prism_gate_stageC_reg.m).
%   계측 태그: iL(벅 인덕터), vI(중간전압), ir1(1차 공진전류), im(자화), ir2(2차 공진전류, 1차 쪽 권선 기준이 아닌 2차 실제값),
%             ix(DCX 출력전류), vcr1, vleg1(1차 레그 1 − DC_N), vlegs1(2차 레그 1 − VO_N), vswb(벅 스위치 노드 − DC_N)
%   T : 시험 구조체 이름(문자열). 필드 SB·CP·CS(Ron Goff Vf Rd Goffd Coss), C(n Lr1 Cr1 Lm Lr2 Cr2 Rw1 Rw2 Co CI L RL),
%       x0 = [iL0 vI0 vo0 ix0]
%   opt.iLTag(선택, TB17): 벅 인덕터 전류 태그 이름(기본 'iL'). Stage B(DAB 누설 인덕터 전류 'iL')와 한 모델에 둘 때 바꾼다.

if nargin < 5, opt = struct(); end
tagL = 'iL'; if isfield(opt, 'iLTag'), tagL = opt.iLTag; end
sc = [sys '/' name];
h = add_block('built-in/Subsystem', sc, 'Position', pos);
fl = 'fl_lib/Electrical/';
add_block('nesl_utility/Connection Port', [sc '/DC_P'], 'Position', [30 100 60 120],    'Side', 'Left',  'Port', '1');
add_block('nesl_utility/Connection Port', [sc '/DC_N'], 'Position', [30 560 60 580],    'Side', 'Left',  'Port', '2');
add_block('nesl_utility/Connection Port', [sc '/VO_P'], 'Position', [1760 200 1790 220], 'Side', 'Right', 'Port', '3');
add_block('nesl_utility/Connection Port', [sc '/VO_N'], 'Position', [1760 460 1790 480], 'Side', 'Right', 'Port', '4');

% ---- 동기 벅 ------------------------------------------------------------------------------------------
cb = struct('Ron', [T '.SB.Ron'], 'Goff', [T '.SB.Goff'], 'Vf', [T '.SB.Vf'], 'Rd', [T '.SB.Rd'], 'Goffd', [T '.SB.Goffd'], ...
            'Coss', [T '.SB.Coss'], 'orient', 'down');
sl_switch_cell(sc, 'SB_H_high', [110 150 170 240], setfield(setfield(cb, 'tag', 'gS_BH'), 'label', 'SB_H')); %#ok<SFLD>
sl_switch_cell(sc, 'SB_L_low',  [110 330 170 420], setfield(setfield(cb, 'tag', 'gS_BL'), 'label', 'SB_L')); %#ok<SFLD>
sl_pc(sc, 'SB_H_high', 'D', 'DC_P', 'port');
sl_pc(sc, 'SB_H_high', 'S', 'SB_L_low', 'D');          % 스위치 노드
sl_pc(sc, 'SB_L_low', 'S', 'DC_N', 'port');
sl_add(sc, [fl 'Electrical Elements/Inductor'], 'L_b', [230 270 290 300], 'l', [T '.C.L'], 'r', [T '.C.RL'], ...
    'i_L_specify', 'on', 'i_L', [T '.x0(1)'], 'i_L_priority', 'High');
sl_add(sc, [fl 'Electrical Sensors/Current Sensor'], 'I_L', [320 265 370 305]);
sl_add(sc, [fl 'Electrical Elements/Capacitor'], 'C_I', [410 380 450 440], 'Orientation', 'down', 'c', [T '.C.CI'], 'r', '1e-6', ...
    'vc_specify', 'on', 'vc', [T '.x0(2)'], 'vc_priority', 'High');
sl_add(sc, [fl 'Electrical Sensors/Voltage Sensor'], 'V_I', [470 380 510 440], 'Orientation', 'down');
sl_add(sc, [fl 'Electrical Sensors/Voltage Sensor'], 'V_swb', [200 450 240 510], 'Orientation', 'down');
sl_pc(sc, 'L_b', 'p', 'SB_H_high', 'S');
sl_pc(sc, 'L_b', 'n', 'I_L', 'p');
sl_pc(sc, 'I_L', 'n', 'C_I', 'p');
sl_pc(sc, 'C_I', 'n', 'DC_N', 'port');
sl_pc(sc, 'V_I', 'p', 'C_I', 'p');
sl_pc(sc, 'V_I', 'n', 'C_I', 'n');
sl_pc(sc, 'V_swb', 'p', 'SB_H_high', 'S');
sl_pc(sc, 'V_swb', 'n', 'DC_N', 'port');

% ---- 1차 브리지와 공진망 ----------------------------------------------------------------------------------
build_fullbridge(sc, 'Primary_Bridge', [560 160 720 360], [T '.CP'], {'Q1_leg1_high', 'Q2_leg1_low', 'Q3_leg2_high', 'Q4_leg2_low'}, ...
    {'gC_Q1', 'gC_Q2', 'gC_Q3', 'gC_Q4'}, [T '.CP.Coss'], ...
    sprintf('Stage C 1차 풀브리지(650 V GaN 2병렬): 1차가 보낼 때 250 kHz 50 %% 상보 + 데드타임 t_dp, 2차가 보낼 때는 꺼 두고 다이오드 정류(경부하 두 브리지 구동 모드에서는 같은 위상)'));
sl_pc(sc, 'Primary_Bridge', 'DC_P', 'C_I', 'p');
sl_pc(sc, 'Primary_Bridge', 'DC_N', 'DC_N', 'port');
sl_add(sc, [fl 'Electrical Elements/Capacitor'], 'C_r1', [790 180 850 210], 'c', [T '.C.Cr1'], 'r', '1e-6', ...
    'vc_specify', 'on', 'vc', '0', 'vc_priority', 'High');
sl_add(sc, [fl 'Electrical Elements/Inductor'], 'L_r1', [880 180 940 210], 'l', [T '.C.Lr1'], 'r', [T '.C.Rw1'], ...
    'i_L_specify', 'on', 'i_L', '0', 'i_L_priority', 'High');
sl_add(sc, [fl 'Electrical Sensors/Current Sensor'], 'I_r1', [970 175 1020 215]);
sl_add(sc, [fl 'Electrical Sensors/Voltage Sensor'], 'V_Cr1', [790 100 850 140]);
sl_add(sc, [fl 'Electrical Sensors/Voltage Sensor'], 'V_leg1', [750 390 790 450], 'Orientation', 'down');
sl_pc(sc, 'Primary_Bridge', 'AC1', 'C_r1', 'p');      % i_r1 양의 방향: 1차 레그 1 → C_r1 → L_r1 → 변압기 1+
sl_pc(sc, 'C_r1', 'n', 'L_r1', 'p');
sl_pc(sc, 'L_r1', 'n', 'I_r1', 'p');
sl_pc(sc, 'V_Cr1', 'p', 'C_r1', 'p');
sl_pc(sc, 'V_Cr1', 'n', 'C_r1', 'n');
sl_pc(sc, 'V_leg1', 'p', 'Primary_Bridge', 'AC1');
sl_pc(sc, 'V_leg1', 'n', 'DC_N', 'port');

sl_add(sc, [fl 'Electrical Elements/Ideal Transformer'], 'Xfmr_n1', [1160 220 1220 300], 'n', [T '.C.n']);
sl_add(sc, [fl 'Electrical Sensors/Current Sensor'], 'I_m', [1070 230 1110 270], 'Orientation', 'down');
sl_add(sc, [fl 'Electrical Elements/Inductor'], 'L_m', [1070 300 1110 340], 'Orientation', 'down', 'l', [T '.C.Lm'], 'r', '0', ...
    'i_L_specify', 'on', 'i_L', '0', 'i_L_priority', 'High');
sl_pc(sc, 'I_r1', 'n', 'Xfmr_n1', 'p1');
sl_pc(sc, 'Xfmr_n1', 'n1', 'Primary_Bridge', 'AC2');
sl_pc(sc, 'I_m', 'p', 'Xfmr_n1', 'p1');
sl_pc(sc, 'I_m', 'n', 'L_m', 'p');
sl_pc(sc, 'L_m', 'n', 'Xfmr_n1', 'n1');

sl_add(sc, [fl 'Electrical Elements/Inductor'], 'L_r2', [1270 180 1330 210], 'l', [T '.C.Lr2'], 'r', [T '.C.Rw2'], ...
    'i_L_specify', 'on', 'i_L', '0', 'i_L_priority', 'High');
sl_add(sc, [fl 'Electrical Elements/Capacitor'], 'C_r2', [1360 180 1420 210], 'c', [T '.C.Cr2'], 'r', '1e-6', ...
    'vc_specify', 'on', 'vc', '0', 'vc_priority', 'High');
sl_add(sc, [fl 'Electrical Sensors/Current Sensor'], 'I_r2', [1450 175 1500 215]);
sl_pc(sc, 'Xfmr_n1', 'p2', 'L_r2', 'p');
sl_pc(sc, 'L_r2', 'n', 'C_r2', 'p');
sl_pc(sc, 'C_r2', 'n', 'I_r2', 'p');

% ---- 2차 브리지와 출력 ------------------------------------------------------------------------------------
build_fullbridge(sc, 'Secondary_Bridge', [1530 180 1660 400], [T '.CS'], {'S1_leg1_high', 'S2_leg1_low', 'S3_leg2_high', 'S4_leg2_low'}, ...
    {'gC_S1', 'gC_S2', 'gC_S3', 'gC_S4'}, [T '.CS.Coss'], ...
    sprintf('Stage C 2차 풀브리지(150 V GaN 2병렬): 1차가 보낼 때는 꺼 두고 다이오드 정류(이상 동기정류 근사), 2차가 보낼 때 250 kHz + 데드타임 t_ds'));
sl_pc(sc, 'I_r2', 'n', 'Secondary_Bridge', 'AC1');
sl_pc(sc, 'Xfmr_n1', 'n2', 'Secondary_Bridge', 'AC2');
sl_add(sc, [fl 'Electrical Sensors/Current Sensor'], 'I_x', [1690 195 1730 235]);
sl_add(sc, [fl 'Electrical Elements/Capacitor'], 'C_o', [1700 300 1740 360], 'Orientation', 'down', 'c', [T '.C.Co'], 'r', '1e-6', ...
    'vc_specify', 'on', 'vc', [T '.x0(3)'], 'vc_priority', 'High');
sl_add(sc, [fl 'Electrical Sensors/Voltage Sensor'], 'V_legs1', [1560 430 1600 490], 'Orientation', 'down');
sl_pc(sc, 'Secondary_Bridge', 'DC_P', 'I_x', 'p');     % i_x 양의 방향: DCX → 48 V
sl_pc(sc, 'I_x', 'n', 'C_o', 'p');
sl_pc(sc, 'Secondary_Bridge', 'DC_N', 'C_o', 'n');
sl_pc(sc, 'C_o', 'p', 'VO_P', 'port');
sl_pc(sc, 'C_o', 'n', 'VO_N', 'port');
sl_pc(sc, 'V_legs1', 'p', 'Secondary_Bridge', 'AC1');
sl_pc(sc, 'V_legs1', 'n', 'C_o', 'n');
sl_add(sc, [fl 'Electrical Elements/Electrical Reference'], 'GND_secondary', [1700 520 1740 550]);
sl_pc(sc, 'GND_secondary', 'V', 'C_o', 'n');            % 절연 2차측 전위 고정(1차와 전류 경로 없음)

% ---- 계측 태그 ----------------------------------------------------------------------------------------------
sl_meas(sc, 'I_L',     'I', tagL,     [320 640]);
sl_meas(sc, 'V_I',     'V', 'vI',     [470 640]);
sl_meas(sc, 'V_swb',   'V', 'vswb',   [150 640]);
sl_meas(sc, 'I_r1',    'I', 'ir1',    [970 640]);
sl_meas(sc, 'I_m',     'I', 'im',     [1120 640]);
sl_meas(sc, 'I_r2',    'I', 'ir2',    [1450 640]);
sl_meas(sc, 'I_x',     'I', 'ix',     [1660 640]);
sl_meas(sc, 'V_Cr1',   'V', 'vcr1',   [790 640]);
sl_meas(sc, 'V_leg1',  'V', 'vleg1',  [640 640]);
sl_meas(sc, 'V_legs1', 'V', 'vlegs1', [1290 640]);
Cv = evalin('base', [T '.C']);
sl_note(sc, sprintf(['조정형 Stage C(검증 코드 E22): 동기 벅(100 kHz, L_b %.0f µH)이 중간전압 V_I = n·V_o + DCX 강하를 만들고,\n' ...
    'CLLC(n = %.1f, L_r %.2f µH, C_r %.1f nF, L_m %.1f µH, f_r 250 kHz)는 공진점 고정 주파수의 직류변압기로 V_I를 48 V로 바꾼다.\n' ...
    '보내는 쪽 브리지만 스위칭하고 받는 쪽은 다이오드 정류(이상 동기정류 근사). 48 V 조정·전류 제한·충전 제한은 벅의 듀티로 한다.\n' ...
    'L_m과 데드타임은 레그 출력용량 모델(E22 zvs)로 정했다. 변압기 극성: 1차 레그 1 상측 켬(+V_I) ↔ 2차 레그 1 상측(+V_o).'], ...
    1e6*Cv.L, Cv.n, 1e6*Cv.Lr1, 1e9*Cv.Cr1, 1e6*Cv.Lm), [30 720 1400 790], 'box');
set_param(h, 'BackgroundColor', 'white');
end
