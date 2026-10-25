function run_TB15(runList)
%RUN_TB15  TB15(조정형 Stage C 경부하 두 브리지 구동)를 사례별로 실행하고 판정한다(기준: 검증 코드 E22 평균모델, ref/make_ref_TB15.py).
%
%   run_TB15          % 사례 1–5
%   TB14와 같은 회로·판정에 경부하 두 브리지 구동(E22 both: |P*| < P_in이면 두 브리지 같은 위상, > P_out이면 보내는 쪽 하나)을 넣었다.
%   사례(시험 전에 고정, 1.5 ms 정상상태 뒤 사건)
%     1 A_400V_ramp       입력 400 V, 0.1 → 5 kW(4 kW/ms): 두 브리지 구동에서 시작해 1차가 보내는 쪽으로      판정 48 V ±2 %
%     2 C_504V_rev        입력 504 V, 5 → −3 kW 계단(회생): 두 브리지 구동 구간을 지나감                  판정 36–52 V
%     3 F_400V_rev_light  입력 400 V, −3 → −0.3 kW 계단: TB14 사례 F와 같은 조건                           판정 36–52 V, (f)
%     4 G_270V_rev_light  입력 270 V, −3 → −0.1 kW 계단: TB14 사례 G와 같은 조건                           판정 36–52 V, (f)
%     5 H_400V_cross      입력 400 V, +1 → −1 kW 램프(1 kW/ms): 두 브리지 구동에 들어갔다 나감                판정 48 V ±2 %, (f)
%   공통 판정
%     (a) 전압: 위 사례별 범위(사건 0.2 ms 전부터 끝까지, 10 µs 평균)
%     (b) 전류: 출력전류 100 µs 이동평균 ≤ 130 A × 1.05, 2차 소자 순간 전류 max|i_r2|/2 ≤ 329 A(EPC2305 펄스 정격)
%     (c) ZVS: 보내는 쪽 레그 1이 켜지기 직전 V_ds ≤ 5 % 레일 전압(정상 구간, 사건 0.5 ms 전까지와 끝 0.5 ms)
%     (d) DCX 이득: 사건 전 정상상태 n·v_o/v_I(10 µs 평균) = 1 ± 3 %
%     (e) E22 대조: v_o 최저·최고 차 ≤ 0.5 V, 끝 0.2 ms 평균 v_o 차 ≤ 0.1 V, i_L 끝 평균 차 ≤ 3 % 또는 0.3 A
%     (f) 경부하 끝 DCX 이득(F·G·H): 끝 0.2 ms n·v_o/v_I = 1 ± 3 %(TB14 F·G에서 깨진 것)
%     (c)는 두 브리지 구동 중이면 두 브리지 모두의 레그 1 켜짐을 본다.
%   결과: results/TB15_<사례>_summary.txt·json, _avg10us.csv, _response.png, _cllc.png, TB15_summary.txt·json

here = fileparts(mfilename('fullpath'));
mdl  = 'TB15_StageC_LightLoad';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {'A_400V_ramp', 'C_504V_rev', 'F_400V_rev_light', 'G_270V_rev_light', 'H_400V_cross'};
if nargin < 1 || isempty(runList), runList = 1:5; end
load_system(fullfile(here, [mdl '.slx']));
res = {};
for r = runList
    cn = R{r};
    assignin('base', 'TB15_case', cn);
    run(fullfile(here, 'TB15_init.m'));
    TB = evalin('base', 'TB');
    tic; out = sim(mdl, 'StopTime', num2str(TB.t_end, '%.9g')); wall = toc;
    S = evaluate(out, TB, refDir, cn, resDir, wall);
    res{end+1} = S; %#ok<AGROW>
    fprintf('%s done (%.0f s): %s\n', cn, wall, S.verdict);
    clear out
end
evalin('base', 'clear TB15_case');
fid = fopen(fullfile(resDir, 'TB15_summary.txt'), 'w');
o2(fid, 'TB15 regulated Stage C with light-load both-bridge drive (sync buck + CLLC DCX 4.8:1), reference E22 averaged model\n');
o2(fid, '%-14s %-6s %-9s %-9s %-9s %-9s %s\n', 'case', 'result', 'vo_min', 'vo_max', 'E22 min', 'E22 max', 'failed');
allPass = true;
for k = 1:numel(res)
    S = res{k};
    o2(fid, '%-14s %-6s %-9.2f %-9.2f %-9.2f %-9.2f %s\n', S.case, S.verdict, S.vo_min, S.vo_max, S.ref.vo_min, S.ref.vo_max, strjoin(S.failed, ', '));
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
o2(fid, 'TB15 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
fclose(fid);
fid = fopen(fullfile(resDir, 'TB15_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true)); fclose(fid);
end

% =======================================================================================================
function S = evaluate(out, TB, refDir, cn, resDir, wall)
t = out.t(:); vb = out.vbus(:); iin = out.iin(:); iL = out.iL(:); vI = out.vI(:); vo = out.vo(:); ix = out.ix(:);
ib = out.ibat(:); il = out.iload(:); ir1 = out.ir1(:); im = out.im(:); ir2 = out.ir2(:);
vl1 = out.vleg1(:); vls1 = out.vlegs1(:); gq1 = out.gq1(:); gq2 = out.gq2(:); gs1 = out.gs1(:); gs2 = out.gs2(:);
uc = squeeze(out.uc); if size(uc, 1) == 4 && size(uc, 2) ~= 4, uc = uc.'; end   % 벡터 신호는 4×1×N으로 저장된다([d mode iref sel])
X = [vb iin iL vI vo ix ib il]; X(1, :) = X(2, :);
dts = t(2) - t(1);
Ts = 10e-6; np = round(Ts/dts);
nper = floor(numel(t)/np);
A10 = zeros(nper, 9);                                      % [t_끝, 10 µs 평균 vb iin iL vI vo ix ib il]
for q = 1:nper
    k = (q-1)*np + (1:np);
    A10(q, :) = [t(k(end)) mean(X(k, :), 1)];
end
writematrix(A10, fullfile(resDir, ['TB15_' cn '_avg10us.csv']));
A = readmatrix(fullfile(refDir, ['TB15_' cn '_avg.csv']));        % t vbus iL vI ix vo d mode ibat iin pload iref (1 µs)
M = jsondecode(fileread(fullfile(refDir, ['TB15_' cn '_metrics.json'])));
te = TB.t_event; tq = A10(:, 1);
post = tq >= te - 0.2e-3;
% ---- (a) 전압 --------------------------------------------------------------------------------------------
vmin = min(A10(post, 6)); vmax = max(A10(post, 6));
switch cn
    case {'A_400V_ramp', 'H_400V_cross'}, band = [48*0.98 48*1.02];
    otherwise, band = [36 52];
end
L.voltage = vmin >= band(1) && vmax <= band(2);
% ---- (b) 전류 --------------------------------------------------------------------------------------------
w = round(100e-6/dts);
ixa = movmean(ix, w);
ix_avg_max = max(abs(ixa(t >= te - 0.2e-3)));
dev_pk = max(abs(ir2(t >= te - 0.2e-3)))/2;
L.current_avg100 = ix_avg_max <= 130*1.05;
L.device_pulse = dev_pk <= TB.pulse_rating_secondary;
ix_late = NaN;
if strcmp(cn, 'E_400V_bat')
    ql = t >= te + 2.5e-3;
    ix_late = max(abs(ixa(ql)));
    L.overload_time_limit = ix_late <= 105*1.05;
end
% ---- (c) ZVS: 보내는 쪽 레그 1, 켜지기 직전 V_ds ------------------------------------------------------------
win = (t < te - 0.5e-3 & t > 0.5e-3) | t > t(end) - 0.5e-3;
[zp, np1] = zvs_check(t, gq1, gq2, vl1, vI, win);        % 1차 레그 1(레일 v_I)
[zs, ns1] = zvs_check(t, gs1, gs2, vls1, vo, win);       % 2차 레그 1(레일 v_o)
zvs = struct('primary_max_V', zp, 'primary_n', np1, 'secondary_max_V', zs, 'secondary_n', ns1);
okz = true;
if np1 > 0, okz = okz && zp <= 0.05*mean(vI(win)); end
if ns1 > 0, okz = okz && zs <= 0.05*mean(vo(win)); end
L.zvs = okz && (np1 + ns1) > 0;
% 전환 파형 저장(사건 전 12 µs, 끝 12 µs, 10 ns 간격): ZVS·전류 전환 점검용
hdr = {'t', 'vI', 'vleg1', 'gq1', 'gq2', 'ir1', 'im', 'ir2', 'vo', 'vlegs1', 'gs1', 'gs2'};
W = [t vI vl1 gq1 gq2 ir1 im ir2 vo vls1 gs1 gs2];
for wn = {{'pre', t >= te - 20e-6 & t < te - 8e-6}, {'end', t >= t(end) - 12e-6}}
    writecell([hdr; num2cell(W(wn{1}{2}, :))], fullfile(resDir, ['TB15_' cn '_wave_' wn{1}{1} '.csv']));
end
% ---- (d) DCX 이득 -------------------------------------------------------------------------------------------
qs = tq > te - 0.5e-3 & tq < te;
gain = TB.C.n*mean(A10(qs, 6))/mean(A10(qs, 5));
L.dcx_gain = abs(gain - 1) <= 0.03;
% ---- (e) E22 대조 ------------------------------------------------------------------------------------------
qe = tq > tq(end) - 0.2e-3; qa = A(:, 1) > A(end, 1) - 0.2e-3;
d_vend = mean(A10(qe, 6)) - mean(A(qa, 6));
iLc = mean(A10(qe, 4)); iLr = mean(A(qa, 3));
d_iL = iLc - iLr;
L.e22_vo_extremes = abs(vmin - M.vo_min) <= 0.5 && abs(vmax - M.vo_max) <= 0.5;
L.e22_vo_end = abs(d_vend) <= 0.1;
L.e22_iL_end = abs(d_iL) <= max(0.03*abs(iLr), 0.3);
% ---- (f) 경부하 끝 DCX 이득 --------------------------------------------------------------------------------
gain_end = TB.C.n*mean(A10(qe, 6))/mean(A10(qe, 5));
if any(strcmp(cn, {'F_400V_rev_light', 'G_270V_rev_light', 'H_400V_cross'}))
    L.dcx_gain_end = abs(gain_end - 1) <= 0.03;
end
fn = fieldnames(L); pass = all(cellfun(@(f) L.(f), fn));
failed = fn(~cellfun(@(f) L.(f), fn))';
% ---- 정보 ---------------------------------------------------------------------------------------------------
tu = (0:size(uc, 1)-1)'*(t(end)/max(size(uc, 1)-1, 1));          % 제어 출력 시각(10 µs 간격 근사)
qu = tu > te;
d_max_post = max(uc(qu, 1)); flips_post = sum(abs(diff(uc(qu, 2))) > 0.5);
both_frac = mean(uc(qu, 2) > 1.5);                                 % 사건 뒤 두 브리지 구동 비율
qs2 = tq > te - 0.5e-3 & tq < te;
pin = mean(A10(qs2, 2).*A10(qs2, 3)); pout = mean(A10(qs2, 6).*(A10(qs2, 7)));
eff = NaN; if abs(pin) > 50, eff = pout/pin; if pin < 0, eff = pin/pout; end, end
S = struct('case', cn, 'verdict', ternary(pass, 'PASS', 'FAIL'), 'failed', {failed}, 'limits', L, 'wall_s', wall, ...
    'vo_min', vmin, 'vo_max', vmax, 'band', band, 'ix_avg100_max', ix_avg_max, 'dev_peak_A', dev_pk, 'ix_late', ix_late, ...
    'zvs', zvs, 'dcx_gain', gain, 'dcx_gain_end', gain_end, 'd_max_post', d_max_post, 'mode_flips_post', flips_post, 'both_frac_post', both_frac, 'eff_pre_event', eff, 'vo_end_diff', d_vend, 'iL_end', [iLc iLr], ...
    'ref', struct('vo_min', M.vo_min, 'vo_max', M.vo_max, 'ix_avg100_max', M.ix_avg100_max), ...
    'ir1_rms_pre', sqrt(mean(ir1(t > te - 0.2e-3 & t < te).^2)), 'im_pk_pre', max(abs(im(t > te - 0.2e-3 & t < te))));
fid = fopen(fullfile(resDir, ['TB15_' cn '_summary.txt']), 'w');
o2(fid, 'TB15 case %s, dt %.2f ns, wall %.0f s\n', cn, 1e9*TB.dt, wall);
o2(fid, '(1) criteria:\n');
for k = 1:numel(fn), o2(fid, '    %-22s %s\n', fn{k}, ternary(L.(fn{k}), 'PASS', 'FAIL')); end
o2(fid, '    v_o (10 us mean) %.3f-%.3f V, band %.2f-%.2f V; E22 %.3f-%.3f V\n', vmin, vmax, band(1), band(2), M.vo_min, M.vo_max);
o2(fid, '    output current 100 us mean max %.1f A (E22 %.1f A), secondary device peak %.1f A (rating 329 A), late %.1f A\n', ...
    ix_avg_max, M.ix_avg100_max, dev_pk, ix_late);
o2(fid, '    ZVS (V_ds before turn-on): primary %.2f V (%d edges), secondary %.2f V (%d edges)\n', zp, np1, zs, ns1);
o2(fid, '    DCX gain n*v_o/v_I before event %.4f, last 0.2 ms %.4f\n', gain, gain_end);
o2(fid, '    after event: duty max %.3f, mode changes %d, both-bridge drive fraction %.2f\n', d_max_post, flips_post, both_frac);
o2(fid, '    end of run: v_o circuit - E22 %+.3f V, i_L circuit %.2f A / E22 %.2f A\n', d_vend, iLc, iLr);
o2(fid, '(2) info: efficiency before event (circuit, input->48 V incl. buck and DCX) %.4f, ir1 rms %.2f A, im peak %.2f A\n', ...
    eff, S.ir1_rms_pre, S.im_pk_pre);
fclose(fid);
fid = fopen(fullfile(resDir, ['TB15_' cn '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
% ---- 그림 ---------------------------------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [50 50 1200 820]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
ax = nexttile(tl); plot(ax, 1e3*tq, A10(:, 6), 'b', 1e3*A(:, 1), A(:, 6), 'r--'); grid(ax, 'on'); ylabel(ax, 'v_o [V]');
yline(ax, band, 'k:'); legend(ax, '회로(10 µs 평균)', 'E22 평균모델', 'Location', 'best');
ax = nexttile(tl); plot(ax, 1e3*tq, A10(:, 4), 'b', 1e3*A(:, 1), A(:, 3), 'r--'); grid(ax, 'on'); ylabel(ax, 'i_L [A]');
ax = nexttile(tl); plot(ax, 1e3*tq, A10(:, 7), 'b', 1e3*A(:, 1), A(:, 5), 'r--', 1e3*tq, A10(:, 8), 'g'); grid(ax, 'on');
ylabel(ax, '[A]'); xlabel(ax, '시간 [ms]'); legend(ax, 'i_x 회로', 'i_x E22', 'i_{bat} 회로', 'Location', 'best');
title(tl, sprintf('TB15 %s', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB15_' cn '_response.png']), 'Resolution', 140); close(f);
k0 = find(t >= te - 20e-6, 1); k1 = find(t >= te - 8e-6, 1);
f = figure('Visible', 'off', 'Position', [50 50 1200 700]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
ax = nexttile(tl); plot(ax, 1e6*t(k0:k1), ir1(k0:k1), 1e6*t(k0:k1), im(k0:k1), 1e6*t(k0:k1), ir2(k0:k1)/TB.C.n); grid(ax, 'on');
ylabel(ax, '[A](1차 환산)'); legend(ax, 'i_{r1}', 'i_m', 'i_{r2}/n', 'Location', 'best');
ax = nexttile(tl); plot(ax, 1e6*t(k0:k1), vl1(k0:k1), 1e6*t(k0:k1), 100*gq1(k0:k1)); grid(ax, 'on'); ylabel(ax, 'v_{leg1} [V]');
ax = nexttile(tl); plot(ax, 1e6*t(k0:k1), vls1(k0:k1), 1e6*t(k0:k1), 20*gs1(k0:k1)); grid(ax, 'on'); ylabel(ax, 'v_{legs1} [V]');
xlabel(ax, '시간 [µs]'); title(tl, sprintf('TB15 %s: 사건 직전 CLLC 파형', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB15_' cn '_cllc.png']), 'Resolution', 140); close(f);
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
