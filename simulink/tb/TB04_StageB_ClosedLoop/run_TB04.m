function run_TB04(caseList, opts)
%RUN_TB04  TB04 폐루프 사례를 실행하고 검증 모델(E12 스위칭 ODE)과 Tier-1 기준으로 판정한다.
%
%   run_TB04                     % 두 사례 모두
%   run_TB04({'A_640V_15to25kW'})
%   run_TB04(caseList, struct('dt', 2.5e-9))   % 적분 간격(= 게이트 시간 분해능)을 바꿔 실행. 결과 파일 이름에 _dt2.5ns
%   run_TB04(caseList, struct('dt', 2.5e-9, 'Coss_d', 20e-12))   % 소자 출력용량(DAB C_oss_d, H-브리지 C_oss_h) 민감도
%
%   판정(사례마다)
%     (1) Tier-1(Simscape 회로 자체): 5 µs 주기 평균 버스전압 400±8 V, 마지막 1 ms 주기 평균 리플 ≤ 0.1 V,
%         경로·필터 순시 전류 ≤ 98 A, 링크전류 주기 평균 ≤ 80 A·링크전력 ≤ 8 kW, 링크전압 90–110 V, |v_s| ≤ 90 V
%     (2) 검증 모델과 일치: 계단 전 정상(0.8–1.0 ms)과 끝(3.8–4.0 ms) 평균 — 버스 0.2 V, 경로·필터 1 A,
%         계단 뒤 최저 버스전압 0.5 V, 최대 경로·필터 순시 전류 max(2 A, 3 %), 주기 평균 버스전압 궤적 RMS 0.2 V
%         링크전압·링크전류의 일치는 사례 A(SPS 영역)에서 판정(링크 0.5 V, 링크전류 1.5 A + 3 %),
%         사례 B(DAB 저전류 구간)는 정보로 기록한다(TB03: 데드타임 영역 전달 특성이 C_oss에 민감)
%   결과: results/TB04_<사례>_summary.txt·json, TB04_<사례>_response.png, TB04_<사례>_step_zoom.png, 회로도 그림

if nargin < 1 || isempty(caseList), caseList = {'A_640V_15to25kW', 'B_788V_0to10kW'}; end
if nargin < 2, opts = struct(); end
tag = '';                                           % 결과 파일 이름에 붙일 변경 사항 표시
if isfield(opts, 'dt') && abs(opts.dt - 5e-9) > 1e-12, tag = [tag sprintf('_dt%gns', 1e9*opts.dt)]; end
if isfield(opts, 'Coss_d'), tag = [tag sprintf('_Cossd%gpF', 1e12*opts.Coss_d)]; end
if isfield(opts, 'Coss_h'), tag = [tag sprintf('_Cossh%gpF', 1e12*opts.Coss_h)]; end
if isempty(fieldnames(opts))
    evalin('base', 'clear TB04_opts');
else
    assignin('base', 'TB04_opts', opts);            % TB04_init이 읽는다(dt는 prism_hub_params, C_oss는 TB.B)
end
here = fileparts(mfilename('fullpath'));
mdl  = 'TB04_StageB_ClosedLoop';
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
load_system(fullfile(here, [mdl '.slx']));
allPass = true;
for c = 1:numel(caseList)
    cn = caseList{c};
    assignin('base', 'TB04_case', cn);
    run(fullfile(here, 'TB04_init.m'));
    tic; out = sim(mdl); wall = toc;
    S = evaluate(out, TB, here, cn, resDir, wall, tag);
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
evalin('base', 'clear TB04_case TB04_opts');
if ~isempty(tag), fprintf('TB04%s overall: %s\n', tag, ternary(allPass, 'PASS', 'FAIL')); return; end
sl_export_png({mdl, [mdl '/StageB_Regulator'], [mdl '/StageB_Regulator/HBridge'], [mdl '/Controller_StageB'], [mdl '/Gate_StageB']}, resDir);
fprintf('TB04 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
end

% =========================================================================================
function S = evaluate(out, TB, here, cn, resDir, wall, tag)
fnm = [cn tag];                                     % 결과 파일 이름(기준값 파일은 cn으로 읽는다)
t = out.t(:); vb = out.vbus(:); ip = out.ip(:); ih = out.ih(:); vs = out.vs(:); vl = out.vlink(:); il = out.ilink(:);
dg = cols(out.dg, 6); uc = cols(out.uc, 2);
% Simscape 첫 출력 표본(t = 0)은 초기화 중의 값(물리량 아님)이므로 판정에서는 다음 표본 값으로 바꾼다
% (모델 안의 제어기·게이트·부하·손실 모델은 시작 표본 보호 블록으로 같은 처리를 한다)
vb(1) = vb(2); ip(1) = ip(2); ih(1) = ih(2); vs(1) = vs(2); vl(1) = vl(2); il(1) = il(2);
T = 5e-6; nper = floor(t(end)/T + 1e-9);
% 주기 통계: [평균 v_bus, 평균 i_p, 평균 i_h, 평균 v_link, 평균 링크전류, 평균 링크전력, max i_h, min i_h, max|i_p|, min v_bus, max v_bus, max|v_s|]
pr = zeros(nper, 12);
for q = 1:nper
    k = (q-1)*TB.Np + (1:TB.Np);  k = k(k <= numel(t));
    pr(q, :) = [mean(vb(k)), mean(ip(k)), mean(ih(k)), mean(vl(k)), mean(il(k)), mean(vl(k).*il(k)), ...
                max(ih(k)), min(ih(k)), max(abs(ip(k))), min(vb(k)), max(vb(k)), max(abs(vs(k)))];
end
tq = (1:nper)'*T;                                   % 주기 끝 시각(검증 모델 rec와 같은 시간축)
R = readmatrix(fullfile(here, 'ref', ['TB04_' cn '_rec.csv']));   % [t_end, rec 25열]
n = min(nper, size(R, 1)); pr = pr(1:n, :); tq = tq(1:n); R = R(1:n, :);
py = struct('vb', R(:, 2), 'ip', R(:, 3), 'ih', R(:, 4), 'vl', R(:, 5), 'il', R(:, 6), 'pl', R(:, 7), ...
    'ihmax', R(:, 8), 'ihmin', R(:, 9), 'ipabs', R(:, 10), 'vbmin', R(:, 11), 'vbmax', R(:, 12), 'rho', R(:, 23), 'eps', R(:, 24));

pre = tq > 0.8e-3 & tq <= 1e-3; post = tq > TB.t_step; fin = tq > 3.8e-3; last1 = tq > tq(end) - 1e-3;
isA = startsWith(cn, 'A');
% ---- (1) Tier-1 ----------------------------------------------------------------------------
T1 = struct();
T1.vbus_window = all(abs(pr(:, 1) - 400) <= 8);
T1.ripple_last1ms = max(pr(last1, 1)) - min(pr(last1, 1)) <= 0.1;
T1.path_current = max(pr(:, 9)) <= 98 && max(max(abs(pr(:, 7:8)))) <= 98;
T1.link_current = max(abs(pr(:, 5))) <= 80 && max(abs(pr(:, 6))) <= 8000;
T1.link_voltage = all(pr(:, 4) >= 90 & pr(:, 4) <= 110);
T1.series_voltage = max(pr(:, 12)) <= 90;
t1pass = all(cellfun(@(f) T1.(f), fieldnames(T1)));
% ---- (2) 검증 모델과 일치 ---------------------------------------------------------------------
cmp = {};   % {이름, Simscape, 검증 모델, 허용, 판정 사용 여부}
add = @(name, a, b, tol, use) {name, a, b, tol, use};
cmp(end+1, :) = add('pre-step mean v_bus [V]',  mean(pr(pre, 1)), mean(py.vb(pre)), 0.2, true);
cmp(end+1, :) = add('pre-step mean i_p [A]',    mean(pr(pre, 2)), mean(py.ip(pre)), 1.0, true);
cmp(end+1, :) = add('pre-step mean i_h [A]',    mean(pr(pre, 3)), mean(py.ih(pre)), 1.0, true);
cmp(end+1, :) = add('pre-step mean v_link [V]', mean(pr(pre, 4)), mean(py.vl(pre)), 0.5, isA);
Ilp = mean(py.il(pre));
cmp(end+1, :) = add('pre-step mean link current [A]', mean(pr(pre, 5)), Ilp, 1.5 + 0.03*abs(Ilp), isA);
cmp(end+1, :) = add('min v_bus after step [V]', min(pr(post, 10)), min(py.vbmin(post)), 0.5, true);
pk = max(py.ipabs(post));
cmp(end+1, :) = add('max |i_p| after step [A]', max(pr(post, 9)), pk, max(2, 0.03*pk), true);
pk = max(py.ihmax(post));
cmp(end+1, :) = add('max i_h after step [A]',   max(pr(post, 7)), pk, max(2, 0.03*pk), true);
rmsVb = sqrt(mean((pr(post, 1) - py.vb(post)).^2));
cmp(end+1, :) = add('rms diff of period-mean v_bus after step [V]', rmsVb, 0, 0.2, true);
cmp(end+1, :) = add('final mean v_bus [V]',     mean(pr(fin, 1)), mean(py.vb(fin)), 0.2, true);
cmp(end+1, :) = add('final mean i_p [A]',       mean(pr(fin, 2)), mean(py.ip(fin)), 1.0, true);
cmp(end+1, :) = add('final mean v_link [V]',    mean(pr(fin, 4)), mean(py.vl(fin)), 0.5, isA);
Ilf = mean(py.il(fin));
cmp(end+1, :) = add('final mean link current [A]', mean(pr(fin, 5)), Ilf, 1.5 + 0.03*abs(Ilf), isA);
% 제어기 추정값(정보): 계단 전 ρ̂, 끝 ε̂
kq = @(tt) min(numel(dg(:, 1)), max(1, round(tt/T)));
cmp(end+1, :) = add('rho_hat at 1.0 ms (info)', dg(kq(1e-3), 4), py.rho(round(1e-3/T)), NaN, false);
cmp(end+1, :) = add('eps_hat at 4.0 ms [A] (info)', dg(end, 5), py.eps(end), NaN, false);

agree = true;
fid = fopen(fullfile(resDir, ['TB04_' fnm '_summary.txt']), 'w');
o2(fid, 'TB04 Stage B closed loop, case %s (V_bat %.0f V, %.0f -> %.0f kW at %.1f ms), dt %.2f ns, wall %.0f s\n', ...
    cn, TB.vbat, TB.P0/1e3, TB.P1/1e3, 1e3*TB.t_step, 1e9*TB.dt, wall);
o2(fid, '(1) Tier-1 on the Simscape circuit:\n');
fn = fieldnames(T1);
o2(fid, '    v_bus period mean %.2f-%.2f V, last-1ms ripple %.3f V, max |i_p| %.2f A, i_h %.2f/%.2f A, link %.2f A / %.0f W, v_link %.2f-%.2f V, max |v_s| %.1f V\n', ...
    min(pr(:, 1)), max(pr(:, 1)), max(pr(last1, 1)) - min(pr(last1, 1)), max(pr(:, 9)), max(pr(:, 7)), min(pr(:, 8)), ...
    max(abs(pr(:, 5))), max(abs(pr(:, 6))), min(pr(:, 4)), max(pr(:, 4)), max(pr(:, 12)));
for k = 1:numel(fn), o2(fid, '    %-16s %s\n', fn{k}, ternary(T1.(fn{k}), 'PASS', 'FAIL')); end
o2(fid, '(2) agreement with the verification model (E12 switching ODE):\n');
o2(fid, '    %-46s %11s %11s %9s %7s\n', 'metric', 'Simscape', 'model', 'diff', 'result');
for k = 1:size(cmp, 1)
    a = cmp{k, 2}; b = cmp{k, 3}; tol = cmp{k, 4}; use = cmp{k, 5};
    d = a - b; ok = abs(d) <= tol;
    if isnan(tol), r = 'info'; elseif ~use, r = ternary(ok, 'info(ok)', 'info'); else, r = ternary(ok, 'PASS', 'FAIL'); agree = agree && ok; end
    o2(fid, '    %-46s %11.4g %11.4g %+9.3g %7s\n', cmp{k, 1}, a, b, d, r);
end
S = struct('case', cn, 'tier1', T1, 'tier1_pass', t1pass, 'agreement_pass', agree, ...
    'verdict', ternary(t1pass && agree, 'PASS', 'FAIL'), 'wall_s', wall, 'model', TB.name, 'dt_ns', 1e9*TB.dt, ...
    'ripple_last1ms_V', max(pr(last1, 1)) - min(pr(last1, 1)), ...
    'date', char(datetime('now')), 'matlab', version);
S.compare = cell2struct(cmp, {'metric', 'simscape', 'model', 'tol', 'judged'}, 2);
o2(fid, 'VERDICT %s: %s\n', cn, S.verdict);
fclose(fid);
fid = fopen(fullfile(resDir, ['TB04_' fnm '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
writematrix([tq pr dg(1:min(n, size(dg, 1)), :)], fullfile(resDir, ['TB04_' fnm '_periods.csv']));

% ---- 그림 1: 전체 응답(주기 평균, Simscape vs 검증 모델) ------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 1000 900]);
tl = tiledlayout(f, 5, 1, 'TileSpacing', 'compact');
ms = 1e3*tq;
nexttile; hold on; grid on; plot(ms, pr(:, 1), 'LineWidth', 1.4); plot(ms, py.vb, '--', 'LineWidth', 1.2);
yline([392 408], ':'); ylabel('v_{bus} [V]'); legend('Simscape', 'verification model', 'Location', 'southeast');
title('bus voltage (5 \mus period mean)');
nexttile; hold on; grid on; plot(ms, pr(:, 2), 'LineWidth', 1.4); plot(ms, py.ip, '--', 'LineWidth', 1.2);
plot(ms, pr(:, 3), 'LineWidth', 1.2); plot(ms, py.ih, '--', 'LineWidth', 1.0);
ylabel('[A]'); legend('i_p Simscape', 'i_p model', 'i_h Simscape', 'i_h model', 'Location', 'southeast');
title('path and filter current (period mean)');
nexttile; hold on; grid on; plot(ms, pr(:, 4), 'LineWidth', 1.4); plot(ms, py.vl, '--', 'LineWidth', 1.2);
ylabel('v_{link} [V]'); title('floating link voltage');
nexttile; hold on; grid on; plot(ms, pr(:, 5), 'LineWidth', 1.4); plot(ms, py.il, '--', 'LineWidth', 1.2);
ylabel('[A]'); title('DAB link current (period mean)');
nexttile; hold on; grid on;
td = (1:size(dg, 1))'*T;
yyaxis left; plot(1e3*td, dg(:, 4), 'LineWidth', 1.3); plot(ms, py.rho, '--'); ylabel('rho-hat');
yyaxis right; plot(1e3*td, dg(:, 5), 'LineWidth', 1.3); plot(ms, py.eps, '--'); ylabel('eps-hat [A]');
xlabel('t [ms]'); title('DAB current-ratio and low-current estimates (solid Simscape, dashed model)');
title(tl, sprintf('TB04 %s: V_{bat} %.0f V, %.0f \\rightarrow %.0f kW at %.0f ms', strrep(fnm, '_', ' '), TB.vbat, TB.P0/1e3, TB.P1/1e3, 1e3*TB.t_step));
exportgraphics(f, fullfile(resDir, ['TB04_' fnm '_response.png']), 'Resolution', 150); close(f);

% ---- 그림 2: 계단 전후 순시 파형 ----------------------------------------------------------------
W = readmatrix(fullfile(here, 'ref', ['TB04_' cn '_wave.csv']));   % [t ip vs vbus ih vlink iL sA-sB s1]
z = t >= 0.95e-3 & t <= 1.25e-3; z(z) = mod(0:nnz(z)-1, 4)' == 0;
f = figure('Visible', 'off', 'Position', [100 100 1000 760]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
nexttile; hold on; grid on; plot(1e6*t(z), vb(z), 'LineWidth', 1.1); plot(1e6*W(:, 1), W(:, 4), '--', 'LineWidth', 1.0);
ylabel('v_{bus} [V]'); legend('Simscape', 'verification model', 'Location', 'southeast');
nexttile; hold on; grid on; plot(1e6*t(z), ip(z), 'LineWidth', 1.1); plot(1e6*W(:, 1), W(:, 2), '--', 'LineWidth', 1.0);
plot(1e6*t(z), ih(z), 'LineWidth', 0.8); plot(1e6*W(:, 1), W(:, 5), '--', 'LineWidth', 0.8);
ylabel('[A]'); legend('i_p Simscape', 'i_p model', 'i_h Simscape', 'i_h model', 'Location', 'southeast');
nexttile; hold on; grid on; plot(1e6*t(z), vl(z), 'LineWidth', 1.1); plot(1e6*W(:, 1), W(:, 6), '--', 'LineWidth', 1.0);
ylabel('v_{link} [V]'); xlabel('t [\mus]');
title(tl, sprintf('TB04 %s: instantaneous waveforms around the load step', strrep(fnm, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB04_' fnm '_step_zoom.png']), 'Resolution', 150); close(f);
fprintf('case %s done\n', fnm);
end

function a = cols(a, m)
% To Workspace 배열을 N×m으로 정리(열 벡터 신호는 m×1×N으로 저장된다)
if ndims(a) == 3, a = reshape(a, size(a, 1)*size(a, 2), [])'; end
if size(a, 2) ~= m, a = a'; end
end

function o2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
