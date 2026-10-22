function probe_TB06()
%PROBE_TB06  TB06 짧은 점검 실행(사례 A, 0.5 ms): 기동 거동과 실행 시간을 본다(판정 아님).
%   결과: results/TB06_probe.txt
here = fileparts(mfilename('fullpath'));
mdl  = 'TB06_Integrated_Drive';
resDir = fullfile(here, 'results'); if ~exist(resDir, 'dir'), mkdir(resDir); end
assignin('base', 'TB06_case', 'A_640V_15to25kW');
evalin('base', 'clear TB06_opts');
run(fullfile(here, 'TB06_init.m'));
load_system(fullfile(here, [mdl '.slx']));
tic; out = sim(mdl, 'StopTime', '0.5e-3'); wall = toc;
t = out.t(:); n = numel(t);
f = @(x) x(:);
vb = f(out.vbus); vA = f(out.vA); ip = f(out.ip); i1 = f(out.iA1); i2 = f(out.iA2); s1 = f(out.st1); s2 = f(out.st2);
vo = f(out.vo48); ic = f(out.icin); vl = f(out.vlink);
fid = fopen(fullfile(resDir, 'TB06_probe.txt'), 'w');
o2(fid, 'TB06 probe: case A, 0.5 ms, dt %.2f ns, wall %.1f s (%.0f s per ms), %d samples\n', 1e9*TB.dt, wall, wall/0.5, n);
for tt = [5e-6 20e-6 50e-6 100e-6 200e-6 300e-6 400e-6 500e-6]
    k = min(n, max(2, round(tt/TB.dt)));
    w = max(2, k - 1000):k;                          % 직전 5 µs 평균
    o2(fid, 't=%6.1f us: v_bus %.2f V, V_A %.2f V, i_p %.2f A, v_link %.2f V, v_48 %.3f V, Stage C in %.0f W, iC pk %.1f/%.1f A, segments %d/%d\n', ...
        1e6*tt, mean(vb(w)), mean(vA(w)), mean(ip(w)), mean(vl(w)), mean(vo(w)), mean(vb(w).*ic(w)), max(abs(i1(w))), max(abs(i2(w))), ...
        nnz(diff(s1(w)) ~= 0), nnz(diff(s2(w)) ~= 0));
end
m = t > 0.3e-3;
o2(fid, 'last 0.2 ms: v_bus %.2f-%.2f V, V_A mean %.3f V, i_p mean %.2f A, v_48 mean %.3f V, Stage C input %.0f W, phase segments %d/%d\n', ...
    min(vb(m)), max(vb(m)), mean(vA(m)), mean(ip(m)), mean(vo(m)), mean(vb(m).*ic(m)), nnz(diff(s1(m)) ~= 0), nnz(diff(s2(m)) ~= 0));
fclose(fid);
evalin('base', 'clear TB06_case');
end

function o2(fid, varargin)
fprintf(varargin{:}); fprintf(fid, varargin{:});
end
