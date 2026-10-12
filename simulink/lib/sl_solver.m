function sl_solver(sys, name, pos, gndBlock, gndPort)
%SL_SOLVER  Simscape Solver Configuration 블록을 넣고 지역 해석기를 설정한다.
%
%   sl_solver(sys, 'Solver', [x1 y1 x2 y2], 'GND', 'V')
%
%   지역 해석기: 후진 오일러(Backward Euler), 간격 TB.dt(기본 5 ns).
%   스위치·다이오드는 구간 선형 소자이므로 후진 오일러가 모드 전환에서도 안정하다.
%   데드타임(50–100 ns)이 정수 간격이 되도록 TB.dt를 정한다.

add_block('nesl_utility/Solver Configuration', [sys '/' name], 'Position', pos, ...
    'UseLocalSolver', 'on', ...
    'LocalSolverChoice', 'NE_BACKWARD_EULER_ADVANCER', ...
    'LocalSolverSampleTime', 'TB.dt', ...
    'DoFixedCost', 'off', ...
    'ResidualTolerance', '1e-9');
simscape.addConnection([sys '/' name], 'port', [sys '/' gndBlock], gndPort);
end
