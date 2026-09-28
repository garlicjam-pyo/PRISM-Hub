"""SALS under the load-class contract of docs/14 (2026-09-28). Reduced 1 ms load model, no electrical coupling.

Classes (400 V-side power, kW):
  M0  uncontrolled, always reserved at declared maximum: Stage C input -3.2..5.3 (slew <= 4 kW/ms),
      V2L 0/3.8 (instantaneous).
  M1  mandatory with handshake: e-compressor P_c <= 6, starts only on grant, ramps up <= 0.06 kW/ms
      (0->6 kW >= 100 ms, no surge), ramps down at 0.5 kW/ms.
  D   deferrable: cabin PTC (priority 1.0) and battery heater (0.7), <= 7 each. Follow the latest
      allowance (sequence-numbered), ramp up <= 0.06 kW/ms, ramp down at exactly 0.5 kW/ms,
      watchdog 50 ms without a valid message -> allowance 0.
Messages: one-way delay U{1..5} ms; each message lost with probability p_loss.
Policies compared on identical scenarios:
  none    all loads follow their requests, compressor starts at once
  static  M0 + P_c,max always reserved, D budget constant, compressor starts at once
  sals    M0 always reserved, M1 reserved from the request, D reallocated by priority; the grant is
          issued only when a causal worst-case bound (message delay, loss, watchdog, ramp rates)
          keeps the aggregate <= budget for every future instant.
Budget B = 0.95 * 25 kW for V_bat >= V_g (voltage-dependent budget is a later task).
"""
from pathlib import Path
import json, heapq
import numpy as np

B = 0.95 * 25.0
M0_MAX = 5.3 + 3.8
SC_MIN, SC_MAX, SC_SLEW = -3.2, 5.3, 4.0
V2L_P = 3.8
PC_MAX, UP, DN = 6.0, 0.06, 0.5
D_MAX = 7.0
WD, DMAX, PERIOD = 50, 5, 10
T = 20000                     # ms per episode
OUT = Path(__file__).resolve().parents[1] / "validation" / "2026-09-28-requirements"


def scenario(rng, p_loss):
    """Exogenous processes, identical for all policies."""
    sc_target = np.empty(T); v = rng.uniform(0, 3); k = 0
    while k < T:
        dur = int(rng.exponential(500)) + 1
        sc_target[k:k + dur] = v; k += dur
        v = rng.uniform(1.5, SC_MAX) if rng.random() < .7 else rng.uniform(SC_MIN, SC_MAX)
    v2l_on = rng.random() < .6
    v2l = np.zeros(T)
    if v2l_on:
        k, state = 0, rng.random() < .5
        while k < T:
            dur = int(rng.exponential(5000)) + 1
            v2l[k:k + dur] = V2L_P if state else 0.; k += dur; state = not state
    comp = []                  # (request time, P_c, stop time)
    k = int(rng.exponential(3000))
    while k < T - 500:
        dur = int(rng.uniform(3000, 10000))
        comp.append((k, rng.uniform(3, PC_MAX), min(T - 1, k + dur)))
        k += dur + int(rng.exponential(2000)) + 200
    dreq = np.zeros((T, 2))
    for j in range(2):
        k, on = int(rng.exponential(2000)), False
        while k < T:
            dur = int(rng.uniform(4000, 16000)) if not on else int(rng.uniform(500, 3000))
            on = not on
            dreq[k:k + dur, j] = rng.uniform(4, D_MAX) if on else 0.
            k += dur
    return dict(sc_target=sc_target, v2l=v2l, comp=comp, dreq=dreq, p_loss=p_loss,
                seed=int(rng.integers(1 << 31)))


class Net:
    def __init__(self, rng, p_loss):
        self.rng, self.p, self.q, self.n = rng, p_loss, [], 0
    def send(self, now, dest, msg):
        if self.rng.random() < self.p: return
        self.n += 1
        heapq.heappush(self.q, (now + int(self.rng.integers(1, DMAX + 1)), self.n, dest, msg))
    def deliver(self, now):
        out = []
        while self.q and self.q[0][0] <= now:
            out.append(heapq.heappop(self.q)[2:])
        return out


def allocate(avail, req):
    a = np.zeros(2)
    for j in (0, 1):                               # PTC first (priority 1.0), then battery heater (0.7)
        a[j] = min(req[j], max(0., avail)); avail -= a[j]
    return a


def d_bound(t, horizon, sent, ack_seq, ack_time, sample, planned):
    """Worst-case power of one D device on [t, t+horizon) under the contract.
    sent: list of (send time, seq, allowance); ack_seq/ack_time: newest applied seq known and when it was applied;
    sample: (time, power) from the newest status; planned: allowance SALS will send from t on."""
    lo = t - 80
    tau = np.arange(lo, t + horizon)
    amax = np.zeros(len(tau))
    msgs = [m for m in sent if m[0] >= lo - DMAX - WD] + [(s, 1 << 60, planned) for s in range(t, t + horizon)]
    for s, seq, a in msgs:
        # an allowance sent at s can be in effect only on [s+1, s+DMAX+WD]; once a newer seq is known applied it is superseded
        i0, i1 = s + 1 - lo, s + DMAX + WD - lo + 1
        if seq < ack_seq: i1 = min(i1, ack_time - lo)
        if i1 > i0: amax[max(i0, 0):max(i1, 0)] = np.maximum(amax[max(i0, 0):max(i1, 0)], a)
    env = np.empty(len(tau)); cur = 0.
    for i in range(len(tau)):                       # power <= allowance envelope with ramp-down 0.5 kW/ms
        cur = max(amax[i], cur - DN); env[i] = cur
    ts, ps = sample
    up = ps + UP * np.maximum(tau - ts, 0)
    return np.minimum(env, up)[t - lo:]


def run(scn, policy):
    rng = np.random.default_rng(scn['seed'])
    net = Net(rng, scn['p_loss'] if policy == 'sals' else 0.)
    sc = 0.; comp_p = 0.; pc = 0.; cstate = 'off'; creq_t = cstop_t = None; rid = 0
    ci, comp_events = 0, scn['comp']
    dp = np.zeros(2); d_allow = np.zeros(2); d_seq = np.zeros(2, int) - 1; d_rx = np.full(2, -10 ** 9)
    # SALS state
    req_known = np.zeros(2); comp_known = None; comp_ts = -1; granted = None
    sent = [[], []]; seq = 0; ack = [(-1, -10 ** 9), (-1, -10 ** 9)]; samp = [(0, 0.), (0, 0.)]
    last_alloc = np.zeros(2)
    L = np.empty(T); unmet = np.zeros(2); req_sum = np.zeros(2)
    latencies, d_delays = [], []; pending_d = [None, None]; checks = 0
    static_alloc = allocate(B - M0_MAX - PC_MAX, np.array([D_MAX, D_MAX]))

    def safe(t, plan, comp_from):
        """Worst-case aggregate stays <= B on the horizon if SALS sends `plan` from now on.
        comp_from: None (compressor cannot run), 'full' (granted, may be at P_c), or an int grant time (ramp)."""
        H = 160
        tot = M0_MAX + sum(d_bound(t, H, sent[j], ack[j][0], ack[j][1], samp[j], plan[j]) for j in (0, 1))
        if comp_from == 'full': tot = tot + comp_known[1]
        elif comp_from is not None: tot = tot + np.minimum(comp_known[1], UP * np.arange(H))
        return bool(np.all(tot <= B + 1e-9))

    for t in range(T):
        sc += np.clip(scn['sc_target'][t] - sc, -SC_SLEW, SC_SLEW)
        v2l = scn['v2l'][t]
        # ---- compressor request / stop
        if ci < len(comp_events) and cstate == 'off' and t >= comp_events[ci][0]:
            creq_t, pc, cstop_t = comp_events[ci]; ci += 1; rid += 1
            if policy == 'sals': cstate = 'waiting'; net.send(t, 'sals', ('cstat', t, rid, cstate, pc))
            else: cstate = 'ramp'; latencies.append(0)
        if cstate in ('ramp', 'run', 'waiting') and t >= cstop_t:
            if cstate == 'waiting': latencies.append(None)
            cstate = 'down'
        # ---- deliveries
        for dest, msg in net.deliver(t):
            kind = msg[0]
            if dest == 'sals':
                if kind == 'cstat':
                    _, ts, r, st, p_c = msg
                    if ts > comp_ts:
                        comp_ts = ts
                        if st == 'off':
                            if comp_known is not None and r == comp_known[0]: comp_known = None; granted = None
                        elif comp_known is None or r != comp_known[0]:
                            comp_known = (r, p_c); granted = None
                elif kind == 'dstat':
                    _, j, a_seq, a_t, ts, p, q = msg
                    req_known[j] = q
                    if a_seq > ack[j][0]: ack[j] = (a_seq, a_t)
                    if ts > samp[j][0]: samp[j] = (ts, p)
            elif dest == 'comp':
                if cstate == 'waiting' and msg[1] == rid:
                    cstate = 'ramp'; latencies.append(t - creq_t)
            else:
                j = int(dest[1]); _, s, a = msg
                if s > d_seq[j]:
                    d_seq[j], d_allow[j], d_rx[j] = s, a, t
                    net.send(t, 'sals', ('dstat', j, s, t, t, dp[j], scn['dreq'][t, j]))
        # ---- compressor device (periodic status)
        if cstate in ('ramp', 'run'): comp_p = min(pc, comp_p + UP)
        elif cstate == 'down':
            comp_p = max(0., comp_p - DN)
            if comp_p == 0.: cstate = 'off'
        if policy == 'sals' and t % PERIOD == 0:
            net.send(t, 'sals', ('cstat', t, rid, cstate, pc))
        # ---- D devices
        q = scn['dreq'][t]
        for j in (0, 1):
            if policy == 'none': allow = q[j]
            elif policy == 'static': allow = min(q[j], static_alloc[j])
            else: allow = min(q[j], d_allow[j] if t - d_rx[j] <= WD else 0.)
            dp[j] = min(dp[j] + UP, allow) if allow > dp[j] else max(allow, dp[j] - DN)
            if policy == 'sals' and t % PERIOD == 0:
                net.send(t, 'sals', ('dstat', j, d_seq[j], d_rx[j], t, dp[j], q[j]))
            if q[j] > 0 and pending_d[j] is None and (t == 0 or scn['dreq'][t - 1, j] == 0):
                c = pc if cstate != 'off' else 0.
                room = B - M0_MAX - c - (q[0] if j == 1 else 0.)
                pending_d[j] = (t, room >= 0.5)
            if pending_d[j] is not None and allow > 0:
                d_delays.append((j, t - pending_d[j][0], pending_d[j][1])); pending_d[j] = None
            if q[j] == 0: pending_d[j] = None
        # ---- SALS
        if policy == 'sals':
            r_m1 = comp_known[1] if comp_known is not None else 0.
            plan = allocate(B - M0_MAX - r_m1, req_known)
            comp_mode = None if comp_known is None else ('full' if granted is not None else None)
            # decreases immediately; increases only if the causal worst-case check passes (every 10 ms)
            new = np.minimum(plan, last_alloc)
            if np.any(plan > last_alloc + 1e-12) and t % PERIOD == 0:
                checks += 1
                if safe(t, plan, comp_mode): new = plan
            for j in (0, 1):
                if new[j] != last_alloc[j] or t % PERIOD == 0:
                    seq += 1; sent[j].append((t, seq, new[j])); net.send(t, f'd{j}', ('allow', seq, new[j]))
                    last_alloc[j] = new[j]
                if t % 50 == 0: sent[j] = [m for m in sent[j] if m[0] >= t - 200]
            if comp_known is not None and granted is None:
                checks += 1
                if safe(t, last_alloc, t): granted = t
            if comp_known is not None and granted is not None and (granted == t or t % PERIOD == 0):
                net.send(t, 'comp', ('grant', comp_known[0]))
        L[t] = sc + v2l + comp_p + dp.sum()
        unmet += np.maximum(q - dp, 0); req_sum += q
    step = np.diff(L)
    return dict(exceed_ms=int(np.sum(L > B + 1e-9)), over25_ms=int(np.sum(L > 25 + 1e-9)), peak=float(L.max()),
                step_up=float(step.max()), step_dn=float(-step.min()), checks=checks,
                latency=[l for l in latencies if l is not None], never_started=sum(l is None for l in latencies),
                d_delay=d_delays, unmet=(unmet / 1000).tolist(), req=(req_sum / 1000).tolist())   # kW*s


def main(N=200):
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260928)
    res = {k: [] for k in ('none', 'static', 'sals')}; meta = []
    for i in range(N):
        p_loss = 0. if i % 2 == 0 else float(rng.uniform(0, .2))
        scn = scenario(rng, p_loss); meta.append(p_loss)
        for pol in res: res[pol].append(run(scn, pol))
        if i % 20 == 0: print(i, flush=True)
    summ = {}
    for pol, rows in res.items():
        lat0 = [l for r, pl in zip(rows, meta) if pl == 0 for l in r['latency']]
        lat1 = [l for r, pl in zip(rows, meta) if pl > 0 for l in r['latency']]
        dd = [d for r in rows for _, d, ok in r['d_delay'] if ok]
        un = np.sum([r['unmet'] for r in rows], axis=0); rq = np.sum([r['req'] for r in rows], axis=0)
        summ[pol] = dict(episodes=len(rows), episodes_exceeding_budget=sum(r['exceed_ms'] > 0 for r in rows),
                         budget_exceed_ms_total=sum(r['exceed_ms'] for r in rows),
                         episodes_over_25kW=sum(r['over25_ms'] > 0 for r in rows),
                         peak_kW=max(r['peak'] for r in rows),
                         max_step_up_kW=max(r['step_up'] for r in rows), max_step_down_kW=max(r['step_dn'] for r in rows),
                         compressor_starts=len(lat0) + len(lat1), compressor_requests_never_started=sum(r['never_started'] for r in rows),
                         grant_latency_ms_noloss=dict(median=float(np.median(lat0)), p99=float(np.percentile(lat0, 99)), max=int(max(lat0))) if lat0 else None,
                         grant_latency_ms_loss=dict(median=float(np.median(lat1)), p99=float(np.percentile(lat1, 99)), max=int(max(lat1))) if lat1 else None,
                         d_start_delay_ms_when_budget_available=dict(median=float(np.median(dd)), p99=float(np.percentile(dd, 99)), max=int(max(dd))) if dd else None,
                         d_unmet_fraction=dict(PTC=float(un[0] / rq[0]), BH=float(un[1] / rq[1]), total=float(un.sum() / rq.sum())))
    out = dict(scope=__doc__.strip(), N=N, budget_kW=B, m0_reserve_kW=M0_MAX, summary=summ)
    (OUT / "sals_contract.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    import sys
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
