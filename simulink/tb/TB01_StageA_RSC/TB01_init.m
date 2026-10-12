%TB01_INIT  TB01(Stage A 1위상 RSC) 초기화: 패키지 경로, 설계 파라미터 P, 시험 조건 TB.
%
%   모델 InitFcn이 이 스크립트를 실행한다(빌드·실행 스크립트도 같은 것을 쓴다).
%   시험 조건은 검증 코드 E1 공차 표본 시험의 공칭 사례와 같다:
%     단상, 배터리 788 V(이상 전압원), 출력 부하 46.875 A(= 375 A / 8위상, 이상 전류 부하),
%     출력 커패시터 400 µF, 고정 타이밍 f_s = 0.98·f_r0, 데드타임 100 ns, 50주기 계산 후 마지막 10주기 평가.

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));

P = prism_hub_params();

TB = struct();
TB.name  = 'TB01_StageA_RSC';
TB.dt    = P.sim.dt;                 % 적분 간격 = 게이트 격자 = Simscape 지역 해석기 간격 (5 ns)
TB.vbat  = P.sim.vbat;               % 배터리 전압 (788 V)
TB.Iload = 375/8;                    % 위상당 출력전류 (46.875 A)
TB.Cout  = 400e-6;                   % V_A 노드 출력 커패시터 (검증 모델의 버스 커패시터와 같은 값)
TB.vout0 = TB.vbat/2;                % 출력 커패시터 초기전압 (정상상태 근처에서 시작)

% Stage A 소자값(설계값, prism_hub_params와 같음). 스위치 R_ds 6 mΩ × 2 + ESR + R_L + R_misc = 16 mΩ
TB.A       = P.A;
TB.A.T     = 1/P.A.fs;               % 스위칭 주기 (f_s = 0.98·f_r0 ≈ 147 kHz → 6.80 µs)
TB.A.Goff  = 1e-8;                   % 스위치 차단 컨덕턴스
TB.A.Rd    = P.A.Rds;                % 바디 다이오드 도통 저항(검증 모델과 같게 R_ds로 둔다)
TB.A.Goffd = 1e-8;                   % 다이오드 차단 컨덕턴스
TB.A.vC0   = TB.vbat/2;              % 플라잉 커패시터 초기전압

TB.ncyc  = 50;                       % 계산 주기 수
TB.neval = 10;                       % 평가 구간(마지막 주기 수)
TB.t_end = TB.ncyc*TB.A.T;

% 게이트 생성기 상수(prism_gate_stageA): [dt T t_d Nph], 동작 위상, 위상별 시작 지연
TB.gate_prm = [TB.dt TB.A.T TB.A.td 8];
TB.gate_en  = [1 0 0 0 0 0 0 0];     % 위상 1만 동작
TB.gate_off = zeros(1, 8);

assignin('base', 'P', P);
assignin('base', 'TB', TB);
