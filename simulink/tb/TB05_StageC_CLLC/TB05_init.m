%TB05_INIT  TB05(Stage C 대칭 CLLC, 개루프) 초기화: 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   부하는 기본 작업공간 변수 TB05_Po [W]로 고른다(없으면 3000 W = 정격).
%     3000 W : 정격(400 주기 = 1.6 ms)   1500 W, 300 W : 부분부하·경부하(300 주기 = 1.2 ms)
%   시험 회로: 입력 400 V 이상 전압원 → Stage C 전력단(build_stageC) → 저항부하 R_L = 48²/P_o
%   게이트: 공진점 250 kHz 고정, 50 % 상보 + 데드타임 50 ns(ctrl/prism_gate_stageC.m)
%   기준: 검증 모델 E10(Stage C 스위칭 ODE)과 같은 계산(ref/make_ref_TB05.py). 초기조건도 같게 둔다
%         (공진망 전류·전압 0, 출력 48 V).
%   정류기: 검증 모델의 이상 동기정류에 맞춰 다이오드를 Vf 1 mV, R_on 0.1 mΩ으로 둔다(동기정류 MOSFET의 근사).

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));

if evalin('base', 'exist(''TB05_Po'', ''var'')')
    Po = evalin('base', 'TB05_Po');
else
    Po = 3000;
end
P = prism_hub_params();

TB = struct();
TB.name = 'TB05_StageC_CLLC';
TB.dt   = P.sim.dt;                  % 5 ns (데드타임 50 ns = 10 간격, 주기 4 µs = 800 간격)
TB.C    = P.C;                       % n Lr1 Cr1 Lm Lr2 Cr2 fs td Coss Co Ron Vf
TB.C.Goff     = 1e-8;                % 스위치 개방 컨덕턴스
TB.C.Rd       = P.C.Ron;             % 바디 다이오드 도통 저항
TB.C.Goffd    = 1e-8;
TB.C.Vf_rect  = 1e-3;                % 2차 정류(동기정류 근사)
TB.C.Ron_rect = 1e-4;
TB.Vin  = 400;                       % 400 V 보조버스(이상 전압원)
TB.Po   = Po;
TB.vo0  = 48;                        % 출력 커패시터 초기전압(검증 모델과 같음)
TB.neval = 10;                       % 마지막 10주기로 정상상태 평가

% 민감도 확인용 덮어쓰기(run_TB05가 TB_override 구조체로 dt, C 등을 바꾼다)
if evalin('base', 'exist(''TB_override'', ''var'')')
    ov = evalin('base', 'TB_override');
    fn = fieldnames(ov);
    for k = 1:numel(fn), TB.(fn{k}) = ov.(fn{k}); end
end

% 파생 값
TB.RL   = 48^2/TB.Po;                % 정격 출력전압 48 V에서 P_o가 되는 저항
TB.ncyc = 300 + 100*(TB.Po >= 3000); % 검증 모델과 같은 실행 주기 수
TB.T    = 1/TB.C.fs;
TB.t_end = TB.ncyc*TB.T;
TB.gate_prm = [TB.dt TB.T TB.C.td 1];   % [간격, 주기, 데드타임, 켬]

assignin('base', 'P', P);
assignin('base', 'TB', TB);
