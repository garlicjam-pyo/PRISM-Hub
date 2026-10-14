function probe_TB05_solver()
%PROBE_TB05_SOLVER  TB05 수치 점검(진단용): 지역 해석기 종류와 적분 간격에 따른 공진 변환기 결과 차이.
%
%   후진 오일러는 무조건 안정하지만 수치 감쇠가 있어, 250 kHz 공진망(간격 5 ns → 주기당 800 간격)에서
%   공진 에너지가 조금씩 사라진다(등가 직렬 손실). 이 손실이 출력전압·전력에 주는 영향을
%   적분 간격(5, 2.5, 1.25 ns)과 사다리꼴 공식(수치 감쇠 없음)으로 비교한다. 3 kW, 400주기(1.6 ms, 마지막 10주기 평가: 해석기 간 상대 비교).
%   결과: results/TB05_solver_probe.txt

here = fileparts(mfilename('fullpath'));
mdl  = 'TB05_StageC_CLLC';
resDir = fullfile(here, 'results');
if ~exist(resDir, 'dir'), mkdir(resDir); end
load_system(fullfile(here, [mdl '.slx']));
slv = [mdl '/Solver'];
orig = get_param(slv, 'LocalSolverChoice');
cfg = {'NE_BACKWARD_EULER_ADVANCER', 5e-9; 'NE_BACKWARD_EULER_ADVANCER', 2.5e-9; 'NE_BACKWARD_EULER_ADVANCER', 1.25e-9; ...
       'NE_TRAPEZOIDAL_ADVANCER', 5e-9; 'NE_TRAPEZOIDAL_ADVANCER', 2.5e-9};
fid = fopen(fullfile(resDir, 'TB05_solver_probe.txt'), 'w');
for icfg = 1:size(cfg, 1)          % (초기화 스크립트가 k를 쓰므로 다른 이름)
    assignin('base', 'TB05_Po', 3000);
    assignin('base', 'TB_override', struct('dt', cfg{icfg, 2}, 'ncyc', 400, 'neval', 10));
    run(fullfile(here, 'TB05_init.m'));
    TB = evalin('base', 'TB');
    set_param(slv, 'LocalSolverChoice', cfg{icfg, 1});
    try
        tic; out = sim(mdl); w = toc;
        t = out.t(:); mk = t > (TB.ncyc - TB.neval)*TB.T + TB.dt/2;
        vo = out.vo(:); ir1 = out.ir1(:); ir2 = out.ir2(:); im = out.im(:); iin = out.iin(:); io = out.io(:);
        s = sprintf('%-28s dt %5.2f ns: Vo %.3f V, Ipri %.3f A, Isec %.2f A, Im_pk %.3f A, Pin %.1f W, Pout %.1f W, ripple %.3f V (%.1f s)\n', ...
            cfg{icfg, 1}, 1e9*cfg{icfg, 2}, mean(vo(mk)), sqrt(mean(ir1(mk).^2)), sqrt(mean(ir2(mk).^2)), max(abs(im(mk))), ...
            mean(TB.Vin*iin(mk)), mean(vo(mk).*io(mk)), max(vo(mk)) - min(vo(mk)), w);
    catch err
        s = sprintf('%-28s dt %5.2f ns: ERROR %s\n', cfg{icfg, 1}, 1e9*cfg{icfg, 2}, err.message);
    end
    fprintf('%s', s); fprintf(fid, '%s', s);
end
fclose(fid);
set_param(slv, 'LocalSolverChoice', orig);
close_system(mdl, 0);
evalin('base', 'clear TB_override TB05_Po');
end
