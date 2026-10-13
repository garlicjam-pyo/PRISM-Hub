function h = build_stageC(sys, name, pos, T)
%BUILD_STAGEC  Stage C 대칭 CLLC(400 V → 48 V) 전력단 서브시스템을 만든다.
%
%   h = build_stageC(sys, 'StageC_CLLC', [x1 y1 x2 y2], 'TB')
%
%   외부 포트: DC_P, DC_N(왼쪽, 400 V 버스), VO_P, VO_N(오른쪽, 절연된 48 V 출력)
%   구성
%     1차 풀브리지(Q1–Q4, C_oss 100 pF) → C_r1 → L_r1 → 이상 변압기 25/3:1(1차에 자화 인덕턴스 L_m 병렬)
%     → L_r2 = L_r1/n², C_r2 = C_r1·n²(대칭 공진망) → 다이오드 정류 브리지(동기정류 근사: Vf·R_on 작게) → C_o
%   계측 태그: ir1(1차 공진전류), im(자화 전류), ir2(2차 공진전류), vcr1(C_r1 전압), vleg1(1차 레그 1 노드 − DC_N)
%   T : 시험 구조체 이름(문자열). 필드 C(소자값: n Lr1 Cr1 Lm Lr2 Cr2 Co Coss Ron Goff Vf Rd Goffd Vf_rect Ron_rect), vo0

sc = [sys '/' name];
h = add_block('built-in/Subsystem', sc, 'Position', pos);
fl = 'fl_lib/Electrical/';
add_block('nesl_utility/Connection Port', [sc '/DC_P'], 'Position', [30 100 60 120],    'Side', 'Left',  'Port', '1');
add_block('nesl_utility/Connection Port', [sc '/DC_N'], 'Position', [30 520 60 540],    'Side', 'Left',  'Port', '2');
add_block('nesl_utility/Connection Port', [sc '/VO_P'], 'Position', [1420 200 1450 220], 'Side', 'Right', 'Port', '3');
add_block('nesl_utility/Connection Port', [sc '/VO_N'], 'Position', [1420 420 1450 440], 'Side', 'Right', 'Port', '4');

% ---- 1차 브리지와 1차 공진망 ----------------------------------------------------------------------
build_fullbridge(sc, 'Primary_Bridge', [130 160 290 320], [T '.C'], {'Q1_leg1_high', 'Q2_leg1_low', 'Q3_leg2_high', 'Q4_leg2_low'}, ...
    {'gC_Q1', 'gC_Q2', 'gC_Q3', 'gC_Q4'}, [T '.C.Coss'], ...
    sprintf('Stage C 1차 풀브리지: 250 kHz 50 %% 상보, 데드타임 50 ns. 상태 +1 → Q1·Q4, −1 → Q2·Q3'));
sl_pc(sc, 'Primary_Bridge', 'DC_P', 'DC_P', 'port');
sl_pc(sc, 'Primary_Bridge', 'DC_N', 'DC_N', 'port');
sl_add(sc, [fl 'Electrical Elements/Capacitor'], 'C_r1', [370 180 430 210], 'c', [T '.C.Cr1'], 'r', '1e-6', ...
    'vc_specify', 'on', 'vc', '0', 'vc_priority', 'High');
sl_add(sc, [fl 'Electrical Elements/Inductor'], 'L_r1', [460 180 520 210], 'l', [T '.C.Lr1'], 'r', '0', ...
    'i_L_specify', 'on', 'i_L', '0', 'i_L_priority', 'High');
sl_add(sc, [fl 'Electrical Sensors/Current Sensor'], 'I_r1', [550 175 600 215]);
sl_add(sc, [fl 'Electrical Sensors/Voltage Sensor'], 'V_Cr1', [370 100 430 140]);
sl_add(sc, [fl 'Electrical Sensors/Voltage Sensor'], 'V_leg1', [330 330 370 390], 'Orientation', 'down');
sl_pc(sc, 'Primary_Bridge', 'AC1', 'C_r1', 'p');      % i_r1 양의 방향: 레그 1 → C_r1 → L_r1 → 변압기 1+
sl_pc(sc, 'C_r1', 'n', 'L_r1', 'p');
sl_pc(sc, 'L_r1', 'n', 'I_r1', 'p');
sl_pc(sc, 'V_Cr1', 'p', 'C_r1', 'p');
sl_pc(sc, 'V_Cr1', 'n', 'C_r1', 'n');
sl_pc(sc, 'V_leg1', 'p', 'Primary_Bridge', 'AC1');
sl_pc(sc, 'V_leg1', 'n', 'DC_N', 'port');

% ---- 변압기와 자화 인덕턴스 -------------------------------------------------------------------------
sl_add(sc, [fl 'Electrical Elements/Ideal Transformer'], 'Xfmr_25to3', [740 220 800 300], 'n', [T '.C.n']);
sl_add(sc, [fl 'Electrical Sensors/Current Sensor'], 'I_m', [650 230 690 270], 'Orientation', 'down');
sl_add(sc, [fl 'Electrical Elements/Inductor'], 'L_m', [650 300 690 340], 'Orientation', 'down', 'l', [T '.C.Lm'], 'r', '0', ...
    'i_L_specify', 'on', 'i_L', '0', 'i_L_priority', 'High');
sl_pc(sc, 'I_r1', 'n', 'Xfmr_25to3', 'p1');
sl_pc(sc, 'Xfmr_25to3', 'n1', 'Primary_Bridge', 'AC2');
sl_pc(sc, 'I_m', 'p', 'Xfmr_25to3', 'p1');           % 자화 가지: 1차 단자 사이
sl_pc(sc, 'I_m', 'n', 'L_m', 'p');
sl_pc(sc, 'L_m', 'n', 'Xfmr_25to3', 'n1');

% ---- 2차 공진망과 정류 ------------------------------------------------------------------------------
sl_add(sc, [fl 'Electrical Elements/Inductor'], 'L_r2', [860 180 920 210], 'l', [T '.C.Lr2'], 'r', '0', ...
    'i_L_specify', 'on', 'i_L', '0', 'i_L_priority', 'High');
sl_add(sc, [fl 'Electrical Elements/Capacitor'], 'C_r2', [950 180 1010 210], 'c', [T '.C.Cr2'], 'r', '1e-6', ...
    'vc_specify', 'on', 'vc', '0', 'vc_priority', 'High');
sl_add(sc, [fl 'Electrical Sensors/Current Sensor'], 'I_r2', [1040 175 1090 215]);
sl_pc(sc, 'Xfmr_25to3', 'p2', 'L_r2', 'p');
sl_pc(sc, 'L_r2', 'n', 'C_r2', 'p');
sl_pc(sc, 'C_r2', 'n', 'I_r2', 'p');

rb = [sc '/Rectifier'];
add_block('built-in/Subsystem', rb, 'Position', [1140 180 1280 440], 'BackgroundColor', 'white');
add_block('nesl_utility/Connection Port', [rb '/AC_P'],  'Position', [30 80 60 100],   'Side', 'Left',  'Port', '1');
add_block('nesl_utility/Connection Port', [rb '/AC_N'],  'Position', [30 300 60 320],  'Side', 'Left',  'Port', '2');
add_block('nesl_utility/Connection Port', [rb '/OUT_P'], 'Position', [420 30 450 50],  'Side', 'Right', 'Port', '3');
add_block('nesl_utility/Connection Port', [rb '/OUT_N'], 'Position', [420 360 450 380], 'Side', 'Right', 'Port', '4');
dprm = {'Vf', [T '.C.Vf_rect'], 'Ron', [T '.C.Ron_rect'], 'Goff', '1e-8'};
sl_add(rb, [fl 'Electrical Elements/Diode'], 'D1_ACP_OUTP', [160 40 220 80],   'Orientation', 'up',   dprm{:});
sl_add(rb, [fl 'Electrical Elements/Diode'], 'D2_OUTN_ACP', [160 140 220 180], 'Orientation', 'up',   dprm{:});
sl_add(rb, [fl 'Electrical Elements/Diode'], 'D3_ACN_OUTP', [300 40 360 80],   'Orientation', 'up',   dprm{:});
sl_add(rb, [fl 'Electrical Elements/Diode'], 'D4_OUTN_ACN', [300 260 360 300], 'Orientation', 'up',   dprm{:});
sl_pc(rb, 'D1_ACP_OUTP', 'p', 'AC_P', 'port');  sl_pc(rb, 'D1_ACP_OUTP', 'n', 'OUT_P', 'port');
sl_pc(rb, 'D2_OUTN_ACP', 'p', 'OUT_N', 'port'); sl_pc(rb, 'D2_OUTN_ACP', 'n', 'AC_P', 'port');
sl_pc(rb, 'D3_ACN_OUTP', 'p', 'AC_N', 'port');  sl_pc(rb, 'D3_ACN_OUTP', 'n', 'OUT_P', 'port');
sl_pc(rb, 'D4_OUTN_ACN', 'p', 'OUT_N', 'port'); sl_pc(rb, 'D4_OUTN_ACN', 'n', 'AC_N', 'port');
sl_note(rb, sprintf('2차 정류 브리지(동기정류 근사: Vf 1 mV, R_on 1 mΩ)\nD1·D4: i_r2 > 0, D2·D3: i_r2 < 0'), [30 400 450 440]);
sl_pc(sc, 'I_r2', 'n', 'Rectifier', 'AC_P');
sl_pc(sc, 'Xfmr_25to3', 'n2', 'Rectifier', 'AC_N');
sl_add(sc, [fl 'Electrical Elements/Capacitor'], 'C_o', [1320 280 1360 340], 'Orientation', 'down', 'c', [T '.C.Co'], 'r', '1e-6', ...
    'vc_specify', 'on', 'vc', [T '.vo0'], 'vc_priority', 'High');
sl_pc(sc, 'Rectifier', 'OUT_P', 'C_o', 'p');
sl_pc(sc, 'Rectifier', 'OUT_N', 'C_o', 'n');
sl_pc(sc, 'C_o', 'p', 'VO_P', 'port');
sl_pc(sc, 'C_o', 'n', 'VO_N', 'port');
% 절연 2차측은 변압기로만 1차와 이어지므로 전위가 정해지지 않는다 → 출력 음극에 기준을 둔다
% (1차 기준과 사이에 전류 경로가 없으므로 회로 동작에는 영향이 없다)
sl_add(sc, [fl 'Electrical Elements/Electrical Reference'], 'GND_secondary', [1320 380 1360 410]);
sl_pc(sc, 'GND_secondary', 'V', 'C_o', 'n');

% ---- 계측 태그 ---------------------------------------------------------------------------------
sl_meas(sc, 'I_r1',   'I', 'ir1',   [550 620]);
sl_meas(sc, 'I_m',    'I', 'im',    [760 620]);
sl_meas(sc, 'I_r2',   'I', 'ir2',   [970 620]);
sl_meas(sc, 'V_Cr1',  'V', 'vcr1',  [340 620]);
sl_meas(sc, 'V_leg1', 'V', 'vleg1', [130 620]);
sl_note(sc, sprintf(['Stage C 대칭 CLLC: 공진점(f_s = f_r = 1/(2π√(L_r1·C_r1)) = 250 kHz) 고정 주파수로 운전 → 이득 ≈ 1(고정이득 400 → 48 V).\n' ...
    'L_r1 11 µH, C_r1 36.8 nF, L_m 66 µH(L_m/L_r = 6), 2차는 1차 환산이 같은 대칭 공진망. 1차는 공진전류로 영전압 스위칭(ZVS).']), ...
    [30 700 1200 750], 'box');
set_param(h, 'BackgroundColor', 'white');
end
