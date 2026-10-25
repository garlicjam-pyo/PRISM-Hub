function y = prism_tb14_profile(t, prm)
%#codegen
%PRISM_TB14_PROFILE  TB14 시험 조건: 버스 전압 지령과 48 V 정전력 부하 전력의 구간 선형 시간 함수(시험 장치, 제어기 아님).
%
%   prm = [t_V(1:4) V(1:4) t_P(1:4) P(1:4)]  (점이 4개보다 적으면 마지막 점을 반복해 채운다)
%   출력 y = [v_bus 지령 [V]; p_load [W]](p_load < 0이면 48 V 쪽 발전원)

tV = prm(1:4); V = prm(5:8); tP = prm(9:12); P = prm(13:16);
y = [pwl(t, tV, V); pwl(t, tP, P)];
end

function v = pwl(t, tt, yy)
v = yy(4);
if t <= tt(1)
    v = yy(1);
    return
end
for k = 2:4
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
