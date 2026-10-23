function run_TB08(runList)
%RUN_TB08  TB08: R2 창 조정 Stage B 모듈(R2-W460, 1000 V급 팩·B_470 부품)을 회로에서 판정한다.
%
%   run_TB08          % 실행 1–5(판정)
%   run_TB08(6)       % 사례 A를 게이트 격자 0.625 ns로(정상상태 리플 정보, TB04B 요구 격자)
%
%   실행 목록
%     1 A  1008 V, 1 → 25 kW(Tier-2, 최대 배터리 전압)       기준 E12 스위칭 ODE(같은 사례 재계산)
%     2 B   930 V, 15 → 25 kW(Tier-1, 창 하단, DAB 저전류)   기준 E12 스위칭 ODE
%     3 C   910 V, 25 kW 끔: 기준 460 V → V_A 1 ms 램프, 1 ms 유지, 영벡터 0.2 ms, 바이패스     기준 E19 모드 평균모델
%     4 D  1008 V, 25 kW DAB 고장: DAB 정지 + 기준 → V_A 1 ms 램프, 영벡터 0.2 ms, 바이패스   기준 E19 모드 평균모델
%     5 E   930 V, 25 kW 켬: 바이패스 + 영벡터 → 0.5 ms 바이패스 열림 → 0.7 ms 제어 시작 + 기준 V_A → 460 V 1 ms 램프
%     6 A, 0.625 ns(정보)
%
%   판정(시험 전에 고정)
%     A·B(창 조정 Tier, 스위칭 기준)
%       회로: Tier-1(B) 5 µs 주기 평균 버스 460 ± 8 V, 순시 경로·필터 ≤ 98 A
%             Tier-2(A) 계단 뒤 주기 평균 버스 [444, 470] V, 마지막 0.2 ms 평균 460 ± 4 V, 순시 경로·필터 ≤ 100 A
%             공통: 링크전류 주기 평균 ≤ 80 A, 링크전력 주기 평균 ≤ DAB 정격 4 kW, 링크 90–110 V, |v_s| ≤ 90 V,
%                   순시 버스 ≤ 470 V(B_470). 마지막 1 ms 리플은 정보(2.5 ns 격자, 요구 격자 0.625 ns는 TB04B)
%       검증 모델 일치: TB04와 같은 항목·허용폭(버스 0.2 V, 전류 1 A, 최저 버스 0.5 V, 최대 전류 max(2 A, 3 %),
%             버스 궤적 RMS 0.2 V). 링크전압·링크전류 일치는 A(SPS 영역)에서 판정, B(저전류)는 정보
%     C·D·E(모드 전환·고장, 평균모델 기준)
%       회로 한계(판정, E19와 같은 기준)
%         C: 순시 경로·필터 ≤ 90 A, |v_s| ≤ 90 V, 링크 주기 평균 90–110 V, 순시 버스 260–470 V, 바이패스 직전 |v_s| ≤ 2 V
%         D: 순시 경로·필터 ≤ 100 A, |v_s| ≤ 90 V, 링크 주기 평균 ≤ 120 V, 순시 버스 ≥ 260 V
%            (강등 뒤 버스 = V_A가 B_470을 넘는 것은 구조적 결과로 기록 → 400 V 부하 분리 필요)
%         E: 순시 경로·필터 ≤ 90 A, |v_s| ≤ 90 V, 링크 주기 평균 90–110 V, 순시 버스 ≤ 470 V, 마지막 0.2 ms 평균 460 ± 4 V
%       평균모델 대조(정보): 주기 평균 버스 최저·최고 ±2 V, 최대 경로전류 ±3 A, 링크 최대 ±1 V, 바이패스 직전 v_s ±1 V,
%         최종 버스 ±1 V, 버스 궤적 RMS 1 V. 평균모델에는 스위칭 리플·DAB 추정기 동특성이 없으므로 판정에 쓰지 않는다
%   결과: results/TB08_<사례><꼬리>_summary.txt·json, _periods.csv, _response.png, TB08_summary.txt·json

here = fileparts(mfilename('fullpath'));
mdl  = 'TB08_R2_WindowModule';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end

R = {  % 이름, 사례, dt, 판정 사용, 결과 파일 꼬리
    'A', 'A_1008V_1to25kW',       2.5e-9,   true,  '';
    'B', 'B_930V_15to25kW',       2.5e-9,   true,  '';
    'C', 'C_910V_disable_25kW',   2.5e-9,   true,  '';
    'D', 'D_1008V_dabfault_25kW', 2.5e-9,   true,  '';
    'E', 'E_930V_enable_25kW',    2.5e-9,   true,  '';
    'A_0.625ns', 'A_1008V_1to25kW', 0.625e-9, false, '_0.625ns'};
if nargin < 1 || isempty(runList), runList = 1:5; end

load_system(fullfile(here, [mdl '.slx']));
res = {};
for r = runList
    cn = R{r, 2};
    assignin('base', 'TB08_case', cn);
    assignin('base', 'TB08_opts', struct('dt', R{r, 3}));
    run(fullfile(here, 'TB08_init.m'));
    TB = evalin('base', 'TB');
    tic; out = sim(mdl); wall = toc;
    if strcmp(TB.kind, 'switching')
        S = eval_switching(out, TB, refDir, cn, resDir, wall, R{r, 5});
    else
        S = eval_modes(out, TB, refDir, cn, resDir, wall, R{r, 5});
    end
    S.run = R{r, 1}; S.judged = R{r, 4};
    res{end+1} = S; %#ok<AGROW>
    fprintf('%s done (%.0f s): %s\n', R{r, 1}, wall, S.verdict);
end
evalin('base', 'clear TB08_case TB08_opts');

% ---- 요약 --------------------------------------------------------------------------------------------
sumName = 'TB08_summary';
if ~isequal(runList, 1:5), sumName = sprintf('TB08_summary_runs%s', sprintf('_%d', runList)); end
fid = fopen(fullfile(resDir, [sumName '.txt']), 'w');
o2(fid, 'TB08 R2 window-regulation Stage B module (R2-W460: V_W 460 V, DAB 4.6:1 4 kW, bypass 3.3 mOhm)\n');
o2(fid, '%-10s %-24s %-10s %-8s %-10s %s\n', 'run', 'case', 'kind', 'limits', 'agreement', 'verdict');
allPass = true;
for k = 1:numel(res)
    S = res{k};
    o2(fid, '%-10s %-24s %-10s %-8s %-10s %s%s\n', S.run, S.case, S.kind, ternary(S.limits_pass, 'PASS', 'FAIL'), ...
        S.agreement_text, S.verdict, ternary(S.judged, '', ' (info)'));
    if S.judged, allPass = allPass && strcmp(S.verdict, 'PASS'); end
end
o2(fid, 'TB08 overall (judged runs): %s\n', ternary(allPass, 'PASS', 'FAIL'));
fclose(fid);
fid = fopen(fullfile(resDir, [sumName '.json']), 'w'); fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true)); fclose(fid);
end

% =======================================================================================================
function [pr, tq, d] = period_stats(out, TB)
% 5 µs 주기 통계: [평균 v_bus, 평균 i_p, 평균 i_h, 평균 v_link, 평균 링크전류, 평균 링크전력, max i_h, min i_h,
%                  max|i_p|, min v_bus, max v_bus, max|v_s|, 평균 v_s, max|i_byp|, max|i_h|]
t = out.t(:); vb = out.vbus(:); ip = out.ip(:); ih = out.ih(:); vs = out.vs(:); vl = out.vlink(:); il = out.ilink(:);
ib = out.ibyp(:);
% Simscape 첫 출력 표본(t = 0)은 초기화 중의 값이므로 다음 표본 값으로 바꾼다
vb(1) = vb(2); ip(1) = ip(2); ih(1) = ih(2); vs(1) = vs(2); vl(1) = vl(2); il(1) = il(2); ib(1) = ib(2);
T = 5e-6; nper = floor(t(end)/T + 1e-9);
pr = zeros(nper, 15);
for q = 1:nper
    k = (q-1)*TB.Np + (1:TB.Np);  k = k(k <= numel(t));
    pr(q, :) = [mean(vb(k)), mean(ip(k)), mean(ih(k)), mean(vl(k)), mean(il(k)), mean(vl(k).*il(k)), ...
                max(ih(k)), min(ih(k)), max(abs(ip(k))), min(vb(k)), max(vb(k)), max(abs(vs(k))), mean(vs(k)), ...
                max(abs(ib(k))), max(abs(ih(k)))];
end
tq = (1:nper)'*T;
d = struct('dg', cols(out.dg, 6), 'seq', cols(out.seq, 3), 't', t, 'vb', vb, 'ip', ip, 'ih', ih, 'vs', vs, 'vl', vl, 'ib', ib);
end

% =======================================================================================================
function S = eval_switching(out, TB, refDir, cn, resDir, wall, tag)
% 창 조정 Tier 사례: 회로 한계 + 검증 모델(E12 스위칭 ODE) 일치. TB04 판정(lib/tb_stageB_evaluate.m)을 V_W로 일반화
fnm = [cn tag];
[pr, tq, d] = period_stats(out, TB);
Rr = readmatrix(fullfile(refDir, ['TB08_' cn '_rec.csv']));
n = min(size(pr, 1), size(Rr, 1)); pr = pr(1:n, :); tq = tq(1:n); Rr = Rr(1:n, :);
py = struct('vb', Rr(:, 2), 'ip', Rr(:, 3), 'ih', Rr(:, 4), 'vl', Rr(:, 5), 'il', Rr(:, 6), 'pl', Rr(:, 7), ...
    'ihmax', Rr(:, 8), 'ihmin', Rr(:, 9), 'ipabs', Rr(:, 10), 'vbmin', Rr(:, 11), 'vbmax', Rr(:, 12), 'rho', Rr(:, 23), 'eps', Rr(:, 24));
pre = tq > 0.8e-3 & tq <= 1e-3; post = tq > TB.t_step; fin = tq > tq(end) - 0.2e-3; last1 = tq > tq(end) - 1e-3;
tier2 = abs(TB.P1 - TB.P0) > 20000;
isA = startsWith(cn, 'A');
L = struct();
if tier2
    L.bus_band_after_step = all(pr(post, 1) >= TB.VW - 16 & pr(post, 1) <= min(TB.VW + 16, TB.upper));
    L.final_voltage = abs(mean(pr(fin, 1)) - TB.VW) <= 4;
    ilim = 100;
else
    L.bus_window = all(abs(pr(:, 1) - TB.VW) <= 8);
    ilim = 98;
end
L.path_filter_current = max(pr(:, 9)) <= ilim && max(pr(:, 15)) <= ilim;
L.link_current = max(abs(pr(:, 5))) <= 80;
L.link_power_rating = max(abs(pr(:, 6))) <= TB.Prated;
L.link_voltage = all(pr(:, 4) >= 90 & pr(:, 4) <= 110);
L.series_voltage = max(pr(:, 12)) <= 90;
L.class_upper = max(pr(:, 11)) <= TB.upper;
lpass = all(cellfun(@(f) L.(f), fieldnames(L)));
ripple = max(pr(last1, 1)) - min(pr(last1, 1));

cmp = {};
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
cmp(end+1, :) = add('rms diff of period-mean v_bus after step [V]', sqrt(mean((pr(post, 1) - py.vb(post)).^2)), 0, 0.2, true);
cmp(end+1, :) = add('final mean v_bus [V]',     mean(pr(fin, 1)), mean(py.vb(fin)), 0.2, true);
cmp(end+1, :) = add('final mean i_p [A]',       mean(pr(fin, 2)), mean(py.ip(fin)), 1.0, true);
cmp(end+1, :) = add('final mean v_link [V]',    mean(pr(fin, 4)), mean(py.vl(fin)), 0.5, isA);
Ilf = mean(py.il(fin));
cmp(end+1, :) = add('final mean link current [A]', mean(pr(fin, 5)), Ilf, 1.5 + 0.03*abs(Ilf), isA);
cmp(end+1, :) = add('max |link power| (period mean) [W]', max(abs(pr(:, 6))), max(abs(py.pl)), NaN, false);
cmp(end+1, :) = add('rho_hat at 1.0 ms (info)', d.dg(min(end, round(1e-3/5e-6)), 4), py.rho(round(1e-3/5e-6)), NaN, false);
[agree, txt] = write_summary(resDir, fnm, TB, wall, L, cmp, ripple, ...
    sprintf('Tier-%d window regulation, V_bat %.0f V, %.0f -> %.0f kW at %.1f ms, dt %.3f ns', 1 + tier2, TB.vbat, TB.P0/1e3, TB.P1/1e3, 1e3*TB.t_step, 1e9*TB.dt), ...
    'E12 switching ODE (same case recomputed with the R2-W460 design values)');
S = pack(cn, fnm, resDir, TB, wall, L, lpass, agree, txt, cmp, ripple);
writematrix([tq pr d.dg(1:min(n, size(d.dg, 1)), :)], fullfile(resDir, ['TB08_' fnm '_periods.csv']));
fig_response(resDir, fnm, TB, tq, pr, d, struct('t', tq, 'vb', py.vb, 'ip', py.ip, 'ih', py.ih, 'vl', py.vl, 'vs', nan(size(tq))), ...
    'E12 switching ODE');
end

% =======================================================================================================
function S = eval_modes(out, TB, refDir, cn, resDir, wall, tag)
% 모드 전환·고장 강등: 회로 한계(판정) + 평균모델(E19) 대조(정보)
fnm = [cn tag];
[pr, tq, d] = period_stats(out, TB);
A = readmatrix(fullfile(refDir, ['TB08_' cn '_avg.csv']));      % [t ip vs vbus ih vlink idab mode], 1 µs 간격
T = 5e-6; n = numel(tq);
qi = ceil(A(:, 1)/T - 1e-9); ok = qi >= 1 & qi <= n;
rp = nan(n, 5);                                                    % 기준 주기 평균 [v_bus i_p i_h v_link v_s]
for j = 1:5
    col = [4 2 5 6 3];
    rp(:, j) = accumarray(qi(ok), A(ok, col(j)), [n 1], @mean, NaN);
end
sq = TB.seq_prm;  t_byp = sq(7); t_zero = sq(6); t_ramp1 = sq(2); t_open = sq(8); t_ctrl = sq(9);
c = cn(1);
L = struct();
switch c
    case 'C'
        ilim = 90;
        L.link_band = all(pr(:, 4) >= 90 & pr(:, 4) <= 110);
        L.bus_window = min(pr(:, 10)) >= 260 && max(pr(:, 11)) <= TB.upper;
    case 'D'
        ilim = 100;
        L.link_max_120V = max(pr(:, 4)) <= 120;
        L.bus_min_260V = min(pr(:, 10)) >= 260;
    otherwise   % E
        ilim = 90;
        L.link_band = all(pr(:, 4) >= 90 & pr(:, 4) <= 110);
        L.bus_upper = max(pr(:, 11)) <= TB.upper;
        L.final_voltage = abs(mean(pr(tq > tq(end) - 0.2e-3, 1)) - TB.VW) <= 4;
end
L.path_current = max(pr(:, 9)) <= ilim;
L.filter_current = max(pr(:, 15)) <= ilim;
L.series_voltage = max(pr(:, 12)) <= 90;
kb = find(tq <= t_byp + 1e-12, 1, 'last');                         % 바이패스 직전 주기
vs_byp = NaN; vs_byp_ref = NaN;
if t_byp < 1
    vs_byp = pr(kb, 13); vs_byp_ref = rp(kb, 5);
    if c == 'C', L.series_at_bypass_2V = abs(vs_byp) <= 2; end
end
lpass = all(cellfun(@(f) L.(f), fieldnames(L)));
% 정보: 바이패스 투입 직후 20 µs의 바이패스 전류 최대, 강등 뒤 버스, 켬 사례의 바이패스 열림 과도
info = struct();
if t_byp < 1
    w = d.t >= t_byp & d.t <= t_byp + 20e-6;
    info.bypass_current_peak_20us_A = max(abs(d.ib(w)));
    info.bus_after_bypass_V = mean(pr(tq > tq(end) - 0.2e-3, 1));
end
if t_open < 1
    w = d.t >= t_open & d.t <= t_ctrl;
    info.vs_excursion_at_open_V = max(abs(d.vs(w)));
    info.ih_range_at_open_A = [min(d.ih(w)) max(d.ih(w))];
    info.bus_before_ctrl_V = mean(pr(tq > t_ctrl - 0.1e-3 & tq <= t_ctrl, 1));
    out_band = find(tq > t_ramp1 & abs(pr(:, 1) - TB.VW) > 4, 1, 'last');
    if isempty(out_band), info.settle_after_ramp_ms = 0; else, info.settle_after_ramp_ms = 1e3*(tq(out_band) - t_ramp1); end
end
v = ~isnan(rp(:, 1));
cmp = {};
add = @(name, a, b, tol, use) {name, a, b, tol, use};
cmp(end+1, :) = add('min period-mean v_bus [V]', min(pr(v, 1)), min(rp(v, 1)), 2, false);
cmp(end+1, :) = add('max period-mean v_bus [V]', max(pr(v, 1)), max(rp(v, 1)), 2, false);
cmp(end+1, :) = add('max period-mean i_p [A]',   max(pr(v, 2)), max(rp(v, 2)), 3, false);
cmp(end+1, :) = add('max period-mean v_link [V]', max(pr(v, 4)), max(rp(v, 4)), 1, false);
cmp(end+1, :) = add('final mean v_bus [V]', mean(pr(tq > tq(end) - 0.2e-3, 1)), mean(rp(tq > tq(end) - 0.2e-3 & v, 1)), 1, false);
cmp(end+1, :) = add('rms diff of period-mean v_bus [V]', sqrt(mean((pr(v, 1) - rp(v, 1)).^2)), 0, 1, false);
if t_byp < 1
    cmp(end+1, :) = add('period-mean v_s just before bypass [V]', vs_byp, vs_byp_ref, 1, false);
end
fi = fieldnames(info);
for k = 1:numel(fi)
    x = info.(fi{k});
    cmp(end+1, :) = add([strrep(fi{k}, '_', ' ') ' (info)'], x(end), NaN, NaN, false); %#ok<AGROW>
end
ttl = sprintf('%s, V_bat %.0f V, %.0f kW, dt %.3f ns', mode_title(c), TB.vbat, TB.P0/1e3, 1e9*TB.dt);
[agree, txt] = write_summary(resDir, fnm, TB, wall, L, cmp, NaN, ttl, 'E19 mode averaged model (diode state held per step)');
S = pack(cn, fnm, resDir, TB, wall, L, lpass, agree, txt, cmp, NaN);
S.info = info;
writematrix([tq pr d.seq(1:min(n, size(d.seq, 1)), :)], fullfile(resDir, ['TB08_' fnm '_periods.csv']));
fig_response(resDir, fnm, TB, tq, pr, d, struct('t', tq, 'vb', rp(:, 1), 'ip', rp(:, 2), 'ih', rp(:, 3), 'vl', rp(:, 4), 'vs', rp(:, 5)), ...
    'E19 averaged model');
end

function s = mode_title(c)
switch c
    case 'C', s = 'disable: ramp to V_A, zero vector, bypass';
    case 'D', s = 'DAB fault: 1 ms ramp to V_A, zero vector, bypass';
    otherwise, s = 'enable: bypass + zero vector, bypass opens, control with ramp to V_W';
end
end

% =======================================================================================================
function [agree, txt] = write_summary(resDir, fnm, TB, wall, L, cmp, ripple, ttl, refName)
agree = true; anyJudged = false;
fid = fopen(fullfile(resDir, ['TB08_' fnm '_summary.txt']), 'w');
o2(fid, 'TB08 case %s: %s, wall %.0f s\n', fnm, ttl, wall);
o2(fid, '(1) circuit limits on the Simscape model:\n');
fn = fieldnames(L);
for k = 1:numel(fn), o2(fid, '    %-24s %s\n', fn{k}, ternary(L.(fn{k}), 'PASS', 'FAIL')); end
if ~isnan(ripple), o2(fid, '    last-1ms ripple of period-mean v_bus %.3f V (info; 0.1 V criterion applies at the 0.625 ns gate grid, TB04B)\n', ripple); end
o2(fid, '(2) comparison with %s:\n', refName);
o2(fid, '    %-46s %11s %11s %9s %9s\n', 'metric', 'Simscape', 'reference', 'diff', 'result');
for k = 1:size(cmp, 1)
    a = cmp{k, 2}; b = cmp{k, 3}; tol = cmp{k, 4}; use = cmp{k, 5};
    dd = a - b; okk = abs(dd) <= tol;
    if isnan(tol), r = 'info';
    elseif ~use, r = ternary(okk, 'info(ok)', 'info(over)');
    else, r = ternary(okk, 'PASS', 'FAIL'); agree = agree && okk; anyJudged = true;
    end
    o2(fid, '    %-46s %11.5g %11.5g %+9.3g %9s\n', cmp{k, 1}, a, b, dd, r);
end
if anyJudged, txt = ternary(agree, 'PASS', 'FAIL'); else, txt = 'info'; end
fclose(fid);
end

function S = pack(cn, fnm, resDir, TB, wall, L, lpass, agree, txt, cmp, ripple)
S = struct('case', cn, 'kind', TB.kind, 'limits', L, 'limits_pass', lpass, 'agreement_pass', agree, ...
    'agreement_text', txt, 'verdict', ternary(lpass && agree, 'PASS', 'FAIL'), 'ripple_last1ms_V', ripple, ...
    'wall_s', wall, 'dt_ns', 1e9*TB.dt, 'date', char(datetime('now')), 'matlab', version);
S.compare = cell2struct(cmp, {'metric', 'simscape', 'reference', 'tol', 'judged'}, 2);
fid = fopen(fullfile(resDir, ['TB08_' fnm '_summary.json']), 'w');
fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
fprintf('VERDICT %s: %s\n', fnm, S.verdict);
end

% =======================================================================================================
function fig_response(resDir, fnm, TB, tq, pr, d, ref, refName)
f = figure('Visible', 'off', 'Position', [100 100 1000 980]);
tl = tiledlayout(f, 5, 1, 'TileSpacing', 'compact');
ms = 1e3*tq;
nexttile; hold on; grid on; plot(ms, pr(:, 1), 'LineWidth', 1.4); plot(1e3*ref.t, ref.vb, '--', 'LineWidth', 1.2);
yline(TB.VW, ':'); yline(TB.upper, 'r:'); ylabel('v_{bus} [V]'); legend('Simscape', refName, 'Location', 'best');
title('bus voltage (5 \mus period mean), dotted: V_W 460 V and B_{470} limit');
nexttile; hold on; grid on; plot(ms, pr(:, 2), 'LineWidth', 1.4); plot(1e3*ref.t, ref.ip, '--', 'LineWidth', 1.2);
plot(ms, pr(:, 3), 'LineWidth', 1.1); plot(1e3*ref.t, ref.ih, '--', 'LineWidth', 1.0);
ylabel('[A]'); legend('i_p Simscape', 'i_p ref', 'i_h Simscape', 'i_h ref', 'Location', 'best'); title('path and filter current (period mean)');
nexttile; hold on; grid on; plot(ms, pr(:, 13), 'LineWidth', 1.4); plot(1e3*ref.t, ref.vs, '--', 'LineWidth', 1.2);
ylabel('v_s [V]'); title('series-port voltage (period mean)');
nexttile; hold on; grid on; plot(ms, pr(:, 4), 'LineWidth', 1.4); plot(1e3*ref.t, ref.vl, '--', 'LineWidth', 1.2);
ylabel('v_{link} [V]'); title('floating link voltage');
nexttile; hold on; grid on;
ts = (0:size(d.seq, 1)-1)'*5e-6;
yyaxis left; stairs(1e3*ts, d.seq(:, 3), 'LineWidth', 1.3); ylim([-0.5 4.5]); ylabel('mode');
yyaxis right; plot(ms, pr(:, 14), 'LineWidth', 1.1); ylabel('max |i_{byp}| per period [A]');
xlim([0 ms(end)]); xlabel('t [ms]'); title('mode (0 control, 1 DAB fault, 2 zero vector, 3 bypass, 4 bypass + zero vector) and bypass current');
title(tl, sprintf('TB08 %s', strrep(fnm, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB08_' fnm '_response.png']), 'Resolution', 140); close(f);
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
