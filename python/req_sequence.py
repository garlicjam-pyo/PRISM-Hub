"""Worst load sequences allowed by the class contract (docs/14 표 R-2), checked against Tier-1 (2026-09-28).

The Tier-1 single step (10 kW) is a surrogate. This script applies the actual worst contract sequences
over several milliseconds, as continuous ramps and as 1 ms staircases:
  up   : 12.7 -> 25 kW  (V2L +3.8 kW step, Stage C -3.2 -> +5.3 kW at 4 kW/ms, compressor/D +0.06 kW/ms)
  down : 25 -> -3.2 kW  (V2L -3.8 kW step, Stage C +5.3 -> -3.2 kW at 4 kW/ms, compressor and D -0.5 kW/ms each)
Tier-1 pass = all voltage checks, port limits, path and bridge-filter current <= 90 A.
"""
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path
import json
import numpy as np
from pprc_fixed_control import NOMINAL, GAIN, assess
from pprc_two_stage import simulate
from req_dynamic import OUT, T1_LIMIT_A

T0 = 1e-3


def seq_up(discrete):
    def f(t):
        if t < T0: return 12700.
        s = (t - T0) * 1e3                                  # ms since start
        sc = min(8500., (np.floor(s) + 1) * 4000. if discrete else s * 4000.)
        slow = 60. * s * 3                                  # compressor + 2 D devices, <= 0.06 kW/ms each
        return min(25000., 12700. + 3800. + sc + slow)
    return f


def seq_down(discrete):
    def f(t):
        if t < T0: return 25000.
        s = (t - T0) * 1e3
        sc = min(8500., (np.floor(s) + 1) * 4000. if discrete else s * 4000.)
        comp = min(6000., 500. * s); ptc = min(7000., 500. * s); bh = min(2900., 500. * s)
        return max(-3200., 25000. - 3800. - sc - comp - ptc - bh)
    return f


def job(args):
    v, pname, p, name, fn = args
    f = {'up_ramp': seq_up(False), 'up_stair': seq_up(True), 'down_ramp': seq_down(False), 'down_stair': seq_down(True)}[fn]
    p0 = f(0.)
    r = simulate(v, p0, p0, p=p, K=GAIN, control_p=NOMINAL, duration=.02, dt=2e-7, keep_trace=True, power_fn=f)
    r.update(assess(r['t'], r['x'], T0, r['completed'], r['within_port_limits']))
    ok = bool(r['requirements_pass'] and r['path_peak'] <= T1_LIMIT_A and r['bridge_peak'] <= T1_LIMIT_A)
    return dict(vbat=v, set=pname, sequence=fn, pass_=ok, path_peak=r['path_peak'], bridge_peak=r['bridge_peak'],
                droop=r['droop'], vbus_max=r['vbus_max'], recovery_s=r['recovery_s'],
                failed=[k for k, c in r['checks'].items() if not c], dab_power_peak=r['dab_power_peak'])


if __name__ == "__main__":
    sets = {'nominal': NOMINAL, 'Lhx0.9': replace(NOMINAL, Lh=NOMINAL.Lh * .9), 'Lx1.1': replace(NOMINAL, L=NOMINAL.L * 1.1)}
    js = [(v, n, p, None, fn) for v in (632., 640., 920.) for n, p in sets.items()
          for fn in ('up_ramp', 'up_stair', 'down_ramp', 'down_stair')]
    with Pool(2) as pool:
        rows = pool.map(job, js)
    out = dict(scope=__doc__.strip(), rows=rows, passed=sum(r['pass_'] for r in rows), total=len(rows),
               worst=max(rows, key=lambda r: max(r['path_peak'], r['bridge_peak'])))
    (OUT / "contract_sequences.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    for r in rows: print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
    print(out['passed'], '/', out['total'])
