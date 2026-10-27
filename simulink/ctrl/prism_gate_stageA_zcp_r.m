function [g, st_out] = prism_gate_stageA_zcp_r(t, iC, prm, en, off)
%#codegen
%PRISM_GATE_STAGEA_ZCP_R  Stage A(2:1 공진 SC, 최대 8위상) 영교차 추종 게이트 — 방향 반전 처리판(E27, TB21).
%
%   prism_gate_stageA_zcp.m(TB06–TB20)과 같고 한 가지만 다르다: 무장하지 못한 반주기(도통 중 |i|가 5·i_thr를 한 번도
%   넘지 않음)는 최대 도통시간 n_max가 아니라 공칭 도통시간 n_nom = prm(7)에서 끈다. 모듈 전류가 0을 지나는 방향 반전
%   (충전 시작·종료)에서 첨두가 무장 문턱보다 작은 반주기가 생기면, 이전 게이트는 영교차를 검출하지 못하고 n_max까지 두어
%   반대 방향 전류가 자란 뒤에 껐다(TB20 사례 D, 1.010 A). 무장한 반주기는 이전과 같다.
%
%   위상마다 다음 상태기계를 적분 간격 dt마다 한 번 진행한다(검증 모델 model_stage_a.py, mode='zcp'와 같은 논리).
%     구간 0(데드타임) → 구간 1(S1·S3: 입력 → C_fly → 출력, 충전) → 구간 0 → 구간 2(S2·S4: C_fly → 출력, 방전) → …
%     - 데드타임이 n_dead 간격 지나면 다음 구간(1과 2를 번갈아)을 시작한다.
%     - 도통 중 공진전류 크기가 5·i_thr를 넘으면 그 펄스의 부호를 기억하고 영교차 검출을 준비한다(arming).
%     - 펄스 부호 기준으로 전류가 i_thr 아래로 돌아오면 영교차로 보고, n_det 간격 연속이면(검출 지연) 구간을 끝낸다.
%     - 블랭킹·보호 창: 도통 n_min 간격 전에는 끄지 않고, n_max 간격이 되면 강제로 끈다
%     - (방향 반전 처리) 무장하지 못한 반주기는 n_nom 간격에서 끈다
%       (공칭 도통시간 t_on = 1/(2 f_r0) − t_d 의 0.80–1.12배).
%   부품 공차로 공진주파수가 달라져도 각 위상이 자기 전류의 영교차에서 끄므로 영전류 스위칭(ZCS)이 유지된다.
%   전류 부호로 판정하므로 역방향 전력(V_A → 배터리)에서도 같은 논리가 동작한다.
%
%   입력  t    시각 [s] (Digital Clock, 간격 dt) — 이 함수는 간격마다 한 번 호출된다고 가정한다
%         iC   8×1 위상별 공진전류 측정값 [A] (한 간격 지연 + 시작 표본 보호를 거친 값. 정지 위상은 0)
%         prm  [dt n_dead n_min n_max n_det i_thr n_nom]  (간격 수 단위, n_nom = 공칭 도통시간 t_on/dt)
%         en   1×8 위상 동작 여부(1 = 동작, 0 = 정지: 네 스위치 모두 끔 → 모듈 셰딩)
%         off  1×8 위상별 시작 지연 [간격 수] (인터리빙: 동작 위상 N개에 반주기/N 간격)
%   출력  g      32×1 게이트 [위상1 S1 S2 S3 S4, 위상2 S1 … , 위상8 S4] (1 = 켬)
%         st_out 8×1 위상별 현재 구간(0 데드타임, 1 충전, 2 방전) — ZCS 평가용 기록

N = 8;
persistent st nxt tmr oncnt armed det psign
if isempty(st)
    st = zeros(N, 1); nxt = ones(N, 1); tmr = -off(:); oncnt = zeros(N, 1);
    armed = zeros(N, 1); det = zeros(N, 1); psign = zeros(N, 1);
end
ndead = prm(2); nmin = prm(3); nmax = prm(4); ndet = prm(5); ithr = prm(6); nnom = prm(7);

for k = 1:N
    if en(k) < 0.5
        st(k) = 0;
        continue
    end
    % 데드타임이 끝나면 다음 구간 시작
    if st(k) == 0 && tmr(k) >= ndead
        st(k) = nxt(k); nxt(k) = 3 - nxt(k);
        armed(k) = 0; det(k) = 0; oncnt(k) = 0; tmr(k) = 0;
    end
    if st(k) ~= 0
        % 펄스 부호 기억(전류가 충분히 커졌을 때)
        if armed(k) < 0.5 && abs(iC(k)) > 5*ithr
            psign(k) = sign(iC(k)); armed(k) = 1;
        end
        % 영교차 검출(펄스 부호 기준으로 전류가 i_thr 아래)
        cross = armed(k) > 0.5 && psign(k)*iC(k) < ithr;
        if cross, det(k) = det(k) + 1; else, det(k) = 0; end
        oncnt(k) = oncnt(k) + 1;
        if (oncnt(k) >= nmin && cross && det(k) > ndet) || oncnt(k) >= nmax ...
                || (armed(k) < 0.5 && oncnt(k) >= nnom)          % 무장 못 한 반주기: 공칭 도통시간에서 끔
            st(k) = 0; tmr(k) = 0;
        end
    end
    if st(k) == 0
        tmr(k) = tmr(k) + 1;
    end
end

g = zeros(4*N, 1);
for k = 1:N
    b = 4*(k - 1);
    on1 = double(st(k) == 1); on2 = double(st(k) == 2);
    g(b + 1) = on1;    % S1 VIN–A
    g(b + 2) = on2;    % S2 A–V_A
    g(b + 3) = on1;    % S3 V_A–B
    g(b + 4) = on2;    % S4 B–GND
end
st_out = st;
end
