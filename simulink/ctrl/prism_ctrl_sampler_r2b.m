function [u, dg] = prism_ctrl_sampler_r2b(t, y, prm, init, tab, smp)
%#codegen
%PRISM_CTRL_SAMPLER_R2B  채택 제어기 표본화 실행기의 R2 보호 상태기계판(TB09, MATLAB Function 블록의 진입 함수).
%
%   ctrl/prism_ctrl_sampler_r2.m과 같이 5 µs마다 제어기를 한 번 계산하고, 상태기계(ctrl/prism_r2_supervisor.m)의
%   지령을 함께 받는다.
%     y(10) V_ref, y(11) 재초기화, y(12) 브리지 모드(3이면 상태기계의 조향 변조율을 PWM 비교값으로),
%     y(13) 조향 변조율, y(14) DAB 모드(1이면 보조 링크전류 지령), y(15) 보조 링크전류 지령
%   제어 법칙은 prism_stageB_controller.m 그대로다(보조 지령은 링크전압 PI 대신 들어간다).
%
%   입력  y = [i_p v_s v_bus i_h v_link V_bat i_link_avg φ_c0 φ_c1 | 상태기계 지령 6개]
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
    [uh, dgh] = prism_stageB_controller(y(1:9), prm2, init, tab, y(11), [double(y(14) == 1); y(15)]);
    if round(y(12)) == 3
        uh(1) = y(13);                                 % 전류 조향: 상태기계가 정한 변조율
    end
end
u = uh;
dg = dgh;
end
