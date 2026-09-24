"""Supplementary analyses for the final interim report (2026-09-25).

1) Steady-state Stage B balance over 640-920 V at 25 kW (finite-link averaged model).
2) Transient (20 ms) power capability from a 5 kW base with the frozen controller:
   largest final power that satisfies every requirement check (bisection, 0.25 kW).
3) 640 V corner margins of the rated 1->25 kW test.
Python only; MATLAB cross-check pending. Not a hardware or firmware margin.
"""
from pathlib import Path
import json, time
import numpy as np
from pprc_two_stage import Parameters, equilibrium, steady_feasible, continuous_power_limit
from pprc_fixed_control import run, NOMINAL

OUT = Path(__file__).resolve().parents[1] / "validation" / "2026-09-25-final-report"
OUT.mkdir(parents=True, exist_ok=True)

def steady_sweep(p=NOMINAL, power=25000.):
    rows=[]
    for vbat in range(640, 921, 10):
        x,u=equilibrium(float(vbat), power, p)
        plink=x[4]*x[5]
        rows.append(dict(vbat=vbat, path_A=x[0], series_V=x[1], link_A=x[5], link_power_W=plink,
                         bus_side_dab_W=(plink/p.eta if plink>=0 else plink*p.eta),
                         processed_ratio=abs(plink)/power, modulation=u[0],
                         feasible_with_reserve=steady_feasible(float(vbat),power,p,True),
                         continuous_limit_W=continuous_power_limit(float(vbat),p)))
    return rows

def capability(vbat, power0=5000., lo=20000., hi=40000., tol=250.):
    """largest power1 in [lo,hi] with requirements_pass (assumes monotone pass/fail)."""
    r=run(vbat,power0,lo)
    if not r["requirements_pass"]: return dict(vbat=vbat, power0=power0, max_power1_W=None, note="fails at lower bound")
    r=run(vbat,power0,hi)
    if r["requirements_pass"]: return dict(vbat=vbat, power0=power0, max_power1_W=hi, note="passes at upper bound")
    fail=None
    while hi-lo>tol:
        mid=(lo+hi)/2; r=run(vbat,power0,mid)
        if r["requirements_pass"]: lo=mid
        else: hi=mid; fail=r
    first=run(vbat,power0,hi)
    return dict(vbat=vbat, power0=power0, max_power1_W=lo, first_fail_power1_W=hi,
                first_fail_checks=[k for k,v in first["checks"].items() if not v],
                first_fail_ports=[k for k,v in first["violations"].items() if v],
                path_peak_at_max_A=run(vbat,power0,lo)["path_peak"])

def corner(vbat=640.):
    r=run(vbat,1000.,25000.)
    p=NOMINAL
    series_limit_low_link = p.modulation_max*90.0 - p.Rh*79.3   # link at 90 V, bridge drop at ~79 A
    return dict(vbat=vbat, path=(r["path_peak"],p.path_max), bridge=(r["bridge_peak"],p.path_max),
                link_current=(r["link_peak"],p.link_max), dab_power=(r["dab_power_peak"],p.power_max),
                modulation=(r["modulation_peak"],p.modulation_max), series=(r["series_peak"],p.series_max),
                series_limit_at_90V_link=series_limit_low_link, vlink_min=r["vlink_min"], droop=r["droop"],
                recovery_s=r["recovery_s"])

VOLTAGES=[640,660,680,700,720,740,760,788,820,860,900,920]
if __name__=="__main__":
    import sys
    t0=time.time(); part=OUT/"capability_parts.json"
    parts=json.load(open(part)) if part.exists() else {}
    todo=[int(a) for a in sys.argv[1:]] if len(sys.argv)>1 else [v for v in VOLTAGES if str(v) not in parts]
    for v in todo:
        c=capability(float(v)); parts[str(v)]=c; json.dump(parts,open(part,"w"),indent=1,default=float)
        print(v, c.get("max_power1_W"), c.get("first_fail_checks"), c.get("first_fail_ports"), "%.0f s"%(time.time()-t0), flush=True)
    if all(str(v) in parts for v in VOLTAGES):
        out=dict(scope=__doc__.strip(), controller="pprc_fixed_control.GAIN (frozen at 788 V / 5 kW)")
        out["steady_25kW"]=steady_sweep(); out["corner_640V"]=corner()
        out["transient_capability_from_5kW"]=[parts[str(v)] for v in VOLTAGES]
        json.dump(out, open(OUT/"report_analysis.json","w"), indent=1, default=float)
        print("saved", OUT/"report_analysis.json")
