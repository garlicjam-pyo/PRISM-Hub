function run_TB04B_resolution_B()
%RUN_TB04B_RESOLUTION_B  TB04B 게이트 시간 분해능 점검의 추가 실행: 사례 B(788 V, 0 → 10 kW)를 0.625 ns로.
%   1.25 ns에서 사례 B의 마지막 1 ms 리플이 0.119 V로 남아(사례 A는 0.095 V), 경부하 DAB 위상 양자화의 영향을 더 고운 격자로 확인한다.
%   요약: results/TB04B_resolution_B_summary.txt·json
run_TB04B(9, 'TB04B_resolution_B_summary');
end
