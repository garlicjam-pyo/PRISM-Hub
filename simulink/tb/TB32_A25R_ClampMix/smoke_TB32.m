function smoke_TB32()
%SMOKE_TB32  TB32 사례 A32(640 V 무부하 경로 상실, 가지 저항 섞임)을 1.56 ms(경로 상실 60 µs 뒤)까지만 돌려 모델·판정 코드를 점검한다
%   (결과 results/smoke, 판정은 의미 없음).
assignin('base', 'TB32_tend', 1.56e-3);
try
    run_TB32(1);
catch e
    evalin('base', 'clear TB32_tend');
    rethrow(e);
end
evalin('base', 'clear TB32_tend');
end
