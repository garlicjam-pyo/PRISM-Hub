function smoke_TB29()
%SMOKE_TB29  TB29 사례 A29(920 V 경로 상실)을 1.56 ms(경로 상실 60 µs 뒤)까지만 돌려 모델·판정 코드를 점검한다
%   (결과 results/smoke, 판정은 의미 없음).
assignin('base', 'TB29_tend', 1.56e-3);
try
    run_TB29(1);
catch e
    evalin('base', 'clear TB29_tend');
    rethrow(e);
end
evalin('base', 'clear TB29_tend');
end
