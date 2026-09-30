"""[E8] 부하 승인 계층(SALS) 시험: 부하 계약 기반 승인과 다른 관리 방식의 비교.

■ 목적
  보조버스에 접속된 부하의 선언 최대 합(29.1 kW)은 연속정격 25 kW보다 크다. SALS(부하 승인 계층)가
  부하 등급 계약(보고서 표 3.4)과 메시지 기반 승인만으로 합산 부하를 예산 23.75 kW(= 0.95 × 25 kW)
  이하로 지키면서, 미공급(서비스 손실)을 얼마나 줄이는지 확인한다(가설 H4, 보고서 4.6절·6.4절).

■ 왜 필요한가
  Stage B·제어기의 정격과 Tier-1 시험은 "부하가 계약을 지킨다"는 전제에 기대고 있다. 그 전제를
  실제로 보장하는 것이 SALS이므로, 메시지 지연·손실이 있어도 예산을 넘지 않는지, 그리고 단순한 정적
  예약보다 서비스 손실이 작은지를 보여야 부분전력 구조의 정격 분리가 운용 측면에서도 성립한다.
  또한 SALS가 만드는 1 ms 부하 변화가 Tier-1 시험(10 kW 스텝) 안에 있는지 확인해 전압 제어와 연결한다.

■ 부하 등급과 계약 (400 V 측 전력 [kW])
  M0 상시 예약 : Stage C 입력 −3.2 … +5.3 (변화율 ≤ 4 kW/ms), V2L 0 / 3.8 (계단)  → 항상 9.1 kW 예약
  M1 승인 후 기동: 전동 컴프레서 ≤ 6. 승인을 받아야 기동, 증가 ≤ 0.06 kW/ms(서지 없음), 감소 0.5 kW/ms
  D  지연 가능  : 캐빈 PTC(우선순위 1.0), 배터리 히터(0.7), 각 ≤ 7. 최신 허용치(일련번호) 추종,
                  증가 ≤ 0.06 kW/ms, 감소 0.5 kW/ms, 유효 메시지 없이 50 ms 지나면 허용치 0(워치독)
  메시지: 편도 지연 1–5 ms 균일, 메시지마다 확률 p_loss로 손실

■ 비교하는 관리 방식 (같은 시나리오에 적용)
  none   : 관리 없음. 모든 부하가 요청대로 동작, 컴프레서 즉시 기동
  static : 정적 예약. M0 + 컴프레서 최대(6 kW)를 항상 예약하고 남는 예산을 D에 고정 배분
  sals   : 계약 기반 승인. M0 상시 예약, M1은 요청 시점부터 예약, D는 우선순위로 재배분.
           허용치 증가·컴프레서 승인은 메시지 지연·손실·워치독·변화율을 모두 고려한 "인과적 최악값
           경계"가 앞으로의 모든 시각에서 예산 이하일 때만 보낸다(safe 함수). 감소는 즉시 보낸다.

■ 방법
  1 ms 간격 축약 부하 모델(전기모델과 결합하지 않음). 무작위 시나리오 200개(각 20 s, 시드 20260928),
  절반은 손실 없음, 나머지 절반은 손실률 0–20 % 균일.

■ 판정 기준
  sals: 예산 초과 시나리오 0, 25 kW 초과 0. 미공급률이 정적 예약보다 작을 것.
  1 ms 최대 부하 변화 ≤ 10 kW(Tier-1 시험 범위 안).

■ 실행   python E8_load_admission.py        (약 5–10분)
■ 결과   results/E8/sals_contract.json
■ 보고서 수치(표 6.4): 예산 초과 93 / 0 / 0, 25 kW 초과 57 / 0 / 0, 최대 합산 28.44 / 23.53 / 23.75 kW,
         미공급 0.6 / 35.2 / 7.0 %, 승인 지연(손실 없음 최대) 17 ms, 손실 시 99 % 25.4 ms·최대 32 ms
"""
import heapq
import sys

import numpy as np

from common import save_json, verdict

B = 0.95 * 25.0                   # SALS 예산 [kW] (V_bat ≥ V_g에서. 전압 의존 예산은 후속 과제)
M0_MAX = 5.3 + 3.8                # M0 상시 예약: Stage C 최대 + V2L
SC_MIN, SC_MAX, SC_SLEW = -3.2, 5.3, 4.0
V2L_P = 3.8
PC_MAX, UP, DN = 6.0, 0.06, 0.5   # 컴프레서 최대, 증가·감소 변화율 [kW/ms]
D_MAX = 7.0
WD, DMAX, PERIOD = 50, 5, 10      # 워치독 [ms], 최대 메시지 지연 [ms], 상태·허용치 주기 [ms]
T = 20000                         # 시나리오 길이 [ms]


def scenario(rng, p_loss):
    """외생 과정(Stage C 목표, V2L, 컴프레서 요청, D 요청). 세 방식에 똑같이 쓴다."""
    sc_target = np.empty(T); v = rng.uniform(0, 3); k = 0
    while k < T:                                          # Stage C: 지수분포 구간마다 새 목표값
        dur = int(rng.exponential(500)) + 1
        sc_target[k:k + dur] = v; k += dur
        v = rng.uniform(1.5, SC_MAX) if rng.random() < .7 else rng.uniform(SC_MIN, SC_MAX)
    v2l_on = rng.random() < .6                           # 60 % 시나리오에서 V2L 사용
    v2l = np.zeros(T)
    if v2l_on:
        k, state = 0, rng.random() < .5
        while k < T:
            dur = int(rng.exponential(5000)) + 1
            v2l[k:k + dur] = V2L_P if state else 0.; k += dur; state = not state
    comp = []                                            # 컴프레서 요청: (요청 시각, P_c, 정지 시각)
    k = int(rng.exponential(3000))
    while k < T - 500:
        dur = int(rng.uniform(3000, 10000))
        comp.append((k, rng.uniform(3, PC_MAX), min(T - 1, k + dur)))
        k += dur + int(rng.exponential(2000)) + 200
    dreq = np.zeros((T, 2))                              # D 부하 요청 [PTC, 배터리 히터]
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
    """메시지망: 편도 지연 1–DMAX ms, 확률 p로 손실. (도착 시각, 순번, 수신처, 내용) 우선순위 큐."""
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
    """남는 예산을 우선순위(PTC → 배터리 히터) 순으로 요청만큼 배분."""
    a = np.zeros(2)
    for j in (0, 1):
        a[j] = min(req[j], max(0., avail)); avail -= a[j]
    return a


def d_bound(t, horizon, sent, ack_seq, ack_time, sample, planned):
    """D 부하 1개의 [t, t+horizon) 최악 전력 경계(계약 기반).
    sent: (보낸 시각, 일련번호, 허용치) 목록, ack_seq/ack_time: 적용이 확인된 최신 일련번호와 적용 시각,
    sample: 최신 상태의 (시각, 전력), planned: SALS가 지금부터 보낼 허용치."""
    lo = t - 80
    tau = np.arange(lo, t + horizon)
    amax = np.zeros(len(tau))
    msgs = [m for m in sent if m[0] >= lo - DMAX - WD] + [(s, 1 << 60, planned) for s in range(t, t + horizon)]
    for s, seq, a in msgs:
        # 시각 s에 보낸 허용치는 [s+1, s+DMAX+WD] 동안만 유효할 수 있다. 더 새 번호의 적용이 확인되면 그 시각에 끝난다.
        i0, i1 = s + 1 - lo, s + DMAX + WD - lo + 1
        if seq < ack_seq: i1 = min(i1, ack_time - lo)
        if i1 > i0: amax[max(i0, 0):max(i1, 0)] = np.maximum(amax[max(i0, 0):max(i1, 0)], a)
    env = np.empty(len(tau)); cur = 0.
    for i in range(len(tau)):                        # 전력 ≤ 허용치 포락선(감소는 0.5 kW/ms로만 가능)
        cur = max(amax[i], cur - DN); env[i] = cur
    ts, ps = sample
    up = ps + UP * np.maximum(tau - ts, 0)           # 최신 측정값에서 증가율 0.06 kW/ms로 올라갈 수 있는 상한
    return np.minimum(env, up)[t - lo:]


def run(scn, policy):
    """시나리오 1개를 한 방식으로 1 ms씩 진행한다. 반환: 예산 초과 시간, 최대 부하, 미공급, 승인 지연 등."""
    rng = np.random.default_rng(scn['seed'])
    net = Net(rng, scn['p_loss'] if policy == 'sals' else 0.)
    sc = 0.; comp_p = 0.; pc = 0.; cstate = 'off'; creq_t = cstop_t = None; rid = 0
    ci, comp_events = 0, scn['comp']
    dp = np.zeros(2); d_allow = np.zeros(2); d_seq = np.zeros(2, int) - 1; d_rx = np.full(2, -10 ** 9)
    # SALS가 알고 있는 상태
    req_known = np.zeros(2); comp_known = None; comp_ts = -1; granted = None
    sent = [[], []]; seq = 0; ack = [(-1, -10 ** 9), (-1, -10 ** 9)]; samp = [(0, 0.), (0, 0.)]
    last_alloc = np.zeros(2)
    L = np.empty(T); unmet = np.zeros(2); req_sum = np.zeros(2)
    latencies, d_delays = [], []; pending_d = [None, None]; checks = 0
    static_alloc = allocate(B - M0_MAX - PC_MAX, np.array([D_MAX, D_MAX]))

    def safe(t, plan, comp_from):
        """앞으로 H ms 동안 최악 합산 부하가 예산 이하인지. comp_from: None(컴프레서 못 켬),
        'full'(이미 승인, P_c까지 가능), 정수(지금 승인 시 0.06 kW/ms 램프)."""
        H = 160
        tot = M0_MAX + sum(d_bound(t, H, sent[j], ack[j][0], ack[j][1], samp[j], plan[j]) for j in (0, 1))
        if comp_from == 'full': tot = tot + comp_known[1]
        elif comp_from is not None: tot = tot + np.minimum(comp_known[1], UP * np.arange(H))
        return bool(np.all(tot <= B + 1e-9))

    for t in range(T):
        sc += np.clip(scn['sc_target'][t] - sc, -SC_SLEW, SC_SLEW)       # Stage C(변화율 제한)
        v2l = scn['v2l'][t]
        # ---- 컴프레서 요청·정지
        if ci < len(comp_events) and cstate == 'off' and t >= comp_events[ci][0]:
            creq_t, pc, cstop_t = comp_events[ci]; ci += 1; rid += 1
            if policy == 'sals': cstate = 'waiting'; net.send(t, 'sals', ('cstat', t, rid, cstate, pc))
            else: cstate = 'ramp'; latencies.append(0)
        if cstate in ('ramp', 'run', 'waiting') and t >= cstop_t:
            if cstate == 'waiting': latencies.append(None)
            cstate = 'down'
        # ---- 메시지 도착
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
                    cstate = 'ramp'; latencies.append(t - creq_t)            # 승인 수신 → 기동
            else:
                j = int(dest[1]); _, s, a = msg
                if s > d_seq[j]:                                            # 더 새로운 허용치만 적용
                    d_seq[j], d_allow[j], d_rx[j] = s, a, t
                    net.send(t, 'sals', ('dstat', j, s, t, t, dp[j], scn['dreq'][t, j]))
        # ---- 컴프레서 동작(주기 상태 보고)
        if cstate in ('ramp', 'run'): comp_p = min(pc, comp_p + UP)
        elif cstate == 'down':
            comp_p = max(0., comp_p - DN)
            if comp_p == 0.: cstate = 'off'
        if policy == 'sals' and t % PERIOD == 0:
            net.send(t, 'sals', ('cstat', t, rid, cstate, pc))
        # ---- D 부하
        q = scn['dreq'][t]
        for j in (0, 1):
            if policy == 'none': allow = q[j]
            elif policy == 'static': allow = min(q[j], static_alloc[j])
            else: allow = min(q[j], d_allow[j] if t - d_rx[j] <= WD else 0.)   # 워치독
            dp[j] = min(dp[j] + UP, allow) if allow > dp[j] else max(allow, dp[j] - DN)
            if policy == 'sals' and t % PERIOD == 0:
                net.send(t, 'sals', ('dstat', j, d_seq[j], d_rx[j], t, dp[j], q[j]))
            # 첫 허용 지연 측정(예산 여유가 있었던 요청만 통계에 쓴다)
            if q[j] > 0 and pending_d[j] is None and (t == 0 or scn['dreq'][t - 1, j] == 0):
                c = pc if cstate != 'off' else 0.
                room = B - M0_MAX - c - (q[0] if j == 1 else 0.)
                pending_d[j] = (t, room >= 0.5)
            if pending_d[j] is not None and allow > 0:
                d_delays.append((j, t - pending_d[j][0], pending_d[j][1])); pending_d[j] = None
            if q[j] == 0: pending_d[j] = None
        # ---- SALS 결정
        if policy == 'sals':
            r_m1 = comp_known[1] if comp_known is not None else 0.
            plan = allocate(B - M0_MAX - r_m1, req_known)
            comp_mode = None if comp_known is None else ('full' if granted is not None else None)
            # 감소는 즉시, 증가는 최악값 검사를 통과할 때만(10 ms마다)
            new = np.minimum(plan, last_alloc)
            if np.any(plan > last_alloc + 1e-12) and t % PERIOD == 0:
                checks += 1
                if safe(t, plan, comp_mode): new = plan
            for j in (0, 1):
                if new[j] != last_alloc[j] or t % PERIOD == 0:
                    seq += 1; sent[j].append((t, seq, new[j])); net.send(t, f'd{j}', ('allow', seq, new[j]))
                    last_alloc[j] = new[j]
                if t % 50 == 0: sent[j] = [m for m in sent[j] if m[0] >= t - 200]
            if comp_known is not None and granted is None:           # 컴프레서 승인: 램프 포함 최악값 검사
                checks += 1
                if safe(t, last_alloc, t): granted = t
            if comp_known is not None and granted is not None and (granted == t or t % PERIOD == 0):
                net.send(t, 'comp', ('grant', comp_known[0]))
        L[t] = sc + v2l + comp_p + dp.sum()                            # 합산 부하
        unmet += np.maximum(q - dp, 0); req_sum += q
    step = np.diff(L)
    return dict(exceed_ms=int(np.sum(L > B + 1e-9)), over25_ms=int(np.sum(L > 25 + 1e-9)), peak=float(L.max()),
                step_up=float(step.max()), step_dn=float(-step.min()), checks=checks,
                latency=[l for l in latencies if l is not None], never_started=sum(l is None for l in latencies),
                d_delay=d_delays, unmet=(unmet / 1000).tolist(), req=(req_sum / 1000).tolist())   # [kW·s]


def main(N=200):
    print(f"[E8] 부하 승인 시험 (시나리오 {N}개 × 20 s)")
    rng = np.random.default_rng(20260928)
    res = {k: [] for k in ('none', 'static', 'sals')}; meta = []
    for i in range(N):
        p_loss = 0. if i % 2 == 0 else float(rng.uniform(0, .2))       # 짝수: 손실 없음, 홀수: 0–20 %
        scn = scenario(rng, p_loss); meta.append(p_loss)
        for pol in res: res[pol].append(run(scn, pol))
        if i % 20 == 0: print(f"   {i}/{N}", flush=True)
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
                         compressor_starts=len(lat0) + len(lat1),
                         compressor_requests_never_started=sum(r['never_started'] for r in rows),
                         grant_latency_ms_noloss=dict(median=float(np.median(lat0)), p99=float(np.percentile(lat0, 99)), max=int(max(lat0))) if lat0 else None,
                         grant_latency_ms_loss=dict(median=float(np.median(lat1)), p99=float(np.percentile(lat1, 99)), max=int(max(lat1))) if lat1 else None,
                         d_start_delay_ms_when_budget_available=dict(median=float(np.median(dd)), p99=float(np.percentile(dd, 99)), max=int(max(dd))) if dd else None,
                         d_unmet_fraction=dict(PTC=float(un[0] / rq[0]), BH=float(un[1] / rq[1]), total=float(un.sum() / rq.sum())))
    name = dict(none="관리 없음", static="정적 예약", sals="계약 기반 SALS")
    for pol, s in summ.items():
        u = s["d_unmet_fraction"]
        print(f"   {name[pol]:10s}: 예산 초과 {s['episodes_exceeding_budget']:3d}, 25 kW 초과 {s['episodes_over_25kW']:3d}, "
              f"최대 {s['peak_kW']:.2f} kW, 미공급 PTC/BH/전체 {u['PTC']*100:.1f}/{u['BH']*100:.1f}/{u['total']*100:.1f} %, "
              f"1 ms 최대 변화 +{s['max_step_up_kW']:.1f}/−{s['max_step_down_kW']:.1f} kW")
    s = summ["sals"]
    print(f"   SALS 승인 지연: 손실 없음 최대 {s['grant_latency_ms_noloss']['max']} ms, "
          f"손실 시 99 % {s['grant_latency_ms_loss']['p99']:.1f} ms·최대 {s['grant_latency_ms_loss']['max']} ms, "
          f"D 첫 허용 지연 최대 {s['d_start_delay_ms_when_budget_available']['max']} ms")
    verdict("SALS: 예산·연속정격 초과 시나리오 0", s["episodes_exceeding_budget"] == 0 and s["episodes_over_25kW"] == 0)
    verdict("SALS 미공급 < 정적 예약 미공급", s["d_unmet_fraction"]["total"] < summ["static"]["d_unmet_fraction"]["total"])
    verdict("1 ms 최대 부하 변화 ≤ 10 kW(Tier-1 범위)", max(s["max_step_up_kW"], s["max_step_down_kW"]) <= 10)
    save_json("E8", "sals_contract", dict(N=N, budget_kW=B, m0_reserve_kW=M0_MAX, summary=summ))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
