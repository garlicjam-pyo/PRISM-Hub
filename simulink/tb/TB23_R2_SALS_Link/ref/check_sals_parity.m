function check_sals_parity()
%CHECK_SALS_PARITY  회로 부하 블록 함수(ctrl/prism_sals_loads.m)와 검증 코드 sals_loads.SalsLoads(E29)의 대조.
%
%   ref/sals_parity.csv(make_sals_parity.py가 만든 무작위 시나리오 40개 × 0–80 ms, 0.1 ms 간격)의 입력을 시나리오마다
%   함수에 차례로 넣고(지속 변수는 시나리오마다 지움), Python이 계산한 부하 전력과의 최대 차를 잰다. 기준: 최대 차 ≤ 1 W.
%   결과: ref/check_sals_parity.txt
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', 'ctrl'));
D = readmatrix(fullfile(here, 'sals_parity.csv'));
sids = unique(D(:, 1));
worst = 0; wsid = -1;
for s = sids'
    clear prism_sals_loads
    R = D(D(:, 1) == s, :);
    for k = 1:size(R, 1)
        [~, p] = prism_sals_loads(R(k, 2), R(k, 3), R(k, 4), R(k, 5:26));
        e = abs(p - R(k, 27));
        if e > worst, worst = e; wsid = s; end
    end
end
fid = fopen(fullfile(here, 'check_sals_parity.txt'), 'w');
msg = sprintf('prism_sals_loads vs sals_loads.SalsLoads: %d scenarios, %d samples, max |dP| = %.3g W (scenario %d) -> %s\n', ...
    numel(sids), size(D, 1), worst, wsid, ternary(worst <= 1, 'PASS', 'FAIL'));
fprintf('%s', msg); fprintf(fid, '%s', msg); fclose(fid);
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
