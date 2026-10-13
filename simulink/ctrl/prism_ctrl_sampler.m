function [u, dg] = prism_ctrl_sampler(t, y, prm, init, tab, smp)
%#codegen
%PRISM_CTRL_SAMPLER  채택 제어기의 표본화 실행기(MATLAB Function 블록의 진입 함수).
%
%   모델 전체를 적분 간격 dt 하나로 돌리고(다중 속도 없음), 이 함수가 반송파 최댓값 시점
%   (k = round(t/dt)가 Np의 배수, 5 µs마다)에만 제어기를 한 번 계산한다. 그 밖의 간격에서는 직전 출력을 유지한다.
%   계산 결과는 모델의 Delay 블록(Np 간격 = 5 µs)을 거쳐 게이트 생성기에 들어가므로, 검증 모델과 같이
%   표본 → 계산 → 5 µs 뒤 적용 순서가 된다.
%
%   입력  t     시각 [s] (Digital Clock)
%         y     [i_p v_s v_bus i_h v_link V_bat i_link_avg φ_c0 φ_c1]  (prism_stageB_controller 설명 참고)
%         prm, init, tab  제어기 상수(prism_hub_params: P.ctrl_prm, 초기상태, 데드타임 교정표)
%         smp   [dt Np]
%   출력  u     [PWM 비교값; DAB 유효 위상]   dg  [m 지령; 링크전류 지령; 브리지 전류지령; ρ̂; ε̂; 예측 링크전류]

persistent uh dgh
if isempty(uh)
    uh = [init(3); 0];
    dgh = zeros(6, 1);
end
k = round(t/smp(1));
if mod(k, round(smp(2))) == 0
    [uh, dgh] = prism_stageB_controller(y, prm, init, tab);
end
u = uh;
dg = dgh;
end
