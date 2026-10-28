function [i_load, p_load] = prism_sals_loads(t, vb, code, prm)
%#codegen
%PRISM_SALS_LOADS  400 V 부하의 등급별 계약 응답(SALS 메시지 지연·손실·워치독 포함). TB23부터.
%
%   검증 코드 sals_loads.SalsLoads(E29)와 같은 해석식이다. 보호 상태기계(ctrl/prism_r2_supervisor.m, SALS 모드)가
%   s(10)에 비트로 명령을 낸다: 1 접촉기 열림(400 V급 부하 분리), 2 SALS 감발, 4 SALS 되돌림, 8 Stage C 회생 차단,
%   16 Stage A 정지(이 블록은 쓰지 않음). 비트가 처음 켜진 시각을 명령 시각으로 잡는다.
%     M0  Stage C sc(회생 차단이면 t_sc 뒤 하한 0으로 sc_slew 변화율), V2L v2l(계단, SALS로 줄이지 않음)
%     M1  컴프레서 comp, D  PTC ptc·배터리 히터 bh:
%         감발 도착 = 명령 + 재송신 주기 × (앞의 손실 수) + 지연. 손실 수 −1이면 모두 손실(도착 없음).
%         D는 워치독으로 명령 + wd에 0으로 간다(마지막 유효 수신 ≤ 명령 시각). 도착 뒤 감소 변화율 dn으로 0까지.
%         되돌림 도착 뒤 증가 변화율 up으로 요청값까지(되돌림이 감발보다 먼저 도착하면 감발은 버려진다).
%     접촉기 열림이면 Stage C만 남는다. 버스가 v_cut 아래면 모든 부하가 끊긴다(검증 코드 E17의 저전압 차단).
%
%   입력  t 시각 [s], vb 버스전압(한 간격 지연·시작 보호), code s(10) 비트 명령,
%         prm [sc v2l comp ptc bh | d_comp d_ptc d_bh | k_comp k_ptc k_bh | kr_comp kr_ptc kr_bh |
%              period wd up dn t_sc sc_slew v_min v_cut]  (22개, 시간 [s]·변화율 [W/s]는 시간 축소를 이미 넣은 값)
%   출력  i_load = p_load / max(vb, v_min) [A], p_load [W]

persistent t_cut t_rest t_blk acut arest
if isempty(t_cut)
    t_cut = -1; t_rest = -1; t_blk = -1; acut = inf(3, 1); arest = inf(3, 1);
end
mix = prm(1:5); dl = prm(6:8); kc = prm(9:11); kr = prm(12:14);
period = prm(15); wd = prm(16); up = prm(17); dn = prm(18); t_sc = prm(19); sc_slew = prm(20); vmin = prm(21); vcut = prm(22);
c = round(code);
open_c = mod(c, 2) >= 1; cut = mod(floor(c/2), 2) >= 1; rest = mod(floor(c/4), 2) >= 1; blk = mod(floor(c/8), 2) >= 1;

if cut && t_cut < 0                                   % 감발 명령: 장치별 도착 시각
    t_cut = t;
    for j = 1:3
        if kc(j) < 0, a = inf; else, a = t + kc(j)*period + dl(j); end
        if j >= 2, a = min(a, t + wd); end            % D(PTC·배터리 히터) 워치독
        acut(j) = a;
    end
end
if (blk || cut) && t_blk < 0
    t_blk = t;
end
if rest && t_rest < 0 && t_cut >= 0                   % 되돌림 명령
    t_rest = t;
    for j = 1:3
        if kr(j) < 0, arest(j) = inf; else, arest(j) = t + kr(j)*period + dl(j); end
    end
end

% Stage C(M0): 회생 차단이면 하한 0으로
sc = mix(1);
if sc < 0 && t_blk >= 0 && t >= t_blk + t_sc
    sc = min(0, sc + sc_slew*(t - t_blk - t_sc));
end
p = sc;
if ~open_c
    p = p + mix(2);
    for j = 1:3
        p0 = mix(2 + j); ac = acut(j); ar = arest(j);
        if t < ac || ar <= ac
            pj = p0;
        else
            pj = max(p0 - dn*(t - ac), 0);
            if t >= ar
                pa = max(p0 - dn*(ar - ac), 0);
                pj = min(p0, pa + up*(t - ar));
            end
        end
        p = p + pj;
    end
end
if vb < vcut
    p = 0;
end
p_load = p;
i_load = p/max(vb, vmin);
end
