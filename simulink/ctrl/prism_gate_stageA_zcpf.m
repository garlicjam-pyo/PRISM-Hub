function [g, st_out, mg_out] = prism_gate_stageA_zcpf(t, iC, prm, chg, en, off)
%#codegen
%PRISM_GATE_STAGEA_ZCPF  Stage A 4모듈 게이트(TB22의 zcpm) + 모듈 고장 처리(고장 모듈을 관리기 후보에서 뺌). TB24부터.
%
%   prism_gate_stageA_zcpm.m(E28)과 같은 순서·조건에 다음을 더했다(검증 코드 E30 model_stage_a.mgr_fault·일반화한 mgr_step과 같음).
%     0) 모듈 고장: 간격 번호 kk = n_f(prm(23))에서 모듈 fm(prm(22), 1–4, 0이면 없음)의 고장을 처리한다.
%        그 모듈 위상의 구간을 바로 0(네 스위치 끔)으로 하고 영구히 막는다. 건전 모듈 목록에서 빼고, 동작 중이었으면
%        동작 수를 1 줄인다. 동작 모듈이 0이 되면 다음 건전 모듈을 바로 두 위상으로 시작하고 추가 막는 시간 n_lock을 건다.
%     관리기는 건전 모듈 가운데 번호가 작은 것부터 동작시킨다(모듈 m의 순위 rk(m) ≤ 동작 수면 동작). 고장이 없으면
%     건전 모듈 = 1–4, 순위 = 번호라 zcpm과 같다.
%   그 밖의 설명은 prism_gate_stageA_zcpm.m을 본다.
%
%   입력  t, iC, chg, en, off: zcpm과 같다.
%         prm  zcpm의 21개 + [fm n_f] = 23개(fm: 고장 모듈 1–4, 0이면 고장 없음, n_f: 고장 간격 번호, 첫 호출 = 0)
%   출력  g 32×1, st_out 8×1, mg_out 8×1 [동작 수; 모듈 1–4 모드(고장 모듈은 0); If; 취소 수]

N = 8; NM = 4;
persistent st nxt tmr oncnt armed det psign mmode tlow blk If Ifm nact tdn tlock mcancel kstep kk fl
ndead = prm(2); nmin = prm(3); nmax = prm(4); ndet = prm(5); ithr = prm(6); nnom = prm(7);
Ioff = prm(8); Ion = prm(9); Ipkon = prm(10); a = prm(11); ndwell = prm(12);
Imup = prm(13); Imdn = prm(14); Ipkm = prm(15); ndwm = prm(16); nlock = prm(17); n0 = prm(18); If0 = prm(19); nhold = prm(20); am = prm(21);
fm = prm(22); nf = prm(23);
if isempty(st)
    st = zeros(N, 1); nxt = ones(N, 1); tmr = -off(:); oncnt = zeros(N, 1);
    armed = zeros(N, 1); det = zeros(N, 1); psign = zeros(N, 1);
    nact = n0; If = If0; Ifm = zeros(NM, 1); mmode = zeros(NM, 1); tlow = zeros(NM, 1); blk = zeros(N, 1);
    tdn = 0; tlock = 0; mcancel = 0; kstep = 0; kk = 0; fl = zeros(NM, 1);
    for m = 1:NM
        if m <= n0
            mmode(m) = 2; Ifm(m) = If0/n0;
        else
            blk(2*m - 1) = 1; blk(2*m) = 1;
        end
    end
end

% ---- 0) 모듈 고장(E30 mgr_fault) ---------------------------------------------------------------------------
if fm > 0 && kk == nf && fl(fm) < 0.5
    [hl, nh, rk] = healthy(fl, NM);
    was = rk(fm) <= nact;
    fl(fm) = 1;
    if was
        nact = nact - 1;
    end
    mmode(fm) = 0; tlow(fm) = 0; blk(2*fm - 1) = 1; blk(2*fm) = 1;
    for k = 2*fm - 1:2*fm
        st(k) = 0; tmr(k) = 0; armed(k) = 0; det(k) = 0; oncnt(k) = 0;
    end
    [hl, nh, rk] = healthy(fl, NM);
    if nact == 0 && nh > 0
        x = hl(1);
        mmode(x) = 2; tlow(x) = 0; blk(2*x - 1) = 0; blk(2*x) = 0;
        nact = 1; tdn = 0; tlock = nlock;
    end
end
[hl, nh, rk] = healthy(fl, NM);

% ---- 1) 출력전류와 필터 ---------------------------------------------------------------------------------
io = 0; iom = zeros(NM, 1);
for k = 1:N
    x = 0;
    if st(k) == 1
        x = iC(k);
    elseif st(k) == 2
        x = -iC(k);
    end
    io = io + x;
    m = ceil(k/2); iom(m) = iom(m) + x;
end
If = If + (io - If)*am;                           % 모듈 수 판단용(느린 필터)
Ifm = Ifm + (iom - Ifm)*a;

% ---- 2)·3) 모듈 관리 --------------------------------------------------------------------------------------
pk = 0;
for k = 1:N
    if mmode(ceil(k/2)) ~= 0 && abs(iC(k)) > pk
        pk = abs(iC(k));
    end
end
Ia = abs(If);
inhold = kstep < nhold;                              % 시작 유지 구간: 모듈 수를 바꾸지 않는다
if inhold
    kstep = kstep + 1;
end
if tlock > 0
    tlock = tlock - 1;
end
up = chg > 0.5 || (tlock == 0 && (Ia > nact*Imup || pk > Ipkm));
if inhold
    tdn = 0;
elseif nact < nh && up
    if chg > 0.5
        nnew = nh;
    else
        nnew = min(nh, max(nact + 1, ceil(Ia/Imup)));
    end
    for j = nact + 1:nnew
        m = hl(j);
        if mmode(m) == 5
            mcancel = mcancel + 1;
        end
        mmode(m) = 2; tlow(m) = 0; blk(2*m - 1) = 0; blk(2*m) = 0;
    end
    nact = nnew; tdn = 0; tlock = nlock;
elseif chg < 0.5 && nact > 1
    ndn = max(1, ceil(Ia/Imdn));
    if ndn < nact, tdn = tdn + 1; else, tdn = 0; end
    if tdn >= ndwm
        for j = ndn + 1:nact
            mmode(hl(j)) = 5;
        end
        for j = 1:ndn                                % 남는 모듈은 두 위상으로
            m = hl(j);
            if mmode(m) == 1 || mmode(m) == 3
                mmode(m) = 2; blk(2*m) = 0;
            end
            tlow(m) = 0;
        end
        nact = ndn; tdn = 0;
    end
else
    tdn = 0;
end

% ---- 4) 모듈별 위상 셰딩, 멈추는 모듈 ----------------------------------------------------------------------
for m = 1:NM
    kp = 2*m - 1; ks = 2*m;
    if rk(m) <= nact
        ret = abs(Ifm(m)) > Ion || abs(iC(kp)) > Ipkon;
        if mmode(m) == 2
            if abs(Ifm(m)) < Ioff, tlow(m) = tlow(m) + 1; else, tlow(m) = 0; end
            if tlow(m) >= ndwell, mmode(m) = 3; end
        elseif mmode(m) == 3
            if ret
                mmode(m) = 2; tlow(m) = 0;
            elseif st(ks) == 0
                blk(ks) = 1; mmode(m) = 1;
            end
        elseif mmode(m) == 1
            if ret
                blk(ks) = 0; mmode(m) = 2; tlow(m) = 0;
            end
        end
    elseif mmode(m) == 5
        if st(kp) == 0, blk(kp) = 1; end
        if st(ks) == 0, blk(ks) = 1; end
        if blk(kp) > 0.5 && blk(ks) > 0.5, mmode(m) = 0; end
    end
end

% ---- 5) 영교차 추종(방향 반전 처리, 막힌 위상은 시작하지 않음) ----------------------------------------------
for k = 1:N
    if en(k) < 0.5
        st(k) = 0;
        continue
    end
    if st(k) == 0 && tmr(k) >= ndead && blk(k) < 0.5
        st(k) = nxt(k); nxt(k) = 3 - nxt(k);
        armed(k) = 0; det(k) = 0; oncnt(k) = 0; tmr(k) = 0;
    end
    if st(k) ~= 0
        if armed(k) < 0.5 && abs(iC(k)) > 5*ithr
            psign(k) = sign(iC(k)); armed(k) = 1;
        end
        if armed(k) > 0.5
            cross = psign(k)*iC(k) < ithr;
        else
            cross = nnom == 0 && abs(iC(k)) < ithr;    % (E28) 무장 전: 부호 없는 영교차
        end
        if cross, det(k) = det(k) + 1; else, det(k) = 0; end
        oncnt(k) = oncnt(k) + 1;
        if (oncnt(k) >= nmin && cross && det(k) > ndet) || oncnt(k) >= nmax ...
                || (nnom > 0 && armed(k) < 0.5 && oncnt(k) >= nnom)
            st(k) = 0; tmr(k) = 0;
        end
    end
    if st(k) == 0
        tmr(k) = tmr(k) + 1;
    end
end

g = zeros(4*N, 1);
for k = 1:N
    b = 4*(k - 1);
    on1 = double(st(k) == 1); on2 = double(st(k) == 2);
    g(b + 1) = on1;    % S1 VIN–A
    g(b + 2) = on2;    % S2 A–V_A
    g(b + 3) = on1;    % S3 V_A–B
    g(b + 4) = on2;    % S4 B–GND
end
st_out = st;
mg_out = [nact; mmode; If; mcancel];
kk = kk + 1;
end

function [hl, nh, rk] = healthy(fl, NM)
% 건전 모듈 목록(번호 순, 앞 nh개가 유효), 개수, 모듈별 순위(고장 모듈은 99)
hl = zeros(NM, 1); rk = 99*ones(NM, 1); nh = 0;
for m = 1:NM
    if fl(m) < 0.5
        nh = nh + 1; hl(nh) = m; rk(m) = nh;
    end
end
end
