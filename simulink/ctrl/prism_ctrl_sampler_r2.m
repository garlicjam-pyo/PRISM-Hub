function [u, dg] = prism_ctrl_sampler_r2(t, y, prm, init, tab, smp)
%#codegen
%PRISM_CTRL_SAMPLER_R2  채택 제어기 표본화 실행기의 R2 창 조정 모듈판(TB08, MATLAB Function 블록의 진입 함수).
%
%   ctrl/prism_ctrl_sampler.m과 같이 5 µs마다(반송파 최댓값 시점) 제어기를 한 번 계산하고 그 밖에는 직전 출력을 유지한다.
%   다른 점은 두 가지다.
%     (1) 버스 기준전압을 상수(prm(9)) 대신 입력 y(10)으로 받는다(모드 시퀀서의 기준 램프).
%     (2) y(11) = 1이면 제어기를 무충격 재초기화한다(영벡터·바이패스 중, prism_stageB_controller의 rst 입력).
%   제어 법칙 자체는 prism_stageB_controller.m 그대로다.
%
%   입력  y = [i_p v_s v_bus i_h v_link V_bat i_link_avg φ_c0 φ_c1 | V_ref 재초기화]
%         prm, init, tab, smp : ctrl/prism_ctrl_sampler.m과 같음
%   출력  u, dg : ctrl/prism_ctrl_sampler.m과 같음

persistent uh dgh
if isempty(uh)
    uh = [init(3); 0];
    dgh = zeros(6, 1);
end
k = round(t/smp(1));
if mod(k, round(smp(2))) == 0
    prm2 = prm;
    prm2(9) = y(10);                                   % 시변 버스 기준전압
    [uh, dgh] = prism_stageB_controller(y(1:9), prm2, init, tab, y(11));
end
u = uh;
dg = dgh;
end
