function run_TB18(runList)
%RUN_TB18  TB18(Stage A 경부하 위상 셰딩)을 사례별로 셰딩 켬·없음 두 번 실행하고 판정한다.
%
%   run_TB18          % 사례 1–5(검증 코드 E24의 과도 사례 F–J)
%   기준: 검증 코드 E24(model_stage_a 셰딩·버스·데드타임 소멸 처리), ref/make_ref_TB18.py
%   사례(시험 전에 고정, E24와 같음)
%     1 F  1008 V, 버스 정전력 부하 25 → 5 → 25 kW(0.5·1.5 ms 계단): 셰딩 → 복귀
%     2 G   540 V, 13.5 → 2.7 → 13.5 kW
%     3 H  1008 V, 버스 5 kW, 1 ms에 V_A 노드 충전기 0 → 74.4 A 주입(모듈당 충전 램프 요구 0.94 A/µs): 셰딩 상태에서 복귀
%     4 I  1008 V, 버스 20 → 1.5 → 20 kW 램프(각 1 ms): 문턱을 천천히 지남(채터링 확인)
%     5 J  1008 V, 버스 5 kW, 0.5 ms에 V_A 노드 충전기 16 A 주입(모듈 출력 약 −6 A, 역방향 경부하), 1.5 ms에 되돌림
%   판정(E24와 같음, 0.3 ms 이후)
%     (T1) 모든 턴오프: |i_off| ≤ max(5 % × 그 반주기 첨두, 1.0 A)
%     (T2) 위상 첨두 ≤ 76.4 A(위상 정격 첨두)
%     (T3) V_A 최저·최고가 같은 회로의 셰딩 없는 실행과 0.5 V 안
%     (T4) 셰딩·복귀 횟수가 예상과 같고 멈추기 취소가 없음(채터링 없음)
%   정보(허용폭 표시): E24와 셰딩·복귀 시각 ±0.02 ms, 위상 첨두 ±10 %, V_A 최저·최고 ±0.3 V
%   결과: results/TB18_<사례>_summary.txt·json, _response.png, TB18_summary.txt·json

here = fileparts(mfilename('fullpath'));
mdl  = 'TB18_StageA_Shedding';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {'F_1008V_bus_25_5_25kW', 'G_540V_bus_13p5_2p7_13p5kW', 'H_1008V_bus5kW_charger_74A', ...
     'I_1008V_bus_ramp_20_1p5_20kW', 'J_1008V_bus5kW_rev_m16A'};
if nargin < 1 || isempty(runList), runList = 1:5; end
load_system(fullfile(here, [mdl '.slx']));
res = {};
for r = runList
    cn = R{r};
    assignin('base', 'TB18_case', cn);
    O = struct();
    for shedFlag = [1 0]                                    % (TB18_init.m가 이 작업공간에 sh 등을 만들므로 다른 이름)
        assignin('base', 'TB18_shed', shedFlag);
        run(fullfile(here, 'TB18_init.m'));
        TB = evalin('base', 'TB');
        tic; out = sim(mdl, 'StopTime', num2str(TB.t_end, '%.9g')); wall = toc;
        O.(sprintf('s%d', shedFlag)) = extract(out, TB); O.(sprintf('w%d', shedFlag)) = wall;
        clear out
    end
    assignin('base', 'TB18_shed', 1);
    run(fullfile(here, 'TB18_init.m'));                     % 셰딩 켬 파라미터로 되돌림(판정 값)
    TB = evalin('base', 'TB');
    S = evaluate(O, TB, refDir, cn, resDir);
    res{end+1} = S; %#ok<AGROW>
    fprintf('%s done (%.0f + %.0f s): %s\n', cn, O.w1, O.w0, S.verdict);
end
evalin('base', 'clear TB18_case TB18_shed');
fid = fopen(fullfile(resDir, 'TB18_summary.txt'), 'w');
o2(fid, 'TB18 Stage A light-load phase shedding (module 1 + shedding gate + R2 bus), reference E24\n');
o2(fid, '%-30s %-6s %-9s %-9s %-15s %-15s %s\n', 'case', 'result', 'peak[A]', 'noshed', 'vA[V]', 'vA noshed', 'failed');
allPass = true;
for k = 1:numel(res)
    S = res{k};
    o2(fid, '%-30s %-6s %-9.1f %-9.1f %-7.2f-%-7.2f %-7.2f-%-7.2f %s\n', S.case, S.verdict, S.phase_peak, S.phase_peak_noshed, ...
        S.vA(1), S.vA(2), S.vA_noshed(1), S.vA_noshed(2), strjoin(S.failed, ', '));
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
o2(fid, 'TB18 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
fclose(fid);
fid = fopen(fullfile(resDir, 'TB18_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true)); fclose(fid);
end

% =======================================================================================================
function X = extract(out, TB)
X.i = double([out.iA1(:) out.iA2(:)]);
X.s = double([out.st1(:) out.st2(:)]);
X.tA = (0:size(X.i, 1)-1)'*TB.dt;
X.t4 = out.t4(:);
X.vA = double(out.vA(:)); X.vA(1) = X.vA(2);
X.vbus = double(out.vbus(:)); X.vbus(1) = X.vbus(2);
X.iAo = double(out.iAo(:)); X.iAo(1) = X.iAo(2);
sh = double(squeeze(out.shed)); if size(sh, 2) ~= 2, sh = sh.'; end
X.sm = sh(:, 1); X.If = sh(:, 2);
end

function [to, ev] = turnoffs(X, t0)
% 반주기별 턴오프 [위상 시각 턴오프전류 반주기첨두](턴오프 전류 = 마지막 도통 표본, E1·E24와 같은 정의)
to = zeros(0, 4);
for p = 1:2
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
ev = [];
end

function E = events(X)
% 셰딩 모드 변화 [시각 [ms], 새 모드]
d = find(diff(X.sm) ~= 0);
E = [1e3*X.t4(d + 1), X.sm(d + 1)];
end

function S = evaluate(O, TB, refDir, cn, resDir)
X = O.s1; B = O.s0; t0 = TB.t0;
to = turnoffs(X, t0);
lim = max(0.05*to(:, 4), TB.i_abs);
bad = abs(to(:, 3)) > lim;
w = X.tA >= t0; wb = B.tA >= t0; w4 = X.t4 >= t0; w4b = B.t4 >= t0;
pk = max(max(abs(X.i(w, :)))); pkb = max(max(abs(B.i(wb, :))));
vA = [min(X.vA(w4)) max(X.vA(w4))]; vAb = [min(B.vA(w4b)) max(B.vA(w4b))];
E = events(X);
prev = [2; E(:, 2)]; nxt = [E(:, 2); NaN];
seq = [prev(1:end-1) nxt(1:end-1)];
n_shed = sum(seq(:, 2) == 1); n_ret = sum(seq(:, 2) == 2 & (seq(:, 1) == 1 | seq(:, 1) == 4)); n_cancel = sum(seq(:, 1) == 3 & seq(:, 2) == 2);
L = struct();
L.T1_turnoff = ~any(bad);
L.T2_phase_peak = pk <= TB.rated_pk;
L.T3_vA_vs_noshed = abs(vA(1) - vAb(1)) <= 0.5 && abs(vA(2) - vAb(2)) <= 0.5;
L.T4_no_chatter = n_shed == TB.n_shed && n_ret == TB.n_ret && n_cancel == 0;
fn = fieldnames(L); pass = all(cellfun(@(f) L.(f), fn));
failed = fn(~cellfun(@(f) L.(f), fn))';
% ---- E24 대조(정보) ---------------------------------------------------------------------------------
M = jsondecode(fileread(fullfile(refDir, ['TB18_' cn '_metrics.json'])));
Z = readmatrix(fullfile(refDir, ['TB18_' cn '_ref.csv']));     % t vA vbus iw iAout smode If vA_noshed vbus_noshed(약 1 µs)
me = M.events; if iscell(me), me = cell2mat(cellfun(@(c) c(:)', me, 'UniformOutput', false)); end
tsh = E(find(E(:, 2) == 1, 1), 1); tsh_ref = me(find(me(:, 2) == 1, 1), 1);
tre = NaN; tre_ref = NaN;
k = find(seq(:, 2) == 2 & seq(:, 1) == 1, 1); if ~isempty(k), tre = E(k, 1); end
kr = find(me(:, 2) == 2, 1); if ~isempty(kr), tre_ref = me(kr, 1); end
cmp = {};
add = @(name, a, b, tol) {name, a, b, tol};
cmp(end+1, :) = add('shed time [ms]', tsh, tsh_ref, 0.02);
cmp(end+1, :) = add('return time [ms]', tre, tre_ref, 0.02);
cmp(end+1, :) = add('phase peak [A]', pk, M.phase_peak, 0.1*M.phase_peak);
cmp(end+1, :) = add('phase peak, no shedding [A]', pkb, M.phase_peak_noshed, 0.1*M.phase_peak_noshed);
cmp(end+1, :) = add('V_A min [V]', vA(1), M.vA(1), 0.3);
cmp(end+1, :) = add('V_A max [V]', vA(2), M.vA(2), 0.3);
cmp(end+1, :) = add('max turn-off current [A]', max(abs(to(:, 3))), M.ioff_max, NaN);
% 끝 0.2 ms 정상 구간 ZCS(위상별 턴오프 전류/창 피크, TB16과 같은 정의) — 정보
fin = to(:, 2) > X.tA(end) - 0.2e-3;
zfin = [NaN NaN];
for p = 1:2
    q = fin & to(:, 1) == p;
    if any(q), zfin(p) = max(abs(to(q, 3)))/max(max(abs(X.i(X.tA > X.tA(end) - 0.2e-3, p))), 1e-9); end
end
% ---- 요약 --------------------------------------------------------------------------------------------
fid = fopen(fullfile(resDir, ['TB18_' cn '_summary.txt']), 'w');
o2(fid, 'TB18 case %s (V_bat %.0f V), dt %.2f ns, wall %.0f s (shed) + %.0f s (no shed)\n', cn, TB.vbat, 1e9*TB.dt, O.w1, O.w0);
o2(fid, '(1) criteria (t >= %.1f ms):\n', 1e3*t0);
for k = 1:numel(fn), o2(fid, '    %-20s %s\n', fn{k}, ternary(L.(fn{k}), 'PASS', 'FAIL')); end
o2(fid, '    turn-offs %d, violations %d (worst |i_off| %.2f A); phase peak %.1f A (no shedding %.1f A, rated %.1f A)\n', ...
    size(to, 1), sum(bad), max(abs(to(:, 3))), pk, pkb, TB.rated_pk);
o2(fid, '    V_A %.3f-%.3f V (no shedding %.3f-%.3f V); shedding events: %s\n', vA(1), vA(2), vAb(1), vAb(2), mat2str(round(E, 4)));
o2(fid, '    shed %d, return %d, cancel %d (expected %d, %d, 0); end-window ZCS %.2f / %.2f %%\n', n_shed, n_ret, n_cancel, ...
    TB.n_shed, TB.n_ret, 100*zfin(1), 100*zfin(2));
o2(fid, '(2) comparison with E24 (info):\n');
o2(fid, '    %-32s %11s %11s %9s %9s\n', 'metric', 'Simscape', 'E24', 'diff', 'result');
for k = 1:size(cmp, 1)
    a = cmp{k, 2}; b = cmp{k, 3}; tol = cmp{k, 4};
    if isnan(tol), rr = 'info'; elseif isnan(a) && isnan(b), rr = 'ok'; else, rr = ternary(abs(a - b) <= tol, 'ok', 'over'); end
    o2(fid, '    %-32s %11.5g %11.5g %+9.3g %9s\n', cmp{k, 1}, a, b, a - b, rr);
end
fclose(fid);
S = struct('case', cn, 'verdict', ternary(pass, 'PASS', 'FAIL'), 'failed', {failed}, 'limits', L, ...
    'n_turnoff', size(to, 1), 'n_bad', sum(bad), 'ioff_max', max(abs(to(:, 3))), 'phase_peak', pk, 'phase_peak_noshed', pkb, ...
    'vA', vA, 'vA_noshed', vAb, 'events_ms', E, 'n_shed', n_shed, 'n_ret', n_ret, 'n_cancel', n_cancel, 'zcs_end', zfin, ...
    'wall_s', [O.w1 O.w0], 'dt_ns', 1e9*TB.dt, 'date', char(datetime('now')));
S.compare = cell2struct(cmp, {'metric', 'simscape', 'e24', 'tol'}, 2);
fid = fopen(fullfile(resDir, ['TB18_' cn '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
% ---- 그림 ------------------------------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [50 50 1100 900]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
plot(ax, 1e3*X.tA(1:4:end), X.i(1:4:end, 1), 'b', 'LineWidth', 0.4); plot(ax, 1e3*X.tA(1:4:end), X.i(1:4:end, 2), 'r', 'LineWidth', 0.4);
yline(ax, [-TB.rated_pk TB.rated_pk], 'k:');
yyaxis(ax, 'right'); stairs(ax, 1e3*X.t4(1:100:end), X.sm(1:100:end), 'g', 'LineWidth', 1.2); ylim(ax, [0.5 3.5]);
ylabel(ax, '셰딩 모드(2 둘, 3 멈추는 중, 1 하나)');
yyaxis(ax, 'left'); ylabel(ax, '위상 공진전류 [A]'); legend(ax, '위상 1', '위상 2', 'Location', 'best');
title(ax, sprintf('위상 전류와 셰딩(위상 첨두 %.1f A, 셰딩 없음 %.1f A, 점선 정격 %.1f A)', pk, pkb, TB.rated_pk));
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
n10 = round(1e-6/(X.t4(2) - X.t4(1)));
mv = @(x) movmean(x, n10);
plot(ax, 1e3*X.t4, mv(X.vA), 'b', 'LineWidth', 1.1); plot(ax, 1e3*B.t4, mv(B.vA), 'c'); plot(ax, 1e3*Z(:, 1), Z(:, 2), 'r--');
ylabel(ax, 'v_A [V](1 µs 평균)'); legend(ax, '셰딩(회로)', '셰딩 없음(회로)', 'E24 셰딩', 'Location', 'best'); title(ax, 'V_A 노드');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
n10 = round(10e-6/(X.t4(2) - X.t4(1)));
plot(ax, 1e3*X.t4, movmean(X.iAo, n10), 'b', 'LineWidth', 1.1); plot(ax, 1e3*Z(:, 1), movmean(Z(:, 5), 10), 'r--');
plot(ax, 1e3*X.t4(1:100:end), X.If(1:100:end), 'g');
ylabel(ax, '[A]'); xlabel(ax, '시간 [ms]'); legend(ax, 'Stage A 출력(회로, 10 µs 평균)', 'E24(10 µs 평균)', '게이트 필터 전류 If', 'Location', 'best');
title(ax, 'Stage A 모듈 출력전류');
title(tl, sprintf('TB18 %s', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB18_' cn '_response.png']), 'Resolution', 130); close(f);
fprintf('VERDICT %s: %s\n', cn, S.verdict);
end

function o2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
