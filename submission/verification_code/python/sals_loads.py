"""400 V 부하의 등급별 계약 응답 모델: 보호 상태기계의 감발·분리·되돌림 명령이 SALS 메시지(지연·손실·워치독)를 거쳐
부하 전력에 닿기까지를 E17 평균모델(r2_run)에 넣기 위한 공용 모듈(E29).

■ 부하 등급과 계약(docs/14 표 R-2, 400 V 측 전력)
  M0  Stage C 입력 sc(−3.2 … +5.3 kW, 변화율 ≤ 4 kW/ms), V2L v2l(0 / 3.8 kW, 계단)  → SALS로 줄이지 않는다
  M1  전동 컴프레서 comp(≤ 6 kW): 증가 ≤ 0.06 kW/ms(승인 뒤), 감소 0.5 kW/ms
  D   캐빈 PTC ptc, 배터리 히터 bh(각 ≤ 7 kW): 허용치 추종, 증가 ≤ 0.06 kW/ms, 감소 0.5 kW/ms, 워치독 50 ms(fail-closed)

■ 명령과 전달(E29에서 정한 연동, docs/35)
  감발(curtail)  : 상태기계가 고장 검출 시각에 SALS로 보낸다(허브 제어기 안, 지연 없음). SALS는 D 허용치 0과 M1 한도 0을
                   순번을 붙여 보내고, 바뀌지 않아도 10 ms마다 다시 보낸다(docs/14 3.5절의 주기 송신).
                   장치 j는 k_j번째 송신(0부터)에서 처음 받는다고 두고(앞의 k_j번은 손실), 도착 = 명령 + 10 ms·k_j + 지연 d_j.
                   D는 새 메시지를 못 받아도 마지막 유효 수신(최악: 명령 시각) + 50 ms에 워치독으로 0으로 간다.
                   M1에는 워치독이 없다(계약에 없음) → 모두 손실이면 줄지 않는다. 그래서 상태기계가 시간 상한 뒤 접촉기 분리로 넘어간다.
  되돌림(restore): 강등이 끝난 뒤 SALS가 D 허용치·M1 한도를 되돌린다. 도착은 감발과 같은 규칙(손실 수는 따로)이고, 도착 뒤
                   증가 변화율 0.06 kW/ms로 요청값까지 오른다. 순번 규칙: 되돌림이 감발보다 먼저 도착하면 감발은 버려진다.
  Stage C 회생 차단(sc_block): Stage C는 허브 안의 변환기라 상태기계가 직접 명령한다(통신 없음). 고장 검출 t_sc 뒤 입력전력
                   하한을 0으로 두고 계약 변화율(4 kW/ms)로 올린다. 양의 전력은 그대로 둔다.
  접촉기 분리      : 접촉기 상태는 r2_run이 정한다(power의 connected). 분리되면 Stage C만 남는다(V2L·M1·D는 400 V급 부품이므로 함께 분리).

■ 시간 축소 ks(회로 시험용): SALS 시간(지연·재송신 주기·워치독)에 ks를 곱하고 M1·D 변화율은 ks로 나눈다(TB09–TB13의
  분리 20 ms → 3 ms와 같은 방식, ks = 0.15). Stage C 회생 차단(허브 내부, 1 ms 미만)은 축소하지 않는다.
"""
import math

DEV = ("comp", "ptc", "bh")          # SALS 감발 대상(M1, D)
D_CLASS = ("ptc", "bh")              # 워치독이 있는 D 등급
INF = math.inf


class SalsLoads:
    """시각 [s], 전력 [W]. 모든 응답은 해석식(구간별 직선)이라 표본마다 불러도 가볍다.

    mix    : dict(sc, v2l, comp, ptc, bh) — 고장 순간의 부하(요청값과 같다고 둔다) [W]
    delay  : 메시지 편도 지연 [s]. 수 하나 또는 장치별 dict(comp, ptc, bh)
    lost   : 장치별 감발 메시지의 처음 손실 횟수 dict. 정수 k(앞의 k번 손실) 또는 'all'(모두 손실)
    lost_r : 되돌림 메시지의 처음 손실 횟수 dict(같은 규칙)
    period, wd : 재송신 주기 10 ms, D 워치독 50 ms
    up, dn : 증가·감소 변화율 [W/s] (0.06·0.5 kW/ms)
    sc_block, t_sc, sc_slew : Stage C 회생 차단 여부, 명령 뒤 시작 지연 [s], 변화율 [W/s](4 kW/ms)
    ks     : 시간 축소 계수(1이면 실제 시간)
    """

    def __init__(self, mix, delay=5e-3, lost=None, lost_r=None, period=10e-3, wd=50e-3, up=60e3, dn=500e3,
                 sc_block=True, t_sc=.1e-3, sc_slew=4e6, ks=1.):
        self.mix = {k: float(mix.get(k, 0.)) for k in ("sc", "v2l", "comp", "ptc", "bh")}
        for k in DEV:
            assert self.mix[k] >= 0., "M1·D 전력은 0 이상"
        self.ks = ks
        dl = delay if isinstance(delay, dict) else {k: delay for k in DEV}
        self.delay = {k: dl[k] * ks for k in DEV}
        self.lost = {k: (lost or {}).get(k, 0) for k in DEV}
        self.lost_r = {k: (lost_r or {}).get(k, 0) for k in DEV}
        self.period, self.wd = period * ks, wd * ks
        self.up, self.dn = up / ks, dn / ks
        self.sc_block, self.t_sc, self.sc_slew = sc_block, t_sc, sc_slew      # Stage C(허브 내부)는 축소하지 않는다
        self.t_cut = self.t_rest = self.t_blk = None
        self.arr_cut = {k: INF for k in DEV}
        self.arr_rest = {k: INF for k in DEV}

    # ---- 명령 -----------------------------------------------------------------------------------
    def _arrival(self, t, k, lost):
        if lost == "all":
            return INF
        return t + int(lost) * self.period + self.delay[k]

    def curtail(self, t):
        """감발 명령(고장 검출 시각). Stage C 회생 차단도 같은 시각에 건다."""
        if self.t_cut is not None:
            return
        self.t_cut = t
        if self.t_blk is None:
            self.t_blk = t
        for k in DEV:
            a = self._arrival(t, k, self.lost[k])
            if k in D_CLASS:
                a = min(a, t + self.wd)                       # 워치독(마지막 유효 수신 ≤ 명령 시각)
            self.arr_cut[k] = a

    def block_regen(self, t):
        if self.t_blk is None:
            self.t_blk = t

    def restore(self, t):
        """되돌림 명령(강등 완료 뒤)."""
        if self.t_rest is not None or self.t_cut is None:
            return
        self.t_rest = t
        for k in DEV:
            self.arr_rest[k] = self._arrival(t, k, self.lost_r[k])

    # ---- 전력 -----------------------------------------------------------------------------------
    def p_dev(self, k, t):
        p0 = self.mix[k]
        ac, ar = self.arr_cut[k], self.arr_rest[k]
        if t < ac or ar <= ac:                                 # 감발 전, 또는 되돌림(더 새 순번)이 먼저 도착
            return p0
        pd = max(p0 - self.dn * (t - ac), 0.)
        if t < ar:
            return pd
        pa = max(p0 - self.dn * (ar - ac), 0.)                 # 되돌림 도착 때의 전력에서 증가 변화율로
        return min(p0, pa + self.up * (t - ar))

    def p_sc(self, t):
        sc = self.mix["sc"]
        if sc >= 0. or not self.sc_block or self.t_blk is None or t < self.t_blk + self.t_sc:
            return sc
        return min(0., sc + self.sc_slew * (t - self.t_blk - self.t_sc))

    def power(self, t, connected=True):
        p = self.p_sc(t)
        if connected:
            p += self.mix["v2l"] + sum(self.p_dev(k, t) for k in DEV)
        return p

    # ---- 해석값 -----------------------------------------------------------------------------------
    def curtail_done(self):
        """감발 대상이 모두 0이 되는 시각(무한대면 줄지 않는 장치가 있음)."""
        return max((self.arr_cut[k] + self.mix[k] / self.dn) if self.mix[k] > 0 else self.t_cut for k in DEV)

    def restore_done(self):
        """되돌림 뒤 모든 장치가 요청값으로 돌아오는 시각."""
        if self.t_rest is None:
            return INF
        out = self.t_rest
        for k in DEV:
            if self.mix[k] <= 0:
                continue
            ac, ar = self.arr_cut[k], self.arr_rest[k]
            if ar <= ac:
                continue
            pa = max(self.mix[k] - self.dn * (ar - ac), 0.)
            out = max(out, ar + (self.mix[k] - pa) / self.up)
        return out

    def describe(self):
        return dict(mix_W=self.mix, delay_s=self.delay, lost=self.lost, lost_r=self.lost_r, period_s=self.period, wd_s=self.wd,
                    up_W_per_s=self.up, dn_W_per_s=self.dn, sc_block=self.sc_block, t_sc_s=self.t_sc, sc_slew_W_per_s=self.sc_slew, ks=self.ks,
                    t_cut=self.t_cut, t_rest=self.t_rest, arr_cut={k: (None if v == INF else v) for k, v in self.arr_cut.items()},
                    arr_rest={k: (None if v == INF else v) for k, v in self.arr_rest.items()})
