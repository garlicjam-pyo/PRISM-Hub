function run_TB16(runList)
%RUN_TB16  TB16(R2 기본형 통합: Stage A 1모듈 + 400 V 버스·감쇠기 + 조정형 Stage C)을 사례별로 실행하고 판정한다.
%
%   run_TB16          % 사례 1–3
%   기준: 검증 코드 E23(E22 평균모델 + 버스 회로, Stage A 정적 등가)과 E1(Stage A 영교차 추종 2위상), ref/make_ref_TB16.py
%   사례(시험 전에 고정, 2 ms 사건, 5 ms까지)
%     1 A_540V_Cstep   배터리 540 V(V_A ≈ 270 V), 400 V 부하 10 kW, Stage C 0.1 → 5 kW 계단      48 V 판정 36–52 V
%     2 B_806V_Qstep   배터리 806 V(V_A ≈ 403 V), Stage C 3 kW, 400 V 부하 15 → 25 kW(10 µs)    48 V 판정 ±2 %
%     3 C_907V_Cregen  배터리 907 V(V_A ≈ 453 V), 400 V 부하 10 kW, Stage C 5 → −3 kW 계단       48 V 판정 36–52 V
%   판정(E23과 같은 기준 + 회로 항목)
%     (a) 48 V: 사례별 범위(사건 0.2 ms 전부터 끝까지, 10 µs 평균)
%     (b) 버스: 10 µs 평균이 [사건 전·끝 평균의 낮은 값 × 0.97, 높은 값 × 1.03] 안(사건 0.2 ms 전부터 끝까지)
%     (c) 버스 안정: 끝 0.5 ms 동안 10 µs 평균 버스의 최대 − 최소 ≤ 0.5 V
%     (d) Stage C 전류: 출력 100 µs 이동평균 ≤ 136.5 A, 2차 소자 순간 max|i_r2|/2 ≤ 329 A
%     (e) Stage C ZVS: 레그 1 켜짐 직전 V_ds ≤ 5 % 레일(1 ms–사건 직전, 끝 0.5 ms)
%     (f) Stage A: 위상별 ZCS(턴오프 순간 |i|/피크) ≤ 5 %, V_A 평균 − E1 ≤ 0.3 V, 위상 전류 차 ≤ 5 %(사건 전·끝 0.2 ms, TB06과 같음)
%     (g) E23 대조: v_o 최저·최고 ±0.5 V, 끝 v_o ±0.1 V, 버스 최저·최고 ±1 V, 끝 버스 ±0.5 V
%     (h) 끝 DCX 이득 n·v_o/v_I = 1 ± 3 %
%   10 µs 평균은 벅 한 주기이고 Stage A 출력 리플(600 kHz)의 6주기라 두 리플이 빠진다.
%   결과: results/TB16_<사례>_summary.txt·json, _avg10us.csv, _response.png, _stageA.png, TB16_summary.txt·json

here = fileparts(mfilename('fullpath'));
mdl  = 'TB16_R2_Base';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {'A_540V_Cstep', 'B_806V_Qstep', 'C_907V_Cregen'};
if nargin < 1 || isempty(runList), runList = 1:3; end
load_system(fullfile(here, [mdl '.slx']));
res = {};
for r = runList
    cn = R{r};
    assignin('base', 'TB16_case', cn);
    run(fullfile(here, 'TB16_init.m'));
    TB = evalin('base', 'TB');
    tic; out = sim(mdl, 'StopTime', num2str(TB.t_end, '%.9g')); wall = toc;
    S = evaluate(out, TB, refDir, cn, resDir, wall);
    res{end+1} = S; %#ok<AGROW>
    fprintf('%s done (%.0f s): %s\n', cn, wall, S.verdict);
    clear out
end
evalin('base', 'clear TB16_case');
fid = fopen(fullfile(resDir, 'TB16_summary.txt'), 'w');
o2(fid, 'TB16 R2 base integrated (Stage A module 1 + 400 V bus with damper + regulated Stage C), reference E23 / E1\n');
o2(fid, '%-15s %-6s %-9s %-9s %-9s %-9s %-9s %-9s %s\n', 'case', 'result', 'vo_min', 'vo_max', 'E23 min', 'E23 max', 'bus_min', 'bus_max', 'failed');
allPass = true;
for k = 1:numel(res)
    S = res{k};
    o2(fid, '%-15s %-6s %-9.2f %-9.2f %-9.2f %-9.2f %-9.2f %-9.2f %s\n', S.case, S.verdict, S.vo_min, S.vo_max, S.ref.vo_min, ...
        S.ref.vo_max, S.bus_min, S.bus_max, strjoin(S.failed, ', '));
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
o2(fid, 'TB16 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
fclose(fid);
fid = fopen(fullfile(resDir, 'TB16_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true)); fclose(fid);
end

% =======================================================================================================
function S = evaluate(out, TB, refDir, cn, resDir, wall)
t = out.t(:); vb = out.vbus(:); iin = out.iin(:); iL = out.iL(:); vI = out.vI(:); vo = out.vo(:); ix = out.ix(:);
ib = out.ibat(:); il = out.iload(:); vA = out.vA(:); iAo = out.iAo(:); p4 = out.p400(:);
ir1 = out.ir1(:); im = out.im(:); ir2 = out.ir2(:);
vl1 = out.vleg1(:); vls1 = out.vlegs1(:); gq1 = out.gq1(:); gq2 = out.gq2(:); gs1 = out.gs1(:); gs2 = out.gs2(:);
uc = squeeze(out.uc); if size(uc, 1) == 4 && size(uc, 2) ~= 4, uc = uc.'; end   % [d mode iref sel]
tA = out.tA(:); iA1 = out.iA1(:); iA2 = out.iA2(:); st1 = out.st1(:); st2 = out.st2(:);
X = [vb iin iL vI vo ix ib il vA iAo p4]; X(1, :) = X(2, :);
dts = t(2) - t(1);
np = round(10e-6/dts);
nper = floor(numel(t)/np);
A10 = zeros(nper, 12);                                     % [t_끝, 10 µs 평균 vb iin iL vI vo ix ib il vA iAo p400]
for q = 1:nper
    k = (q-1)*np + (1:np);
    A10(q, :) = [t(k(end)) mean(X(k, :), 1)];
end
writematrix(A10, fullfile(resDir, ['TB16_' cn '_avg10us.csv']));
A = readmatrix(fullfile(refDir, ['TB16_' cn '_avg.csv']));        % t vbus iL vI ix vo d mode ibat iin pload iref vA iA p400(1 µs)
M = jsondecode(fileread(fullfile(refDir, ['TB16_' cn '_metrics.json'])));
SA = jsondecode(fileread(fullfile(refDir, ['TB16_' cn '_stageA.json'])));
te = TB.t_event; tq = A10(:, 1);
post = tq >= te - 0.2e-3;
pre = tq > te - 0.2e-3 & tq <= te; fin = tq > tq(end) - 0.2e-3;
% ---- (a) 48 V -------------------------------------------------------------------------------------------
vmin = min(A10(post, 6)); vmax = max(A10(post, 6)); band = TB.band;
L.voltage = vmin >= band(1) && vmax <= band(2);
% ---- (b)·(c) 버스 ------------------------------------------------------------------------------------------
vb_pre = mean(A10(pre, 2)); vb_fin = mean(A10(fin, 2));
bb = [min(vb_pre, vb_fin)*0.97, max(vb_pre, vb_fin)*1.03];
bmin = min(A10(post, 2)); bmax = max(A10(post, 2));
L.bus_band = bmin >= bb(1) && bmax <= bb(2);
q5 = tq > tq(end) - 0.5e-3;
osc = max(A10(q5, 2)) - min(A10(q5, 2));
L.bus_settle = osc <= 0.5;
% ---- (d) Stage C 전류 ---------------------------------------------------------------------------------------
w = round(100e-6/dts);
ixa = movmean(ix, w);
ix_avg_max = max(abs(ixa(t >= te - 0.2e-3)));
dev_pk = max(abs(ir2(t >= te - 0.2e-3)))/2;
L.current_avg100 = ix_avg_max <= 130*1.05;
L.device_pulse = dev_pk <= TB.pulse_rating_secondary;
% ---- (e) Stage C ZVS ------------------------------------------------------------------------------------------
win = (t > 1.0e-3 & t < te - 0.05e-3) | t > t(end) - 0.5e-3;
[zp, np1] = zvs_check(t, gq1, gq2, vl1, vI, win);
[zs, ns1] = zvs_check(t, gs1, gs2, vls1, vo, win);
okz = true;
if np1 > 0, okz = okz && zp <= 0.05*mean(vI(win)); end
if ns1 > 0, okz = okz && zs <= 0.05*mean(vo(win)); end
L.zvs = okz && (np1 + ns1) > 0;
% ---- (f) Stage A --------------------------------------------------------------------------------------------
wins = {'pre', te - 0.2e-3, te; 'final', tA(end) - 0.2e-3, tA(end)};
SAc = struct(); okA = true;
for wv = 1:2
    m = tA > wins{wv, 2} & tA <= wins{wv, 3};
    ref = SA.(wins{wv, 1});
    I = [iA1(m) iA2(m)]; Sg = [st1(m) st2(m)];
    zz = zeros(1, 2); pk = zeros(1, 2); io = zeros(1, 2); noff = zeros(1, 2);
    for p = 1:2
        i = I(:, p); s = Sg(:, p);
        offk = find(s(1:end-1) > 0.5 & s(2:end) < 0.5);          % 도통 → 데드타임(턴오프 순간)
        pk(p) = max(abs(i)); zz(p) = max(abs(i(offk)))/pk(p);    % 턴오프 순간 전류 = 마지막 도통 표본(TB01·TB06과 같은 정의)
        io(p) = mean(i.*(s == 1) - i.*(s == 2));                % 위상 평균 출력전류
        noff(p) = numel(offk);
    end
    mv = tq > wins{wv, 2} & tq <= wins{wv, 3};
    vAm = mean(A10(mv, 10));
    sh = abs(io(1) - io(2))/abs(mean(io));
    SAc.(wins{wv, 1}) = struct('zcs', zz, 'Ipk', pk, 'io', io, 'noff', noff, 'vA_mean', vAm, 'vA_E1', ref.vA_mean, ...
        'zcs_E1', ref.zcs(:)', 'sharing', sh, 'iAo_mean', mean(A10(mv, 11)), 'iout_E1', ref.iout);
    okA = okA && all(zz <= 0.05) && abs(vAm - ref.vA_mean) <= 0.3 && sh <= 0.05;
end
L.stageA = okA;
% ---- (g) E23 대조 ------------------------------------------------------------------------------------------
qa = A(:, 1) > A(end, 1) - 0.2e-3;
d_vend = mean(A10(fin, 6)) - mean(A(qa, 6));
d_bend = vb_fin - mean(A(qa, 2));
L.e23_vo_extremes = abs(vmin - M.vo_min) <= 0.5 && abs(vmax - M.vo_max) <= 0.5;
L.e23_vo_end = abs(d_vend) <= 0.1;
L.e23_bus = abs(bmin - M.bus_min) <= 1 && abs(bmax - M.bus_max) <= 1 && abs(d_bend) <= 0.5;
% ---- (h) 끝 DCX 이득 ----------------------------------------------------------------------------------------
gain_end = TB.C.n*mean(A10(fin, 6))/mean(A10(fin, 5));
L.dcx_gain_end = abs(gain_end - 1) <= 0.03;
fn = fieldnames(L); pass = all(cellfun(@(f) L.(f), fn));
failed = fn(~cellfun(@(f) L.(f), fn))';
% ---- 정보 ---------------------------------------------------------------------------------------------------
tu = (0:size(uc, 1)-1)'*(t(end)/max(size(uc, 1)-1, 1));
qu = tu > te;
d_max_post = max(uc(qu, 1)); flips_post = sum(abs(diff(uc(qu, 2))) > 0.5); both_frac = mean(uc(qu, 2) > 1.5);
rip_raw = max(vb(t > t(end) - 0.5e-3)) - min(vb(t > t(end) - 0.5e-3));
pin_pre = mean(A10(pre, 2).*A10(pre, 3)); pin_fin = mean(A10(fin, 2).*A10(fin, 3));
S = struct('case', cn, 'verdict', ternary(pass, 'PASS', 'FAIL'), 'failed', {failed}, 'limits', L, 'wall_s', wall, ...
    'vo_min', vmin, 'vo_max', vmax, 'band', band, 'bus_min', bmin, 'bus_max', bmax, 'bus_pre', vb_pre, 'bus_end', vb_fin, ...
    'bus_band', bb, 'bus_osc_end', osc, 'bus_ripple_raw_end', rip_raw, 'ix_avg100_max', ix_avg_max, 'dev_peak_A', dev_pk, ...
    'zvs', struct('primary_max_V', zp, 'primary_n', np1, 'secondary_max_V', zs, 'secondary_n', ns1), 'stageA', SAc, ...
    'dcx_gain_end', gain_end, 'vo_end_diff', d_vend, 'bus_end_diff', d_bend, 'd_max_post', d_max_post, ...
    'mode_flips_post', flips_post, 'both_frac_post', both_frac, 'stageC_pin', [pin_pre pin_fin], ...
    'ref', struct('vo_min', M.vo_min, 'vo_max', M.vo_max, 'bus_min', M.bus_min, 'bus_max', M.bus_max, ...
                  'ix_avg100_max', M.ix_avg100_max));
fid = fopen(fullfile(resDir, ['TB16_' cn '_summary.txt']), 'w');
o2(fid, 'TB16 case %s, V_bat %.0f V, dt %.2f ns, wall %.0f s\n', cn, TB.vbat, 1e9*TB.dt, wall);
o2(fid, '(1) criteria:\n');
for k = 1:numel(fn), o2(fid, '    %-22s %s\n', fn{k}, ternary(L.(fn{k}), 'PASS', 'FAIL')); end
o2(fid, '    v_o (10 us mean) %.3f-%.3f V, band %.2f-%.2f V; E23 %.3f-%.3f V; end diff %+.3f V\n', vmin, vmax, band(1), band(2), ...
    M.vo_min, M.vo_max, d_vend);
o2(fid, '    bus (10 us mean) %.2f-%.2f V (pre %.2f, end %.2f, band %.2f-%.2f); E23 %.2f-%.2f V; end diff %+.3f V; end osc %.3f V\n', ...
    bmin, bmax, vb_pre, vb_fin, bb(1), bb(2), M.bus_min, M.bus_max, d_bend, osc);
o2(fid, '    Stage C output current 100 us mean max %.1f A (E23 %.1f A), secondary device peak %.1f A (rating 329 A)\n', ...
    ix_avg_max, M.ix_avg100_max, dev_pk);
o2(fid, '    Stage C ZVS (V_ds before turn-on): primary %.2f V (%d edges), secondary %.2f V (%d edges); end DCX gain %.4f\n', ...
    zp, np1, zs, ns1, gain_end);
for wv = {'pre', 'final'}
    a = SAc.(wv{1});
    o2(fid, '    Stage A %-5s: ZCS %.2f / %.2f %% (E1 %.2f / %.2f %%), Ipk %.1f / %.1f A, V_A %.3f V (E1 %.3f V), sharing %.2f %%, i_A %.2f A (E1 %.2f A)\n', ...
        wv{1}, 100*a.zcs(1), 100*a.zcs(2), 100*a.zcs_E1(1), 100*a.zcs_E1(2), a.Ipk(1), a.Ipk(2), a.vA_mean, a.vA_E1, 100*a.sharing, ...
        a.iAo_mean, a.iout_E1);
end
o2(fid, '(2) info: after event duty max %.3f, mode changes %d, both-bridge fraction %.2f; bus raw ripple end %.3f V; Stage C input %.0f / %.0f W\n', ...
    d_max_post, flips_post, both_frac, rip_raw, pin_pre, pin_fin);
fclose(fid);
fid = fopen(fullfile(resDir, ['TB16_' cn '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
% ---- 그림 ---------------------------------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [50 50 1200 950]);
tl = tiledlayout(f, 4, 1, 'TileSpacing', 'compact');
ax = nexttile(tl); plot(ax, 1e3*tq, A10(:, 6), 'b', 1e3*A(:, 1), A(:, 6), 'r--'); grid(ax, 'on'); ylabel(ax, 'v_o [V]');
yline(ax, band, 'k:'); legend(ax, '회로(10 µs 평균)', 'E23 평균모델', 'Location', 'best');
ax = nexttile(tl); plot(ax, 1e3*tq, A10(:, 2), 'b', 1e3*A(:, 1), A(:, 2), 'r--', 1e3*tq, A10(:, 10), 'c'); grid(ax, 'on');
ylabel(ax, '[V]'); legend(ax, 'v_{bus} 회로', 'v_{bus} E23', 'v_A 회로', 'Location', 'best');
ax = nexttile(tl); plot(ax, 1e3*tq, A10(:, 11), 'b', 1e3*A(:, 1), A(:, 14), 'r--', 1e3*tq, A10(:, 3), 'm'); grid(ax, 'on');
ylabel(ax, '[A]'); legend(ax, 'Stage A 출력 회로', 'Stage A 출력 E23', 'Stage C 입력 회로', 'Location', 'best');
ax = nexttile(tl); plot(ax, 1e3*tq, A10(:, 7), 'b', 1e3*A(:, 1), A(:, 5), 'r--'); grid(ax, 'on');
ylabel(ax, 'i_x [A]'); xlabel(ax, '시간 [ms]'); legend(ax, '회로', 'E23', 'Location', 'best');
title(tl, sprintf('TB16 %s', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB16_' cn '_response.png']), 'Resolution', 140); close(f);
k0 = find(tA >= tA(end) - 20e-6, 1);
f = figure('Visible', 'off', 'Position', [50 50 1200 600]);
tl = tiledlayout(f, 2, 1, 'TileSpacing', 'compact');
ax = nexttile(tl); plot(ax, 1e6*tA(k0:end), iA1(k0:end), 1e6*tA(k0:end), iA2(k0:end)); grid(ax, 'on');
ylabel(ax, '위상 공진전류 [A]'); legend(ax, '위상 1', '위상 2', 'Location', 'best');
ax = nexttile(tl); plot(ax, 1e6*tA(k0:end), st1(k0:end), 1e6*tA(k0:end), st2(k0:end) + 0.05); grid(ax, 'on');
ylabel(ax, '구간(0 데드, 1 충전, 2 방전)'); xlabel(ax, '시간 [µs]');
title(tl, sprintf('TB16 %s: Stage A 끝 20 µs(ZCS %.2f / %.2f %%)', strrep(cn, '_', ' '), 100*SAc.final.zcs(1), 100*SAc.final.zcs(2)));
exportgraphics(f, fullfile(resDir, ['TB16_' cn '_stageA.png']), 'Resolution', 140); close(f);
end

function [vmax, ne] = zvs_check(t, gh, gl, vleg, vrail, win)
% 레그 1 상측(gh)·하측(gl)이 켜지기 직전(한 표본 앞) V_ds: 상측 = v_rail − v_leg, 하측 = v_leg
vmax = 0; ne = 0;
eh = find(diff(gh) > 0.5) + 1; el = find(diff(gl) > 0.5) + 1;
for k = eh(:)'
    if k > 1 && win(k), vmax = max(vmax, abs(vrail(k-1) - vleg(k-1))); ne = ne + 1; end
end
for k = el(:)'
    if k > 1 && win(k), vmax = max(vmax, abs(vleg(k-1))); ne = ne + 1; end
end
end

function o2(fid, varargin)
fprintf(fid, varargin{:}); fprintf(varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
