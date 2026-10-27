function smoke_TB22()
%SMOKE_TB22  TB22 사례 MC를 0.75 ms(충전 요청·충전기 램프 뒤)까지만 돌려 모델·판정 코드를 점검한다(결과 results/smoke, 판정은 의미 없음).
assignin('base', 'TB22_tend', 0.75e-3);
try
    run_TB22(3);
catch e
    evalin('base', 'clear TB22_tend');
    rethrow(e);
end
evalin('base', 'clear TB22_tend');
end
