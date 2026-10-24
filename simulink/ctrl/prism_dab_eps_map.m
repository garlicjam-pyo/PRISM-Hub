function eps = prism_dab_eps_map(sup, meas, prm, tD, tP, tK)
%#codegen
%PRISM_DAB_EPS_MAP  H-브리지 고장 강등 중 DAB 고장 모드 변조(EPS) 지령(TB10, 검증 코드 E20과 같은 표).
%
%  강등 상태(9 유지, 10 링크 붕괴, 11 소프트 투입)에서 DAB 모드가 보조 지령(1)이면, 상태기계의 보조 링크전류 지령을
%  1차 내부 위상천이(EPS) 지령 [등가 위상 φ; 내부 위상비 D1]로 바꾼다. 게이트 생성기(ctrl/prism_gate_stageB_e.m)는
%  1차 두 레그 가운데 레그 2를 D1·T/2만큼 늦춰 1차 전압에 영구간을 넣고, 2차는 φ만큼 위상을 둔 구형파로 둔다.
%
%  정규화(2차 환산): V1' = v_bus/n, ωL' = 2π f_s L_dab/n², I_b = V1'/ωL', r = v_link/V1', j = 지령/I_b.
%  표(검증 코드 dab_modulation.py가 만든 것을 TB10_init.m이 읽음): r(행) × j(열, −0.78–0, 링크 → 1차만)마다
%    tD 1차 펄스 폭 d [rad](D1 = 1 − d/π), tP 등가 위상 φ [rad], tK 정규화 첨두.
%  첨두 상한: 같은 r에서 tK ≤ pk_max/I_b인 가장 큰 |j|까지만 지령한다(나머지 링크전력은 제동 저항이 받음).
%  링크를 채우는 지령(j > 0)은 내지 않는다(강등 중 링크는 다이오드 정류 전류로 채워진다).
%
%  입력  sup   상태기계 지령 12개(5 DAB 모드, 6 보조 링크전류 지령, 11 상태)
%        meas  [v_bus v_link]
%        prm   [켬 n L_dab f_s pk_max r0 dr j0 dj]
%  출력  eps   [EPS 켬; φ; D1]

on = prm(1) > 0.5 && round(sup(5)) == 1 && round(sup(11)) >= 9 && round(sup(11)) <= 11;
eps = [0; 0; 0];
if ~on
    return
end
n = prm(2); Ld = prm(3); fs = prm(4); pkmax = prm(5);
r0 = prm(6); dr = prm(7); j0 = prm(8); dj = prm(9);
[nr, nj] = size(tD);
v1 = max(meas(1), 1)/n;
Ib = v1/(2*pi*fs*Ld/(n*n));
r = min(max(meas(2)/v1, r0), r0 + (nr - 1)*dr);
ir = min(floor((r - r0)/dr) + 1, nr - 1); fr = (r - r0)/dr - (ir - 1);
% 첨두 상한을 지키는 최대 |j|(j = 0 열에서 음의 방향으로)
tgt = pkmax/Ib;
jl = 0;
for k = nj:-1:1
    pk = (1 - fr)*tK(ir, k) + fr*tK(ir + 1, k);
    if pk > tgt
        break
    end
    jl = -(j0 + (k - 1)*dj);
end
jn = min(max(sup(6)/Ib, -jl), 0);
jn = max(jn, j0);
ij = min(floor((jn - j0)/dj) + 1, nj - 1); fj = (jn - j0)/dj - (ij - 1);
d  = (1 - fr)*(1 - fj)*tD(ir, ij) + (1 - fr)*fj*tD(ir, ij + 1) + fr*(1 - fj)*tD(ir + 1, ij) + fr*fj*tD(ir + 1, ij + 1);
ph = (1 - fr)*(1 - fj)*tP(ir, ij) + (1 - fr)*fj*tP(ir, ij + 1) + fr*(1 - fj)*tP(ir + 1, ij) + fr*fj*tP(ir + 1, ij + 1);
D1 = min(max(1 - d/pi, 0), 0.95);
eps = [1; ph; D1];
end
