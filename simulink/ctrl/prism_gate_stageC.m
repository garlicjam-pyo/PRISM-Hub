function g = prism_gate_stageC(t, prm)
%#codegen
%PRISM_GATE_STAGEC  Stage C(대칭 CLLC) 1차 풀브리지 게이트: 공진점 고정 주파수, 50 % 상보 구형파 + 데드타임.
%
%   전반주기 [t_d, T/2)      : Q1(레그 1 상측)·Q4(레그 2 하측) 도통 → 1차 브리지 출력 +V_in
%   후반주기 [T/2 + t_d, T)  : Q2(레그 1 하측)·Q3(레그 2 상측) 도통 → −V_in
%   데드타임 동안 공진전류가 레그 노드의 출력용량을 충방전해 다음 소자가 영전압에서 켜진다(ZVS).
%   Stage C는 400 V 버스를 고정이득(권선비 25/3)으로 48 V로 바꾸므로 폐루프 제어 없이 이 타이밍만 쓴다.
%
%   입력  t    시각 [s] (Digital Clock, 간격 dt)
%         prm  [dt T t_d enable]  (T = 1/250 kHz, t_d = 50 ns)
%   출력  g    [Q1 Q2 Q3 Q4] (1 = 켬)

dt = prm(1); T = prm(2); td = prm(3);
g = zeros(4, 1);
if prm(4) > 0.5
    t0 = round(t/dt)*dt;                     % 적분 간격 격자 시각
    tau = mod(t0 + 1e-3*dt, T);              % 주기 안 위치(작은 치우침으로 경계 반올림 오차 흡수)
    on1 = (tau >= td) && (tau < T/2);
    on2 = (tau >= T/2 + td) && (tau < T);
    g = double([on1; on2; on2; on1]);
end
end
