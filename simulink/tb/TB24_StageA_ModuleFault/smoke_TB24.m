function smoke_TB24()
%SMOKE_TB24  TB24 사례 FF(800 V 충전, 모듈 1 고장)를 0.6 ms(고장 0.5 ms 뒤 0.1 ms)까지만 돌려 모델·판정 코드를 점검한다
%   (결과 results/smoke, 판정은 의미 없음).
assignin('base', 'TB24_tend', 0.6e-3);
try
    run_TB24(3);
catch e
    evalin('base', 'clear TB24_tend');
    rethrow(e);
end
evalin('base', 'clear TB24_tend');
end
