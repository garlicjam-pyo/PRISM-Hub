function smoke_TB30()
%SMOKE_TB30  TB30 사례 A30(640 V 무부하 경로 상실, 큰 저항 모서리)을 1.56 ms(경로 상실 60 µs 뒤)까지만 돌려 모델·판정 코드를 점검한다
%   (결과 results/smoke, 판정은 의미 없음).
assignin('base', 'TB30_tend', 1.56e-3);
try
    run_TB30(1);
catch e
    evalin('base', 'clear TB30_tend');
    rethrow(e);
end
evalin('base', 'clear TB30_tend');
end
