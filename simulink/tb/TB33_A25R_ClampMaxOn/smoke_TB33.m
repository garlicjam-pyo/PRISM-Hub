function smoke_TB33()
%SMOKE_TB33  TB33 사례 C33(920 V 충전 중 오동작 강제 켬)을 2.1 ms(강제 켬 0.6 ms 뒤, 최대 켜짐 시간에 따른 끔 직후)까지만 돌려
%   모델·클램프 비교기(prism_va_clamp_m)·판정 코드를 점검한다(결과 results/smoke, 판정은 의미 없음).
assignin('base', 'TB33_tend', 2.1e-3);
try
    run_TB33(3);
catch e
    evalin('base', 'clear TB33_tend');
    rethrow(e);
end
evalin('base', 'clear TB33_tend');
end
