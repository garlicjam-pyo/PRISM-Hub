function plot_TB04B_resolution()
%PLOT_TB04B_RESOLUTION  게이트 시간 분해능과 마지막 1 ms 버스 리플: Simscape 회로(TB04·TB04B)와 검증 모델(E12, 에지 양자화)을 한 그림에.
%
%   입력(이미 계산된 결과를 읽기만 한다)
%     results/TB04B_coss_summary.json, TB04B_resolution_summary.json, TB04B_resolution_B_summary.json  (Simscape, 후보 소자 C_oss)
%     ../TB04_StageB_ClosedLoop/results/TB04_<사례>[_dt*]_summary.json                                   (Simscape, C_oss 100 pF)
%     ref/E12_gate_resolution_representative.csv   (검증 모델 E12에 게이트 에지 양자화를 넣은 값, E12 gate_resolution 파트)
%   출력: results/TB04B_resolution.png

here = fileparts(mfilename('fullpath'));
res = fullfile(here, 'results');
tb04 = fullfile(fileparts(here), 'TB04_StageB_ClosedLoop', 'results');

% Simscape, 후보 소자 출력용량
S = [];
for f = {'TB04B_coss_summary.json', 'TB04B_resolution_summary.json', 'TB04B_resolution_B_summary.json'}
    p = fullfile(res, f{1});
    if exist(p, 'file'), j = jsondecode(fileread(p)); S = [S; j.runs(:)]; end %#ok<AGROW>
end
dev = S(arrayfun(@(x) x.coss_s_pF > 1000 && x.coss_p_pF > 300, S));
% Simscape, C_oss 100 pF(TB04)
T = struct('case', {}, 'dt', {}, 'rip', {});
for c = {'A_640V_15to25kW', 'B_788V_0to10kW'}
    for d = {'', '_dt2.5ns', '_dt1.25ns'}
        p = fullfile(tb04, ['TB04_' c{1} d{1} '_summary.json']);
        if exist(p, 'file')
            j = jsondecode(fileread(p));
            T(end+1) = struct('case', c{1}, 'dt', j.dt_ns, 'rip', j.ripple_last1ms_V); %#ok<AGROW>
        end
    end
end
% 검증 모델(E12) 에지 양자화: [사례(1=A, 2=B), q_H ns, q_DAB ns, 리플 V]
E = readmatrix(fullfile(here, 'ref', 'E12_gate_resolution_representative.csv'));
E = E(E(:, 2) > 0 & E(:, 2) == E(:, 3), :);

f = figure('Visible', 'off', 'Position', [100 100 980 620]); hold on; grid on;
set(gca, 'XScale', 'log', 'XDir', 'reverse');
mk = {'o', 's'}; nm = {'A_640V_15to25kW', 'B_788V_0to10kW'}; lab = {'case A', 'case B'};
cl = lines(3);
for k = 1:2
    e = E(E(:, 1) == k, :); [~, o] = sort(e(:, 2));
    plot(e(o, 2), max(e(o, 4), 1e-3), ['-' mk{k}], 'Color', cl(1, :), 'LineWidth', 1.2, 'MarkerFaceColor', 'w', ...
        'DisplayName', ['E12 + edge quantisation, ' lab{k}]);
    t = T(strcmp({T.case}, nm{k})); [~, o] = sort([t.dt]);
    if ~isempty(t)
        plot([t(o).dt], [t(o).rip], ['--' mk{k}], 'Color', cl(2, :), 'LineWidth', 1.2, ...
            'DisplayName', ['Simscape, C_{oss} 100 pF (TB04), ' lab{k}]);
    end
    d = dev(strcmp({dev.case}, nm{k})); [~, o] = sort([d.dt_ns]);
    if ~isempty(d)
        plot([d(o).dt_ns], [d(o).ripple_V], ['-' mk{k}], 'Color', cl(3, :), 'LineWidth', 1.6, 'MarkerFaceColor', cl(3, :), ...
            'DisplayName', ['Simscape, C_{oss} 335/1371 pF (TB04B), ' lab{k}]);
    end
end
yline(0.1, 'k:', 'Tier-1 limit 0.1 V', 'LabelHorizontalAlignment', 'left', 'HandleVisibility', 'off');
xline(0.15, 'k-.', 'HRPWM ~150 ps', 'LabelVerticalAlignment', 'bottom', 'HandleVisibility', 'off');
set(gca, 'YScale', 'log'); ylim([1e-3 1]); xlim([0.06 6]);
xlabel('gate edge time grid (PWM duty / DAB phase resolution) [ns]'); ylabel('last-1 ms bus ripple (5 \mus period mean, max-min) [V]');
legend('Location', 'eastoutside', 'FontSize', 8);
title({'Stage B closed loop: limit-cycle ripple vs gate time resolution', 'case A: 640 V, 15 \rightarrow 25 kW   case B: 788 V, 0 \rightarrow 10 kW'});
exportgraphics(f, fullfile(res, 'TB04B_resolution.png'), 'Resolution', 150); close(f);
fprintf('saved %s\n', fullfile(res, 'TB04B_resolution.png'));
end
