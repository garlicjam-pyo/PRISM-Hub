function run_TB05()
%RUN_TB05  TB05(Stage C 대칭 CLLC 개루프)를 부하 3개로 실행하고 검증 모델(E10 스위칭 ODE)과 대조한다.
%
%   기준: ref/TB05_ref_python.json(사례별 지표), ref/TB05_ref_python_wave_3kW.csv(3 kW 마지막 3주기 파형)
%         (ref/make_ref_TB05.py — E10_stage_c_cllc.simulate와 같은 식·적분)
%   판정(사례마다 2000주기 계산 후 마지막 100주기 = 정상상태, 기준값도 같은 창)
%     (a) 출력전압: 검증 모델 ±0.3 V,  이득 V_o·n/V_in = 1 ± 3 %(고정이득 설계 요구)
%     (b) 1차 공진전류 RMS, 2차 전류 RMS: 검증 모델 ±3 %
%     (c) 자화 전류 첨두: 검증 모델 ±5 %,  스위칭(꺼짐) 순간 1차 전류: 검증 모델 ±10 %
%     (d) ZVS: 1차 스위치가 켜지기 직전 V_ds ≤ 5 % V_in (레그 1의 상·하측, 평가 창의 모든 켜짐)
%     (e) 3 kW 파형: 1차 공진전류의 정규화 RMS 차(검증 모델 파형 대비) ≤ 10 %
%   정보: 효율(입력·출력 전력), 출력 리플, 레그 전이 시간, 적분 간격 5 ns 결과(3 kW, 통합 모델 간격)
%   결과: results/TB05_summary.txt·json, TB05_waveforms_3kW.png, TB05_zvs_transition.png, TB05_output_voltage.png, 회로도 그림

here = fileparts(mfilename('fullpath'));
mdl  = 'TB05_StageC_CLLC';
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
evalin('base', 'clear TB_override');
ref = jsondecode(fileread(fullfile(here, 'ref', 'TB05_ref_python.json')));
wref = readmatrix(fullfile(here, 'ref', 'TB05_ref_python_wave_3kW.csv'));   % t ir1 vcr1 im ir2_sec Vo vp
load_system(fullfile(here, [mdl '.slx']));

PoList = [ref.cases.Po];
nc = numel(PoList);
M = cell(nc, 1); Rk = cell(nc, 1); Rv = cell(nc, 1);
for c = 1:nc
    assignin('base', 'TB05_Po', PoList(c));
    run(fullfile(here, 'TB05_init.m'));
    TB = evalin('base', 'TB');
    R = simulate(mdl);
    fprintf('P_o %4.0f W: simulation done, %.1f s wall, %d steps\n', PoList(c), R.wall, numel(R.t));
    M{c} = metrics(R, TB);
    M{c}.wall_s = R.wall;
    Rk{c} = keep_tail(R, TB.t_end - 5*TB.T);                 % 그림용: 마지막 5주기만 전 해상도로 보관(메모리 절약)
    dd = 1:200:numel(R.t); Rv{c} = [R.t(dd) R.vo(dd)];   % 출력전압 전 구간(1 µs 간격)
    clear R
end

% ---- 판정 -----------------------------------------------------------------------------------------
rows = zeros(nc, 16);
pass = true;
for c = 1:nc
    m = M{c}; r = ref.cases(c);
    okV   = abs(m.Vo - r.Vo) <= 0.3;
    okG   = abs(m.gain - 1) <= 0.03;
    okIp  = abs(m.Ipri_rms/r.Ipri_rms - 1) <= 0.03;
    okIs  = abs(m.Isec_rms/r.Isec_rms - 1) <= 0.03;
    okIm  = abs(m.Im_pk/r.Im_pk - 1) <= 0.05;
    okIsw = abs(m.i_sw/r.i_sw - 1) <= 0.10;
    okZ   = m.vds_on_max <= 0.05*TB.Vin;
    ok = okV && okG && okIp && okIs && okIm && okIsw && okZ;
    pass = pass && ok;
    rows(c, :) = [r.Po, m.Vo, r.Vo, m.gain, m.Ipri_rms, r.Ipri_rms, m.Isec_rms, r.Isec_rms, ...
                  m.Im_pk, r.Im_pk, m.i_sw, r.i_sw, m.vds_on_max, m.eff, m.Vo_ripple, ok];
end

% (e) 3 kW 파형 대조: 검증 모델의 시각 격자로 회로 파형을 보간
c3 = find(PoList == 3000, 1);
R3 = Rk{c3};
tq = wref(:, 1);
w.ir1 = interp1(R3.t, R3.ir1, tq); w.im = interp1(R3.t, R3.im, tq); w.ir2 = interp1(R3.t, R3.ir2, tq);
w.vo  = interp1(R3.t, R3.vo, tq);
nr = @(a, b) sqrt(mean((a - b).^2))/sqrt(mean(b.^2));
wave = struct('ir1', nr(w.ir1, wref(:, 2)), 'im', nr(w.im, wref(:, 4)), 'ir2', nr(w.ir2, wref(:, 5)));
okW = wave.ir1 <= 0.10;
pass = pass && okW;

% 정보: 적분 간격 5 ns(3 kW) — 통합 모델(TB06)의 간격. 후진 오일러 수치 감쇠의 영향을 기록한다
ov = struct('Po', 3000, 'dt', 5e-9);
assignin('base', 'TB_override', ov);
assignin('base', 'TB05_Po', 3000);
run(fullfile(here, 'TB05_init.m'));
Rd = simulate(mdl);
md = metrics(Rd, evalin('base', 'TB'));
fprintf('dt 5 ns: Vo %.3f V, Ipri %.3f A, Im_pk %.3f A, vds_on %.2f V, P_in - P_out %.1f W (%.1f s wall)\n', md.Vo, md.Ipri_rms, md.Im_pk, md.vds_on_max, md.Pin - md.Pout, Rd.wall);
clear Rd
evalin('base', 'clear TB_override');
assignin('base', 'TB05_Po', 3000);
run(fullfile(here, 'TB05_init.m'));
TB = evalin('base', 'TB');

% ---- 요약 ------------------------------------------------------------------------------------------
fid = fopen(fullfile(resDir, 'TB05_summary.txt'), 'w');
out2(fid, 'TB05 Stage C symmetric CLLC open loop (400 V -> 48 V, 250 kHz at resonance): Simscape circuit vs verification model (E10)\n');
out2(fid, 'evaluation window: last %d of %d switching periods (steady state; reference uses the same window)\n', TB.neval, TB.ncyc);
out2(fid, '%6s | %8s %8s | %6s | %8s %8s | %8s %8s | %7s %7s | %6s %6s | %7s | %6s | %7s | %s\n', 'Po[W]', 'Vo_sim', 'Vo_py', 'gain', ...
    'Ipri_sim', 'Ipri_py', 'Isec_sim', 'Isec_py', 'Im_sim', 'Im_py', 'isw_s', 'isw_p', 'Vds_on', 'eff', 'ripple', 'result');
for c = 1:nc
    out2(fid, '%6.0f | %8.3f %8.3f | %6.4f | %8.3f %8.3f | %8.2f %8.2f | %7.3f %7.3f | %6.2f %6.2f | %7.2f | %6.4f | %7.3f | %s\n', ...
        rows(c, 1:15), ternary(rows(c, 16), 'PASS', 'FAIL'));
end
out2(fid, 'limits: Vo +-0.3 V vs model, gain 1 +-3 %%, Ipri/Isec rms +-3 %%, Im peak +-5 %%, i_sw +-10 %%, V_ds before turn-on <= %.0f V\n', 0.05*TB.Vin);
out2(fid, '(e) 3 kW waveform, normalised rms difference vs model: i_r1 %.2f %% (limit 10 %%): %s;  i_m %.2f %%, i_r2 %.2f %% (info)\n', ...
    100*wave.ir1, ternary(okW, 'PASS', 'FAIL'), 100*wave.im, 100*wave.ir2);
for c = 1:nc
    out2(fid, 'P_o %4.0f W: leg-1 transition (turn-off -> 90 %% swing) %.1f ns of t_d %.0f ns, P_in %.1f W, P_out %.1f W\n', ...
        PoList(c), 1e9*M{c}.t_tr, 1e9*TB.C.td, M{c}.Pin, M{c}.Pout);
end
out2(fid, 'integration step %.2f ns (backward Euler). Info, 3 kW at 5 ns (TB06 step): Vo %.3f V (%.3f), Ipri %.3f A (%.3f), Isec %.2f A (%.2f), Im_pk %.3f A (%.3f), P_in - P_out %.1f W (%.1f)\n', ...
    1e9*TB.dt, md.Vo, M{c3}.Vo, md.Ipri_rms, M{c3}.Ipri_rms, md.Isec_rms, M{c3}.Isec_rms, md.Im_pk, M{c3}.Im_pk, md.Pin - md.Pout, M{c3}.Pin - M{c3}.Pout);
out2(fid, '  (P_in - P_out includes the numerical damping of backward Euler in the resonant tank; switch and rectifier conduction loss is about 2 W at 3 kW)\n');
out2(fid, 'VERDICT: %s\n', ternary(pass, 'PASS', 'FAIL'));
fclose(fid);
S = struct('cases', {M}, 'ref', ref.cases, 'table_cols', {{'Po', 'Vo_sim', 'Vo_py', 'gain', 'Ipri_sim', 'Ipri_py', 'Isec_sim', ...
    'Isec_py', 'Im_sim', 'Im_py', 'isw_sim', 'isw_py', 'Vds_on_max', 'eff', 'Vo_ripple', 'pass'}}, 'table', rows, ...
    'wave_nrmse_3kW', wave, 'info_5ns_3kW', md, 'dt_ns', 1e9*TB.dt, 'verdict', ternary(pass, 'PASS', 'FAIL'), ...
    'model', mdl, 'date', char(datetime('now')), 'matlab', version);
fid = fopen(fullfile(resDir, 'TB05_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(S, 'PrettyPrint', true)); fclose(fid);

% ---- 그림 1: 3 kW 파형(마지막 3주기) -------------------------------------------------------------
T = TB.T; tus = 1e6*(tq - tq(1));
f = figure('Visible', 'off', 'Position', [100 100 1000 860]);
tl = tiledlayout(f, 4, 1, 'TileSpacing', 'compact');
nexttile; hold on; grid on;
plot(tus, interp1(R3.t, R3.vleg1, tq), 'LineWidth', 1.1); plot(tus, 400*interp1(R3.t, R3.gq1, tq, 'previous'), ':', 'LineWidth', 1.0);
ylabel('[V]'); legend('v_{leg1} (Simscape)', '400 \times gate Q1', 'Location', 'eastoutside'); title('primary leg 1 node voltage and gate');
nexttile; hold on; grid on;
plot(tus, w.ir1, 'LineWidth', 1.3); plot(tus, wref(:, 2), '--', 'LineWidth', 1.2);
plot(tus, w.im, 'LineWidth', 1.1); plot(tus, wref(:, 4), '--', 'LineWidth', 1.0);
ylabel('[A]'); legend('i_{r1} Simscape', 'i_{r1} model (E10)', 'i_m Simscape', 'i_m model', 'Location', 'eastoutside');
title(sprintf('primary resonant and magnetising current (nrmse i_{r1} %.1f %%, i_m %.1f %%)', 100*wave.ir1, 100*wave.im));
nexttile; hold on; grid on;
plot(tus, w.ir2, 'LineWidth', 1.3); plot(tus, wref(:, 5), '--', 'LineWidth', 1.2);
ylabel('[A]'); legend('i_{r2} Simscape', 'i_{r2} model', 'Location', 'eastoutside');
title(sprintf('secondary resonant current (nrmse %.1f %%)', 100*wave.ir2));
nexttile; hold on; grid on;
plot(tus, w.vo, 'LineWidth', 1.3); plot(tus, wref(:, 6), '--', 'LineWidth', 1.2);
ylabel('V_o [V]'); xlabel(sprintf('t - %.0f \\mus [\\mus]', 1e6*tq(1))); legend('Simscape', 'model', 'Location', 'eastoutside');
title('output voltage');
title(tl, sprintf('TB05 Stage C CLLC, 3 kW, last 3 periods (f_s = f_r = 250 kHz, T = %.0f \\mus)', 1e6*T));
exportgraphics(f, fullfile(resDir, 'TB05_waveforms_3kW.png'), 'Resolution', 150); close(f);

% ---- 그림 2: ZVS 전이(꺼짐 → 켜짐), 3 kW와 0.3 kW --------------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 1000 620]);
tl = tiledlayout(f, 2, 2, 'TileSpacing', 'compact');
for c = [c3, find(PoList == 300, 1)]
    R = Rk{c};
    q = TB.ncyc - 2;                                      % 끝에서 두 번째 주기의 반주기 경계
    t0 = q*T + T/2; mk = R.t >= t0 - 30e-9 & R.t <= t0 + 90e-9;
    nexttile; hold on; grid on;
    plot(1e9*(R.t(mk) - t0), R.vleg1(mk), 'LineWidth', 1.3);
    stairs(1e9*(R.t(mk) - t0), 400*R.gq1(mk), ':', 'LineWidth', 1.1);
    stairs(1e9*(R.t(mk) - t0), 400*R.gq2(mk), '--', 'LineWidth', 1.1);
    xline(1e9*TB.C.td, ':', 't_d'); ylabel('[V]'); ylim([-40 440]);
    legend('v_{leg1}', '400 \times Q1', '400 \times Q2', 'Location', 'east');
    title(sprintf('%.1f kW: Q1 off \\rightarrow Q2 on', PoList(c)/1e3));
    nexttile; hold on; grid on;
    plot(1e9*(R.t(mk) - t0), R.ir1(mk), 'LineWidth', 1.3); xline(1e9*TB.C.td, ':', 't_d');
    ylabel('i_{r1} [A]'); title(sprintf('%.1f kW: primary current during dead time', PoList(c)/1e3));
end
xlabel(tl, 'time from Q1 turn-off [ns]');
title(tl, 'TB05 ZVS transition of leg 1 (C_{oss} 100 pF per switch, dead time 50 ns)');
exportgraphics(f, fullfile(resDir, 'TB05_zvs_transition.png'), 'Resolution', 150); close(f);

% ---- 그림 3: 출력전압(전 구간) ----------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 900 420]); hold on; grid on;
for c = 1:nc
    plot(1e3*Rv{c}(:, 1), Rv{c}(:, 2), 'LineWidth', 1.1);
end
for c = 1:nc
    yline(ref.cases(c).Vo, ':');
end
xlabel('t [ms]'); ylabel('V_o [V]');
legend([arrayfun(@(p) sprintf('Simscape %.1f kW', p/1e3), PoList, 'UniformOutput', false), {'model final (E10)'}], 'Location', 'southeast');
title(sprintf('TB05 output voltage from 48 V initial state (resonant tank starts at zero), %d periods', TB.ncyc));
exportgraphics(f, fullfile(resDir, 'TB05_output_voltage.png'), 'Resolution', 150); close(f);

sl_export_png({mdl, [mdl '/StageC_CLLC'], [mdl '/StageC_CLLC/Rectifier'], [mdl '/Gate_StageC']}, resDir);
fprintf('results written to %s\n', resDir);
end

% ======================================================================================================
function R = simulate(mdl)
% 모델을 실행하고 판정에 쓰는 신호를 열 벡터로 정리한다.
tic; out = sim(mdl); R.wall = toc;
nm = {'t', 'vo', 'io', 'iin', 'ir1', 'im', 'ir2', 'vcr1', 'vleg1', 'gq1', 'gq2'};
for k = 1:numel(nm)
    R.(nm{k}) = double(out.(nm{k})(:));
    if k >= 2 && k <= 9, R.(nm{k})(1) = R.(nm{k})(2); end   % Simscape 첫 출력 표본(t = 0)은 초기화 중의 값
end
end

function Rt = keep_tail(R, t0)
% t ≥ t0 구간만 남긴 사본(그림용)
k = R.t >= t0;
fn = fieldnames(R);
for j = 1:numel(fn)
    if numel(R.(fn{j})) == numel(R.t), Rt.(fn{j}) = R.(fn{j})(k); else, Rt.(fn{j}) = R.(fn{j}); end
end
end

function m = metrics(R, TB)
% 마지막 TB.neval 주기의 지표(검증 모델 make_ref_TB05.py의 정의와 같게 계산)
T = TB.T; dt = TB.dt; Vin = TB.Vin; n = TB.C.n;
t0 = (TB.ncyc - TB.neval)*T;
mk = R.t > t0 + dt/2 & R.t <= TB.t_end + dt/2;
m.Vo = mean(R.vo(mk));
m.gain = m.Vo*n/Vin;
m.Ipri_rms = sqrt(mean(R.ir1(mk).^2));
m.Isec_rms = sqrt(mean(R.ir2(mk).^2));
m.Im_pk = max(abs(R.im(mk)));
m.Vo_ripple = max(R.vo(mk)) - min(R.vo(mk));
m.Pin = mean(Vin*R.iin(mk));
m.Pout = mean(R.vo(mk).*R.io(mk));
m.eff = m.Pout/m.Pin;
idx = @(tt) min(max(round(tt/dt) + 1, 1), numel(R.t));
q = (TB.ncyc - TB.neval):(TB.ncyc - 1);
% 스위칭(꺼짐) 순간 전류: 반주기 끝(Q1·Q4 꺼짐, Q2·Q3 꺼짐) 직전 표본
ioff = [idx(q*T + T/2 - dt), idx((q + 1)*T - dt)];
m.i_sw = mean(abs(R.ir1(ioff)));
% ZVS: 켜지기 직전 표본의 드레인-소스 전압. Q1(상측) V_ds = V_in − v_leg1, Q2(하측) V_ds = v_leg1
iQ1 = idx(q*T + TB.C.td - dt); iQ2 = idx(q*T + T/2 + TB.C.td - dt);
iQ1 = iQ1(iQ1 > 1);
m.vds_on_max = max([Vin - R.vleg1(iQ1); R.vleg1(iQ2)]);
% 레그 전이 시간: Q1 꺼짐 후 v_leg1이 90 % 내려갈 때까지
tr = zeros(size(q));
for j = 1:numel(q)
    k0 = idx(q(j)*T + T/2);
    k1 = find(R.vleg1(k0:k0 + round(TB.C.td/dt)) <= 0.1*Vin, 1);
    if isempty(k1), tr(j) = NaN; else, tr(j) = (k1 - 1)*dt; end
end
m.t_tr = mean(tr, 'omitnan');
end

function out2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end

function s = ternary(c, a, b)
if c, s = a; else, s = b; end
end
