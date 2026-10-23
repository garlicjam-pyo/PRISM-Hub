function run_TB08_zoom()
%RUN_TB08_ZOOM  TB08 바이패스 전환 순간의 순시 파형을 확대해 정량화한다(run_TB08의 보조 분석, 정보).
%
%   run_TB08에서 바이패스 투입 직후 바이패스 전류가 경로전류보다 크게 튀었고(직렬 커패시터 C_s 방전),
%   켬 사례 E에서는 바이패스 열림 직후 경로전류가 출렁였다(제어 시작 전, 영벡터 상태).
%   이 함수는 같은 모델·같은 사례를 전환 직후까지만 다시 계산해 순시 파형을 저장하고 다음을 계산한다.
%     닫힘(C, D): 투입 직전 v_s, 바이패스 전류 최대(부호 포함)와 시각, 투입 뒤 정착값(+20–40 µs 평균),
%                 정착값에서 20 A 넘게 벗어난 시간, 초과 전하 ∫(i_byp − 정착값)dt, 투입 직전 C_s 에너지 ½·C_s·v_s²,
%                 소자 1개 전류(2병렬 가정, ibyp/2)와 EPC2305 펄스 정격(329 A, 25 °C, 300 µs) 비
%     열림(E): 0.5 ms 바이패스 열림 뒤 제어 시작(0.7 ms)까지의 순시 경로·필터전류 최대, v_s 범위, 버스 최대,
%              경로전류 출렁임 주파수(평균을 뺀 신호의 영점 교차 간격)
%   결과: results/TB08_zoom_<사례>.csv(10 ns 간격), TB08_zoom.png, TB08_zoom_summary.txt·json
%   실행: prism_run('run_TB08_zoom')   (모델은 build_TB08로 만든 TB08_R2_WindowModule.slx)

here = fileparts(mfilename('fullpath'));
mdl  = 'TB08_R2_WindowModule';
resDir = fullfile(here, 'results');
load_system(fullfile(here, [mdl '.slx']));
cases = {'C_910V_disable_25kW', 'D_1008V_dabfault_25kW', 'E_930V_enable_25kW'};
Z = struct(); W = struct();
for k = 1:numel(cases)
    cn = cases{k}; c = cn(1);
    assignin('base', 'TB08_case', cn);
    assignin('base', 'TB08_opts', struct('dt', 2.5e-9));
    run(fullfile(here, 'TB08_init.m'));
    TB = evalin('base', 'TB');
    sq = TB.seq_prm;
    if c == 'E', tEv = sq(8); tStop = sq(9) + 0.1e-3; else, tEv = sq(7); tStop = tEv + 40e-6; end
    tic; out = sim(mdl, 'StopTime', num2str(tStop, '%.9g')); wall = toc;
    t = out.t(:); ib = out.ibyp(:); ip = out.ip(:); ih = out.ih(:); vs = out.vs(:); vb = out.vbus(:);
    if c == 'E', w = t >= tEv - 20e-6 & t <= sq(9); else, w = t >= tEv - 5e-6 & t <= tStop; end
    w(w) = mod(0:nnz(w)-1, 4)' == 0;                                         % 10 ns 간격으로 저장
    writematrix([t(w) - tEv, ib(w), ip(w), ih(w), vs(w), vb(w)], fullfile(resDir, ['TB08_zoom_' cn '.csv']));
    W.(c) = struct('t', t(w) - tEv, 'ib', ib(w), 'ip', ip(w), 'ih', ih(w), 'vs', vs(w), 'vb', vb(w));
    m = struct('case', cn, 'wall_s', wall, 't_event_ms', 1e3*tEv);
    if c ~= 'E'
        kb = find(t < tEv, 1, 'last');
        a = t >= tEv & t <= tEv + 20e-6;
        fin = mean(ib(t >= tEv + 20e-6 & t <= tEv + 40e-6));
        [~, j] = max(abs(ib(a))); ia = ib(a); ta = t(a);
        ex = abs(ib - fin) > 20 & t >= tEv;
        m.vs_before_V = vs(kb);
        m.ip_before_A = ip(kb);
        m.ih_before_A = ih(kb);
        m.ibyp_peak_A = ia(j);
        m.t_peak_us = 1e6*(ta(j) - tEv);
        m.ibyp_settled_A = fin;
        m.excess_over_20A_us = 1e6*sum(ex)*TB.dt;
        m.excess_charge_uC = 1e6*trapz(t(a), ib(a) - fin);
        m.Cs_discharge_charge_uC = 1e6*trapz(t(a), ib(a) - (ip(a) - ih(a)));   % C_s 방전분(i_byp − (i_p − i_h))
        m.Cs_dv_charge_uC = 1e6*TB.B.Cs*(vs(find(t <= tEv + 20e-6, 1, 'last')) - vs(kb));   % 같은 부호(v_s = v_BUS − v_SER)
        m.Cs_energy_uJ = 1e6*0.5*TB.B.Cs*vs(kb)^2;
        m.per_device_peak_A = abs(ia(j))/2;                                    % 2병렬 역직렬(E15 R_BYP 가정)
        m.per_device_vs_pulse_rating = m.per_device_peak_A/329;               % EPC2305 I_D,pulse 329 A(25 °C, 300 µs)
    else
        a = t >= tEv & t < sq(9);
        m.ip_max_A = max(ip(a)); m.ip_min_A = min(ip(a));
        m.ih_max_A = max(ih(a)); m.ih_min_A = min(ih(a));
        m.vs_range_V = [min(vs(a)) max(vs(a))];
        m.vbus_max_V = max(vb(a));
        x = ip(a) - mean(ip(a)); ta = t(a);
        zc = ta(find(x(1:end-1) .* x(2:end) < 0) + 1);
        zc = zc([true; diff(zc) > 5e-6]);                                     % 스위칭 리플에 의한 잦은 교차 제거
        if numel(zc) >= 3, m.ring_freq_kHz = 1e-3/(2*mean(diff(zc))); else, m.ring_freq_kHz = NaN; end
    end
    Z.(c) = m;
    fprintf('%s done (%.0f s)\n', cn, wall);
end
evalin('base', 'clear TB08_case TB08_opts');

% ---- 요약 --------------------------------------------------------------------------------------------
fid = fopen(fullfile(resDir, 'TB08_zoom_summary.txt'), 'w');
o2(fid, 'TB08 bypass transitions, instantaneous (Simscape, dt 2.5 ns, ideal bypass loop: no stray inductance, C_s ESR 1 uOhm, bypass 3.3 mOhm)\n');
for c = 'CD'
    m = Z.(c);
    o2(fid, '%s bypass closing at %.2f ms: v_s before %.3f V (i_p %.1f A, i_h %.1f A), i_byp peak %.1f A at +%.2f us, settled %.1f A,\n', ...
        m.case, m.t_event_ms, m.vs_before_V, m.ip_before_A, m.ih_before_A, m.ibyp_peak_A, m.t_peak_us, m.ibyp_settled_A);
    o2(fid, '    |i_byp - settled| > 20 A for %.2f us, C_s discharge %.1f uC (C_s*dv %.1f uC), C_s energy %.1f uJ, per device %.0f A = %.2f x EPC2305 pulse rating (329 A)\n', ...
        m.excess_over_20A_us, m.Cs_discharge_charge_uC, m.Cs_dv_charge_uC, m.Cs_energy_uJ, m.per_device_peak_A, m.per_device_vs_pulse_rating);
end
m = Z.E;
o2(fid, '%s bypass opening at %.2f ms (zero vector until control at 0.70 ms): i_p %.1f-%.1f A, i_h %.1f-%.1f A, v_s %.2f..%.2f V, v_bus max %.2f V, ringing %.1f kHz\n', ...
    m.case, m.t_event_ms, m.ip_min_A, m.ip_max_A, m.ih_min_A, m.ih_max_A, m.vs_range_V(1), m.vs_range_V(2), m.vbus_max_V, m.ring_freq_kHz);
fclose(fid);
fid = fopen(fullfile(resDir, 'TB08_zoom_summary.json'), 'w'); fprintf(fid, '%s', jsonencode(Z, 'PrettyPrint', true)); fclose(fid);

% ---- 그림 ----------------------------------------------------------------------------------------------
f = figure('Visible', 'off', 'Position', [100 100 1100 900]);
tl = tiledlayout(f, 3, 2, 'TileSpacing', 'compact');
for c = 'CD'
    w = W.(c);
    nexttile; hold on; grid on;
    plot(1e6*w.t, w.ib, 'LineWidth', 1.3); plot(1e6*w.t, w.ip, 'LineWidth', 1.1); plot(1e6*w.t, w.ih, 'LineWidth', 1.1);
    xline(0, ':'); ylabel('[A]'); xlabel('t - t_{bypass} [\mus]');
    legend('i_{byp}', 'i_p', 'i_h', 'Location', 'best');
    title(sprintf('%s: bypass closing (peak %.0f A, %.0f A per device)', strrep(Z.(c).case, '_', ' '), Z.(c).ibyp_peak_A, Z.(c).per_device_peak_A));
    nexttile; hold on; grid on;
    plot(1e6*w.t, w.vs, 'LineWidth', 1.3); xline(0, ':'); ylabel('v_s [V]'); xlabel('t - t_{bypass} [\mus]');
    title(sprintf('series-port voltage (%.2f V before closing)', Z.(c).vs_before_V));
end
w = W.E;
nexttile; hold on; grid on;
plot(1e3*(w.t + Z.E.t_event_ms*1e-3), w.ip, 'LineWidth', 1.2); plot(1e3*(w.t + Z.E.t_event_ms*1e-3), w.ih, 'LineWidth', 1.0);
plot(1e3*(w.t + Z.E.t_event_ms*1e-3), w.ib, 'LineWidth', 1.0);
ylabel('[A]'); xlabel('t [ms]'); legend('i_p', 'i_h', 'i_{byp}', 'Location', 'best');
title(sprintf('E: bypass opens at 0.5 ms, control starts at 0.7 ms (ringing %.1f kHz)', Z.E.ring_freq_kHz));
nexttile; hold on; grid on;
yyaxis left; plot(1e3*(w.t + Z.E.t_event_ms*1e-3), w.vs, 'LineWidth', 1.2); ylabel('v_s [V]');
yyaxis right; plot(1e3*(w.t + Z.E.t_event_ms*1e-3), w.vb, 'LineWidth', 1.0); ylabel('v_{bus} [V]');
xlabel('t [ms]'); title('E: series-port and bus voltage (instantaneous)');
title(tl, 'TB08 bypass transitions (instantaneous, ideal bypass loop)');
exportgraphics(f, fullfile(resDir, 'TB08_zoom.png'), 'Resolution', 140); close(f);
end

function o2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end
