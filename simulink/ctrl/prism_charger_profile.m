function ich = prism_charger_profile(t, prm)
%#codegen
%PRISM_CHARGER_PROFILE  400 V급 충전기 출력전류 지령(충전기는 스스로 전류를 제어하는 전류원으로 둔다).
%
%   ich = prism_charger_profile(t, prm),   prm = [i0 i1 t_sw t_ramp]
%   t < t_sw 에서 i0, t_sw 부터 t_ramp 동안 i1 로 선형 변화, 이후 i1.
%   예) 충전 비상 정지: [375 0 2e-3 10e-6],  충전 시작: [0 375 2e-3 10e-6],  일정 충전: [375 375 0 1]
%   검증 모델 E16(평균모델·스위칭 모델)의 충전전류 프로파일과 같은 정의다.

i0 = prm(1); i1 = prm(2); ts = prm(3); tr = max(prm(4), 1e-12);
a = min(max((t - ts)/tr, 0), 1);
ich = i0 + (i1 - i0)*a;
end
