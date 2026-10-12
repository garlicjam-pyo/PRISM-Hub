function run_TB03()
%RUN_TB03  TB03(DAB 개루프 위상 계단)을 실행하고 검증 모델(E12 스위칭 ODE의 DAB 부분)과 대조한다.
%
%   기준: ref/TB03_ref_python.json·csv  (ref/make_ref_TB03.py — run_core의 DAB 에지 일정·데드타임·영전류 클램프를
%         그대로 옮기고 버스 400 V, 링크 100 V를 고정한 계산)
%   판정
%     (a) SPS 영역(δ ≥ 2t_d: 0.4, 0.8, −0.5 rad): 정상 링크전류가 검증 모델과 1 A + 2 % 안,
%         SPS 식과 1.5 A + 3 % 안
%     (b) 변압기 직류 편류(반송파 주기 평균 i_L): 위상 부호 반전 직후 생기는 편류 크기가 검증 모델과 1 A 안,
%         정상 단계(0.4, 0.8 rad)의 편류 0.5 A 이하. 감쇠 시정수는 정보(회로는 출력용량 충방전으로 더 빨리 준다)
%     (c) 게이트 생성기의 링크전류 주기 평균(aux 1)이 측정 파형의 주기 평균과 0.1 A 안
%     (d) 데드타임 영역(δ < 2t_d: 0.15, 0.08 rad)은 정보: 회로·검증 모델·SPS를 비교하고 C_oss 민감도(20/100/500 pF)를 기록
%   결과: results/TB03_summary.txt·json, TB03_phase_steps.png, TB03_deadtime_region.png, 회로도 그림

here = fileparts(mfilename('fullpath'));
mdl  = 'TB03_StageB_DAB';
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
evalin('base', 'clear TB_override');
run(fullfile(here, 'TB03_init.m'));
load_system(fullfile(here, [mdl '.slx']));
R = simulate(mdl);
fprintf('simulation done: %.1f s wall, %d steps\n', R.wall, numel(R.t));

T = 1/TB.B.fs; td = TB.B.td_d; n = TB.B.n;
k = n*TB.Vbus/(2*pi*TB.B.fs*TB.B.Ldab);
Isps = @(p) k*p.*(1 - abs(p)/pi);
ref = jsondecode(fileread(fullfile(here, 'ref', 'TB03_ref_python.json')));
w = readmatrix(fullfile(here, 'ref', 'TB03_ref_python.csv'));      % [t_center, iL 주기 평균, 링크전류 주기 평균]
nseg = numel(TB.ph_steps);

% ---- (a)(d) 단계별 정상 링크전류 --------------------------------------------------------------------
seg = zeros(nseg, 9);   % [phi delta_ns I_sim I_py I_SPS err_py tol_py err_sps passA]
for s = 1:nseg
    p = TB.ph_steps(s); d = abs(p)/(2*pi)*T;
    Im = segmean(R, TB, s, T);
    Ipy = ref.segments(s).I_link;
    tolPy = 1.0 + 0.02*abs(Ipy); tolS = 1.5 + 0.03*abs(Isps(p));
    if d >= 2*td
        ok = abs(Im - Ipy) <= tolPy && abs(Im - Isps(p)) <= tolS;
    else
        ok = NaN;                                    % 데드타임 영역: 정보
    end
    seg(s, :) = [p, 1e9*d, Im, Ipy, Isps(p), Im - Ipy, tolPy, Im - Isps(p), ok];
end
passA = all(seg(~isnan(seg(:, 9)), 9) == 1);

% ---- (b) 직류 편류 ------------------------------------------------------------------------------
% 위상 부호가 바뀌는 계단(0.8 → −0.5 rad)에서는 데드타임 동안의 전압·시간 오차가 전이 반주기에서 한쪽으로 쌓여
% 변압기 전류에 직류 편류가 생긴다(검증 모델에도 있는 실제 현상). 판정은 편류가 생기는 크기의 일치로 하고,
% 감쇠 속도는 정보로 남긴다: 검증 모델은 권선저항 시정수(L/R = 555 µs)로만 줄지만, 회로에서는 출력용량 충방전
% 시간이 전류 크기에 따라 달라 편류를 되돌리는 전압·시간 차가 생긴다(C_oss 민감도로 확인).
nper = floor(R.t(end)/T + 1e-9);
dcp = permeans(R, T, TB.dt, nper);                   % [t_center, i_L 주기 평균, 링크전류 주기 평균]
qa = round(TB.t_steps(3)/T) + 2;                     % 부호 반전 계단 다음 첫 주기(207.5 µs)
qb = round(TB.t_steps(4)/T);                         % 그 단계의 마지막 주기(297.5 µs)
biasSim = dcp(qa, 2); biasPy = w(qa, 2);
passB1 = abs(biasSim - biasPy) <= 1.0;
q1 = round(TB.t_steps(2)/T) + (-9:0); q2 = round(TB.t_steps(3)/T) + (-9:0);   % 0.4, 0.8 rad 단계의 마지막 10주기
steadyBias = max(abs(dcp([q1 q2], 2)));
passB2 = steadyBias <= 0.5;
passB = passB1 && passB2;
tau = @(b1, b2) (dcp(qb, 1) - dcp(qa, 1))/log(b1/b2);
tauSim = tau(dcp(qa, 2), dcp(qb, 2)); tauPy = tau(w(qa, 2), w(qb, 2));

% ---- (c) 게이트 생성기 주기 평균 ------------------------------------------------------------------
avgErr = 0;
for q = 2:nper
    kq = round(q*T/TB.dt);
    if kq + 1 <= numel(R.t)
        mk = (R.t >= (q-1)*T - 1.5*TB.dt) & (R.t < q*T - 1.5*TB.dt);   % 입력은 한 간격 지연
        avgErr = max(avgErr, abs(R.aux(kq + 1, 1) - mean(R.il(mk))));
    end
end
passC = avgErr <= 0.1;

% ---- (d) C_oss 민감도(데드타임 영역) ---------------------------------------------------------------
cossList = [20e-12 100e-12 500e-12];
sens = zeros(numel(cossList), nseg); tauC = zeros(1, numel(cossList)); biasC = zeros(1, numel(cossList));
for c = 1:numel(cossList)
    if cossList(c) == TB.B.Coss_d
        for s = 1:nseg, sens(c, s) = seg(s, 3); end
        tauC(c) = tauSim; biasC(c) = biasSim;
        continue
    end
    ov = struct('B', TB.B); ov.B.Coss_d = cossList(c);
    assignin('base', 'TB_override', ov);
    Rc = simulate(mdl);
    for s = 1:nseg, sens(c, s) = segmean(Rc, TB, s, T); end
    pc = permeans(Rc, T, TB.dt, nper);
    tauC(c) = (pc(qb, 1) - pc(qa, 1))/log(pc(qa, 2)/pc(qb, 2)); biasC(c) = pc(qa, 2);
    fprintf('C_oss %.0f pF: I_link = %s A\n', 1e12*cossList(c), mat2str(round(sens(c, :), 2)));
end
% 적분 간격 점검: 2.5 ns(게이트 격자도 같이 바꿈)로 다시 계산
ov = struct('dt', TB.dt/2, 'gate_prm', [TB.dt/2, 2*TB.gate_prm(2), 2*TB.gate_prm(3), 2*TB.gate_prm(4), TB.gate_prm(5)]);
assignin('base', 'TB_override', ov);
Rh = simulate(mdl);
dtchk = zeros(1, nseg);
for s = 1:nseg, dtchk(s) = segmean(Rh, TB, s, T); end
fprintf('dt 2.5 ns: I_link = %s A\n', mat2str(round(dtchk, 2)));
evalin('base', 'clear TB_override');
run(fullfile(here, 'TB03_init.m'));

pass = passA && passB && passC;
fid = fopen(fullfile(resDir, 'TB03_summary.txt'), 'w');
out2(fid, 'TB03 Stage B DAB open loop (V_bus 400 V, V_link 100 V matched): Simscape circuit vs verification model (E12 DAB part)\n');
out2(fid, '%8s %9s %10s %10s %10s %9s %7s %9s %8s\n', 'phi[rad]', 'delta[ns]', 'I_sim[A]', 'I_py[A]', 'I_SPS[A]', 'sim-py', 'tol', 'sim-SPS', 'result');
for s = 1:nseg
    if isnan(seg(s, 9)), r = 'info'; elseif seg(s, 9), r = 'PASS'; else, r = 'FAIL'; end
    out2(fid, '%+8.3f %9.1f %+10.3f %+10.3f %+10.3f %+9.3f %7.2f %+9.3f %8s\n', seg(s, 1:8), r);
end
out2(fid, '(a) steady link current in SPS region (delta >= 2 t_d): %s\n', ternary(passA, 'PASS', 'FAIL'));
out2(fid, '(b) transformer DC bias after the phase reversal 0.8 -> -0.5 rad (period mean of i_L, first full period): Simscape %+.2f A, verification model %+.2f A, diff %.2f A (limit 1 A): %s\n', ...
    biasSim, biasPy, abs(biasSim - biasPy), ternary(passB1, 'PASS', 'FAIL'));
out2(fid, '    steady bias in the 0.4 / 0.8 rad segments: max %.3f A (limit 0.5 A): %s\n', steadyBias, ternary(passB2, 'PASS', 'FAIL'));
out2(fid, '    decay time constant (info): verification model %.0f us (L/R = %.0f us); Simscape C_oss 20/100/500 pF: %s us\n', ...
    1e6*tauPy, 1e6*TB.B.Ldab/TB.B.Rdab, mat2str(round(1e6*tauC)));
out2(fid, '(c) gate generator period-average link current vs measured: max diff %.4f A (limit 0.1 A): %s\n', avgErr, ternary(passC, 'PASS', 'FAIL'));
out2(fid, '(d) dead-time region (info), link current [A] by C_oss:\n');
for c = 1:numel(cossList)
    out2(fid, '    C_oss %4.0f pF: phi 0.15 -> %+7.2f A, phi 0.08 -> %+7.2f A   (py %+6.2f / %+6.2f, SPS %+6.2f / %+6.2f)\n', ...
        1e12*cossList(c), sens(c, 4), sens(c, 5), seg(4, 4), seg(5, 4), seg(4, 5), seg(5, 5));
end
out2(fid, 'step-size check, link current [A] at 5 ns / 2.5 ns:');
for s = 1:nseg, out2(fid, '  %+.2f: %+.2f / %+.2f', TB.ph_steps(s), seg(s, 3), dtchk(s)); end
out2(fid, '\n');
out2(fid, 'VERDICT: %s\n', ternary(pass, 'PASS', 'FAIL'));
fclose(fid);
S = struct('segments', seg, 'dc_bias_after_reversal_sim_A', biasSim, 'dc_bias_after_reversal_py_A', biasPy, ...
    'dc_bias_steady_max_A', steadyBias, 'dc_decay_tau_py_us', 1e6*tauPy, 'dc_decay_tau_sim_us_by_coss', 1e6*tauC, ...
    'period_means_sim', dcp, 'dt_check_2p5ns_A', dtchk, ...
    'gate_avg_err_A', avgErr, 'coss_pF', 1e12*cossList, 'coss_sensitivity_A', sens, 'verdict', ternary(pass, 'PASS', 'FAIL'), ...
    'k_A_per_rad', k, 'model', mdl, 'date', char(datetime('now')), 'matlab', version);
fid = fopen(fullfile(resDir, 'TB03_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);

% ---- 그림 1: 위상 계단 응답 ---------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 1000 820]);
tl = tiledlayout(f, 4, 1, 'TileSpacing', 'compact');
nexttile; plot(1e6*R.t, R.ph, 'LineWidth', 1.3); grid on; ylabel('\phi [rad]');
title('phase command (applied at the next half-period centre)');
nexttile; plot(1e6*R.t(1:2:end), R.iL(1:2:end), 'LineWidth', 0.6); grid on; ylabel('i_L [A]');
title('leakage current (primary side), Simscape circuit');
nexttile; hold on; grid on;
stairs(1e6*(dcp(:, 1) - T/2), dcp(:, 2), 'LineWidth', 1.4);
stairs(1e6*(w(:, 1) - T/2), w(:, 2), '--', 'LineWidth', 1.2);
ylabel('period mean of i_L [A]'); legend('Simscape', 'verification model (E12)', 'Location', 'southeast');
title(sprintf('DC bias after reversal: Simscape %.2f A, model %.2f A; decay \\tau %.0f vs %.0f \\mus', biasSim, biasPy, 1e6*tauSim, 1e6*tauPy));
nexttile; hold on; grid on;
plot(1e6*R.t(1:5:end), R.il(1:5:end), 'Color', [0.75 0.75 0.75]);
kk = R.t >= T;   % 첫 주기는 출력용량 초기 충전 과도가 섞이므로 두 번째 주기부터 표시
plot(1e6*R.t(kk), R.aux(kk, 1), 'LineWidth', 1.5);
stairs(1e6*(w(:, 1) + T/2), w(:, 3), '--', 'LineWidth', 1.2);
ylabel('link current [A]'); xlabel('t [\mus]'); ylim([-90 120]);
legend('instantaneous', 'period average (gate generator, Simscape)', 'period average (verification model)', 'Location', 'eastoutside');
title(tl, 'TB03 DAB open loop: phase steps 0.4 \rightarrow 0.8 \rightarrow -0.5 \rightarrow 0.15 \rightarrow 0.08 rad');
exportgraphics(f, fullfile(resDir, 'TB03_phase_steps.png'), 'Resolution', 150); close(f);

% ---- 그림 2: 데드타임 영역 ---------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 780 500]); hold on; grid on;
pp = linspace(0, 0.9, 400); dd = pp/(2*pi)*T; Idt = zeros(size(pp));
for q = 1:numel(pp)
    if dd(q) >= 2*td, Idt(q) = Isps(pp(q)); elseif dd(q) > td, Idt(q) = Isps(2*pi*2*(dd(q) - td)/T); end
end
plot(pp, Isps(pp), ':', 'LineWidth', 1.2); plot(pp, Idt, '-', 'Color', [0.5 0.5 0.5], 'LineWidth', 1.2);
plot(abs(seg(:, 1)), abs(seg(:, 4)), 'ks', 'MarkerSize', 8);
mk = {'o', 'd', '^'};
for c = 1:numel(cossList)
    plot(abs(TB.ph_steps), abs(sens(c, :)), mk{c}, 'MarkerSize', 7, 'LineWidth', 1.2);
end
xline(2*pi*td/T, ':', 't_d'); xline(2*pi*2*td/T, ':', '2t_d');
xlabel('|\phi| [rad]'); ylabel('|steady link current| [A]');
legend([{'SPS (no dead time)', 'E12 dead-time model', 'verification model (E12 DAB)'}, ...
    arrayfun(@(c) sprintf('Simscape, C_{oss} %.0f pF', 1e12*c), cossList, 'UniformOutput', false)], 'Location', 'southeast');
title('TB03: DAB transfer with 100 ns dead time (V_{bus} = n V_{link})');
exportgraphics(f, fullfile(resDir, 'TB03_deadtime_region.png'), 'Resolution', 150); close(f);

sl_export_png({mdl, [mdl '/DAB_Primary'], [mdl '/Gate_StageB']}, resDir);
fprintf('results written to %s\n', resDir);
end

% ======================================================================================================
function R = simulate(mdl)
% 모델을 실행하고 판정에 쓰는 신호를 열 벡터(보조 출력은 N×6)로 정리한다.
tic; out = sim(mdl); R.wall = toc;
R.t = out.t(:); R.iL = out.iL(:); R.il = out.ilink(:); R.ph = out.ph(:);
a = out.aux;
if ndims(a) == 3, a = reshape(a, size(a, 1)*size(a, 2), [])'; end   % 열 벡터 출력은 6×1×N 배열로 저장된다
if size(a, 2) ~= 6, a = a'; end
R.aux = a;
end

function dcp = permeans(R, T, dt, nper)
% 반송파 주기별 [중심 시각, i_L 평균, 링크전류 평균]
dcp = zeros(nper, 3);
for q = 1:nper
    mk = (R.t >= (q-1)*T - dt/2) & (R.t < q*T - dt/2);
    dcp(q, :) = [(q - 0.5)*T, mean(R.iL(mk)), mean(R.il(mk))];
end
end

function Im = segmean(R, TB, s, T)
% 단계 s의 마지막 TB.neval 주기 평균 링크전류
te = TB.t_steps(s) + 100e-6;
msk = (R.t >= te - TB.neval*T - TB.dt/2) & (R.t < te - TB.dt/2);
Im = mean(R.il(msk));
end

function out2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
