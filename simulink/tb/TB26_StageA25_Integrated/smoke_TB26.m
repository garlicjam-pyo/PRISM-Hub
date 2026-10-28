function smoke_TB26()
%SMOKE_TB26  TB26 사례 FF25(800 V 충전, 모듈 1 고장)를 1.3 ms(고장 1.1 ms 뒤 0.2 ms)까지만 돌려 모델·판정 코드를 점검한다
%   (결과 results/smoke, 판정은 의미 없음).
assignin('base', 'TB26_tend', 1.3e-3);
try
    run_TB26(2);
catch e
    evalin('base', 'clear TB26_tend');
    rethrow(e);
end
evalin('base', 'clear TB26_tend');
end
