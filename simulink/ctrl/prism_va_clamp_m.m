function [g, st_out] = prism_va_clamp_m(t, vA, prm)
%#codegen
%PRISM_VA_CLAMP_M  V_A 클램프 비교기 + 최대 연속 켜짐 시간(설계 변경 M, E40) + 시험용 강제 켬. TB33부터.
%
%   [g, st] = prism_va_clamp_m(t, vA, prm),  prm = [dt v_on v_off n_delay n_onmax n_force]
%   비교기는 prism_va_clamp.m과 같다: 켬 요청 v_A ≥ v_on, 켜진 동안 v_A > v_off이면 유지, 요청이 n_delay 간격 이어지면 바꾼다.
%   n_onmax > 0: 스위치가 n_onmax 간격 연속으로 켜져 있으면 끔 요청을 낸다(같은 n_delay 뒤 꺼짐). 그 뒤는 보통 비교기 논리.
%   n_force > 0: 그 간격 번호에서 비교기와 무관하게 스위치를 바로 켠다(오동작 사건 시험, 한 번).
%   검증 코드 E26 run_event의 CL["t_on_max"]·CL["force_on_at"]과 같은 논리다.
%   출력: g 게이트(1 켬), st [상태; 지연 카운터; 연속 켜짐 간격 수; 강제 끔 횟수; 강제 끔 뒤 다시 켬 횟수]

persistent on cnt want_prev k ton nforced nreon forced_done
if isempty(on)
    on = 0; cnt = 0; want_prev = 0; k = 0; ton = 0; nforced = 0; nreon = 0; forced_done = 0;
end
von = prm(2); voff = prm(3); nd = prm(4); nmax = prm(5); nf = prm(6);
k = k + 1;
if nf > 0 && forced_done < 0.5 && k >= nf
    forced_done = 1;
    if on < 0.5
        on = 1; cnt = 0; ton = 0;
    end
end
cut = on > 0.5 && nmax > 0 && ton >= nmax;
want = double((vA >= von || (on > 0.5 && vA > voff)) && ~cut);
if want ~= on
    if want == want_prev
        cnt = cnt + 1;
    else
        cnt = 1;
    end
    if cnt >= nd
        on = want; cnt = 0;
        if on > 0.5
            ton = 0;
            if nforced > 0, nreon = nreon + 1; end
        elseif cut
            nforced = nforced + 1;
        end
    end
else
    cnt = 0;
end
want_prev = want;
if on > 0.5, ton = ton + 1; end
g = on;
st_out = [on; cnt; ton; nforced; nreon];
end
