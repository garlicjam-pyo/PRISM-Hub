function sl_pc(sys, a, pa, b, pb)
%SL_PC  두 Simscape 물리 포트를 포트 이름으로 잇는다(simscape.addConnection, R2025a 이상).
%
%   sl_pc(sys, 'Lr', 'n', 'Cfly', 'p')       % sys/Lr 의 n 포트 ↔ sys/Cfly 의 p 포트
%   sl_pc(sys, 'VIN', 'port', 'S1', 'D')     % Connection Port 블록(VIN)은 'port',
%                                              서브시스템(S1)의 포트는 그 안의 Connection Port 이름(D)
%
%   포트 이름(설치 R2025a에서 조사, logs/probe_ports.log):
%     R, L, C, Diode, DC 전압원 : p(+), n(−)      Switch : p, n, vT(제어)
%     전류·전압 센서 : p, n, I 또는 V(출력)        제어 전류원 : head, tail, iT
%     이상 변압기    : p1, n1, p2, n2              Simulink-PS : output, PS-Simulink : input

simscape.addConnection([sys '/' a], pa, [sys '/' b], pb, 'autorouting', 'smart');
end
