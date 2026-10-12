%TB02_INIT  TB02(Stage B H-브리지 + L_h, 개루프) 초기화: 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   시험 회로: 이상 링크 전압원 100 V → H-브리지(셀마다 C_oss 1 nF, 데드타임 50 ns, 유니폴라 PWM 200 kHz)
%             → L_h 5 µH(R_h 2 mΩ) → 부하 저항 0.5 Ω + 설정 전압원 V_set.
%   V_set = m·V_link − i_target·R_load 로 두어 원하는 평균 필터전류(양·음, 경부하·중부하)를 만든다.
%   기본 사례는 m = 0.5, 20 A. run_TB02가 TB_override(기본 작업공간)로 사례를 바꿔 가며 반복 실행한다.

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));

P = prism_hub_params();

TB = struct();
TB.name  = 'TB02_StageB_HBridge';
TB.dt    = P.sim.dt;                 % 5 ns (데드타임 50 ns = 10 간격)
TB.B     = P.B;                      % L_h 5 µH, R_h 2 mΩ, f_s 200 kHz, t_d 50 ns, C_oss 1 nF, R_on 0.1 mΩ, Vf 1 mV
TB.B.Goff  = 1e-8;
TB.B.Rd    = P.B.Ron;                % 바디 다이오드 도통 저항(검증 모델의 이상 클램프에 가깝게)
TB.B.Goffd = 1e-8;
TB.Vlink = 100;                      % 링크 전압(교정표 기준 전압과 같음)
TB.Rload = 0.5;                      % 부하 저항(설정 전압원과 함께 평균 전류를 정한다)
TB.m     = 0.5;                      % PWM 비교값(변조율)
TB.i0    = 20;                       % 목표 평균 필터전류 [A]
TB.nper  = 30;                       % 계산 주기 수(시정수 L/R = 10 µs의 15배)
TB.neval = 10;                       % 평가 구간(마지막 주기 수)

% 게이트 생성기(prism_gate_stageB) 상수: [dt Np 데드타임(H) 데드타임(DAB) T] (간격 수는 dt 기준)
TB.gate_prm = P.gateB_prm;

% 사례 바꾸기(run_TB02의 반복 실행용): 기본 작업공간의 TB_override 필드를 덮어쓴다
if evalin('base', 'exist(''TB_override'', ''var'')')
    ov = evalin('base', 'TB_override');
    fn = fieldnames(ov);
    for k = 1:numel(fn), TB.(fn{k}) = ov.(fn{k}); end
end

TB.Vset  = TB.m*TB.Vlink - TB.i0*TB.Rload;       % 설정 전압(데드타임 오차는 무시한 근삿값; 실제 전류는 측정값을 쓴다)
TB.t_end = TB.nper/TB.B.fs;
% 게이트 생성기 초기값 [m ph il]
TB.gate_init = [TB.m 0 0];
% 데드타임 교정표(제어기 보상에 쓰는 것과 같은 표, prism_hub_params)
TB.tab  = P.ctrl_tab;
TB.Vtab = P.comp.Vtab;
% 시험 사례 [m, 목표 전류 A]: 영전류 부근(부분 영전압 스위칭)과 대전류(하드 스위칭), 양·음 방향, 변조율 3종
TB.cases = [0.5 -60; 0.5 -20; 0.5 -8; 0.5 -4; 0.5 -2; 0.5 0; 0.5 2; 0.5 4; 0.5 8; 0.5 20; 0.5 60; ...
            0.2 -20; 0.2 20; -0.5 -20; -0.5 20];

assignin('base', 'P', P);
assignin('base', 'TB', TB);
