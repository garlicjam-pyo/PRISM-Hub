%TB03_INIT  TB03(Stage B DAB, 개루프) 초기화: 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   시험 회로: 버스 전압원 400 V → 1차 풀브리지 → L_dab 11.1 µH(R_dab 0.02 Ω) → 이상 변압기 4:1
%             → 2차 풀브리지 → 링크 전압원 100 V(두 브리지 전압 정합: V_bus = n·V_link).
%   게이트: Stage B 게이트 생성기(ctrl/prism_gate_stageB.m)의 DAB 부분. 유효 위상을 100 µs마다 계단으로 바꾼다.
%     0.4 rad(δ = 318 ns) → 0.8 rad → −0.5 rad(역방향) → 0.15 rad(δ = 119 ns, t_d < δ < 2t_d) → 0.08 rad(δ = 64 ns < t_d)
%   마지막 두 단계는 E12에서 찾은 DAB 데드타임 영역(증분 이득 2배, 불감대)을 회로에서 확인하기 위한 것이다.

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));

P = prism_hub_params();

TB = struct();
TB.name  = 'TB03_StageB_DAB';
TB.dt    = P.sim.dt;                 % 5 ns (DAB 데드타임 100 ns = 20 간격)
TB.B     = P.B;                      % L_dab 11.1 µH, R_dab 0.02 Ω, n = 4, f_s 200 kHz, t_d 100 ns
TB.B.Goff   = 1e-8;
TB.B.Rd     = P.B.Ron;
TB.B.Goffd  = 1e-8;
TB.B.Coss_d = 100e-12;               % DAB 소자 출력용량(수치 안정용 소값; 검증 모델에는 없음)
TB.Vbus  = 400;
TB.Vlink = 100;
TB.t_steps  = (0:4)*100e-6;          % 위상 계단 시각 [s]
TB.ph_steps = [0.4 0.8 -0.5 0.15 0.08];   % 유효 위상 [rad]
TB.t_end  = 500e-6;
TB.neval  = 10;                      % 단계마다 마지막 10주기로 정상상태 평가
TB.gate_prm = P.gateB_prm;           % [dt Np 데드타임(H) 데드타임(DAB) T] (간격 수)

if evalin('base', 'exist(''TB_override'', ''var'')')
    ov = evalin('base', 'TB_override');
    fn = fieldnames(ov);
    for k = 1:numel(fn), TB.(fn{k}) = ov.(fn{k}); end
end
TB.gate_init = [0 TB.ph_steps(1) 0];   % [PWM 비교값, 초기 위상, 링크전류 평균 초기값]

assignin('base', 'P', P);
assignin('base', 'TB', TB);
