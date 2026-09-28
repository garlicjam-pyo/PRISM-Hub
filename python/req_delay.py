"""Tier-1 delay boundary of the frozen controller (2026-09-28).

Transport delay swept above the nominal 5 us for three representative Tier-1 steps (15->25, 25->15,
0->10 kW), nominal plant parameters only, at 640 and 920 V (dt 0.1 us, as in sweep_fixed_control_delay.py). Compared with the delay budget of docs/14 (+3.0 us).
"""
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path
import json
from pprc_fixed_control import NOMINAL
from req_dynamic import one, OUT

DELAYS_US = [5.8, 6.0, 6.2, 6.3, 6.4, 6.5, 6.6, 7.0, 8.0]
STEPS = [(15000, 25000), (25000, 15000), (0, 10000)]


def job(args):
    v, d, a, b = args
    r = one((1, f"delay{d}", float(v), a, b, replace(NOMINAL, delay=round(d * 10) * 1e-7), 1e-7))
    return dict(vbat=v, delay_us=d, p0=a, p1=b, pass_=r['pass_'], path=r.get('path_peak'),
                bridge=r.get('bridge_peak'), failed=[k for k, ok in r.get('checks', {}).items() if not ok])


if __name__ == "__main__":
    js = [(v, d, a, b) for v in (640, 920) for d in DELAYS_US for a, b in STEPS]
    with Pool(2) as p:
        rows = p.map(job, js)
    bound = {}
    for v in (640, 920):
        ok = [d for d in DELAYS_US if all(r['pass_'] for r in rows if r['vbat'] == v and r['delay_us'] == d)]
        bad = [d for d in DELAYS_US if d not in ok]
        bound[str(v)] = dict(last_pass_us=max([d for d in ok if not bad or d < min(bad)], default=None),
                             first_fail_us=min(bad, default=None))
    out = dict(scope=__doc__.strip(), nominal_delay_us=NOMINAL.delay * 1e6, budget_added_us=3.0, boundary=bound, rows=rows)
    (OUT / "delay_tier1.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    for r in rows: print(r)
    print(bound)
