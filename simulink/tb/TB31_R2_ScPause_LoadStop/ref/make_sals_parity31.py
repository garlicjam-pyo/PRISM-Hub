"""(TB31) 회로 부하 블록(ctrl/prism_sals_loads.m, 파라미터 23개)과 검증 코드 sals_loads.SalsLoads의 대조 자료.

TB23 대조(make_sals_parity.py)에 E38의 Stage C 일시 정지·재개(비트 32)와 400 V 부하 정지(비트 64, 램프 = 23번째 파라미터)를 더했다.
무작위 시나리오 40개마다 명령 시각(감발·회생 차단, 되돌림, 접촉기 열림, 일시 정지·재개, 부하 정지)을 정하고 0–80 ms를 0.1 ms 간격으로
Python 부하 전력을 계산해 sals_parity31.csv에 쓴다. check_sals_parity31.m이 같은 입력을 MATLAB 함수에 넣어 차를 잰다.
실행: python make_sals_parity.py <검증 코드 python 폴더>
"""
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
from sals_loads import SalsLoads, DEV          # noqa: E402

rng = np.random.default_rng(20261029)
rows = []
dt = 100e-6
tt = np.arange(0, 80e-3 + 1e-12, dt)
for sid in range(40):
    ks = 1. if sid % 2 == 0 else .15
    mix = dict(sc=float(rng.choice([-3200., 0., 2000., 5300.])), v2l=float(rng.choice([0., 3800.])),
               comp=float(rng.uniform(0, 6000)), ptc=float(rng.uniform(0, 7000)), bh=float(rng.uniform(0, 7000)))
    delay = {k: float(rng.uniform(1e-3, 5e-3)) for k in DEV}
    lost = {k: (int(rng.integers(0, 3)) if rng.random() < .8 else "all") for k in DEV}
    lost_r = {k: int(rng.integers(0, 2)) for k in DEV}
    L = SalsLoads(mix, delay=delay, lost=lost, lost_r=lost_r, ks=ks)
    k_cut = int(rng.integers(5, 20)); t_cut = tt[k_cut]
    k_rest = k_cut + int(rng.integers(50, 300)); t_rest = tt[min(k_rest, len(tt) - 1)]
    k_open = k_cut + int(rng.integers(100, 700)) if rng.random() < .3 else 10 ** 9
    L.curtail(t_cut)
    if rng.random() < .7:
        L.restore(t_rest)
    else:
        t_rest = 1e9
    t_pz = tt[k_cut + int(rng.integers(10, 100))] if rng.random() < .7 else 1e9          # (E38) Stage C 일시 정지
    t_rz = t_pz + float(rng.uniform(2e-3, 15e-3)) if (t_pz < 1e9 and rng.random() < .8) else 1e9
    t_rz = tt[min(int(np.ceil(t_rz / dt - 1e-9)), len(tt) - 1)] if t_rz < 1e9 else 1e9
    t_st = tt[k_cut + int(rng.integers(20, 400))] if rng.random() < .5 else 1e9           # (E38) 400 V 부하 정지
    ramp = float(rng.choice([1e-3, 2e-3, 3e-3, 5e-3]))
    if t_pz < 1e9:
        L.sc_pause(t_pz)
    if t_rz < 1e9:
        L.sc_resume(t_rz)
    if t_st < 1e9:
        L.load_stop(t_st, ramp)
    s = L.describe()
    lk = lambda v: -1. if v == "all" else float(v)
    prm = ([mix["sc"], mix["v2l"], mix["comp"], mix["ptc"], mix["bh"]] + [s["delay_s"][k] for k in DEV]
           + [lk(s["lost"][k]) for k in DEV] + [lk(s["lost_r"][k]) for k in DEV]
           + [s["period_s"], s["wd_s"], s["up_W_per_s"], s["dn_W_per_s"], s["t_sc_s"], s["sc_slew_W_per_s"], 250., 250., ramp])
    for k, t in enumerate(tt):
        op = k >= k_open
        code = ((1 if op else 0) + (2 + 8 if t >= t_cut else 0) + (4 if t >= t_rest else 0)
                + (32 if t_pz <= t < t_rz else 0) + (64 if t >= t_st else 0))
        rows.append([sid, t, 400., code] + prm + [L.power(t, not op)])
np.savetxt("sals_parity31.csv", np.array(rows), delimiter=",", fmt="%.12g",
           header="sid,t,vb,code," + ",".join("p%d" % i for i in range(1, 24)) + ",P_py", comments="")
print("rows", len(rows))
