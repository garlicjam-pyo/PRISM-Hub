function y = prism_tb20_profile(t, prm)
%#codegen
%PRISM_TB20_PROFILE  TB20 시험 조건: 충전기 전류, 400 V 부하 전력, 48 V 부하 전력, Stage A 위상 동작 여부.
%
%   y = prism_tb20_profile(t, prm),   y = [i_ch; Q_400; P_48; en(1:8)]  (11×1)
%   prm = [t_I(6) I(6) t_ev mask(8) Q P]  (23개)
%     t_I·I : 충전기 전류 구간 선형 6점(시각 오름차순). 비상 정지(5 A 이하에서 차량 접촉기 개방)를 포함한 전류를
%             검증 코드 E26(run_event의 ich_pwl)과 같은 점으로 준다.
%     t_ev  : Stage A 사건 시각. 이 시각부터 위상 동작 여부가 mask(1이면 동작, 0이면 게이트 차단)가 된다.
%             배터리 경로 상실은 mask = 0(8위상 모두 차단), 모듈 4 고장은 mask = [1 1 1 1 1 1 0 0].
%     Q·P   : 400 V 부하 전력과 48 V 부하 전력(사례 동안 일정)

tI = prm(1:6); II = prm(7:12); tev = prm(13); mask = prm(14:21); Q = prm(22); P = prm(23);
ich = II(6);
if t <= tI(1)
    ich = II(1);
else
    for k = 1:5
        if t <= tI(k + 1)
            a = (t - tI(k))/max(tI(k + 1) - tI(k), 1e-12);
            ich = II(k) + a*(II(k + 1) - II(k));
            break
        end
    end
end
en = ones(8, 1);
if t >= tev
    en = mask(:);
end
y = [ich; Q; P; en];
end
