%TB25_INIT  TB25(Stage A 1위상 + 스위치 출력용량: 하드 스위칭 출력용량 손실 확인) 초기화.
%
%   사례: 기본 작업공간 변수 TB25_case(없으면 'O_nl_C'). 사례 값은 ref/TB25_cases.json(ref/make_ref_TB25.py, 검증 코드 E31).
%   사례 이름 = <설계>_<부하>_<용량>: 설계 O(원설계 150 kHz)·A(E31 선택 (가))·B(E31 선택 (나)),
%   부하 nl(무부하)·ld(46.875 A = 375 A/8위상), 용량 0(출력용량 없음, 1 fF)·C(스위치마다 등가 선형 C_oss).
%   등가 선형 C_oss = Q_oss,위치(V_bat/2)/(V_bat/2): 하드 스위칭 전이 손실이 전하 × 전압이므로 같은 손실을 낸다.
%   회로·게이트는 TB01과 같다(고정 타이밍 f_s = 0.98·f_r, 데드타임 100 ns). 배터리 800 V, C_out 400 µF.
%   해석기: Simscape 지역 해석기 후진 오일러 2.5 ns.

tbDir = fileparts(mfilename('fullpath'));
pkgRoot = fileparts(fileparts(tbDir));
addpath(pkgRoot, fullfile(pkgRoot, 'ctrl'), fullfile(pkgRoot, 'lib'), fullfile(pkgRoot, 'tools'));
caseName = 'O_nl_C';
if evalin('base', 'exist(''TB25_case'', ''var'')'), caseName = evalin('base', 'TB25_case'); end
CS = jsondecode(fileread(fullfile(tbDir, 'ref', 'TB25_cases.json')));
C0 = CS.cases.(caseName);

P = prism_hub_params(struct('dt', 2.5e-9));
TB = struct();
TB.name  = 'TB25_StageA_Coss';
TB.case  = caseName;
TB.dt    = 2.5e-9;
TB.vbat  = CS.vbat;
TB.Iload = C0.Iload;
TB.Cout  = 400e-6;
TB.vout0 = C0.vout0;

TB.A       = P.A;
TB.A.Lr    = C0.Lr;  TB.A.Cfly = C0.Cfly;  TB.A.Rds = C0.Rds;
TB.A.fr0   = 1/(2*pi*sqrt(TB.A.Lr*TB.A.Cfly));
TB.A.fs    = 0.98*TB.A.fr0;
TB.A.T     = round(1/TB.A.fs/TB.dt)*TB.dt;     % 게이트 격자에 맞춘 주기
TB.A.Goff  = 1e-8;  TB.A.Rd = C0.Rds;  TB.A.Goffd = 1e-8;
TB.A.vC0   = C0.vC0;
TB.A.Coss  = C0.Coss;                          % 스위치 셀마다(위치당 등가) [F]

TB.ncyc  = CS.ncyc;
TB.neval = CS.neval;
if evalin('base', 'exist(''TB25_ncyc'', ''var'')'), TB.ncyc = evalin('base', 'TB25_ncyc'); end   % (smoke)
TB.t_end = TB.ncyc*TB.A.T;
TB.gate_prm = [TB.dt TB.A.T TB.A.td 8];
TB.gate_en  = [1 0 0 0 0 0 0 0];
TB.gate_off = zeros(1, 8);

assignin('base', 'P', P);
assignin('base', 'TB', TB);
