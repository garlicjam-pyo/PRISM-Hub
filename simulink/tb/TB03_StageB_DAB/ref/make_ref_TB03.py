"""TB03 기준값 생성: 검증 모델(E12 스위칭 ODE)의 DAB 부분만 떼어 같은 개루프 위상 계단을 계산한다.

model_stage_b_switching.run_core의 DAB 에지 일정(반주기 중심 대칭 에지, A ← −A + 2Δ 위상 갱신, 남은 에지가
과거로 가면 지금 스위칭), 데드타임 구간 평균(_dab_avg: 전류가 있으면 다이오드가 출력을 정함), 영전류 클램프를
그대로 옮기고, 버스·링크 전압은 이상 전압원(400 V, 100 V)으로 고정했다. 적분은 run_core와 같은 중점법, 간격 5 ns.
결과: TB03_ref_python.csv(주기별 i_L 평균·링크전류 평균), TB03_ref_python.json(단계별 정상 링크전류)
실행: python make_ref_TB03.py <검증 코드 python 폴더>
"""
import json, math, sys
import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
from model_stage_b_switching import _dab_avg  # noqa: E402

PI = math.pi
dt = 5e-9; T = 5e-6; Np = int(round(T / dt)); Nh = Np // 2
Vb, Vl, n, L, Rd, td = 400.0, 100.0, 4.0, 11.1e-6, 0.02, 100e-9
t_steps = np.arange(5) * 100e-6; ph_steps = np.array([0.4, 0.8, -0.5, 0.15, 0.08])
n_tot = int(round(500e-6 / dt))

def ph_at(t):
    return ph_steps[np.searchsorted(t_steps, t + 1e-15, side="right") - 1]

ph_tgt = ph_steps[0]; d0 = ph_tgt / (2 * PI) * T; A = d0
p_t = np.full(2, 1e30); s_t = np.full(2, 1e30); p_h = np.zeros(2); s_h = np.zeros(2)
p_te = -1.0; s_te = -1.0
p_j = 1; p_h[0] = -d0 / 2; p_state = 1.0; p_before = 1.0; s_j = 0; s_state = -1.0; s_before = -1.0
iL = 0.0
per_iL = []; per_il = []; acc_iL = 0.0; acc_il = 0.0
for i in range(n_tot):
    t0 = i * dt; t1 = t0 + dt
    if i % Nh == 0:
        ph_tgt = ph_at(t0)
        j = i // Nh; cj = t0
        if j >= 1:
            jm = (j - 1) % 2
            A = -A + 2 * (s_h[jm] - p_h[jm])
        dtg = ph_tgt / (2 * PI) * T
        D = .5 * (A + dtg); jj = j % 2
        p_done = p_j > j; s_done = s_j > j
        if p_done and not s_done:
            s_t[jj] = max(cj, p_h[jj] + D)
        elif s_done and not p_done:
            p_t[jj] = max(cj, s_h[jj] - D)
        elif not p_done and not s_done:
            if D >= 0:
                p_t[jj] = cj; s_t[jj] = cj + D
            else:
                s_t[jj] = cj; p_t[jj] = cj - D
        tpj = p_h[jj] if p_done else p_t[jj]
        tsj = s_h[jj] if s_done else s_t[jj]
        D1 = .5 * (-A + 2 * (tsj - tpj) + dtg)
        cn = (j + 1) * Nh * dt
        p_t[1 - jj] = cn - D1 / 2; s_t[1 - jj] = cn + D1 / 2
    if p_t[p_j % 2] < t1:
        te = max(p_t[p_j % 2], t0)
        p_before = p_state; p_state = 1. if p_j % 2 == 0 else -1.; p_te = te; p_h[p_j % 2] = te; p_t[p_j % 2] = 1e30; p_j += 1
    if s_t[s_j % 2] < t1:
        te = max(s_t[s_j % 2], t0)
        s_before = s_state; s_state = 1. if s_j % 2 == 0 else -1.; s_te = te; s_h[s_j % 2] = te; s_t[s_j % 2] = 1e30; s_j += 1
    iL0 = iL
    s1, s2 = _dab_avg(t0, t1, p_te, p_before, p_state, s_te, s_before, s_state, td, iL0, Vb, n * Vl)
    f = lambda x: (s1 * Vb - n * s2 * Vl - Rd * x) / L
    iL = iL + dt * f(iL + .5 * dt * f(iL))
    pd1 = p_te < t1 < p_te + td; sd1 = s_te < t1 < s_te + td
    if pd1 or sd1:
        if (iL0 > 0. and iL <= 0.) or (iL0 < 0. and iL >= 0.):
            iL = 0.
        elif iL0 == 0.:
            if (pd1 and sd1) or (pd1 and n * Vl <= Vb) or (sd1 and Vb <= n * Vl):
                iL = 0.
    acc_iL += iL; acc_il += n * s2 * iL
    if i % Np == Np - 1:
        per_iL.append(acc_iL / Np); per_il.append(acc_il / Np); acc_iL = 0.0; acc_il = 0.0

per_iL = np.array(per_iL); per_il = np.array(per_il); tc = (np.arange(len(per_iL)) + .5) * T
np.savetxt("TB03_ref_python.csv", np.c_[tc, per_iL, per_il], delimiter=",",
           header="t_center_s,iL_period_mean_A,ilink_period_mean_A", comments="", fmt="%.9g")
seg = []
for s in range(5):
    q1 = int(round((t_steps[s] + 100e-6) / T)); q0 = q1 - 10
    seg.append(dict(phi=float(ph_steps[s]), I_link=float(per_il[q0:q1].mean()), iL_bias=float(per_iL[q0:q1].mean())))
ref = dict(source="make_ref_TB03.py: DAB part of model_stage_b_switching.run_core, fixed 400 V / 100 V, dt 5 ns",
           segments=seg, dc_bias_max=float(np.abs(per_iL).max()))
json.dump(ref, open("TB03_ref_python.json", "w"), indent=1)
print(json.dumps(ref, indent=1))
print("period mean iL (A):", np.round(per_iL[38:66], 2))
