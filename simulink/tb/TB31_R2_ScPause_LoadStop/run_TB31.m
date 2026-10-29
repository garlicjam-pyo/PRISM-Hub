function run_TB31(runList)
%RUN_TB31  TB31: Stage C 일시 정지(P6)와 이중 고장 400 V 부하 정지(F2)를 회로에서 판정한다(R2-W460, 기준: 검증 코드 E38 = E17 r2_run
%           + sals_loads의 sc_pause·load_stop, 시간 축소 0.15).
%
%   TB23 회로(TB13 전력 회로·지령 블록 + 등급별 계약 응답 부하 + SALS 모드 상태기계 + Stage A 정지 스위치)에 다음을 더했다.
%     - 상태기계 파라미터 71개: 70 Stage C 일시 정지(비트 32), 71 400 V 부하 정지(비트 64)
%     - 부하 블록 파라미터 23개: 23 정지 램프(E38 f2 선정)
%     - C_A 2.4 mF(A25R)
%
%   run_TB31          % 실행 1–2
%   실행 목록(고장 0.5 ms)
%     1 A31  930 V, 25 kW(Stage C 5.3 + V2L 3.8 + 컴프레서 6 + PTC 7 + 배터리 히터 2.9 kW), H-브리지 개방, 메시지 지연 5 ms(축소 0.75 ms),
%            Stage C 일시 정지 → 붕괴가 링크 0.5 V까지 끝나고 소프트 투입 → 강등 → 0.5 ms 뒤 SALS 되돌림·Stage C 재개
%     2 E31  1008 V, 25 kW, DAB 고장 → 제동 유지 중(검출 0.5 ms 뒤) H-브리지 차단(이중 고장) → 접촉기 분리 + SALS 감발 + Stage A 정지
%            + 400 V 부하 정지(전용 배선 신호, E38 선정 램프). 방전 저항 없음
%
%   판정(시험 전에 고정)
%     H-브리지 고장(A31): TB23과 같은 회로 한계(순시 경로·필터 ≤ 100 A, |v_s| ≤ 120 V, 링크 ≤ 120 V, 바이패스 ≤ 329 A, 버스 ≥ 260 V,
%                강등 상태 도달, 400 V 부하가 연결된 동안 버스 ≤ 상한, 강등 상태 9–11의 DAB 링크 쪽 순시 첨두 ≤ 1.5 × 정격점)
%                + 제동 저항 에너지 ≤ 64 J + (P6) 바이패스 소프트 투입 소자 EPC2305 1개: 100 °C + Foster ΔT(1 µs 평균 전력) ≤ 150 °C
%     이중 고장(E31): TB23 E와 같다(순시 경로·필터 ≤ 100 A, |v_s| ≤ 120 V, 링크 ≤ 120 V, 400 V 부하 연결 중 버스 ≤ 상한, 제동 ≤ 64 J,
%                Stage A 정지 뒤 5 ms 안에 경로전류(5 µs 평균) |i_p| ≤ 1 A가 되어 끝까지 유지)
%     E38 대조(정보): 상태 전이 시각, 주기 평균 버스·전류·링크, 부하 전력, 소프트 투입 에너지, |i_p| ≤ 1 A까지 시간
%   결과: results/TB31_<사례>_summary.txt·json, _periods.csv, _response.png, TB31_summary.txt·json

here = fileparts(mfilename('fullpath'));
mdl  = 'TB31_R2_ScPause_LoadStop';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {'A31', 'A31_930V_MX_S5_pause'; 'E31', 'E31_1008V_dab_double_stop'};
if nargin < 1 || isempty(runList), runList = 1:2; end
load_system(fullfile(here, [mdl '.slx']));
res = {};
for r = runList
    cn = R{r, 2};
    assignin('base', 'TB31_case', cn);
    evalin('base', 'clear TB31_opts');
    run(fullfile(here, 'TB31_init.m'));
    TB = evalin('base', 'TB');
    tic; out = sim(mdl, 'StopTime', num2str(TB.t_end, '%.9g')); wall = toc;
    S = evaluate(out, TB, refDir, cn, resDir, wall);
    S.run = R{r, 1};
    res{end+1} = S; %#ok<AGROW>
    fprintf('%s done (%.0f s): %s\n', R{r, 1}, wall, S.verdict);
end
evalin('base', 'clear TB31_case');
fid = fopen(fullfile(resDir, 'TB31_summary.txt'), 'w');
o2(fid, 'TB31 Stage C pause (P6) and 400 V load stop (F2), R2-W460, SALS time scale 0.15, DAB design limit %.3fx rated, C_A %.1f mF\n', TB.pk_max/TB.rated_pk, 1e3*TB.CA);
o2(fid, '%-4s %-28s %-8s %s\n', 'run', 'case', 'limits', 'failed');
allPass = true;
for k = 1:numel(res)
    S = res{k};
    o2(fid, '%-4s %-28s %-8s %s\n', S.run, S.case, S.verdict, strjoin(S.failed, ', '));
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
o2(fid, 'TB31 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
fclose(fid);
fid = fopen(fullfile(resDir, 'TB31_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true)); fclose(fid);
end

% =======================================================================================================
function S = evaluate(out, TB, refDir, cn, resDir, wall)
t = out.t(:); vb = out.vbus(:); ip = out.ip(:); ih = out.ih(:); vs = out.vs(:); vl = out.vlink(:);
ib = out.ibyp(:); ik = out.ibrk(:); iL = out.iL(:);
pl = cols(out.pload, 1); vAq = cols(out.vA, 1);           % 부하 전력, V_A 노드(5 µs마다)
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
code = round(sup(:, 10));                                   % SALS 모드 비트 명령(1 접촉기 열림, 2 감발, 4 되돌림, 8 회생 차단, 16 Stage A 정지)
bit = @(b) mod(floor(code/b), 2);
shedq = interp1(ts, bit(1), tq - T, 'previous', 'extrap');    % 1 = 접촉기 열림(400 V급 부하 분리)
% ---- 상태 전이 시각 ---------------------------------------------------------------------------------
names = {'BYPASS', 'PREP', 'OPEN_WAIT', 'WINDOW', 'OFF_RAMP', 'OFF_HOLD', 'ZERO', 'DAB_HOLD', 'DAB_RAMP', 'HB_HOLD', ...
         'HB_COLLAPSE', 'SOFT_BYP', 'DEGRADED', 'FAILSAFE'};
ch = find(diff(sup(:, 11)) ~= 0) + 1;
ev = struct('state', {}, 'ms', {});
for j = 1:numel(ch)
    ev(end+1) = struct('state', names{round(sup(ch(j), 11)) + 1}, 'ms', 1e3*ts(ch(j))); %#ok<AGROW>
end
bn = {1, 'shed_done'; 2, 'shed_cmd'; 4, 'restore'; 16, 'stageA_stop'; 32, 'sc_pause'; 64, 'load_stop'};
for j = 1:size(bn, 1)
    kb = find(diff(bit(bn{j, 1})) > 0.5, 1);
    if ~isempty(kb), ev(end+1) = struct('state', bn{j, 2}, 'ms', 1e3*ts(kb + 1)); end %#ok<AGROW>
end
kr = find(diff(bit(32)) < -0.5, 1);                         % Stage C 재개(비트 32가 꺼짐)
if ~isempty(kr), ev(end+1) = struct('state', 'sc_resume', 'ms', 1e3*ts(kr + 1)); end
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
ip_zero_ms = NaN;
if strcmp(TB.event, 'dab')                                  % 이중 고장(E)
    L.current_100A = max(abs(ip(post))) <= 100 && max(abs(ih(post))) <= 100;
    L.series_120V = max(abs(vs(post))) <= 120;
    L.link_120V = max(vl(post)) <= 120;
    L.class_upper_while_400V_loads = max(pr(loaded & tq > 0.5e-3, 1)) <= TB.upper;
    L.brake_64J = sum(pr(:, 11))*T <= 64;
    ka = find(bit(16) > 0.5, 1);
    held = false;
    if ~isempty(ka)
        t1 = ts(ka); w = tq - T >= t1 - 1e-12;
        hi = find(abs(pr(w, 2)) > 1, 1, 'last'); tw = tq(w);
        if isempty(hi), ip_zero_ms = 0; held = true;
        elseif hi < numel(tw), ip_zero_ms = 1e3*(tw(hi + 1) - T - t1); held = true; end
    end
    L.ip_zero_5ms = held && ip_zero_ms <= 5;
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
    L.brake_64J = sum(pr(:, 11))*T <= 64;
    % (P6) 바이패스 소프트 투입 소자 EPC2305 1개: 1 µs 평균 전력 |v_s·i_byp| → Foster Z_thJC(E34) → 100 °C + ΔT ≤ 150 °C
    n1 = round(1e-6/TB.dt); m1 = floor(numel(t)/n1);
    p1 = mean(reshape(abs(vs(1:n1*m1).*ib(1:n1*m1)), n1, m1), 1)';
    Rf = TB.foster.R(:)'; tf = TB.foster.tau(:)'; a = exp(-1e-6./tf); b = Rf.*(1 - a); xs = zeros(1, numel(Rf)); dTmax = 0;
    for q = 1:m1
        xs = a.*xs + b*p1(q); dTmax = max(dTmax, sum(xs));
    end
    P6 = struct('Tj_C', TB.T_C + dTmax, 'P_pk_1us_W', max(p1));
    L.P6_epc_150C = P6.Tj_C <= TB.T_lim;
end
fn = fieldnames(L); lpass = all(cellfun(@(f) L.(f), fn));
failed = fn(~cellfun(@(f) L.(f), fn))';
% ---- E17 대조 ------------------------------------------------------------------------------------------
A = readmatrix(fullfile(refDir, ['TB31_' cn '_avg.csv']));   % [t ip vs vbus ih vlink idab ibyp loads bridge Pbrk Pload], 1 µs
M = jsondecode(fileread(fullfile(refDir, ['TB31_' cn '_metrics.json'])));
qi = ceil(A(:, 1)/T - 1e-9); ok = qi >= 1 & qi <= nper;
rp = nan(nper, 7);   % 기준 주기 평균 [vb ip ih vl vs Pbrk Pload]
colA = [4 2 5 6 3 11 12];
for j = 1:7, rp(:, j) = accumarray(qi(ok), A(ok, colA(j)), [nper 1], @mean, NaN); end
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
nq = min(numel(pl), nper);
cmp(end+1, :) = add('load energy after event [J]', sum(pl(1:nq).*(tq(1:nq) > 0.5e-3))*T, sum(rp(v, 7))*T, NaN);
if strcmp(TB.event, 'dab')
    cmp(end+1, :) = add('V_A node at end [V]', vAq(end), NaN, NaN);
end
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
fid = fopen(fullfile(resDir, ['TB31_' cn '_summary.txt']), 'w');
o2(fid, 'TB31 case %s (V_bat %.0f V, %.0f kW, event %s), dt %.2f ns, wall %.0f s\n', cn, TB.vbat, TB.P0/1e3, TB.event, 1e9*TB.dt, wall);
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
        if any(q), o2(fid, '    DAB peak in state %d (%s): n|i_L| %.1f A (design %.3fx %.1f A, limit 1.5x %.1f A)\n', sj, names{sj + 1}, ...
                nt*max(pr(q, 13)), TB.pk_max/TB.rated_pk, TB.pk_max, 1.5*TB.rated_pk); end
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
o2(fid, '    final state: %s; brake energy %.2f J; path current |i_p| <= 1 A after Stage A stop: %.3f ms\n', final_state, sum(pr(:, 11))*T, ip_zero_ms);
if ~exist('P6', 'var'), P6 = struct('Tj_C', NaN, 'P_pk_1us_W', NaN); end   % 이중 고장 사례에는 소프트 투입이 없다(1차 실행의 출력 단계 오류 수정)
if isfinite(P6.Tj_C), o2(fid, '    (P6) soft-bypass device EPC2305 (one device, 1 us mean power): T_J %.1f C, peak power %.1f W\n', P6.Tj_C, P6.P_pk_1us_W); end
if isfield(M, 'ip_zero_ms'), o2(fid, '    E38 model: |i_p| <= 1 A after Stage A stop %.3f ms\n', M.ip_zero_ms); end
if isfield(M, 'P6_Tj'), o2(fid, '    E38 model: P6 T_J %.1f C, peak %.1f W\n', M.P6_Tj, M.P6_P_pk_W); end
fclose(fid);
S = struct('case', cn, 'event', TB.event, 'limits', L, 'P6', P6, 'verdict', ternary(lpass, 'PASS', 'FAIL'), 'failed', {failed}, ...
    'transitions', ev, 'final_state', final_state, 'clamp_err_V', clamp_err, 'dab', dab, 'soft', soft, ...
    'peaks', struct('ip_A', max(abs(ip(post))), 'ih_A', max(abs(ih(post))), 'vs_V', max(abs(vs(post))), 'vlink_max_V', max(vl(post)), ...
                    'vlink_min_V', min(vl(post)), 'ibyp_A', max(abs(ib(post))), 'bus_min_V', min(pr(:, 12)), 'bus_max_V', max(pr(:, 1)), ...
                    'bus_max_loaded_V', max(pr(loaded, 1)), 'brake_J', sum(pr(:, 11))*T), ...
    'ip_zero_ms', ip_zero_ms, 'vA_end_V', vAq(end), 'wall_s', wall, 'dt_ns', 1e9*TB.dt, 'date', char(datetime('now')));
S.compare = cell2struct(cmp, {'metric', 'simscape', 'e17', 'tol'}, 2);
fid = fopen(fullfile(resDir, ['TB31_' cn '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
plq = nan(nper, 1); plq(1:nq) = pl(1:nq);
writematrix([tq pr stq shedq plq], fullfile(resDir, ['TB31_' cn '_periods.csv']));
% ---- 그림 ------------------------------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 1000 900]);
tl = tiledlayout(f, 5, 1, 'TileSpacing', 'compact');
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
nexttile; hold on; grid on; plot(ms_, plq/1e3, 'LineWidth', 1.3); plot(mr, A(:, 12)/1e3, '--');
ylabel('[kW]'); legend('load power (circuit block)', 'E29 model', 'Location', 'best'); title('400 V bus load (class contracts via SALS)');
nexttile; hold on; grid on;
yyaxis left; stairs(1e3*ts, sup(:, 11), 'LineWidth', 1.2); ylabel('state'); ylim([-0.5 13.5]);
yyaxis right; plot(ms_, pr(:, 11)/1e3, 'LineWidth', 1.0); ylabel('brake power [kW]');
xlabel('t [ms]'); title('state (3 window, 6 zero, 7 DAB hold, 8 DAB ramp, 9 HB hold, 10 collapse, 11 soft bypass, 12 degraded, 13 double fault)');
title(tl, sprintf('TB31 %s (E38: Stage C pause / 400 V load stop)', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB31_' cn '_response.png']), 'Resolution', 140); close(f);
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
