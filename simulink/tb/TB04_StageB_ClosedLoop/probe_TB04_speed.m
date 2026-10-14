function probe_TB04_speed()
%PROBE_TB04_SPEED  TB04 모델의 실행 속도를 짧은 구간(20 µs, 50 µs)으로 잰다(진단용).
%
%   전체 실행(4 ms = 80만 간격)이 오래 걸릴 때 간격당 계산 시간을 확인하고, Simscape 지역 해석기의
%   고정 비용 설정(DoFixedCost, 비선형 반복 수)에 따른 차이를 비교한다.
%   결과: results/TB04_speed_probe.txt

here = fileparts(mfilename('fullpath'));
mdl  = 'TB04_StageB_ClosedLoop';
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
load_system(fullfile(here, [mdl '.slx']));
assignin('base', 'TB04_case', 'A_640V_15to25kW');
run(fullfile(here, 'TB04_init.m'));
slv = [mdl '/Solver'];
fid = fopen(fullfile(resDir, 'TB04_speed_probe.txt'), 'w');
cfgs = {'off', '', 'variable cost'; 'on', '2', 'fixed cost, 2 nonlinear iterations'; 'on', '3', 'fixed cost, 3 nonlinear iterations'};
orig = get_param(slv, 'DoFixedCost');
for k = 1:size(cfgs, 1)
    set_param(slv, 'DoFixedCost', cfgs{k, 1});
    if ~isempty(cfgs{k, 2}), set_param(slv, 'MaxNonlinIter', cfgs{k, 2}); end
    for tstop = [20e-6 50e-6]
        tic; out = sim(mdl, 'StopTime', num2str(tstop)); w = toc;
        n = numel(out.t);
        s = sprintf('%-38s stop %5.0f us: %6.1f s wall, %7d steps, %7.1f us/step, vbus end %.3f V\n', ...
            cfgs{k, 3}, 1e6*tstop, w, n, 1e6*w/n, out.vbus(end));
        fprintf('%s', s); fprintf(fid, '%s', s);
    end
end
set_param(slv, 'DoFixedCost', orig);
fclose(fid);
close_system(mdl, 0);
evalin('base', 'clear TB04_case');
end
