function run_TB11(runList)
%RUN_TB11  TB11: DAB 고장 모드 변조의 첨두 표를 스위칭 반영값으로 바꾼 강등(R2-W460)을 회로에서 판정한다
%           (기준: 검증 코드 E21 P3s = E17 r2_run에 pk_table 'sw', 설계 상한 1.455 × 정격점).
%
%   TB10과 같은 회로·게이트 생성기·지령 블록이다. 다른 것은 지령 블록이 쓰는 첨두 표 TB.eps_pk(데드타임 100 ns·출력용량·
%   역방향 도통을 넣은 스위칭 정상상태, dab_switching.py)와 첨두 상한(1.455 × 정격점 = 1.5배 / 1.03)뿐이다.
%   켬 순서(C)는 지령 블록이 강등 상태에서만 동작하므로 TB10 C와 같다(실행하지 않음, 필요하면 run_TB11(3)).
%
%   run_TB11          % 실행 1–2
%   실행 목록
%     1 A  1008 V, 25 kW, H-브리지 개방 → 전압비 정합 유지(링크 ≈ 89 V, 제동 저항) → 400 V 부하 분리(3 ms) → 링크 붕괴(EPS)
%          → 소프트 바이패스 → 강등
%     2 B   930 V, 25 kW, 같은 고장. 일시 감발(3 ms) → 붕괴(EPS) → 소프트 바이패스 → 강등 → 0.5 ms 뒤 부하 되돌림
%     3 C   930 V, 25 kW, 켬(전류 조향): EPS가 꺼진 정상 순서(새 게이트 생성기의 회귀, TB09 C와 같은 기준)
%
%   판정(시험 전에 고정)
%     고장(A·B): TB09와 같은 회로 한계(순시 경로·필터 ≤ 100 A, |v_s| ≤ 120 V, 링크 ≤ 120 V, 바이패스 ≤ 329 A, 버스 ≥ 260 V,
%                강등 상태 도달, 400 V 부하가 연결된 동안 버스 ≤ 상한)
%                + DAB 링크 쪽 순시 첨두 n·max|i_L|(강등 상태 9–11) ≤ 1.5 × 정격점 첨두(68.7 A) — TB10의 2배 기준을 설계 목표로 좁힘
%     켬(C): TB09와 같음
%     E17 대조(정보): TB09와 같은 항목
%   결과: results/TB11_<사례>_summary.txt·json, _periods.csv, _response.png, TB11_summary.txt·json

here = fileparts(mfilename('fullpath'));
mdl  = 'TB11_R2_FaultMod_SW';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {'A', 'A_1008V_hbopen_25kW'; 'B', 'B_930V_hbopen_25kW'; 'C', 'C_930V_enable_steer_25kW'};
if nargin < 1 || isempty(runList), runList = 1:2; end
load_system(fullfile(here, [mdl '.slx']));
res = {};
for r = runList
    cn = R{r, 2};
    assignin('base', 'TB11_case', cn);
    evalin('base', 'clear TB11_opts');
    run(fullfile(here, 'TB11_init.m'));
    TB = evalin('base', 'TB');
    tic; out = sim(mdl, 'StopTime', num2str(TB.t_end, '%.9g')); wall = toc;
    S = evaluate(out, TB, refDir, cn, resDir, wall);
    S.run = R{r, 1};
    res{end+1} = S; %#ok<AGROW>
    fprintf('%s done (%.0f s): %s\n', R{r, 1}, wall, S.verdict);
end
evalin('base', 'clear TB11_case');
fid = fopen(fullfile(resDir, 'TB11_summary.txt'), 'w');
o2(fid, 'TB11 DAB fault-mode modulation with switching-aware peak table (R2-W460): design limit 1.455x rated, criterion 1.5x rated\n');
o2(fid, '%-4s %-28s %-8s %s\n', 'run', 'case', 'limits', 'failed');
allPass = true;
for k = 1:numel(res)
    S = res{k};
    o2(fid, '%-4s %-28s %-8s %s\n', S.run, S.case, S.verdict, strjoin(S.failed, ', '));
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
o2(fid, 'TB11 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
fclose(fid);
fid = fopen(fullfile(resDir, 'TB11_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true)); fclose(fid);
end

% =======================================================================================================
function S = evaluate(out, TB, refDir, cn, resDir, wall)
t = out.t(:); vb = out.vbus(:); ip = out.ip(:); ih = out.ih(:); vs = out.vs(:); vl = out.vlink(:);
ib = out.ibyp(:); ik = out.ibrk(:); iL = out.iL(:);
vb(1) = vb(2); ip(1) = ip(2); ih(1) = ih(2); vs(1) = vs(2); vl(1) = vl(2); ib(1) = ib(2); ik(1) = ik(2); iL(1) = iL(2);
sup = cols(out.sup, 12);                                   % 5 µs마다(표본 k = 0, 1, …)
T = 5e-6; nper = floor(t(end)/T + 1e-9);
pr = zeros(nper, 14);   % [평균 vb, 평균 ip, 평균 ih, 평균 vl, 평균 vs, max|ip|, max|ih|, max|vs|, max vl, max|ib|, 평균 제동 전력, min vb,
                        %  max|i_L|(DAB 1차), ∫|v_s·i_byp|dt(바이패스 소자 소비 에너지)]
for q = 1:nper
    k = (q-1)*TB.Np + (1:TB.Np);  k = k(k <= numel(t));
    pr(q, :) = [mean(vb(k)), mean(ip(k)), mean(ih(k)), mean(vl(k)), mean(vs(k)), max(abs(ip(k))), max(abs(ih(k))), ...
                max(abs(vs(k))), max(vl(k)), max(abs(ib(k))), mean(vl(k).*ik(k)), min(vb(k)), max(abs(iL(k))), ...
                sum(abs(vs(k).*ib(k)))*TB.dt];
end
tq = (1:nper)'*T;
ts = (0:size(sup, 1)-1)'*T;                                % 상태기계 출력 시각
stq = interp1(ts, sup(:, 11), tq - T, 'previous', 'extrap');   % 각 주기 시작의 상태
shedq = interp1(ts, sup(:, 10), tq - T, 'previous', 'extrap');
% ---- 상태 전이 시각 ---------------------------------------------------------------------------------
names = {'BYPASS', 'PREP', 'OPEN_WAIT', 'WINDOW', 'OFF_RAMP', 'OFF_HOLD', 'ZERO', 'DAB_HOLD', 'DAB_RAMP', 'HB_HOLD', ...
         'HB_COLLAPSE', 'SOFT_BYP', 'DEGRADED', 'FAILSAFE'};
ch = find(diff(sup(:, 11)) ~= 0) + 1;
ev = struct('state', {}, 'ms', {});
for j = 1:numel(ch)
    ev(end+1) = struct('state', names{round(sup(ch(j), 11)) + 1}, 'ms', 1e3*ts(ch(j))); %#ok<AGROW>
end
k1 = find(diff(sup(:, 10)) > 0.5, 1);
if ~isempty(k1), ev(end+1) = struct('state', 'shed_done', 'ms', 1e3*ts(k1 + 1)); end
k2 = find(diff(sup(:, 10)) < -0.5, 1);
if ~isempty(k2), ev(end+1) = struct('state', 'restore', 'ms', 1e3*ts(k2 + 1)); end
final_state = names{round(sup(end, 11)) + 1};
% ---- 부품 스트레스(정보): DAB 순시 첨두, 소프트 투입 ----------------------------------------------------------------
dab_on = ismember(stq, [3 4 5 9 10 11]);
nt = TB.B.n;
dab = struct('sec_peak_A', NaN, 'prim_peak_A', NaN, 'ms', NaN, 'state', '');
if any(dab_on)
    q = find(dab_on); [pk, j] = max(pr(q, 13)); q = q(j);
    dab = struct('sec_peak_A', nt*pk, 'prim_peak_A', pk, 'ms', 1e3*tq(q), 'state', names{round(stq(q)) + 1});
end
soft = struct('entry_ms', NaN, 'vl_V', NaN, 'vs_V', NaN, 'ms', NaN, 'energy_J', NaN, 'path_peak_A', NaN);
k11 = find(sup(:, 11) == 11, 1);
if ~isempty(k11)
    q1 = find(tq - T >= ts(k11) - 1e-12, 1); qs = stq == 11;
    k12 = find(sup(:, 11) == 12, 1); if isempty(k12), k12 = size(sup, 1); end
    soft = struct('entry_ms', 1e3*ts(k11), 'vl_V', pr(q1, 4), 'vs_V', pr(q1, 5), 'ms', 1e3*(ts(k12) - ts(k11)), ...
                  'energy_J', sum(pr(qs, 14)), 'path_peak_A', max(pr(qs | [false; qs(1:end-1)], 6)));
end
% ---- 판정 ----------------------------------------------------------------------------------------------
post = t >= 0.5e-3;
loaded = shedq < 0.5;
L = struct();
if strcmp(TB.event, 'enable')
    L.current_90A = max(abs(ip)) <= 90 && max(abs(ih)) <= 90;
    L.series_90V = max(abs(vs)) <= 90;
    L.link_band = min(pr(:, 4)) >= 90 && max(pr(:, 4)) <= 110;
    L.class_upper = max(pr(:, 1)) <= TB.upper;
    L.bypass_current = max(abs(ib)) <= 329;
    L.final_voltage = abs(mean(pr(tq > tq(end) - 0.2e-3, 1)) - TB.VW) <= 4;
else
    L.current_100A = max(abs(ip(post))) <= 100 && max(abs(ih(post))) <= 100;
    L.series_120V = max(abs(vs(post))) <= 120;
    L.link_120V = max(vl(post)) <= 120;
    L.bypass_current = max(abs(ib(post))) <= 329;
    L.bus_ge_260 = min(pr(tq > 0.5e-3, 12)) >= 260;
    L.degraded_reached = strcmp(final_state, 'DEGRADED');
    L.class_upper_while_400V_loads = max(pr(loaded & tq > 0.5e-3, 1)) <= TB.upper;
    fq = ismember(stq, [9 10 11]) & tq > 0.5e-3;
    L.dab_peak_1p5x_rated = ~any(fq) || nt*max(pr(fq, 13)) <= 1.5*TB.rated_pk;
end
fn = fieldnames(L); lpass = all(cellfun(@(f) L.(f), fn));
failed = fn(~cellfun(@(f) L.(f), fn))';
% ---- E17 대조 ------------------------------------------------------------------------------------------
A = readmatrix(fullfile(refDir, ['TB11_' cn '_avg.csv']));   % [t ip vs vbus ih vlink idab ibyp loads bridge Pbrk], 1 µs
M = jsondecode(fileread(fullfile(refDir, ['TB11_' cn '_metrics.json'])));
qi = ceil(A(:, 1)/T - 1e-9); ok = qi >= 1 & qi <= nper;
rp = nan(nper, 6);   % 기준 주기 평균 [vb ip ih vl vs Pbrk]
colA = [4 2 5 6 3 11];
for j = 1:6, rp(:, j) = accumarray(qi(ok), A(ok, colA(j)), [nper 1], @mean, NaN); end
v = ~isnan(rp(:, 1)) & tq > 0.5e-3;
cmp = {};
add = @(name, a, b, tol) {name, a, b, tol};
cmp(end+1, :) = add('min period-mean v_bus after event [V]', min(pr(v, 1)), min(rp(v, 1)), 3);
cmp(end+1, :) = add('max period-mean v_bus after event [V]', max(pr(v, 1)), max(rp(v, 1)), 3);
cmp(end+1, :) = add('max period-mean i_p [A]', max(pr(v, 2)), max(rp(v, 2)), 5);
cmp(end+1, :) = add('max period-mean i_h [A]', max(abs(pr(v, 3))), max(abs(rp(v, 3))), 5);
cmp(end+1, :) = add('max period-mean v_link [V]', max(pr(v, 4)), max(rp(v, 4)), 2);
cmp(end+1, :) = add('min period-mean v_link [V]', min(pr(v, 4)), min(rp(v, 4)), 2);
cmp(end+1, :) = add('final mean v_bus [V]', mean(pr(tq > tq(end) - 0.2e-3, 1)), mean(rp(tq > tq(end) - 0.2e-3 & ~isnan(rp(:, 1)), 1)), 1);
cmp(end+1, :) = add('brake energy [J]', sum(pr(:, 11))*T, sum(rp(~isnan(rp(:, 6)), 6))*T, NaN);
if isfield(M, 'dab_sec_peak')
    cmp(end+1, :) = add('DAB link-side peak (circuit n|i_L|, E17 SPS) [A]', dab.sec_peak_A, M.dab_sec_peak, NaN);
end
if isfield(M, 'soft_energy_J') && ~isnan(soft.energy_J)
    cmp(end+1, :) = add('soft-bypass device energy [J]', soft.energy_J, M.soft_energy_J, NaN);
end
% 상태 전이 시각(같은 이름의 첫 전이)
if isfield(M, 'events')
    me = M.events;
    for j = 1:numel(ev)
        for q = 1:size(me, 1)
            nm = me{q}; if iscell(nm), st_ = nm{1}; tms = nm{2}; else, st_ = ''; tms = NaN; end
            if strcmp(st_, ev(j).state)
                cmp(end+1, :) = add(['transition ' ev(j).state ' [ms]'], ev(j).ms, tms, 0.05); %#ok<AGROW>
                break
            end
        end
    end
end
% 다이오드 정류 클램프(H-브리지 차단 중, 필터전류 > 5 A)
hbh = ismember(stq, [9 10]) & abs(pr(:, 3)) > 5;
clamp_err = NaN;
if any(hbh)
    clamp_err = mean(pr(hbh, 5) + (pr(hbh, 4) + 2*TB.B.Vf + TB.B.Rh*abs(pr(hbh, 3))).*sign(pr(hbh, 3)));
end
% ---- 요약 ------------------------------------------------------------------------------------------------
fid = fopen(fullfile(resDir, ['TB11_' cn '_summary.txt']), 'w');
o2(fid, 'TB11 case %s (V_bat %.0f V, %.0f kW, event %s), dt %.2f ns, wall %.0f s\n', cn, TB.vbat, TB.P0/1e3, TB.event, 1e9*TB.dt, wall);
o2(fid, '(1) circuit limits:\n');
for k = 1:numel(fn), o2(fid, '    %-30s %s\n', fn{k}, ternary(L.(fn{k}), 'PASS', 'FAIL')); end
o2(fid, '    instantaneous: |i_p| %.1f A, |i_h| %.1f A, |v_s| %.1f V, v_link %.1f-%.1f V, |i_byp| %.1f A; bus(5 us) %.1f-%.1f V (loaded max %.1f V)\n', ...
    max(abs(ip(post))), max(abs(ih(post))), max(abs(vs(post))), min(vl(post)), max(vl(post)), max(abs(ib(post))), ...
    min(pr(:, 12)), max(pr(:, 1)), max(pr(loaded, 1)));
o2(fid, '    diode-clamp check during H-bridge off: mean(v_s + (v_link + 2V_D + R_h|i_h|)·sign(i_h)) = %.3f V\n', clamp_err);
rated_pk = NaN; if isfield(M, 'dab_rated_sec_peak'), rated_pk = M.dab_rated_sec_peak; end
o2(fid, '    DAB stress (info): link-side peak n|i_L| %.1f A (primary %.1f A) at %.3f ms in %s; rated-point link-side peak (E17 SPS) %.1f A\n', ...
    dab.sec_peak_A, dab.prim_peak_A, dab.ms, dab.state, rated_pk);
fq = ismember(stq, [9 10 11]);
if any(fq)
    for sj = [9 10 11]
        q = stq == sj;
        if any(q), o2(fid, '    DAB peak in state %d (%s): n|i_L| %.1f A (design 1.455x %.1f A, limit 1.5x %.1f A)\n', sj, names{sj + 1}, ...
                nt*max(pr(q, 13)), TB.pk_max, 1.5*TB.rated_pk); end
    end
end
o2(fid, '    soft bypass (info): entry %.3f ms (v_link %.2f V, v_s %.2f V), duration %.3f ms, device energy %.4f J, path instantaneous peak %.1f A\n', ...
    soft.entry_ms, soft.vl_V, soft.vs_V, soft.ms, soft.energy_J, soft.path_peak_A);
o2(fid, '(2) comparison with E17 (info):\n');
o2(fid, '    %-44s %11s %11s %9s %9s\n', 'metric', 'Simscape', 'E17', 'diff', 'result');
for k = 1:size(cmp, 1)
    a = cmp{k, 2}; b = cmp{k, 3}; tol = cmp{k, 4};
    if isnan(tol), r = 'info'; else, r = ternary(abs(a - b) <= tol, 'ok', 'over'); end
    o2(fid, '    %-44s %11.5g %11.5g %+9.3g %9s\n', cmp{k, 1}, a, b, a - b, r);
end
o2(fid, '    final state: %s\n', final_state);
fclose(fid);
S = struct('case', cn, 'event', TB.event, 'limits', L, 'verdict', ternary(lpass, 'PASS', 'FAIL'), 'failed', {failed}, ...
    'transitions', ev, 'final_state', final_state, 'clamp_err_V', clamp_err, 'dab', dab, 'soft', soft, ...
    'peaks', struct('ip_A', max(abs(ip(post))), 'ih_A', max(abs(ih(post))), 'vs_V', max(abs(vs(post))), 'vlink_max_V', max(vl(post)), ...
                    'vlink_min_V', min(vl(post)), 'ibyp_A', max(abs(ib(post))), 'bus_min_V', min(pr(:, 12)), 'bus_max_V', max(pr(:, 1)), ...
                    'bus_max_loaded_V', max(pr(loaded, 1)), 'brake_J', sum(pr(:, 11))*T), ...
    'wall_s', wall, 'dt_ns', 1e9*TB.dt, 'date', char(datetime('now')));
S.compare = cell2struct(cmp, {'metric', 'simscape', 'e17', 'tol'}, 2);
fid = fopen(fullfile(resDir, ['TB11_' cn '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
writematrix([tq pr stq shedq], fullfile(resDir, ['TB11_' cn '_periods.csv']));
% ---- 그림 ------------------------------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 1000 900]);
tl = tiledlayout(f, 4, 1, 'TileSpacing', 'compact');
ms_ = 1e3*tq; mr = 1e3*A(:, 1);
nexttile; hold on; grid on; plot(ms_, pr(:, 1), 'LineWidth', 1.4); plot(mr, A(:, 4), '--', 'LineWidth', 1.1);
yline(TB.upper, 'r:'); yline(TB.VA, ':'); ylabel('v_{bus} [V]'); legend('Simscape (5 \mus mean)', 'E17 model', 'Location', 'best');
title('bus voltage (dotted: B_{470} limit and V_A)');
nexttile; hold on; grid on; plot(ms_, pr(:, 2), 'LineWidth', 1.3); plot(mr, A(:, 2), '--');
plot(ms_, pr(:, 3), 'LineWidth', 1.1); plot(mr, A(:, 5), '--'); plot(ms_, sign(pr(:, 10)).*pr(:, 10), 'LineWidth', 1.0);
dpk = nt*pr(:, 13); dpk(~dab_on) = NaN; plot(ms_, dpk, ':', 'LineWidth', 1.0);
ylabel('[A]'); legend('i_p', 'i_p E17', 'i_h', 'i_h E17', 'max|i_{byp}| per period', 'DAB link-side peak n|i_L|', 'Location', 'best');
title('currents (5 \mus means; peaks per period)');
nexttile; hold on; grid on; plot(ms_, pr(:, 4), 'LineWidth', 1.3); plot(mr, A(:, 6), '--');
plot(ms_, -pr(:, 5), 'LineWidth', 1.1); plot(mr, -A(:, 3), '--');
ylabel('[V]'); legend('v_{link}', 'v_{link} E17', '-v_s', '-v_s E17', 'Location', 'best'); title('link and series voltage');
nexttile; hold on; grid on;
yyaxis left; stairs(1e3*ts, sup(:, 11), 'LineWidth', 1.2); ylabel('state'); ylim([-0.5 13.5]);
yyaxis right; plot(ms_, pr(:, 11)/1e3, 'LineWidth', 1.0); ylabel('brake power [kW]');
xlabel('t [ms]'); title('state (0 bypass, 1 prep, 2 open, 3 window, 6 zero, 7 DAB hold, 8 DAB ramp, 9 HB hold, 10 collapse, 11 soft bypass, 12 degraded)');
title(tl, sprintf('TB11 %s', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB11_' cn '_response.png']), 'Resolution', 140); close(f);
fprintf('VERDICT %s: %s\n', cn, S.verdict);
end

function a = cols(a, m)
if ndims(a) == 3, a = reshape(a, size(a, 1)*size(a, 2), [])'; end
if size(a, 2) ~= m, a = a'; end
end

function o2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
