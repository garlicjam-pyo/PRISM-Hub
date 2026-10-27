function y = prism_tb22_profile(t, prm)
%#codegen
%PRISM_TB22_PROFILE  TB22 시험 조건(시험 장치): 400 V 버스 정전력 부하 전력, V_A 노드 직접 전류(충전기), 충전 요청 신호.
%
%   prm = [t_P(1:6) P(1:6) t_I(1:6) I(1:6) t_chg_on t_chg_off]  (구간 선형 6점, prism_tb18_profile과 같은 규칙)
%   출력 y = [P [W]; I_VA [A]; chg]  (I_VA < 0이면 충전기 주입, chg = 1이면 충전 요청: t_chg_on ≤ t < t_chg_off)
%   충전 요청은 차량 충전 제어기가 충전기 전류를 올리기 전에 Stage A 모듈을 모두 켜라고 보내는 신호다(E28).

y = [prism_tb18_profile(t, prm(1:24)); double(t >= prm(25) && t < prm(26))];
end
