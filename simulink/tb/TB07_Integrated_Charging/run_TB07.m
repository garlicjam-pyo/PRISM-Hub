function run_TB07(runList)
%RUN_TB07  TB07 통합 회로 모델(충전 모드)을 사례별로 실행하고 판정한다.
%
%   run_TB07          % 사례 1–3(5 ns)
%
%   실행 목록(사례, 적분 간격, 판정 사용)
%     1 A_640V_chg_15to25kW  5 ns  판정(Tier-1) — 충전 375 A 중 보조부하 계단, 가장 큰 경로전류·링크전력
%     2 B_920V_chgstop_25kW  5 ns  판정(Tier-2) — 충전 비상 정지 326 A → 0(10 µs), 음의 직렬전압, 최고 전압
%     3 C_788V_chgon_5kW     5 ns  판정(Tier-2) — 충전기 접속 0 → 375 A(10 µs), 직렬전압 ≈ 0, DAB 저전류
%     4–7 추가 실행(정보, run_TB07(4:7)): 사례 C를 충전전류 변화 100 µs·1 ms로(등가 모델의 유효 범위),
%         640 V·25 kW에서 충전기 접속·비상 정지 10 µs(회로의 Tier-2 경로전류 여유)
%
%   판정(시험 전에 고정, README 참고). 평가 구간은 초기 정착 1 ms 이후.
%     (1) 회로 한계: 5 µs 주기 평균 버스 — Tier-1 400 ± 8 V, Tier-2 384–416 V. 경로·필터 순시 Tier-1 ≤ 98 A, Tier-2 ≤ 100 A.
%         공통: 링크전류 주기 평균 ≤ 80 A·링크전력 ≤ 8 kW, 링크전압 90–110 V, |v_s| ≤ 90 V. 마지막 1 ms 리플은 정보(5 ns 격자).
%     (2) Stage B 기준 모델(E16 스위칭 모드: E12 엔진, 충전 경로 전원 V_bat/2 + R_A·i_ch, R = R_A + 3 mΩ)과 일치 — TB06과 같은 허용폭
%         (전환 전·끝 평균 버스 0.2 V, 경로·필터 1 A, 링크 0.5 V·1.5 A + 3 %(사례 A만), 전환 뒤 최저·최고 버스 1.0 V,
%          최대 경로·필터 순시 max(3 A, 5 %), 주기 평균 버스 궤적 RMS 0.3 V)
%     (3) Stage A(E1 영교차 추종 8위상, 같은 평균 출력전류): 위상별 턴오프 전류 ≤ 피크의 5 % 또는 ≤ 2 A
%         (2 A 턴오프 에너지 ½·V·I·20 ns ≤ 9 µJ는 출력용량 에너지 24 µJ보다 작다), V_A 평균 ±0.3 V, 위상 출력전류 분담 ≤ 5 %
%     (4) Stage C: 48 V 출력 ±2 %, 끝 평균이 TB05와 ±0.15 V
%     (5) 정보: 충전전류와 경로전류, Stage A 출력전류의 KCL(i_Aout = i_p − i_ch) 잔차
%   결과: results/TB07_<사례>_summary.txt·json, _periods.csv, _response.png, _stageA.png, TB07_summary.txt·json, 회로도 그림

here = fileparts(mfilename('fullpath'));
mdl  = 'TB07_Integrated_Charging';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {  % 사례,                     dt,    판정, 결과 꼬리
    'A_640V_chg_15to25kW',     5e-9, true,  '';
    'B_920V_chgstop_25kW',     5e-9, true,  '';
    'C_788V_chgon_5kW',        5e-9, true,  '';
    'C2_788V_chgon_5kW_100us', 5e-9, false, '';      % 추가(정보): 충전전류 변화 100 µs
    'C3_788V_chgon_5kW_1ms',   5e-9, false, '';      % 추가(정보): 충전전류 변화 1 ms
    'D_640V_chgon_25kW',       5e-9, false, '';      % 추가(정보): 최대 경로전류 코너, 충전기 접속 10 µs
    'E_640V_chgstop_25kW',     5e-9, false, ''};     % 추가(정보): 최대 경로전류 코너, 충전 비상 정지 10 µs
if nargin < 1 || isempty(runList), runList = 1:3; end

load_system(fullfile(here, [mdl '.slx']));
res = struct('case', {}, 'dt_ns', {}, 'judged', {}, 'verdict', {}, 'tier1', {}, 'equiv', {}, 'stageA', {}, ...
    'stageC', {}, 'ripple_V', {}, 'wall_s', {});
for r = runList
    cn = R{r, 1};
    assignin('base', 'TB07_case', cn);
    assignin('base', 'TB07_opts', struct('dt', R{r, 2}));
    run(fullfile(here, 'TB07_init.m'));
    tic; out = sim(mdl); wall = toc;
    S = evaluate(out, TB, refDir, cn, resDir, wall, R{r, 4});
    res(end+1) = struct('case', cn, 'dt_ns', 1e9*TB.dt, 'judged', R{r, 3}, 'verdict', S.verdict, ...
        'tier1', S.tier1_pass, 'equiv', S.equiv_pass, 'stageA', S.stageA_pass, 'stageC', S.stageC_pass, ...
        'ripple_V', S.ripple_last1ms_V, 'wall_s', wall); %#ok<AGROW>
    fprintf('%s%s done (%.0f s): %s\n', cn, R{r, 4}, wall, S.verdict);
    clear out
end
evalin('base', 'clear TB07_case TB07_opts');

% ---- 요약 -------------------------------------------------------------------------------------
sumName = 'TB07_summary';
if ~isequal(runList, 1:3), sumName = sprintf('TB07_summary_runs%s', sprintf('_%d', runList)); end
judged = [res.judged];
pass = all(strcmp({res(judged).verdict}, 'PASS')) && nnz(judged) == 3;
fid = fopen(fullfile(resDir, [sumName '.txt']), 'w');
o2(fid, 'TB07 integrated circuit model (charging mode): Stage A 4 modules (8 phases, zero-crossing tracking) + 400 V charger + Stage B + Stage C 3 kW + CPL\n');
o2(fid, '%-22s %6s %7s %7s %7s %7s %10s %7s %s\n', 'case', 'dt[ns]', 'Tier', 'E16', 'StageA', 'StageC', 'ripple[V]', 'wall[s]', 'verdict');
for k = 1:numel(res)
    x = res(k);
    o2(fid, '%-22s %6.2f %7s %7s %7s %7s %10.3f %7.0f %s%s\n', x.case, x.dt_ns, pf(x.tier1), pf(x.equiv), pf(x.stageA), ...
        pf(x.stageC), x.ripple_V, x.wall_s, x.verdict, ternary(x.judged, '', ' (info)'));
end
o2(fid, 'ripple = last-1 ms max-min of the 5 us period-mean bus voltage: information only at the 5 ns gate grid (TB04B)\n');
if nnz(judged) == 3
    o2(fid, 'TB07 VERDICT (cases A, B, C at 5 ns): %s\n', ternary(pass, 'PASS', 'FAIL'));
end
fclose(fid);
fid = fopen(fullfile(resDir, [sumName '.json']), 'w');
fprintf(fid, '%s', jsonencode(struct('runs', res, 'verdict', ternary(pass, 'PASS', 'FAIL'), 'date', char(datetime('now')), ...
    'matlab', version), 'PrettyPrint', true)); fclose(fid);
if isequal(runList, 1:3)
    sl_export_png({mdl, [mdl '/Gate_StageA'], [mdl '/Charger_Profile']}, resDir);
end
end

% =====================================================================================================
function S = evaluate(out, TB, refDir, cn, resDir, wall, tag)
fnm = [cn tag];
sig = {'t', 'vbus', 'ip', 'ih', 'vs', 'vlink', 'ilink', 'iL', 'vA', 'iAo', 'iA1', 'iA2', 'iA3', 'iA4', 'iA5', 'iA6', 'iA7', 'iA8', ...
       'st1', 'st2', 'st3', 'st4', 'st5', 'st6', 'st7', 'st8', 'icin', 'vo48'};
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
Rr = readmatrix(fullfile(refDir, ['TB07_' cn '_rec.csv']));
ichq = out.ich(:); ichq(1) = ichq(min(2, end));
n = min(nper, size(Rr, 1)); pr = pr(1:n, :); tq = tq(1:n); Rr = Rr(1:n, :); vAm = vAm(1:n); vom = vom(1:n); pcin = pcin(1:n);
py = struct('vb', Rr(:, 2), 'ip', Rr(:, 3), 'ih', Rr(:, 4), 'vl', Rr(:, 5), 'il', Rr(:, 6), 'ihmax', Rr(:, 8), ...
    'ipabs', Rr(:, 10), 'vbmin', Rr(:, 11), 'vbmax', Rr(:, 12), 'rho', Rr(:, 23), 'eps', Rr(:, 24));
ev = tq > TB.t_eval; pre = tq > TB.t_step - 0.2e-3 & tq <= TB.t_step; post = tq > TB.t_step;
fin = tq > TB.t_end - 0.2e-3; last1 = tq > TB.t_end - 1e-3;
isA = startsWith(cn, 'A');

% ---- (1) 회로 한계(사례 A Tier-1, B·C Tier-2) ------------------------------------------------------
T1 = struct();
if TB.tier == 1
    T1.vbus_window = all(abs(pr(ev, 1) - 400) <= 8);
    ilim = 98;
else
    T1.vbus_window = all(pr(ev, 1) >= 384 & pr(ev, 1) <= 416) && abs(mean(pr(fin, 1)) - 400) <= 4;
    ilim = 100;
end
T1.path_current = max(pr(ev, 9)) <= ilim && max(max(abs(pr(ev, 7:8)))) <= ilim;
T1.link_current = max(abs(pr(ev, 5))) <= 80 && max(abs(pr(ev, 6))) <= 8000;
T1.link_voltage = all(pr(ev, 4) >= 90 & pr(ev, 4) <= 110);
T1.series_voltage = max(pr(ev, 12)) <= 90;
t1pass = all(cellfun(@(f) T1.(f), fieldnames(T1)));
ripple = max(pr(last1, 1)) - min(pr(last1, 1));

% ---- (2) Stage B 기준 모델(E16 스위칭 모드)과 일치 ---------------------------------------------------
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

% ---- (3) Stage A(8위상) ------------------------------------------------------------------------------
SA = jsondecode(fileread(fullfile(refDir, ['TB07_' cn '_stageA.json'])));
win = {'pre', TB.t_step - 0.2e-3, TB.t_step; 'final', TB.t_end - 0.2e-3, TB.t_end};
A = struct(); apass = true; arows = {};
for w = 1:2
    m = D.t > win{w, 2} & D.t <= win{w, 3};
    ref = SA.(win{w, 1});
    I = [D.iA1(m) D.iA2(m) D.iA3(m) D.iA4(m) D.iA5(m) D.iA6(m) D.iA7(m) D.iA8(m)];
    Sg = [D.st1(m) D.st2(m) D.st3(m) D.st4(m) D.st5(m) D.st6(m) D.st7(m) D.st8(m)];
    for p = 1:8
        i = I(:, p); s = Sg(:, p);
        offk = find(s(1:end-1) > 0.5 & s(2:end) < 0.5);         % 도통 → 데드타임(턴오프 순간)
        Ipk = max(abs(i)); ioff = max(abs(i(offk))); zcs = ioff/Ipk;   % 턴오프 순간 전류 = 마지막 도통 표본(TB01과 같은 정의)
        io = mean(i.*(s == 1) - i.*(s == 2));                  % 위상 평균 출력전류(V_A 방향 양수, 충전 중 음수)
        A.(win{w, 1}).zcs(p) = zcs; A.(win{w, 1}).ioff(p) = ioff; A.(win{w, 1}).Ipk(p) = Ipk;
        A.(win{w, 1}).io(p) = io; A.(win{w, 1}).noff(p) = numel(offk);
        okz = zcs <= 0.05 || ioff <= 2;
        arows(end+1, :) = {sprintf('%s phase %d ZCS ratio (or i_off <= 2 A: %.2f A)', win{w, 1}, p, ioff), zcs, ref.zcs(p), 0.05, ternary(okz, 'okz', 'ngz')}; %#ok<AGROW>
        apass = apass && okz;
    end
    arows(end+1, :) = {sprintf('%s peak current, phases 1-8 max [A] (info)', win{w, 1}), max(A.(win{w, 1}).Ipk), max(ref.Ipk), NaN, 'info'}; %#ok<AGROW>
    vA = mean(D.vA(m));
    arows(end+1, :) = {sprintf('%s mean V_A [V]', win{w, 1}), vA, ref.vA_mean, 0.3, 'abs'}; %#ok<AGROW>
    apass = apass && abs(vA - ref.vA_mean) <= 0.3;
    io = A.(win{w, 1}).io; sh = max(abs(io - mean(io)))/abs(mean(io));
    arows(end+1, :) = {sprintf('%s phase current sharing max|I_k-I|/|I|', win{w, 1}), sh, 0, 0.05, 'limit'}; %#ok<AGROW>
    apass = apass && sh <= 0.05;
    kcl = mean(D.iAo(m)) - (mean(D.ip(m)) - mean(ichq(max(1, floor(find(m, 1)/Np)):min(end, floor(find(m, 1, 'last')/Np)))));
    arows(end+1, :) = {sprintf('%s KCL residual i_Aout-(i_p-i_ch) [A] (info)', win{w, 1}), kcl, 0, NaN, 'info'}; %#ok<AGROW>
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
fid = fopen(fullfile(resDir, ['TB07_' fnm '_summary.txt']), 'w');
o2(fid, 'TB07 integrated model (charging), case %s (V_bat %.0f V, bus total %.1f -> %.1f kW, charger %.1f -> %.1f A at %.1f ms in %.0f us), dt %.2f ns, wall %.0f s\n', ...
    cn, TB.vbat, TB.P0tot/1e3, TB.P1tot/1e3, TB.chg_prm(1), TB.chg_prm(2), 1e3*TB.t_step, 1e6*TB.chg_prm(4), 1e9*TB.dt, wall);
o2(fid, '(1) Tier-%d limits on the circuit (t > %.1f ms):\n', TB.tier, 1e3*TB.t_eval);
o2(fid, '    v_bus period mean %.2f-%.2f V, max |i_p| %.2f A, i_h %.2f/%.2f A, link %.2f A / %.0f W, v_link %.2f-%.2f V, max |v_s| %.1f V\n', ...
    min(pr(ev, 1)), max(pr(ev, 1)), max(pr(ev, 9)), max(pr(ev, 7)), min(pr(ev, 8)), max(abs(pr(ev, 5))), max(abs(pr(ev, 6))), ...
    min(pr(ev, 4)), max(pr(ev, 4)), max(pr(ev, 12)));
fn = fieldnames(T1);
for k = 1:numel(fn), o2(fid, '    %-16s %s\n', fn{k}, pf(T1.(fn{k}))); end
o2(fid, '    last-1ms ripple %.3f V (information only at the %.2f ns gate grid; limit 0.1 V met at 0.625 ns in TB04B)\n', ripple, 1e9*TB.dt);
o2(fid, '(2) agreement with the Stage B verification model (E16 switching: E12 engine, source V_bat/2 + R_A*i_ch, R = R_A + 3 mOhm, Stage C as CPL):\n');
o2(fid, '    %-46s %11s %11s %9s %7s\n', 'metric', 'Simscape', 'model', 'diff', 'result');
for k = 1:size(cmp, 1)
    a = cmp{k, 2}; b = cmp{k, 3}; tol = cmp{k, 4}; use = cmp{k, 5};
    d = a - b; ok = abs(d) <= tol;
    if isnan(tol), rr = 'info'; elseif ~use, rr = ternary(ok, 'info(ok)', 'info'); else, rr = pf(ok); equiv = equiv && ok; end
    o2(fid, '    %-46s %11.4g %11.4g %+9.3g %7s\n', cmp{k, 1}, a, b, d, rr);
end
o2(fid, '(3) Stage A (verification model E1, zero-crossing tracking, 8 phases, same mean output current i_p - i_ch):\n');
o2(fid, '    %-46s %11s %11s %9s %7s\n', 'metric', 'Simscape', 'E1', 'diff', 'result');
for k = 1:size(arows, 1)
    a = arows{k, 2}; b = arows{k, 3}; tol = arows{k, 4};
    switch arows{k, 5}
        case 'limit', rr = pf(a <= tol);
        case 'okz',   rr = 'PASS';
        case 'ngz',   rr = 'FAIL';
        case 'abs',   rr = pf(abs(a - b) <= tol);
        otherwise,    rr = 'info';
    end
    o2(fid, '    %-46s %11.4g %11.4g %+9.3g %7s\n', arows{k, 1}, a, b, a - b, rr);
end
o2(fid, '    turn-off current <= 5 %% of peak or <= 2 A, V_A mean +-0.3 V vs E1, phase sharing <= 5 %%\n');
o2(fid, '(4) Stage C: v_48 %.3f-%.3f V after %.1f ms (limit 47.04-48.96 V), final mean %.3f V (TB05 at %.1f ns: %.3f V, tol 0.15 V),\n', ...
    C.vo_min, C.vo_max, 1e3*TB.t_eval, C.vo_final, 1e9*TB.dt, TB.vo_TB05);
o2(fid, '    max deviation of period-mean v_48 after the step %.3f V (info), Stage C input power %.0f W before / %.0f W at end (CPL estimate used %.0f W): %s\n', ...
    C.vo_step_dev, C.pin_pre, C.pin_final, TB.Pc_in, pf(cpass));
o2(fid, '(5) charger current %.1f -> %.1f A, path current before/end %.2f / %.2f A (charging current does not pass the series port)\n', ...
    mean(ichq(1:min(end, round(TB.t_step/T)))), ichq(end), mean(pr(pre, 2)), mean(pr(fin, 2)));
verdict = ternary(t1pass && equiv && apass && cpass, 'PASS', 'FAIL');
o2(fid, 'VERDICT %s: %s (Tier-%d %s, E16 agreement %s, Stage A %s, Stage C %s)\n', fnm, verdict, TB.tier, pf(t1pass), pf(equiv), pf(apass), pf(cpass));
fclose(fid);
S = struct('case', cn, 'dt_ns', 1e9*TB.dt, 'verdict', verdict, 'tier1', T1, 'tier1_pass', t1pass, 'equiv_pass', equiv, ...
    'stageA_pass', apass, 'stageC_pass', cpass, 'ripple_last1ms_V', ripple, 'stageA', A, 'stageC', C, 'wall_s', wall, ...
    'date', char(datetime('now')), 'matlab', version);
S.compare = cell2struct(cmp, {'metric', 'simscape', 'model', 'tol', 'judged'}, 2);
S.stageA_compare = cell2struct(arows, {'metric', 'simscape', 'E1', 'tol', 'type'}, 2);
fid = fopen(fullfile(resDir, ['TB07_' fnm '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
writematrix([tq pr vAm vom pcin], fullfile(resDir, ['TB07_' fnm '_periods.csv']));

% ---- 그림 1: 응답(주기 평균) -------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 1000 1050]);
tl = tiledlayout(f, 6, 1, 'TileSpacing', 'compact');
ms = 1e3*tq;
nexttile; hold on; grid on; plot(ms, pr(:, 1), 'LineWidth', 1.4); plot(ms, py.vb, '--', 'LineWidth', 1.2);
yline([392 408], ':'); ylabel('v_{bus} [V]'); legend('Simscape (integrated, charging)', 'E16 (charging-mode source, CPL)', 'Location', 'southeast');
title('bus voltage (5 \mus period mean)');
nexttile; hold on; grid on; plot(ms, pr(:, 2), 'LineWidth', 1.4); plot(ms, py.ip, '--', 'LineWidth', 1.2);
plot(ms, pr(:, 3), 'LineWidth', 1.1); plot(ms, py.ih, '--', 'LineWidth', 1.0);
ylabel('[A]'); legend('i_p Simscape', 'i_p E12', 'i_h Simscape', 'i_h E12', 'Location', 'southeast'); title('path and filter current');
nexttile; hold on; grid on; plot(ms, pr(:, 4), 'LineWidth', 1.4); plot(ms, py.vl, '--', 'LineWidth', 1.2);
ylabel('v_{link} [V]'); title('floating link voltage');
nexttile; hold on; grid on; plot(ms, pr(:, 5), 'LineWidth', 1.4); plot(ms, py.il, '--', 'LineWidth', 1.2);
ylabel('[A]'); title('DAB link current (period mean)');
nexttile; hold on; grid on; nq = min(numel(ichq), numel(tq)); ich_q = ichq(1:nq); ich_q(end+1:numel(tq)) = ich_q(end);
yyaxis left; plot(ms, vAm, 'LineWidth', 1.4); plot(ms, TB.vbat/2 + TB.A.RA*(ich_q(:) - py.ip), '--', 'LineWidth', 1.2); ylabel('V_A [V]');
yyaxis right; plot(ms, ich_q, 'LineWidth', 1.0); ylabel('i_{ch} [A]');
legend('V_A Simscape (Stage A 4 modules)', 'V_{bat}/2 + 2.55 m\Omega(i_{ch} - i_p) (E16)', 'charger current', 'Location', 'east');
title('Stage A output node V_A and charger current');
nexttile; hold on; grid on; plot(ms, vom, 'LineWidth', 1.4); yline(TB.vo_TB05, '--'); yline([47.04 48.96], ':');
ylabel('v_{48} [V]'); xlabel('t [ms]'); title('Stage C 48 V output (dashed: TB05 at the same step size, dotted: \pm2 %)');
title(tl, sprintf('TB07 %s: V_{bat} %.0f V, bus %.0f \\rightarrow %.0f kW, charger %.0f \\rightarrow %.0f A at %.0f ms', strrep(fnm, '_', ' '), ...
    TB.vbat, TB.P0tot/1e3, TB.P1tot/1e3, TB.chg_prm(1), TB.chg_prm(2), 1e3*TB.t_step));
exportgraphics(f, fullfile(resDir, ['TB07_' fnm '_response.png']), 'Resolution', 150); close(f);

% ---- 그림 2: Stage A 공진전류(끝 구간 마지막 3주기) ---------------------------------------------------------
Tr = 2*pi*sqrt(TB.A.Lr*TB.A.Cfly);                         % 공칭 공진 주기(약 6.7 µs)
z = D.t > TB.t_end - 3*Tr;
f = figure('Visible', 'off', 'Position', [100 100 1000 700]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
tz = 1e6*(D.t(z) - D.t(find(z, 1)));
nexttile; hold on; grid on;
for p = 1:8, plot(tz, D.(sprintf('iA%d', p))(z), 'LineWidth', 1.0); end
ylabel('i_C [A]'); legend(arrayfun(@(p) sprintf('phase %d', p), 1:8, 'UniformOutput', false), 'Location', 'eastoutside', 'NumColumns', 2);
title('Stage A resonant currents, 8 phases (zero-crossing tracking, interleaved T/16)');
nexttile; hold on; grid on; stairs(tz, D.st1(z), 'LineWidth', 1.1); stairs(tz, D.st2(z) + 0.05, 'LineWidth', 1.1); stairs(tz, D.st5(z) + 0.1, 'LineWidth', 1.1);
ylabel('segment'); yticks([0 1 2]); yticklabels({'dead', 'S1·S3', 'S2·S4'}); legend('phase 1', 'phase 2', 'phase 5', 'Location', 'eastoutside');
nexttile; hold on; grid on;
yyaxis left;  plot(tz, D.vA(z), 'LineWidth', 1.2); ylabel('V_A [V]');
yyaxis right; plot(tz, D.ip(z), 'LineWidth', 1.0); ylabel('i_p [A]');
legend('V_A', 'i_p', 'Location', 'eastoutside'); xlabel('t [\mus]'); title('V_A node voltage and path current');
title(tl, sprintf('TB07 %s: Stage A 4 modules at the end of the run (turn-off current max %.2f A, ratio max %.2f %%)', strrep(fnm, '_', ' '), ...
    max(A.final.ioff), 100*max(A.final.zcs)));
exportgraphics(f, fullfile(resDir, ['TB07_' fnm '_stageA.png']), 'Resolution', 150); close(f);
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
