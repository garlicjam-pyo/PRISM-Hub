function run_TB24(runList)
%RUN_TB24  TB24(Stage A 모듈 고장과 모듈 관리기 연동)를 사례별로 실행하고 판정한다.
%
%   run_TB24          % 사례 1–4(검증 코드 E30의 고장 사례 FA·FB·FF·FH, 공칭 부품값)
%   기준: 검증 코드 E30(model_stage_a 모듈 관리기 + mgr_fault, 버스, 데드타임 소멸 처리, 무장 전 부호 없는 영교차 검출),
%         ref/make_ref_TB24.py
%   사례(시험 전에 고정, E30과 같음, 고장 시각 0.5 ms)
%     1 FA  800 V, 버스 15 kW(모듈 1개 동작), 모듈 1 고장 → 모듈 2가 대신
%     2 FB  540 V, 버스 25 kW(모듈 2개), 모듈 1 고장 → 모듈 2 혼자 약 93 A → 모듈 3 추가
%     3 FF  800 V 충전(V_A 노드 −375 A, 충전 요청 계속, 4개 동작), 모듈 1 고장 → 3개가 375 A
%     4 FH  800 V 충전, 모듈 4 고장
%   판정(E30과 같음, 0.3 ms 이후)
%     (F1) 모든 턴오프(고장 모듈의 고장 순간 이후는 뺌): |i_off| ≤ max(5 % × 그 반주기 첨두, 1.0 A)
%     (F2) 위상 첨두(고장 모듈은 고장 전까지만): 주행 ≤ P_rated, 충전 ≤ 1.5 × P_rated(P_rated = 공칭 정격 충전점 첨두, E28 rated)
%     (F3) V_A가 고장 직전 20 µs 평균과 ±10 V 안, 배터리 ≤ 920 V면 ≤ 470 V
%     (F4) 끝 동작 모듈 수 = 기대값(주행 max(1, ⌈|I|/70 A⌉), 충전 3), 고장 모듈 위상이 다시 켜지지 않음,
%          고장 뒤 동작 수 감소는 고장 자체 한 번뿐, 멈추기 취소 0
%   정보(허용폭 표시): E30과 모듈 수 전환 시각 ±0.02 ms, 위상 첨두 ±10 %, V_A 최저·최고 ±0.3 V, 대체 모듈 시작 ±1 µs
%   결과: results/TB24_<사례>_summary.txt·json, _response.png, TB24_summary.txt·json

here = fileparts(mfilename('fullpath'));
mdl  = 'TB24_StageA_ModuleFault';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if evalin('base', 'exist(''TB24_tend'', ''var'')'), resDir = fullfile(here, 'results', 'smoke'); end
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {'FA_800V_drive_15kW_m1', 'FB_540V_drive_25kW_m1', 'FF_800V_charge_m1', 'FH_800V_charge_m4'};
if nargin < 1 || isempty(runList), runList = 1:4; end
load_system(fullfile(here, [mdl '.slx']));
res = {};
for r = runList
    cn = R{r};
    assignin('base', 'TB24_case', cn);
    run(fullfile(here, 'TB24_init.m'));
    TB = evalin('base', 'TB');
    tic; out = sim(mdl, 'StopTime', num2str(TB.t_end, '%.9g')); wall = toc;
    X = extract(out, TB); clear out
    S = evaluate(X, TB, refDir, cn, resDir, wall);
    res{end+1} = S; %#ok<AGROW>
    fprintf('%s done (%.0f s): %s\n', cn, wall, S.verdict);
end
evalin('base', 'clear TB24_case');
fid = fopen(fullfile(resDir, 'TB24_summary.txt'), 'w');
o2(fid, 'TB24 Stage A module fault + module manager (faulted module excluded), R2 bus, reference E30\n');
o2(fid, '%-24s %-6s %-9s %-9s %-24s %-12s %s\n', 'case', 'result', 'peak[A]', 'limit', 'vA pre -> min-max [V]', 'modules', 'failed');
allPass = true;
for k = 1:numel(res)
    S = res{k};
    o2(fid, '%-24s %-6s %-9.1f %-9.1f %-7.2f -> %-7.2f-%-7.2f end %d %s\n', S.case, S.verdict, S.phase_peak, S.pk_limit, ...
        S.vA_pre, S.vA(1), S.vA(2), S.n_end, strjoin(S.failed, ', '));
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
o2(fid, 'TB24 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
fclose(fid);
fid = fopen(fullfile(resDir, 'TB24_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true)); fclose(fid);
end

% =======================================================================================================
function X = extract(out, TB)
X.i = double([out.iA1(:) out.iA2(:) out.iA3(:) out.iA4(:) out.iA5(:) out.iA6(:) out.iA7(:) out.iA8(:)]);
X.s = double([out.st1(:) out.st2(:) out.st3(:) out.st4(:) out.st5(:) out.st6(:) out.st7(:) out.st8(:)]);
X.tA = (0:size(X.i, 1)-1)'*TB.dt;
X.t4 = out.t4(:);
X.vA = double(out.vA(:)); X.vA(1) = X.vA(2);
X.vbus = double(out.vbus(:)); X.vbus(1) = X.vbus(2);
X.iAo = double(out.iAo(:)); X.iAo(1) = X.iAo(2);
X.iVA = double(out.iVA(:)); X.chg = double(out.chg(:));
mg = double(squeeze(out.mgr)); if size(mg, 2) ~= 7, mg = mg.'; end
X.nact = mg(:, 1); X.mm = mg(:, 2:5); X.If = mg(:, 6); X.mcancel = mg(:, 7);
end

function to = turnoffs(X, t0)
% 반주기별 턴오프 [위상 시각 턴오프전류 반주기첨두](턴오프 전류 = 마지막 도통 표본, E1·E24·E28·E30과 같은 정의)
to = zeros(0, 4);
for p = 1:8
    s = X.s(:, p); i = X.i(:, p);
    off = find(s(1:end-1) ~= 0 & s(2:end) == 0);
    on = find(s(1:end-1) == 0 & s(2:end) ~= 0) + 1;
    for j = 1:numel(off)
        o = off(j);
        if X.tA(o) < t0, continue; end
        k0 = on(find(on <= o, 1, 'last'));
        if isempty(k0), continue; end
        to(end+1, :) = [p, X.tA(o), i(o), max(abs(i(k0:o)))]; %#ok<AGROW>
    end
end
end

function S = evaluate(X, TB, refDir, cn, resDir, wall)
t0 = TB.t0; fm = TB.fault_module; fph = [2*fm - 1, 2*fm];
kf = round(TB.t_fault/TB.dt) + 1;                              % 고장 간격(1부터 센 표본 번호)
tf = X.tA(kf);
to = turnoffs(X, t0);
keep = ~(ismember(to(:, 1), fph) & to(:, 2) >= tf - 1.5*TB.dt);  % 고장 모듈의 강제 턴오프(마지막 도통 표본)부터 뺌
to = to(keep, :);
lim = max(0.05*to(:, 4), TB.i_abs);
bad = abs(to(:, 3)) > lim;
w = X.tA >= t0;
pk = 0;
for p = 1:8
    if ismember(p, fph), msk = w & X.tA < tf; else, msk = w; end
    if any(msk), pk = max(pk, max(abs(X.i(msk, p)))); end
end
pre = X.t4 >= TB.t_fault - 20e-6 & X.t4 < TB.t_fault; post = X.t4 >= TB.t_fault;
vpre = mean(X.vA(pre)); vA = [min(X.vA(post)) max(X.vA(post))];
d = find(diff(X.nact) ~= 0);
E = [1e3*X.t4(d + 1), X.nact(d + 1)];
dec = d(X.nact(d + 1) < X.nact(d));
dec_after = dec(abs(X.t4(dec + 1) - TB.t_fault) > 15e-9);     % 고장 순간의 감소는 뺌(10 ns 계측 간격)
restart = any(any(X.s(kf + 1:end, fph) ~= 0));
n_end = X.nact(end); n_cancel = X.mcancel(end);
% 대체 모듈: 고장 직전 한 주기 동안 꺼져 있던 위상이 고장 뒤 처음 켜진 시각
nT = round(1/(150e3)/TB.dt); t_rep = NaN;
for p = setdiff(1:8, fph)
    if ~any(X.s(max(1, kf - nT):kf - 1, p) ~= 0)
        k1 = find(X.s(kf:end, p) ~= 0, 1);
        if ~isempty(k1), t_rep = min([t_rep, (k1 - 1)*TB.dt]); end
    end
end
L = struct();
L.F1_turnoff = ~any(bad);
L.F2_phase_peak = pk <= TB.pk_limit;
L.F3_vA = abs(vA(1) - vpre) <= TB.dv_A && abs(vA(2) - vpre) <= TB.dv_A && (TB.vbat > 920 || vA(2) <= TB.v_b470);
L.F4_modules = n_end == TB.n_end && ~restart && isempty(dec_after) && n_cancel == 0;
fn = fieldnames(L); pass = all(cellfun(@(f) L.(f), fn));
failed = fn(~cellfun(@(f) L.(f), fn))';
% ---- E30 대조(정보) ---------------------------------------------------------------------------------
M = jsondecode(fileread(fullfile(refDir, ['TB24_' cn '_metrics.json'])));
Z = readmatrix(fullfile(refDir, ['TB24_' cn '_ref.csv']));     % t vA vbus iw iAout nact If(약 1 µs)
me = M.events; if iscell(me), me = cell2mat(cellfun(@(c) c(:)', me, 'UniformOutput', false)); end
if isempty(me), me = zeros(0, 2); end
cmp = {};
add = @(name, a, b, tol) {name, a, b, tol};
for k = 1:max(size(E, 1), size(me, 1))
    a = NaN; b = NaN;
    if k <= size(E, 1), a = E(k, 1); end
    if k <= size(me, 1), b = me(k, 1); end
    nm = sprintf('module change %d time [ms]', k);
    if k <= size(E, 1), nm = sprintf('%s (-> %d)', nm, E(k, 2)); end
    cmp(end+1, :) = add(nm, a, b, 0.02); %#ok<AGROW>
end
mrep = NaN; if ~isempty(M.t_rep_us), mrep = M.t_rep_us; end
cmp(end+1, :) = add('replacement start [us]', 1e6*t_rep, mrep, 1.0);
cmp(end+1, :) = add('phase peak [A]', pk, M.phase_peak, 0.1*M.phase_peak);
cmp(end+1, :) = add('V_A before fault [V]', vpre, M.vA_pre, 0.3);
cmp(end+1, :) = add('V_A min after fault [V]', vA(1), M.vA(1), 0.3);
cmp(end+1, :) = add('V_A max after fault [V]', vA(2), M.vA(2), 0.3);
cmp(end+1, :) = add('max turn-off current [A]', max(abs(to(:, 3))), M.ioff_max, NaN);
% ---- 요약 --------------------------------------------------------------------------------------------
fid = fopen(fullfile(resDir, ['TB24_' cn '_summary.txt']), 'w');
o2(fid, 'TB24 case %s (V_bat %.0f V, %s, module %d fault at %.2f ms), dt %.2f ns, wall %.0f s\n', cn, TB.vbat, TB.kind, fm, ...
    1e3*TB.t_fault, 1e9*TB.dt, wall);
o2(fid, '(1) criteria (t >= %.1f ms):\n', 1e3*t0);
for k = 1:numel(fn), o2(fid, '    %-20s %s\n', fn{k}, ternary(L.(fn{k}), 'PASS', 'FAIL')); end
o2(fid, '    turn-offs %d, violations %d (worst |i_off| %.2f A); phase peak %.1f A (limit %.1f A, P_rated %.1f A)\n', ...
    size(to, 1), sum(bad), max(abs(to(:, 3))), pk, TB.pk_limit, TB.P_rated);
o2(fid, '    V_A before %.3f V, after %.3f-%.3f V; module changes: %s; end %d, restart %d, cancel %d, replacement %.2f us\n', ...
    vpre, vA(1), vA(2), mat2str(round(E, 4)), n_end, restart, n_cancel, 1e6*t_rep);
o2(fid, '(2) comparison with E30 (info):\n');
o2(fid, '    %-36s %11s %11s %9s %9s\n', 'metric', 'Simscape', 'E30', 'diff', 'result');
for k = 1:size(cmp, 1)
    a = cmp{k, 2}; b = cmp{k, 3}; tol = cmp{k, 4};
    if isnan(tol), rr = 'info'; elseif isnan(a) && isnan(b), rr = 'ok'; else, rr = ternary(abs(a - b) <= tol, 'ok', 'over'); end
    o2(fid, '    %-36s %11.5g %11.5g %+9.3g %9s\n', cmp{k, 1}, a, b, a - b, rr);
end
fclose(fid);
S = struct('case', cn, 'verdict', ternary(pass, 'PASS', 'FAIL'), 'failed', {failed}, 'limits', L, ...
    'n_turnoff', size(to, 1), 'n_bad', sum(bad), 'ioff_max', max(abs(to(:, 3))), 'phase_peak', pk, 'pk_limit', TB.pk_limit, ...
    'vA_pre', vpre, 'vA', vA, 'events_ms', E, 'n_end', n_end, 'restart', restart, 'n_cancel', n_cancel, 't_rep_us', 1e6*t_rep, ...
    'wall_s', wall, 'dt_ns', 1e9*TB.dt, 'date', char(datetime('now')));
S.compare = cell2struct(cmp, {'metric', 'simscape', 'e30', 'tol'}, 2);
fid = fopen(fullfile(resDir, ['TB24_' cn '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
% ---- 그림 ------------------------------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [50 50 1100 900]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
cl = lines(4);
for p = 1:8
    plot(ax, 1e3*X.tA(1:8:end), X.i(1:8:end, p), 'Color', cl(ceil(p/2), :), 'LineWidth', 0.3);
end
yline(ax, [-TB.pk_limit TB.pk_limit], 'k:'); xline(ax, 1e3*TB.t_fault, 'r--');
yyaxis(ax, 'right'); stairs(ax, 1e3*X.t4(1:100:end), X.nact(1:100:end), 'k', 'LineWidth', 1.3); ylim(ax, [0 4.5]);
ylabel(ax, '동작 모듈 수');
yyaxis(ax, 'left'); ylabel(ax, '위상 공진전류 [A](색 = 모듈)');
title(ax, sprintf('위상 전류와 동작 모듈 수(모듈 %d 고장 %.2f ms, 위상 첨두 %.1f A, 점선 한도 %.1f A)', fm, 1e3*TB.t_fault, pk, TB.pk_limit));
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
n1 = round(1e-6/(X.t4(2) - X.t4(1)));
plot(ax, 1e3*X.t4, movmean(X.vA, n1), 'b', 'LineWidth', 1.1); plot(ax, 1e3*Z(:, 1), Z(:, 2), 'r--');
xline(ax, 1e3*TB.t_fault, 'r--');
ylabel(ax, 'v_A [V](1 µs 평균)'); legend(ax, '회로', 'E30', 'Location', 'best'); title(ax, 'V_A 노드');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
n10 = round(10e-6/(X.t4(2) - X.t4(1)));
plot(ax, 1e3*X.t4, movmean(X.iAo, n10), 'b', 'LineWidth', 1.1); plot(ax, 1e3*Z(:, 1), movmean(Z(:, 5), 10), 'r--');
plot(ax, 1e3*X.t4(1:100:end), X.If(1:100:end), 'g');
ylabel(ax, '[A]'); xlabel(ax, '시간 [ms]');
legend(ax, 'Stage A 출력(회로, 10 µs 평균)', 'E30(10 µs 평균)', '게이트 필터 전류 If', 'Location', 'best');
title(ax, 'Stage A 전체 출력전류');
title(tl, sprintf('TB24 %s', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB24_' cn '_response.png']), 'Resolution', 130); close(f);
fprintf('VERDICT %s: %s\n', cn, S.verdict);
end

function o2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
