function run_TB06(runList)
%RUN_TB06  TB06 통합 회로 모델을 사례별로 실행하고 판정한다.
%
%   run_TB06          % 사례 1–3(5 ns)
%   run_TB06(4)       % 정보: 사례 A를 2.5 ns로(정상상태 리플·Stage C 수치 감쇠의 적분 간격 의존 확인)
%
%   실행 목록(사례, 적분 간격, 판정 사용)
%     1 A_640V_15to25kW  5 ns  판정   — 설계 코너(가장 큰 경로전류, 링크전력)
%     2 B_788V_5to15kW   5 ns  판정   — 직렬전압 ≈ 0 부근, DAB 저전류 구간
%     3 C_920V_25to15kW  5 ns  판정   — 음의 직렬전압(링크 → 버스), Stage A 최고 입력전압, 부하 감소
%     4 A_640V_15to25kW  2.5 ns 정보
%
%   판정(시험 전에 고정, README 참고). 평가 구간은 초기 정착 1 ms 이후.
%     (1) Tier-1(회로): 5 µs 주기 평균 버스 400 ± 8 V, 경로·필터 순시 ≤ 98 A, 링크전류 주기 평균 ≤ 80 A·링크전력 ≤ 8 kW,
%         링크전압 90–110 V, |v_s| ≤ 90 V. 마지막 1 ms 버스 리플(기준 0.1 V)은 5 ns 게이트 격자의 리밋 사이클을 포함하므로 정보.
%     (2) Stage B 등가 모델(E12, Stage A = V_bat/2 + 13.2 mΩ, Stage C = 정전력 부하)과 일치
%         계단 전(1.8–2.0 ms)·끝(4.8–5.0 ms) 평균: 버스 0.2 V, 경로·필터 1 A, 링크전압 0.5 V·링크전류 1.5 A + 3 %(사례 A만 판정)
%         계단 뒤: 최저·최고 버스전압 1.0 V, 최대 경로·필터 순시 전류 max(3 A, 5 %), 주기 평균 버스전압 궤적 RMS 0.3 V
%         (TB04보다 과도 허용폭을 넓힌 이유: 실제 Stage A 출력 임피던스(공진 SC + C_A)와 Stage C 입력은 등가 모델과 다르다.
%          이 차이가 등가 모델로 설계한 Stage B 판정을 바꾸지 않는지를 보는 시험이다)
%     (3) Stage A(E1 영교차 추종, 2위상, 같은 평균 출력전류): 위상별 ZCS 비율(턴오프 순간 |i|/피크) ≤ 5 %,
%         V_A 평균 ±0.3 V, 위상 간 평균 출력전류 차 ≤ 5 %(계단 전·끝 구간)
%     (4) Stage C: 48 V 출력 ±2 %(47.04–48.96 V, 1 ms 이후 전 구간), 끝 평균 출력이 TB05(같은 적분 간격, 400 V 입력)와 ±0.15 V
%   결과: results/TB06_<사례><꼬리>_summary.txt·json, _periods.csv, _response.png, _stageA.png, TB06_summary.txt·json, 회로도 그림

here = fileparts(mfilename('fullpath'));
mdl  = 'TB06_Integrated_Drive';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {  % 사례,             dt,      판정, 결과 꼬리
    'A_640V_15to25kW', 5e-9,   true,  '';
    'B_788V_5to15kW',  5e-9,   true,  '';
    'C_920V_25to15kW', 5e-9,   true,  '';
    'A_640V_15to25kW', 2.5e-9, false, '_dt2.5ns'};
if nargin < 1 || isempty(runList), runList = 1:3; end

load_system(fullfile(here, [mdl '.slx']));
res = struct('case', {}, 'dt_ns', {}, 'judged', {}, 'verdict', {}, 'tier1', {}, 'equiv', {}, 'stageA', {}, ...
    'stageC', {}, 'ripple_V', {}, 'wall_s', {});
for r = runList
    cn = R{r, 1};
    assignin('base', 'TB06_case', cn);
    assignin('base', 'TB06_opts', struct('dt', R{r, 2}));
    run(fullfile(here, 'TB06_init.m'));
    tic; out = sim(mdl); wall = toc;
    S = evaluate(out, TB, refDir, cn, resDir, wall, R{r, 4});
    res(end+1) = struct('case', cn, 'dt_ns', 1e9*TB.dt, 'judged', R{r, 3}, 'verdict', S.verdict, ...
        'tier1', S.tier1_pass, 'equiv', S.equiv_pass, 'stageA', S.stageA_pass, 'stageC', S.stageC_pass, ...
        'ripple_V', S.ripple_last1ms_V, 'wall_s', wall); %#ok<AGROW>
    fprintf('%s%s done (%.0f s): %s\n', cn, R{r, 4}, wall, S.verdict);
    clear out
end
evalin('base', 'clear TB06_case TB06_opts');

% ---- 요약 -------------------------------------------------------------------------------------
sumName = 'TB06_summary';
if ~isequal(runList, 1:3), sumName = sprintf('TB06_summary_runs%s', sprintf('_%d', runList)); end
judged = [res.judged];
pass = all(strcmp({res(judged).verdict}, 'PASS')) && nnz(judged) == 3;
fid = fopen(fullfile(resDir, [sumName '.txt']), 'w');
o2(fid, 'TB06 integrated circuit model (drive mode): Stage A module 1 (2 phases, zero-crossing tracking) + Stage B + Stage C 3 kW + CPL\n');
o2(fid, '%-18s %6s %7s %7s %7s %7s %10s %7s %s\n', 'case', 'dt[ns]', 'Tier1', 'E12', 'StageA', 'StageC', 'ripple[V]', 'wall[s]', 'verdict');
for k = 1:numel(res)
    x = res(k);
    o2(fid, '%-18s %6.2f %7s %7s %7s %7s %10.3f %7.0f %s%s\n', x.case, x.dt_ns, pf(x.tier1), pf(x.equiv), pf(x.stageA), ...
        pf(x.stageC), x.ripple_V, x.wall_s, x.verdict, ternary(x.judged, '', ' (info)'));
end
o2(fid, 'ripple = last-1 ms max-min of the 5 us period-mean bus voltage: information only at the 5 ns gate grid (TB04B)\n');
if nnz(judged) == 3
    o2(fid, 'TB06 VERDICT (cases A, B, C at 5 ns): %s\n', ternary(pass, 'PASS', 'FAIL'));
end
fclose(fid);
fid = fopen(fullfile(resDir, [sumName '.json']), 'w');
fprintf(fid, '%s', jsonencode(struct('runs', res, 'verdict', ternary(pass, 'PASS', 'FAIL'), 'date', char(datetime('now')), ...
    'matlab', version), 'PrettyPrint', true)); fclose(fid);
if isequal(runList, 1:3)
    sl_export_png({mdl, [mdl '/StageA_Module1'], [mdl '/StageA_Module1/StageA_Phase1'], [mdl '/Gate_StageA']}, resDir);
end
end

% =====================================================================================================
function S = evaluate(out, TB, refDir, cn, resDir, wall, tag)
fnm = [cn tag];
sig = {'t', 'vbus', 'ip', 'ih', 'vs', 'vlink', 'ilink', 'iL', 'vA', 'iAo', 'iA1', 'iA2', 'st1', 'st2', 'icin', 'vo48'};
D = struct();
for k = 1:numel(sig)
    x = out.(sig{k}); x = x(:);
    if k > 1, x(1) = x(2); end                     % Simscape 첫 출력 표본(초기화 값) 제외
    D.(sig{k}) = x;
end
dg = cols(out.dg, 6);
T = 5e-6; Np = TB.Np; nper = floor(numel(D.t)/Np);
idx = reshape(1:nper*Np, Np, nper);
pm = @(x) mean(x(idx), 1)';
% 주기 통계(tb_stageB_evaluate와 같은 열 순서)
pr = [pm(D.vbus), pm(D.ip), pm(D.ih), pm(D.vlink), pm(D.ilink), pm(D.vlink.*D.ilink), ...
      max(D.ih(idx), [], 1)', min(D.ih(idx), [], 1)', max(abs(D.ip(idx)), [], 1)', min(D.vbus(idx), [], 1)', ...
      max(D.vbus(idx), [], 1)', max(abs(D.vs(idx)), [], 1)'];
vAm = pm(D.vA); vom = pm(D.vo48); pcin = pm(D.vbus.*D.icin);
tq = (1:nper)'*T;
Rr = readmatrix(fullfile(refDir, ['TB06_' cn '_rec.csv']));
n = min(nper, size(Rr, 1)); pr = pr(1:n, :); tq = tq(1:n); Rr = Rr(1:n, :); vAm = vAm(1:n); vom = vom(1:n); pcin = pcin(1:n);
py = struct('vb', Rr(:, 2), 'ip', Rr(:, 3), 'ih', Rr(:, 4), 'vl', Rr(:, 5), 'il', Rr(:, 6), 'ihmax', Rr(:, 8), ...
    'ipabs', Rr(:, 10), 'vbmin', Rr(:, 11), 'vbmax', Rr(:, 12), 'rho', Rr(:, 23), 'eps', Rr(:, 24));
ev = tq > TB.t_eval; pre = tq > TB.t_step - 0.2e-3 & tq <= TB.t_step; post = tq > TB.t_step;
fin = tq > TB.t_end - 0.2e-3; last1 = tq > TB.t_end - 1e-3;
isA = startsWith(cn, 'A');

% ---- (1) Tier-1 --------------------------------------------------------------------------------
T1 = struct();
T1.vbus_window = all(abs(pr(ev, 1) - 400) <= 8);
T1.path_current = max(pr(ev, 9)) <= 98 && max(max(abs(pr(ev, 7:8)))) <= 98;
T1.link_current = max(abs(pr(ev, 5))) <= 80 && max(abs(pr(ev, 6))) <= 8000;
T1.link_voltage = all(pr(ev, 4) >= 90 & pr(ev, 4) <= 110);
T1.series_voltage = max(pr(ev, 12)) <= 90;
t1pass = all(cellfun(@(f) T1.(f), fieldnames(T1)));
ripple = max(pr(last1, 1)) - min(pr(last1, 1));

% ---- (2) Stage B 등가 모델(E12)과 일치 ------------------------------------------------------------
cmp = {};
add = @(name, a, b, tol, use) {name, a, b, tol, use};
cmp(end+1, :) = add('pre-step mean v_bus [V]',  mean(pr(pre, 1)), mean(py.vb(pre)), 0.2, true);
cmp(end+1, :) = add('pre-step mean i_p [A]',    mean(pr(pre, 2)), mean(py.ip(pre)), 1.0, true);
cmp(end+1, :) = add('pre-step mean i_h [A]',    mean(pr(pre, 3)), mean(py.ih(pre)), 1.0, true);
cmp(end+1, :) = add('pre-step mean v_link [V]', mean(pr(pre, 4)), mean(py.vl(pre)), 0.5, isA);
Il = mean(py.il(pre));
cmp(end+1, :) = add('pre-step mean link current [A]', mean(pr(pre, 5)), Il, 1.5 + 0.03*abs(Il), isA);
cmp(end+1, :) = add('min v_bus after step [V]', min(pr(post, 10)), min(py.vbmin(post)), 1.0, true);
cmp(end+1, :) = add('max v_bus after step [V]', max(pr(post, 11)), max(py.vbmax(post)), 1.0, true);
pk = max(py.ipabs(post));
cmp(end+1, :) = add('max |i_p| after step [A]', max(pr(post, 9)), pk, max(3, 0.05*pk), true);
pk = max(py.ihmax(post));
cmp(end+1, :) = add('max i_h after step [A]',   max(pr(post, 7)), pk, max(3, 0.05*pk), true);
cmp(end+1, :) = add('rms diff of period-mean v_bus after step [V]', sqrt(mean((pr(post, 1) - py.vb(post)).^2)), 0, 0.3, true);
cmp(end+1, :) = add('final mean v_bus [V]',     mean(pr(fin, 1)), mean(py.vb(fin)), 0.2, true);
cmp(end+1, :) = add('final mean i_p [A]',       mean(pr(fin, 2)), mean(py.ip(fin)), 1.0, true);
cmp(end+1, :) = add('final mean v_link [V]',    mean(pr(fin, 4)), mean(py.vl(fin)), 0.5, isA);
Il = mean(py.il(fin));
cmp(end+1, :) = add('final mean link current [A]', mean(pr(fin, 5)), Il, 1.5 + 0.03*abs(Il), isA);
kq = @(tt) min(size(dg, 1), max(1, round(tt/T)));
cmp(end+1, :) = add('rho_hat before step (info)', dg(kq(TB.t_step), 4), py.rho(round(TB.t_step/T)), NaN, false);
cmp(end+1, :) = add('eps_hat at end [A] (info)', dg(end, 5), py.eps(end), NaN, false);

% ---- (3) Stage A ------------------------------------------------------------------------------------
SA = jsondecode(fileread(fullfile(refDir, ['TB06_' cn '_stageA.json'])));
win = {'pre', TB.t_step - 0.2e-3, TB.t_step; 'final', TB.t_end - 0.2e-3, TB.t_end};
A = struct(); apass = true; arows = {};
for w = 1:2
    m = D.t > win{w, 2} & D.t <= win{w, 3};
    ref = SA.(win{w, 1});
    I = [D.iA1(m) D.iA2(m)]; Sg = [D.st1(m) D.st2(m)];
    for p = 1:2
        i = I(:, p); s = Sg(:, p);
        offk = find(s(1:end-1) > 0.5 & s(2:end) < 0.5);         % 도통 → 데드타임(턴오프 순간)
        Ipk = max(abs(i)); zcs = max(abs(i(offk)))/Ipk;        % 턴오프 순간 전류 = 마지막 도통 표본(TB01과 같은 정의)
        io = mean(i.*(s == 1) - i.*(s == 2));                  % 위상 평균 출력전류(충전 +i, 방전 −i)
        A.(win{w, 1}).zcs(p) = zcs; A.(win{w, 1}).Ipk(p) = Ipk; A.(win{w, 1}).io(p) = io; A.(win{w, 1}).noff(p) = numel(offk);
        arows(end+1, :) = {sprintf('%s phase %d ZCS ratio', win{w, 1}, p), zcs, ref.zcs(p), 0.05, 'limit'}; %#ok<AGROW>
        arows(end+1, :) = {sprintf('%s phase %d peak current [A] (info)', win{w, 1}, p), Ipk, ref.Ipk(p), NaN, 'info'}; %#ok<AGROW>
        apass = apass && zcs <= 0.05;
    end
    vA = mean(D.vA(m));
    arows(end+1, :) = {sprintf('%s mean V_A [V]', win{w, 1}), vA, ref.vA_mean, 0.3, 'abs'}; %#ok<AGROW>
    apass = apass && abs(vA - ref.vA_mean) <= 0.3;
    io = A.(win{w, 1}).io; sh = abs(io(1) - io(2))/mean(io);
    arows(end+1, :) = {sprintf('%s phase current sharing |I1-I2|/I', win{w, 1}), sh, 0, 0.05, 'limit'}; %#ok<AGROW>
    apass = apass && sh <= 0.05;
    arows(end+1, :) = {sprintf('%s Stage A output current [A] (info)', win{w, 1}), mean(D.iAo(m)), ref.iout, NaN, 'info'}; %#ok<AGROW>
    arows(end+1, :) = {sprintf('%s V_A ripple p-p [V] (info)', win{w, 1}), max(D.vA(m)) - min(D.vA(m)), ref.vA_ripple, NaN, 'info'}; %#ok<AGROW>
end

% ---- (4) Stage C ------------------------------------------------------------------------------------
vo_ev = D.vo48(D.t > TB.t_eval);
C = struct('vo_min', min(vo_ev), 'vo_max', max(vo_ev), 'vo_final', mean(vom(fin)), 'pin_pre', mean(pcin(pre)), ...
    'pin_final', mean(pcin(fin)), 'vo_step_dev', max(abs(vom(post) - mean(vom(pre)))));
cpass = C.vo_min >= 48*0.98 && C.vo_max <= 48*1.02 && abs(C.vo_final - TB.vo_TB05) <= 0.15;

% ---- 기록 -------------------------------------------------------------------------------------------
equiv = true;
fid = fopen(fullfile(resDir, ['TB06_' fnm '_summary.txt']), 'w');
o2(fid, 'TB06 integrated model, case %s (V_bat %.0f V, bus total %.1f -> %.1f kW at %.1f ms, CPL %.2f -> %.2f kW + Stage C), dt %.2f ns, wall %.0f s\n', ...
    cn, TB.vbat, TB.P0tot/1e3, TB.P1tot/1e3, 1e3*TB.t_step, TB.P0/1e3, TB.P1/1e3, 1e9*TB.dt, wall);
o2(fid, '(1) Tier-1 on the circuit (t > %.1f ms):\n', 1e3*TB.t_eval);
o2(fid, '    v_bus period mean %.2f-%.2f V, max |i_p| %.2f A, i_h %.2f/%.2f A, link %.2f A / %.0f W, v_link %.2f-%.2f V, max |v_s| %.1f V\n', ...
    min(pr(ev, 1)), max(pr(ev, 1)), max(pr(ev, 9)), max(pr(ev, 7)), min(pr(ev, 8)), max(abs(pr(ev, 5))), max(abs(pr(ev, 6))), ...
    min(pr(ev, 4)), max(pr(ev, 4)), max(pr(ev, 12)));
fn = fieldnames(T1);
for k = 1:numel(fn), o2(fid, '    %-16s %s\n', fn{k}, pf(T1.(fn{k}))); end
o2(fid, '    last-1ms ripple %.3f V (information only at the %.2f ns gate grid; limit 0.1 V met at 0.625 ns in TB04B)\n', ripple, 1e9*TB.dt);
o2(fid, '(2) agreement with the Stage B verification model (E12, Stage A as V_bat/2 + 13.2 mOhm, Stage C as CPL):\n');
o2(fid, '    %-46s %11s %11s %9s %7s\n', 'metric', 'Simscape', 'model', 'diff', 'result');
for k = 1:size(cmp, 1)
    a = cmp{k, 2}; b = cmp{k, 3}; tol = cmp{k, 4}; use = cmp{k, 5};
    d = a - b; ok = abs(d) <= tol;
    if isnan(tol), rr = 'info'; elseif ~use, rr = ternary(ok, 'info(ok)', 'info'); else, rr = pf(ok); equiv = equiv && ok; end
    o2(fid, '    %-46s %11.4g %11.4g %+9.3g %7s\n', cmp{k, 1}, a, b, d, rr);
end
o2(fid, '(3) Stage A (verification model E1, zero-crossing tracking, 2 phases, same mean output current):\n');
o2(fid, '    %-46s %11s %11s %9s %7s\n', 'metric', 'Simscape', 'E1', 'diff', 'result');
for k = 1:size(arows, 1)
    a = arows{k, 2}; b = arows{k, 3}; tol = arows{k, 4};
    switch arows{k, 5}
        case 'limit', rr = pf(a <= tol);
        case 'abs',   rr = pf(abs(a - b) <= tol);
        otherwise,    rr = 'info';
    end
    o2(fid, '    %-46s %11.4g %11.4g %+9.3g %7s\n', arows{k, 1}, a, b, a - b, rr);
end
o2(fid, '    ZCS limit 5 %% (design criterion), V_A mean +-0.3 V vs E1, phase sharing <= 5 %%\n');
o2(fid, '(4) Stage C: v_48 %.3f-%.3f V after %.1f ms (limit 47.04-48.96 V), final mean %.3f V (TB05 at %.1f ns: %.3f V, tol 0.15 V),\n', ...
    C.vo_min, C.vo_max, 1e3*TB.t_eval, C.vo_final, 1e9*TB.dt, TB.vo_TB05);
o2(fid, '    max deviation of period-mean v_48 after the step %.3f V (info), Stage C input power %.0f W before / %.0f W at end (CPL estimate used %.0f W): %s\n', ...
    C.vo_step_dev, C.pin_pre, C.pin_final, TB.Pc_in, pf(cpass));
verdict = ternary(t1pass && equiv && apass && cpass, 'PASS', 'FAIL');
o2(fid, 'VERDICT %s: %s (Tier-1 %s, E12 agreement %s, Stage A %s, Stage C %s)\n', fnm, verdict, pf(t1pass), pf(equiv), pf(apass), pf(cpass));
fclose(fid);
S = struct('case', cn, 'dt_ns', 1e9*TB.dt, 'verdict', verdict, 'tier1', T1, 'tier1_pass', t1pass, 'equiv_pass', equiv, ...
    'stageA_pass', apass, 'stageC_pass', cpass, 'ripple_last1ms_V', ripple, 'stageA', A, 'stageC', C, 'wall_s', wall, ...
    'date', char(datetime('now')), 'matlab', version);
S.compare = cell2struct(cmp, {'metric', 'simscape', 'model', 'tol', 'judged'}, 2);
S.stageA_compare = cell2struct(arows, {'metric', 'simscape', 'E1', 'tol', 'type'}, 2);
fid = fopen(fullfile(resDir, ['TB06_' fnm '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
writematrix([tq pr vAm vom pcin], fullfile(resDir, ['TB06_' fnm '_periods.csv']));

% ---- 그림 1: 응답(주기 평균) -------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 1000 1050]);
tl = tiledlayout(f, 6, 1, 'TileSpacing', 'compact');
ms = 1e3*tq;
nexttile; hold on; grid on; plot(ms, pr(:, 1), 'LineWidth', 1.4); plot(ms, py.vb, '--', 'LineWidth', 1.2);
yline([392 408], ':'); ylabel('v_{bus} [V]'); legend('Simscape (integrated)', 'E12 (equivalent Stage A, CPL)', 'Location', 'southeast');
title('bus voltage (5 \mus period mean)');
nexttile; hold on; grid on; plot(ms, pr(:, 2), 'LineWidth', 1.4); plot(ms, py.ip, '--', 'LineWidth', 1.2);
plot(ms, pr(:, 3), 'LineWidth', 1.1); plot(ms, py.ih, '--', 'LineWidth', 1.0);
ylabel('[A]'); legend('i_p Simscape', 'i_p E12', 'i_h Simscape', 'i_h E12', 'Location', 'southeast'); title('path and filter current');
nexttile; hold on; grid on; plot(ms, pr(:, 4), 'LineWidth', 1.4); plot(ms, py.vl, '--', 'LineWidth', 1.2);
ylabel('v_{link} [V]'); title('floating link voltage');
nexttile; hold on; grid on; plot(ms, pr(:, 5), 'LineWidth', 1.4); plot(ms, py.il, '--', 'LineWidth', 1.2);
ylabel('[A]'); title('DAB link current (period mean)');
nexttile; hold on; grid on; plot(ms, vAm, 'LineWidth', 1.4); plot(ms, TB.vbat/2 - TB.A.RA*py.ip, '--', 'LineWidth', 1.2);
ylabel('V_A [V]'); legend('Simscape (Stage A circuit)', 'V_{bat}/2 - 10.2 m\Omega \cdot i_p (E12)', 'Location', 'northeast');
title('Stage A output node V_A');
nexttile; hold on; grid on; plot(ms, vom, 'LineWidth', 1.4); yline(TB.vo_TB05, '--'); yline([47.04 48.96], ':');
ylabel('v_{48} [V]'); xlabel('t [ms]'); title('Stage C 48 V output (dashed: TB05 at the same step size, dotted: \pm2 %)');
title(tl, sprintf('TB06 %s: V_{bat} %.0f V, bus %.0f \\rightarrow %.0f kW at %.0f ms (Stage C 3 kW included)', strrep(fnm, '_', ' '), ...
    TB.vbat, TB.P0tot/1e3, TB.P1tot/1e3, 1e3*TB.t_step));
exportgraphics(f, fullfile(resDir, ['TB06_' fnm '_response.png']), 'Resolution', 150); close(f);

% ---- 그림 2: Stage A 공진전류(끝 구간 마지막 3주기) ---------------------------------------------------------
Tr = 2*pi*sqrt(TB.A.Lr*TB.A.Cfly);                         % 공칭 공진 주기(약 6.7 µs)
z = D.t > TB.t_end - 3*Tr;
f = figure('Visible', 'off', 'Position', [100 100 1000 700]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
tz = 1e6*(D.t(z) - D.t(find(z, 1)));
nexttile; hold on; grid on; plot(tz, D.iA1(z), 'LineWidth', 1.2); plot(tz, D.iA2(z), 'LineWidth', 1.2);
ylabel('i_C [A]'); legend('phase 1', 'phase 2', 'Location', 'eastoutside'); title('Stage A resonant currents (zero-crossing tracking, interleaved)');
nexttile; hold on; grid on; stairs(tz, D.st1(z), 'LineWidth', 1.1); stairs(tz, D.st2(z) + 0.05, 'LineWidth', 1.1);
ylabel('segment'); yticks([0 1 2]); yticklabels({'dead', 'S1·S3', 'S2·S4'}); legend('phase 1', 'phase 2', 'Location', 'eastoutside');
nexttile; hold on; grid on;
yyaxis left;  plot(tz, D.vA(z), 'LineWidth', 1.2); ylabel('V_A [V]');
yyaxis right; plot(tz, D.ip(z), 'LineWidth', 1.0); ylabel('i_p [A]');
legend('V_A', 'i_p', 'Location', 'eastoutside'); xlabel('t [\mus]'); title('V_A node voltage and path current');
title(tl, sprintf('TB06 %s: Stage A module 1 at the end of the run (ZCS %.2f %% / %.2f %%)', strrep(fnm, '_', ' '), ...
    100*A.final.zcs(1), 100*A.final.zcs(2)));
exportgraphics(f, fullfile(resDir, ['TB06_' fnm '_stageA.png']), 'Resolution', 150); close(f);
end

function a = cols(a, m)
if ndims(a) == 3, a = reshape(a, size(a, 1)*size(a, 2), [])'; end
if size(a, 2) ~= m, a = a'; end
end

function s = pf(c)
s = ternary(c, 'PASS', 'FAIL');
end

function o2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
