function smoke_TB20()
%SMOKE_TB20  TB20 사례 A를 1.56 ms(경로 상실 60 µs 뒤)까지만 돌려 모델·판정 코드를 점검한다(결과 results/smoke, 판정은 의미 없음).
assignin('base', 'TB20_tend', 1.56e-3);
try
    run_TB20(1);
catch e
    evalin('base', 'clear TB20_tend');
    rethrow(e);
end
evalin('base', 'clear TB20_tend');
end
