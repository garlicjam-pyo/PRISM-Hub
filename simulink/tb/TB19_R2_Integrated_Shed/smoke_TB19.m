function smoke_TB19()
%SMOKE_TB19  TB19 사례 A를 1.6 ms(고장 0.1 ms 뒤)까지만 돌려 모델·판정 코드를 점검한다(결과 results/smoke, 판정은 의미 없음).
assignin('base', 'TB19_tend', 1.6e-3);
try
    run_TB19(1);
catch e
    evalin('base', 'clear TB19_tend');
    rethrow(e);
end
evalin('base', 'clear TB19_tend');
end
