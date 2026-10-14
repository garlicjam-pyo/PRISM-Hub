function sl_solver(sys, name, pos, gndBlock, gndPort, nIter)
%SL_SOLVER  Simscape Solver Configuration 블록을 넣고 지역 해석기를 설정한다.
%
%   sl_solver(sys, 'Solver', [x1 y1 x2 y2], 'GND', 'V')
%
%   지역 해석기: 후진 오일러(Backward Euler), 간격 TB.dt(기본 5 ns).
%   스위치·다이오드는 구간 선형 소자이므로 후진 오일러가 모드 전환에서도 안정하다.
%   데드타임(50–100 ns)이 정수 간격이 되도록 TB.dt를 정한다.
%
%   nIter(선택): 고정 비용 실행. 간격마다 비선형(모드) 반복을 nIter번으로 고정한다.
%     스위치가 많은 회로(TB04: 셀 12개)에서 가변 비용은 간격당 약 1.9 ms로 느려지지만
%     고정 비용(2–3회)은 같은 결과(50 µs 비교에서 버스전압이 소수 셋째 자리까지 같음)를 25배 이상 빨리 낸다(TB04 results/TB04_speed_probe.txt).

add_block('nesl_utility/Solver Configuration', [sys '/' name], 'Position', pos, ...
    'UseLocalSolver', 'on', ...
    'LocalSolverChoice', 'NE_BACKWARD_EULER_ADVANCER', ...
    'LocalSolverSampleTime', 'TB.dt', ...
    'DoFixedCost', 'off', ...
    'ResidualTolerance', '1e-9');
if nargin >= 6 && ~isempty(nIter)
    set_param([sys '/' name], 'DoFixedCost', 'on', 'MaxNonlinIter', num2str(nIter));
end
simscape.addConnection([sys '/' name], 'port', [sys '/' gndBlock], gndPort);
end
