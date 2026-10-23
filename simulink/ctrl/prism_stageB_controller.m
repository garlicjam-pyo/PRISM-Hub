function [u, dg] = prism_stageB_controller(y, prm, init, tab, rst)
%#codegen
%PRISM_STAGEB_CONTROLLER  Stage B 채택 제어기 1회 계산(제어주기 5 µs, 반송파 최댓값에서 표본).
%
%  검증 코드(model_stage_b_switching.run_core의 제어 부분)와 같은 법칙이다.
%   (1) 1주기 예측: 고속 상태 [i_p, v_s, i_h]를 직전 변조율로 5 µs 앞까지 공칭 모델로 적분(중점법 5단계)
%   (2) 상태궤환 + 버스전압 적분 → 브리지 전류지령(±84 A 포화, 역포화 보정)
%   (3) 내부 전류 법칙 → 변조율 m(±0.95)
%   (4) 링크전압 PI + 소비전류 앞먹임 → DAB 링크전류 지령(정격 80 A·8 kW·SPS 한계)
%   (5) DAB 링크전류 → 위상: 누설 인덕턴스 −10 % 기준 앞먹임 + 측정 전류비 ρ̂ 보정 + 저전류 가산 보정 ε̂
%   (6) H-브리지 데드타임 보상: 교정표 × 전류 스케줄 κ(20 A 이하 0.6 → 80 A 1.0)
%
%  입력
%   y    = [i_p v_s v_bus i_h v_link V_bat i_link_avg ph_c0 ph_c1]  (표본값)
%          i_link_avg : 직전 제어주기의 DAB 링크 직류전류 평균(측정)
%          ph_c0/ph_c1: 그 주기의 두 반주기 중심에서 적용된 유효 위상(게이트 생성기가 기록)
%   prm  = 상수 벡터(prism_hub_params의 P.ctrl_prm)
%           1 L  2 Cs  3 Cb  4 R  5 Lh  6 Rh  7 Clink  8 Ts  9 vref  10 vlink  11 mmax  12 refmax
%          13 link_max  14 power_max  15 link_bw  16 inner_tau  17 Ldab  18 fs  19 turns  20 phmax
%          21–25 K  26 lmin(0.9)  27 ρ̂ 이득  28 ρ̂ 최소 전류  29 ε̂ 이득  30 ε̂ 상한
%          31 κ 경부하 비율  32 κ 시작 전류  33 κ 1 도달 전류  34 교정표 기준 링크전압  35 예측 단계 수
%          36 예측 사용(1)  37 데드타임 보상 사용(1)
%   init = [q0 q_link0 m0 i_link0]   (평형점에서 시작: 적분기가 지령 = i_p가 되도록)
%   tab  = [i_grid; E(i)]            데드타임 교정표(전류별 상승 전이 한 번의 전압·시간 손실)
%   rst  = (선택, R2 창 조정 모듈 TB08) 1이면 이번 표본에서 무충격 재초기화한다. 적분기를 지령 = 경로전류가 되도록 맞추고
%          링크 적분기·직전 변조율·ρ̂·ε̂를 처음 값(0, 0, 1, 0)으로 둔다(검증 코드 StageBController.reset과 같은 계산).
%          영벡터·바이패스로 제어 출력이 쓰이지 않는 동안 매 표본 다시 맞춰, 제어를 시작할 때 충격이 없게 한다.
%          네 입력으로 부르면(TB04–TB07) 이 기능은 없고 계산은 이전과 같다.
%  출력
%   u  = [PWM 비교값(데드타임 보상 후); DAB 유효 위상 지령 rad]
%   dg = [m 지령(보상 전); 링크전류 지령; 브리지 전류지령; ρ̂; ε̂; 예측 링크전류]

persistent q qlink mprev rho epsA vbprev started
if isempty(started)
    q = init(1); qlink = init(2); mprev = init(3); rho = 1; epsA = 0; vbprev = y(3); started = 1;
end

L = prm(1); Cs = prm(2); R = prm(4); Lh = prm(5); Rh = prm(6); Clink = prm(7); Ts = prm(8);
vref = prm(9); vlink = prm(10); mmax = prm(11); refmax = prm(12);
link_max = prm(13); power_max = prm(14); link_bw = prm(15); itau = prm(16);
Ldab = prm(17); fs = prm(18); turns = prm(19); phmax = prm(20);
K = prm(21:25);
lmin = prm(26); est_g = prm(27); est_min = prm(28); eps_g = prm(29); eps_max = prm(30);
k_scale = prm(31); k_from = prm(32); k_full = prm(33); Vtab = prm(34); nsub = prm(35);

ip = y(1); vs = y(2); vb = y(3); ih = y(4); vl = y(5); vbat = y(6);
il_meas = y(7); ph_c0 = y(8); ph_c1 = y(9);
if nargin >= 5                                   % (R2, TB08) 무충격 재초기화
    if rst > 0.5
        q = -(ip + K(1)*ip + K(2)*vs + K(3)*vb + K(4)*ih)/K(5);
        qlink = 0; mprev = 0; rho = 1; epsA = 0; vbprev = vb;
    end
end

% ---- (1) 1주기 예측 -----------------------------------------------------------------
sip = ip; svs = vs; sih = ih;
if prm(36) > 0.5
    m = mprev; h = Ts/nsub;
    for s = 1:nsub
        a1 = (vbat/2 - R*sip + svs - vb)/L;
        a2 = (sih - sip)/Cs;
        a3 = (m*vl - svs - Rh*sih)/Lh;
        mp = sip + 0.5*h*a1;  mv = svs + 0.5*h*a2;  mh = sih + 0.5*h*a3;
        b1 = (vbat/2 - R*mp + mv - vb)/L;
        b2 = (mh - mp)/Cs;
        b3 = (m*vl - mv - Rh*mh)/Lh;
        sip = sip + h*b1;  svs = svs + h*b2;  sih = sih + h*b3;
    end
end
% ---- (2) 상태궤환 + 적분 -----------------------------------------------------------
raw  = -(K(1)*sip + K(2)*svs + K(3)*vb + K(4)*sih) - K(5)*q;
iref = min(refmax, max(-refmax, raw));
q = q + Ts*(vref - vb) + 0.1*(iref - raw)/(-K(5));
% ---- (3) 내부 전류 법칙 → 변조율 ---------------------------------------------------
vlx = max(vl, 1);                                % (보상 계산용 하한)
mraw = (svs + Rh*sih + Lh/itau*(iref - sih))/vl;
mcmd = min(mmax, max(-mmax, mraw));
% ---- (4) 링크전압 PI + 앞먹임 → DAB 링크전류 지령 ---------------------------------
w = 2*pi*link_bw;
rawlink = mcmd*sih + Clink*(2*0.7*w*(vlink - vl) + w*w*qlink);
sps = max(vb, 0)*turns*phmax*(1 - phmax/pi)/(2*pi*fs*Ldab);
lim = min(min(link_max, sps), power_max/max(vl, 1e-9));
icmd = min(lim, max(-lim, rawlink));
qlink = qlink + Ts*(vlink - vl) + 0.1*(icmd - rawlink)/(Clink*w*w);
mprev = mcmd;
% ---- (5) DAB 전류비·저전류 보정 → 위상 ----------------------------------------------
% 직전 주기 두 반주기 중심에 적용된 위상의 예측 전류. 그 위상을 적용할 때 쓰인 버스전압은 직전 표본값이다
% (검증 모델: 반주기 중심에서 그때의 측정 버스전압으로 예측 전류를 계산).
il_pred = 0.5*(ipred(ph_c0, vbprev, turns, fs, Ldab, lmin) + ipred(ph_c1, vbprev, turns, fs, Ldab, lmin));
vbprev = vb;
dph = abs(ph_c1 - ph_c0);
if abs(il_pred) >= est_min && il_meas*il_pred > 0 && dph < 0.035
    rho = rho + est_g*(il_meas/il_pred - rho);
    rho = min(max(rho, 0.75), 1.25);
end
if eps_g > 0
    if abs(il_pred) < est_min && dph < 0.035
        epsA = epsA + eps_g*((il_meas - rho*il_pred) - epsA);
    elseif abs(il_pred) >= est_min
        epsA = epsA - eps_g*epsA;
    end
    epsA = min(max(epsA, -eps_max), eps_max);
end
ph_new = phase_ff((icmd - epsA)/rho, vb, turns, fs, Ldab, lmin, phmax);
% ---- (6) H-브리지 데드타임 보상 ----------------------------------------------------
m_pwm = mcmd;
if prm(37) > 0.5
    kap = k_scale + (1 - k_scale)*min(max((abs(sih) - k_from)/max(k_full - k_from, 1e-9), 0), 1);
    m_pwm = mcmd - kap*dt_error_tab(mcmd, sih, vlx, Lh, fs, tab, Vtab)/vlx;
end
u  = [m_pwm; ph_new];
dg = [mcmd; icmd; iref; rho; epsA; il_pred];
end

% ======================================================================================
function i = ipred(ph, vb, turns, fs, Ldab, lb)
% 위상 ph에서 SPS 식이 주는 링크전류(누설 인덕턴스 = 공칭의 lb배 가정)
k = turns*max(vb, 1)/(2*pi*fs*Ldab*lb);
i = k*ph*(1 - abs(ph)/pi);
end

function ph = phase_ff(il, vb, turns, fs, Ldab, lb, phmax)
% 링크전류 → SPS 위상 앞먹임(|φ| ≤ φ_max)
k = turns*max(vb, 1)/(2*pi*fs*Ldab*lb);
a = min(abs(il)/(pi*k/4), 1);
ph = min(pi/2*(1 - sqrt(1 - a)), phmax);
if il < 0, ph = -ph; end
end

function d = dt_error_tab(m, i, V, Lh, f, tab, Vtab)
% 유니폴라 PWM 한 주기의 브리지 평균 전압오차 [V]: 리플 극값 전류에서의 전이별 손실을 교정표에서 읽는다.
sg = 1;
if m < 0, m = -m; i = -i; sg = -1; end
r = V*m*(1 - m)/(4*Lh*f);
imin = i - r; imax = i + r;
d = sg*2*(tab_interp(-imax, tab) - tab_interp(imin, tab))*(V/Vtab)*f;
end

function e = tab_interp(x, tab)
% 선형 보간(범위 밖은 끝값) — numpy.interp와 같음
n = size(tab, 2);
if x <= tab(1, 1), e = tab(2, 1); return; end
if x >= tab(1, n), e = tab(2, n); return; end
lo = 1; hi = n;
while hi - lo > 1
    mid = floor((lo + hi)/2);
    if tab(1, mid) <= x, lo = mid; else, hi = mid; end
end
w = (x - tab(1, lo))/(tab(1, hi) - tab(1, lo));
e = tab(2, lo) + w*(tab(2, hi) - tab(2, lo));
end
