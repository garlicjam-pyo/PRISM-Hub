"""Design exploration behind controller R1 (2026-09-29): the alternatives that were rejected.

1) Frozen controller structure, pole-placement bandwidth / fastest pole scan: linear added-delay margin.
2) Lower bandwidth (2.5 and 3.0 kHz) in nonlinear simulation: droop, path current, collapse under L_h -10 %.
3) Bus-voltage proportional gain scaled by alpha (frozen gain + prediction): spectral radius -> instability below ~0.35-0.5.
4) Hard deviation limit E on the voltage term (frozen gain + prediction): Tier-2 1->25 kW path current at 640 V
   (reduced), and 25->1 kW (limit cycle at E = 1.5 V).
5) Delay-limited mode of the frozen controller: frequency and eigenvector composition at +1.5 us.
6) Frozen controller, one-at-a-time tolerance sets: linear spectral radius at nominal delay (no hidden oscillation).
Averaged model, Python only.
"""
from dataclasses import replace
from pathlib import Path
import itertools, json
import numpy as np
from pprc_fixed_control import NOMINAL, GAIN, assess
from pprc_two_stage import simulate
from ctrl_redesign import StageBController, design_poles
from ctrl_linear import delay_margin, rho_ctrl, jacobian

OUT = Path(__file__).resolve().parents[1] / "validation" / "2026-09-29-controller"


def run(v, a, b, p, K, cp, **opt):
    c = StageBController(K, cp, v, **opt)
    r = simulate(v, a, b, p=p, K=K, control_p=cp, duration=.02, dt=2e-7, keep_trace=True, controller=c)
    r.update(assess(r['t'], r['x'], .001, r['completed'], r['within_port_limits']))
    return dict(path_peak=r['path_peak'], droop=r['droop'], completed=r['completed'], tail_ripple_V=r['tail_ripple_V'],
                requirements_pass=r['requirements_pass'], failed=[k for k, c in r['checks'].items() if not c])


def main():
    out = {}
    # 1
    scan = []
    for bw, a3 in itertools.product([2.5e3, 3.0e3, 3.5e3, 4.0e3, 4.8e3], [1.5, 2.5]):
        cp = replace(NOMINAL, bus_bw=bw); K = design_poles(788, 5000, cp, a=(1., 1 / 3, a3))
        dm = min(delay_margin(v, 25000, NOMINAL, cp, K, hi=8e-6, tol=1e-7) for v in (640, 920))
        scan.append(dict(bus_bw=bw, fastest_pole=a3, delay_margin_us=round(dm * 1e6, 2)))
    out['bandwidth_scan_frozen_structure'] = scan
    # 2
    low = []
    for bw, a3 in [(3.0e3, 1.5), (2.5e3, 2.5)]:
        cp = replace(NOMINAL, bus_bw=bw); K = design_poles(788, 5000, cp, a=(1., 1 / 3, a3))
        for name, p in [('nominal', NOMINAL), ('Lhx0.9', replace(NOMINAL, Lh=NOMINAL.Lh * .9))]:
            for a, b in [(15000, 25000), (1000, 25000)]:
                low.append(dict(bus_bw=bw, fastest_pole=a3, plant=name, p0=a, p1=b, **run(640., a, b, p, K, cp)))
    out['low_bandwidth_nonlinear_640V'] = low
    # 3
    K = np.array(GAIN); alpha = []
    for al in [1., .75, .5, .35, .25, 0.]:
        Ka = K.copy(); Ka[2] *= al
        r = max(rho_ctrl(v, P, NOMINAL, lambda vb: StageBController(Ka, NOMINAL, vb, predict=True))[0]
                for v in (640., 920.) for P in (1000., 25000.))
        alpha.append(dict(alpha=al, max_spectral_radius=r))
    out['voltage_gain_scaling_with_prediction'] = alpha
    # 4
    out['hard_voltage_limit'] = dict(gain='frozen GAIN with prediction',
        load_step_1_to_25kW=[dict(E=E, **run(640., 1000, 25000, NOMINAL, K, NOMINAL, predict=True, vdev_limit=E)) for E in (None, 3.0, 2.0)],
        unload_25_to_1kW=[dict(E=E, **run(640., 25000, 1000, NOMINAL, K, NOMINAL, predict=True, vdev_limit=E)) for E in (2.0, 1.5)])
    # 5
    J, _ = jacobian(640, 25000, replace(NOMINAL, delay=6.5e-6), NOMINAL, K)
    lam, V = np.linalg.eig(J); i = int(np.argmax(abs(lam))); v = V[:, i]
    names = ['i_p', 'v_s', 'v_bus', 'i_h', 'v_link', 'i_dab', 'q', 'q_link', 'm(k-1)', 'i_link(k-1)', 'm(k-2)', 'i_link(k-2)', 'm(k-3)', 'i_link(k-3)', 'm(k-4)', 'i_link(k-4)']
    scale = np.array([10, 10, 1, 10, 1, 10, 1e-3, 1e-3, .1, 10, .1, 10, .1, 10, .1, 10]); w = abs(v) / scale; w /= w.max()
    out['delay_limited_mode'] = dict(delay_s=6.5e-6, spectral_radius=float(abs(lam[i])), frequency_hz=float(abs(np.angle(lam[i])) / (2 * np.pi * 5e-6)),
                                     normalized_participation=dict(sorted(zip(names, map(float, w)), key=lambda t: -t[1])[:6]))
    # 6
    tol = []
    for f in ['L', 'Cs', 'Cb', 'Lh', 'Clink', 'R', 'Rh']:
        for k in (.9, 1.1):
            tol.append(replace(NOMINAL, **{f: getattr(NOMINAL, f) * k}))
    tol += [replace(NOMINAL, tau=15e-6), replace(NOMINAL, eta=.94)]
    rmax = max(rho_ctrl(v, P, p, lambda vb: StageBController(K, NOMINAL, vb))[0] for p in tol for v in (640., 920.) for P in (1000., 25000.))
    out['frozen_tolerance_linear_check'] = dict(sets=len(tol), max_spectral_radius=rmax)
    out['scope'] = __doc__.strip()
    (OUT / "exploration.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != 'scope'}, indent=1, default=float)[:4000])


if __name__ == "__main__":
    main()
