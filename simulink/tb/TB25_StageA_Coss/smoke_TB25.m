function smoke_TB25()
%SMOKE_TB25  TB25 사례 O_nl_C(원설계, 무부하, 출력용량 있음)를 8주기만 돌려 모델·계산 코드를 점검한다(판정 의미 없음).
assignin('base', 'TB25_ncyc', 8);
try
    run_TB25({'O_nl_C'}, 'smoke');
catch e
    evalin('base', 'clear TB25_ncyc');
    rethrow(e);
end
evalin('base', 'clear TB25_ncyc');
end
