function run_TB27(runList)
%RUN_TB27  TB27(Stage A 25 kHz 설계 수정안 A25R = A25 + C_A 2.4 mF, 4모듈 + 스위치 출력용량)을 사례별로 실행하고 판정한다.
%
%   run_TB27          % 사례 1–4
%   기준: 검증 코드 E35(A25R, E32 문턱, 모듈 관리기·셰딩·고장 처리), ref/make_ref_TB27.py
%   사례(시험 전에 고정)
%     1 FF27  800 V 충전 375 A + 버스 15 kW, 모듈 1 고장(1.1 ms) → 3모듈
%     2 MC27  800 V 충전 시작·종료(사전 기동 600 µs·충전전류 램프 600 µs)
%     3 MA27  540 V 버스 5 → 15 → 5 kW 계단(docs/14 D3 Tier-1)
%     4 SC27  800 V 정격 충전 정상상태(V_A 노드 −375 A + 버스 15 kW, 처음부터 충전 요청, 4 ms) — 손실 대조
%   판정(시험 전에 고정, t ≥ t0; SC27의 t0는 끝 1 ms 전)
%     (C1) 모든 턴오프(고장 모듈의 고장 순간 이후는 뺌): |i_off| ≤ max(5 % × 그 반주기 첨두, 1.0 A)
%     (C2) 위상 첨두(고장 모듈은 고장 전까지): 고장 없는 사례 ≤ P_rated(A25 공칭 74.5 A), 충전 중 고장 ≤ 1.5 × P_rated
%     (C3) V_A: 고장 사례는 고장 직전 20 µs 평균 ±10 V 안·≤ 470 V, 그 밖은 모델(E35) 최저·최고와 1.0 V 안
%     (C4) 끝 동작 모듈 수 = 기대값, 동작 수 변화 횟수 = 모델, 고장 모듈 재시작 없음, 멈추기 취소 0
%     (C5, SC27만) Stage A 손실(배터리 전력 − V_A 쪽 출력 전력)을 마지막 20주기(회로 위상 1의 구간 1 시작 간격으로 잰 실제 주기)
%          창에서 계산해 모델(도통 + 다이오드 + 출력용량, 게이트 제외, 마지막 20주기)과 10 % 안. TB26 진단(창이 실제 주기와
%          맞지 않으면 C_fly 저장 에너지가 남음)을 반영한 정의다. 다른 사례의 손실은 정보.
%   정보: 모델과 모듈 수 전환 시각 ±0.05 ms, 위상 첨두 ±10 %, V_A 최저·최고 ±0.5 V
%   결과: results/TB27_<사례>_summary.txt·json, _response.png, TB27_summary.txt·json

here = fileparts(mfilename('fullpath'));
mdl  = 'TB27_StageA25R_Integrated';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if evalin('base', 'exist(''TB27_tend'', ''var'')'), resDir = fullfile(here, 'results', 'smoke'); end
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {'FF27_800V_charge_m1', 'MC27_800V_charge_slow', 'MA27_540V_bus_5_15_5kW', 'SC27_800V_charge_steady'};
if nargin < 1 || isempty(runList), runList = 1:4; end
load_system(fullfile(here, [mdl '.slx']));
res = {};
for r = runList
    cn = R{r};
    assignin('base', 'TB27_case', cn);
    run(fullfile(here, 'TB27_init.m'));
    TB = evalin('base', 'TB');
    tic; out = sim(mdl, 'StopTime', num2str(TB.t_end, '%.9g')); wall = toc;
    X = extract(out, TB); clear out
    S = evaluate(X, TB, refDir, cn, resDir, wall);
    res{end+1} = S; %#ok<AGROW>
    fprintf('%s done (%.0f s): %s\n', cn, wall, S.verdict);
end
evalin('base', 'clear TB27_case');
fid = fopen(fullfile(resDir, 'TB27_summary.txt'), 'w');
o2(fid, 'TB27 Stage A 25 kHz design revision (A25R, C_A 2.4 mF) 4 modules + switch C_oss, module manager/shedding/fault, R2 bus, reference E35\n');
o2(fid, '%-24s %-6s %-9s %-9s %-26s %-8s %-18s %s\n', 'case', 'result', 'peak[A]', 'limit', 'vA [V]', 'modules', 'loss sim/model [W]', 'failed');
allPass = true;
for k = 1:numel(res)
    S = res{k};
    o2(fid, '%-24s %-6s %-9.1f %-9.1f %-7.2f-%-7.2f (%-7.2f) end %d  %7.1f / %7.1f   %s\n', S.case, S.verdict, S.phase_peak, S.pk_limit, ...
        S.vA(1), S.vA(2), S.vA_pre, S.n_end, S.loss_sim, S.loss_model, strjoin(S.failed, ', '));
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
o2(fid, 'TB27 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
fclose(fid);
fid = fopen(fullfile(resDir, 'TB27_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true)); fclose(fid);
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
X.qbat = double(out.qbat(:)); X.eout = double(out.eout(:));
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
t0 = TB.t0; fm = TB.fault_module;
M = jsondecode(fileread(fullfile(refDir, ['TB27_' cn '_metrics.json'])));
Z = readmatrix(fullfile(refDir, ['TB27_' cn '_ref.csv']));     % t vA vbus iw iAout nact If(약 1 µs)
if fm > 0
    fph = [2*fm - 1, 2*fm];
    kf = round(TB.t_fault/TB.dt) + 1; tf = X.tA(kf);
else
    fph = []; kf = numel(X.tA); tf = Inf;
end
to = turnoffs(X, t0);
keep = ~(ismember(to(:, 1), fph) & to(:, 2) >= tf - 1.5*TB.dt);
to = to(keep, :);
lim = max(0.05*to(:, 4), TB.i_abs);
bad = abs(to(:, 3)) > lim;
w = X.tA >= t0;
pk = 0;
for p = 1:8
    if ismember(p, fph), msk = w & X.tA < tf; else, msk = w; end
    if any(msk), pk = max(pk, max(abs(X.i(msk, p)))); end
end
w4 = X.t4 >= t0;
if fm > 0
    pre = X.t4 >= TB.t_fault - 20e-6 & X.t4 < TB.t_fault; post = X.t4 >= TB.t_fault;
    vpre = mean(X.vA(pre)); vA = [min(X.vA(post)) max(X.vA(post))];
    c3 = abs(vA(1) - vpre) <= TB.dv_A && abs(vA(2) - vpre) <= TB.dv_A && (TB.vbat > 920 || vA(2) <= TB.v_b470);
else
    vpre = NaN; vA = [min(X.vA(w4)) max(X.vA(w4))];
    c3 = abs(vA(1) - M.vA(1)) <= 1.0 && abs(vA(2) - M.vA(2)) <= 1.0;
end
d = find(diff(X.nact) ~= 0);
E = [1e3*X.t4(d + 1), X.nact(d + 1)];
dec = d(X.nact(d + 1) < X.nact(d));
dec_after = dec(X.t4(dec + 1) > tf + 15e-9);
if fm > 0, restart = any(any(X.s(kf + 1:end, fph) ~= 0)); else, restart = false; end
n_end = X.nact(end); n_cancel = X.mcancel(end);
me = M.events; if iscell(me), me = cell2mat(cellfun(@(c) c(:)', me, 'UniformOutput', false)); end
if isempty(me), me = zeros(0, 2); end
if fm > 0
    c4 = n_end == TB.n_end && ~restart && isempty(dec_after) && n_cancel == 0 && size(E, 1) == size(me, 1);
else
    c4 = n_end == TB.n_end && n_cancel == 0 && size(E, 1) == size(me, 1);
end
% (C5) 손실: 실제 주기(위상 1의 구간 1 시작 간격, 마지막 12번 평균) × n_loss 창
s1 = X.s(:, 1); on1 = find(s1(1:end-1) ~= 1 & s1(2:end) == 1) + 1;
if numel(on1) > 13, Tact = mean(diff(on1(end-12:end)))*TB.dt; else, Tact = TB.T; end
t1 = X.t4(end) - TB.n_loss*Tact; k1 = find(X.t4 >= t1, 1); k2 = numel(X.t4);
Dt = X.t4(k2) - X.t4(k1);
Pbat = TB.vbat*(X.qbat(k2) - X.qbat(k1))/Dt; Pout = (X.eout(k2) - X.eout(k1))/Dt;
loss = Pbat - Pout;
c5 = abs(loss - M.loss_ng_W) <= 0.10*M.loss_ng_W;
L = struct();
L.C1_turnoff = ~any(bad);
L.C2_phase_peak = pk <= TB.pk_limit;
L.C3_vA = c3;
L.C4_modules = c4;
if TB.loss_case, L.C5_loss = c5; end
fn = fieldnames(L); pass = all(cellfun(@(f) L.(f), fn));
failed = fn(~cellfun(@(f) L.(f), fn))';
% ---- 모델 대조(정보) ---------------------------------------------------------------------------------
nT = round(TB.T/TB.dt); t_rep = NaN;
if fm > 0
    for p = setdiff(1:8, fph)
        if ~any(X.s(max(1, kf - nT):kf - 1, p) ~= 0)
            kk = find(X.s(kf:end, p) ~= 0, 1);
            if ~isempty(kk), t_rep = min([t_rep, (kk - 1)*TB.dt]); end
        end
    end
end
cmp = {};
add = @(name, a, b, tol) {name, a, b, tol};
for k = 1:max(size(E, 1), size(me, 1))
    a = NaN; b = NaN;
    if k <= size(E, 1), a = E(k, 1); end
    if k <= size(me, 1), b = me(k, 1); end
    nm = sprintf('module change %d time [ms]', k);
    if k <= size(E, 1), nm = sprintf('%s (-> %d)', nm, E(k, 2)); end
    cmp(end+1, :) = add(nm, a, b, 0.05); %#ok<AGROW>
end
if isfield(M, 't_rep_us') && ~isempty(M.t_rep_us), mrep = M.t_rep_us; else, mrep = NaN; end
cmp(end+1, :) = add('replacement start [us]', 1e6*t_rep, mrep, 5.0);
cmp(end+1, :) = add('phase peak [A]', pk, M.phase_peak, 0.1*M.phase_peak);
cmp(end+1, :) = add('V_A min [V]', vA(1), M.vA(1), 0.5);
cmp(end+1, :) = add('V_A max [V]', vA(2), M.vA(2), 0.5);
cmp(end+1, :) = add(sprintf('Stage A loss, last %d periods [W]', TB.n_loss), loss, M.loss_ng_W, 0.1*M.loss_ng_W);
cmp(end+1, :) = add('max turn-off current [A]', max(abs(to(:, 3))), M.ioff_max, NaN);
% ---- 요약 --------------------------------------------------------------------------------------------
fid = fopen(fullfile(resDir, ['TB27_' cn '_summary.txt']), 'w');
o2(fid, 'TB27 case %s (V_bat %.0f V, %s, fault module %d at %.2f ms; model %s), dt %.2f ns, wall %.0f s\n', cn, TB.vbat, TB.kind, fm, ...
    1e3*TB.t_fault, M.model, 1e9*TB.dt, wall);
o2(fid, '(1) criteria (t >= %.2f ms):\n', 1e3*t0);
for k = 1:numel(fn), o2(fid, '    %-20s %s\n', fn{k}, ternary(L.(fn{k}), 'PASS', 'FAIL')); end
o2(fid, '    turn-offs %d, violations %d (worst |i_off| %.2f A); phase peak %.1f A (limit %.1f A, P_rated %.1f A)\n', ...
    size(to, 1), sum(bad), max(abs(to(:, 3))), pk, TB.pk_limit, TB.P_rated);
o2(fid, '    V_A %.3f-%.3f V (pre-fault %.3f); module changes: %s; end %d, restart %d, cancel %d; loss %.1f W (model %.1f W, P_bat %.0f W)\n', ...
    vA(1), vA(2), vpre, mat2str(round(E, 4)), n_end, restart, n_cancel, loss, M.loss_ng_W, Pbat);
o2(fid, '(2) comparison with E35 model (info):\n');
o2(fid, '    %-36s %11s %11s %9s %9s\n', 'metric', 'Simscape', 'E35', 'diff', 'result');
for k = 1:size(cmp, 1)
    a = cmp{k, 2}; b = cmp{k, 3}; tol = cmp{k, 4};
    if isnan(tol), rr = 'info'; elseif isnan(a) && isnan(b), rr = 'ok'; else, rr = ternary(abs(a - b) <= tol, 'ok', 'over'); end
    o2(fid, '    %-36s %11.5g %11.5g %+9.3g %9s\n', cmp{k, 1}, a, b, a - b, rr);
end
fclose(fid);
S = struct('case', cn, 'verdict', ternary(pass, 'PASS', 'FAIL'), 'failed', {failed}, 'limits', L, ...
    'n_turnoff', size(to, 1), 'n_bad', sum(bad), 'ioff_max', max(abs(to(:, 3))), 'phase_peak', pk, 'pk_limit', TB.pk_limit, ...
    'vA_pre', vpre, 'vA', vA, 'events_ms', E, 'n_end', n_end, 'restart', restart, 'n_cancel', n_cancel, 't_rep_us', 1e6*t_rep, ...
    'loss_sim', loss, 'loss_model', M.loss_ng_W, 'P_bat', Pbat, 'wall_s', wall, 'dt_ns', 1e9*TB.dt, 'date', char(datetime('now')));
S.compare = cell2struct(cmp, {'metric', 'simscape', 'e33', 'tol'}, 2);
fid = fopen(fullfile(resDir, ['TB27_' cn '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
% ---- 그림 ------------------------------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [50 50 1100 900]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
cl = lines(4);
for p = 1:8
    plot(ax, 1e3*X.tA(1:8:end), X.i(1:8:end, p), 'Color', cl(ceil(p/2), :), 'LineWidth', 0.3);
end
yline(ax, [-TB.pk_limit TB.pk_limit], 'k:'); if fm > 0, xline(ax, 1e3*TB.t_fault, 'r--'); end
yyaxis(ax, 'right'); stairs(ax, 1e3*X.t4(1:100:end), X.nact(1:100:end), 'k', 'LineWidth', 1.3); ylim(ax, [0 4.5]);
ylabel(ax, '동작 모듈 수');
yyaxis(ax, 'left'); ylabel(ax, '위상 공진전류 [A](색 = 모듈)');
title(ax, sprintf('위상 전류와 동작 모듈 수(고장 모듈 %d, %.2f ms, 위상 첨두 %.1f A, 점선 한도 %.1f A)', fm, 1e3*TB.t_fault, pk, TB.pk_limit));
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
n1 = round(1e-6/(X.t4(2) - X.t4(1)));
plot(ax, 1e3*X.t4, movmean(X.vA, n1), 'b', 'LineWidth', 1.1); plot(ax, 1e3*Z(:, 1), Z(:, 2), 'r--');
if fm > 0, xline(ax, 1e3*TB.t_fault, 'r--'); end
ylabel(ax, 'v_A [V](1 µs 평균)'); legend(ax, '회로', 'E35', 'Location', 'best'); title(ax, 'V_A 노드');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
n10 = round(10e-6/(X.t4(2) - X.t4(1)));
plot(ax, 1e3*X.t4, movmean(X.iAo, n10), 'b', 'LineWidth', 1.1); plot(ax, 1e3*Z(:, 1), movmean(Z(:, 5), 10), 'r--');
plot(ax, 1e3*X.t4(1:100:end), X.If(1:100:end), 'g');
ylabel(ax, '[A]'); xlabel(ax, '시간 [ms]');
legend(ax, 'Stage A 출력(회로, 10 µs 평균)', 'E35(10 µs 평균)', '게이트 필터 전류 If', 'Location', 'best');
title(ax, 'Stage A 전체 출력전류');
title(tl, sprintf('TB27 %s', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB27_' cn '_response.png']), 'Resolution', 130); close(f);
fprintf('VERDICT %s: %s\n', cn, S.verdict);
end

function o2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
