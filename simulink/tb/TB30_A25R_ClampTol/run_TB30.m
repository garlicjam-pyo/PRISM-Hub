function run_TB30(runList)
%RUN_TB30  TB30(TB28 회로 + 재선정 V_A 클램프, E38 Q1)을 사례별로 실행하고 판정한다.
%
%   run_TB30          % 사례 1–2
%   기준: ref/make_ref_TB30.py = 검증 코드 E26(V_A 노드 평균모델, R_A 9.0 mΩ, C_A 2.4 mF, 클램프 468/463 V·1 µs, 사례의 저항 모서리·강하),
%         E22(조정형 Stage C 평균모델, E26 버스 궤적), A25R Stage A 스위칭 모델. 충전기 정지 시간 3 ms(TB20·TB28·TB29와 같음).
%   클램프: E38 선정 = SP 저항 가지 2개 × 공칭 1.6 Ω(가지마다 SiC 스위치, 같은 게이트). 회로는 등가 가지 하나(저항 / 2, 같은 강하).
%   사례(시험 전에 고정, 400 V 부하·Stage C 0)
%     1 A30_640V_noload_Rmax  640 V, 충전 375 A. 1.5 ms 배터리 경로 상실(8위상 차단), 충전기 3 ms 유지 뒤 0. 큰 저항 모서리
%                             (가지 2.340 Ω → 등가 1.170 Ω, 강하 2.05 V): E38 32사건 가운데 버스 최고가 가장 높았던 사건과 같은 조건
%     2 B30_920V_noload_Rmin  920 V, 같은 사건. 작은 저항 모서리(가지 1.190 Ω → 등가 0.595 Ω): 가지 전류가 가장 컸던 사건
%   판정(시험 전에 고정, TB29와 같은 항목)
%     (C1)  V_A·버스 1 µs 평균 ≤ 470 V(1 ms 이후). 순시 최고는 정보
%     (C1r) E26 대조: V_A·버스 1 µs 최고 ±1.5 V, 클램프 저항 흡수 에너지 ±10 %(또는 ±10 J 중 큰 값)
%     (C3)  48 V 10 µs 평균 ±2 %·E22 대조 ±0.5 V, Stage C 전류, ZVS
%     (C4)  사건 전 Stage A: 8위상 턴오프 전류/피크 ≤ 5 %, 위상 전류 차 ≤ 5 %, V_A − 모델 ≤ 0.3 V
%     (C5)  1 ms 이후 모든 턴오프(사건 순간 강제 차단 제외): |i_off| ≤ max(5 % × 반주기 첨두, 1 A)
%   정보: 클램프 켬 횟수·켜진 시간(E26과 비교), 클램프 전류 첨두(가지당 = 합 / 2)
%   결과: results/TB30_<사례>_summary.txt·json, _avg1us.csv, _response.png, _stageA.png, TB30_summary.txt·json

here = fileparts(mfilename('fullpath'));
mdl  = 'TB30_A25R_ClampTol';
refDir = fullfile(here, 'ref');
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
R = {'A30_640V_noload_Rmax', 'B30_920V_noload_Rmin'};
if nargin < 1 || isempty(runList), runList = 1:2; end
tStop = [];
if evalin('base', 'exist(''TB30_tend'', ''var'')')
    tStop = evalin('base', 'TB30_tend'); resDir = fullfile(resDir, 'smoke');
    if ~exist(resDir, 'dir'), mkdir(resDir); end
end
load_system(fullfile(here, [mdl '.slx']));
res = {};
for r = runList
    cn = R{r};
    assignin('base', 'TB30_case', cn);
    run(fullfile(here, 'TB30_init.m'));
    TB = evalin('base', 'TB');
    if ~isempty(tStop), TB.t_end = tStop; end
    tic; out = sim(mdl, 'StopTime', num2str(TB.t_end, '%.9g')); wall = toc;
    S = evaluate(out, TB, refDir, cn, resDir, wall);
    res{end+1} = S; %#ok<AGROW>
    fprintf('%s done (%.0f s): %s\n', cn, wall, S.verdict);
    clear out
end
evalin('base', 'clear TB30_case');
fid = fopen(fullfile(resDir, 'TB30_summary.txt'), 'w');
o2(fid, 'TB30 = TB28 circuit (A25R) with re-selected V_A clamp (E38 Q1: 2 x 1.6 ohm SP branches, resistance corners), reference E26 (same corner) / E22 / E35 model\n');
o2(fid, '%-22s %-6s %-9s %-9s %-9s %-9s %-9s %s\n', 'case', 'result', 'vA_max', 'ref', 'E_cl[J]', 'ref', 'vo_min', 'failed');
allPass = true;
for k = 1:numel(res)
    S = res{k};
    o2(fid, '%-22s %-6s %-9.2f %-9.2f %-9.1f %-9.1f %-9.3f %s\n', S.case, S.verdict, S.vA_max_1us, S.ref.vA_max, S.E_clamp_J, ...
        S.ref.E_clamp_J, S.vo_min, strjoin(S.failed, ', '));
    allPass = allPass && strcmp(S.verdict, 'PASS');
end
o2(fid, 'TB30 overall: %s\n', ternary(allPass, 'PASS', 'FAIL'));
fclose(fid);
fid = fopen(fullfile(resDir, 'TB30_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(res, 'PrettyPrint', true)); fclose(fid);
end

% =======================================================================================================
function S = evaluate(out, TB, refDir, cn, resDir, wall)
te = TB.t_event;
M = jsondecode(fileread(fullfile(refDir, ['TB30_' cn '_metrics.json'])));
SA = jsondecode(fileread(fullfile(refDir, ['TB30_' cn '_stageA.json'])));
Rf = readmatrix(fullfile(refDir, ['TB30_' cn '_ref.csv']));          % E26 1 µs: t vA vb ich iA icl
Zc = readmatrix(fullfile(refDir, ['TB30_' cn '_stageC.csv']));       % E22 1 µs
R0 = jsondecode(fileread(fullfile(refDir, ['TB30_' cn '_init.json'])));
% ---- 10 ns 신호 -----------------------------------------------------------------------------------------
t4 = out.t(:); dt4 = t4(2) - t4(1);
X = double([out.vA(:) out.vbus(:) out.iAo(:) out.icl(:) out.ich(:) out.ipath(:) out.iin(:) out.iL(:) out.vI(:) out.vo(:) ...
            out.ix(:) out.iload(:)]);
X(1, :) = X(2, :);
gcl = double(out.gcl(:));
ir2 = double(out.ir2(:)); vl1 = double(out.vleg1(:)); vls1 = double(out.vlegs1(:));
gq1 = double(out.gq1(:)); gq2 = double(out.gq2(:)); gs1 = double(out.gs1(:)); gs2 = double(out.gs2(:));
n1 = round(1e-6/dt4); m1 = floor(numel(t4)/n1);
A1 = zeros(m1, 13);                                          % [t_끝, 1 µs 평균 vA vbus iAo icl ich ipath iin iL vI vo ix iload]
for q = 1:m1
    k = (q-1)*n1 + (1:n1);
    A1(q, :) = [t4(k(end)) mean(X(k, :), 1)];
end
writematrix(A1, fullfile(resDir, ['TB30_' cn '_avg1us.csv']));
t1 = A1(:, 1);
L = struct();
w1 = t1 >= 1.0e-3;
vA_max1 = max(A1(w1, 2)); vb_max1 = max(A1(w1, 3));
vA_inst = max(X(t4 >= 1.0e-3, 1)); vb_inst = max(X(t4 >= 1.0e-3, 2));
L.C1_voltage = vA_max1 <= TB.v_lim && vb_max1 <= TB.v_lim;
% 클램프 저항 에너지(10 ns 순시 (v_A − 강하)·i_cl 적분, E26의 저항 에너지와 같은 정의)
E_cl = sum(max(X(:, 1) - TB.Vdrop, 0).*X(:, 4))*dt4;
t_on = sum(gcl > 0.5)*dt4;
P_cl_pk = max(max(X(:, 1) - TB.Vdrop, 0).*X(:, 4));
n_sw = sum(diff(gcl) > 0.5);
eTol = max(0.1*M.E_clamp_J, 10);
L.C1r_e26 = abs(vA_max1 - M.vA_max) <= 1.5 && abs(vb_max1 - M.vb_max) <= 1.5 && abs(E_cl - M.E_clamp_J) <= eTol;
% ---- 48 V·Stage C --------------------------------------------------------------------------------------
n10 = round(10e-6/dt4); m10 = floor(numel(t4)/n10);
A10 = zeros(m10, 3);
for q = 1:m10
    k = (q-1)*n10 + (1:n10);
    A10(q, :) = [t4(k(end)) mean(X(k, 10)) mean(X(k, 9))];
end
w10 = A10(:, 1) >= 1.0e-3;
vo_min = min(A10(w10, 2)); vo_max = max(A10(w10, 2));
L.C3_vo = vo_min >= TB.band(1) && vo_max <= TB.band(2) && abs(vo_min - M.vo_min) <= 0.5 && abs(vo_max - M.vo_max) <= 0.5;
w100 = round(100e-6/dt4);
ixa = movmean(X(:, 11), w100);
ix_avg_max = max(abs(ixa(t4 >= 1.0e-3)));
dev_pk = max(abs(ir2(t4 >= 1.0e-3)))/2;
L.C3_stageC_current = ix_avg_max <= 130*1.05 && dev_pk <= TB.pulse_rating_secondary;
wz = t4 > 1.0e-3;
[zp, np1] = zvs_check(t4, gq1, gq2, vl1, X(:, 9), wz);
[zs, ns1] = zvs_check(t4, gs1, gs2, vls1, X(:, 10), wz);
okz = (np1 + ns1) > 0;
if np1 > 0, okz = okz && zp <= 0.05*mean(X(wz, 9)); end
if ns1 > 0, okz = okz && zs <= 0.05*mean(X(wz, 10)); end
L.C3_zvs = okz;
% ---- Stage A(2.5 ns) ------------------------------------------------------------------------------------
I = zeros(numel(out.iA1), 8, 'single'); Sg = zeros(numel(out.st1), 8, 'int8');
for p = 1:8
    I(:, p) = out.(sprintf('iA%d', p))(:); Sg(:, p) = out.(sprintf('st%d', p))(:);
end
tA = (0:size(I, 1)-1)'*TB.dt;
mg = double(squeeze(out.mgr)); if size(mg, 2) ~= 7, mg = mg.'; end   % [동작 수, 모듈 모드 4, If, 취소 수]
nact = mg(:, 1); mcancel = mg(:, 7);
mask = R0.mask(:)';
fm = TB.fault_module;
isPathLoss = all(mask == 0); isFault = fm > 0; isSlow = strcmp(TB.kind, 'charge_slow');
if isFault, fph = [2*fm - 1, 2*fm]; else, fph = []; end
% (C4) 사건 전
SAc = struct();
mpre = tA > te - 0.2e-3 & tA <= te - 2e-6;                  % 사건 순간 강제 차단(턴오프)은 빼고 판정
if isSlow, phpre = 1:2; else, phpre = 1:8; end              % D: 충전 요청 전 경부하(모듈 1)
[zz, pk, io] = zcs_window(I(mpre, :), Sg(mpre, :), phpre);
mv = t1 > te - 0.2e-3 & t1 <= te - 2e-6;
vAm = mean(A1(mv, 2));
sh = max(abs(io - mean(io)))/abs(mean(io));
SAc.pre = struct('zcs', zz, 'Ipk', pk, 'io', io, 'vA_mean', vAm, 'vA_ref', SA.pre.vA_mean, 'zcs_ref', max(SA.pre.zcs), ...
    'Ipk_ref', max(SA.pre.Ipk), 'sharing', sh, 'sharing_ref', SA.pre.sharing, 'iAo_mean', mean(A1(mv, 4)));
if isSlow
    L.C4_stageA_pre = abs(vAm - SA.pre.vA_mean) <= 0.3;     % 충전 요청 전(경부하)은 (C5)로 판정
else
    L.C4_stageA_pre = max(zz) <= 0.05 && sh <= 0.05 && abs(vAm - SA.pre.vA_mean) <= 0.3;
end
% (C5) 모든 턴오프(사건 순간 강제 차단, 고장 모듈의 고장 순간 이후 제외)
T1n = 0; T1bad = 0; T1worst = 0; cut = zeros(1, 8); badlist = zeros(0, 4);   % 위반 [시각 ms, 위상, i_off, 반주기 첨두]
for p = 1:8
    ii = double(I(:, p)); ss = double(Sg(:, p));
    off = find(ss(1:end-1) ~= 0 & ss(2:end) == 0); on = find(ss(1:end-1) == 0 & ss(2:end) ~= 0) + 1;
    for jj = 1:numel(off)
        o = off(jj); if tA(o) < 1.0e-3, continue; end
        if (mask(p) == 0 || ismember(p, fph)) && abs(tA(o) - te) <= 3*TB.dt   % 사건 순간 게이트 차단(고장 차단): 정보
            cut(p) = abs(ii(o)); continue
        end
        if ismember(p, fph) && tA(o) >= te - 1.5*TB.dt, continue; end
        k0 = on(find(on <= o, 1, 'last')); if isempty(k0), continue; end
        pkh = max(abs(ii(k0:o))); T1n = T1n + 1;
        T1worst = max(T1worst, abs(ii(o)));
        if abs(ii(o)) > max(0.05*pkh, TB.i_abs)
            T1bad = T1bad + 1; badlist(end+1, :) = [1e3*tA(o), p, ii(o), pkh]; %#ok<AGROW>
        end
    end
end
L.C5_turnoff = T1bad == 0;
pkA = 0;
for p = 1:8
    if ismember(p, fph), msk = tA >= 1.0e-3 & tA < te; else, msk = tA >= 1.0e-3; end
    if any(msk), pkA = max(pkA, max(abs(I(msk, p)))); end
end
% 모듈 수 사건
d = find(diff(nact) ~= 0);
Ev = [1e3*t4(d + 1), nact(d + 1)];
me = SA.events; if iscell(me), me = cell2mat(cellfun(@(c) c(:)', me, 'UniformOutput', false)); end
if isempty(me), me = zeros(0, 2); end
% 사건 뒤
post = struct();
if isFault
    m = tA > te + 0.5e-3;
    ph = setdiff(1:8, fph);
    [zz, pk, io] = zcs_window(I(m, :), Sg(m, :), ph);
    sh = max(abs(io - mean(io)))/abs(mean(io));
    kf = find(tA >= te, 1);
    restart = any(any(Sg(kf + 2:end, fph) ~= 0));
    post = struct('zcs', zz, 'Ipk', pk, 'io', io, 'sharing', sh, 'zcs_ref', max(SA.final.zcs), 'Ipk_ref', max(SA.final.Ipk), ...
        'sharing_ref', SA.final.sharing, 'fault_phase_max_after_A', max(max(abs(I(m, fph)))), 'restart', restart, 'n_end', nact(end));
    L.C2_module_fault = max(pk) <= TB.pk_lim && max(zz) <= 0.05 && sh <= 0.05 && nact(end) == 3 && ~restart;
elseif isSlow
    m = tA > TB.w_hold(1) & tA <= TB.w_hold(2);
    [zz, pk, io] = zcs_window(I(m, :), Sg(m, :), 1:8);
    sh = max(abs(io - mean(io)))/abs(mean(io));
    post = struct('zcs', zz, 'Ipk', pk, 'io', io, 'sharing', sh, 'zcs_ref', max(SA.mid.zcs), 'Ipk_ref', max(SA.mid.Ipk), ...
        'sharing_ref', SA.mid.sharing, 'phase_peak_ref', SA.phase_peak);
    L.C6_charge_slow = pkA <= TB.P_rated && max(zz) <= 0.05 && sh <= 0.05;
    L.C7_modules = nact(end) == SA.n_end && size(Ev, 1) == size(me, 1) && mcancel(end) == 0;
else
    m = tA > te + 50e-6;
    post = struct('phase_max_after_50us_A', max(max(abs(I(m, :)))), 'cut_A', cut);
end
fn = fieldnames(L); pass = all(cellfun(@(f) L.(f), fn));
failed = fn(~cellfun(@(f) L.(f), fn))';
% ---- 요약 ---------------------------------------------------------------------------------------------------
S = struct('case', cn, 'verdict', ternary(pass, 'PASS', 'FAIL'), 'failed', {failed}, 'limits', L, 'wall_s', wall, ...
    'vA_max_1us', vA_max1, 'vbus_max_1us', vb_max1, 'vA_max_inst', vA_inst, 'vbus_max_inst', vb_inst, ...
    'E_clamp_J', E_cl, 't_clamp_on_ms', 1e3*t_on, 'P_clamp_pk_W', P_cl_pk, 'clamp_on_count', n_sw, ...
    'vo_min', vo_min, 'vo_max', vo_max, 'ix_avg100_max', ix_avg_max, 'dev_peak_A', dev_pk, ...
    'zvs', struct('primary_max_V', zp, 'primary_n', np1, 'secondary_max_V', zs, 'secondary_n', ns1), ...
    'stageA_pre', SAc.pre, 'stageA_post', post, 'turnoffs', struct('n', T1n, 'bad', T1bad, 'worst_A', T1worst, 'violations', badlist), ...
    'phase_peak_A', pkA, 'cut_A', cut, 'module_events', Ev, 'module_events_ref', me, 'n_end', nact(end), 'n_mcancel', mcancel(end), ...
    'ref', struct('vA_max', M.vA_max, 'vb_max', M.vb_max, 'E_clamp_J', M.E_clamp_J, 't_clamp_on_ms', M.t_clamp_on_ms, ...
                  'vo_min', M.vo_min, 'vo_max', M.vo_max));
fid = fopen(fullfile(resDir, ['TB30_' cn '_summary.txt']), 'w');
o2(fid, 'TB30 case %s, V_bat %.0f V, event %.2f ms, dt %.2f ns, wall %.0f s\n', cn, TB.vbat, 1e3*te, 1e9*TB.dt, wall);
o2(fid, '(1) criteria:\n');
for k = 1:numel(fn), o2(fid, '    %-20s %s\n', fn{k}, ternary(L.(fn{k}), 'PASS', 'FAIL')); end
o2(fid, '    V_A 1 us max %.2f V (E26 %.2f), bus %.2f V (E26 %.2f); instantaneous V_A %.2f V, bus %.2f V (limit %.0f V)\n', ...
    vA_max1, M.vA_max, vb_max1, M.vb_max, vA_inst, vb_inst, TB.v_lim);
o2(fid, '    clamp: energy %.1f J (E26 %.1f J), on %.3f ms (E26 %.3f ms), peak %.0f kW, turn-ons %d (E26 %d), clamp current max %.1f A\n', E_cl, M.E_clamp_J, 1e3*t_on, ...
    M.t_clamp_on_ms, P_cl_pk/1e3, n_sw, M.n_on, max(X(:, 4)));
o2(fid, '    clamp branch current max (total / 2): %.1f A, corner resistance %.4f ohm (equivalent), drop %.2f V\n', max(X(:, 4))/2, TB.Rclamp, TB.Vdrop);
o2(fid, '    48 V (10 us mean, from 1 ms) %.3f-%.3f V (E22 %.3f-%.3f, band %.2f-%.2f); Stage C 100 us max %.1f A, secondary peak %.1f A\n', ...
    vo_min, vo_max, M.vo_min, M.vo_max, TB.band(1), TB.band(2), ix_avg_max, dev_pk);
o2(fid, '    Stage C ZVS: primary %.2f V (%d edges), secondary %.2f V (%d edges)\n', zp, np1, zs, ns1);
a = SAc.pre;
o2(fid, '    Stage A pre: ZCS max %.2f %% (ref %.2f %%), Ipk max %.1f A (ref %.1f A), sharing %.2f %%, V_A %.3f V (ref %.3f V), i_A %.1f A\n', ...
    100*max(a.zcs), 100*a.zcs_ref, max(a.Ipk), a.Ipk_ref, 100*a.sharing, a.vA_mean, a.vA_ref, a.iAo_mean);
o2(fid, '    Stage A turn-offs after 1 ms (excluding forced cuts): %d, violations %d, worst %.2f A; phase peak %.1f A (P_rated %.1f A, fault limit %.1f A)\n', ...
    T1n, T1bad, T1worst, pkA, TB.P_rated, TB.pk_lim);
o2(fid, '    modules: events %s (model %s), end %d (model %d), cancels %d\n', mat2str(round(Ev, 3)), mat2str(me), nact(end), SA.n_end, mcancel(end));
for q = 1:size(badlist, 1)
    o2(fid, '      violation: %.4f ms, phase %d, i_off %.3f A, half-cycle peak %.2f A\n', badlist(q, :));
end
if isFault || isSlow
    o2(fid, '    Stage A after event: ZCS max %.2f %% (ref %.2f %%), Ipk max %.1f A (ref %.1f A), sharing %.2f %% (ref %.2f %%)\n', ...
        100*max(post.zcs), 100*post.zcs_ref, max(post.Ipk), post.Ipk_ref, 100*post.sharing, 100*post.sharing_ref);
else
    o2(fid, '    Stage A forced cut currents %s A, phase max 50 us after cut %.2f A\n', mat2str(round(cut, 1)), post.phase_max_after_50us_A);
end
fclose(fid);
fid = fopen(fullfile(resDir, ['TB30_' cn '_summary.json']), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);
% ---- 그림 ---------------------------------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [50 50 1200 950]);
tl = tiledlayout(f, 4, 1, 'TileSpacing', 'compact');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
plot(ax, 1e3*t1, A1(:, 2), 'b', 1e3*Rf(:, 1), Rf(:, 2), 'r--', 1e3*t1, A1(:, 3), 'c');
yline(ax, TB.v_lim, 'k:'); ylabel(ax, '[V]'); legend(ax, 'V_A 회로(1 µs)', 'V_A E26', '버스 회로', 'Location', 'best');
ax = nexttile(tl); hold(ax, 'on'); grid(ax, 'on');
plot(ax, 1e3*t1, A1(:, 6), 'g', 1e3*t1, -A1(:, 4), 'b', 1e3*t1, A1(:, 5), 'm', 1e3*Rf(:, 1), Rf(:, 6), 'r--');
ylabel(ax, '[A]'); legend(ax, '충전기', 'Stage A(→배터리)', '클램프', '클램프 E26', 'Location', 'best');
ax = nexttile(tl); plot(ax, 1e3*A10(:, 1), A10(:, 2), 'b', 1e3*Zc(:, 1), Zc(:, 6), 'r--'); grid(ax, 'on');
yline(ax, TB.band, 'k:'); ylabel(ax, 'v_o [V]'); legend(ax, '회로(10 µs)', 'E22(E26 버스)', 'Location', 'best');
ax = nexttile(tl); plot(ax, 1e3*t1, A1(:, 8), 'b', 1e3*t1, A1(:, 13), 'k'); grid(ax, 'on');
ylabel(ax, '[A]'); xlabel(ax, '시간 [ms]'); legend(ax, 'Stage C 입력', '400 V 부하', 'Location', 'best');
title(tl, sprintf('TB30 %s', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB30_' cn '_response.png']), 'Resolution', 130); close(f);
f = figure('Visible', 'off', 'Position', [50 50 1200 950]);
tl = tiledlayout(f, 3, 1, 'TileSpacing', 'compact');
k0 = find(tA >= te - 15e-6, 1); k1 = find(tA <= te + 25e-6, 1, 'last');
ax = nexttile(tl); plot(ax, 1e6*(tA(k0:20:k1) - te), double(I(k0:20:k1, :))); grid(ax, 'on');
ylabel(ax, '위상 공진전류 [A]'); xlabel(ax, '사건 기준 시간 [µs]'); title(ax, '사건 전후 8위상');
k0 = find(tA >= tA(end) - 20e-6, 1);
ax = nexttile(tl); plot(ax, 1e6*tA(k0:end), double(I(k0:end, :))); grid(ax, 'on');
ylabel(ax, '위상 공진전류 [A]'); xlabel(ax, '시간 [µs]'); title(ax, '끝 20 µs');
ax = nexttile(tl); stairs(ax, 1e3*t4(1:100:end), nact(1:100:end), 'b'); grid(ax, 'on'); ylim(ax, [0 4.5]);
ylabel(ax, '동작 모듈 수'); xlabel(ax, '시간 [ms]'); title(ax, '모듈 관리기');
title(tl, sprintf('TB30 %s: Stage A', strrep(cn, '_', ' ')));
exportgraphics(f, fullfile(resDir, ['TB30_' cn '_stageA.png']), 'Resolution', 130); close(f);
end

function [zz, pk, io] = zcs_window(I, Sg, ph)
% 창 안 위상별 턴오프 전류/피크(마지막 도통 표본), 피크, 위상 평균 출력전류(충전 구간 +i, 방전 구간 −i)
zz = zeros(1, numel(ph)); pk = zeros(1, numel(ph)); io = zeros(1, numel(ph));
for j = 1:numel(ph)
    i = double(I(:, ph(j))); s = double(Sg(:, ph(j)));
    offk = find(s(1:end-1) > 0.5 & s(2:end) < 0.5);
    pk(j) = max(abs(i));
    if isempty(offk), zz(j) = 0; else, zz(j) = max(abs(i(offk)))/max(pk(j), 1e-6); end
    io(j) = mean(i.*(s == 1) - i.*(s == 2));
end
end

function [vmax, ne] = zvs_check(t, gh, gl, vleg, vrail, win)
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
