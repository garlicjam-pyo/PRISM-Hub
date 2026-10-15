function run_TB04B_resolution()
%RUN_TB04B_RESOLUTION  TB04B 게이트 시간 분해능 점검: 후보 소자 출력용량(335/1371 pF)에서 적분 간격(= 게이트 에지 격자)을
%   1.25 ns(사례 A·B), 0.625 ns(사례 A, 사례 B는 run_TB04B_resolution_B)로 줄여 마지막 1 ms 버스 리플이 줄어드는지 본다.
%   결과 1·2(2.5 ns)가 리플 기준(0.1 V)을 넘은 원인이 게이트 에지의 시간 양자화(디지털 PWM 리밋 사이클)인지 확인하는 실행이다.
%   요약: results/TB04B_resolution_summary.txt·json (사례별 판정 파일은 TB04B_<사례>_device_<간격>_*)
run_TB04B(6:8, 'TB04B_resolution_summary');
end
