function build_TB13()
%BUILD_TB13  TB13 테스트벤치 모델(TB13_R2_FaultMod_TA.slx)을 처음부터 만든다.
%
%   H-브리지 고장 강등 중 DAB 순환전류를 묶는 강등 방식(검증 코드 E20의 P3)을 회로에서 확인한다.
%   TB09와 같은 회로·상태기계에 다음을 더한다: 상태기계 파라미터 57–60(전압비 정합 유지, 일시 감발, 시간 상한 → 이중 고장),
%   게이트 쪽 DAB 고장 모드 변조 지령 블록 DAB_EPS_Map(ctrl/prism_dab_eps_map.m)과 1차 레그 2 지연 게이트 생성기
%   (ctrl/prism_gate_stageB_e.m). 강등 상태(9–11)가 아니면 TB09와 같은 게이트를 낸다.
%   구성(TB08 + 보호 기능, TB09와 같음)
%     V_A(이상 V_bat/2) ── R_path ── L_path ── 경로전류 센서 ──┬── StageB_Regulator(SER → BUS, 링크 제동 저항 포함) ──┬── 버스
%                                                               ├── 바이패스 주 스위치(150 V GaN 역직렬, gByp) ──────────┤
%                                                               └── 소프트 투입 가변 저항(상태기계 지령 R) ───────────────┘
%     버스: C_b ∥ RC 감쇠기(1.6 mF·48.6 mΩ) ∥ 정전력 부하(400 V 부하 분리 신호) ∥ DAB 손실 등가 ∥ 버스전압 센서
%     Controller_StageB: R2_Supervisor(측정 기반 상태기계) + 채택 제어기(보조 링크전류 지령 입력)
%     Gate_StageB: 게이트 생성기 → 보호 게이트 재정의(하드웨어 비교기, 고장 주입, 모드) → 게이트 14개
%   실행: prism_run('build_TB13')  →  prism_run('run_TB13')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB13_R2_FaultMod_TA';
evalin('base', 'clear TB13_opts TB13_case');
run(fullfile(here, 'TB13_init.m'));
sl_model_new(mdl, 'TB13_init.m');

sl_note(mdl, 'TB13 — DAB 고장 모드 변조(R2-W460): 스위칭 반영 첨두 표 + EPS 전이 변화율 상한 + 전이 여유를 넣은 설계 상한으로 1.5배', [30 10 1100 40], 'title');

% ---- 전력 회로 ----------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_A', [70 230 110 290], 'Orientation', 'down', 'v0', 'TB.VA');
sl_add(mdl, [fl 'Electrical Elements/Electrical Reference'], 'GND', [70 440 110 470]);
sl_solver(mdl, 'Solver', [10 360 50 390], 'GND', 'V', 3);
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_path', [150 160 200 180], 'R', 'TB.Rpath');
sl_add(mdl, [fl 'Electrical Elements/Inductor'], 'L_path', [230 160 280 180], 'l', 'TB.Lpath', 'r', '0', ...
    'i_L_specify', 'on', 'i_L', 'TB.ip0', 'i_L_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_path', [310 150 360 190]);
build_stageB(mdl, 'StageB_Regulator', [420 140 660 380], 'TB', ...
    struct('CossP', 'TB.B.Coss_dp', 'CossS', 'TB.B.Coss_ds', ...
           'CossNote', 'DAB C_oss 1차 335 pF·2차 1371 pF, 소자 역방향 도통 2 V', ...
           'Xfmr', 'Xfmr_4p6to1', 'DabNote', '창 조정 R2-W460: 권선비 4.6:1, 누설 14.68 µH, 정격 4 kW', 'Brake', 'TB.Rbrk'));
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_bus', [760 240 800 300], 'Orientation', 'down', ...
    'c', 'TB.Cb', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vb0', 'vc_priority', 'High');
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_dmp', [690 420 740 440], 'R', 'TB.Rdmp');
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_dmp', [760 400 800 460], 'Orientation', 'down', ...
    'c', 'TB.Cdmp', 'r', '0', 'vc_specify', 'on', 'vc', 'TB.vcd0', 'vc_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_bus', [840 240 880 300], 'Orientation', 'down');
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load', [930 240 970 300], 'Orientation', 'down');
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_dabloss', [1020 240 1060 300], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iload_PS', [940 200 970 220]);
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iloss_PS', [1030 200 1060 220]);

% ---- 바이패스: 주 스위치(역직렬 GaN 셀 2개) ∥ 소프트 투입 가변 저항 -----------------------------------------
cb = struct('tag', 'gByp', 'Ron', 'TB.Rbyp_cell', 'Goff', 'TB.B.Goff', 'Vf', 'TB.Vf_byp', 'Rd', 'TB.Rd_byp', ...
    'Goffd', 'TB.B.Goffd', 'Coss', '');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_byp', [430 60 480 100]);
sl_switch_cell(mdl, 'S_BYP_1', [520 55 600 105], setfield(setfield(cb, 'label', 'BYP1'), 'orient', 'right')); %#ok<SFLD>
sl_switch_cell(mdl, 'S_BYP_2', [640 55 720 105], setfield(setfield(cb, 'label', 'BYP2'), 'orient', 'left'));  %#ok<SFLD>
sl_add(mdl, [fl 'Electrical Elements/Variable Resistor'], 'R_soft', [700 140 750 156], 'Rmin', '1e-4');   % 바이패스 셀 이름표 아래(겹침 방지)
sl_add(mdl, 'simulink/Signal Routing/From', 'sup_from', [380 115 450 135], 'GotoTag', 'r2_sup', 'ShowName', 'off');
sl_add(mdl, 'simulink/Signal Routing/Selector', 'Rsoft_sel', [465 115 485 135], 'IndexParamArray', {'7'}, 'InputPortWidth', '12');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'Rsoft_PS', [520 115 550 135]);
sl_line(mdl, 'sup_from/1', 'Rsoft_sel/1');
sl_line(mdl, 'Rsoft_sel/1', 'Rsoft_PS/1');

sl_pc(mdl, 'V_A', 'p', 'R_path', 'p');
sl_pc(mdl, 'V_A', 'n', 'GND', 'V');
sl_pc(mdl, 'R_path', 'n', 'L_path', 'p');
sl_pc(mdl, 'L_path', 'n', 'I_path', 'p');
sl_pc(mdl, 'I_path', 'n', 'StageB_Regulator', 'SER');
sl_pc(mdl, 'I_byp', 'p', 'I_path', 'n');             % 바이패스 전류(주 스위치 + 소프트 저항) 양의 방향: 경로(SER) → 버스
sl_pc(mdl, 'I_byp', 'n', 'S_BYP_1', 'D');
sl_pc(mdl, 'S_BYP_1', 'S', 'S_BYP_2', 'S');
sl_pc(mdl, 'S_BYP_2', 'D', 'C_bus', 'p');
sl_pc(mdl, 'R_soft', 'p', 'I_byp', 'n');
sl_pc(mdl, 'R_soft', 'n', 'C_bus', 'p');
sl_pc(mdl, 'Rsoft_PS', 'output', 'R_soft', 'R');
sl_pc(mdl, 'StageB_Regulator', 'BUS', 'C_bus', 'p');
sl_pc(mdl, 'StageB_Regulator', 'GND', 'GND', 'V');
sl_pc(mdl, 'C_bus', 'n', 'GND', 'V');
sl_pc(mdl, 'R_dmp', 'p', 'C_bus', 'p');              % RC 감쇠기: 버스 → R_dmp → C_dmp → GND
sl_pc(mdl, 'R_dmp', 'n', 'C_dmp', 'p');
sl_pc(mdl, 'C_dmp', 'n', 'GND', 'V');
sl_pc(mdl, 'V_bus', 'p', 'C_bus', 'p');
sl_pc(mdl, 'V_bus', 'n', 'GND', 'V');
sl_pc(mdl, 'I_load', 'tail', 'C_bus', 'p');
sl_pc(mdl, 'I_load', 'head', 'GND', 'V');
sl_pc(mdl, 'I_dabloss', 'tail', 'C_bus', 'p');
sl_pc(mdl, 'I_dabloss', 'head', 'GND', 'V');
sl_pc(mdl, 'iload_PS', 'output', 'I_load', 'iT');
sl_pc(mdl, 'iloss_PS', 'output', 'I_dabloss', 'iT');
sl_meas(mdl, 'I_path', 'I', 'ip',   [310 440]);
sl_meas(mdl, 'V_bus',  'V', 'vbus', [840 440]);
sl_meas(mdl, 'I_byp',  'I', 'ibyp', [180 70]);
sl_note(mdl, sprintf('Stage A 등가\n(이상 V_bat/2 + 13.2 mΩ + 1.5 µH)'), [40 300 260 330]);
sl_note(mdl, sprintf(['바이패스: 150 V GaN 2병렬 × 역직렬(합계 3.3 mΩ, 역방향 도통 1.4 V), 게이트 gByp\n' ...
    '∥ 소프트 투입 가변 저항 R_soft(상태기계 지령: 열림 1 MΩ, 10 Ω에서 로그 램프, 경로전류 > 시작값 + 25 A면 되올림)']), [800 50 1240 90]);
sl_note(mdl, sprintf('버스 RC 감쇠기(R2 기본형): 1.6 mF·48.6 mΩ'), [600 495 810 512]);
sl_note(mdl, sprintf('보조버스(창 기준 460 V, 상한 B_470)\nC_b 400 µF, 정전력 부하(분리 신호 → 5 kW), DAB 손실 등가'), [760 520 1100 550]);

% ---- 부하·손실 계산, 제어부 ------------------------------------------------------------------
build_bus_loads(mdl, [880 140 990 190], [1000 140 1110 190], 'TB', struct('ShedTag', 'r2_sup', 'ShedIndex', 10, 'ShedWidth', 12));
sl_line(mdl, 'Load_CPL/1', 'iload_PS/1');
sl_line(mdl, 'DAB_Loss_Model/1', 'iloss_PS/1');
build_stageB_control(mdl, [150 580 330 660], [420 580 600 660], 'TB', struct('r2d', true));   % 게이트 생성기 prism_gate_stageB_f.m
sl_note(mdl, sprintf(['제어부: Controller_StageB(보호 상태기계 R2_Supervisor + 채택 제어기, 5 µs 표본·계산·5 µs 지연)\n' ...
    '→ Gate_StageB(게이트 생성기 + DAB 고장 모드 변조(EPS) → 보호 게이트 재정의: 비교기·고장 주입, 태그 gB_*, gD_*, gByp, gBrk)']), [150 685 900 715]);

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [1180 140 1300 380], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_Bus', {'vbus', 'p_load'}; ...
     'Scope_Currents', {'ip', 'ih', 'ibyp'}; ...
     'Scope_Link', {'vlink', 'ilink', 'ibrk', 'iL'}; ...
     'Scope_State', {'r2_sup', 'vs'}; ...
     'Scope_Controller', {'ctrl_dg', 'uc'}}, ...
    {'t', 't', ''; 'vbus', 'vbus', ''; 'ip', 'ip', ''; 'ih', 'ih', ''; 'vs', 'vs', ''; 'vlink', 'vlink', ''; ...
     'ilink', 'ilink', ''; 'ibyp', 'ibyp', ''; 'ibrk', 'ibrk', ''; 'iL', 'iL', ''; 'ctrl_dg', 'dg', 'TB.Np'; 'uc', 'uc', 'TB.Np'; ...
     'r2_sup', 'sup', 'TB.Np'; 'r2_flags', 'flags', 'TB.Np'});
sl_note(mdl, sprintf('계측: Scope 5개(버스, 전류, 링크·제동, 상태기계·직렬전압, 제어기 내부)\n+ To Workspace(판정용, 상태기계·제어 신호는 5 µs마다)'), [1160 415 1460 445]);

sl_note(mdl, sprintf(['파라미터(TB13_init.m, 기준 ref/TB13_<사례>_init.json = 검증 코드 E17·E20). TB09와 같은 회로. 다른 것: 상태기계 파라미터 60개(정합 유지·감발·시간 상한),\n' ...
    'EPS 지령표 TB.eps_d·eps_phi(TB10과 같음), 첨두 표 TB.eps_pk = 스위칭 정상상태(데드타임·C_oss·V_f, 검증 코드 E21), 설계 상한 1.387 × 정격점 63.6 A(스위칭 표 오차 3 %·지령 전이 5 %),\n' ...
    '400 V 부하 분리·감발 3 ms(분리 뒤 5 kW), 보호(TB.prot_prm)\n' ...
    '해석기: Simulink 고정 간격 이산 TB.dt(2.5 ns), Simscape 지역 해석기 후진 오일러 TB.dt(고정 비용, 모드 반복 3회), 제어주기 5 µs, 전달지연 5 µs']), ...
    [30 740 1150 800], 'box');
sl_note(mdl, sprintf(['검증 목적: TB12(EPS 전이 변화율 상한)는 TB11의 전이 첨두 88.5 A를 70.0 A로 줄였지만, 전이가 끝나는 주기에 정상 상한(66.7 A) 위로\n' ...
    '약 5 %가 남아 1.5배(68.7 A)를 넘었다. 설계 상한에 지령 전이 여유 5 %를 넣어(1.387 × 정격점) 1.5배 안에 묶이는가, 그 대가(링크 붕괴·소프트 투입)는 얼마인가.\n' ...
    'A: 1008 V·25 kW H-브리지 개방, B: 930 V 같은 고장(일시 감발). 회로·지령 블록·표·게이트 생성기는 TB12와 같고 첨두 상한만 다르다']), [30 820 1150 880], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
if ~exist(fullfile(here, 'results'), 'dir'), mkdir(fullfile(here, 'results')); end
sl_export_png({mdl, [mdl '/StageB_Regulator'], [mdl '/Controller_StageB'], [mdl '/Gate_StageB']}, fullfile(here, 'results'));
end
