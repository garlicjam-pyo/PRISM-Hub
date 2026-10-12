function g = prism_gate_stageA(t, prm, en, off)
%#codegen
%PRISM_GATE_STAGEA  Stage A(2:1 공진 SC, 최대 8위상) 고정 타이밍 게이트 생성기.
%
%   한 위상의 스위치 4개(S1 VIN–A, S2 A–V_A, S3 V_A–B, S4 B–GND)를 다음 순서로 켠다.
%     전반주기 [t_d, T/2)      : S1·S3 도통 → 플라잉 커패시터가 출력과 직렬로 충전(입력 → C_fly → 출력)
%     후반주기 [T/2 + t_d, T)  : S2·S4 도통 → 플라잉 커패시터가 출력으로 방전
%     각 반주기 앞의 t_d       : 데드타임(모두 끔, 바디 다이오드가 전류를 넘긴다)
%   스위칭 주기 T = 1/f_s, f_s = 0.98·f_r0(설계값). 공진 반주기보다 약간 긴 반주기를 써서 전류가 0에 가까울 때 끈다.
%   위상 k는 off(k)만큼 늦게 시작한다(인터리빙, 동작 위상 N개에 T/(2N) 간격).
%   검증 코드(model_stage_a.py, mode='fixed')와 같은 타이밍이다. 시각은 적분 간격 dt 격자에 맞춘다.
%
%   입력  t    시뮬레이션 시각 [s] (Digital Clock, 간격 dt)
%         prm  [dt T t_d Nph]
%         en   1×8 위상 동작 여부(1 = 동작, 0 = 정지: 네 스위치 모두 끔 → 모듈 셰딩)
%         off  1×8 위상별 시작 지연 [s]
%   출력  g    32×1 게이트 [위상1 S1 S2 S3 S4, 위상2 S1 … , 위상8 S4] (1 = 켬)

dt = prm(1); T = prm(2); td = prm(3);
N = 8;
g = zeros(4*N, 1);
t0 = round(t/dt)*dt;                 % 적분 간격 격자 시각
for k = 1:N
    if en(k) > 0.5
        tau = mod(t0 - off(k) + 1e-3*dt, T);          % 주기 안 위치(작은 치우침으로 경계 반올림 오차 흡수)
        on1 = (tau >= td) && (tau < T/2);            % S1·S3
        on2 = (tau >= T/2 + td) && (tau < T);        % S2·S4
        b = 4*(k - 1);
        g(b + 1) = double(on1);    % S1
        g(b + 2) = double(on2);    % S2
        g(b + 3) = double(on1);    % S3
        g(b + 4) = double(on2);    % S4
    end
end
end
