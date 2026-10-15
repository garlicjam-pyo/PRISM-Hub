function run_TB04B(runList, sumName)
%RUN_TB04B  TB04B: DAB 소자 출력용량을 후보 소자 값으로 넣고 TB04 기준으로 다시 판정한다(25 kW 정상 리플 쟁점).
%
%   run_TB04B            % 아래 실행 목록 전부
%   run_TB04B([1 2])     % 일부만
%   run_TB04B(6:8, 'TB04B_resolution_summary')   % 게이트 시간 분해능 점검(요약 파일 이름을 따로 준다)
%
%   실행 목록(사례, 적분 간격, DAB 1차/2차 C_oss)
%     1 device_A     : A 640 V 15 → 25 kW, 2.5 ns, 335 / 1371 pF  (후보 소자 C_o(tr))         ← 판정
%     2 device_B     : B 788 V 0 → 10 kW,  2.5 ns, 335 / 1371 pF                                ← 판정
%     3 er_A         : A, 2.5 ns, 207 / 1053 pF  (에너지 등가 C_o(er): 같은 소자의 다른 선형 등가, 민감도 정보)
%     4 tb04equiv_A  : A, 2.5 ns, 100 / 100 pF   (TB04와 같은 값: 모델이 TB04를 재현하는지, 직류 편류 비교 기준)
%     5 device_A_5ns : A, 5 ns,   335 / 1371 pF  (통합 모델 TB06의 적분 간격, 정보)
%     6 device_A_1.25ns, 7 device_B_1.25ns, 8 device_A_0.625ns, 9 device_B_0.625ns : 후보 소자 출력용량에서 게이트 시간 분해능을 높인 점검
%       (결과 1·2가 리플 기준을 넘은 원인이 게이트 에지의 시간 양자화인지 확인. 요약은 TB04B_resolution_summary)
%
%   판정(TB04와 같은 기준, lib/tb_stageB_evaluate.m): Tier-1(마지막 1 ms 리플 ≤ 0.1 V 포함) + 검증 모델(E12) 일치.
%   TB04B 결론 = 실행 1·2가 모두 통과하는가.
%   추가 지표(정보): 변압기 직류 편류 = DAB 1차 누설전류 i_L의 주기(5 µs) 평균.
%     마지막 1 ms의 편류 변동폭·RMS, 링크전류 주기 평균 변동폭, 버스 리플과의 상관, 버스 리플의 주된 주파수
%   결과: results/TB04B_<사례><tag>_*(공용 판정 파일), TB04B_coss_summary.txt·json, TB04B_dc_bias.png, 회로도 그림

here = fileparts(mfilename('fullpath'));
mdl  = 'TB04B_StageB_DAB_Coss';
pkgRoot = fileparts(fileparts(here));
refDir = fullfile(pkgRoot, 'tb', 'TB04_StageB_ClosedLoop', 'ref');
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end

R = {  % 이름,          사례,               dt,     C_oss 1차, C_oss 2차, 판정 사용, 결과 파일 꼬리
    'device_A',     'A_640V_15to25kW', 2.5e-9, 335e-12,  1371e-12, true,  '_device';
    'device_B',     'B_788V_0to10kW',  2.5e-9, 335e-12,  1371e-12, true,  '_device';
    'er_A',         'A_640V_15to25kW', 2.5e-9, 207e-12,  1053e-12, false, '_er';
    'tb04equiv_A',  'A_640V_15to25kW', 2.5e-9, 100e-12,  100e-12,  false, '_tb04equiv';
    'device_A_5ns', 'A_640V_15to25kW', 5e-9,   335e-12,  1371e-12, false, '_device_5ns';
    'device_A_1.25ns',  'A_640V_15to25kW', 1.25e-9,  335e-12, 1371e-12, false, '_device_1.25ns';
    'device_B_1.25ns',  'B_788V_0to10kW',  1.25e-9,  335e-12, 1371e-12, false, '_device_1.25ns';
    'device_A_0.625ns', 'A_640V_15to25kW', 0.625e-9, 335e-12, 1371e-12, false, '_device_0.625ns';
    'device_B_0.625ns', 'B_788V_0to10kW',  0.625e-9, 335e-12, 1371e-12, false, '_device_0.625ns'};
if nargin < 1 || isempty(runList), runList = 1:5; end
if nargin < 2 || isempty(sumName), sumName = 'TB04B_coss_summary'; end

load_system(fullfile(here, [mdl '.slx']));
res = struct('name', {}, 'case', {}, 'dt_ns', {}, 'coss_p_pF', {}, 'coss_s_pF', {}, 'judged', {}, ...
    'verdict', {}, 'tier1_pass', {}, 'agreement_pass', {}, 'ripple_V', {}, 'bias_pp_A', {}, 'bias_rms_A', {}, ...
    'link_pp_A', {}, 'ip_pp_A', {}, 'corr_bias_link', {}, 'f_ripple_kHz', {}, 'wall_s', {});
B = {};   % 그림용: {이름, 주기 끝 시각, 직류 편류, 링크전류 평균, 버스 평균}
for r = runList
    nm = R{r, 1}; cn = R{r, 2};
    assignin('base', 'TB04_case', cn);
    assignin('base', 'TB04B_opts', struct('dt', R{r, 3}, 'Coss_dp', R{r, 4}, 'Coss_ds', R{r, 5}));
    run(fullfile(here, 'TB04B_init.m'));
    tic; out = sim(mdl); wall = toc;
    S = tb_stageB_evaluate(out, TB, refDir, cn, resDir, wall, R{r, 7}, 'TB04B');   % 파일: TB04B_<사례><꼬리>_*
    D = dcbias(out, TB);
    res(end+1) = struct('name', nm, 'case', cn, 'dt_ns', 1e9*TB.dt, 'coss_p_pF', 1e12*TB.B.Coss_dp, ...
        'coss_s_pF', 1e12*TB.B.Coss_ds, 'judged', R{r, 6}, 'verdict', S.verdict, 'tier1_pass', S.tier1_pass, ...
        'agreement_pass', S.agreement_pass, 'ripple_V', S.ripple_last1ms_V, 'bias_pp_A', D.bias_pp, ...
        'bias_rms_A', D.bias_rms, 'link_pp_A', D.link_pp, 'ip_pp_A', D.ip_pp, 'corr_bias_link', D.corr, ...
        'f_ripple_kHz', D.f_peak/1e3, 'wall_s', wall); %#ok<AGROW>
    B(end+1, :) = {nm, D.tq, D.bias, D.link, D.vb}; %#ok<AGROW>
    fprintf('%s done (%.0f s)\n', nm, wall);
end
evalin('base', 'clear TB04_case TB04B_opts');

% ---- 요약 --------------------------------------------------------------------------------------------
judged = [res.judged];
pass = all(strcmp({res(judged).verdict}, 'PASS')) && nnz(judged) == 2;
fid = fopen(fullfile(resDir, [sumName '.txt']), 'w');
o2(fid, 'TB04B Stage B closed loop with candidate-device DAB output capacitance (C_o(tr)): 25 kW steady-state ripple question from TB04\n');
o2(fid, '%-16s %-16s %6s %8s %8s %9s %7s %7s %9s %9s %8s %7s %8s %6s %s\n', 'run', 'case', 'dt[ns]', 'Cp[pF]', 'Cs[pF]', ...
    'ripple[V]', 'Tier1', 'agree', 'bias_pp', 'bias_rms', 'link_pp', 'ip_pp', 'corr', 'f[kHz]', 'verdict');
for k = 1:numel(res)
    x = res(k);
    o2(fid, '%-16s %-16s %6.3f %8.0f %8.0f %9.4f %7s %7s %9.3f %9.3f %8.3f %7.3f %8.2f %6.2f %s%s\n', x.name, x.case, x.dt_ns, ...
        x.coss_p_pF, x.coss_s_pF, x.ripple_V, ternary(x.tier1_pass, 'PASS', 'FAIL'), ternary(x.agreement_pass, 'PASS', 'FAIL'), ...
        x.bias_pp_A, x.bias_rms_A, x.link_pp_A, x.ip_pp_A, x.corr_bias_link, x.f_ripple_kHz, x.verdict, ternary(x.judged, '', ' (info)'));
end
o2(fid, 'columns: ripple = last-1ms max-min of 5 us period-mean v_bus (Tier-1 limit 0.1 V); bias = period mean of DAB primary current i_L\n');
o2(fid, '         (transformer DC bias) in the last 1 ms, pp and rms; link_pp / ip_pp = pp of period-mean link / path current;\n');
o2(fid, '         corr = correlation of bias with link-current period mean (last 1 ms); f = dominant frequency of v_bus ripple (1.5-4 ms)\n');
if nnz(judged) == 2
    o2(fid, 'TB04B VERDICT (runs device_A and device_B judged with the TB04 criteria): %s\n', ternary(pass, 'PASS', 'FAIL'));
end
fclose(fid);
fid = fopen(fullfile(resDir, [sumName '.json']), 'w');
fprintf(fid, '%s', jsonencode(struct('runs', res, 'verdict', ternary(pass, 'PASS', 'FAIL'), 'date', char(datetime('now')), ...
    'matlab', version), 'PrettyPrint', true)); fclose(fid);

% ---- 그림: 직류 편류와 링크전류(사례 A, 마지막 2 ms) --------------------------------------------------
iA = find(endsWith(B(:, 1), '_A') | endsWith(B(:, 1), '_5ns'));
if ~isempty(iA) && isequal(runList, 1:5)
    f = figure('Visible', 'off', 'Position', [100 100 1000 760]);
    tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
    lbl = cellfun(@(n) strrep(n, '_', ' '), B(iA, 1), 'UniformOutput', false);
    ax = gobjects(3, 1);
    for p = 1:3
        ax(p) = nexttile; hold on; grid on;
        for j = iA'
            w = B{j, 2} > 2e-3;
            plot(1e3*B{j, 2}(w), B{j, 2 + p}(w), 'LineWidth', 1.1);
        end
    end
    ylabel(ax(1), 'i_L period mean [A]'); title(ax(1), 'transformer DC bias (period mean of DAB primary current)');
    ylabel(ax(2), '[A]'); title(ax(2), 'DAB link current (period mean)');
    ylabel(ax(3), 'v_{bus} [V]'); title(ax(3), 'bus voltage (period mean)'); xlabel(ax(3), 't [ms]');
    legend(ax(1), lbl, 'Location', 'eastoutside'); legend(ax(2), lbl, 'Location', 'eastoutside'); legend(ax(3), lbl, 'Location', 'eastoutside');
    title(tl, 'TB04B case A (640 V, 25 kW after the step): DAB output capacitance and steady-state behaviour');
    exportgraphics(f, fullfile(resDir, 'TB04B_dc_bias.png'), 'Resolution', 150); close(f);
end
if isequal(runList, 1:5)
    sl_export_png({mdl, [mdl '/StageB_Regulator']}, resDir);
end
if nnz(judged) == 2, fprintf('TB04B overall: %s\n', ternary(pass, 'PASS', 'FAIL')); end
end

% ======================================================================================================
function D = dcbias(out, TB)
% 주기(5 µs)별 평균: DAB 1차 누설전류 i_L(변압기 직류 편류), 링크전류, 경로전류, 버스전압
t = out.t(:); iL = out.iL(:); il = out.ilink(:); ip = out.ip(:); vb = out.vbus(:);
iL(1) = iL(2); il(1) = il(2); ip(1) = ip(2); vb(1) = vb(2);      % 첫 표본(초기화 값) 제외
Np = TB.Np; nper = floor(numel(t)/Np);
k = reshape(1:nper*Np, Np, nper);
D.tq = (1:nper)'*Np*TB.dt;
D.bias = mean(iL(k), 1)'; D.link = mean(il(k), 1)'; ipm = mean(ip(k), 1)'; D.vb = mean(vb(k), 1)';
w = D.tq > D.tq(end) - 1e-3;
D.bias_pp = max(D.bias(w)) - min(D.bias(w));
D.bias_rms = sqrt(mean((D.bias(w) - mean(D.bias(w))).^2));
D.link_pp = max(D.link(w)) - min(D.link(w));
D.ip_pp = max(ipm(w)) - min(ipm(w));
c = corrcoef(D.bias(w), D.link(w)); D.corr = c(1, 2);
% 버스 리플의 주된 주파수(계단 뒤 정착 구간 1.5 ms 이후, 평균 제거, 해닝 창)
w2 = D.tq > 1.5e-3; x = D.vb(w2) - mean(D.vb(w2)); n = numel(x);
X = abs(fft(x.*(0.5 - 0.5*cos(2*pi*(0:n-1)'/(n-1)))));       % 해닝 창
fr = (0:n-1)'/(n*Np*TB.dt);
h = 2:floor(n/2); [~, im] = max(X(h)); D.f_peak = fr(h(im));
end

function o2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
