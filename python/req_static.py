"""Requirements analysis (2026-09-28), static part: R1 bus-window check and R3 minimum battery voltage.

R1  Compares the unregulated Stage A output V_A with published input ranges of 400 V-class
    components and with the 48 V range of ISO 21780 seen through a fixed-gain Stage C.
    Also evaluates a window-regulation variant (bus capped at V_CAP, pass-through below it).
R3  Guaranteed minimum battery voltage from the finite-link averaged model:
      V_g,static : 25 kW steady point feasible with the link at its 90 V lower band limit,
                   path resistance +10 %, modulation <= 0.95, DAB limits.
      V_deg      : same, but the bus reference lowered to the Tier-2 floor of 384 V.
Python only. Not a hardware margin.
"""
from dataclasses import replace
from pathlib import Path
import json
import numpy as np
from scipy.optimize import brentq
from pprc_two_stage import Parameters, equilibrium, current_limit, continuous_power_limit

OUT = Path(__file__).resolve().parents[1] / "validation" / "2026-09-28-requirements"
P = Parameters()
N_STAGE_C = 400 / 48          # fixed-gain CLLC turns ratio (nominal bus / nominal 48 V)
V_CAP = 410.                  # window-variant bus cap: 410 + 8 V transient < 420 V (ISO 21498-1 B_420)

# Published input voltage ranges (V DC). Sources in docs/14 reference list.
COMPONENTS = [
    dict(name="Sanden SHS33 Gen2 전동 컴프레서", vmin=165, vmax=432, src="[S1]"),
    dict(name="Sanden SHS33 Gen3 전동 컴프레서", vmin=165, vmax=470, src="[S1]"),
    dict(name="Sanden SHS45 전동 컴프레서(냉방 10 kW)", vmin=260, vmax=470, src="[S1]"),
    dict(name="Sanden SEE27 전동 컴프레서", vmin=155, vmax=460, src="[S1]"),
    dict(name="Webasto HVH 50/70 고전압 히터(5/7 kW)", vmin=100, vmax=490, src="[S2]"),
    dict(name="BorgWarner Gen5 HV DC/DC(1.2 kW)", vmin=220, vmax=800, src="[S3]"),
]
ISO21498_B420, ISO21498_B470 = 420., 470.     # sub-class upper voltage limits [S4]
ISO21780_48V = (36., 52.)                       # 48 V unlimited (nominal) operating range [S5]


def v_a(vbat, power=25000., p=P):
    """Stage A output under load (2:1 ideal minus path drop at the load current)."""
    i = power / (vbat / 2)
    return vbat / 2 - p.R * i


def static_ok(vbat, power, p, path_limit):
    x, u = equilibrium(vbat, power, p)
    plink = x[4] * x[5]
    return bool(abs(x[0]) <= path_limit and abs(x[1]) <= p.series_max and abs(u[0]) <= p.modulation_max
                and abs(x[5]) <= current_limit(x[2], x[4], p) and abs(plink) <= p.power_max)


def min_vbat(p, power=25000., path_limit=90., lo=560., hi=700.):
    f = lambda v: 1. if static_ok(v, power, p, path_limit) else -1.
    assert f(hi) > 0 and f(lo) < 0
    for _ in range(60):
        mid = (lo + hi) / 2
        if f(mid) > 0: hi = mid
        else: lo = mid
    return hi


def window_variant(vbat, power=25000., p=P):
    """Bus = min(V_A, V_CAP). Returns bus voltage and |link power| of Stage B."""
    va = v_a(vbat, power, p)
    if va <= V_CAP:
        return dict(vbat=vbat, bus_V=va, series_V=0., link_power_W=0., active=False)
    q = replace(p, vref=V_CAP)
    x, u = equilibrium(vbat, power, q)
    return dict(vbat=vbat, bus_V=V_CAP, series_V=float(x[1]), link_power_W=float(x[4] * x[5]),
                path_A=float(x[0]), active=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    grid = list(range(600, 921, 20)) + [640, 866, 920]
    grid = sorted(set(grid))
    # ---------------- R1
    va_rows = []
    for v in grid:
        va0, va25 = v / 2, v_a(v)
        va_rows.append(dict(vbat=v, VA_noload=va0, VA_25kW=va25,
                            v48_fixed_gain_noload=va0 / N_STAGE_C,
                            components_violated=[c["name"] for c in COMPONENTS if not (c["vmin"] <= va25 and va0 <= c["vmax"])],
                            above_B420=va0 > ISO21498_B420, above_B470=va0 > ISO21498_B470,
                            v48_outside_ISO21780=not (ISO21780_48V[0] <= va25 / N_STAGE_C and va0 / N_STAGE_C <= ISO21780_48V[1])))
    vbat_b420 = 2 * ISO21498_B420                    # no-load V_A reaches 420 V
    vbat_48v = 2 * ISO21780_48V[1] * N_STAGE_C       # fixed-gain 48 V output reaches 52 V
    # regulated baseline (③): Stage B link power over the range, for comparison with the window variant
    reg = []
    for v in grid:
        if v < 625: continue
        x, u = equilibrium(float(v), 25000., P)
        reg.append(dict(vbat=v, link_power_W=float(x[4] * x[5]), series_V=float(x[1])))
    win = [window_variant(float(v)) for v in grid]
    # ---------------- R3
    tol = replace(P, R=P.R * 1.1, vlink=90.)
    vg_static = min_vbat(tol)
    vg_nominal = min_vbat(P, path_limit=P.path_max)            # link 100 V, R nominal, ports only
    vdeg = min_vbat(replace(tol, vref=384.))
    vdeg390 = min_vbat(replace(tol, vref=390.))                 # 390 V reference + Tier-2 droop (<= 5.4 V) stays >= 384 V
    vdeg390_mand = min_vbat(replace(tol, vref=390.), power=15100., lo=540.)
    x_g, u_g = equilibrium(vg_static, 25000., tol)
    out = dict(
        scope=__doc__.strip(),
        R1=dict(components=COMPONENTS, iso21498_upper_limits_V=dict(B_420=ISO21498_B420, B_470=ISO21498_B470),
                iso21780_48V_unlimited_V=ISO21780_48V, stage_c_ratio=N_STAGE_C,
                vbat_where_VA_exceeds_B420=vbat_b420, vbat_where_fixed_gain_48V_exceeds_52V=vbat_48v,
                va_table=va_rows,
                regulated_link_power=reg, window_variant=dict(v_cap=V_CAP, rows=win)),
        R3=dict(assumptions=dict(power_W=25000., link_V=90., R_ohm=tol.R, modulation_max=P.modulation_max,
                                 path_limit_A=90.),
                V_g_static=vg_static, V_static_nominal_link100_R_nom=vg_nominal,
                V_degraded_bus384=vdeg, V_degraded_ref390=vdeg390, V_degraded_ref390_mandatory_15p1kW=vdeg390_mand,
                point_at_V_g=dict(path_A=float(x_g[0]), series_V=float(x_g[1]), modulation=float(u_g[0]),
                                  link_A=float(x_g[5]), link_power_W=float(x_g[4] * x_g[5])),
                continuous_limit_W={str(v): continuous_power_limit(float(v)) for v in [600, 615, 620, 625, 630, 640]}),
    )
    (OUT / "static_requirements.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    print(f"V_A(25 kW) {va_rows[0]['VA_25kW']:.1f}..{va_rows[-1]['VA_noload']:.1f} V; B_420 exceeded above {vbat_b420:.0f} V; "
          f"fixed-gain 48 V > 52 V above {vbat_48v:.1f} V")
    for r in va_rows:
        if r["components_violated"]: print("  ", r["vbat"], r["components_violated"])
    print(f"V_g,static={vg_static:.2f} V (path {x_g[0]:.1f} A, m={u_g[0]:.3f}), nominal-link static={vg_nominal:.2f} V, V_deg(384 V)={vdeg:.2f} V, ref 390 V: {vdeg390:.2f} V (15.1 kW: {vdeg390_mand:.2f} V)")
    for w in win:
        if w['vbat'] in (640, 800, 840, 860, 880, 900, 920):
            print("  window", w['vbat'], round(w['bus_V'], 1), round(w['series_V'], 2), round(w['link_power_W']))
    for r in reg:
        if r['vbat'] in (640, 800, 920): print("  regulated", r['vbat'], round(r['link_power_W']))


if __name__ == "__main__":
    main()
