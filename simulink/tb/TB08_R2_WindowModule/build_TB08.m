function build_TB08()
%BUILD_TB08  TB08 테스트벤치 모델(TB08_R2_WindowModule.slx)을 처음부터 만든다.
%
%   R2 창 조정 Stage B 모듈(R2-W460: 1000 V급 240s 팩, B_470 부품)의 회로 확인.
%   구성
%     V_A(이상 전압원 V_bat/2) ── R_path ── L_path ── 경로전류 센서 ──┬── StageB_Regulator(SER → BUS) ──┬── 버스
%                                                                     └── 바이패스(150 V GaN 역직렬 2개) ─┘
%     버스: C_b ∥ 정전력 부하(Load_CPL) ∥ DAB 손실 등가(DAB_Loss_Model) ∥ 버스전압 센서
%     Controller_StageB(채택 제어기 + 모드 시퀀서 R2_Sequence) → 5 µs 전달지연
%     → Gate_StageB(H-브리지 PWM, DAB 위상) → R2 게이트 재정의(DAB 정지·영벡터·바이패스) → 스위치 셀
%     Measurements: Scope 5개 + To Workspace(판정용)
%   TB04B와 다른 것: DAB 권선비 4.6:1·누설 14.68 µH, 제어기 기준전압 460 V·DAB 정격 4 kW, 바이패스 스위치,
%   모드 시퀀서와 게이트 재정의(공용 빌더 lib/build_stageB_control.m의 r2 선택)
%   실행: prism_run('build_TB08')  →  prism_run('run_TB08')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB08_R2_WindowModule';
evalin('base', 'clear TB08_opts TB08_case');
run(fullfile(here, 'TB08_init.m'));
sl_model_new(mdl, 'TB08_init.m');

sl_note(mdl, 'TB08 — R2 창 조정 Stage B 모듈(R2-W460): 1000 V급 팩의 창 조정, 모드 전환, DAB 고장 강등', [30 10 1100 40], 'title');

% ---- 전력 회로 ----------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_A', [70 230 110 290], 'Orientation', 'down', 'v0', 'TB.VA');
sl_add(mdl, [fl 'Electrical Elements/Electrical Reference'], 'GND', [70 440 110 470]);
sl_solver(mdl, 'Solver', [10 360 50 390], 'GND', 'V', 3);   % 고정 비용(모드 반복 3회)
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_path', [150 160 200 180], 'R', 'TB.Rpath');
sl_add(mdl, [fl 'Electrical Elements/Inductor'], 'L_path', [230 160 280 180], 'l', 'TB.Lpath', 'r', '0', ...
    'i_L_specify', 'on', 'i_L', 'TB.ip0', 'i_L_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_path', [310 150 360 190]);
build_stageB(mdl, 'StageB_Regulator', [420 140 660 380], 'TB', ...
    struct('CossP', 'TB.B.Coss_dp', 'CossS', 'TB.B.Coss_ds', ...
           'CossNote', 'DAB C_oss 1차 335 pF·2차 1371 pF(후보 소자 C_o(tr))', ...
           'Xfmr', 'Xfmr_4p6to1', 'DabNote', '창 조정 R2-W460: 권선비 4.6:1, 누설 14.68 µH, 정격 4 kW'));
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_bus', [760 240 800 300], 'Orientation', 'down', ...
    'c', 'TB.Cb', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vb0', 'vc_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_bus', [840 240 880 300], 'Orientation', 'down');
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load', [930 240 970 300], 'Orientation', 'down');
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_dabloss', [1020 240 1060 300], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iload_PS', [940 200 970 220]);
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iloss_PS', [1030 200 1060 220]);

% ---- 바이패스 스위치: 직렬 포트(SER–BUS)를 단락. 역직렬 2개로 두 방향 전압을 모두 막는다 ----------------------
cb = struct('tag', 'gByp', 'Ron', 'TB.Rbyp_cell', 'Goff', 'TB.B.Goff', 'Vf', 'TB.B.Vf', 'Rd', 'TB.B.Rd', ...
    'Goffd', 'TB.B.Goffd', 'Coss', '');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_byp', [430 60 480 100]);
sl_switch_cell(mdl, 'S_BYP_1', [520 55 600 105], setfield(setfield(cb, 'label', 'BYP1'), 'orient', 'right')); %#ok<SFLD>
sl_switch_cell(mdl, 'S_BYP_2', [640 55 720 105], setfield(setfield(cb, 'label', 'BYP2'), 'orient', 'left'));  %#ok<SFLD>

sl_pc(mdl, 'V_A', 'p', 'R_path', 'p');
sl_pc(mdl, 'V_A', 'n', 'GND', 'V');
sl_pc(mdl, 'R_path', 'n', 'L_path', 'p');
sl_pc(mdl, 'L_path', 'n', 'I_path', 'p');            % i_p 양의 방향: V_A → 직렬 포트 → 버스
sl_pc(mdl, 'I_path', 'n', 'StageB_Regulator', 'SER');
sl_pc(mdl, 'I_byp', 'p', 'I_path', 'n');             % 바이패스 전류 양의 방향: 경로(SER) → 버스
sl_pc(mdl, 'I_byp', 'n', 'S_BYP_1', 'D');
sl_pc(mdl, 'S_BYP_1', 'S', 'S_BYP_2', 'S');          % 공통 소스(역직렬): 꺼지면 두 바디 다이오드가 서로 막는다
sl_pc(mdl, 'S_BYP_2', 'D', 'C_bus', 'p');
sl_pc(mdl, 'StageB_Regulator', 'BUS', 'C_bus', 'p');
sl_pc(mdl, 'StageB_Regulator', 'GND', 'GND', 'V');
sl_pc(mdl, 'C_bus', 'n', 'GND', 'V');
sl_pc(mdl, 'V_bus', 'p', 'C_bus', 'p');
sl_pc(mdl, 'V_bus', 'n', 'GND', 'V');
sl_pc(mdl, 'I_load', 'tail', 'C_bus', 'p');            % 부하 전류: 버스 → 전류원 → GND
sl_pc(mdl, 'I_load', 'head', 'GND', 'V');
sl_pc(mdl, 'I_dabloss', 'tail', 'C_bus', 'p');
sl_pc(mdl, 'I_dabloss', 'head', 'GND', 'V');
sl_pc(mdl, 'iload_PS', 'output', 'I_load', 'iT');
sl_pc(mdl, 'iloss_PS', 'output', 'I_dabloss', 'iT');
sl_meas(mdl, 'I_path', 'I', 'ip',   [310 440]);
sl_meas(mdl, 'V_bus',  'V', 'vbus', [840 440]);
sl_meas(mdl, 'I_byp',  'I', 'ibyp', [440 112]);
sl_note(mdl, sprintf('Stage A 등가\n(이상 V_bat/2 + 13.2 mΩ + 1.5 µH)'), [40 300 260 330]);
sl_note(mdl, sprintf('바이패스: 150 V GaN 역직렬 2개(합계 3.3 mΩ), 게이트 태그 gByp.\n모드 3·4에서 켜져 직렬 포트를 단락한다'), [740 60 1100 100]);
sl_note(mdl, sprintf('보조버스(창 기준 460 V, 상한 B_470)\nC_b 400 µF, 정전력 부하, DAB 손실 등가'), [760 500 1100 530]);

% ---- 부하·손실 계산, 제어부 ------------------------------------------------------------------
build_bus_loads(mdl, [880 140 990 190], [1000 140 1110 190], 'TB');
sl_line(mdl, 'Load_CPL/1', 'iload_PS/1');
sl_line(mdl, 'DAB_Loss_Model/1', 'iloss_PS/1');
build_stageB_control(mdl, [150 560 330 640], [420 560 600 640], 'TB', struct('r2', true));
sl_note(mdl, sprintf(['제어부: Controller_StageB(모드 시퀀서 R2_Sequence + 채택 제어기, 5 µs 표본·계산·5 µs 지연)\n' ...
    '→ Gate_StageB(게이트 생성기 → R2 게이트 재정의, 태그 gB_*, gD_*, gByp)']), [150 665 900 695]);

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [1180 140 1300 380], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_Bus', {'vbus', 'p_load'}; ...
     'Scope_Currents', {'ip', 'ih', 'ibyp'}; ...
     'Scope_Link', {'vlink', 'ilink'}; ...
     'Scope_Mode', {'r2_seq', 'vs'}; ...
     'Scope_Controller', {'ctrl_dg', 'uc'}}, ...
    {'t', 't', ''; 'vbus', 'vbus', ''; 'ip', 'ip', ''; 'ih', 'ih', ''; 'vs', 'vs', ''; 'vlink', 'vlink', ''; ...
     'ilink', 'ilink', ''; 'iL', 'iL', ''; 'ibyp', 'ibyp', ''; 'ctrl_dg', 'dg', 'TB.Np'; 'uc', 'uc', 'TB.Np'; ...
     'r2_seq', 'seq', 'TB.Np'});
sl_note(mdl, sprintf('계측: Scope 5개(버스, 전류, 링크, 모드·직렬전압, 제어기 내부)\n+ To Workspace(판정용, 제어 신호는 5 µs마다)'), [1160 415 1460 445]);

sl_note(mdl, sprintf(['파라미터(TB08_init.m → prism_hub_params.m). TB04B와 다른 것: DAB 4.6:1·누설 14.68 µH, 제어기 V_ref 460 V·DAB 정격 4 kW,\n' ...
    '바이패스 3.3 mΩ, 모드 시퀀서(TB.seq_prm). 같은 것: C_s 100 µF, L_h 5 µH·2 mΩ, C_link 2 mF, C_b 400 µF, 200 kHz, 데드타임 50/100 ns, C_oss H 1 nF·DAB 335/1371 pF\n' ...
    '해석기: Simulink 고정 간격 이산 TB.dt(2.5 ns), Simscape 지역 해석기 후진 오일러 TB.dt(고정 비용, 모드 반복 3회), 제어주기 5 µs, 전달지연 5 µs\n' ...
    '시작 표본 보호: Simscape 첫 출력 표본(t = 0)은 초기화 중의 값이므로 제어기·게이트·부하·손실 모델은 t < 1.5 dt 동안 초기값을 쓴다']), [30 720 1150 800], 'box');
sl_note(mdl, sprintf(['검증 목적: 개선 구조 R2에서 Stage B는 V_A가 부품 상한을 넘는 팩에만 붙이는 창 조정 모듈이다(docs/23). 1000 V급 팩(V_A ≤ 504 V)·B_470 부품의\n' ...
    'R2-W460을 회로에서 확인한다. 사례 A·B: 창 조정 Tier-2(1008 V 1→25 kW)·Tier-1(930 V 15→25 kW), 기준 E12 스위칭 ODE.\n' ...
    '사례 C: 끔(기준 램프 → 영벡터 → 바이패스), D: DAB 고장 강등(1 ms 램프 → 바이패스), E: 켬(바이패스 + 영벡터 → 영벡터 → 제어), 기준 E19 모드 평균모델']), ...
    [30 820 1150 890], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
sl_export_png({mdl, [mdl '/StageB_Regulator'], [mdl '/Controller_StageB'], [mdl '/Gate_StageB']}, fullfile(here, 'results'));
end
