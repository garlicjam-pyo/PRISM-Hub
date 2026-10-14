function run_TB04_resolution()
%RUN_TB04_RESOLUTION  TB04 게이트 시간 분해능 점검: 정상상태 버스전압 잔류 리플이 PWM·DAB 에지 양자화에서 오는지 확인한다.
%
%   Simscape 고정 간격 모델은 H-브리지 PWM 비교와 DAB 에지를 적분 간격(5 ns) 격자에 맞춘다
%   (듀티 분해능 5 ns/5 µs = 0.1 %, DAB 위상 분해능 2π·5 ns/5 µs = 6.3 mrad ≈ 링크전류 0.72 A).
%   검증 모델(E12)은 간격 안의 에지 위치로 스위치 상태를 평균하므로 분해능 제한이 없다.
%   디지털 PWM의 분해능이 유한하면 적분 동작이 있는 루프는 양자화 준위 사이를 오가는 리밋 사이클을 낼 수 있다
%   (Peterchev & Sanders, IEEE TPEL 18(1), 2003). 같은 사례를 2.5 ns, 1.25 ns로 다시 계산해
%   마지막 1 ms 리플이 분해능에 비례해 줄어드는지 본다.
%   결과: results/TB04_<사례>_dt*ns_*, results/TB04_resolution.txt

here = fileparts(mfilename('fullpath'));
resDir = fullfile(here, 'results');
run_TB04({'A_640V_15to25kW', 'B_788V_0to10kW'}, struct('dt', 2.5e-9));
run_TB04({'A_640V_15to25kW'}, struct('dt', 1.25e-9));
rows = {'A_640V_15to25kW', '', 5; 'A_640V_15to25kW', '_dt2.5ns', 2.5; 'A_640V_15to25kW', '_dt1.25ns', 1.25; ...
        'B_788V_0to10kW', '', 5; 'B_788V_0to10kW', '_dt2.5ns', 2.5};
fid = fopen(fullfile(resDir, 'TB04_resolution.txt'), 'w');
hdr = sprintf('%-18s %8s %14s %14s %16s %10s\n', 'case', 'dt[ns]', 'ripple[V]', 'min vbus[V]', 'final ip diff[A]', 'verdict');
fprintf('%s', hdr); fprintf(fid, '%s', hdr);
for k = 1:size(rows, 1)
    f = fullfile(resDir, ['TB04_' rows{k, 1} rows{k, 2} '_summary.json']);
    if ~exist(f, 'file'), continue; end
    S = jsondecode(fileread(f));
    c = S.compare;
    mv = c(strcmp({c.metric}, 'min v_bus after step [V]'));
    fi = c(strcmp({c.metric}, 'final mean i_p [A]'));
    if isfield(S, 'ripple_last1ms_V'), rp = S.ripple_last1ms_V; else, rp = NaN; end
    s = sprintf('%-18s %8.2f %14.4f %14.3f %16.3f %10s\n', rows{k, 1}, rows{k, 3}, rp, mv.simscape, fi.simscape - fi.model, S.verdict);
    fprintf('%s', s); fprintf(fid, '%s', s);
end
fclose(fid);
end
