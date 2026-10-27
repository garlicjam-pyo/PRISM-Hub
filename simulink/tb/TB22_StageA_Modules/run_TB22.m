function run_TB22(runList)
%RUN_TB22  TB22(Stage A 4모듈 경부하 운전)을 사례별로 관리기 켬·전부 켬 두 번 실행하고 판정한다.
%
%   run_TB22          % 사례 1–4(검증 코드 E28의 과도 사례 MA·MB·MC·MF, 공칭 부품값)
%   기준: 검증 코드 E28(model_stage_a 모듈 관리기 mgr·위상 셰딩·버스·데드타임 소멸 처리·방향 반전 처리), ref/make_ref_TB22.py
%   사례(시험 전에 고정, E28과 같음)
%     1 MA  540 V, 버스 정전력 부하 5 → 25 → 5 kW(0.5·1.5 ms 계단): 모듈 1 → 2(바로) → 1(1 ms 지속 뒤)
%     2 MB  800 V, 버스 2 → 36 → 2 kW 램프(각 1 ms): 문턱을 천천히 지남(반복 전환 확인)
%     3 MC  800 V, 버스 15 kW, 0.4 ms 충전 요청 → 0.5 ms부터 충전기 0 → 375 A(100 µs) → 1.3 ms부터 0(100 µs), 1.45 ms 요청 끝
%     4 MF  800 V, MC와 같으나 충전 요청 없음(사전 기동이 빠진 경우: 관리기가 전류를 보고 모듈을 더함)
%   판정(E28과 같음, 0.3 ms 이후)
%     (T1) 모든 턴오프: |i_off| ≤ max(5 % × 그 반주기 첨두, 1.0 A)
%     (T2) 위상 첨두 ≤ P_rated(공칭 정격 충전점 375 A·4모듈의 위상 첨두, E28 rated)
%     (T3) V_A 최저·최고가 같은 회로의 전부 켬 실행(모듈 4개, 위상 셰딩 없음)과 1.0 V 안
%     (T4) 끝 동작 모듈 수가 기대값, 모듈 추가·줄임 횟수가 상한 이하, 멈추던 모듈의 취소 0
%   정보(허용폭 표시): E28과 모듈 수 전환 시각 ±0.02 ms, 위상 첨두 ±10 %, V_A 최저·최고 ±0.3 V
%   결과: results/TB22_<사례>_summary.txt·json, _response.png, TB22_summary.txt·json

here = fileparts(mfilename('fullpath'));
mdl  = 'TB22_StageA_Modules';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if evalin('base', 'exist(''TB22_tend'', ''var'')'), resDir = fullfile(here, 'results', 'smoke'); end
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {'MA_540V_bus_5_25_5kW', 'MB_800V_bus_ramp_2_36_2kW', 'MC_800V_charge_prestart', 'MF_800V_charge_no_prestart'};
if nargin < 1 || isempty(runList), runList = 1:4; end
load_system(fullfile(here, [mdl '.slx']));
res = {};
for r = runList
    cn = R{r};
    assignin('base', 'TB22_case', cn);
    O = struct();
    for refFlag = [0 1]
        assignin('base', 'TB22_ref', refFlag);
        run(fullfile(here, 'TB22_init.m'));
        TB = evalin('base', 'TB');
        tic; out = sim(mdl, 'StopTime', num2str(TB.t_end, '%.9g')); wall = toc;
        O.(sprintf('r%d', refFlag)) = extract(out, TB); O.(sprintf('w%d', refFlag)) = wall;
        clear out
    end
    assignin('base', 'TB22_ref', 0);
    run(fullfile(here, 'TB22_init.m'));                     % 관리기 켬 파라미터로 되돌림(판정 값)
    TB = evalin('base', 'TB');
    S = evaluate(O, TB, refDir, cn, resDir);
    res{end+1} = S; %#ok<AGROW>
    fprintf('%s done (%.0f + %.0f s): %s\n', cn, O.w0, O.w1, S.verdict);
end
evalin('base', 'clear TB22_case TB22_ref');
fid = fopen(fullfile(resDir, 'TB22_summary.txt'), 'w');
o2(fid, 'TB22 Stage A 4 modules (module manager + per-module phase shedding + reversal handling), R2 bus, reference E28\n');
o2(fid, '%-28s %-6s %-9s %-9s %-15s %-15s %-14s %s\n', 'case', 'result', 'peak[A]', 'all-on', 'vA[V]', 'vA all-on', 'modules', 'failed');
allPass = true;
for k = 1:numel(res)
    S = res{k};
    o2(fid, '%-28s %-6s %-9.1f %-9.1f %-7.2f-%-7.2f %-7.2f-%-7.2f +%d/-%d end %d %s\n', S.case, S.verdict, S.phase_peak, S.phase_peak_ref, ...
        S.vA(1), S.vA(2), S.vA_ref(1), S.vA_ref(2), S.n_add, S.n_rem, S.n_end, strjoin(S.failed, ', '));
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
o2(fid, 'TB22 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
fclose(fid);
fid = fopen(fullfile(resDir, 'TB22_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true)); fclose(fid);
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
% 반주기별 턴오프 [위상 시각 턴오프전류 반주기첨두](턴오프 전류 = 마지막 도통 표본, E1·E24·E28과 같은 정의)
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

function S = evaluate(O, TB, refDir, cn, resDir)
X = O.r0; B = O.r1; t0 = TB.t0;
to = turnoffs(X, t0);
lim = max(0.05*to(:, 4), TB.i_abs);
bad = abs(to(:, 3)) > lim;
w = X.tA >= t0; wb = B.tA >= t0; w4 = X.t4 >= t0; w4b = B.t4 >= t0;
pk = max(max(abs(X.i(w, :)))); pkb = max(max(abs(B.i(wb, :))));
vA = [min(X.vA(w4)) max(X.vA(w4))]; vAb = [min(B.vA(w4b)) max(B.vA(w4b))];
d = find(diff(X.nact) ~= 0);
E = [1e3*X.t4(d + 1), X.nact(d + 1)];                          % 모듈 수 변화 [시각 [ms], 새 동작 수]
n_add = sum(X.nact(d + 1) > X.nact(d)); n_rem = sum(X.nact(d + 1) < X.nact(d));
n_end = X.nact(end); n_cancel = X.mcancel(end);
L = struct();
L.T1_turnoff = ~any(bad);
L.T2_phase_peak = pk <= TB.P_rated;
L.T3_vA_vs_allon = abs(vA(1) - vAb(1)) <= TB.dv_tol && abs(vA(2) - vAb(2)) <= TB.dv_tol;
L.T4_modules = n_end == TB.n_end && n_add <= TB.add_max && n_rem <= TB.rem_max && n_cancel == 0;
fn = fieldnames(L); pass = all(cellfun(@(f) L.(f), fn));
failed = fn(~cellfun(@(f) L.(f), fn))';
% ---- E28 대조(정보) ---------------------------------------------------------------------------------
M = jsondecode(fileread(fullfile(refDir, ['TB22_' cn '_metrics.json'])));
Z = readmatrix(fullfile(refDir, ['TB22_' cn '_ref.csv']));     % t vA vbus iw iAout nact If vA_allon vbus_allon(약 1 µs)
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
cmp(end+1, :) = add('phase peak [A]', pk, M.phase_peak, 0.1*M.phase_peak);
cmp(end+1, :) = add('phase peak, all on [A]', pkb, M.phase_peak_ref, 0.1*M.phase_peak_ref);
cmp(end+1, :) = add('V_A min [V]', vA(1), M.vA(1), 0.3);
cmp(end+1, :) = add('V_A max [V]', vA(2), M.vA(2), 0.3);
cmp(end+1, :) = add('max turn-off current [A]', max(abs(to(:, 3))), M.ioff_max, NaN);
% ---- 요약 --------------------------------------------------------------------------------------------
fid = fopen(fullfile(resDir, ['TB22_' cn '_summary.txt']), 'w');
o2(fid, 'TB22 case %s (V_bat %.0f V), dt %.2f ns, wall %.0f s (manager) + %.0f s (all on)\n', cn, TB.vbat, 1e9*TB.dt, O.w0, O.w1);
o2(fid, '(1) criteria (t >= %.1f ms):\n', 1e3*t0);
for k = 1:numel(fn), o2(fid, '    %-20s %s\n', fn{k}, ternary(L.(fn{k}), 'PASS', 'FAIL')); end
o2(fid, '    turn-offs %d, violations %d (worst |i_off| %.2f A); phase peak %.1f A (all on %.1f A, P_rated %.1f A)\n', ...
    size(to, 1), sum(bad), max(abs(to(:, 3))), pk, pkb, TB.P_rated);
o2(fid, '    V_A %.3f-%.3f V (all on %.3f-%.3f V); module changes: %s\n', vA(1), vA(2), vAb(1), vAb(2), mat2str(round(E, 4)));
o2(fid, '    added %d, removed %d, end %d, stop-cancel %d (limits +%d/-%d, end %d)\n', n_add, n_rem, n_end, n_cancel, ...
    TB.add_max, TB.rem_max, TB.n_end);
o2(fid, '(2) comparison with E28 (info):\n');
o2(fid, '    %-36s %11s %11s %9s %9s\n', 'metric', 'Simscape', 'E28', 'diff', 'result');
for k = 1:size(cmp, 1)
    a = cmp{k, 2}; b = cmp{k, 3}; tol = cmp{k, 4};
    if isnan(tol), rr = 'info'; elseif isnan(a) && isnan(b), rr = 'ok'; else, rr = ternary(abs(a - b) <= tol, 'ok', 'over'); end
    o2(fid, '    %-36s %11.5g %11.5g %+9.3g %9s\n', cmp{k, 1}, a, b, a - b, rr);
end
fclose(fid);
S = struct('case', cn, 'verdict', ternary(pass, 'PASS', 'FAIL'), 'failed', {failed}, 'limits', L, ...
    'n_turnoff', size(to, 1), 'n_bad', sum(bad), 'ioff_max', max(abs(to(:, 3))), 'phase_peak', pk, 'phase_peak_ref', pkb, ...
    'vA', vA, 'vA_ref', vAb, 'events_ms', E, 'n_add', n_add, 'n_rem', n_rem, 'n_end', n_end, 'n_cancel', n_cancel, ...
    'wall_s', [O.w0 O.w1], 'dt_ns', 1e9*TB.dt, 'date', char(datetime('now')));
S.compare = cell2struct(cmp, {'metric', 'simscape', 'e28', 'tol'}, 2);
fid = fopen(fullfile(resDir, ['TB22_' cn '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
% ---- 그림 ------------------------------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [50 50 1100 900]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
cl = lines(4);
for p = 1:8
    plot(ax, 1e3*X.tA(1:8:end), X.i(1:8:end, p), 'Color', cl(ceil(p/2), :), 'LineWidth', 0.3);
end
yline(ax, [-TB.P_rated TB.P_rated], 'k:');
yyaxis(ax, 'right'); stairs(ax, 1e3*X.t4(1:100:end), X.nact(1:100:end), 'k', 'LineWidth', 1.3); ylim(ax, [0 4.5]);
ylabel(ax, '동작 모듈 수');
yyaxis(ax, 'left'); ylabel(ax, '위상 공진전류 [A](색 = 모듈)');
title(ax, sprintf('위상 전류와 동작 모듈 수(위상 첨두 %.1f A, 전부 켬 %.1f A, 점선 P_{rated} %.1f A)', pk, pkb, TB.P_rated));
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
n1 = round(1e-6/(X.t4(2) - X.t4(1)));
mv = @(x) movmean(x, n1);
plot(ax, 1e3*X.t4, mv(X.vA), 'b', 'LineWidth', 1.1); plot(ax, 1e3*B.t4, mv(B.vA), 'c'); plot(ax, 1e3*Z(:, 1), Z(:, 2), 'r--');
ylabel(ax, 'v_A [V](1 µs 평균)'); legend(ax, '관리기(회로)', '전부 켬(회로)', 'E28 관리기', 'Location', 'best'); title(ax, 'V_A 노드');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
n10 = round(10e-6/(X.t4(2) - X.t4(1)));
plot(ax, 1e3*X.t4, movmean(X.iAo, n10), 'b', 'LineWidth', 1.1); plot(ax, 1e3*Z(:, 1), movmean(Z(:, 5), 10), 'r--');
plot(ax, 1e3*X.t4(1:100:end), X.If(1:100:end), 'g'); plot(ax, 1e3*X.t4(1:100:end), 100*X.chg(1:100:end), 'm');
ylabel(ax, '[A]'); xlabel(ax, '시간 [ms]');
legend(ax, 'Stage A 출력(회로, 10 µs 평균)', 'E28(10 µs 평균)', '게이트 필터 전류 If', '충전 요청 × 100', 'Location', 'best');
title(ax, 'Stage A 전체 출력전류');
title(tl, sprintf('TB22 %s', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB22_' cn '_response.png']), 'Resolution', 130); close(f);
fprintf('VERDICT %s: %s\n', cn, S.verdict);
end

function o2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
