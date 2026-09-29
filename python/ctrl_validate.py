"""Validation of the redesigned Stage B controller (R1) against docs/14 acceptance criteria (2026-09-29).

R1 = same state-feedback + integral structure and inner current law as the frozen controller, with
  (1) one-sample prediction of [i_p, v_s, i_h] using the nominal model and the previous command,
  (2) dominant pole damping 0.7 -> 0.95 (bus_bw 4.8 kHz, other poles unchanged), design point 788 V / 5 kW.
Parts (run individually: python ctrl_validate.py grid|delay|corners|sequences|linear|corners_lh5|all):
  grid      Tier-1/Tier-2 grid identical to req_dynamic.py (552 runs)
  delay     Tier-1 added-delay boundary, 640/920 V, 3 representative steps, dt 0.1 us
  corners   all 128 combined +/-10 % corners of [L, Cs, Cb, Lh, Clink, R, Rh] at 640 V:
            Tier-1 15->25 kW with +3.0 us delay and Tier-2 1->25 kW at nominal delay
  sequences worst contract load sequences (req_sequence.py) with R1
  linear    sampled-data delay margin map (ctrl_linear.py) over V_bat and load
  corners_lh5  Tier-2 corners that failed, re-run with L_h tolerance +/-5 % (others +/-10 %)
Judge = docs/14 Tier criteria plus an internal-oscillation check (last 1 ms: i_h peak-to-peak <= 1 A and
modulation peak-to-peak <= 0.01), because a sustained bridge-current oscillation can leave the bus ripple
below 0.1 V. Averaged model, Python only. Not a hardware or firmware margin.
"""
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path
import itertools, json, sys, time
import numpy as np
from pprc_fixed_control import NOMINAL, GAIN, assess
from pprc_two_stage import simulate
from ctrl_redesign import StageBController, design_poles
from ctrl_linear import delay_margin_ctrl, rho_ctrl
import req_dynamic as rd
import req_sequence as rs

OUT = Path(__file__).resolve().parents[1] / "validation" / "2026-09-29-controller"
CP = replace(NOMINAL, bus_bw=4800.)
ZETA, POLES = .95, (1., 1 / 3, 2.5)
K_R1 = design_poles(788, 5000, CP, z=ZETA, a=POLES)
FIELDS = ['L', 'Cs', 'Cb', 'Lh', 'Clink', 'R', 'Rh']


def make(vbat, kind='R1'):
    if kind == 'frozen': return StageBController(np.array(GAIN), NOMINAL, vbat)
    return StageBController(K_R1, CP, vbat, predict=True)


def sim(vbat, a, b, p, dt=None, kind='R1', power_fn=None):
    if dt is None:
        dt = 1e-7 if abs(p.delay / 2e-7 - round(p.delay / 2e-7)) > 1e-9 else 2e-7
    c = make(vbat, kind)
    r = simulate(vbat, a, b, p=p, K=K_R1, control_p=CP, duration=.02, dt=dt, keep_trace=True,
                 controller=c, power_fn=power_fn)
    r.update(assess(r['t'], r['x'], .001, r['completed'], r['within_port_limits']))
    return r


TAIL_IH_PP_A, TAIL_M_PP = 1.0, .01   # internal-oscillation check (averaged model: steady state is constant)


def judge(tier, r):
    post = r['x'][r['t'] >= .001, 2]
    tail = r['t'] >= r['t'][-1] - .001
    ih_pp = float(np.ptp(r['x'][tail, 3])); m_pp = float(np.ptp(r['u'][tail, 0]))
    internal_ok = bool(ih_pp <= TAIL_IH_PP_A and m_pp <= TAIL_M_PP)
    row = dict(path_peak=r['path_peak'], bridge_peak=r['bridge_peak'], link_peak=r['link_peak'],
               dab_power_peak=r['dab_power_peak'], droop=r['droop'], vbus_min_post=float(post.min()),
               vbus_max_post=float(post.max()), recovery_s=r['recovery_s'], tail_ripple_V=r['tail_ripple_V'],
               modulation_peak=r['modulation_peak'], vlink_min=r['vlink_min'],
               tail_ih_pp_A=ih_pp, tail_m_pp=m_pp,
               failed=[k for k, c in r['checks'].items() if not c] + ([] if internal_ok else ['internal_tail_oscillation']),
               ports_violated=[k for k, v in r['violations'].items() if v])
    if tier == 1:
        row['pass_'] = bool(r['requirements_pass'] and internal_ok and r['path_peak'] <= rd.T1_LIMIT_A and r['bridge_peak'] <= rd.T1_LIMIT_A)
    else:
        row['pass_'] = bool(r['completed'] and r['within_port_limits'] and post.min() >= rd.T2_BAND[0]
                            and post.max() <= rd.T2_BAND[1] and abs(r['x'][-1, 2] - 400) <= 4
                            and r['path_peak'] <= rd.T2_LIMIT_A and r['bridge_peak'] <= rd.T2_LIMIT_A and internal_ok)
    return row


def grid_job(job):
    tier, name, v, a, b, p = job
    row = dict(tier=tier, set=name, vbat=v, p0=a, p1=b)
    row.update(judge(tier, sim(v, a, b, p)))
    return row


def part_grid():
    rows = Pool(2).map(grid_job, rd.jobs(), chunksize=4)
    summ = {}
    for tier in (1, 2):
        for name in sorted({r['set'] for r in rows}):
            sel = [r for r in rows if r['tier'] == tier and r['set'] == name]
            summ[f"T{tier}:{name}"] = dict(total=len(sel), passed=sum(r['pass_'] for r in sel),
                                           max_path_A=max(r['path_peak'] for r in sel),
                                           max_bridge_A=max(r['bridge_peak'] for r in sel),
                                           max_droop_V=max(r['droop'] for r in sel),
                                           fails=[(r['vbat'], r['p0'], r['p1'], r['failed']) for r in sel if not r['pass_']])
    return dict(summary=summ, rows=rows)


def delay_job(args):
    v, extra, a, b = args
    p = replace(NOMINAL, delay=round((NOMINAL.delay + extra * 1e-6) / 1e-7) * 1e-7)
    row = dict(vbat=v, added_us=extra, p0=a, p1=b)
    row.update(judge(1, sim(v, a, b, p, dt=1e-7)))
    return row


def part_delay():
    extras = [3.0, 3.5, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3, 4.5, 5.0]
    js = [(v, e, a, b) for v in (640, 920) for e in extras for a, b in [(15000, 25000), (25000, 15000), (0, 10000)]]
    rows = Pool(2).map(delay_job, js)
    bound = {}
    for v in (640, 920):
        ok = [e for e in extras if all(r['pass_'] for r in rows if r['vbat'] == v and r['added_us'] == e)]
        bad = [e for e in extras if e not in ok]
        bound[str(v)] = dict(last_pass_added_us=max([e for e in ok if not bad or e < min(bad)], default=None),
                             first_fail_added_us=min(bad, default=None))
    return dict(boundary=bound, rows=rows)


def corner_job(args):
    signs, tier = args
    extra = 3e-6 if tier == 1 else 0.
    p = replace(NOMINAL, delay=NOMINAL.delay + extra, **{f: getattr(NOMINAL, f) * (1 + .1 * s) for f, s in zip(FIELDS, signs)})
    a, b = (15000, 25000) if tier == 1 else (1000, 25000)
    row = dict(signs=signs, tier=tier, vbat=640, p0=a, p1=b, added_delay_us=extra * 1e6)
    row.update(judge(tier, sim(640., a, b, p)))
    return row


def part_corners():
    js = [(s, t) for s in itertools.product([-1, 1], repeat=7) for t in (1, 2)]
    rows = Pool(2).map(corner_job, js, chunksize=4)
    out = {}
    for t in (1, 2):
        sel = [r for r in rows if r['tier'] == t]
        w = max(sel, key=lambda r: max(r['path_peak'], r['bridge_peak']))
        out[f"T{t}"] = dict(total=len(sel), passed=sum(r['pass_'] for r in sel), worst=w)
    return dict(summary=out, rows=rows)


def seq_job(args):
    v, pname, p, fn = args
    f = {'up_ramp': rs.seq_up(False), 'up_stair': rs.seq_up(True), 'down_ramp': rs.seq_down(False), 'down_stair': rs.seq_down(True)}[fn]
    p0 = f(0.)
    row = dict(vbat=v, set=pname, sequence=fn)
    row.update(judge(1, sim(v, p0, p0, p, power_fn=f)))
    return row


def part_sequences():
    sets = {'nominal': NOMINAL, 'Lhx0.9': replace(NOMINAL, Lh=NOMINAL.Lh * .9), 'Lx1.1': replace(NOMINAL, L=NOMINAL.L * 1.1),
            'delay+3.0us': replace(NOMINAL, delay=NOMINAL.delay + 3e-6)}
    js = [(v, n, p, fn) for v in (632., 640., 920.) for n, p in sets.items() for fn in ('up_ramp', 'up_stair', 'down_ramp', 'down_stair')]
    rows = Pool(2).map(seq_job, js)
    return dict(passed=sum(r['pass_'] for r in rows), total=len(rows),
                worst=max(rows, key=lambda r: max(r['path_peak'], r['bridge_peak'])), rows=rows)


def lin_job(args):
    v, P, kind = args
    mk = (lambda vb: make(vb, kind))
    dm = delay_margin_ctrl(v, P, NOMINAL, mk)
    r0, f0 = rho_ctrl(v, P, NOMINAL, mk)
    r3, f3 = rho_ctrl(v, P, replace(NOMINAL, delay=NOMINAL.delay + 3e-6), mk)
    return dict(vbat=v, power=P, controller=kind, delay_margin_us=dm * 1e6, rho_nominal=r0, mode_hz_nominal=f0,
                rho_plus3us=r3, mode_hz_plus3us=f3)


def part_linear():
    js = [(v, P, k) for k in ('frozen', 'R1') for v in (632., 640., 700., 788., 860., 920.) for P in (-3200., 0., 10000., 25000.)]
    rows = Pool(2).map(lin_job, js)
    return dict(rows=rows, min_margin_us={k: min(r['delay_margin_us'] for r in rows if r['controller'] == k) for k in ('frozen', 'R1')})


def lh5_job(signs):
    tol = {f: (.05 if f == 'Lh' else .1) for f in FIELDS}
    p = replace(NOMINAL, **{f: getattr(NOMINAL, f) * (1 + tol[f] * sg) for f, sg in zip(FIELDS, signs)})
    row = dict(signs=signs, tier=2, vbat=640, p0=1000, p1=25000)
    row.update(judge(2, sim(640., 1000, 25000, p)))
    return row


def part_corners_lh5():
    """Tier-2 corners that failed in part_corners, re-run with the bridge-filter inductor tolerance tightened to +/-5 %."""
    prev = json.loads((OUT / "corners.json").read_text(encoding="utf-8"))
    fails = [tuple(r['signs']) for r in prev['rows'] if r['tier'] == 2 and not r['pass_']]
    rows = Pool(2).map(lh5_job, fails)
    return dict(passed=sum(r['pass_'] for r in rows), total=len(rows),
                max_path_A=max(r['path_peak'] for r in rows), rows=rows)


PARTS = dict(grid=part_grid, delay=part_delay, corners=part_corners, sequences=part_sequences, linear=part_linear, corners_lh5=part_corners_lh5)

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    todo = sys.argv[1:] or ['all']
    if todo == ['all']: todo = list(PARTS)
    for name in todo:
        t0 = time.time()
        res = PARTS[name]()
        res.update(scope=__doc__.strip(), controller=dict(K=K_R1.tolist(), bus_bw=CP.bus_bw, zeta=ZETA, poles=POLES,
                                                         prediction='one sample, [i_p, v_s, i_h], nominal model',
                                                         design_point=[788, 5000]))
        (OUT / f"{name}.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
        brief = {k: v for k, v in res.items() if k in ('summary', 'boundary', 'passed', 'total', 'min_margin_us')}
        print(name, "%.0f s" % (time.time() - t0), json.dumps(brief, default=float)[:3000], flush=True)
