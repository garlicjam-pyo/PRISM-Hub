function [g, st_out] = prism_va_clamp(t, vA, prm)
%#codegen
%PRISM_VA_CLAMP  V_A 노드 클램프(저항 + 스위치) 히스테리시스 비교기. TB20부터.
%
%   [g, st] = prism_va_clamp(t, vA, prm),  prm = [dt v_on v_off n_delay]
%   켬 요청: v_A ≥ v_on, 끔 요청: v_A ≤ v_off(켜진 동안 v_A > v_off이면 유지).
%   요청이 바뀐 뒤 n_delay 간격(스위치·구동 지연, 기본 1 µs) 동안 같은 요청이 이어지면 스위치 상태를 바꾼다.
%   검증 코드 E26(run_event의 클램프)과 같은 논리다.
%   출력: g 게이트(1 켬), st [상태; 지연 카운터]

persistent on cnt want_prev
if isempty(on)
    on = 0; cnt = 0; want_prev = 0;
end
von = prm(2); voff = prm(3); nd = prm(4);
want = double(vA >= von || (on > 0.5 && vA > voff));
if want ~= on
    if want == want_prev
        cnt = cnt + 1;
    else
        cnt = 1;
    end
    if cnt >= nd
        on = want; cnt = 0;
    end
else
    cnt = 0;
end
want_prev = want;
g = on;
st_out = [on; cnt];
end
