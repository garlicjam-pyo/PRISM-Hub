function probe_TB14_solver()
%PROBE_TB14_SOLVER  해석기 점검: 사례 A를 가변 비용(모드 반복 제한 없음, TB05와 같음)으로 다시 계산해 고정 비용(3회, run_TB14) 결과와 비교한다.
%
%   TB14는 시간을 줄이려고 TB08–TB13처럼 고정 비용(모드 반복 3회)으로 판정한다. 가변 비용 실행은 사례 A(4.5 ms)에 약 24분 걸린다.
%   먼저 run_TB14를 실행해 results/TB14_A_400V_ramp_avg10us.csv가 있어야 한다.
%   비교: 10 µs 평균 v_o·i_L·v_I·i_x의 최대 차, 사건 전 정상상태 평균의 차. 결과: results/solver_probe/TB14_solver_probe.txt

here = fileparts(mfilename('fullpath'));
mdl  = 'TB14_StageC_Regulated';
pd = fullfile(here, 'results', 'solver_probe');
if ~exist(pd, 'dir'), mkdir(pd); end
F = readmatrix(fullfile(here, 'results', 'TB14_A_400V_ramp_avg10us.csv'));   % [t vb iin iL vI vo ix ib il]
load_system(fullfile(here, [mdl '.slx']));
assignin('base', 'TB14_case', 'A_400V_ramp');
run(fullfile(here, 'TB14_init.m'));
TB = evalin('base', 'TB');
old = get_param([mdl '/Solver'], 'DoFixedCost');
set_param([mdl '/Solver'], 'DoFixedCost', 'off');
tic; out = sim(mdl, 'StopTime', num2str(TB.t_end, '%.9g')); wall = toc;
set_param([mdl '/Solver'], 'DoFixedCost', old);
evalin('base', 'clear TB14_case');
t = out.t(:); X = [out.vbus(:) out.iin(:) out.iL(:) out.vI(:) out.vo(:) out.ix(:) out.ibat(:) out.iload(:)]; X(1, :) = X(2, :);
np = round(10e-6/(t(2) - t(1))); nper = floor(numel(t)/np);
V = zeros(nper, 9);
for q = 1:nper
    k = (q-1)*np + (1:np);
    V(q, :) = [t(k(end)) mean(X(k, :), 1)];
end
writematrix(V, fullfile(pd, 'TB14_A_400V_ramp_avg10us_variable_cost.csv'));
m = min(size(V, 1), size(F, 1));
nm = {'v_o', 'i_L', 'v_I', 'i_x'}; col = [6 4 5 7];
qs = V(1:m, 1) > TB.t_event - 0.5e-3 & V(1:m, 1) < TB.t_event;
fid = fopen(fullfile(pd, 'TB14_solver_probe.txt'), 'w');
pf = @(varargin) [fprintf(fid, varargin{:}), fprintf(varargin{:})];
pf('TB14 solver probe, case A_400V_ramp: variable cost (wall %.0f s) vs fixed cost 3 iterations (run_TB14)\n', wall);
for j = 1:4
    c = col(j);
    pf('  %-4s max |diff| %.4f, steady mean variable %.4f / fixed %.4f\n', nm{j}, max(abs(V(1:m, c) - F(1:m, c))), ...
        mean(V(qs, c)), mean(F(qs, c)));
end
pf('  v_o min/max variable %.3f/%.3f, fixed %.3f/%.3f\n', min(V(V(:, 1) > TB.t_event - 0.2e-3, 6)), max(V(V(:, 1) > TB.t_event - 0.2e-3, 6)), ...
    min(F(F(:, 1) > TB.t_event - 0.2e-3, 6)), max(F(F(:, 1) > TB.t_event - 0.2e-3, 6)));
fclose(fid);
end
