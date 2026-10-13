function iloss = prism_dab_loss(t, vl, il, iL, vb, prm, ploss0)
%#codegen
%PRISM_DAB_LOSS  DAB 손실 등가 전류(검증 모델과 같은 손실 모델).
%
%   스위칭 회로의 DAB에는 권선저항 R_dab만 있고 스위칭·자기 손실이 없다. 검증 모델(E12)은 평균모델과 같은
%   방향별 효율 η = 0.96을 쓰기 위해, 직전 제어주기의 평균 링크전력 p̄로 정한 손실
%       P_loss = (1/η − 1)·max(p̄, 0) + (1 − η)·max(−p̄, 0) − R_dab·mean(i_L²)   (0 이상)
%   을 버스에서 끄는 전류 P_loss/v_bus로 넣는다. 이 블록은 같은 계산을 해서 버스의 제어 전류원에 준다.
%   이렇게 하면 정상상태의 DAB 총손실이 검증 모델과 같아, 두 모델의 차이는 스위칭 동작에서만 나온다.
%
%   입력  t 시각, vl 링크전압, il 링크 직류전류(2차 브리지 → 링크), iL 누설 전류, vb 버스전압
%         prm [dt Np η R_dab]   ploss0 초기 손실 [W](평형점 링크전력 기준)
%   출력  iloss  버스에서 끄는 손실 전류 [A]

persistent accP accI2 ploss started
if isempty(started)
    started = 1; accP = 0; accI2 = 0; ploss = ploss0;
end
dt = prm(1); Np = round(prm(2)); eta = prm(3); Rd = prm(4);
k = round(t/dt);
accP = accP + vl*il;
accI2 = accI2 + iL*iL;
if mod(k, Np) == Np - 1                       % 주기 마지막 간격에서 갱신(다음 주기에 적용)
    pbar = accP/Np;
    lossEta = (1/eta - 1)*max(pbar, 0) + (1 - eta)*max(-pbar, 0);
    ploss = max(lossEta - Rd*accI2/Np, 0);
    accP = 0; accI2 = 0;
end
iloss = ploss/max(vb, 1);
end
