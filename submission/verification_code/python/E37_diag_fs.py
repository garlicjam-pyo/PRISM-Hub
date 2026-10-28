"""[E37 실행 뒤 진단] 이중 고장 F2에서 C_A 방전 저항(1 Ω)을 넣어도 W460 팩의 경로전류가 5 ms 안에 1 A 아래로 머물지 않는 이유.
Stage A 정지 뒤 0–8 ms의 경로전류·직렬 전압·버스·H-브리지 전류·링크를 방전 없음/1 Ω으로 비교한다(판정 아님).
실행: python E37_diag_fs.py"""
import sys, numpy as np
sys.path.insert(0, ".")
import E17_protection_integration as E17, E29_sals_degradation as E29
from common import load_json
for case, V in (("W460_240s", 930.), ("W410_spec", 920.)):
    det = load_json("E29", "failsafe")["dab_det_ms"]["%s_%.0f" % (case, V)]
    t2 = E17.T_EV + det * 1e-3 + E29.T_EV2
    for R in (None, 1.0):
        ast = dict(E29.ASTOP, C_A=2.4e-3) if R is None else dict(E29.ASTOP, C_A=2.4e-3, R_dis=R)
        job = dict(case=case, V=V, P=E29.P0, event="dab", policy="brk_hold", event2=t2, duration=t2 + 10e-3, keep=True,
                   sals=E29.sals_cfg(case, E29.MIXES["MX"], E29.SCEN["S5"]), fs_brake=True, astop=ast, **E29.P3T)
        m = E17.r2_run(job); tr = m["trace"]; t, lg = tr["t"], tr["log"]
        ta = E17.T_EV + m["t_astop_ms"] * 1e-3
        print(case, V, "R", R, "t_astop %.2f ms" % m["t_astop_ms"], "events", [e for e in m["events"] if e[1] > m["t_astop_ms"] - 1][:8])
        for dtm in (0, 0.5, 1, 2, 3, 4, 5, 6, 7, 8):
            k = np.searchsorted(t, ta + dtm * 1e-3)
            if k >= len(t): break
            print("   +%.1f ms: i_p %7.2f A, v_s %7.2f V, v_bus %6.1f V, i_h %6.1f, v_link %6.1f, loads %d" % (dtm, lg[k,0], lg[k,1], lg[k,2], lg[k,3], lg[k,4], lg[k,7]))
