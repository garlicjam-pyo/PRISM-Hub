"""[E14] Stage B 보호·기동 1차 검증(보고서 이후 추가 검증).

■ 목적
  Stage B는 보조버스 전체 경로에 직렬로 들어가므로, 정상 제어만이 아니라 정지(보호 동작)·기동 전이와
  센서 고장에서도 소자 정격과 보조버스 서비스 창을 지켜야 한다. 다음 네 가지를 시뮬레이션으로 확인한다.
  (1) 정지 전이: 보호 동작으로 Stage B를 멈출 때 버스·경로전류·직렬전압·링크전압이 어디까지 가는가
  (2) 기동 전이: 영벡터(직렬전압 0, 버스 = V_A) 상태에서 400 V 조정으로 넘어갈 때의 과도
  (3) 링크 프리차지: DAB로 링크를 0 V에서 충전할 때 변압기 전류(SPS 해석식)
  (4) 링크전류 센서 고장: 측정 기반 DAB 전류 제한(ρ̂·ε̂)이 센서 고장에서 정격을 넘지 않는가, 타당성 감시의 효과

■ 왜 필요한가
  E5–E13은 Stage B가 정상 동작하는 동안의 검증이다. Stage B가 멈추면 보조버스는 V_A = V_bat/2로 돌아가는데,
  배터리 840 V 초과에서는 V_A가 B_420 상한(420 V)을 넘는다. 또 직렬 포트·링크·H-브리지 필터에 저장된 에너지가
  정지 방식에 따라 과전압·과전류로 나타날 수 있다. DAB 전류 제한은 링크전류 센서에 기대므로(E12 3.5절),
  센서가 낮게 읽으면 실제 전류가 정격을 넘을 수 있다. 이 위험의 크기와 대책을 하드웨어 설계 전에 정해야 한다.

■ 모델
  (1)(2) Stage B 6상태 평균모델(model_stage_b.rhs)에 운전 모드를 더한 적분기(중점법 0.2 µs, 제어주기 5 µs·지연 5 µs).
     모드: 제어(채택 제어기, 버스 기준 램프 가능) / 영벡터(m = 0, DAB 정지) / 전 소자 차단(H-브리지 다이오드가
     필터전류를 링크로 환류, 전류 0에서 차단) / 바이패스(직렬 포트 단락 소자 투입, v_s = 0) / Stage A 정지(V_A 소스 제거,
     경로전류 ≥ 0). 부하는 정전력.
  (3) 이상 SPS(데드타임·손실 없음)의 반주기 구분선형 해석: 링크전압 0–100 V에서 평균 링크전류를 지정값으로 둘 때
     위상과 변압기 1차 전류 피크.
  (4) Stage B 스위칭 모델(model_stage_b_switching.py)의 링크전류 센서에 고장(고착 0·100 A, 이득 ×0.5·×2·−1,
     오프셋 ±10 A)을 넣고, 타당성 감시(측정 DAB 전류 대 링크 전하 수지 m·i_h + C_l·Δv_link/T)의 유무를 비교한다.

■ 구성
  stop        정지 전이 5종 × 배터리 640·700·788·860·920 V × 부하 5·25 kW
  start       기동 전이: 영벡터 → 400 V 조정(버스 기준 램프 0·0.5·1·2 ms) × 배터리 5종 × 부하 0·15·25 kW,
              배터리 800 V 이상은 Stage A 소프트스타트 중 400 V에서 Stage B가 인계(기울기 60·20·6 V/ms)
  precharge   링크 프리차지 SPS 해석(링크 0–100 V, 평균 10·20 A, 스위칭주파수 200·400·600 kHz)
  link_sensor 링크전류 센서 고장 7종 × 8개 사례 × 감시 유무, 정상 사례의 오경보 확인(기본 집합 84건)
  figures     그림

■ 판정
  정지·기동: 경로·필터 전류 ≤ 100 A(기동은 Tier-1 90 A), 직렬전압 ≤ 90 V, 링크 90–110 V(기동)·≤ 120 V(정지, DAB 정지 중
  환류 흡수), 버스 ∈ [260 V, 420 V](B_420 부품) — 정지 후 버스가 V_A로 가는 것은 구조적 결과이므로 배터리 전압별로 표시
  센서 고장: 링크전류 주기 평균 ≤ 80 A·링크전력 ≤ 8 kW·경로·필터 순시 ≤ 100 A(안전), Tier 판정(서비스)은 따로 집계

■ 실행   python E14_protection_startup.py               (전체, 2코어 약 15분)
■ 결과   results/E14/*.json, results/E14/E14_*.png
"""
import sys
import time
from dataclasses import replace
from multiprocessing import Pool

import numpy as np

from model_stage_b import rhs, equilibrium, primary_power
from controller_reference import NOMINAL
from controller_adopted import StageBController, K_ADOPTED, CP
from common import save_json, load_json, verdict, workers, outdir

LOAD_MIN_V, B420, B470 = 260., 420., 470.
UVLO_V = 250.             # 400 V 부하의 저전압 차단(정전력 부하가 이 아래로 버스를 끌어내리지 않음)
V_LIST = [640., 700., 788., 860., 920.]
T_EV = 1e-3


# ----------------------------------------------------------------------------------------------
# 모드가 있는 평균모델 적분기
# ----------------------------------------------------------------------------------------------
class RampController(StageBController):
    """채택 제어기 + 시간에 따라 바뀌는 버스 기준전압(기동·정지 램프). vref_fn(t)를 매 제어주기 반영한다."""
    def __init__(self, vbat, vref_fn):
        super().__init__(K_ADOPTED, CP, vbat, predict=True)
        self.vref_fn = vref_fn; self.t = 0.

    def step(self, x):
        self.cp = replace(CP, vref=float(self.vref_fn(self.t)))
        return super().step(x)


def diode_state(x, mode):
    """'off'·'bypass'·'offastop'에서 H-브리지 다이오드 상태(me, blocked). deriv와 같은 규칙."""
    ip, vs, vb, ih, vl, idab = x
    vsx = 0. if mode == "bypass" else vs
    if ih == 0. and abs(vsx) <= vl:
        return 0., True
    return (-np.sign(ih) if ih != 0. else np.sign(vsx)), False


def deriv(x, u, mode, vbat, power, p, diode=None):
    """모드별 미분. mode: 'ctrl'·'zero'(u 사용), 'off'(H-브리지 전 소자 차단), 'bypass'(직렬 포트 단락),
    'astop'(Stage A 정지 + 직렬 포트 영벡터).
    diode: (me, blocked)를 주면 다이오드 상태를 그 값으로 고정한다(E19의 run_modes(diode_fix=True)가 적분 한 걸음 동안
    시작 시점의 다이오드 상태를 유지하는 데 쓴다)."""
    ip, vs, vb, ih, vl, idab = x
    if mode in ("ctrl", "zero"):
        return rhs(x, u, vbat, power, p)
    if mode in ("off", "bypass", "offastop"):
        vsx = 0. if mode == "bypass" else vs
        if diode is not None:
            me, blocked = diode
        elif ih == 0. and abs(vsx) <= vl:                     # 다이오드 차단: 필터전류 0 유지(브리지 출력은 떠 있음)
            me = 0.; blocked = True
        else:
            me = -np.sign(ih) if ih != 0. else np.sign(vsx); blocked = False
    if mode == "off":
        if blocked:
            return np.array([(vbat / 2 - p.R * ip + vs - vb) / p.L, (ih - ip) / p.Cs,
                             (ip - (power + primary_power(vl * idab, p)) / vb) / p.Cb, 0., idab / p.Clink, -idab / p.tau])
        return np.array([(vbat / 2 - p.R * ip + vs - vb) / p.L, (ih - ip) / p.Cs,
                         (ip - (power + primary_power(vl * idab, p)) / vb) / p.Cb,
                         (me * vl - vs - p.Rh * ih) / p.Lh, (idab - me * ih) / p.Clink, -idab / p.tau])
    if mode == "bypass":
        return np.array([(vbat / 2 - p.R * ip - vb) / p.L, 0., (ip - (power + primary_power(vl * idab, p)) / vb) / p.Cb,
                         0. if blocked else (me * vl - p.Rh * ih) / p.Lh, (idab - me * ih) / p.Clink, -idab / p.tau])
    if mode in ("astop", "offastop"):                         # Stage A 정지: 경로전류는 0 아래로 갈 수 없음(다이오드)
        dip = (-p.R * ip + vs - vb) / p.L
        if ip <= 0. and dip < 0.:
            ip = 0.; dip = 0.
    if mode == "astop":                                      # V_A 소스 제거, H-브리지 영벡터, DAB 정지
        return np.array([dip, (ih - ip) / p.Cs, (ip - power / vb) / p.Cb,
                         (-vs - p.Rh * ih) / p.Lh, idab / p.Clink, -idab / p.tau])
    if mode == "offastop":                                   # V_A 소스 제거 + H-브리지 전 소자 차단
        return np.array([dip, (ih - ip) / p.Cs, (ip - power / vb) / p.Cb,
                         0. if blocked else (me * vl - vs - p.Rh * ih) / p.Lh, (idab - me * ih) / p.Clink, -idab / p.tau])
    raise ValueError(mode)


def run_modes(vbat, power, schedule, x0, ctrl=None, p=NOMINAL, dt=2e-7, duration=.01, keep=False, diode_fix=False):
    """schedule(t) → 모드 이름. 'ctrl' 모드에서만 제어기가 지령을 낸다(지연 버퍼 포함). 다른 모드에서는 지령 무시.
    'off'·'bypass'에서 H-브리지 필터전류가 0을 지나면 0에 고정(다이오드 차단), 'astop'에서 경로전류 ≥ 0."""
    sample = int(round(CP.Ts / dt)); lag = int(round(p.delay / dt))
    x = np.array(x0, float)
    u = np.array([x[1] / x[4] if x[4] > 0 else 0., 0.])
    if ctrl is not None:
        ctrl.reset(x, u)
    buf = np.tile(u, (lag + 1, 1)); tick = 0
    n = int(round(duration / dt))
    log = np.empty((n, 6)); modes = []
    mode_prev = None; load_on = True
    for k in range(n):
        t = k * dt
        mode = schedule(t)
        if mode != mode_prev:
            modes.append((t, mode)); mode_prev = mode
            if mode == "bypass":
                x[1] = 0.                                     # 직렬 포트 단락: C_s 전압 0(에너지는 단락 소자에서 소산)
        if k % sample == 0 and ctrl is not None and mode in ("ctrl", "ctrl_nodab"):
            ctrl.t = t
            u = ctrl.step(x)
            if mode == "ctrl_nodab":
                u = np.array([u[0], 0.])                      # DAB 고장: 링크전류 0
        elif mode == "zero":
            u = np.array([0., 0.])
        buf[tick] = u; applied = buf[(tick + 1) % len(buf)].copy(); tick = (tick + 1) % len(buf)
        if mode == "zero":
            applied = np.array([0., 0.])
        if mode == "ctrl_nodab":
            applied = np.array([applied[0], 0.])
        if load_on and x[2] < UVLO_V:
            load_on = False                                   # 400 V 부하 저전압 차단(래치)
        P = power if load_on else 0.
        md = "ctrl" if mode == "ctrl_nodab" else mode
        ih0 = x[3]
        # diode_fix: 다이오드 상태를 걸음 시작 시점 값으로 고정한다. 고정하지 않으면(기본, E14 결과 재현) 필터전류가
        # 한 걸음 변화량(dt·v_link/L_h ≈ 4.4 A)보다 작을 때 중점 평가에서 부호가 뒤집혀 0으로 가지 못하고 진동하며,
        # 그 평균전류가 링크를 계속 충전한다(E19에서 발견, 링크전압을 크게 보는 쪽의 수치 오차).
        dz = diode_state(x, md) if (diode_fix and md in ("off", "bypass", "offastop")) else None
        d1 = deriv(x, applied, md, vbat, P, p, dz)
        x = x + dt * deriv(x + .5 * dt * d1, applied, md, vbat, P, p, dz)
        if mode in ("off", "bypass", "offastop") and (ih0 == 0. or ih0 * x[3] < 0.):
            if not (mode in ("off", "offastop") and abs(x[1]) > x[4]):   # 직렬전압이 링크전압을 넘으면 다이오드가 다시 도통
                x[3] = 0.
        if mode in ("astop", "offastop") and x[0] < 0.:
            x[0] = 0.
        log[k] = x
        if not np.isfinite(x).all() or x[2] < 20:
            log = log[:k + 1]; break
    t = (np.arange(len(log)) + 1) * dt
    out = dict(t=t, x=log, modes=modes) if keep else dict(modes=modes)
    return out, t, log


def metrics(t, log, t_ev, vref0=400.):
    post = t >= t_ev
    X = log[post]
    tail = t >= t[-1] - 1e-3
    return dict(vbus_min=float(X[:, 2].min()), vbus_max=float(X[:, 2].max()), vbus_end=float(log[-1, 2]),
                path_peak=float(np.abs(X[:, 0]).max()), bridge_peak=float(np.abs(X[:, 3]).max()),
                series_peak=float(np.abs(X[:, 1]).max()), vlink_min=float(X[:, 4].min()), vlink_max=float(X[:, 4].max()),
                tail_ripple_V=float(np.ptp(log[tail, 2])), completed=bool(len(t) and t[-1] >= t[-1]))


# ----------------------------------------------------------------------------------------------
# (1) 정지 전이
# ----------------------------------------------------------------------------------------------
STOP_MODES = {
    "제어 정지(기준 램프 → 영벡터)": "ramp_zero",
    "DAB 고장 중 제어 정지(램프 0.5 ms)": "nodab_ramp",
    "전 소자 차단 + 10 µs 후 Stage A 정지": "off_astop",
    "전 소자 차단 + 50 µs 후 바이패스": "off_bypass",
    "영벡터 즉시(램프 없음)": "zero",
}
RAMP_STOP, HOLD_STOP = 1e-3, 2e-3       # 정지 램프: 버스 기준 400 V → V_A 1 ms, 정착 2 ms 뒤 영벡터


def va_est(vbat, power, R=NOMINAL.R):
    e = vbat / 2
    return (e + np.sqrt(e * e - 4 * R * power)) / 2


def stop_trace(name, vbat, power, duration=.01):
    """정지 전이 1건의 시간 궤적. 반환: (t, log, V_A, 종류)."""
    kind = STOP_MODES[name]
    x0, u0 = equilibrium(vbat, power, NOMINAL)
    va = float(va_est(vbat, power))
    ctrl = RampController(vbat, lambda t: 400.)
    if kind == "zero":
        sch = lambda t: "ctrl" if t < T_EV else "zero"
    elif kind == "ramp_zero":
        ctrl = RampController(vbat, lambda t: 400. if t < T_EV else 400. + (va - 400.) * min((t - T_EV) / RAMP_STOP, 1.))
        sch = lambda t: "ctrl" if t < T_EV + RAMP_STOP + HOLD_STOP else "zero"
    elif kind == "nodab_ramp":
        ctrl = RampController(vbat, lambda t: 400. if t < T_EV else 400. + (va - 400.) * min((t - T_EV) / .5e-3, 1.))
        sch = lambda t: "ctrl" if t < T_EV else ("ctrl_nodab" if t < T_EV + .5e-3 + .5e-3 else "zero")
    elif kind == "off_bypass":
        sch = lambda t: "ctrl" if t < T_EV else ("off" if t < T_EV + 50e-6 else "bypass")
    elif kind == "off_astop":
        sch = lambda t: "ctrl" if t < T_EV else ("off" if t < T_EV + 10e-6 else "offastop")
    else:
        sch = lambda t: "ctrl" if t < T_EV else "astop"
    _, t, log = run_modes(vbat, power, sch, x0, ctrl=ctrl, duration=duration)
    return t, log, va, kind


def stop_case(args):
    name, vbat, power = args
    t, log, va, kind = stop_trace(name, vbat, power)
    m = metrics(t, log, T_EV)
    m.update(response=name, vbat=vbat, power=power, VA=va)
    if kind in ("astop", "off_astop"):
        below = np.flatnonzero((t >= T_EV) & (log[:, 2] < LOAD_MIN_V))
        m["holdup_to_260V_ms"] = float((t[below[0]] - T_EV) * 1e3) if len(below) else None
    else:
        m["holdup_to_260V_ms"] = None
    m["checks"] = dict(path_100A=m["path_peak"] <= 100., bridge_100A=m["bridge_peak"] <= 100., series_90V=m["series_peak"] <= 90.,
                       link_110V=m["vlink_max"] <= 110., bus_le_420V=m["vbus_max"] <= B420, bus_le_470V=m["vbus_max"] <= B470)
    if kind not in ("off_astop",):
        m["checks"]["bus_ge_260V"] = m["vbus_min"] >= LOAD_MIN_V
    return m


def part_stop():
    js = [(n, v, P) for n in STOP_MODES for v in V_LIST for P in (5000., 25000.)]
    with Pool(workers()) as pool:
        rows = pool.map(stop_case, js, chunksize=2)
    summ = {}
    for n in STOP_MODES:
        sel = [r for r in rows if r["response"] == n]
        summ[n] = dict(path_peak_A=max(r["path_peak"] for r in sel), bridge_peak_A=max(r["bridge_peak"] for r in sel),
                       series_peak_V=max(r["series_peak"] for r in sel), vlink_max_V=max(r["vlink_max"] for r in sel),
                       vbus_range_V=[min(r["vbus_min"] for r in sel), max(r["vbus_max"] for r in sel)],
                       fails={k: [(r["vbat"], r["power"]) for r in sel if not r["checks"][k]] for k in sel[0]["checks"]})
        print(f"   {n:28s}: 경로 {summ[n]['path_peak_A']:.1f} A, 필터 {summ[n]['bridge_peak_A']:.1f} A, 직렬 {summ[n]['series_peak_V']:.1f} V, "
              f"링크 최대 {summ[n]['vlink_max_V']:.1f} V, 버스 {summ[n]['vbus_range_V'][0]:.1f}–{summ[n]['vbus_range_V'][1]:.1f} V")
        for k, f in summ[n]["fails"].items():
            if f:
                print(f"      {k} 미달: {f}")
    hold = {f"{r['vbat']:.0f}V_{r['power'] / 1e3:g}kW": r["holdup_to_260V_ms"] for r in rows if r["response"] == "전 소자 차단 + 10 µs 후 Stage A 정지"}
    print(f"   Stage A 정지 후 버스 260 V까지 유지 시간(ms): {hold}")
    v_b420 = 2 * B420
    print(f"   정지 후 버스 = V_A이므로 배터리 {v_b420:.0f} V 초과에서는 Stage B 정지만으로 B_420 상한을 지킬 수 없다(Stage A 정지 또는 차단 필요).")
    return dict(responses=STOP_MODES, voltages=V_LIST, summary=summ, holdup_ms=hold, rows=rows)


# ----------------------------------------------------------------------------------------------
# (2) 기동 전이: 영벡터(버스 = V_A) → 400 V 조정
# ----------------------------------------------------------------------------------------------
START_RAMPS = [0., .5e-3, 1e-3, 2e-3]


def zero_vector_state(vbat, power, p=NOMINAL):
    """영벡터 정상상태: 직렬 포트를 H-브리지 영벡터로 단락(m = 0, DAB 정지), 링크 100 V 충전 완료.
    v_s = −R_h·i_p, 버스 = V_bat/2 − (R + R_h)·i_p (정전력 부하의 큰 근)."""
    va = float(va_est(vbat, power, p.R + p.Rh)); ip = power / va
    return np.array([ip, -p.Rh * ip, va, ip, 100., 0.]), va


def start_case(args):
    """영벡터(버스 = V_A)에서 400 V 조정으로 기동. 제어기는 현재 상태로 초기화(적분기: 지령 = 경로전류, 직전 지령 = 영벡터)하고
    버스 기준을 V_A → 400 V로 tr 동안 직선 증가시킨다(tr = 0이면 계단)."""
    tr, vbat, power = args
    x0, va = zero_vector_state(vbat, power)
    vfn = (lambda t: 400.) if tr == 0 else (lambda t: va + (400. - va) * min(t / tr, 1.))
    ctrl = RampController(vbat, vfn)
    ctrl.reset(x0, np.array([0., 0.]))
    _, t2, log2 = run_modes_cont(vbat, power, x0, ctrl, duration=.016)
    m = metrics(t2, log2, 0.)
    post = t2 >= tr
    out = np.flatnonzero(post & (np.abs(log2[:, 2] - 400.) > 4.))
    settle = float(t2[out[-1]] - tr) if len(out) else 0.                  # 램프 끝 이후 ±4 V 밖에 있던 마지막 시각
    m.update(kind="영벡터 → 조정", ramp_ms=tr * 1e3, vbat=vbat, power=power, VA=va,
             vbus_max_after_ramp=float(log2[post, 2].max()), settle_after_ramp_ms=settle * 1e3)
    m["checks"] = dict(current_90A=max(m["path_peak"], m["bridge_peak"]) <= 90., series_90V=m["series_peak"] <= 90.,
                       link_band=bool(m["vlink_min"] >= 90. and m["vlink_max"] <= 110.),
                       overshoot_408V=bool(log2[post, 2].max() <= max(408., va)), settle_10ms=settle <= 10e-3,
                       final=abs(m["vbus_end"] - 400.) <= 4., initial_bus_le_420V=va <= B420)
    m["pass_"] = all(m["checks"].values())
    return m


def start_continue_case(args):
    """배터리 800 V 이상: Stage A 소프트스타트가 V_A = 400 V에 이른 시점(버스 = 400 V, 직렬 0)에 Stage B 조정을 시작하고,
    Stage A가 V_A를 V_bat/2까지 계속 올리는 동안(기울기 rate) Stage B가 버스를 400 V로 유지한다."""
    rate, vbat, power = args
    x0, va0 = zero_vector_state(800. + 2 * (NOMINAL.R + NOMINAL.Rh) * power / 400., power)   # V_A ≈ 400 V인 영벡터 상태
    va_end = vbat / 2
    vfn = lambda t: min(va0 + rate * t, va_end) * 2                                          # V_bat 등가(2·V_A)
    ctrl = RampController(vbat, lambda t: 400.)
    ctrl.reset(x0, np.array([0., 0.]))
    T = (va_end - va0) / rate
    _, t2, log2 = run_modes_cont(vbat, power, x0, ctrl, duration=T + 6e-3, vbat_fn=vfn)
    m = metrics(t2, log2, 0.)
    m.update(kind="Stage A 소프트스타트 연속", rate_V_per_ms=rate * 1e-3, vbat=vbat, power=power, ramp_ms=T * 1e3)
    m["checks"] = dict(current_90A=max(m["path_peak"], m["bridge_peak"]) <= 90., series_90V=m["series_peak"] <= 90.,
                       link_band=bool(m["vlink_min"] >= 90. and m["vlink_max"] <= 110.),
                       bus_392_408V=bool(392. <= m["vbus_min"] and m["vbus_max"] <= 408.), final=abs(m["vbus_end"] - 400.) <= 4.)
    m["pass_"] = all(m["checks"].values())
    return m


def run_modes_cont(vbat, power, x0, ctrl, p=NOMINAL, dt=2e-7, duration=.01, vbat_fn=None):
    """기동용: 영벡터에서 무충격으로 제어 시작(지연 버퍼를 영벡터 지령으로 채움). vbat_fn(t)를 주면 Stage A 출력(V_bat/2)이
    시간에 따라 변한다(소프트스타트). 제어기의 V_bat 측정값도 같이 갱신한다."""
    sample = int(round(CP.Ts / dt)); lag = int(round(p.delay / dt))
    x = np.array(x0, float); u = np.array([0., 0.])
    buf = np.tile(u, (lag + 1, 1)); tick = 0
    n = int(round(duration / dt)); log = np.empty((n, 6))
    for k in range(n):
        t = k * dt
        vb_t = vbat if vbat_fn is None else vbat_fn(t)
        if k % sample == 0:
            ctrl.t = t; ctrl.vbat = vb_t
            u = ctrl.step(x)
        buf[tick] = u; applied = buf[(tick + 1) % len(buf)].copy(); tick = (tick + 1) % len(buf)
        d1 = rhs(x, applied, vb_t, power, p)
        x = x + dt * rhs(x + .5 * dt * d1, applied, vb_t, power, p)
        log[k] = x
        if not np.isfinite(x).all() or x[2] < 20 or x[4] < 5:
            log = log[:k + 1]; break
    return None, (np.arange(len(log)) + 1) * dt, log


START_RATES = [60e3, 20e3, 6e3]          # Stage A 소프트스타트 기울기 [V/s] (400 → 460 V를 1·3·10 ms)


def part_start():
    js = [(tr, v, P) for tr in START_RAMPS for v in V_LIST for P in (0., 15000., 25000.)]
    js2 = [(r, v, P) for r in START_RATES for v in (860., 920.) for P in (0., 15000., 25000.)]
    with Pool(workers()) as pool:
        rows = pool.map(start_case, js, chunksize=2)
        rows2 = pool.map(start_continue_case, js2, chunksize=1)
    summ = {}
    for tr in START_RAMPS:
        sel = [r for r in rows if r["ramp_ms"] == tr * 1e3]
        summ[f"{tr * 1e3:g}ms"] = dict(passed=sum(r["pass_"] for r in sel), total=len(sel),
                                       max_current_A=max(max(r["path_peak"], r["bridge_peak"]) for r in sel),
                                       vbus_max_V=max(r["vbus_max"] for r in sel), series_peak_V=max(r["series_peak"] for r in sel),
                                       vlink_range_V=[min(r["vlink_min"] for r in sel), max(r["vlink_max"] for r in sel)],
                                       max_settle_after_ramp_ms=max(r["settle_after_ramp_ms"] for r in sel if r["vbat"] <= 2 * B420),
                                       fails=[(r["vbat"], r["power"], [k for k, ok in r["checks"].items() if not ok]) for r in sel if not r["pass_"]])
        s = summ[f"{tr * 1e3:g}ms"]
        print(f"   기준 램프 {tr * 1e3:g} ms: {s['passed']}/{s['total']} 통과, 최대 전류 {s['max_current_A']:.1f} A, 버스 최대 {s['vbus_max_V']:.1f} V, "
              f"직렬 {s['series_peak_V']:.1f} V, 링크 {s['vlink_range_V'][0]:.1f}–{s['vlink_range_V'][1]:.1f} V, 램프 후 정착 최대 {s['max_settle_after_ramp_ms']:.2f} ms"
              + (f", 실패 {[f for f in s['fails'] if f[0] <= 2 * B420]}" if [f for f in s['fails'] if f[0] <= 2 * B420] else ""))
    low = [r for r in rows if r["vbat"] <= 2 * B420]
    ok = sorted({r["ramp_ms"] for r in low} - {r["ramp_ms"] for r in low if not r["pass_"]})
    verdict("배터리 840 V 이하: 영벡터 → 400 V 조정 기동이 전류·전압 기준을 만족(기준 램프)", bool(ok), f"통과한 램프 {ok} ms")
    hi = [r for r in rows if r["vbat"] > 2 * B420]
    print(f"   배터리 840 V 초과({sorted({r['vbat'] for r in hi})} V): 영벡터 상태의 버스 = V_A가 이미 420 V 초과 → 이 순서로 기동할 수 없다")
    summ2 = {}
    for rt in START_RATES:
        sel = [r for r in rows2 if r["rate_V_per_ms"] == rt * 1e-3]
        summ2[f"{rt * 1e-3:g}V/ms"] = dict(passed=sum(r["pass_"] for r in sel), total=len(sel),
                                          max_current_A=max(max(r["path_peak"], r["bridge_peak"]) for r in sel),
                                          vbus_range_V=[min(r["vbus_min"] for r in sel), max(r["vbus_max"] for r in sel)],
                                          vlink_range_V=[min(r["vlink_min"] for r in sel), max(r["vlink_max"] for r in sel)])
        s2 = summ2[f"{rt * 1e-3:g}V/ms"]
        print(f"   Stage A 소프트스타트 연속(400 → V_bat/2, {rt * 1e-3:g} V/ms): {s2['passed']}/{s2['total']}, 최대 전류 {s2['max_current_A']:.1f} A, "
              f"버스 {s2['vbus_range_V'][0]:.2f}–{s2['vbus_range_V'][1]:.2f} V, 링크 {s2['vlink_range_V'][0]:.1f}–{s2['vlink_range_V'][1]:.1f} V")
    verdict("배터리 800 V 이상: Stage A 소프트스타트 중 Stage B 조정 인계가 기준을 만족", any(v["passed"] == v["total"] for v in summ2.values()))
    return dict(ramps_ms=[r * 1e3 for r in START_RAMPS], summary=summ, rows=rows, stageA_rates_V_per_ms=[r * 1e-3 for r in START_RATES],
                summary_continue=summ2, rows_continue=rows2)


# ----------------------------------------------------------------------------------------------
# (3) 링크 프리차지: 이상 SPS 해석
# ----------------------------------------------------------------------------------------------
def sps_wave(v1, v2, phi, f, L, n=4000):
    """이상 SPS 정상상태(반주기 반대칭) 1차 전류 파형. v1: 1차 직류, v2: 2차 1차 환산(n·v_link), phi: 위상[rad].
    반환: (1차 전류 피크, 2차 측 평균 전류 = n·평균(s2·i)/n 환산 전 1차 환산 평균)."""
    T = 1 / f; th = np.linspace(0, T / 2, n, endpoint=False); h = th[1] - th[0]
    d = phi / (2 * np.pi) * T
    s1 = np.ones_like(th); s2 = np.where(th < d, -1., 1.)
    vL = v1 * s1 - v2 * s2
    i = np.concatenate([[0.], np.cumsum(vL) * h / L])[:-1]
    i = i - (i[0] + i[-1] + vL[-1] * h / L) / 2                # 반주기 반대칭: i(T/2) = −i(0)
    return float(np.abs(i).max()), float(np.mean(s2 * i))


def part_precharge():
    p = NOMINAL; vb = 400.
    out = []
    for f in (200e3, 400e3, 600e3):
        for iavg in (10., 20.):
            for vl in (0., 10., 25., 50., 75., 100.):
                # 링크 평균전류 iavg(2차) = n·평균(s2·i_1) 가 되는 위상을 찾는다
                target = iavg / p.turns
                lo, hi = 0., np.pi / 2
                for _ in range(60):
                    mid = (lo + hi) / 2
                    _, ia = sps_wave(vb, p.turns * vl, mid, f, p.Ldab)
                    if ia < target: lo = mid
                    else: hi = mid
                pk, ia = sps_wave(vb, p.turns * vl, hi, f, p.Ldab)
                out.append(dict(f_kHz=f / 1e3, link_avg_A=iavg, vlink=vl, phase_deg=float(np.degrees(hi)), primary_peak_A=pk,
                                secondary_peak_A=pk * p.turns))
    # 정격 운전(640 V·25 kW 정상점, 링크 100 V)의 1차 전류 피크를 기준으로 비교
    x, u = equilibrium(640., 25000., p)
    from model_stage_b_switching import _phase_ff, _cp_vec
    ph_r = float(_phase_ff(u[1] / .9, x[2], _cp_vec(CP), .9))   # 공칭 L에서 실제 지령 전류를 내는 위상(ρ̂ ≈ 0.9)
    ref_pk, _ = sps_wave(400., p.turns * 100., ph_r, p.fs, p.Ldab)
    for r in out:
        r["over_rated_peak"] = r["primary_peak_A"] > ref_pk
    print(f"   정격 운전 기준(640 V·25 kW, 링크 {u[1]:.1f} A): 1차 피크 {ref_pk:.1f} A(2차 {ref_pk * p.turns:.0f} A)")
    for f in (200., 400., 600.):
        for ia in (10., 20.):
            sel = [r for r in out if r["f_kHz"] == f and r["link_avg_A"] == ia]
            over = [r["vlink"] for r in sel if r["over_rated_peak"]]
            print(f"   {f:.0f} kHz, 평균 {ia:g} A: 1차 피크 " + ", ".join(f"{r['vlink']:.0f} V {r['primary_peak_A']:.1f} A" for r in sel)
                  + (f"  → 정격 피크 초과 링크전압 {over}" if over else ""))
    return dict(bus_V=vb, rated_primary_peak_A=ref_pk, rated_phase_deg=float(np.degrees(ph_r)), rows=out)


# ----------------------------------------------------------------------------------------------
# (4) 링크전류 센서 고장(스위칭 모델)
# ----------------------------------------------------------------------------------------------
LS_FAULTS = {"고착 0 A": (0., 0.), "고착 100 A": (0., 100.), "이득 ×0.5": (.5, 0.), "이득 ×2": (2., 0.),
             "부호 반전": (-1., 0.), "오프셋 +10 A": (1., 10.), "오프셋 −10 A": (1., -10.)}
LS_CASES = [(2, "nominal", 640., 1000., 25000.), (1, "nominal", 640., 15000., 25000.), (2, "nominal", 920., 25000., 1000.),
            (1, "nominal", 788., 0., 10000.), (1, "Ldabx0.9", 640., 15000., 25000.), (1, "Ldabx1.1", 640., 15000., 25000.),
            (2, "Ldabx0.9", 632., 1000., 25000.), (2, "Ldabx0.9", 640., 1000., 25000.)]   # 누설 L −10 %: 낮게 읽는 센서의 최악
LS_FAULT_T = .5e-3        # 고장 시각(스텝 0.5 ms 전, 사전 구간에서 ρ̂ 학습 후)


def _ls_job(a):
    import E12_switching_verification as E
    tier, sname, v, P0, P1, fname, mon, extra = a
    base, tol = E.sets_sw()
    p = base.get(sname) or tol[sname]
    sens = np.vstack([np.array([[1., 0., 0., 0.]] * 6), [[1., 0., 0., 0.]]])
    if fname is not None:
        g, o = LS_FAULTS[fname]; sens[6] = [g, o, 0., 0.]
    sw = dict(link_sensor_fault_t=LS_FAULT_T, link_monitor=mon)
    if extra:
        sw.update(extra)
    from model_stage_b_switching import simulate_switching
    r = simulate_switching(v, P0, P1, p, CP, K_ADOPTED, sw=sw, sensors=sens)
    row = dict(tier=tier, set=sname, vbat=v, p0=P0, p1=P1, fault=fname or "정상", monitor=mon)
    row.update(E.judge_sw(tier, r, p))
    R = r["rec"]; pos = r["t"] > 0
    row["monitor_trip"] = bool(R[pos, 24].max() > 0)
    trip = np.flatnonzero(pos & (R[:, 24] > 0))
    row["trip_time_ms"] = float((r["t"][trip[0]] - LS_FAULT_T) * 1e3) if len(trip) else None
    row["rho_end"] = float(R[-1, 21]); row["eps_end"] = float(R[-1, 22]); row["resid_max_A"] = float(np.abs(R[pos, 23]).max())
    row["safe"] = bool(row["link_avg"] <= 80. + .5 and row["link_power_avg"] <= 8000. + 50.
                       and max(row["path_inst"], row["bridge_inst"]) <= 100.)
    return row


def part_link_sensor():
    js = [(t, s, v, a, b, f, mon, None) for f in LS_FAULTS for mon in (False, True) for t, s, v, a, b in LS_CASES]
    js += [(t, s, v, a, b, None, True, None) for t, s, v, a, b in LS_CASES]
    # 오경보 확인: 정상 센서(잡음·이득·오프셋 오차 포함)에서 감시를 켠 기본 집합
    import E12_switching_verification as E
    import stage_b_tests as st
    errs = E.sensor_set(bits=16, noise=E.SENS_NOISE_REQ, sign=E.CUR_LOW_V_HIGH)
    errs2 = E.sensor_set(bits=16, noise=E.SENS_NOISE_REQ, sign=-E.CUR_LOW_V_HIGH)
    fa = []
    for i, (t, v, a, b) in enumerate([(t, v, a, b) for v in st.V_ALL for t, steps in ((1, st.T1_STEPS), (2, st.T2_STEPS)) for a, b in steps]):
        fa.append((t, "nominal", float(v), float(a), float(b), errs if i % 2 == 0 else errs2, 1000 + i))
    with Pool(workers()) as pool:
        rows = pool.map(_ls_job, js, chunksize=1)
        farows = pool.map(_fa_job, fa, chunksize=2)
    summ = {}
    for f in LS_FAULTS:
        for mon in (False, True):
            sel = [r for r in rows if r["fault"] == f and r["monitor"] == mon]
            k = f"{f} | 감시 {'있음' if mon else '없음'}"
            summ[k] = dict(safe=sum(r["safe"] for r in sel), passed=sum(r["pass_"] for r in sel), total=len(sel),
                           max_link_avg_A=max(r["link_avg"] for r in sel), max_link_power_W=max(r["link_power_avg"] for r in sel),
                           tripped=sum(r["monitor_trip"] for r in sel),
                           max_trip_ms=max([r["trip_time_ms"] for r in sel if r["trip_time_ms"] is not None], default=None),
                           unsafe=[(r["set"], r["vbat"], r["p0"], r["p1"], round(r["link_avg"], 1)) for r in sel if not r["safe"]],
                           fails=[(r["set"], r["vbat"], r["p0"], r["p1"]) for r in sel if not r["pass_"]])
            s = summ[k]
            print(f"   {k:24s}: 안전 {s['safe']}/{s['total']}, Tier {s['passed']}/{s['total']}, 링크 최대 {s['max_link_avg_A']:.1f} A·{s['max_link_power_W'] / 1e3:.2f} kW"
                  + (f", 감시 동작 {s['tripped']}건" + (f"(최대 {s['max_trip_ms']:.2f} ms)" if s["max_trip_ms"] is not None else "") if mon else "")
                  + (f", 불안전 {s['unsafe']}" if s["unsafe"] else ""))
    norm = [r for r in rows if r["fault"] == "정상"]
    fa_trips = [r for r in farows if r["monitor_trip"]]
    print(f"   정상 센서 {len(norm)}개 사례(감시 있음): Tier {sum(r['pass_'] for r in norm)}/{len(norm)}, 감시 동작 {sum(r['monitor_trip'] for r in norm)}")
    print(f"   오경보 확인(기본 집합 84건, 센서 요구 사양 + 이득·오프셋 오차 ±, 잡음): 감시 동작 {len(fa_trips)}건, 잔차 최대 {max(r['resid_max_A'] for r in farows):.2f} A, "
          f"Tier {sum(r['pass_'] for r in farows)}/{len(farows)}")
    verdict("타당성 감시를 두면 링크전류 센서 고장 7종에서 정격(80 A·8 kW·100 A)을 넘지 않는다",
            all(summ[f"{f} | 감시 있음"]["safe"] == summ[f"{f} | 감시 있음"]["total"] for f in LS_FAULTS))
    verdict("정상 센서(오차·잡음 포함) 84건에서 감시 오경보 없음", not fa_trips)
    return dict(faults={k: list(v) for k, v in LS_FAULTS.items()}, fault_time_s=LS_FAULT_T, cases=LS_CASES,
                monitor=dict(threshold_A=6., threshold_rel=.15, alpha=.05, gate_alpha=.3, gate_fraction=.5), summary=summ, rows=rows,
                false_alarm=dict(total=len(farows), trips=len(fa_trips), resid_max_A=max(r["resid_max_A"] for r in farows),
                                 tier_pass=sum(r["pass_"] for r in farows), rows=farows))


def _fa_job(a):
    import E12_switching_verification as E
    tier, sname, v, P0, P1, sens, seed = a
    base, _ = E.sets_sw()
    p = base[sname]
    from model_stage_b_switching import simulate_switching
    r = simulate_switching(v, P0, P1, p, CP, K_ADOPTED, sw=dict(link_monitor=True), sensors=sens, seed=seed)
    row = dict(tier=tier, vbat=v, p0=P0, p1=P1)
    row.update(E.judge_sw(tier, r, p))
    R = r["rec"]; pos = r["t"] > -1e9
    row["monitor_trip"] = bool(R[pos, 24].max() > 0); row["resid_max_A"] = float(np.abs(R[pos, 23]).max())
    return row


# ----------------------------------------------------------------------------------------------
# 그림
# ----------------------------------------------------------------------------------------------
def part_figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    fig, ax = plt.subplots(1, 3, figsize=(10.4, 3.3))
    # (a) 정지 전이 25 kW: 버스전압
    for name, col in (("제어 정지(기준 램프 → 영벡터)", C["green"]), ("전 소자 차단 + 10 µs 후 Stage A 정지", C["gray"]),
                      ("전 소자 차단 + 50 µs 후 바이패스", C["red"]), ("영벡터 즉시(램프 없음)", C["orange"])):
        for v, ls in ((920., "-"), (640., "--")):
            t, log, _, _ = stop_trace(name, v, 25000., duration=.006)
            ax[0].plot((t - T_EV) * 1e3, log[:, 2], color=col, lw=1, ls=ls, label=name if v == 920. else None)
    ax[0].axhline(B420, color=C["red"], ls=":", lw=.8); ax[0].axhline(LOAD_MIN_V, color=C["red"], ls=":", lw=.8)
    ax[0].set_xlim(-.2, 4.5); ax[0].set_ylim(200, 560); ax[0].set_xlabel("정지 명령 후 시간 (ms)"); ax[0].set_ylabel("보조버스 (V)")
    ax[0].set_title("(a) 정지 전이, 25 kW(실선 920 V, 점선 640 V)"); ax[0].legend(fontsize=6, loc="upper right")
    # (b) 기동 640 V: 버스 기준 램프 0·1 ms × 부하 5·25 kW
    for P, ls in ((5000., "-"), (25000., "--")):
        for tr, col in ((0., C["red"]), (1., C["blue"])):
            x0, va = zero_vector_state(640., P)
            ctrl = RampController(640., (lambda va_, tr_: (lambda t: 400. if tr_ == 0 else va_ + (400. - va_) * min(t / (tr_ * 1e-3), 1.)))(va, tr))
            ctrl.reset(x0, np.array([0., 0.]))
            _, t, log = run_modes_cont(640., P, x0, ctrl, duration=.012)
            ax[1].plot(t * 1e3, log[:, 2], color=col, lw=1, ls=ls, label=f"{P / 1e3:g} kW, 램프 {tr:g} ms")
    ax[1].axhline(408, color=C["red"], ls=":", lw=.8)
    ax[1].set_xlim(0, 12); ax[1].set_xlabel("기동 후 시간 (ms)"); ax[1].set_ylabel("보조버스 (V)")
    ax[1].set_title("(b) 기동 640 V(영벡터 → 400 V)"); ax[1].legend(fontsize=6.5, loc="lower right")
    # (c) 링크 프리차지 1차 전류 피크
    pc = load_json("E14", "precharge")
    for f, col in ((200., C["red"]), (400., C["orange"]), (600., C["green"])):
        sel = [r for r in pc["rows"] if r["f_kHz"] == f and r["link_avg_A"] == 10.]
        ax[2].plot([r["vlink"] for r in sel], [r["primary_peak_A"] for r in sel], "o-", color=col, lw=1, ms=3, label=f"{f:.0f} kHz")
    ax[2].axhline(pc["rated_primary_peak_A"], color=C["blue"], ls="--", lw=.9)
    ax[2].text(2, pc["rated_primary_peak_A"] + 1, "정격 운전 피크", fontsize=7, color=C["blue"])
    ax[2].set_xlabel("링크전압 (V)"); ax[2].set_ylabel("DAB 1차 전류 피크 (A)"); ax[2].set_title("(c) 링크 프리차지(평균 10 A)")
    ax[2].legend(fontsize=6.5)
    fig.tight_layout(); fig.savefig(outdir("E14") / "E14_protection_startup.png"); plt.close(fig)
    print("   → 그림: results/E14/E14_protection_startup.png")


PARTS = dict(stop=part_stop, start=part_start, precharge=part_precharge, link_sensor=part_link_sensor, figures=part_figures)

if __name__ == "__main__":
    todo = sys.argv[1:] or list(PARTS)
    print("[E14] Stage B 보호·기동 1차 검증")
    for name in todo:
        t0 = time.time(); print(f"-- {name}", flush=True)
        res = PARTS[name]()
        if res is not None:
            save_json("E14", name, res)
        print(f"   ({time.time() - t0:.0f} s)", flush=True)
