%% prism_design_params.m
%  PRISM-Hub  --  WP1 설계 파라미터 스크립트 (수식 기반 산정 + 스윕)
%  실행: >> prism_design_params
%  결과: 구조체 P (Simulink 모델의 Model Workspace/Base Workspace 파라미터로 사용)
%  각 수식의 근거는 "PRISM-Hub_엔지니어링_설계검증서.md" 3장 참조
clear; clc;

%% 1. 시스템 사양 ---------------------------------------------------------
P.bat.Ns    = 216;                 % NMC 직렬 셀 수 (3.0~4.2 V/cell)
P.bat.Vmin  = P.bat.Ns*3.0;        % 648 V
P.bat.Vnom  = P.bat.Ns*3.65;       % 788 V
P.bat.Vmax  = P.bat.Ns*4.2;        % 907 V
P.bat.Vabs  = 920;                 % 소자 선정용 절대 최대
P.bus.V     = 400;                 % 중간버스 정격
P.chg.P     = 150e3;               % 400 V 급속충전 최대
P.chg.Ibus  = P.chg.P/P.bus.V;     % 375 A (충전기 측)
P.chg.Ibat  = P.chg.P/(2*P.bus.V); % 187.5 A (배터리 측)
P.aux.Pmax  = 25e3;                % 주행 모드 400 V 보조부하 최대
P.aux.Imax  = P.aux.Pmax/P.bus.V;  % 62.5 A

%% 2. Stage A : 2:1 공진형 스위치드-커패시터 (RSC) -------------------------
A.Nmod   = 4;   A.Nph = 2;                    % 4 모듈 x 2 위상 = 8 위상
A.Pmod   = P.chg.P/A.Nmod;                    % 37.5 kW
A.Iph    = A.Pmod/P.bus.V/A.Nph;              % 46.9 A (위상당 평균 출력전류)
A.Ipk    = pi/2*A.Iph;                        % 73.6 A (반파 정현 피크)
A.Irms_sw= A.Ipk/2;                           % 36.8 A (스위치 rms, 반주기 도통)
A.Irms_c = A.Ipk/sqrt(2);                     % 52.1 A (플라잉 캡 rms)
A.Vsw    = P.bat.Vabs/2;                      % 460 V (스위치 차단전압)
A.fr     = 150e3;                             % 공진주파수 (스윕 결과로 선정, 3.2절)
A.dVc    = 0.05*P.bus.V;                      % 캡 전압 스윙 5 % (20 V)
A.Cfly   = A.Iph/(2*A.fr*A.dVc);              % 7.8 uF
A.Lr     = 1/((2*pi*A.fr)^2*A.Cfly);          % 144 nH
A.tdead  = 100e-9;                            % 데드타임
% 이론: 도통구간(T/2 - tdead)이 공진 반주기와 일치 -> fs = fr_eff/(1+2*tdead*fr_eff), fr_eff = fr*(1+Cfly/(2*Cout))
% TB-A1 미세 스윕(Cout=400 uF) 결과 최적 fs/fr = 0.975~0.98 -> 0.98 채택 (147 kHz)
A.fs     = 0.98*A.fr;
A.Zr     = sqrt(A.Lr/A.Cfly);                 % 0.136 ohm
A.Iinrush= A.Vsw/A.Zr;                        % 3.4 kA (프리차지 없을 때) -> 프리차지 필수
% 소자 (750 V SiC, 12 mohm@125C, 2병렬)
A.Rds    = 12e-3/2;  A.Eoss = 12e-6*2;  A.Qg_E = 1e-6*2;
A.ESRc   = 1.5e-3;   A.RL = 1e-3;       A.Rmisc = 1.5e-3;
A.Pcond  = 4*A.Irms_sw^2*A.Rds;
A.Psw    = 4*A.Eoss*A.fs;                     % Coss 손실 (ZCS, 보수적 100 %)  [TB-A1 검증: 59.4 W/위상 @0.98fr]
A.Pgate  = 4*A.Qg_E*A.fs;
A.Pcap   = A.Irms_c^2*A.ESRc;  A.Pind = A.Irms_c^2*A.RL;  A.Pmisc = A.Irms_c^2*A.Rmisc;
A.Pph    = A.Pcond+A.Psw+A.Pgate+A.Pcap+A.Pind+A.Pmisc;   % 59 W/위상
A.Pmod_loss = A.Pph*A.Nph;                    % 118 W/모듈
A.eta_full  = 1 - A.Pmod_loss/A.Pmod;         % 99.69 %
A.Rout_mod  = A.Pmod_loss/(A.Pmod/P.bus.V)^2; % 13.4 mohm
A.Rout_sys  = A.Rout_mod/A.Nmod;              % 3.35 mohm
A.Rout_avg  = A.Rout_mod;                     % 평균값 모델(모듈)용 등가 출력저항 (위상 단위 모델은 2*Rout_mod: 2위상 병렬)
% fs 스윕 (효율 vs 수동소자 크기)
fs_sw = [50 100 150 200 300 400]*1e3;
for k = 1:numel(fs_sw)
    f = fs_sw(k); C_sweep = A.Iph/(2*f*A.dVc); L_sweep = 1/((2*pi*f)^2*C_sweep);
    Pl = A.Pcond + 4*A.Eoss*f + 4*A.Qg_E*f + A.Pcap + A.Pind + A.Pmisc;
    A.sweep(k,:) = [f/1e3, C_sweep*1e6, L_sweep*1e9, Pl, (1-Pl/(A.Pmod/A.Nph))*100];
end
A.sweep_cols = {'fs[kHz]','Cfly[uF]','Lr[nH]','Ploss/ph[W]','eta[%]'};

%% 3. Stage B : 부분전력 직렬 조정 셀 (PPRC, 절연 DAB) -----------------------
B.R_A=10.2e-3; B.Rpath=3e-3; B.Rtotal=B.R_A+B.Rpath; % same average path as TB-B
B.Ipath=zeros(1,3); B.Vser=zeros(1,3);
for k=1:3
    vbats=[P.bat.Vmin P.bat.Vnom P.bat.Vmax];
    xe=prism_pprc_equilibrium(vbats(k),P.aux.Pmax,B.Rtotal,P.bus.V);
    B.Ipath(k)=xe(1); B.Vser(k)=xe(2);
end
B.VA_mid = P.bus.V-B.Vser; % 주행 모드(1모듈)
B.dV      = P.bus.V - B.VA_mid;
B.kpr     = abs(B.dV.*B.Ipath)/P.aux.Pmax;    % output-fed power balance
B.P_need  = abs(B.dV.*B.Ipath);              % ideal DAB; losses would increase requirement
B.Prated  = 8e3;  B.Vser_max = 90;  B.Iser_max = 100;   % 정격 결정 (3.3절)
B.n       = 4;  B.V1 = 400;  B.V2 = 100;  B.fs = 200e3;  B.phi_max = pi/3;
B.Ls = 11.1e-6; % preserve reviewed hardware value; do not silently redesign
B.Isps = B.V1*B.n*B.phi_max*(1-B.phi_max/pi)/(2*pi*B.fs*B.Ls); % about 80.08 A
B.Cser    = 100e-6;                           % 직렬 출력 캡 (150 V 정격)
B.Rser    = 2*(4e-3/4);                       % 직렬 경로 도통저항 (200 V GaN 4병렬 x 2)
B.Pser_drive = B.Ipath.^2*B.Rser;             % operating-point-dependent path current
B.Pser_chg   = P.chg.Ibus^2*B.Rser + P.chg.Ibus^2*0.3e-3;  % 323 W (0.22 %) - 바이패스 채택 근거
B.eta_dab = 0.96;  B.Pidle = 15;
B.Isat_Vmin = min([B.Iser_max, B.Isps, B.Prated/abs(B.dV(1))]);
B.minimum_Vbat_no_load=2*(P.bus.V-B.Vser_max);
B.derate_Vbat = NaN; B.derate_Paux = NaN; % power derating alone cannot solve voltage reach
% 제어 (v1.1): 직렬 경로 공진 14.5 kHz(Q~10) -> PI 단독 1.8 kHz 상한, 상태궤환+적분(tb_b_pprc.m 극배치 8 kHz) 채택
B.Lpath  = 1.5e-6;  B.Cbus = 400e-6;
B.Ceff   = B.Cser*B.Cbus/(B.Cser+B.Cbus);
B.fres   = 1/(2*pi*sqrt(B.Lpath*B.Ceff));     % 14.5 kHz
B.fbw    = 8e3;                               % 상태궤환 설계 대역폭 (TB-S1: 60 A droop 4.7 V)
B.Iheadroom = @(Ipath) min(B.Iser_max,B.Isps) - Ipath; % current-only margin; also check voltage/power

%% 4. Stage C : 고정이득 CLLC 400 -> 48 V, 3 kW ------------------------------
C.Vo = 48; C.Po = 3e3; C.n = P.bus.V/C.Vo; C.turns = [25 3];
C.fr = 250e3; C.m = 6; C.Q = 0.4;
C.RL = C.Vo^2/C.Po;  C.Rac = 8*C.n^2*C.RL/pi^2;
C.Lr = C.Q*C.Rac/(2*pi*C.fr);  C.Cr = 1/((2*pi*C.fr)^2*C.Lr);  C.Lm = C.m*C.Lr;
C.Lr2 = C.Lr/C.n^2;  C.Cr2 = C.Cr*C.n^2;      % 2차측 대칭 탱크
C.Im_pk = P.bus.V/(4*C.Lm*C.fr);              % 6.1 A
C.Coss  = 100e-12;  C.tdead_min = 2*C.Coss*P.bus.V/C.Im_pk;
gain = @(fn,Q,m) 1./sqrt((1+(1/m)*(1-1./fn.^2)).^2 + (Q*(fn-1./fn).*(2+(1/m)*(1-1./fn.^2))).^2);
C.gain_tol = gain([0.97 1 1.03], C.Q, C.m);   % +-1 %
C.eta_target = 0.97;
% 12 V : 48->12 V 4상 동기 벅 1.5 kW
D.P = 1.5e3; D.Io = 125; D.Nph = 4; D.fs = 300e3; D.dI_ratio = 0.3;
D.L = (48-12)*(12/48)/(D.fs*D.dI_ratio*D.Io/D.Nph);   % 3.2 uH

%% 5. 버스 커패시터 ------------------------------------------------------------
BUS.C = 400e-6;  BUS.Vrated = 500;  BUS.E = 0.5*BUS.C*P.bus.V^2;   % 32 J
BUS.Rcpl = -P.bus.V^2/P.aux.Pmax;                                   % -6.4 ohm (CPL)
BUS.Cmin_cpl = B.Lpath/(B.Rtotal*abs(BUS.Rcpl)); % simple Rs-L-C/CPL only, not full PPRC proof
BUS.preboost = 0.02;
BUS.E_pb = 0.5*(BUS.C+B.Cser)*((P.bus.V*(1+BUS.preboost))^2 - P.bus.V^2);  % 1.6 J
BUS.t_pb_60A = BUS.E_pb/(P.bus.V*60);                               % 67 us

%% 6. SALS (v1.1: ARL 대체, 부록 D·H) ---------------------------------------------
A.Cin=100e-6; A.Cin_Vrated=1200; % provisional rating, component/lifetime selection pending
C.Po_combined_required=3e3+D.P/0.965; C.combined_rating_ok=C.Po>=C.Po_combined_required;
SALS.Tc = 1e-3; SALS.H = 15;                  % 1 ms 주기, 15 ms 지평선
SALS.Imax = 95;                               % 헤드룸 상한 = min(95 A, 0.95*8 kW/|dV|) (런타임 계산)
SALS.validated=false; % historical scheduler bound; must migrate to corrected plant/port constraints
SALS.win.comp = [0.020 0.220]; SALS.win.comp_k = 2.2;   % 컴프레서 명령 후 서지 가능 창 [s], 서지 계수
SALS.win.v2l  = 0.005;                        % V2L 요청 후 지연
SALS.win.susp = 7.5;                          % 서스펜션 상시 마진 [A]
SALS.w = [1.0 0.7 0.5];                       % 우선순위: 캐빈 PTC / 배터리 히터 / 48 V 저우선
SALS.uv_trip = 388; SALS.uv_act = 1e-3; SALS.uv_restore = 20e-3;   % 반응형 백업 부하 덤프

%% 7. 출력 ---------------------------------------------------------------------
P.A = A; P.B = B; P.C = C; P.D = D; P.BUS = BUS; P.SALS = SALS;
fprintf('Stage A: Cfly=%.1f uF, Lr=%.0f nH, eta_full=%.2f %%, Rout_sys=%.2f mohm, Iinrush(no precharge)=%.0f A\n', ...
    A.Cfly*1e6, A.Lr*1e9, A.eta_full*100, A.Rout_sys*1e3, A.Iinrush);
disp(array2table(A.sweep,'VariableNames',A.sweep_cols));
fprintf('Stage B: dV = [%+.0f %+.0f %+.0f] V, P_need = [%.2f %.2f %.2f] kW, Ls=%.1f uH, SPS current limit=%.2f A\n', ...
    B.dV, B.P_need/1e3, B.Ls*1e6, B.Isps);
fprintf('Stage C: Lr=%.1f uH, Cr=%.1f nF, Lm=%.0f uH, Im=%.1f A, gain(0.97/1/1.03)=[%.3f %.3f %.3f]\n', ...
    C.Lr*1e6, C.Cr*1e9, C.Lm*1e6, C.Im_pk, C.gain_tol);
fprintf('Bus: E=%.0f J, preboost 2%% = %.2f J -> %.0f us @60 A\n', BUS.E, BUS.E_pb, BUS.t_pb_60A*1e6);
if ~C.combined_rating_ok, warning('PRISM:CombinedRating','3 kW CLLC cannot supply both full LV port ratings continuously.'); end
save('prism_params.mat','P');
