function [g, st_out, sh_out] = prism_gate_stageA_zcps(t, iC, prm, en, off)
%#codegen
%PRISM_GATE_STAGEA_ZCPS  Stage A 영교차 추종 게이트 + 경부하 위상 셰딩(모듈 하나, 위상 keep·sh). TB18부터.
%
%   영교차 추종 부분은 prism_gate_stageA_zcp.m과 같다(위상마다 데드타임 → 구간 1·2 교대, 영교차 검출 지연 뒤 턴오프,
%   블랭킹·보호 창 0.80–1.12 × 공칭 도통시간). 여기에 검증 코드 model_stage_a.shed_step(E24)과 같은 셰딩 상태기계를
%   간격마다 영교차 갱신 직전에 한 번 진행한다.
%     1) 모듈 출력전류 i_o = Σ(구간 1이면 +i, 구간 2이면 −i)를 1차 필터(계수 a = dt/τ)로 거른다(If).
%     2) 모드 2(두 위상): |If| < I_off가 n_dwell 간격 이어지면 모드 3(멈추는 중).
%     3) 모드 3: 복귀 조건이면 모드 2(취소). 멈출 위상이 구간 0(구간을 자연 턴오프로 끝냄)이면 막고 모드 1.
%        → 도통 중인 구간을 자르지 않으므로 멈추는 순간도 영전류다.
%     4) 모드 1(위상 하나): 복귀 조건(|If| > I_on 또는 남는 위상 |i| > I_pk,on)이면 막음을 풀고 모드 2.
%        멈춘 위상은 데드타임 타이머가 이미 지났으므로 다음 간격에 멈추기 전 구간의 다음 구간부터 시작한다.
%   막힌 위상은 네 스위치를 모두 끈다(플라잉 커패시터 전압은 그대로 둔다).
%
%   입력  t    시각 [s] (Digital Clock, 간격 dt)
%         iC   8×1 위상별 공진전류 측정값 [A](한 간격 지연 + 시작 표본 보호)
%         prm  [dt n_dead n_min n_max n_det i_thr  I_off I_on I_pk_on a n_dwell keep sh]  (keep·sh는 1부터의 위상 번호)
%         en   1×8 위상 동작 여부, off 1×8 위상별 시작 지연 [간격 수]
%   출력  g      32×1 게이트, st_out 8×1 위상별 구간(0 데드타임, 1 충전, 2 방전)
%         sh_out 2×1 [셰딩 모드(2 둘, 3 멈추는 중, 1 하나), 필터한 모듈 출력전류 If [A]]

N = 8;
persistent st nxt tmr oncnt armed det psign smode If tlow blocked
ndead = prm(2); nmin = prm(3); nmax = prm(4); ndet = prm(5); ithr = prm(6);
Ioff = prm(7); Ion = prm(8); Ipkon = prm(9); a = prm(10); ndwell = prm(11); kp = prm(12); ks = prm(13);
if isempty(st)
    st = zeros(N, 1); nxt = ones(N, 1); tmr = -off(:); oncnt = zeros(N, 1);
    armed = zeros(N, 1); det = zeros(N, 1); psign = zeros(N, 1);
    smode = 2; If = 0; tlow = 0; blocked = 0;
end

% ---- 셰딩 상태기계(직전 간격의 구간·타이머로 판단) -----------------------------------------------------
io = 0;
for k = 1:N
    if en(k) > 0.5
        if st(k) == 1
            io = io + iC(k);
        elseif st(k) == 2
            io = io - iC(k);
        end
    end
end
If = If + (io - If)*a;
ret = abs(If) > Ion || abs(iC(kp)) > Ipkon;
if smode == 2
    if abs(If) < Ioff, tlow = tlow + 1; else, tlow = 0; end
    if tlow >= ndwell, smode = 3; end
elseif smode == 3
    if ret
        smode = 2; tlow = 0;
    elseif st(ks) == 0
        blocked = 1; smode = 1;
    end
elseif smode == 1
    if ret
        blocked = 0; smode = 2; tlow = 0;
    end
end

% ---- 영교차 추종(prism_gate_stageA_zcp.m과 같음, 막힌 위상은 시작하지 않음) --------------------------------
for k = 1:N
    if en(k) < 0.5
        st(k) = 0;
        continue
    end
    if st(k) == 0 && tmr(k) >= ndead && ~(blocked > 0.5 && k == ks)
        st(k) = nxt(k); nxt(k) = 3 - nxt(k);
        armed(k) = 0; det(k) = 0; oncnt(k) = 0; tmr(k) = 0;
    end
    if st(k) ~= 0
        if armed(k) < 0.5 && abs(iC(k)) > 5*ithr
            psign(k) = sign(iC(k)); armed(k) = 1;
        end
        cross = armed(k) > 0.5 && psign(k)*iC(k) < ithr;
        if cross, det(k) = det(k) + 1; else, det(k) = 0; end
        oncnt(k) = oncnt(k) + 1;
        if (oncnt(k) >= nmin && cross && det(k) > ndet) || oncnt(k) >= nmax
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
sh_out = [smode; If];
end
