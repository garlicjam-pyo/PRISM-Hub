function smoke_TB27()
%SMOKE_TB27  TB27 사례 FF27(800 V 충전, 모듈 1 고장)를 1.3 ms(고장 1.1 ms 뒤 0.2 ms)까지만 돌려 모델·판정 코드를 점검한다
%   (결과 results/smoke, 판정은 의미 없음).
assignin('base', 'TB27_tend', 1.3e-3);
try
    run_TB27(1);
catch e
    evalin('base', 'clear TB27_tend');
    rethrow(e);
end
evalin('base', 'clear TB27_tend');
end
