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
%         모드 2(경부하, TB15부터): 두 브리지를 같은 위상으로 구동한다. 1차 데드타임 t_dp, 2차 t_dsb(자화 전류가 두 브리지로
%         나뉘어 2차 전이가 느려지므로 따로 둔다. 검증 코드 E22 both).
%   입력  t    시각 [s]
%         u    [d; 모드(+1 1차가 보냄, −1 2차가 보냄, 2 두 브리지)]
%         prm  [dt T_b t_db T_c t_dp t_ds (t_dsb)]   (7번이 없으면 t_dsb = t_ds)
%   출력  g    [벅 상측 벅 하측 Q1 Q2 Q3 Q4 S1 S2 S3 S4](1 = 켬)

persistent ml
if isempty(ml), ml = 1; end
dt = prm(1); Tb = prm(2); tdb = prm(3); Tc = prm(4); tdp = prm(5); tds = prm(6);
tdsb = tds;
if numel(prm) >= 7, tdsb = prm(7); end
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
sp = double([(tau >= tdp) && (tau < Tc/2); (tau >= Tc/2 + tdp) && (tau < Tc)]);     % 1차 데드타임
ss = double([(tau >= tds) && (tau < Tc/2); (tau >= Tc/2 + tds) && (tau < Tc)]);     % 2차(보낼 때)
sb = double([(tau >= tdsb) && (tau < Tc/2); (tau >= Tc/2 + tdsb) && (tau < Tc)]);   % 2차(두 브리지 구동)
if ml > 1.5                                          % 두 브리지 같은 위상
    g(3:6) = sp([1 2 2 1]);
    g(7:10) = sb([1 2 2 1]);
elseif ml > 0
    g(3:6) = sp([1 2 2 1]);
else
    g(7:10) = ss([1 2 2 1]);
end
end
