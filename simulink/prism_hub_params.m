function P = prism_hub_params(cs)
%PRISM_HUB_PARAMS  PRISM-Hub 스위칭 Simulink 모델의 파라미터·초기조건.
%
%   P = prism_hub_params()            기본 사례(788 V, 5 → 25 kW)
%   P = prism_hub_params(cs)          사례 구조체 cs의 필드로 기본값을 바꾼다.
%       cs.vbat      배터리 전압 [V]
%       cs.P0, cs.P1 400 V 보조부하(정전력) 스텝 전·후 [W]
%       cs.t_step    스텝 시각 [s]   (DAB 전류비 추정이 학습되도록 2 ms 이상 권장)
%       cs.t_end     시뮬레이션 종료 시각 [s]
%       cs.delay_extra 모델 밖 추가 지연 [s] (Tier 시험 +3.0 µs)
%       cs.stageA_modules  동작하는 Stage A 모듈 [1×4 논리] (주행 모드는 모듈 1만)
%       cs.stageC_enable   Stage C(48 V) 동작 여부
%
%   모델(PRISM_Hub_switching.slx)의 InitFcn이 이 함수를 불러 기본 작업공간에 P를 만든다.
%   부품값은 검증 코드(E1·E5–E14)와 같은 설계값이다. 제어기는 공칭값만 알고, 회로는 이 값으로 동작한다.

if nargin < 1, cs = struct(); end

%% ---------------- 시뮬레이션 공통 ----------------------------------------------------
S.dt         = 5e-9;        % 기본 적분 간격 = 게이트 생성 간격 = Simscape 지역 해석기 간격 [s]
S.Ts         = 5e-6;        % Stage B 제어주기(200 kHz, 반송파 최댓값에서 표본) [s]
S.vbat       = 788;
S.P0         = 5000;
S.P1         = 25000;
S.t_step     = 2e-3;
S.t_end      = 6e-3;
S.delay_extra = 0;
S.stageA_modules = [1 0 0 0];
S.stageC_enable  = 1;
fn = fieldnames(cs);
for k = 1:numel(fn), S.(fn{k}) = cs.(fn{k}); end
S.Np = round(S.Ts/S.dt);                         % 제어주기당 적분 간격 수(1000)
P.sim = S;

%% ---------------- Stage A: 2:1 공진 스위치드 커패시터(RSC), 4모듈 × 2위상 ----------------
A.Nmod   = 4;  A.Nph = 2;                        % 모듈 수, 모듈당 위상 수
A.Cfly   = 7.8125e-6;                            % 플라잉 커패시터 [F]
A.Lr     = 1.441e-7;                             % 공진 인덕턴스 [H]  → f_r0 ≈ 150 kHz
A.Rds    = 6e-3;                                 % 스위치 도통저항(750 V SiC 2병렬) [Ω]
A.ESR    = 1.5e-3;  A.RL = 1e-3;  A.Rmisc = 1.5e-3;
A.Vf     = 0.9;                                  % 바디 다이오드 순방향 전압 [V]
A.td     = 100e-9;                               % 데드타임 [s]
A.fr0    = 1/(2*pi*sqrt(A.Lr*A.Cfly));
A.fs     = 0.98*A.fr0;                           % 고정 타이밍(설계값 f_s/f_r = 0.98)
A.Cin    = 100e-6;                               % 배터리 측 입력 커패시터 [F]
A.Cout   = 400e-6;                               % V_A 노드(충전 포트) 출력 커패시터 [F]
A.Rout_est = 10.2e-3;                            % 1모듈 등가 출력저항(설계 추정, 초기조건용) [Ω]
A.modules = logical(S.stageA_modules(:)');
P.A = A;

%% ---------------- Stage B: 직렬 부분전력 조정기 ------------------------------------------
B.Lpath  = 1.5e-6;     B.Rpath = 3e-3;           % V_A → 직렬 포트 배선(Stage A 출력저항은 회로에서 생김)
B.Cs     = 100e-6;                               % 직렬 포트 커패시터
B.Cb     = 400e-6;                               % 400 V 보조버스 커패시터
B.Lh     = 5e-6;       B.Rh   = 2e-3;            % H-브리지 LC 필터
B.Clink  = 2e-3;                                 % 부유 링크 커패시터(100 V)
B.Ldab   = 11.1e-6;    B.Rdab = 0.02;            % DAB 누설 인덕턴스·권선저항(1차 환산)
B.n      = 4;                                    % DAB 권선비 4:1
B.fs     = 200e3;
B.td_h   = 50e-9;      B.td_d = 100e-9;          % H-브리지·DAB 데드타임
B.Coss_h = 1e-9;                                 % H-브리지 스위치 출력용량(선형) [F]
B.Ron    = 1e-4;                                 % 스위치 도통저항(경로 저항은 R_h·R_dab에 포함)
B.Vf     = 1e-3;                                 % 다이오드 순방향 전압(검증 모델은 이상 클램프)
B.R_dab_link = 0;                                % (예비)
P.B = B;

%% ---------------- Stage C: 대칭 CLLC 400 → 48 V, 3 kW ------------------------------------
C.n    = 25/3;                                   % 권선비
C.Lr1  = 11.0e-6;  C.Cr1 = 36.8e-9;              % 1차 공진망
C.Lm   = 66e-6;                                  % 자화 인덕턴스
C.Lr2  = C.Lr1/C.n^2;  C.Cr2 = C.Cr1*C.n^2;      % 2차 공진망(대칭, 1차 환산이 1차와 같음)
C.fs   = 250e3;                                  % 공진점 고정 주파수
C.td   = 50e-9;
C.Coss = 100e-12;
C.Co   = 470e-6;
C.Po   = 3000;
C.enable = logical(S.stageC_enable);
C.Rload = 48^2/C.Po;
if ~C.enable, C.Rload = 1e6; end
C.Ron  = 5e-3;   C.Vf = 0.05;                    % 1차 스위치·2차 정류 다이오드(동기정류 근사)
P.C = C;

%% ---------------- 부하 -----------------------------------------------------------------
L.P0 = S.P0;  L.P1 = S.P1;  L.t_step = S.t_step;
L.vmin = 50;                                     % 정전력 부하 전류 계산의 하한 전압(기동 보호)
P.load = L;

%% ---------------- Stage B 제어기(채택 설계) -------------------------------------------
% 공칭 파라미터(제어기 내부 모델). 경로 저항 R = 13.2 mΩ은 Stage A 출력저항 포함값이다.
cp = struct('L',1.5e-6,'Cs',100e-6,'Cb',400e-6,'R',0.0132,'Lh',5e-6,'Rh',0.002,'Clink',0.002, ...
            'Ts',S.Ts,'vref',400,'vlink',100,'mmax',0.95,'refmax',84,'link_max',80,'power_max',8000, ...
            'link_bw',1000,'itau',10e-6,'Ldab',11.1e-6,'fs',200e3,'turns',4,'phmax',pi/3);
K = [-1.5813581402097892, 1.1112552918606937, 1.539757867322121, 0.6419266519985994, -12686.999839382896];
est = struct('lmin',0.9,'gain',0.05,'min_A',40,'eps_gain',0.2,'eps_max',10);
comp = struct('scale',0.6,'from_A',20,'full_A',80,'Vtab',100,'enable',1);
P.cp = cp;  P.K = K;  P.est = est;  P.comp = comp;
% 제어기 상수 벡터(MATLAB Function 블록 입력). 순서는 ctrl/prism_stageB_controller.m 머리말 참고.
P.ctrl_prm = [cp.L cp.Cs cp.Cb cp.R cp.Lh cp.Rh cp.Clink cp.Ts cp.vref cp.vlink cp.mmax cp.refmax ...
              cp.link_max cp.power_max cp.link_bw cp.itau cp.Ldab cp.fs cp.turns cp.phmax K ...
              est.lmin est.gain est.min_A est.eps_gain est.eps_max ...
              comp.scale comp.from_A comp.full_A comp.Vtab 5 1 comp.enable];
% H-브리지 데드타임 교정표(전류별 상승 전이 한 번의 전압·시간 손실, 선형 출력용량 1 nF, 링크 100 V)
[ig, eg] = deadtime_table_linear(B.td_h, B.Coss_h, comp.Vtab);
P.ctrl_tab = [ig; eg];

%% ---------------- 초기조건: 평균모델 평형점 --------------------------------------------
Pc = C.Po * C.enable;                            % Stage C가 버스에서 가져가는 전력(근사)
[x0, u0] = stageB_equilibrium(S.vbat, S.P0 + Pc, cp);
ip0 = x0(1);
I.ip   = ip0;
I.VA   = S.vbat/2 - A.Rout_est*ip0;              % V_A 노드(Stage A 출력)
I.vs   = cp.vref - I.VA + B.Rpath*ip0;           % 직렬 포트(경로 저항 강하 포함)
I.vbus = cp.vref;
I.ih   = ip0;
I.vlink = cp.vlink;
I.m    = (I.vs + cp.Rh*I.ih)/cp.vlink;
I.il   = I.m*I.ih;
I.vcfly = S.vbat/2;
I.v48  = 48*cp.vref/400;
I.q    = -(ip0 + K(1:4)*[ip0; I.vs; cp.vref; I.ih])/K(5);
I.ph   = phase_ff(I.il, cp.vref, cp, est.lmin);
I.u0   = u0;
P.init = I;
P.ctrl_init = [I.q 0 I.m I.il];

%% ---------------- 게이트 생성기 상수 ---------------------------------------------------
dly = round((S.Ts + S.delay_extra)/S.dt);        % 계산 후 적용까지 지연(기본 1 제어주기 = 5 µs)
P.gateB_prm = [S.dt S.Np round(B.td_h/S.dt) round(B.td_d/S.dt) 1/B.fs];
P.gateB_init = [I.m I.ph I.il];                  % 초기 PWM 비교값, 초기 위상, 초기 링크전류(주기 평균 기록 초기값)
P.delay_steps = dly;
act = find(kron(A.modules, ones(1, A.Nph)));     % 동작 위상 번호(1–8)
offs = zeros(1, A.Nmod*A.Nph);
offs(act) = (0:numel(act)-1) * (1/A.fs) / (2*numel(act));   % 인터리빙 오프셋 T/(2N)
P.gateA_prm = [S.dt 1/A.fs A.td A.Nmod*A.Nph];
P.gateA_en  = double(kron(A.modules, ones(1, A.Nph)));
P.gateA_off = offs;
P.gateC_prm = [S.dt 1/C.fs C.td double(C.enable)];
end

%% =======================================================================================
function [x, u] = stageB_equilibrium(vbat, power, cp)
% 평균모델 평형점(model_stage_b.equilibrium과 같은 식). DAB 효율 0.96.
eta = 0.96;
plink = @(ip) (cp.vref - vbat/2 + cp.R*ip + cp.Rh*ip).*ip;
pin = @(pl) pl/eta.*(pl >= 0) + pl*eta.*(pl < 0);
balance = @(ip) cp.vref*ip - power - pin(plink(ip));
ip = fzero(balance, [-500 500]);
vs = cp.vref - vbat/2 + cp.R*ip;
m = (vs + cp.Rh*ip)/cp.vlink;
x = [ip vs cp.vref ip cp.vlink m*ip];
u = [m m*ip];
end

function ph = phase_ff(il, vb, cp, lbasis)
% 링크전류 → SPS 위상(누설 인덕턴스를 공칭의 lbasis배로 가정)
k = cp.turns*max(vb, 1)/(2*pi*cp.fs*cp.Ldab*lbasis);
a = min(abs(il)/(pi*k/4), 1);
ph = min(pi/2*(1 - sqrt(1 - a)), cp.phmax);
if il < 0, ph = -ph; end
end

function [ig, eg] = deadtime_table_linear(td, C, V)
% 데드타임 교정표: 레그 노드를 0 V에서 시작해 dv/dt = −i/C_node(0–V 클램프)로 데드타임 동안 적분하고
% 잃는 전압·시간 ∫(V − v)dt를 구한다(C_node = 두 스위치 출력용량의 합 = 2C). 검증 코드와 같은 계산.
ig = [-logspace(2, -2, 81), 0, logspace(-2, 2, 81)];
n = 2000; h = td/n;
v = zeros(size(ig)); lost = zeros(size(ig));
cn = 2*C;
for s = 1:n                                      % 용량이 일정하므로 중점법 = 오일러
    vn = min(max(v + h*(-ig/cn), 0), V);
    lost = lost + (V - 0.5*(v + vn))*h;
    v = vn;
end
eg = lost;
end
