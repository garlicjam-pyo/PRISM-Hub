"""Requirements analysis (2026-09-28), dynamic part: two-tier transient criteria for the frozen controller.

Tier 1 (load contract, docs/14 표 R-2): any step |dP| <= 10 kW inside -3.2..25 kW.
         Pass = all existing voltage checks (400+/-8 V, final +/-4 V, 1 ms recovery, ripple <= 0.1 V),
         port limits, AND path and bridge-filter current <= 90 A.
Tier 2 (contract breach / SALS failure envelope): 1->25 kW and 25->1 kW.
         Pass = completed, physical port limits, path and bridge-filter current <= 93.75 A
         (100 A rating minus worst-case switching-ripple half amplitude 6.25 A), bus inside
         384..416 V after the step, final value within +/-4 V at 20 ms.
Parameter sets: nominal and delay +3.0 us at every voltage; one-at-a-time +/-10 % tolerances,
tau 15 us, eta 0.94 at 640 and 920 V. Averaged model, Python only, not a hardware margin.
Usage: python req_dynamic.py            (full grid, 2 processes)
"""
from dataclasses import replace, asdict
from multiprocessing import Pool
from pathlib import Path
import json, sys, time
import numpy as np
from pprc_fixed_control import NOMINAL, GAIN, assess
from pprc_two_stage import simulate

OUT = Path(__file__).resolve().parents[1] / "validation" / "2026-09-28-requirements"
T1_LIMIT_A = 90.
T2_BAND = (384., 416.)
T2_LIMIT_A = 100. - 6.25          # averaged-model limit: rating minus max ripple half amplitude
DELAY_BUDGET = 3.0e-6
T1_STEPS = [(0, 10000), (5000, 15000), (10000, 20000), (15000, 25000),
            (10000, 0), (15000, 5000), (20000, 10000), (25000, 15000),
            (-3200, 6800), (6800, -3200)]
T2_STEPS = [(1000, 25000), (25000, 1000)]
V_ALL = [632, 640, 660, 700, 788, 860, 920]
V_TOL = [640, 920]


def param_sets():
    sets = {"nominal": NOMINAL, "delay+3.0us": replace(NOMINAL, delay=NOMINAL.delay + DELAY_BUDGET)}
    tol = {}
    for field in ['L', 'Cs', 'Cb', 'Lh', 'Clink', 'R', 'Rh']:
        for f in [.9, 1.1]:
            tol[f"{field}x{f}"] = replace(NOMINAL, **{field: getattr(NOMINAL, field) * f})
    tol["tau15us"] = replace(NOMINAL, tau=15e-6)
    tol["eta0.94"] = replace(NOMINAL, eta=.94)
    return sets, tol


def one(job):
    tier, name, vbat, a, b, p = job[:6]
    dt = job[6] if len(job) > 6 else (1e-7 if abs(p.delay / 2e-7 - round(p.delay / 2e-7)) > 1e-9 else 2e-7)
    try:
        r = simulate(vbat, a, b, p=p, K=GAIN, control_p=NOMINAL, duration=.02, dt=dt, keep_trace=True)
    except ValueError as e:
        return dict(tier=tier, set=name, vbat=vbat, p0=a, p1=b, error=str(e), pass_=False)
    r.update(assess(r['t'], r['x'], .001, r['completed'], r['within_port_limits']))
    t, x = r['t'], r['x']
    post = x[t >= .001, 2]
    row = dict(tier=tier, set=name, vbat=vbat, p0=a, p1=b, dt=dt, completed=r['completed'],
               path_peak=r['path_peak'], bridge_peak=r['bridge_peak'], link_peak=r['link_peak'],
               dab_power_peak=r['dab_power_peak'], droop=r['droop'], vbus_max=r['vbus_max'],
               vbus_min_post=float(post.min()), vbus_max_post=float(post.max()), vlink_min=r['vlink_min'],
               recovery_s=r['recovery_s'], checks=r['checks'],
               ports_violated=[k for k, v in r['violations'].items() if v])
    if tier == 1:
        row['pass_'] = bool(r['requirements_pass'] and r['path_peak'] <= T1_LIMIT_A and r['bridge_peak'] <= T1_LIMIT_A)
    else:
        row['pass_'] = bool(r['completed'] and r['within_port_limits'] and post.min() >= T2_BAND[0]
                            and r['path_peak'] <= T2_LIMIT_A and r['bridge_peak'] <= T2_LIMIT_A
                            and post.max() <= T2_BAND[1] and abs(x[-1, 2] - 400) <= 4)
    return row


def jobs():
    sets, tol = param_sets()
    js = []
    for v in V_ALL:
        for name, p in sets.items():
            js += [(1, name, float(v), a, b, p) for a, b in T1_STEPS]
            js += [(2, name, float(v), a, b, p) for a, b in T2_STEPS]
    for v in V_TOL:
        for name, p in tol.items():
            js += [(1, name, float(v), a, b, p) for a, b in T1_STEPS]
            js += [(2, name, float(v), a, b, p) for a, b in T2_STEPS]
    return js


def vg_dynamic(lo=622., hi=640., tol_v=.25):
    """Lowest V_bat where the nominal Tier-1 worst step (15->25 kW) passes."""
    f = lambda v: one((1, 'nominal', v, 15000, 25000, NOMINAL))['pass_']
    if not f(hi): return None
    while hi - lo > tol_v:
        mid = (lo + hi) / 2
        if f(mid): hi = mid
        else: lo = mid
    return hi


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time(); js = jobs(); print(len(js), "runs", flush=True)
    with Pool(2) as pool:
        rows = pool.map(one, js, chunksize=4)
    print("grid done %.0f s" % (time.time() - t0), flush=True)
    vg = vg_dynamic()
    summ = {}
    for tier in (1, 2):
        for name in sorted({r['set'] for r in rows}):
            sel = [r for r in rows if r['tier'] == tier and r['set'] == name]
            if not sel: continue
            fails = [r for r in sel if not r['pass_']]
            summ[f"T{tier}:{name}"] = dict(total=len(sel), passed=len(sel) - len(fails),
                                           max_path_A=max(r.get('path_peak', np.nan) for r in sel),
                                           max_bridge_A=max(r.get('bridge_peak', np.nan) for r in sel),
                                           max_droop_V=max(r.get('droop', np.nan) for r in sel),
                                           fails=[(r['vbat'], r['p0'], r['p1']) for r in fails])
    def worst(tier, sets):
        sel = [r for r in rows if r['tier'] == tier and r['set'] in sets and 'path_peak' in r]
        return max(sel, key=lambda r: max(r['path_peak'], r['bridge_peak']))
    sets, tol = param_sets()
    out = dict(scope=__doc__.strip(), controller="pprc_fixed_control.GAIN (frozen at 788 V / 5 kW)",
               tier1_limit_A=T1_LIMIT_A, tier2_limit_A=T2_LIMIT_A, tier2_band_V=T2_BAND, delay_budget_s=DELAY_BUDGET,
               V_g_dynamic_nominal=vg, summary=summ,
               worst_tier1_nominal_and_tolerance=worst(1, ['nominal'] + list(tol)),
               worst_tier2_nominal_and_tolerance=worst(2, ['nominal'] + list(tol)),
               rows=rows)
    (OUT / "dynamic_requirements.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    for k, s in summ.items():
        print(k, f"{s['passed']}/{s['total']}", f"path {s['max_path_A']:.2f} bridge {s['max_bridge_A']:.2f} droop {s['max_droop_V']:.2f}",
              s['fails'][:6])
    print("V_g,dynamic(nominal, 15->25 kW) =", vg, " total %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
