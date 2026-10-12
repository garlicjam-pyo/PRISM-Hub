function run_TB02()
%RUN_TB02  TB02 사례 15개를 실행하고, 회로의 데드타임 평균 전압오차를 제어기 교정표와 비교해 판정한다.
%
%   사례마다: 평균 필터전류 i, 평균 브리지 전압 v_AB를 마지막 10주기에서 구하고
%     ΔV_회로 = mean(v_AB) − V_link·(d_A − d_B)        (d_A, d_B: 게이트 목표의 실제 듀티 — 5 ns 격자 반영)
%     ΔV_표   = 제어기의 dt_error_tab(m, i, V_link, L_h, f_s, 교정표)   (ctrl/prism_stageB_controller.m와 같은 식)
%   판정: |ΔV_회로 − ΔV_표| ≤ 0.1 V + 5 %·|ΔV_표|
%   결과: results/TB02_summary.txt·json, TB02_deadtime_error.png, TB02_transition.png, 회로도 그림

here = fileparts(mfilename('fullpath'));
mdl  = 'TB02_StageB_HBridge';
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
evalin('base', 'clear TB_override');
run(fullfile(here, 'TB02_init.m'));
load_system(fullfile(here, [mdl '.slx']));

cases = TB.cases; n = size(cases, 1);
Np = TB.gate_prm(2); kk = (0:Np-1)'; car = 4*abs(kk/Np - 0.5) - 1;     % 게이트 생성기와 같은 반송파
R = zeros(n, 8);   % [m, i_target, i_avg, dV_circuit, dV_table, err, pass, wall s]
wave = [];
for j = 1:n
    assignin('base', 'TB_override', struct('m', cases(j, 1), 'i0', cases(j, 2)));
    tic; out = sim(mdl); wall = toc;
    TBj = evalin('base', 'TB');
    t = out.t(:); vAB = out.vAB(:); ih = out.ih(:);
    T = 1/TBj.B.fs;
    msk = (t > t(end) - TBj.neval*T - TBj.dt/2) & (t < t(end) - TBj.dt/2);
    m = TBj.m;
    vIdeal = TBj.Vlink*(mean(m > car) - mean(-m > car));
    iAvg = mean(ih(msk));
    dVc = mean(vAB(msk)) - vIdeal;
    dVt = dt_error_tab(m, iAvg, TBj.Vlink, TBj.B.Lh, TBj.B.fs, TBj.tab, TBj.Vtab);
    err = dVc - dVt;
    ok = abs(err) <= 0.1 + 0.05*abs(dVt);
    R(j, :) = [m, cases(j, 2), iAvg, dVc, dVt, err, ok, wall];
    fprintf('case %2d  m=%+.2f  i=%+7.2f A  dV_circuit=%+7.4f V  dV_table=%+7.4f V  err=%+7.4f V  %s  (%.1f s)\n', ...
        j, m, iAvg, dVc, dVt, err, ternary(ok, 'PASS', 'FAIL'), wall);
    if m == 0.5 && cases(j, 2) == 2          % 부분 영전압 스위칭 사례의 전이 파형 저장
        wave = struct('t', t, 'vA', out.vA(:), 'ih', ih, 'gAH', out.gAH(:), 'gAL', out.gAL(:), 'T', T, 'i', iAvg);
    end
end
% ---- 적분 간격 점검: 대표 3사례를 2.5 ns로 다시 계산(게이트 격자·데드타임 간격 수도 함께 바꾼다) ----------
chk = [3 9 11];  dt2 = TB.dt/2;
C = zeros(numel(chk), 5);   % [case, i_avg, dV_circuit(5 ns), dV_circuit(2.5 ns), dV_table]
for q = 1:numel(chk)
    j = chk(q);
    gp = TB.gate_prm; gp(1) = dt2; gp(2) = 2*gp(2); gp(3) = 2*gp(3); gp(4) = 2*gp(4);
    assignin('base', 'TB_override', struct('m', cases(j, 1), 'i0', cases(j, 2), 'dt', dt2, 'gate_prm', gp));
    out = sim(mdl);
    TBj = evalin('base', 'TB');
    t = out.t(:); vAB = out.vAB(:); ih = out.ih(:); T = 1/TBj.B.fs;
    msk = (t > t(end) - TBj.neval*T - TBj.dt/2) & (t < t(end) - TBj.dt/2);
    car2 = 4*abs((0:gp(2)-1)'/gp(2) - 0.5) - 1;
    vIdeal = TBj.Vlink*(mean(TBj.m > car2) - mean(-TBj.m > car2));
    iAvg = mean(ih(msk));
    C(q, :) = [j, iAvg, R(j, 4), mean(vAB(msk)) - vIdeal, dt_error_tab(TBj.m, iAvg, TBj.Vlink, TBj.B.Lh, TBj.B.fs, TBj.tab, TBj.Vtab)];
    fprintf('dt check case %d: i=%+.2f A  dV(5 ns)=%+.4f  dV(2.5 ns)=%+.4f  table=%+.4f\n', C(q, :));
end
evalin('base', 'clear TB_override');

% ---- 요약 -------------------------------------------------------------------------------------
fid = fopen(fullfile(resDir, 'TB02_summary.txt'), 'w');
out2(fid, 'TB02 Stage B H-bridge dead-time voltage error: Simscape circuit vs controller calibration table\n');
out2(fid, '%4s %6s %9s %11s %11s %9s %6s\n', 'case', 'm', 'i_avg[A]', 'dV_circ[V]', 'dV_tab[V]', 'err[V]', 'result');
for j = 1:n
    out2(fid, '%4d %+6.2f %+9.2f %+11.4f %+11.4f %+9.4f %6s\n', j, R(j, 1), R(j, 3), R(j, 4), R(j, 5), R(j, 6), ternary(R(j, 7), 'PASS', 'FAIL'));
end
S = struct('cases', n, 'passed', sum(R(:, 7)), 'max_abs_err_V', max(abs(R(:, 6))), ...
    'verdict', ternary(all(R(:, 7)), 'PASS', 'FAIL'), 'model', mdl, 'date', char(datetime('now')), 'matlab', version);
S.table = array2table(R, 'VariableNames', {'m', 'i_target', 'i_avg', 'dV_circuit', 'dV_table', 'err', 'pass', 'wall_s'});
out2(fid, 'passed %d/%d, max |err| = %.4f V (full-scale dead-time error 2*V*td*f = %.2f V)\n', S.passed, n, S.max_abs_err_V, 2*TB.Vlink*TB.B.td_h*TB.B.fs);
out2(fid, 'step-size check (dV_circuit at 5 ns vs 2.5 ns, table):\n');
for q = 1:size(C, 1)
    out2(fid, '  case %2d  i=%+7.2f A  5 ns %+8.4f V   2.5 ns %+8.4f V   table %+8.4f V\n', C(q, :));
end
S.dt_check = array2table(C, 'VariableNames', {'case_no', 'i_avg', 'dV_5ns', 'dV_2p5ns', 'dV_table'});
out2(fid, 'VERDICT: %s\n', S.verdict);
fclose(fid);
Sj = S; Sj.table = table2struct(S.table); Sj.dt_check = table2struct(S.dt_check);
fid = fopen(fullfile(resDir, 'TB02_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(Sj, 'PrettyPrint', true)); fclose(fid);

% ---- 그림 1: 전류별 데드타임 전압오차 ---------------------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 900 520]); hold on; grid on;
ii = linspace(-70, 70, 561);
ms = unique(R(:, 1))'; cols = lines(numel(ms)); lg = {};
for q = 1:numel(ms)
    curve = arrayfun(@(x) dt_error_tab(ms(q), x, TB.Vlink, TB.B.Lh, TB.B.fs, TB.tab, TB.Vtab), ii);
    plot(ii, curve, '-', 'Color', cols(q, :), 'LineWidth', 1.3);
    sel = R(:, 1) == ms(q);
    plot(R(sel, 3), R(sel, 4), 'o', 'Color', cols(q, :), 'MarkerFaceColor', cols(q, :), 'MarkerSize', 6);
    lg = [lg, {sprintf('table, m = %+.1f', ms(q)), sprintf('Simscape circuit, m = %+.1f', ms(q))}]; %#ok<AGROW>
end
xlabel('mean filter current i_h [A]'); ylabel('\DeltaV = mean v_{AB} - ideal [V]');
title(sprintf('TB02 dead-time voltage error (t_d = 50 ns, C_{oss} = 1 nF): %d/%d within tolerance, max |err| %.3f V', S.passed, n, S.max_abs_err_V));
legend(lg, 'Location', 'eastoutside');
exportgraphics(f, fullfile(resDir, 'TB02_deadtime_error.png'), 'Resolution', 150); close(f);

% ---- 그림 2: 부분 영전압 스위칭 전이(m = 0.5, i ≈ 2 A) ----------------------------------------
if ~isempty(wave)
    t = wave.t; T = wave.T;
    k1 = find(wave.gAL(1:end-1) > 0.5 & wave.gAL(2:end) < 0.5, 1, 'last');   % 레그 A 하측 소자 꺼짐(상승 전이 시작)
    win = (t >= t(k1) - 30e-9) & (t <= t(k1) + 120e-9);
    f = figure('Visible', 'off', 'Position', [100 100 900 600]);
    tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
    nexttile; plot(1e9*(t(win) - t(k1)), wave.vA(win), 'LineWidth', 1.4); grid on; ylabel('v_A node [V]');
    title(sprintf('leg A rising transition at i_h \\approx %.1f A (ripple valley)', wave.i));
    nexttile; plot(1e9*(t(win) - t(k1)), wave.ih(win), 'LineWidth', 1.4); grid on; ylabel('i_h [A]');
    nexttile; stairs(1e9*(t(win) - t(k1)), [wave.gAH(win), wave.gAL(win) + 0.02], 'LineWidth', 1.2); grid on;
    ylim([-0.1 1.2]); ylabel('gate'); legend('QA high', 'QA low'); xlabel('t - t_{off} [ns]');
    title(tl, 'TB02: dead time 50 ns, node charged by filter current through 2 \times C_{oss}');
    exportgraphics(f, fullfile(resDir, 'TB02_transition.png'), 'Resolution', 150); close(f);
end

sl_export_png({mdl, [mdl '/StageB_HBridge'], [mdl '/Gate_StageB'], [mdl '/StageB_HBridge/QA_high']}, resDir);
fprintf('results written to %s\n', resDir);
end

% ======================================================================================
function d = dt_error_tab(m, i, V, Lh, f, tab, Vtab)
% ctrl/prism_stageB_controller.m의 dt_error_tab과 같은 식(유니폴라 PWM 한 주기의 평균 전압오차 [V])
sg = 1;
if m < 0, m = -m; i = -i; sg = -1; end
r = V*m*(1 - m)/(4*Lh*f);
imin = i - r; imax = i + r;
d = sg*2*(tab_interp(-imax, tab) - tab_interp(imin, tab))*(V/Vtab)*f;
end

function e = tab_interp(x, tab)
e = interp1(tab(1, :), tab(2, :), min(max(x, tab(1, 1)), tab(1, end)), 'linear');
end

function out2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
