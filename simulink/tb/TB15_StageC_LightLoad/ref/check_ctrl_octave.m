function check_ctrl_octave(caseName)
%CHECK_CTRL_OCTAVE  (TB15: 경부하 두 브리지 구동 포함) 회로 제어기(ctrl/prism_stageC_reg_ctrl.m)를 검증 코드 E22와 같은 평균 플랜트에 붙여 E22 결과와 대조한다.
%   MATLAB·Octave 공용. 제어기 코드를 Python(E22)에서 MATLAB으로 옮길 때 생길 수 있는 차이를 회로 실행 전에 찾는다.
%   플랜트(E22 _avg와 같은 식, 전진 오일러 0.05 µs): L di_L/dt = d·v_bus − v_I − R_L i_L, C_I dv_I/dt = i_L − i_x/n,
%   L_x di_x/dt = v_I/n − v_o − R_x i_x(받는 쪽 동기정류: 보내는 방향 반대 전류 0), C_o dv_o/dt = i_x − P/v_o − i_bat
%   실행: cd ref; check_ctrl_octave('F_400V_rev_light')   → v_o·i_L의 E22 대비 최대 차를 출력

if nargin < 1, caseName = 'F_400V_rev_light'; end
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, '..', '..', '..', 'ctrl'));
R0 = jsondecode(fileread(fullfile(here, ['TB15_' caseName '_init.json'])));
A = csvread(fullfile(here, ['TB15_' caseName '_avg.csv']), 1, 0);   % t vbus iL vI ix vo d mode ibat iin pload iref
clear prism_stageC_reg_ctrl
n = R0.n; L = R0.L; RL = R0.RL; CI = R0.CI; Co = R0.CO; Lx = R0.equiv.Lx; Rx = R0.equiv.Rx;
dt = 0.05e-6;                                         % 0.05 µs(E22와 같음)
pad = @(v) [v(:)' repmat(v(end), 1, 4 - numel(v))];
prof = [pad(R0.tV) pad(R0.VV) pad(R0.tP) pad(R0.PP)];
x = R0.x0(:)'; iL = x(1); vI = x(2); vo = x(3); ix = x(4);
mode0 = 1; if iL < 0, mode0 = -1; end
if abs(prof(13)) < R0.P_in, mode0 = 2; end           % 시작 전력(PP(1))이 문턱 아래면 두 브리지 구동(TB15_init과 같음)
prm = [R0.ctl(:)' R0.Vref dt R0.bat_on 0 R0.d0 mode0 iL n R0.P_in R0.P_out];
N = round(R0.t_end/dt); dec = 20;
out = zeros(floor(N/dec) + 1, 4); j = 0;
u = [R0.d0; mode0; iL; 0];
for k = 0:N-1
    t = k*dt;
    y = prism_tb14_profile(t, prof); vb = y(1); pl = y(2);
    ib = 0; if R0.bat_on > 0.5, ib = (vo - R0.OCV)/R0.Rbat; end
    u = prism_stageC_reg_ctrl(t, [vb; iL; vI; vo; pl/vo; ib], prm);
    d = u(1); mode = u(2);
    diL = (d*vb - vI - RL*iL)/L; dvI = (iL - ix/n)/CI; dix = (vI/n - vo - Rx*ix)/Lx; dvo = (ix - pl/vo - ib)/Co;
    iL = iL + diL*dt; vI = vI + dvI*dt; ix = ix + dix*dt; vo = vo + dvo*dt;
    if mode == 1 && ix < 0, ix = 0; elseif mode == -1 && ix > 0, ix = 0; end   % 모드 2(두 브리지)는 양방향
    if mod(k, dec) == 0
        j = j + 1; out(j, :) = [t vo iL ix];
    end
end
out = out(1:j, :);
m = min(j, size(A, 1));
fprintf('%s: max|Δv_o| %.4f V, max|Δi_L| %.4f A, max|Δi_x| %.3f A (E22 대비, %d점)\n', caseName, ...
    max(abs(out(1:m, 2) - A(1:m, 6))), max(abs(out(1:m, 3) - A(1:m, 3))), max(abs(out(1:m, 4) - A(1:m, 5))), m);
end
