function smoke_TB17()
%SMOKE_TB17  TB17 사례 A를 1.6 ms(고장 0.1 ms 뒤)까지만 돌려 모델·판정 코드를 점검한다(결과 results/smoke, 판정은 의미 없음).
assignin('base', 'TB17_tend', 1.6e-3);
try
    run_TB17(1);
catch e
    evalin('base', 'clear TB17_tend');
    rethrow(e);
end
evalin('base', 'clear TB17_tend');
end
