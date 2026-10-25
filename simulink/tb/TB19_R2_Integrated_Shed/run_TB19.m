function run_TB19(runList)
%RUN_TB19  TB19(R2-W460 통합 강등 + Stage A 경부하 위상 셰딩)을 사례별로 실행하고 판정한다.
%
%   run_TB19          % 사례 1–2(사례당 약 16분)
%   회로·사례·기준값은 TB17과 같고 Stage A 게이트만 셰딩 게이트다(E24·TB18과 같은 문턱).
%   판정(시험 전에 고정)
%     TB17과 같은 항목: 보호·강등(TB13과 같음), 48 V ±2 %(강등 내내), Stage C 전류·ZVS·끝 DCX 이득
%     Stage A(바뀐 것)
%       사건 전(1.3–1.5 ms, 두 위상): 위상별 턴오프 전류/피크 ≤ 5 %, V_A − 기준 ≤ 0.3 V, 위상 전류 차 ≤ 5 %
%       끝 0.2 ms: 기준 위상 수(사례 A 위상 하나, B 두 위상)로 운전, 턴오프 전류/피크 ≤ 5 %, V_A − 기준 ≤ 0.3 V,
%                  (두 위상이면) 위상 전류 차 ≤ 5 %. 기준은 데드타임 소멸 처리를 켠 E24 모델(ref/TB19_<사례>_stageA_df.json)
%       (T1) 1 ms 이후 모든 턴오프: |i_off| ≤ max(5 % × 그 반주기 첨두, 1.0 A)(E24·TB18과 같음)
%       (T2) 위상 첨두 ≤ 76.4 A(위상 정격 첨두)
%       (T4) 멈추기 취소(모드 3 → 2) 없음, 끝 셰딩 모드가 기준 위상 수와 같음
%   결과: results/TB19_<사례>_summary.txt·json, _periods.csv, _avg10us.csv, _response.png, _stageA.png, TB19_summary.txt·json

here = fileparts(mfilename('fullpath'));
mdl  = 'TB19_R2_Integrated_Shed';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {'A_1008V_hbopen', 'B_930V_hbopen'};
if nargin < 1 || isempty(runList), runList = 1:2; end
tStop = [];                                                % 점검 실행(smoke_TB19): 기본 작업공간 TB19_tend까지만, 결과는 results/smoke
if evalin('base', 'exist(''TB19_tend'', ''var'')')
    tStop = evalin('base', 'TB19_tend'); resDir = fullfile(resDir, 'smoke');
    if ~exist(resDir, 'dir'), mkdir(resDir); end
end
load_system(fullfile(here, [mdl '.slx']));
res = {};
for r = runList
    cn = R{r};
    assignin('base', 'TB19_case', cn);
    run(fullfile(here, 'TB19_init.m'));
    TB = evalin('base', 'TB');
    if ~isempty(tStop), TB.t_end = tStop; end
    tic; out = sim(mdl, 'StopTime', num2str(TB.t_end, '%.9g')); wall = toc;
    S = evaluate(out, TB, refDir, cn, resDir, wall);
    res{end+1} = S; %#ok<AGROW>
    fprintf('%s done (%.0f s): %s\n', cn, wall, S.verdict);
    clear out
end
evalin('base', 'clear TB19_case');
fid = fopen(fullfile(resDir, 'TB19_summary.txt'), 'w');
o2(fid, 'TB19 R2-W460 integrated (Stage A module 1 + window Stage B with H-bridge-open degrade + regulated Stage C), reference E23 degrade / E17 / E1\n');
o2(fid, '%-16s %-6s %-9s %-9s %-10s %-9s %-11s %s\n', 'case', 'result', 'vo_min', 'vo_max', 'bus_min', 'bus_max', 'final', 'failed');
allPass = true;
for k = 1:numel(res)
    S = res{k};
    o2(fid, '%-16s %-6s %-9.3f %-9.3f %-10.1f %-9.1f %-11s %s\n', S.case, S.verdict, S.vo_min, S.vo_max, S.peaks.bus_min_V, ...
        S.peaks.bus_max_V, S.final_state, strjoin(S.failed, ', '));
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
o2(fid, 'TB19 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
fclose(fid);
fid = fopen(fullfile(resDir, 'TB19_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true)); fclose(fid);
end

% =======================================================================================================
function S = evaluate(out, TB, refDir, cn, resDir, wall)
te = TB.t_event;
% ---- Stage B 쪽(5 ns 간격) ------------------------------------------------------------------------------
t = out.t(:); dts = t(2) - t(1);
vb = double(out.vbus(:)); ip = double(out.ip(:)); ih = double(out.ih(:)); vs = double(out.vs(:)); vl = double(out.vlink(:));
ib = double(out.ibyp(:)); ik = double(out.ibrk(:)); iL = double(out.iL(:));
vb(1) = vb(2); ip(1) = ip(2); ih(1) = ih(2); vs(1) = vs(2); vl(1) = vl(2); ib(1) = ib(2); ik(1) = ik(2); iL(1) = iL(2);
sup = cols(out.sup, 12);                                   % 5 µs마다(표본 k = 0, 1, …)
T = 5e-6; np5 = round(T/dts); nper = floor(numel(t)/np5);
pr = zeros(nper, 14);   % [평균 vb, 평균 ip, 평균 ih, 평균 vl, 평균 vs, max|ip|, max|ih|, max|vs|, max vl, max|ib|, 평균 제동 전력, min vb,
                        %  max|i_L|(DAB 1차), ∫|v_s·i_byp|dt]
for q = 1:nper
    k = (q-1)*np5 + (1:np5);
    pr(q, :) = [mean(vb(k)), mean(ip(k)), mean(ih(k)), mean(vl(k)), mean(vs(k)), max(abs(ip(k))), max(abs(ih(k))), ...
                max(abs(vs(k))), max(vl(k)), max(abs(ib(k))), mean(vl(k).*ik(k)), min(vb(k)), max(abs(iL(k))), ...
                sum(abs(vs(k).*ib(k)))*dts];
end
tq = (1:nper)'*T;
ts = (0:size(sup, 1)-1)'*T;
stq = interp1(ts, sup(:, 11), tq - T, 'previous', 'extrap');
shedq = interp1(ts, sup(:, 10), tq - T, 'previous', 'extrap');
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
% ---- 판정 1: 보호·강등(TB13과 같음, 사건 시각만 te) ---------------------------------------------------------------
post = t >= te;
loaded = shedq < 0.5;
L = struct();
L.current_100A = max(abs(ip(post))) <= 100 && max(abs(ih(post))) <= 100;
L.series_120V = max(abs(vs(post))) <= 120;
L.link_120V = max(vl(post)) <= 120;
L.bypass_current = max(abs(ib(post))) <= 329;
L.bus_ge_260 = min(pr(tq > te, 12)) >= 260;
L.degraded_reached = strcmp(final_state, 'DEGRADED');
L.class_upper_while_400V_loads = max(pr(loaded & tq > te, 1)) <= TB.upper;
fq = ismember(stq, [9 10 11]) & tq > te;
L.dab_peak_1p5x_rated = ~any(fq) || nt*max(pr(fq, 13)) <= 1.5*TB.rated_pk;
% ---- Stage C·Stage A 쪽(10 ns 간격) --------------------------------------------------------------------------
t4 = out.t4(:); dt4 = t4(2) - t4(1);
X = double([out.iin(:) out.iLb(:) out.vI(:) out.vo(:) out.ix(:) out.iload(:) out.vA(:) out.iAo(:)]);
X(1, :) = X(2, :);
ir2 = double(out.ir2(:)); vl1 = double(out.vleg1(:)); vls1 = double(out.vlegs1(:));
gq1 = double(out.gq1(:)); gq2 = double(out.gq2(:)); gs1 = double(out.gs1(:)); gs2 = double(out.gs2(:));
n10 = round(10e-6/dt4); m10 = floor(numel(t4)/n10);
A10 = zeros(m10, 10);                                      % [t_끝, 10 µs 평균 iin iLb vI vo ix iload vA iAo, vbus]
for q = 1:m10
    k = (q-1)*n10 + (1:n10);
    A10(q, 1:9) = [t4(k(end)) mean(X(k, :), 1)];
end
nb10 = round(10e-6/dts);
for q = 1:m10
    k = (q-1)*nb10 + (1:nb10); k = k(k <= numel(vb));
    A10(q, 10) = mean(vb(k));
end
writematrix(A10, fullfile(resDir, ['TB19_' cn '_avg10us.csv']));
t10 = A10(:, 1);
win_c = t10 >= te - 0.2e-3;
vo_min = min(A10(win_c, 5)); vo_max = max(A10(win_c, 5));
L.vo_contract = vo_min >= TB.band(1) && vo_max <= TB.band(2);
w100 = round(100e-6/dt4);
ixa = movmean(X(:, 5), w100);
ix_avg_max = max(abs(ixa(t4 >= te - 0.2e-3)));
dev_pk = max(abs(ir2(t4 >= te - 0.2e-3)))/2;
L.stageC_current = ix_avg_max <= 130*1.05 && dev_pk <= TB.pulse_rating_secondary;
wz = t4 > 1.0e-3;
[zp, np1] = zvs_check(t4, gq1, gq2, vl1, X(:, 3), wz);
[zs, ns1] = zvs_check(t4, gs1, gs2, vls1, X(:, 4), wz);
okz = (np1 + ns1) > 0;
if np1 > 0, okz = okz && zp <= 0.05*mean(X(wz, 3)); end
if ns1 > 0, okz = okz && zs <= 0.05*mean(X(wz, 4)); end
L.stageC_zvs = okz;
fin10 = t10 > t10(end) - 0.2e-3;
gain_end = TB.C.n*mean(A10(fin10, 5))/mean(A10(fin10, 4));
L.dcx_gain_end = abs(gain_end - 1) <= 0.03;
% Stage A(2.5 ns, 시간은 표본 번호로)
iA1 = double(out.iA1(:)); iA2 = double(out.iA2(:)); st1 = double(out.st1(:)); st2 = double(out.st2(:));
tA = (0:numel(iA1)-1)'*TB.dt;
SA = jsondecode(fileread(fullfile(refDir, ['TB19_' cn '_stageA_df.json'])));     % E24 모델(데드타임 소멸 처리) 기준
shd = double(squeeze(out.shed)); if size(shd, 2) ~= 2, shd = shd.'; end
t4s = (0:size(shd, 1)-1)'*(t4(2) - t4(1));
wins = {'pre', te - 0.2e-3, te; 'final', tA(end) - 0.2e-3, tA(end)};
SAc = struct();
for wv = 1:2
    m = tA > wins{wv, 2} & tA <= wins{wv, 3};
    ref = SA.(wins{wv, 1});
    [zz, pk, io, noff] = zcs_window(iA1(m), iA2(m), st1(m), st2(m));
    mv = t10 > wins{wv, 2} & t10 <= wins{wv, 3};
    vAm = mean(A10(mv, 8));
    nph = sum(noff > 0);                                   % 이 구간에서 스위칭한 위상 수
    if ref.phases == 1
        sh = NaN; zuse = zz(1);
        ok = nph == 1 && noff(2) == 0 && zuse <= 0.05 && abs(vAm - ref.vA_mean) <= 0.3;
    else
        sh = abs(io(1) - io(2))/abs(mean(io)); zuse = max(zz);
        ok = nph == 2 && zuse <= 0.05 && abs(vAm - ref.vA_mean) <= 0.3 && sh <= 0.05;
    end
    SAc.(wins{wv, 1}) = struct('zcs', zz, 'Ipk', pk, 'io', io, 'noff', noff, 'phases', nph, 'phases_ref', ref.phases, ...
        'vA_mean', vAm, 'vA_ref', ref.vA_mean, 'zcs_ref', ref.zcs(:)', 'sharing', sh, 'iAo_mean', mean(A10(mv, 9)), ...
        'iout_ref', ref.iout, 'pass', ok);
end
L.stageA_pre = SAc.pre.pass;
L.stageA_final = SAc.final.pass;
% (T1)·(T2)·(T4) 셰딩 과도
T1bad = 0; T1n = 0; T1worst = 0;
for p = 1:2
    if p == 1, ii = iA1; ss = st1; else, ii = iA2; ss = st2; end
    off = find(ss(1:end-1) ~= 0 & ss(2:end) == 0); on = find(ss(1:end-1) == 0 & ss(2:end) ~= 0) + 1;
    for jj = 1:numel(off)
        o = off(jj); if tA(o) < 1.0e-3, continue; end
        k0 = on(find(on <= o, 1, 'last')); if isempty(k0), continue; end
        pkh = max(abs(ii(k0:o))); T1n = T1n + 1;
        T1worst = max(T1worst, abs(ii(o)));
        if abs(ii(o)) > max(0.05*pkh, TB.i_abs), T1bad = T1bad + 1; end
    end
end
pkA = max(max(abs([iA1(tA >= 1.0e-3) iA2(tA >= 1.0e-3)])));
L.T1_turnoff = T1bad == 0;
L.T2_phaseA_peak = pkA <= TB.rated_pk_A;
dm = find(diff(shd(:, 1)) ~= 0);
Esh = [1e3*t4s(dm + 1), shd(dm + 1, 1)];
n_cancel = 0;
if ~isempty(Esh)
    prevm = [2; Esh(:, 2)];
    n_cancel = sum(prevm(1:end-1) == 3 & Esh(:, 2) == 2);
end
mode_end = shd(end, 1);
L.T4_shedding = n_cancel == 0 && ((SA.final.phases == 1 && mode_end == 1) || (SA.final.phases == 2 && mode_end == 2));
fn = fieldnames(L); lpass = all(cellfun(@(f) L.(f), fn));
failed = fn(~cellfun(@(f) L.(f), fn))';
% ---- 정보: Stage A 전류 급변 중 ZCS(50 µs 창), Stage C 입력 전력, E23·E17 대조 ----------------------------------------
Wz = 50e-6; nw = floor(tA(end)/Wz);
zt = nan(nw, 6);   % [창 끝 시각, max ZCS(창 피크 기준), Stage A 출력 평균, max |i|, max ZCS(반주기별), max 턴오프 전류 [A]]
for q = 1:nw
    m = tA > (q-1)*Wz & tA <= q*Wz;
    [zz, pk, ~, ~, zc, ioff] = zcs_window(iA1(m), iA2(m), st1(m), st2(m));
    mv = t10 > (q-1)*Wz & t10 <= q*Wz;
    zt(q, :) = [q*Wz, max(zz), mean(A10(mv, 9)), max(pk), max(zc), max(ioff)];
end
qa = zt(:, 1) > 1.0e-3;
ztq = zt(qa, :); [zmax_tr, jz] = max(ztq(:, 5));          % 반주기별 ZCS의 최대(전류 급변 중)
ioff_max = max(ztq(:, 6));
pinC = A10(:, 2).*A10(:, 10);
C = readmatrix(fullfile(refDir, ['TB19_' cn '_stageC.csv']));   % E23 degrade: t vbus iL vI ix vo d mode ibat iin pload iref(1 µs)
M = jsondecode(fileread(fullfile(refDir, ['TB19_' cn '_metrics.json'])));
qc = C(:, 1) >= te - 0.2e-3;
cmpC = struct('vo_min_circuit', vo_min, 'vo_min_E23', min(C(qc, 6)), 'vo_max_circuit', vo_max, 'vo_max_E23', max(C(qc, 6)), ...
    'vo_end_circuit', mean(A10(fin10, 5)), 'vo_end_E23', mean(C(C(:, 1) > C(end, 1) - 0.2e-3, 6)));
A = readmatrix(fullfile(refDir, ['TB19_' cn '_avg.csv']));   % E17 [t ip vs vbus ih vlink idab ibyp loads bridge Pbrk], 1 µs
qi = ceil(A(:, 1)/T - 1e-9); ok = qi >= 1 & qi <= nper;
rp = nan(nper, 6);
colA = [4 2 5 6 3 11];
for j = 1:6, rp(:, j) = accumarray(qi(ok), A(ok, colA(j)), [nper 1], @mean, NaN); end
v = ~isnan(rp(:, 1)) & tq > te;
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
cmp(end+1, :) = add('48 V min (10 us mean, E23) [V]', cmpC.vo_min_circuit, cmpC.vo_min_E23, 0.5);
cmp(end+1, :) = add('48 V max (10 us mean, E23) [V]', cmpC.vo_max_circuit, cmpC.vo_max_E23, 0.5);
cmp(end+1, :) = add('48 V end (E23) [V]', cmpC.vo_end_circuit, cmpC.vo_end_E23, 0.1);
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
% ---- 요약 ------------------------------------------------------------------------------------------------
fid = fopen(fullfile(resDir, ['TB19_' cn '_summary.txt']), 'w');
o2(fid, 'TB19 case %s (V_bat %.0f V, 400 V load %.0f kW + Stage C %.0f W at 48 V, event %s at %.1f ms), dt %.2f ns, wall %.0f s\n', ...
    cn, TB.vbat, TB.P0/1e3, TB.P48, TB.event, 1e3*te, 1e9*TB.dt, wall);
o2(fid, '(1) criteria:\n');
for k = 1:numel(fn), o2(fid, '    %-30s %s\n', fn{k}, ternary(L.(fn{k}), 'PASS', 'FAIL')); end
o2(fid, '    protection: |i_p| %.1f A, |i_h| %.1f A, |v_s| %.1f V, v_link %.1f-%.1f V, |i_byp| %.1f A; bus(5 us) %.1f-%.1f V (loaded max %.1f V)\n', ...
    max(abs(ip(post))), max(abs(ih(post))), max(abs(vs(post))), min(vl(post)), max(vl(post)), max(abs(ib(post))), ...
    min(pr(tq > te, 12)), max(pr(tq > te, 1)), max(pr(loaded & tq > te, 1)));
if any(fq)
    o2(fid, '    DAB link-side peak in states 9-11: n|i_L| %.1f A (limit 1.5x %.1f A)\n', nt*max(pr(fq, 13)), 1.5*TB.rated_pk);
end
o2(fid, '    soft bypass: entry %.3f ms (v_link %.2f V, v_s %.2f V), duration %.3f ms, device energy %.4f J, path peak %.1f A\n', ...
    soft.entry_ms, soft.vl_V, soft.vs_V, soft.ms, soft.energy_J, soft.path_peak_A);
o2(fid, '    48 V (10 us mean, from %.1f ms): %.3f-%.3f V, band %.2f-%.2f V; E23 %.3f-%.3f V\n', 1e3*(te - 0.2e-3), vo_min, vo_max, ...
    TB.band(1), TB.band(2), cmpC.vo_min_E23, cmpC.vo_max_E23);
o2(fid, '    Stage C: output 100 us mean max %.1f A, secondary device peak %.1f A; ZVS primary %.2f V (%d edges), secondary %.2f V (%d edges); end DCX gain %.4f\n', ...
    ix_avg_max, dev_pk, zp, np1, zs, ns1, gain_end);
o2(fid, '    Stage C input power (10 us mean, after event): %.0f-%.0f W (E23 avg model %.0f-%.0f W)\n', ...
    min(pinC(t10 > te)), max(pinC(t10 > te)), M.stageC.pin_min, M.stageC.pin_max);
for wv = {'pre', 'final'}
    a = SAc.(wv{1});
    o2(fid, '    Stage A %-5s: phases %d (ref %d), ZCS %.2f / %.2f %% (ref %s %%), Ipk %.1f / %.1f A, V_A %.3f V (ref %.3f V), sharing %.2f %%, i_A %.2f A (ref %.2f A)\n', ...
        wv{1}, a.phases, a.phases_ref, 100*a.zcs(1), 100*a.zcs(2), mat2str(round(100*a.zcs_ref, 2)), a.Ipk(1), a.Ipk(2), a.vA_mean, ...
        a.vA_ref, 100*a.sharing, a.iAo_mean, a.iout_ref);
end
o2(fid, '    Stage A shedding: turn-offs after 1 ms %d, (T1) violations %d, max |i_off| %.2f A; phase peak %.1f A (rated %.1f A); cancels %d, end mode %d\n', ...
    T1n, T1bad, T1worst, pkA, TB.rated_pk_A, n_cancel, mode_end);
o2(fid, '    shedding events [ms, mode]: %s\n', mat2str(round(Esh, 3)));
o2(fid, '    (info) Stage A after 1 ms (50 us windows): max half-cycle ZCS %.2f %% at %.3f ms (i_A %.1f A, window phase peak %.1f A); max turn-off current %.2f A; i_A range %.1f to %.1f A\n', ...
    100*zmax_tr, 1e3*ztq(jz, 1), ztq(jz, 3), ztq(jz, 4), ioff_max, min(ztq(:, 3)), max(ztq(:, 3)));
o2(fid, '(2) comparison with E17 / E23 (info):\n');
o2(fid, '    %-44s %11s %11s %9s %9s\n', 'metric', 'Simscape', 'reference', 'diff', 'result');
for k = 1:size(cmp, 1)
    a = cmp{k, 2}; b = cmp{k, 3}; tol = cmp{k, 4};
    if isnan(tol), rr = 'info'; else, rr = ternary(abs(a - b) <= tol, 'ok', 'over'); end
    o2(fid, '    %-44s %11.5g %11.5g %+9.3g %9s\n', cmp{k, 1}, a, b, a - b, rr);
end
o2(fid, '    final state: %s\n', final_state);
fclose(fid);
S = struct('case', cn, 'event', TB.event, 'limits', L, 'verdict', ternary(lpass, 'PASS', 'FAIL'), 'failed', {failed}, ...
    'transitions', ev, 'final_state', final_state, 'dab', dab, 'soft', soft, 'vo_min', vo_min, 'vo_max', vo_max, ...
    'peaks', struct('ip_A', max(abs(ip(post))), 'ih_A', max(abs(ih(post))), 'vs_V', max(abs(vs(post))), 'vlink_max_V', max(vl(post)), ...
                    'ibyp_A', max(abs(ib(post))), 'bus_min_V', min(pr(tq > te, 12)), 'bus_max_V', max(pr(tq > te, 1)), ...
                    'bus_max_loaded_V', max(pr(loaded & tq > te, 1)), 'brake_J', sum(pr(:, 11))*T), ...
    'stageC', struct('ix_avg100_max', ix_avg_max, 'dev_peak_A', dev_pk, 'zvs_primary_V', zp, 'zvs_primary_n', np1, ...
                     'zvs_secondary_V', zs, 'zvs_secondary_n', ns1, 'gain_end', gain_end, 'pin_min', min(pinC(t10 > te)), ...
                     'pin_max', max(pinC(t10 > te)), 'E23', cmpC), ...
    'stageA', SAc, 'shedding', struct('events_ms', Esh, 'n_cancel', n_cancel, 'mode_end', mode_end, 'T1_n', T1n, 'T1_bad', T1bad, ...
                     'ioff_max', T1worst, 'phase_peak', pkA), 'stageA_transient', struct('zcs_halfcycle_max', zmax_tr, 'ms', 1e3*ztq(jz, 1), 'iA', ztq(jz, 3), 'Ipk', ztq(jz, 4), ...
                     'ioff_max_A', ioff_max, 'iA_min', min(ztq(:, 3)), 'iA_max', max(ztq(:, 3))), ...
    'wall_s', wall, 'dt_ns', 1e9*TB.dt, 'date', char(datetime('now')));
S.compare = cell2struct(cmp, {'metric', 'simscape', 'reference', 'tol'}, 2);
fid = fopen(fullfile(resDir, ['TB19_' cn '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
writematrix([tq pr stq shedq], fullfile(resDir, ['TB19_' cn '_periods.csv']));
writematrix(zt, fullfile(resDir, ['TB19_' cn '_stageA_zcs50us.csv']));
% ---- 그림 ------------------------------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [50 50 1100 1150]);
tl = tiledlayout(f, 5, 1, 'TileSpacing', 'compact');
ms_ = 1e3*tq; mr = 1e3*A(:, 1);
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
plot(ax, 1e3*t10, A10(:, 5), 'b', 'LineWidth', 1.2); plot(ax, 1e3*C(:, 1), C(:, 6), 'r--');
yline(ax, TB.band, 'k:'); ylabel(ax, 'v_o [V]'); legend(ax, '회로(10 µs 평균)', 'E23(E17 버스 → E22)', 'Location', 'best');
title(ax, '48 V 출력(점선: ±2 %)');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
plot(ax, ms_, pr(:, 1), 'b', 'LineWidth', 1.3); plot(ax, mr, A(:, 4), 'r--'); plot(ax, 1e3*t10, A10(:, 8), 'c');
yline(ax, TB.upper, 'k:'); ylabel(ax, '[V]'); legend(ax, 'v_{bus} 회로(5 µs)', 'v_{bus} E17', 'v_A 회로', 'Location', 'best');
title(ax, '버스 전압과 V_A(점선: B_{470} 상한)');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
plot(ax, ms_, pr(:, 2), 'b', 'LineWidth', 1.2); plot(ax, mr, A(:, 2), 'r--'); plot(ax, 1e3*t10, A10(:, 9), 'c');
plot(ax, ms_, pr(:, 3), 'm'); plot(ax, 1e3*t10, A10(:, 2), 'g');
ylabel(ax, '[A]'); legend(ax, 'i_p 경로', 'i_p E17', 'Stage A 출력', 'i_h', 'Stage C 입력', 'Location', 'best');
title(ax, '전류(평균)');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
plot(ax, ms_, pr(:, 4), 'b', 'LineWidth', 1.2); plot(ax, mr, A(:, 6), 'r--'); plot(ax, ms_, -pr(:, 5), 'm'); plot(ax, mr, -A(:, 3), 'k--');
ylabel(ax, '[V]'); legend(ax, 'v_{link}', 'v_{link} E17', '-v_s', '-v_s E17', 'Location', 'best'); title(ax, '링크·직렬 전압');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
yyaxis(ax, 'left'); stairs(ax, 1e3*ts, sup(:, 11), 'LineWidth', 1.2); ylabel(ax, '상태'); ylim(ax, [-0.5 13.5]);
yyaxis(ax, 'right'); plot(ax, ms_, pr(:, 11)/1e3); ylabel(ax, '제동 전력 [kW]');
xlabel(ax, '시간 [ms]'); title(ax, '상태(3 창, 9 HB 유지, 10 붕괴, 11 소프트 바이패스, 12 강등)');
title(tl, sprintf('TB19 %s', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB19_' cn '_response.png']), 'Resolution', 130); close(f);
f = figure('Visible', 'off', 'Position', [50 50 1100 800]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
yyaxis(ax, 'left'); plot(ax, 1e3*zt(:, 1), zt(:, 3)); ylabel(ax, 'Stage A 출력 평균 [A]');
yyaxis(ax, 'right'); plot(ax, 1e3*zt(:, 1), 100*zt(:, 5), '.'); yline(ax, 5, ':'); ylabel(ax, 'ZCS(반주기별, 50 µs 창 최대) [%]');
plot(ax, 1e3*t4s(1:200:end), 10*shd(1:200:end, 1), 'g-');   % 셰딩 모드 × 10(20 둘, 30 멈추는 중, 10 하나)
xlabel(ax, '시간 [ms]'); title(ax, 'Stage A 전류 급변과 영전류 스위칭');
for wv = 1:2
    k0 = find(tA >= wins{wv, 3} - 20e-6, 1); k1e = find(tA <= wins{wv, 3}, 1, 'last');
    ax = nexttile(tl); plot(ax, 1e6*tA(k0:k1e), iA1(k0:k1e), 1e6*tA(k0:k1e), iA2(k0:k1e)); grid(ax, 'on');
    ylabel(ax, '위상 전류 [A]'); legend(ax, '위상 1', '위상 2', 'Location', 'best');
    a = SAc.(wins{wv, 1});
    title(ax, sprintf('%s 마지막 20 µs: 위상 %d개, ZCS %.2f / %.2f %%(기준 %s %%)', ternary(wv == 1, '사건 전', '끝'), ...
        a.phases, 100*a.zcs(1), 100*a.zcs(2), mat2str(round(100*a.zcs_ref, 2))));
end
xlabel(ax, '시간 [µs]');
title(tl, sprintf('TB19 %s: Stage A', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB19_' cn '_stageA.png']), 'Resolution', 130); close(f);
fprintf('VERDICT %s: %s\n', cn, S.verdict);
end

function [zz, pk, io, noff, zc, ioff] = zcs_window(i1, i2, s1, s2)
% 위상별 ZCS = 턴오프 순간 전류(마지막 도통 표본) / 창 안 피크(TB01·TB06·TB16과 같은 정의), 위상 평균 출력전류
% zc: 반주기별 ZCS(턴오프 전류 / 그 도통 구간의 피크, 피크 ≥ 1 A인 구간)의 최대 — 전류가 급변하는 창의 정보용
% ioff: 턴오프 순간 전류 크기의 최대 [A]
I = [i1 i2]; Sg = [s1 s2];
zz = nan(1, 2); pk = zeros(1, 2); io = zeros(1, 2); noff = zeros(1, 2); zc = nan(1, 2); ioff = nan(1, 2);
for p = 1:2
    i = I(:, p); s = Sg(:, p);
    offk = find(s(1:end-1) > 0.5 & s(2:end) < 0.5);
    onk = find(s(1:end-1) < 0.5 & s(2:end) > 0.5) + 1;
    pk(p) = max(abs(i));
    if ~isempty(offk) && pk(p) > 0
        zz(p) = max(abs(i(offk)))/pk(p);
        ioff(p) = max(abs(i(offk)));
        r = nan(numel(offk), 1);
        for j = 1:numel(offk)
            k0 = onk(find(onk <= offk(j), 1, 'last'));
            if isempty(k0), continue; end
            pj = max(abs(i(k0:offk(j))));
            if pj >= 1, r(j) = abs(i(offk(j)))/pj; end
        end
        if any(~isnan(r)), zc(p) = max(r); end
    end
    io(p) = mean(i.*(s == 1) - i.*(s == 2));
    noff(p) = numel(offk);
end
end

function [vmax, ne] = zvs_check(t, gh, gl, vleg, vrail, win)
% 레그 1 상측(gh)·하측(gl)이 켜지기 직전(한 표본 앞) V_ds: 상측 = v_rail − v_leg, 하측 = v_leg(TB14–TB16과 같음)
vmax = 0; ne = 0;
eh = find(diff(gh) > 0.5) + 1; el = find(diff(gl) > 0.5) + 1;
for k = eh(:)'
    if k > 1 && win(k), vmax = max(vmax, abs(vrail(k-1) - vleg(k-1))); ne = ne + 1; end
end
for k = el(:)'
    if k > 1 && win(k), vmax = max(vmax, abs(vleg(k-1))); ne = ne + 1; end
end
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
