function [g, aux] = prism_gate_stageB(t, uc, ilink, prm, init)
%#codegen
%PRISM_GATE_STAGEB  Stage B 게이트 생성기(적분 간격 dt = 5 ns마다 실행).
%
%  H-브리지 : 유니폴라 PWM. 삼각 반송파 c(t)는 제어주기 시작(표본 시점)에서 +1, 반주기에서 −1.
%             레그 A 상측 목표 = (m > c), 레그 B 상측 목표 = (−m > c). 목표가 바뀌면 두 소자를 데드타임 동안
%             끄고(출력용량 충방전·다이오드 도통은 회로가 정함) 새 소자를 켠다.
%  DAB      : 50 % 구형파 두 풀브리지, 단일 위상천이. 에지는 반송파 반주기 중심 c_j에 대칭(1차 c_j − δ/2,
%             2차 c_j + δ/2, δ = φ·T/2π)으로 놓고, 지령은 도착 후 첫 반주기 중심에서 반영한다.
%             전이 반주기의 위상차를 이전·새 위상의 평균으로 두는 갱신(A ← −A + 2Δ, Δ = (A + δ_new)/2)으로
%             위상이 바뀔 때 변압기 직류 편류가 생기지 않게 한다(검증 코드와 같은 알고리즘).
%             에지 시각은 dt 격자에 반올림하고, 실제 실행 시각으로 다음 반주기의 A를 계산한다.
%  링크전류 : DAB 2차 브리지가 링크로 보내는 직류전류를 제어주기마다 평균해 다음 표본에 넘긴다.
%
%  입력  t      시뮬레이션 시각(Digital Clock, dt 간격)
%        uc     [PWM 비교값; DAB 유효 위상 rad]  (제어기 출력, 전달지연 뒤)
%        ilink  DAB 2차 브리지 → 링크 직류전류 [A](순시)
%        prm    [dt Np td_h(간격 수) td_d(간격 수) T]
%        init   [PWM 비교값 초기값, 위상 초기값, 링크전류 초기값]
%  출력  g      [A상측 A하측 B상측 B하측 | P1 P2 P3 P4 | S1 S2 S3 S4]  (1 = 켬)
%               DAB 브리지: 상태 +1 → 1·4번 켬, −1 → 2·3번 켬(1·2번이 레그 1, 3·4번이 레그 2, 홀수 = 상측)
%        aux    [링크전류 주기 평균; 그 주기 두 반주기 중심의 위상 φ_c0, φ_c1; 반송파; 1차 상태; 2차 상태]

persistent started kA kB tgtA tgtB A ph_tgt p_t s_t p_h s_h p_j s_j p_state s_state p_te s_te ...
           acc il_avg phc0 phc1 lat0 lat1
dt = prm(1); Np = prm(2); ndh = prm(3); ndd = prm(4); T = prm(5);
Nh = round(Np/2);
k  = round(t/dt);                     % 적분 간격 번호(0부터)
t0 = k*dt;

if isempty(started)
    started = 1;
    m0 = init(1); ph0 = init(2);
    c0 = 1;                            % k = 0의 반송파
    tgtA = double(m0 > c0); tgtB = double(-m0 > c0);
    kA = -1e9; kB = -1e9;              % 데드타임 없이 시작
    ph_tgt = ph0;
    d0 = ph0/(2*pi)*T;
    A = d0;
    p_t = [1e30 1e30]; s_t = [1e30 1e30]; p_h = [0 0]; s_h = [0 0];
    p_te = -1; s_te = -1;
    if d0 > 0
        p_j = 1; p_h(1) = -d0/2; p_state = 1;  s_j = 0; s_state = -1;
    elseif d0 < 0
        s_j = 1; s_h(1) = d0/2;  s_state = 1;  p_j = 0; p_state = -1;
    else
        p_j = 0; s_j = 0; p_state = -1; s_state = -1;
    end
    acc = 0; il_avg = init(3); phc0 = ph0; phc1 = ph0; lat0 = ph0; lat1 = ph0;
end

m = uc(1);
ph_tgt = uc(2);

% ---------------- H-브리지 유니폴라 PWM -------------------------------------------------
kin = mod(k, Np);
c = 4*abs(kin/Np - 0.5) - 1;
nA = double(m > c); nB = double(-m > c);
if nA ~= tgtA, tgtA = nA; kA = k; end
if nB ~= tgtB, tgtB = nB; kB = k; end
okA = (k - kA) >= ndh; okB = (k - kB) >= ndh;
gA_hi = double(okA && tgtA == 1); gA_lo = double(okA && tgtA == 0);
gB_hi = double(okB && tgtB == 1); gB_lo = double(okB && tgtB == 0);

% ---------------- DAB 위상 갱신(반주기 중심) --------------------------------------------
if mod(k, Nh) == 0
    j = k/Nh; cj = t0;
    if j >= 1
        jm = mod(j - 1, 2) + 1;
        A = -A + 2*(s_h(jm) - p_h(jm));
    end
    dtg = ph_tgt/(2*pi)*T;
    D = 0.5*(A + dtg);
    jj = mod(j, 2) + 1;
    p_done = p_j > j; s_done = s_j > j;
    if p_done && ~s_done
        s_t(jj) = max(cj, p_h(jj) + D);
    elseif s_done && ~p_done
        p_t(jj) = max(cj, s_h(jj) - D);
    elseif ~p_done && ~s_done
        if D >= 0
            p_t(jj) = cj; s_t(jj) = cj + D;
        else
            s_t(jj) = cj; p_t(jj) = cj - D;
        end
    end
    if p_done, tpj = p_h(jj); else, tpj = p_t(jj); end
    if s_done, tsj = s_h(jj); else, tsj = s_t(jj); end
    D1 = 0.5*(-A + 2*(tsj - tpj) + dtg);
    cn = (j + 1)*Nh*dt;
    p_t(3 - jj) = cn - D1/2; s_t(3 - jj) = cn + D1/2;
    if mod(j, 2) == 0, phc0 = ph_tgt; else, phc1 = ph_tgt; end
end
% ---------------- DAB 에지 실행(가장 가까운 간격에 반올림) ------------------------------
sp = mod(p_j, 2) + 1;
if p_t(sp) < t0 + 0.5*dt
    if mod(p_j, 2) == 0, p_state = 1; else, p_state = -1; end
    p_te = t0; p_h(sp) = t0; p_t(sp) = 1e30; p_j = p_j + 1;
end
ss = mod(s_j, 2) + 1;
if s_t(ss) < t0 + 0.5*dt
    if mod(s_j, 2) == 0, s_state = 1; else, s_state = -1; end
    s_te = t0; s_h(ss) = t0; s_t(ss) = 1e30; s_j = s_j + 1;
end
p_ok = (t0 - p_te) >= ndd*dt - 0.5*dt;
s_ok = (t0 - s_te) >= ndd*dt - 0.5*dt;
gP = [0 0 0 0]; gS = [0 0 0 0];
if p_ok
    if p_state > 0, gP = [1 0 0 1]; else, gP = [0 1 1 0]; end
end
if s_ok
    if s_state > 0, gS = [1 0 0 1]; else, gS = [0 1 1 0]; end
end

% ---------------- 링크전류 주기 평균(표본 직전 간격에서 확정) -------------------------
acc = acc + ilink;
if kin == Np - 1
    il_avg = acc/Np; acc = 0;
    lat0 = phc0; lat1 = phc1;
end

g = [gA_hi gA_lo gB_hi gB_lo gP gS]';
aux = [il_avg; lat0; lat1; c; p_state; s_state];
end
