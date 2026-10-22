"""[E17] Stage B 보호 상태기계 결합(보고서 이후 추가 검증).

■ 목적
  E14에서 정한 보호·기동 요구(P1–P6)를, 미리 짜 둔 전환 순서가 아니라 측정값으로 판단하는 보호 상태기계로 묶어
  검증 모델에 결합한다. 그리고 다음 세 가지를 확인한다.
  (1) 링크전류 센서 타당성 감시(P6)를 켠 상태로 E12의 시험 격자와 센서 요구 사양 집합을 다시 계산해도 판정이 같은가
  (2) 고장(제어 출력 고착, DAB 정지)과 정지 요청에서 상태기계가 검출 지연을 포함해 정격 안에서 정지시키는가
  (3) 충전 중(E16)에는 Stage A를 멈출 수 없는 구간이 생긴다. 이때 보호 절차를 어떻게 바꿔야 하는가(P7)

■ 왜 필요한가
  E14의 정지 전이는 "언제 어떤 모드로 바꿀지"를 시험 조건으로 정해 둔 계산이다. 실제 장치에서는 측정값으로 고장을 판단하고,
  판단·차단에 지연이 있으며, 운전 상태(배터리 전압, 충전 여부)에 따라 다른 절차를 골라야 한다. 이 결정 논리 자체가 검증 대상이다.
  또 E14 이후 충전 통합(E16)으로 새 운전 상태가 생겼다. 충전 중 Stage A가 멈추면 충전기 전류(최대 375 A)가 V_A 노드
  커패시터(400 µF)로만 들어가 V_A가 약 0.94 V/µs로 오른다. 따라서 P3("하드 고장은 Stage A를 10 µs 안에 함께 정지")를
  충전 중에는 그대로 쓸 수 없다.

■ 구성
  monitor     E12 시험 격자 576건과 센서 요구 사양 집합(요구 사양·오차 두 방향, 각 168건)을 감시를 켜고 다시 계산해
              E12 결과와 판정·지표를 비교하고, 감시 동작(오경보) 건수를 센다
  supervisor  (뒤에 추가) 보호 상태기계 + 모드 평균모델

■ 실행   python E17_protection_integration.py monitor
■ 결과   results/E17/*.json
"""
import sys
import time
from multiprocessing import Pool

import numpy as np

import stage_b_tests as st
from controller_adopted import K_ADOPTED, CP
from model_stage_b_switching import simulate_switching
from common import save_json, verdict, workers
import E12_switching_verification as E12

EID = "E17"
VAL_E12 = "../../../validation/2026-10-11-matlab-switching/E12"


# ----------------------------------------------------------------------------------------------
# (1) 감시를 켠 E12 재계산
# ----------------------------------------------------------------------------------------------
def _mon_case(args):
    tier, vbat, a, b, p, sw, meta = args
    meta = dict(meta); sens = meta.pop("_sensors", None); seed = meta.pop("_seed", 1)
    r = simulate_switching(float(vbat), float(a), float(b), p, CP, K_ADOPTED, predict=True, profile=0, sw=sw,
                           sensors=None if sens is None else np.array(sens), seed=seed)
    row = dict(tier=tier, vbat=vbat, p0=a, p1=b, **meta)
    row.update(E12.judge_sw(tier, r, p))
    rec = r["rec"]
    row["monitor_fault"] = bool(rec[:, 24].max() > .5)          # 감시가 고장으로 판정했는가(오경보)
    row["monitor_resid_max_A"] = float(np.abs(rec[:, 23]).max())  # 느린 필터 잔차 최대
    return row


def _key(r):
    return (r["tier"], r["set"], float(r["vbat"]), float(r["p0"]), float(r["p1"]), r.get("variant", ""))


def monitor():
    import json, os
    base, tol = E12.sets_sw()
    mon = dict(link_monitor=True)
    js = []
    for v in st.V_ALL:
        for n, p in base.items():
            js += [(1, v, a, b, p, mon, dict(set=n)) for a, b in st.T1_STEPS]
            js += [(2, v, a, b, p, mon, dict(set=n)) for a, b in st.T2_STEPS]
    for v in st.V_TOL:
        for n, p in tol.items():
            js += [(1, v, a, b, p, mon, dict(set=n)) for a, b in st.T1_STEPS]
            js += [(2, v, a, b, p, mon, dict(set=n)) for a, b in st.T2_STEPS]
    ngrid = len(js)
    cases = [(t, v, a, b, n, p) for v in st.V_ALL for n, p in base.items()
             for t, steps in ((1, st.T1_STEPS), (2, st.T2_STEPS)) for a, b in steps]
    variants = {"요구 사양(16비트·잡음)": E12.sensor_set(bits=16, noise=E12.SENS_NOISE_REQ),
                "요구 사양 + 오차(전류 낮게·전압 높게)": E12.sensor_set(bits=16, noise=E12.SENS_NOISE_REQ, sign=E12.CUR_LOW_V_HIGH),
                "요구 사양 + 오차(전류 높게·전압 낮게)": E12.sensor_set(bits=16, noise=E12.SENS_NOISE_REQ, sign=-E12.CUR_LOW_V_HIGH)}
    js += [(t, v, a, b, p, mon, dict(set=n, variant=name, _sensors=s.tolist(), _seed=1000 + i))
           for name, s in variants.items() for i, (t, v, a, b, n, p) in enumerate(cases)]
    t0 = time.time()
    with Pool(workers()) as pool:
        rows = pool.map(_mon_case, js, chunksize=2)
    print("  monitor: %d건, %.0f s" % (len(rows), time.time() - t0))
    grid, sens = rows[:ngrid], rows[ngrid:]
    # E12 저장 결과(감시 없음)와 비교
    ref_grid = {_key(r): r for r in json.load(open(os.path.join(VAL_E12, "grid.json")))["rows"]}
    ref_sens = {_key(r): r for r in json.load(open(os.path.join(VAL_E12, "sensors.json")))["rows"]}
    def compare(rows, ref):
        ch, dp, dd, miss = [], [], [], 0
        for r in rows:
            q = ref.get(_key(r))
            if q is None:
                miss += 1; continue
            if q["pass_"] != r["pass_"]:
                ch.append((r["tier"], r["set"], r["vbat"], r["p0"], r["p1"], r.get("variant", ""), q["pass_"], r["pass_"]))
            dp.append(max(r["path_inst"], r["bridge_inst"]) - max(q["path_inst"], q["bridge_inst"]))
            dd.append(r["droop"] - q["droop"])
        return dict(compared=len(dp), missing=miss, verdict_changes=ch,
                    inst_current_diff_A=[float(min(dp)), float(max(dp))] if dp else None,
                    droop_diff_V=[float(min(dd)), float(max(dd))] if dd else None)
    out = dict(grid=dict(total=len(grid), passed=sum(r["pass_"] for r in grid),
                         monitor_faults=sum(r["monitor_fault"] for r in grid),
                         resid_max_A=max(r["monitor_resid_max_A"] for r in grid),
                         vs_E12=compare(grid, ref_grid)),
               sensors={})
    for name in variants:
        sel = [r for r in sens if r["variant"] == name]
        out["sensors"][name] = dict(total=len(sel), passed=sum(r["pass_"] for r in sel),
                                    passed_640plus=sum(r["pass_"] for r in sel if r["vbat"] >= 640),
                                    total_640plus=sum(1 for r in sel if r["vbat"] >= 640),
                                    monitor_faults=sum(r["monitor_fault"] for r in sel),
                                    resid_max_A=max(r["monitor_resid_max_A"] for r in sel),
                                    vs_E12=compare(sel, ref_sens))
    g = out["grid"]
    print("  격자(감시 켬): %d/%d 통과, 오경보 %d건, 잔차 최대 %.2f A, E12 대비 판정 변화 %d건, 순시 전류 차 %s A"
          % (g["passed"], g["total"], g["monitor_faults"], g["resid_max_A"], len(g["vs_E12"]["verdict_changes"]), g["vs_E12"]["inst_current_diff_A"]))
    for name, s in out["sensors"].items():
        print("  %s: %d/%d 통과(640 V 이상 %d/%d), 오경보 %d건, 잔차 최대 %.2f A, 판정 변화 %d건"
              % (name, s["passed"], s["total"], s["passed_640plus"], s["total_640plus"], s["monitor_faults"], s["resid_max_A"],
                 len(s["vs_E12"]["verdict_changes"])))
    ok = (g["monitor_faults"] == 0 and not g["vs_E12"]["verdict_changes"]
          and all(s["monitor_faults"] == 0 and not s["vs_E12"]["verdict_changes"] for s in out["sensors"].values()))
    verdict("E17 감시를 켜도 E12 격자·센서 요구 사양 판정이 같고 오경보가 없다", ok)
    out["pass_"] = bool(ok)
    save_json(EID, "monitor", dict(summary=out, rows=rows))
    return out


# ----------------------------------------------------------------------------------------------
# (2) 보호 상태기계 + 모드 평균모델
# ----------------------------------------------------------------------------------------------
from dataclasses import replace                                     # noqa: E402
from controller_reference import NOMINAL                             # noqa: E402
from controller_adopted import StageBController                      # noqa: E402
from model_stage_b import equilibrium                                # noqa: E402
import E14_protection_startup as E14                                 # noqa: E402

RA_MOD, RW, CA = 10.2e-3, 3.0e-3, 400e-6   # Stage A 모듈 출력저항, 배선, V_A 노드 커패시터
# 보호 문턱(시험 전에 고정). 하드웨어 비교기는 연속 감시, 소프트웨어는 5 µs 표본
I_HW, VL_HW, VB_HW, VS_HW = 110., 115., 418., 100.   # 경로·필터 전류, 링크전압, 버스전압, 직렬전압
T_HW = 1.2e-6                              # 비교기 검출 1 µs + 게이트 구동 전파 0.2 µs
T_ASTOP = 10e-6                            # Stage A 정지(P3)
VL_SW, T_SW = (92., 108.), 50e-6           # 링크전압 소프트웨어 감시 창과 지속 시간(DAB 고장 판단)
ICH_DONE = 5.                              # 충전전류가 끊겼다고 보는 값
V_P2_MAX = 840.                            # 이 배터리 전압까지 제어 정지(P2) 후 버스 = V_A로 계속 공급
P2_RAMP, P2_HOLD = 1e-3, 2e-3
T_EV = 1e-3                                # 고장·정지 요청 시각


class Charger:
    """충전기 전류(지령 추종 전류원). stop(t) 요청을 받으면 t_resp 동안 0으로 줄인다."""
    def __init__(self, i0, t_resp):
        self.i0 = i0; self.t_resp = t_resp; self.t_stop = None

    def stop(self, t):
        if self.t_stop is None:
            self.t_stop = t

    def i(self, t):
        if self.t_stop is None or t < self.t_stop:
            return self.i0
        return self.i0 * max(0., 1. - (t - self.t_stop) / max(self.t_resp, 1e-9))


class SupCtrl(StageBController):
    """채택 제어기 + 상태기계가 정하는 버스 기준전압(P2 정지 램프)."""
    def __init__(self, vbat):
        super().__init__(K_ADOPTED, CP, vbat, predict=True)
        self.vref = 400.

    def step(self, x):
        self.cp = replace(CP, vref=float(self.vref))
        return super().step(x)


def supervise(job):
    """보호 상태기계 1건. job = dict(V, P, charging, fault, policy, t_chg, shed, duration)
    fault  : 'stop'(정지 요청) | 'm_pos'·'m_neg'(제어 출력 변조율 +0.95·−0.95 고착) | 'dab'(DAB 응답 없음, 링크전류 0)
    policy : 충전 중 하드 고장 대응 'P3'(Stage A 10 µs 정지, 충전기 정지 요청 동시) | 'P7'(충전기 정지 요청 → 충전전류가
             5 A 아래가 된 뒤 Stage A 정지) | 'P7s'(P7 + 400 V 부하 분리 t_shed 뒤)
    """
    V, P = job["V"], job["P"]; charging = job["charging"]; fault = job["fault"]; policy = job.get("policy", "P7")
    dt = 2e-7; dur = job.get("duration", 0.02)
    n_mod = 4 if charging else 1
    ich0 = min(375., 150e3 / (V / 2)) if charging else 0.
    ch = Charger(ich0, job.get("t_chg", 10e-3))
    RA = RA_MOD / n_mod
    pA = replace(NOMINAL, R=RA + RW); pW = replace(NOMINAL, R=RW)
    x, u = equilibrium(2 * (V / 2 + RA * ich0), P, pA)
    x = np.array(x, float)
    ctrl = SupCtrl(V); ctrl.reset(x, u)
    sample = int(round(CP.Ts / dt)); lag = int(round(NOMINAL.delay / dt))
    buf = np.tile(u, (lag + 1, 1)); tick = 0
    A_on = True; vA = V / 2 + RA * (ich0 - x[0]); t_astop = None
    bmode = "ctrl"; t_ramp = None; vA_est = None
    hw_since = None; sw_since = None; t_trip = None; trip_src = None
    t_shed = None; load_on = True
    events = []
    n = int(round(dur / dt)); log = np.empty((n, 9))
    for k in range(n):
        t = k * dt
        ich = ch.i(t)
        # ---- 하드웨어 비교기(연속) ----------------------------------------------------------
        if t_trip is None:
            cond = (abs(x[0]) > I_HW or abs(x[3]) > I_HW or x[4] > VL_HW or x[2] > VB_HW or abs(x[1]) > VS_HW)
            if cond:
                hw_since = t if hw_since is None else hw_since
                if t - hw_since >= T_HW:
                    t_trip = t; trip_src = "hw"
            else:
                hw_since = None
        # ---- 소프트웨어(5 µs 표본): 링크전압 감시, 정지 요청 ---------------------------------------
        if k % sample == 0:
            if t_trip is None and bmode in ("ctrl", "ramp"):
                if not (VL_SW[0] <= x[4] <= VL_SW[1]):
                    sw_since = t if sw_since is None else sw_since
                    if t - sw_since >= T_SW:
                        t_trip = t; trip_src = "sw_link"
                else:
                    sw_since = None
            if fault == "stop" and t >= T_EV and t_ramp is None and t_trip is None and bmode == "ctrl":
                if ich > ICH_DONE:
                    ch.stop(t)                                 # 충전 중 정지 요청: 충전기를 먼저 멈춘다(P7)
                    if ("chg_stop", ) not in [e[:1] for e in events]:
                        events.append(("chg_stop", t))
                elif V <= V_P2_MAX:
                    t_ramp = t; bmode = "ramp"
                    vA_est = float(E14.va_est(V, P))
                    events.append(("P2_ramp", t))
                else:
                    t_trip = t; trip_src = "stop_high_V"         # 840 V 초과: Stage A 협조 정지(P3)
        # ---- 하드 차단 처리 ---------------------------------------------------------------------
        if t_trip is not None and bmode != "off" and t >= t_trip:
            bmode = "off"; events.append(("B_off", t, trip_src))
            if charging and ich > ICH_DONE:
                ch.stop(t); events.append(("chg_stop", t))
                if policy == "P3":
                    t_astop = t + T_ASTOP
                if policy == "P7s":
                    t_shed = t + job.get("t_shed", 1e-3)
            else:
                t_astop = t + T_ASTOP
        if bmode == "off" and charging and policy in ("P7", "P7s") and t_astop is None and A_on and ich <= ICH_DONE:
            t_astop = t + T_ASTOP                              # 충전전류가 끊긴 뒤 Stage A 정지
        if A_on and t_astop is not None and t >= t_astop:
            A_on = False; vA = V / 2 + RA * (ich - x[0]); events.append(("A_off", t))
        if t_shed is not None and load_on and t >= t_shed:
            load_on = False; events.append(("load_shed", t))
        # ---- P2 램프 ---------------------------------------------------------------------------
        if bmode == "ramp":
            ctrl.vref = 400. + (vA_est - 400.) * min((t - t_ramp) / P2_RAMP, 1.)
            if t - t_ramp >= P2_RAMP + P2_HOLD:
                bmode = "zero"; events.append(("P2_zero", t))
        # ---- 제어기·고장 주입 -------------------------------------------------------------------
        if k % sample == 0 and bmode in ("ctrl", "ramp"):
            ctrl.t = t
            u = ctrl.step(x)
        buf[tick] = u; applied = buf[(tick + 1) % len(buf)].copy(); tick = (tick + 1) % len(buf)
        if t >= T_EV and fault in ("m_pos", "m_neg") and bmode in ("ctrl", "ramp"):
            applied[0] = .95 if fault == "m_pos" else -.95
        if t >= T_EV and fault == "dab":
            applied[1] = 0.
        mode = {"ctrl": "ctrl", "ramp": "ctrl", "zero": "zero", "off": "off"}[bmode]
        if mode == "zero":
            applied = np.array([0., 0.])
        if load_on and x[2] < E14.UVLO_V:
            load_on = False; events.append(("UVLO", t))
        Pl = P if load_on else 0.
        # ---- 플랜트 적분(중점법). Stage A 동작 중: 경로 전원 V_bat/2 + R_A·i_ch, 정지: V_A 노드(C_A) --------------
        if A_on:
            src, pe = V / 2 + RA * ich, pA
            d1 = E14.deriv(x, applied, mode, 2 * src, Pl, pe)
            x_new = x + dt * E14.deriv(x + .5 * dt * d1, applied, mode, 2 * src, Pl, pe)
            vA = V / 2 + RA * (ich - x[0])
        else:
            d1 = E14.deriv(x, applied, mode, 2 * vA, Pl, pW); dv1 = (ich - x[0]) / CA
            xm = x + .5 * dt * d1; vm = vA + .5 * dt * dv1
            x_new = x + dt * E14.deriv(xm, applied, mode, 2 * vm, Pl, pW)
            vA = vA + dt * (ich - xm[0]) / CA
            vA = min(max(vA, 0.), V)                           # Stage A 바디 다이오드: 0 ≤ V_A ≤ V_bat
        ih0 = x[3]; x = x_new
        if mode == "off" and (ih0 == 0. or ih0 * x[3] < 0.) and not abs(x[1]) > x[4]:
            x[3] = 0.                                          # H-브리지 다이오드 차단
        log[k] = [*x, vA, ich, float(load_on)]
        if not np.isfinite(x).all():
            log = log[:k + 1]; break
    tt = (np.arange(len(log)) + 1) * dt
    post = tt >= T_EV
    L = log[post]
    m = dict(V=V, P=P, charging=charging, fault=fault, policy=policy if charging else "-", t_chg=job.get("t_chg"),
             events=[(e[0], round(e[1] * 1e3, 4)) + tuple(e[2:]) for e in events],
             path_peak=float(np.abs(L[:, 0]).max()), bridge_peak=float(np.abs(L[:, 3]).max()),
             series_peak=float(np.abs(L[:, 1]).max()), vlink_max=float(L[:, 4].max()), vlink_min=float(L[:, 4].min()),
             vbus_max=float(L[:, 2].max()), vbus_min=float(L[log[post, 8] > .5, 2].min()) if (log[post, 8] > .5).any() else None,
             vA_max=float(L[:, 6].max()), ich_end=float(L[-1, 7]), bus_end=float(L[-1, 2]), load_end=bool(L[-1, 8] > .5),
             trip_ms=None if t_trip is None else round((t_trip - T_EV) * 1e3, 4), trip_src=trip_src)
    # 100 A 넘는 시간(펄스 길이)
    over = np.flatnonzero(post & ((np.abs(log[:, 0]) > 100.) | (np.abs(log[:, 3]) > 100.)))
    m["over100A_us"] = float(len(over) * dt * 1e6)
    m["checks"] = dict(current_pulse_150A=m["path_peak"] <= 150. and m["bridge_peak"] <= 150.,
                       current_over100A_le_20us=m["over100A_us"] <= 20.,
                       series_120V=m["series_peak"] <= 120., link_120V=m["vlink_max"] <= 120.,
                       bus_le_420V=m["vbus_max"] <= 420., vA_le_500V=m["vA_max"] <= 500.)
    m["pass_"] = bool(all(m["checks"].values()))
    if job.get("keep"):
        m["trace"] = dict(t=tt, log=log)
    return m


def supervisor_jobs():
    js = []
    for V in (640., 788., 860., 920.):
        for P in (5000., 25000.):
            for f in ("stop", "m_pos", "m_neg", "dab"):
                js.append(dict(V=V, P=P, charging=False, fault=f))
                for pol in ("P3", "P7", "P7s"):
                    for tc in (1e-3, 10e-3):
                        if f == "stop" and pol != "P7":
                            continue
                        js.append(dict(V=V, P=P, charging=True, fault=f, policy=pol, t_chg=tc, duration=.02 + tc))
    return js


def supervisor():
    js = supervisor_jobs()
    t0 = time.time()
    with Pool(workers()) as pool:
        rows = pool.map(supervise, js, chunksize=2)
    print("  supervisor: %d건, %.0f s" % (len(rows), time.time() - t0))
    groups = {}
    for r in rows:
        k = "%s|%s|%s|%s" % ("충전" if r["charging"] else "주행", r["fault"], r["policy"], "" if r["t_chg"] is None or not r["charging"] else "%.0fms" % (r["t_chg"] * 1e3))
        g = groups.setdefault(k, dict(n=0, passed=0, path=0., bridge=0., series=0., link=0., bus_max=0., vA=0., fails={}))
        g["n"] += 1; g["passed"] += int(r["pass_"])
        g["path"] = max(g["path"], r["path_peak"]); g["bridge"] = max(g["bridge"], r["bridge_peak"])
        g["series"] = max(g["series"], r["series_peak"]); g["link"] = max(g["link"], r["vlink_max"])
        g["bus_max"] = max(g["bus_max"], r["vbus_max"]); g["vA"] = max(g["vA"], r["vA_max"])
        for c, ok in r["checks"].items():
            if not ok:
                g["fails"].setdefault(c, []).append((r["V"], r["P"]))
    for k, g in groups.items():
        print("  %-28s %2d/%2d 통과, 경로 %.0f·필터 %.0f A, 직렬 %.0f V, 링크 %.0f V, 버스 최대 %.0f V, V_A 최대 %.0f V%s"
              % (k, g["passed"], g["n"], g["path"], g["bridge"], g["series"], g["link"], g["bus_max"], g["vA"],
                 ("  실패 " + str({c: len(v) for c, v in g["fails"].items()})) if g["fails"] else ""))
    save_json(EID, "supervisor", dict(groups=groups, rows=rows,
                                      thresholds=dict(I_HW=I_HW, VL_HW=VL_HW, VB_HW=VB_HW, VS_HW=VS_HW, T_HW=T_HW, T_ASTOP=T_ASTOP,
                                                      VL_SW=VL_SW, T_SW=T_SW, ICH_DONE=ICH_DONE, V_P2_MAX=V_P2_MAX)))
    return groups


PARTS = dict(monitor=monitor, supervisor=supervisor)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        print("==== E17 %s ====" % w, flush=True)
        PARTS[w]()
