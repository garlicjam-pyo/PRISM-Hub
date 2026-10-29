function smoke_TB31()
%SMOKE_TB31  TB31 빠른 점검: 사례 A31을 1.5 ms(고장 0.5 ms 뒤 1 ms)까지만 계산해 모델이 돌고, 상태기계가 H-브리지 고장 유지(9)로
%            가며, 부하 블록이 SALS 감발 비트를 받는지 확인한다(판정 아님). 결과: results/smoke/TB31_smoke.txt
here = fileparts(mfilename('fullpath'));
mdl = 'TB31_R2_ScPause_LoadStop';
out_dir = fullfile(here, 'results', 'smoke');
if ~exist(out_dir, 'dir'), mkdir(out_dir); end
assignin('base', 'TB31_case', 'A31_930V_MX_S5_pause');
evalin('base', 'clear TB31_opts');
run(fullfile(here, 'TB31_init.m'));
load_system(fullfile(here, [mdl '.slx']));
tic; out = sim(mdl, 'StopTime', '1.5e-3'); wall = toc;
sup = out.sup; if ndims(sup) == 3, sup = reshape(sup, size(sup, 1)*size(sup, 2), [])'; end
if size(sup, 2) ~= 12, sup = sup'; end
pl = out.pload(:); vA = out.vA(:);
fid = fopen(fullfile(out_dir, 'TB31_smoke.txt'), 'w');
msg = sprintf(['TB31 smoke (case A to 1.5 ms): wall %.0f s, final state %d, code %d, p_load first/last %.0f/%.0f W, ' ...
    'v_A last %.2f V, max |i_p| %.1f A\n'], wall, round(sup(end, 11)), round(sup(end, 10)), pl(1), pl(end), vA(end), max(abs(out.ip(:))));
fprintf('%s', msg); fprintf(fid, '%s', msg); fclose(fid);
evalin('base', 'clear TB31_case');
end
