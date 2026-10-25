function y = prism_tb18_profile(t, prm)
%#codegen
%PRISM_TB18_PROFILE  TB18 시험 조건: 400 V 버스 정전력 부하 전력과 V_A 노드 직접 전류(충전기 등)의 구간 선형 시간 함수(시험 장치).
%
%   prm = [t_P(1:6) P(1:6) t_I(1:6) I(1:6)]  (점이 6개보다 적으면 마지막 점을 반복해 채운다)
%   출력 y = [P [W]; I_VA [A]](I_VA > 0이면 V_A 노드에서 빼는 부하, < 0이면 충전기 주입)
%   같은 시각에 두 점을 두면 계단이다(뒤 점의 값으로 바뀜).

tP = prm(1:6); P = prm(7:12); tI = prm(13:18); I = prm(19:24);
y = [pwl(t, tP, P); pwl(t, tI, I)];
end

function v = pwl(t, tt, yy)
v = yy(6);
if t <= tt(1)
    v = yy(1);
    return
end
for k = 2:6
    if t <= tt(k)
        if tt(k) > tt(k-1)
            v = yy(k-1) + (yy(k) - yy(k-1))*(t - tt(k-1))/(tt(k) - tt(k-1));
        else
            v = yy(k);
        end
        return
    end
end
end
