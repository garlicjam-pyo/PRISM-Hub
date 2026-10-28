function run_TB25(cases, tag)
%RUN_TB25  TB25 사례들을 실행하고 손실을 기준값(ref/TB25_cases.json, 검증 코드 E31)과 비교해 판정한다.
%
%   run_TB25()                 모든 사례(설계 O·A·B × 부하 nl·ld × 용량 0·C)
%   run_TB25({'O_nl_C'}, 'smoke')   지정 사례만(결과 results/smoke, 판정 없음)
%
%   손실(마지막 neval주기) = V_bat·mean(i_in) − mean(v_out·i_o) − [½C_fly·Δ(v_C²) + ½L_r·Δ(i_C²)]/Δt
%   판정(실행 전 고정, E31 문서)
%     T1 무부하 출력용량 손실 P(nl_C) − P(nl_0)이 4·C_oss·(V_bat/2)²·f_s와 5 % 안(설계마다)
%     T2 46.875 A 출력용량 있음 손실 P(ld_C)가 정확해(노드 용량 행렬 지수 해, 같은 출력전류)와 5 % 안
%     T3 46.875 A 출력용량 없음 손실 P(ld_0)이 E1 모델(sim_array 고정 타이밍)과 3 % 안
%   참고: 부하 시 출력용량 손실 P(ld_C) − P(ld_0)과 공식의 비(턴오프 잔류 전류가 노드를 일부 옮기면 1보다 작다)

here = fileparts(mfilename('fullpath'));
mdl  = 'TB25_StageA_Coss';
CS = jsondecode(fileread(fullfile(here, 'ref', 'TB25_cases.json')));
if nargin < 1 || isempty(cases), cases = fieldnames(CS.cases)'; end
if nargin < 2, tag = 'run'; end
resDir = fullfile(here, 'results');
if strcmp(tag, 'smoke'), resDir = fullfile(resDir, 'smoke'); end
if ~exist(resDir, 'dir'), mkdir(resDir); end
load_system(fullfile(here, [mdl '.slx']));

R = struct();
W = struct();
for k = 1:numel(cases)
    c = cases{k};
    assignin('base', 'TB25_case', c);
    run(fullfile(here, 'TB25_init.m'));
    TBc = evalin('base', 'TB');
    tic; out = sim(mdl); wall = toc;
    t = out.t(:); iin = out.iin(:); io = out.io(:); vo = out.vout(:); iC = out.iC(:); vC = out.vC(:);
    T = TBc.A.T;
    neval = min(TBc.neval, TBc.ncyc - 2);         % (smoke: 짧은 실행)
    t1 = t(end) - neval*T;
    m = t > t1 + 0.5*TBc.dt;
    i0 = max(find(m, 1) - 1, 1); i1 = numel(t);
    Pin = TBc.vbat*mean(iin(m));
    Pout = mean(vo(m).*io(m));
    dE = 0.5*TBc.A.Cfly*(vC(i1)^2 - vC(i0)^2) + 0.5*TBc.A.Lr*(iC(i1)^2 - iC(i0)^2);
    loss = Pin - Pout - dE/(t(i1) - t(i0));
    R.(c) = struct('loss_W', loss, 'Pin_W', Pin, 'Pout_W', Pout, 'dE_J', dE, 'Iout_A', mean(io(m)), 'Vout_V', mean(vo(m)), ...
                   'Ipk_A', max(abs(iC(m))), 'fs_Hz', 1/T, 'Coss_F', TBc.A.Coss, 'wall_s', wall, 'steps', numel(t));
    fprintf('%-8s loss %8.2f W (P_in %9.2f, P_out %9.2f), I_out %7.3f A, V_out %7.2f V, I_pk %6.1f A, f_s %.1f kHz, %.1f s\n', ...
        c, loss, Pin, Pout, mean(io(m)), mean(vo(m)), max(abs(iC(m))), 1e-3/T, wall);
    ms = t >= t(end) - 2*T;                      % 그림용 마지막 2주기
    W.(c) = struct('t', t(ms) - t(end), 'iC', iC(ms), 'iin', iin(ms));
end

S = struct('case', R, 'model', mdl, 'date', char(datetime('now')), 'matlab', version);
if strcmp(tag, 'smoke')
    fid = fopen(fullfile(resDir, 'TB25_smoke.json'), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
    fprintf('smoke done (no verdict)\n');
    return
end

% ---- 판정 -------------------------------------------------------------------------------------
fid = fopen(fullfile(resDir, 'TB25_summary.txt'), 'w');
out2(fid, 'TB25 Stage A 1-phase RSC with switch output capacitance (fixed timing 0.98 f_r, 800 V)\n');
out2(fid, '%-6s %-34s %10s %10s %9s %6s\n', 'design', 'check', 'Simulink', 'reference', 'diff', 'result');
allPass = true;
J = struct();
for d = fieldnames(CS.designs)'
    D = d{1}; ref = CS.designs.(D);
    have = @(s) isfield(R, [D '_' s]);
    if ~(have('nl_0') && have('nl_C') && have('ld_0') && have('ld_C')), continue; end
    p = @(s) R.([D '_' s]).loss_W;
    % T1
    a = p('nl_C') - p('nl_0'); b = ref.formula_W; e = a/b - 1; ok1 = abs(e) <= 0.05;
    out2(fid, '%-6s %-34s %10.2f %10.2f %+8.2f%% %6s\n', D, 'T1 no-load C_oss loss vs 4CV^2f', a, b, 100*e, pf(ok1));
    % T2
    a2 = p('ld_C'); b2 = ref.exact_ld_C_W; e2 = a2/b2 - 1; ok2 = abs(e2) <= 0.05;
    out2(fid, '%-6s %-34s %10.2f %10.2f %+8.2f%% %6s\n', D, 'T2 46.9 A loss with C_oss vs exact', a2, b2, 100*e2, pf(ok2));
    % T3
    a3 = p('ld_0'); b3 = ref.e1_ld_0_W; e3 = a3/b3 - 1; ok3 = abs(e3) <= 0.03;
    out2(fid, '%-6s %-34s %10.2f %10.2f %+8.2f%% %6s\n', D, 'T3 46.9 A loss without C_oss vs E1', a3, b3, 100*e3, pf(ok3));
    % 참고
    a4 = p('ld_C') - p('ld_0'); r4 = a4/ref.formula_W;
    out2(fid, '%-6s %-34s %10.2f %10.2f %8.3f  %6s\n', D, 'info: 46.9 A C_oss loss / formula', a4, ref.formula_W, r4, 'info');
    out2(fid, '%-6s   (%s, f_r %.1f kHz, C_oss %.3f nF per switch, R_ds %.2f mOhm; exact no-load %.2f W)\n', D, ref.label, ...
        ref.fr/1e3, 1e9*ref.Coss, 1e3*ref.Rds, ref.exact_nl_C_W);
    allPass = allPass && ok1 && ok2 && ok3;
    J.(D) = struct('T1', struct('sim', a, 'ref', b, 'err', e, 'pass', ok1), 'T2', struct('sim', a2, 'ref', b2, 'err', e2, 'pass', ok2), ...
                   'T3', struct('sim', a3, 'ref', b3, 'err', e3, 'pass', ok3), 'ld_coss_ratio', r4);
end
S.judge = J; S.verdict = pf(allPass);
out2(fid, 'VERDICT: %s\n', S.verdict);
fclose(fid);
fid = fopen(fullfile(resDir, 'TB25_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);

% ---- 그림: 손실 막대 + 마지막 2주기 공진전류·입력전류 ------------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 1200 700]);
tl = tiledlayout(f, 2, 2, 'TileSpacing', 'compact');
Ds = fieldnames(J)';
nexttile; hold on; grid on;
vals = zeros(numel(Ds), 4);
for i = 1:numel(Ds)
    D = Ds{i};
    vals(i, :) = [R.([D '_nl_C']).loss_W - R.([D '_nl_0']).loss_W, CS.designs.(D).formula_W, ...
                  R.([D '_ld_C']).loss_W - R.([D '_ld_0']).loss_W, CS.designs.(D).model_fix_W];
end
bar(categorical(Ds), vals);
ylabel('W per phase'); legend('no-load C_{oss} loss (Simulink)', '4 C V^2 f_s', '46.9 A C_{oss} loss (Simulink)', ...
    'E1 model fixed loss (4 E_{oss} f_s + gate)', 'Location', 'northeast');
title('C_{oss} loss: circuit vs formula vs original model');
nexttile; hold on; grid on;
for i = 1:numel(Ds)
    D = Ds{i};
    a = R.([D '_ld_0']).loss_W; b = R.([D '_ld_C']).loss_W;
    bar(i - 0.15, a, 0.3, 'FaceColor', [0.5 0.5 0.5]); bar(i + 0.15, b, 0.3, 'FaceColor', [0.77 0.35 0.07]);
    plot(i + 0.15, CS.designs.(D).exact_ld_C_W, 'kd', 'MarkerFaceColor', 'k');
end
set(gca, 'XTick', 1:numel(Ds), 'XTickLabel', Ds); ylabel('W per phase');
legend('46.9 A, no C_{oss}', '46.9 A, with C_{oss}', 'exact (matrix exponential)', 'Location', 'northeast');
title('loss at 46.875 A');
for i = 1:min(2, numel(Ds))
    D = Ds{i};
    nexttile; hold on; grid on;
    w1 = W.([D '_nl_C']); w0 = W.([D '_ld_C']);
    plot(1e6*w0.t, w0.iC, 'LineWidth', 1.2); plot(1e6*w0.t, w0.iin, 'LineWidth', 0.8);
    plot(1e6*w1.t, w1.iin, 'LineWidth', 0.8);
    xlabel('t - t_{end} [\mus]'); ylabel('A');
    legend('i_C (46.9 A)', 'i_{in} (46.9 A)', 'i_{in} (no load)', 'Location', 'northeast');
    title(sprintf('%s: battery current spikes at hard turn-on (C_{oss} %.2f nF)', D, 1e9*CS.designs.(D).Coss));
end
title(tl, 'TB25 Stage A output-capacitance loss under zero-current switching');
exportgraphics(f, fullfile(resDir, 'TB25_coss.png'), 'Resolution', 140);
close(f);
sl_export_png({mdl, [mdl '/StageA_Phase1'], [mdl '/StageA_Phase1/S1_VIN_A']}, resDir);
fprintf('results written to %s\n', resDir);
end

function out2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = pf(ok)
if ok, s = 'PASS'; else, s = 'FAIL'; end
end
