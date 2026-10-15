function build_TB04B()
%BUILD_TB04B  TB04B 테스트벤치 모델(TB04B_StageB_DAB_Coss.slx)을 처음부터 만든다.
%
%   TB04와 같은 회로·제어기에서 DAB 1차·2차 소자 출력용량을 따로 준다(TB.B.Coss_dp, TB.B.Coss_ds).
%   구성
%     V_A(이상 전압원 V_bat/2) ── R_path ── L_path ── 경로전류 센서 ── StageB_Regulator(SER → BUS)
%     400 V 버스: C_b ∥ 정전력 부하(Load_CPL) ∥ DAB 손실 등가(DAB_Loss_Model) ∥ 버스전압 센서
%     Controller_StageB(채택 제어기) → 5 µs 전달지연 → Gate_StageB(H-브리지 PWM, DAB 위상) → 스위치 셀
%     Measurements: Scope 4개 + To Workspace(판정용)
%   실행: prism_run('build_TB04B')  →  prism_run('run_TB04B')

here = fileparts(mfilename('fullpath'));
mdl  = 'TB04B_StageB_DAB_Coss';
evalin('base', 'clear TB04B_opts');
run(fullfile(here, 'TB04B_init.m'));
sl_model_new(mdl, 'TB04B_init.m');

sl_note(mdl, 'TB04B — Stage B 폐루프: DAB 소자 출력용량(후보 소자)과 25 kW 정상상태 리플', [30 10 1100 40], 'title');
sl_note(mdl, sprintf(['검증 목적: TB04에서 25 kW 정상상태 버스 리플(기준 0.1 V)이 DAB 소자 출력용량(수치 안정용 100 pF)에 따라 0.07–0.14 V로 달라졌다.\n' ...
    'DAB 1차(400 V)·2차(100 V) 소자 출력용량을 대표 후보 소자의 시간 등가 값 C_o(tr)로 따로 넣고, 같은 사례·같은 기준으로 다시 판정한다.\n' ...
    '1차 650 V GaN GS66516T: C_o(tr) 335 pF(0–400 V)   2차 150 V GaN EPC2305: C_oss(tr) 1371 pF(0–75 V)   (제조사 데이터시트)\n' ...
    '사례·기준: TB04와 같음(640 V 15 → 25 kW, 788 V 0 → 10 kW, 검증 모델 E12). 적분 간격 2.5 ns(TB04에서 정한 게이트 시간 분해능 요구).']), ...
    [30 50 1150 130], 'box');

% ---- 전력 회로 ----------------------------------------------------------------------------
fl = 'fl_lib/Electrical/';
sl_add(mdl, [fl 'Electrical Sources/DC Voltage Source'], 'V_A', [70 230 110 290], 'Orientation', 'down', 'v0', 'TB.VA');
sl_add(mdl, [fl 'Electrical Elements/Electrical Reference'], 'GND', [70 440 110 470]);
sl_solver(mdl, 'Solver', [10 360 50 390], 'GND', 'V', 3);   % 고정 비용(모드 반복 3회): 스위치 셀 12개에서 약 10배 빠름
sl_add(mdl, [fl 'Electrical Elements/Resistor'], 'R_path', [150 160 200 180], 'R', 'TB.Rpath');
sl_add(mdl, [fl 'Electrical Elements/Inductor'], 'L_path', [230 160 280 180], 'l', 'TB.Lpath', 'r', '0', ...
    'i_L_specify', 'on', 'i_L', 'TB.ip0', 'i_L_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Current Sensor'], 'I_path', [310 150 360 190]);
build_stageB(mdl, 'StageB_Regulator', [420 140 660 380], 'TB', ...
    struct('CossP', 'TB.B.Coss_dp', 'CossS', 'TB.B.Coss_ds', 'CossNote', 'DAB C_oss 1차 335 pF·2차 1371 pF(후보 소자 C_o(tr), TB.B.Coss_dp·Coss_ds)'));
sl_add(mdl, [fl 'Electrical Elements/Capacitor'], 'C_bus', [760 240 800 300], 'Orientation', 'down', ...
    'c', 'TB.Cb', 'r', '1e-6', 'vc_specify', 'on', 'vc', 'TB.vb0', 'vc_priority', 'High');
sl_add(mdl, [fl 'Electrical Sensors/Voltage Sensor'], 'V_bus', [840 240 880 300], 'Orientation', 'down');
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_load', [930 240 970 300], 'Orientation', 'down');
sl_add(mdl, [fl 'Electrical Sources/Controlled Current Source'], 'I_dabloss', [1020 240 1060 300], 'Orientation', 'down');
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iload_PS', [940 200 970 220]);
sl_add(mdl, 'nesl_utility/Simulink-PS Converter', 'iloss_PS', [1030 200 1060 220]);

sl_pc(mdl, 'V_A', 'p', 'R_path', 'p');
sl_pc(mdl, 'V_A', 'n', 'GND', 'V');
sl_pc(mdl, 'R_path', 'n', 'L_path', 'p');
sl_pc(mdl, 'L_path', 'n', 'I_path', 'p');            % i_p 양의 방향: V_A → 직렬 포트 → 버스
sl_pc(mdl, 'I_path', 'n', 'StageB_Regulator', 'SER');
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
sl_note(mdl, sprintf('Stage A 등가\n(이상 V_bat/2 + 13.2 mΩ + 1.5 µH)'), [40 300 260 330]);
sl_note(mdl, sprintf('400 V 보조버스\nC_b 400 µF, 정전력 부하, DAB 손실 등가'), [760 500 1100 530]);

% ---- 부하·손실 계산, 제어부 ------------------------------------------------------------------
build_bus_loads(mdl, [880 60 990 110], [1000 60 1110 110], 'TB');
sl_line(mdl, 'Load_CPL/1', 'iload_PS/1');
sl_line(mdl, 'DAB_Loss_Model/1', 'iloss_PS/1');
build_stageB_control(mdl, [150 560 330 640], [420 560 600 640], 'TB');
sl_note(mdl, sprintf('제어부: Controller_StageB(5 µs 표본·계산·5 µs 지연) → Gate_StageB(게이트 태그 gB_*, gD_*)'), [150 675 800 695]);

% ---- 계측부 ---------------------------------------------------------------------------------
ms = [mdl '/Measurements'];
add_block('built-in/Subsystem', ms, 'Position', [1180 140 1300 380], 'BackgroundColor', 'lightBlue');
sl_probe_panel(ms, 30, 30, ...
    {'Scope_Bus', {'vbus', 'p_load'}; ...
     'Scope_Currents', {'ip', 'ih'}; ...
     'Scope_Link', {'vlink', 'ilink'}; ...
     'Scope_Controller', {'ctrl_dg', 'uc'}}, ...
    {'t', 't', ''; 'vbus', 'vbus', ''; 'ip', 'ip', ''; 'ih', 'ih', ''; 'vs', 'vs', ''; 'vlink', 'vlink', ''; ...
     'ilink', 'ilink', ''; 'iL', 'iL', ''; 'ctrl_dg', 'dg', 'TB.Np'; 'uc', 'uc', 'TB.Np'; 'gate_aux', 'aux', 'TB.Np'});
sl_note(mdl, sprintf('계측: Scope 4개(버스, 전류, 링크, 제어기 내부)\n+ To Workspace(판정용, 제어 신호는 5 µs마다)'), [1160 415 1460 445]);

sl_note(mdl, sprintf(['파라미터(TB04B_init.m → prism_hub_params.m, 검증 모델과 같은 설계값. TB04와 다른 것은 DAB 소자 출력용량뿐)\n' ...
    'C_s 100 µF, L_h 5 µH·2 mΩ, C_link 2 mF, C_b 400 µF, DAB 4:1·200 kHz·11.1 µH·0.02 Ω, 데드타임 50/100 ns, C_oss H-브리지 1 nF·DAB 1차 335 pF·2차 1371 pF\n' ...
    '해석기: Simulink 고정 간격 이산 TB.dt(판정 2.5 ns), Simscape 지역 해석기 후진 오일러 TB.dt(고정 비용, 모드 반복 3회), 제어주기 5 µs, 전달지연 5 µs\n' ...
    '시작 표본 보호: Simscape 첫 출력 표본(t = 0)은 초기화 중의 값이므로 제어기·게이트·부하·손실 모델은 t < 1.5 dt 동안 평형점 값을 쓴다']), [30 720 1000 800], 'box');

save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('saved %s\n', fullfile(here, [mdl '.slx']));
set_param(mdl, 'SimulationCommand', 'update');
fprintf('update diagram OK\n');
end
