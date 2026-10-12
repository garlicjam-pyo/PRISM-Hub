function run_TB01()
%RUN_TB01  TB01을 실행하고 검증 모델(Python, E1 공칭 사례)과 비교해 판정한다.
%
%   결과(results/ 폴더)
%     TB01_summary.txt / .json : 지표 비교표와 판정
%     TB01_waveforms.png       : 마지막 3주기 공진전류·C_fly 전압·출력전압(Simulink vs 검증 모델)
%     TB01_*.png               : 회로도(최상위, 위상 서브시스템, 스위치 셀, 게이트 생성기)

here = fileparts(mfilename('fullpath'));
mdl  = 'TB01_StageA_RSC';
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
run(fullfile(here, 'TB01_init.m'));
load_system(fullfile(here, [mdl '.slx']));

tic;
out = sim(mdl);
fprintf('simulation done: %.1f s wall, %d steps\n', toc, numel(out.t));

% ---- 마지막 10주기 지표 ---------------------------------------------------------------------
t = out.t(:); iC = out.iC(:); vC = out.vC(:); vo = out.vout(:); io = out.io(:); g1 = out.g1(:); g2 = out.g2(:);
T = TB.A.T;
m = t >= t(end) - TB.neval*T;
iCm = iC(m); g1m = g1(m); g2m = g2(m);
offIdx = find((g1m(1:end-1) > 0.5 & g1m(2:end) < 0.5) | (g2m(1:end-1) > 0.5 & g2m(2:end) < 0.5));
Ipk  = max(abs(iCm));
Ioff = max(abs(iCm(offIdx)));
S = struct();
S.zcs     = Ioff/Ipk;
S.Ipk     = Ipk;
S.Irms    = sqrt(mean(iCm.^2));
S.Iavg    = mean(io(m));
S.Vbus    = mean(vo(m));
S.ripple  = max(vo(m)) - min(vo(m));
S.vC_pp   = max(vC(m)) - min(vC(m));
S.vC_mean = mean(vC(m));
S.n_turnoff = numel(offIdx);

% ---- 검증 모델 기준값과 비교 ------------------------------------------------------------------
ref = jsondecode(fileread(fullfile(here, 'ref', 'TB01_ref_python.json')));
rows = { ...
  'zcs',    'ZCS ratio |i_off|/I_pk',    'abs', 0.01;
  'Ipk',    'peak resonant current [A]', 'rel', 0.03;
  'Irms',   'rms resonant current [A]',  'rel', 0.03;
  'Iavg',   'mean output current [A]',   'rel', 0.01;
  'Vbus',   'mean output voltage [V]',   'abs', 0.5;
  'vC_pp',  'C_fly ripple p-p [V]',      'rel', 0.05;
  'vC_mean','C_fly mean voltage [V]',    'abs', 0.5;
  'ripple', 'output ripple p-p [V] (info)', 'info', NaN};
fid = fopen(fullfile(resDir, 'TB01_summary.txt'), 'w');
pr = @(varargin) cellfun(@(f) fprintf(f, varargin{:}), {1, fid});
pr('TB01 Stage A single-phase RSC (fixed timing 0.98 f_r0) vs verification model (Python E1 nominal)\n');
pr('%-30s %12s %12s %10s %8s\n', 'metric', 'Simulink', 'reference', 'diff', 'result');
allPass = true;
for k = 1:size(rows, 1)
    key = rows{k, 1}; a = S.(key); b = ref.(key);
    switch rows{k, 3}
        case 'rel', d = (a - b)/b; ok = abs(d) <= rows{k, 4}; ds = sprintf('%+.2f%%', 100*d);
        case 'abs', d = a - b;     ok = abs(d) <= rows{k, 4}; ds = sprintf('%+.4g', d);
        otherwise,  d = a - b;     ok = true;                  ds = sprintf('%+.4g', d);
    end
    if strcmp(rows{k, 3}, 'info'), res = 'info'; elseif ok, res = 'PASS'; else, res = 'FAIL'; end
    allPass = allPass && ok;
    pr('%-30s %12.5g %12.5g %10s %8s\n', rows{k, 2}, a, b, ds, res);
    S.compare.(key) = struct('simulink', a, 'reference', b, 'diff', d, 'result', res);
end
S.verdict = ternary(allPass, 'PASS', 'FAIL');
S.zcs_criterion_5pct = ternary(S.zcs <= 0.05, 'PASS', 'FAIL');
pr('turn-off events evaluated: %d\n', S.n_turnoff);
pr('ZCS design criterion (<= 5%%): %s (%.2f%%)\n', S.zcs_criterion_5pct, 100*S.zcs);
pr('VERDICT (agreement with verification model): %s\n', S.verdict);
fclose(fid);
S.model = mdl; S.date = char(datetime('now')); S.matlab = version;
fid = fopen(fullfile(resDir, 'TB01_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);

% ---- 파형 비교 그림(마지막 3주기) -------------------------------------------------------------
w = readmatrix(fullfile(here, 'ref', 'TB01_ref_python_wave.csv'));
t3 = t(end) - 3*T;
ms = t >= t3; mw = w(:, 1) >= t3;
f = figure('Visible', 'off', 'Position', [100 100 900 750]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
nexttile; hold on; grid on;
plot(1e6*t(ms), iC(ms), 'LineWidth', 1.4);
plot(1e6*w(mw, 1), w(mw, 2), '--', 'LineWidth', 1.2);
area(1e6*t(ms), 80*g1(ms), 'FaceAlpha', 0.08, 'EdgeColor', 'none');
area(1e6*t(ms), -80*g2(ms), 'FaceAlpha', 0.08, 'EdgeColor', 'none');
ylabel('i_C [A]'); legend('Simulink (Simscape)', 'verification model (Python)', 'S1·S3 on', 'S2·S4 on', 'Location', 'eastoutside');
title(sprintf('resonant current: ZCS ratio %.2f %% (ref %.2f %%), I_{pk} %.1f A (ref %.1f A)', 100*S.zcs, 100*ref.zcs, S.Ipk, ref.Ipk));
nexttile; hold on; grid on;
plot(1e6*t(ms), vC(ms), 'LineWidth', 1.4); plot(1e6*w(mw, 1), w(mw, 3), '--', 'LineWidth', 1.2);
ylabel('v_{Cfly} [V]'); legend('Simulink', 'Python', 'Location', 'eastoutside');
nexttile; hold on; grid on;
plot(1e6*t(ms), vo(ms), 'LineWidth', 1.4); plot(1e6*w(mw, 1), w(mw, 4), '--', 'LineWidth', 1.2);
ylabel('v_{out} [V]'); xlabel('t [\mus]'); legend('Simulink', 'Python', 'Location', 'eastoutside');
title(tl, 'TB01 Stage A 1-phase RSC, fixed timing f_s = 0.98 f_{r0}, 46.875 A');
exportgraphics(f, fullfile(resDir, 'TB01_waveforms.png'), 'Resolution', 150);
close(f);

% ---- 회로도 그림 ----------------------------------------------------------------------------
sl_export_png({mdl, [mdl '/StageA_Phase1'], [mdl '/StageA_Phase1/S1_VIN_A'], [mdl '/Gate_StageA']}, resDir);
fprintf('results written to %s\n', resDir);
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
