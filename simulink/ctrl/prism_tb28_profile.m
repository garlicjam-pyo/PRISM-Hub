function y = prism_tb28_profile(t, prm)
%#codegen
%PRISM_TB28_PROFILE  TB28 시험 조건: TB20의 시험 조건(충전기 전류, 400 V 부하, 48 V 부하, Stage A 위상 동작 여부) + 충전 요청.
%
%   y = prism_tb28_profile(t, prm),   y = [i_ch; Q_400; P_48; en(1:8); chg]  (12×1)
%   prm = [t_I(6) I(6) t_ev mask(8) Q P t_chg_on t_chg_off]  (25개)
%     앞 23개는 prism_tb20_profile과 같다(충전기 전류 구간 선형 6점, 사건 시각, 사건 뒤 위상 동작 여부, 부하 전력).
%     충전 요청 chg = 1(t_chg_on ≤ t < t_chg_off): 차량 충전 제어기가 충전기 전류를 올리기 전에 Stage A 모듈을 모두 켜라고
%     보내는 신호(E28, A25R 요구: 사전 기동 ≥ 600 µs).

y = [prism_tb20_profile(t, prm(1:23)); double(t >= prm(24) && t < prm(25))];
end
