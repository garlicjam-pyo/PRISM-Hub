"""TB10 기준값 생성: H-브리지 고장 강등의 DAB 고장 모드 변조(검증 코드 E20의 P3 = E17 r2_run에 hold 'match',
dmod 'eps', curtail, soft_fail).

사례(모두 R2-W460: V_W 460 V, DAB 4.6:1·4 kW, 바이패스 3.3 mΩ, 버스 RC 감쇠기, 링크 제동 저항 3 Ω)
  A  1008 V, 25 kW, H-브리지 개방 → 전압비 정합 유지(링크 ≈ 89 V, DAB 정격 밖은 제동 저항) → 400 V 부하 분리(3 ms)
     → 링크 붕괴(EPS, 첨두 ≤ 1.5 × 정격점) → 소프트 투입 → 강등
  B   930 V, 25 kW, 같은 고장. V_A ≤ 상한이지만 일시 감발(3 ms) 뒤 붕괴·투입, 강등 0.5 ms 뒤 부하 되돌림
  C   930 V, 25 kW, 켬(전류 조향): EPS가 꺼진 정상 순서가 TB09와 같은지(새 게이트 생성기의 회귀)
  부하 분리·감발 시간은 회로 계산 시간을 줄이려고 3 ms(E17·E20 기본 20 ms).
결과: TB10_<사례>_init.json, _avg.csv, _metrics.json, TB10_eps_table.json(회로 지령표: j ≤ 0만), TB10_ref_summary.json
실행: python make_ref_TB10.py <검증 코드 python 폴더>
"""
import json
import math
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E17_protection_integration as E17          # noqa: E402
import E19_r2_window_module as E19                # noqa: E402
import dab_modulation as DM                       # noqa: E402
from controller_adopted import K_ADOPTED          # noqa: E402
from model_stage_b import equilibrium             # noqa: E402

CASE = "W460_240s"
T_SHED_TB = 3e-3
P3 = dict(hold="match", dmod="eps", soft_fail=True, curtail=True)
CASES = {
    "A_1008V_hbopen_25kW": dict(V=1008., P=25000., event="hb_open", policy="clamp_brk", t_shed=T_SHED_TB, duration=E17.T_EV + 16.5e-3, **P3),
    "B_930V_hbopen_25kW": dict(V=930., P=25000., event="hb_open", policy="clamp_brk", t_shed=T_SHED_TB, duration=E17.T_EV + 16.5e-3, **P3),
    "C_930V_enable_steer_25kW": dict(V=930., P=25000., event="enable", prep="steer", wait=0., duration=E17.T_EV + 3.5e-3),
}
EV = {"enable": 1, "disable": 2, "dab": 3, "hb_open": 4, "m_pos": 5, "m_neg": 6}
POL = {"now": 1, "collapse_now": 2, "clamp": 3, "clamp_brk": 4, "clamp_brk_hard": 5, "ramp": 1, "brk_hold": 2}
FTYPE = {"hb_open": 1, "dab": 2}

c = E19.CASES[CASE]; p, cp = E19.plant(CASE)
K = np.asarray(K_ADOPTED, float)
pk_rated = E17.dab_sps_peak(c["VW"], 100., p.power_max / 100., p)

# ---- 회로 지령표(j ≤ 0): 1차 펄스 폭 d, 등가 위상 φ = α + D1·π(−π, π]), 정규화 첨두 ------------------------------
T = DM.eps_table()
J = np.asarray(T["j"]); keep = J <= 1e-9
d = np.asarray(T["d"])[:, keep]; a = np.asarray(T["a"])[:, keep]; pk = np.asarray(T["pk"])[:, keep]
d[:, -1] = d[:, -2]; a[:, -1] = a[:, -2]; pk[:, -1] = pk[:, -2]           # j = 0 열(퇴화)은 j = −0.01 열로
phi = np.vectorize(lambda aa, dd: math.remainder(aa + (1 - dd / np.pi) * np.pi, 2 * np.pi))(a, d)
jump = float(np.nanmax(np.abs(np.diff(phi, axis=1))))
tab = dict(r0=float(T["r"][0]), dr=float(T["r"][1] - T["r"][0]), j0=float(J[keep][0]), dj=float(J[1] - J[0]),
           d=d.tolist(), phi=phi.tolist(), pk=pk.tolist(), pk_max=E17.PK_FAULT * pk_rated, rated_pk=pk_rated, max_phi_step=jump)
json.dump(tab, open("TB10_eps_table.json", "w"))
print("eps table %d x %d, pk_max %.2f A, max phi step along j %.3f rad" % (d.shape[0], d.shape[1], tab["pk_max"], jump))

out = {}
for name, job in CASES.items():
    j = dict(case=CASE, keep=True, **job)
    m = E17.r2_run(j)
    tr = m.pop("trace")
    V, P = job["V"], job["P"]
    if job["event"] == "enable":
        x0 = E17.bypass_state(V, P, p); st0 = 0
    else:
        xe, ue = equilibrium(V, P, p); x0 = np.array(xe, float); st0 = 3
    u0 = np.array([x0[1] / x0[4], 0.])
    q0 = float(-(x0[0] + K[:4] @ x0[:4]) / K[4])
    sup = [c["VW"], c["upper"], E17.H, p.R, p.Rh, p.Cs, p.Lh, p.inner_tau, p.Clink, j.get("vd", E17.VD),
           E17.T_EV, EV[job["event"]], POL.get(job.get("policy", "clamp_brk"), 4), 1. if job.get("prep") == "steer" else 0.,
           1. if job.get("close") == "steer" else 0., j.get("t_prep", E17.T_PREP), j.get("wait", E17.T_WAIT),
           E17.RAMP, E17.HOLD, E17.ZERO, j.get("t_shed", E17.T_SHED), E17.RATE_COL, E17.VL_SOFT, j.get("t_soft", E17.T_SOFT),
           E17.R_SOFT0, E17.R_BYP, E17.T_COL_MAX, E17.VL_SW[0], E17.VL_SW[1], E17.T_SW, E17.VB_SW, E17.T_VB,
           E17.KP_B, E17.KI_B, E17.QB_MAX, E17.W_L, E17.TAU_ST, 1e6, p.power_max, p.link_max, p.turns, p.phase_max,
           p.fs, p.Ldab, V, st0, p.Ts, E17.VS_GATE, E17.T_GATE, E17.T_GATE_MAX,
           E17.VL_STALL, E17.T_STALL, E17.DV_STALL, E17.DI_SOFT, E17.K_UP, E17.T_SOFT_MAX,
           1. if job.get("hold") == "match" else 0., 1. if job.get("curtail") else 0., 1. if job.get("soft_fail") else 0., E17.T_RESTORE]
    prot = [E17.T_HW, E17.I_HW, E17.VL_HW, E17.VS_HW, c["upper"], FTYPE.get(job["event"], 0), E17.T_EV, E17.T_GDF]
    eps_prm = [1. if job.get("dmod") == "eps" else 0., p.turns, p.Ldab, p.fs, E17.PK_FAULT * pk_rated,
               tab["r0"], tab["dr"], tab["j0"], tab["dj"]]
    init = dict(case=name, vbat=V, P0=P, Pc=min(P, E17.P_C), t_end=job["duration"], x0=x0[:6].tolist(), vcd0=float(x0[2]),
                u0=u0.tolist(), q0=q0, st0=st0, VW=c["VW"], upper=c["upper"], dab_rated_W=p.power_max, turns=p.turns, Ldab=p.Ldab,
                eta=p.eta, R_bypass=E17.R_BYP, Vd=j.get("vd", E17.VD), Rbrk=E17.R_BRK, Rdmp=E17.R_DMP, Cdmp=E17.C_DMP,
                sup_prm=sup, prot_prm=prot, eps_prm=eps_prm, event=job["event"], policy=job.get("policy", "-"),
                rated_pk=pk_rated, pk_max=E17.PK_FAULT * pk_rated)
    json.dump(init, open(f"TB10_{name}_init.json", "w"), indent=1)
    L = tr["log"]; t = tr["t"]
    np.savetxt(f"TB10_{name}_avg.csv", np.column_stack([t, L[:, :6], L[:, 6], L[:, 7], L[:, 8], L[:, 9]]), delimiter=",",
               header="t_s,ip,vs,vbus,ih,vlink,idab,ibyp,loads400,bridge,Pbrk", comments="", fmt="%.9g")
    json.dump({k: v for k, v in m.items()}, open(f"TB10_{name}_metrics.json", "w"), indent=1, default=float)
    out[name] = dict(pass_=m["pass_"], failed=[k for k, v in m["checks"].items() if not v], events=m["events"],
                     path_peak=m["path_peak"], bridge_peak=m["bridge_peak"], vbus_min=m["vbus_min"], vbus_max=m["vbus_max"],
                     vbus_max_loaded=m["vbus_max_loaded"], vlink_max=m["vlink_max"], vlink_min=m["vlink_min"],
                     byp_peak=m["byp_peak"], brk_energy_J=m["brk_energy_J"], soft_entry=m.get("soft_entry"), soft_ms=m.get("soft_ms"),
                     soft_energy_J=m.get("soft_energy_J"), dab_sec_peak=m.get("dab_sec_peak"), dab_peak_hold=m.get("dab_peak_hold"),
                     dab_peak_collapse=m.get("dab_peak_collapse"), dab_peak_limit=m.get("dab_peak_limit"))
    print(name, "PASS" if m["pass_"] else "FAIL", {k: out[name][k] for k in ("events", "path_peak", "vbus_min", "brk_energy_J",
                                                                            "soft_energy_J", "dab_sec_peak", "dab_peak_hold", "dab_peak_collapse")})
json.dump(out, open("TB10_ref_summary.json", "w"), indent=1, default=float)
