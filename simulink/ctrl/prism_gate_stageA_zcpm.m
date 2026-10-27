function [g, st_out, mg_out] = prism_gate_stageA_zcpm(t, iC, prm, chg, en, off)
%#codegen
%PRISM_GATE_STAGEA_ZCPM  Stage A 4모듈(8위상) 게이트: 영교차 추종(무장 전 부호 없는 검출) + 모듈 관리기 + 모듈별 위상 셰딩. TB22부터.
%
%   검증 코드 model_stage_a.mgr_step(E28)과 같은 순서·조건이다. 간격마다 영교차 갱신 직전에 한 번 진행한다
%   (판단에는 직전 간격의 구간 st를 쓴다). 모듈 m(1–4)은 위상 2m−1(남는 위상)·2m(셰딩 위상)이다.
%     1) 위상 출력전류(구간 1이면 +i, 2이면 −i)로 모듈 출력전류 iom과 전체 출력전류 io를 만들고 1차 필터로 거른다
%        (모듈 전류는 위상 셰딩용 계수 a, 전체 전류는 모듈 수 판단용 계수 a_m: 위상 펄스 리플을 거르는 느린 필터).
%     2) 모듈 추가(바로): 충전 요청(chg)이거나, 추가 뒤 막는 시간(n_lock)이 지났고 |If| > 동작 수 × Im_up이거나
%        동작 위상의 순시 |i| > Ipk_m이면 → 충전 요청이면 4개, 아니면 max(동작 수 + 1, ceil(|If|/Im_up))개.
%        멈추는 중이던 모듈은 취소(mcancel). 더한 모듈은 두 위상으로 시작한다.
%     (시작 유지) 시작 뒤 n_hold 간격 동안은 2)·3)을 하지 않는다(시작 과도로 모듈을 더하지 않도록).
%     3) 모듈 줄임(지속 뒤): 충전 요청이 없고 ceil(|If|/Im_dn) < 동작 수가 n_dwell_m 간격 이어지면 그 수로 줄인다.
%        줄인 모듈(모드 5)의 위상은 지금 구간을 자연 턴오프로 끝낸 뒤(구간 0) 막는다 → 끄는 순간도 영전류.
%        남는 모듈은 두 위상으로 되돌린다(줄인 모듈의 전류를 위상 하나가 받지 않도록).
%     4) 동작 모듈마다 경부하 위상 셰딩(E24·prism_gate_stageA_zcps.m과 같음, 복귀는 바로).
%     5) 영교차 추종: 무장한 반주기는 prism_gate_stageA_zcp.m과 같다. 무장하지 못한 반주기(|i|가 5·i_thr를 넘지 않음)는
%        prm(7) n_nom > 0이면 n_nom에서 끄고(E27·zcp_r 방식), n_nom = 0이면 부호 없이 |i| < i_thr가 검출 지연만큼
%        이어질 때 블랭킹(n_min) 뒤 끈다(E28 방식, 'mag'). 공진주파수가 낮은 위상(공차)이나 모듈 재시작 직후의 비대칭
%        펄스는 공칭 도통시간에 아직 1 A 넘게 흐를 수 있어(E28 transient 1차) 실제 영교차 근처에서 끈다.
%   막힌 위상은 네 스위치를 모두 끈다(플라잉 커패시터 전압은 그대로 둔다).
%
%   입력  t    시각 [s] (Digital Clock, 간격 dt)
%         iC   8×1 위상별 공진전류 측정값 [A](한 간격 지연 + 시작 표본 보호)
%         prm  [dt n_dead n_min n_max n_det i_thr n_nom(0 = 부호 없는 검출)  I_off I_on I_pk_on a n_dwell
%               Im_up Im_dn Ipk_m n_dwell_m n_lock n0 If0 n_hold a_m]  (21개, 간격 수 단위, n0 = 시작 동작 모듈 수,
%               If0 = 필터 초기값, n_hold = 시작 유지 간격 수, a_m = dt/τ_m 모듈 수 판단용 필터 계수)
%         chg  충전 요청(1이면 모든 모듈 동작: 충전기 전류 증가 전 사전 기동)
%         en   1×8 위상 동작 여부(0이면 강제 정지), off 1×8 위상별 시작 지연 [간격 수]
%   출력  g      32×1 게이트, st_out 8×1 위상별 구간(0 데드타임, 1 충전, 2 방전)
%         mg_out 8×1 [동작 모듈 수; 모듈 1–4 모드(0 정지, 2 두 위상, 3 셰딩 중, 1 위상 하나, 5 모듈 멈추는 중);
%                     필터한 전체 출력전류 If [A]; 모듈 멈추기 취소 수]

N = 8; NM = 4;
persistent st nxt tmr oncnt armed det psign mmode tlow blk If Ifm nact tdn tlock mcancel kstep
ndead = prm(2); nmin = prm(3); nmax = prm(4); ndet = prm(5); ithr = prm(6); nnom = prm(7);
Ioff = prm(8); Ion = prm(9); Ipkon = prm(10); a = prm(11); ndwell = prm(12);
Imup = prm(13); Imdn = prm(14); Ipkm = prm(15); ndwm = prm(16); nlock = prm(17); n0 = prm(18); If0 = prm(19); nhold = prm(20); am = prm(21);
if isempty(st)
    st = zeros(N, 1); nxt = ones(N, 1); tmr = -off(:); oncnt = zeros(N, 1);
    armed = zeros(N, 1); det = zeros(N, 1); psign = zeros(N, 1);
    nact = n0; If = If0; Ifm = zeros(NM, 1); mmode = zeros(NM, 1); tlow = zeros(NM, 1); blk = zeros(N, 1);
    tdn = 0; tlock = 0; mcancel = 0; kstep = 0;
    for m = 1:NM
        if m <= n0
            mmode(m) = 2; Ifm(m) = If0/n0;
        else
            blk(2*m - 1) = 1; blk(2*m) = 1;
        end
    end
end

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
elseif nact < NM && up
    if chg > 0.5
        nnew = NM;
    else
        nnew = min(NM, max(nact + 1, ceil(Ia/Imup)));
    end
    for m = nact + 1:nnew
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
        for m = ndn + 1:nact
            mmode(m) = 5;
        end
        for m = 1:ndn                                % 남는 모듈은 두 위상으로
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
    if m <= nact
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
end
