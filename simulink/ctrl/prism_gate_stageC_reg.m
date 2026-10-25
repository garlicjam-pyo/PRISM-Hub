function g = prism_gate_stageC_reg(t, u, prm)
%#codegen
%PRISM_GATE_STAGEC_REG  조정형 Stage C 게이트: 동기 벅(중앙 정렬 PWM, 100 kHz) + CLLC DCX(공진점 250 kHz, 보내는 쪽만 스위칭).
%
%   벅: 삼각 반송파 c = 2·min(τ, 1 − τ)(τ = 주기 안 위치, 골 τ = 0에서 제어 표본). 상측은 c < d − t_db/T_b,
%       하측은 c > d + t_db/T_b에서 켠다(전이마다 데드타임 t_db).
%   CLLC: 보내는 쪽 브리지만 [t_dc, T/2) +1(1·4번), [T/2 + t_dc, T) −1(2·3번)으로 스위칭하고, 받는 쪽은 꺼 둔다.
%         데드타임은 보내는 쪽마다 다르다: 1차가 보낼 때 t_dp(자화 전류 수 A로 1차 레그 전이), 2차가 보낼 때 t_ds(전류가 커서
%         전이가 빠르고, 길면 공진전류가 반전해 노드가 되돌아간다. 검증 코드 E22 zvs)
%         (받는 쪽 소자는 역병렬 다이오드로 도통 = 이상 동기정류. 검증 코드 E22 dcx와 같은 방식).
%         보내는 쪽(제어기 출력)은 CLLC 주기 시작에서만 바꿔 반쪽 펄스를 막는다.
%   입력  t    시각 [s]
%         u    [d; 보내는 쪽(+1 1차, −1 2차)]
%         prm  [dt T_b t_db T_c t_dp t_ds]
%   출력  g    [벅 상측 벅 하측 Q1 Q2 Q3 Q4 S1 S2 S3 S4](1 = 켬)

persistent ml
if isempty(ml), ml = 1; end
dt = prm(1); Tb = prm(2); tdb = prm(3); Tc = prm(4); tdp = prm(5); tds = prm(6);
t0 = round(t/dt)*dt;
g = zeros(10, 1);
% ---- 동기 벅 ----------------------------------------------------------------------------------------
tb = mod(t0 + 1e-3*dt, Tb)/Tb;
c = 2*min(tb, 1 - tb);
d = u(1);
g(1) = double(c < d - tdb/Tb);
g(2) = double(c > d + tdb/Tb);
% ---- CLLC DCX ---------------------------------------------------------------------------------------
tau = mod(t0 + 1e-3*dt, Tc);
if tau < dt
    ml = u(2);                                       % 주기 시작에서만 보내는 쪽을 바꾼다
end
tdc = tdp;
if ml < 0, tdc = tds; end
on1 = (tau >= tdc) && (tau < Tc/2);
on2 = (tau >= Tc/2 + tdc) && (tau < Tc);
s = double([on1; on2; on2; on1]);
if ml > 0
    g(3:6) = s;
else
    g(7:10) = s;
end
end
