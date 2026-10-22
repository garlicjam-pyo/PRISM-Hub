"""[E19] R2 창 조정 Stage B 모듈 검증: 축소 DAB 정격의 과도 성립, 모드 전환, DAB 고장 시 바이패스 강등.

■ 목적
  E18의 가치 지도에서 Stage B가 가치를 갖는 곳은 V_A가 400 V급 부품 상한을 넘는 팩이다. 이때 Stage B는
  400 V 전 범위 조정기(③, DAB 8 kW)가 아니라 창 조정 모듈(R2-W: V_A > V_W에서만 동작, DAB 1–3.5 kW)이 된다.
  설계를 이렇게 바꾸면 세 가지를 새로 확인해야 한다.
  (A) DAB 정격을 ③의 8 kW에서 창 조정에 맞게 줄여도 Tier-1·Tier-2 과도와 공차에서 판정을 지키는가.
      먼저 정격을 바꿔 가며(rating, 공칭·지연) Tier-2 과도의 DAB 전력 첨두와 정격 하한을 찾고, 정적 최대 링크전력의
      1.8배(과도 첨두 비)로 정한 최종 정격(1000 V급 240s 팩·B_470 부품의 R2-W460: 4.0 kW, 사양 팩·B_420 부품의
      R2-W410: 5.0 kW)을 공차까지 넣어 판정한다(window). 처음 후보였던 1.25배(3.0·3.5 kW)는 rating 결과로 남긴다.
  (B) 바이패스 ↔ 창 조정 전환: 히스테리시스 h = 5 V로 V_bat/2 ≥ V_W + h에서 켜고 ≤ V_W − h에서 끈다.
      켤 때(영벡터 → 조정, 기준 램프)와 끌 때(기준을 V_A로 램프 → 영벡터 → 바이패스), 그리고 고 SOC에서
      Stage A 소프트스타트 중 V_A = V_W에서 Stage B가 인계하는 경우의 과도를 확인한다.
  (C) Stage B 고장 시 바이패스 강등: DAB 고장(링크전류 0)에서 기준을 V_A로 램프한 뒤 바이패스하면 Stage A를
      멈추지 않고 경로가 유지되는가(기준선 ③은 배터리 840 V 초과의 Stage B 정지에 Stage A 협조 정지가 필요했다, E14).
      H-브리지 전 소자 차단 고장에서 바로 바이패스할 때의 충격도 기록한다(E14 정지 전이와 같은 모델).

■ 왜 필요한가
  R2는 Stage B를 선택 모듈로 줄이고 48 V 공급이 Stage B 고장에 끊기지 않게 하는 것이 목표다. 축소 정격이 과도를
  견디지 못하거나, 모드 전환·고장 강등이 과전류·과전압을 만들면 그 목표는 성립하지 않는다.

■ 모델
  Stage B 6상태 평균모델(model_stage_b)과 채택 제어기(R1, 이득·예측 구조 동일). 창 조정 설계값은 기준전압 V_W,
  DAB 권선비 V_W/100, 누설 L 11.1 µH·(V_W/400)²(SPS 전달 한계를 링크전류 기준으로 400 V 설계와 같게),
  DAB 정격 P_r(제어기 전류 한계 min(80 A, P_r/v_link, SPS)과 판정 한계에 함께 적용).
  모드 전환·고장은 E14의 모드 적분기(제어·영벡터·전 소자 차단·바이패스)를 쓰되, 다이오드 상태를 적분 한 걸음 동안
  시작 시점 값으로 고정한다(diode_fix). 고정하지 않으면 작은 필터전류가 0으로 가지 못하고 진동해 링크를 수치적으로
  충전한다(이 시험에서 발견. E14의 기본 계산은 바꾸지 않았다).

■ 판정(시험 전에 고정)
  (A) E13 창 조정 판정과 같다. Tier-1: ±8 V·회복 1 ms·최종 ±4 V·리플 0.1 V·포트 한계(DAB 전력 ≤ P_r 포함)·
      전류 ≤ 90 A. Tier-2: 버스 [V_W − 16, min(V_W + 16, 상한)]·최종 ±4 V·포트 한계·전류 ≤ 93.75 A.
      두 Tier 모두 내부 꼬리 진동(필터전류 ≤ 1 A_pp, 변조율 ≤ 0.01)과 버스 ≤ 부품 등급 상한
  (B) 전류 ≤ 90 A, 직렬 ≤ 90 V, 링크 90–110 V, 버스 ≤ 상한, 켬: 램프 끝 이후 ±4 V 정착 ≤ 10 ms·최종 ±4 V,
      끔: 바이패스 직전 직렬전압 ≤ 2 V
  (C) 경로·필터 ≤ 100 A, 직렬 ≤ 90 V, 링크 ≤ 120 V(DAB 정지 중 환류 흡수). 강등 후 버스 = V_A가 부품 상한을
      넘는지는 구조적 결과로 따로 기록한다(넘으면 400 V 부하 분리 필요).

■ 실행   python E19_r2_window_module.py                 (전체, 2코어 약 40분)
         python E19_r2_window_module.py window rating transition fault figures
■ 결과   results/E19/*.json, results/E19/E19_*.png

■ 한계
  평균모델이다(스위칭 리플·데드타임은 E12·TB04가 같은 제어기에서 따로 확인). 바이패스 소자와 H-브리지 영벡터 사이의
  전류 이전은 직렬전압 ≈ 0에서 일어난다고 보고 모델링하지 않는다. 400 V 부하 분리 소자·SALS 명령은 모델 밖이다.
"""
import sys
import time
from dataclasses import replace
from multiprocessing import Pool

import numpy as np

from model_stage_b import simulate, equilibrium
from controller_reference import NOMINAL, assess
from controller_adopted import StageBController, K_ADOPTED, CP
from stage_b_tests import T1_STEPS, T2_STEPS, T1_LIMIT_A, T2_LIMIT_A, TAIL_IH_PP_A, TAIL_M_PP, FIELDS, DELAY_BUDGET
from E14_protection_startup import run_modes, run_modes_cont, metrics, zero_vector_state, va_est
from common import save_json, load_json, verdict, workers, outdir

T0 = 1e-3                     # 스텝 시각
DURATION = .02
H = 5.                        # 모드 히스테리시스 [V]
LOAD_MIN_V = 260.

# 창 조정 설계 사례(E18 가치 지도에서 Stage B가 필요한 대표 두 사례)
CASES = {
    "W460_240s": dict(VW=460., Pr=4000., upper=470., vbat_max=1008., label="R2-W460, 240s 팩(720–1008 V), B_470 부품",
                      V_win=[930., 960., 1008.], V_tol=[930., 1008.]),
    "W410_spec": dict(VW=410., Pr=5000., upper=420., vbat_max=920., label="R2-W410, 사양 팩(640–920 V), B_420 부품",
                      V_win=[830., 860., 920.], V_tol=[920.]),
}
RATING_SWEEP = {"W460_240s": [2000., 2500., 3000., 3500., 4000.], "W410_spec": [3000., 3500., 4000., 4500., 5000.]}


def plant(case, Pr=None):
    c = CASES[case]; s = c["VW"] / 400.
    kw = dict(vref=c["VW"], turns=c["VW"] / NOMINAL.vlink, Ldab=NOMINAL.Ldab * s * s, power_max=Pr or c["Pr"])
    return replace(NOMINAL, **kw), replace(CP, **kw)


def param_sets(p):
    sets = {"nominal": p, "delay+3.0us": replace(p, delay=p.delay + DELAY_BUDGET)}
    tol = {}
    for field in FIELDS:
        for f in (.9, 1.1):
            tol[f"{field}x{f}"] = replace(p, **{field: getattr(p, field) * f})
    tol["tau15us"] = replace(p, tau=15e-6)
    tol["eta0.94"] = replace(p, eta=.94)
    return sets, tol


# ----------------------------------------------------------------------------------------------
# (A) 창 조정 Tier-1·Tier-2 (축소 DAB 정격)
# ----------------------------------------------------------------------------------------------
def judge_w(tier, r, vref, upper):
    """E13 judge_reg와 같은 판정에 부품 등급 상한(upper)만 일반화."""
    t, x, u = r["t"], r["x"], r["u"]
    post = x[t >= T0, 2]; tail = t >= t[-1] - 1e-3
    ih_pp = float(np.ptp(x[tail, 3])); m_pp = float(np.ptp(u[tail, 0]))
    peak = max(r["path_peak"], r["bridge_peak"])
    vmax_all = float(x[:, 2].max())
    if tier == 1:
        checks = dict(r["checks"]); checks["current_90A"] = peak <= T1_LIMIT_A
    else:
        lo, hi = vref - 16, min(vref + 16, upper)
        checks = dict(completed=r["completed"], ports=r["within_port_limits"], bus_band=bool(lo <= post.min() and post.max() <= hi),
                      final_voltage=bool(abs(x[-1, 2] - vref) <= 4), current_93p75A=peak <= T2_LIMIT_A)
    checks["internal_tail_oscillation"] = bool(ih_pp <= TAIL_IH_PP_A and m_pp <= TAIL_M_PP)
    checks["class_upper"] = vmax_all <= upper
    return dict(path_peak=r["path_peak"], bridge_peak=r["bridge_peak"], dab_power_peak=r["dab_power_peak"],
                vbus_min_post=float(post.min()), vbus_max_post=float(post.max()), vbus_max_all=vmax_all,
                dev_max=float(np.max(np.abs(post - vref))), recovery_s=r["recovery_s"], series_peak=r["series_peak"],
                vlink_min=r["vlink_min"], vlink_max=r["vlink_max"], ports_violated=[k for k, v in r["violations"].items() if v],
                failed=[k for k, v in checks.items() if not v], pass_=bool(all(checks.values())))


def run_window(job):
    case, Pr, tier, name, vbat, a, b, p = job
    c = CASES[case]; _, cp = plant(case, Pr)
    dt = 1e-7 if abs(p.delay / 2e-7 - round(p.delay / 2e-7)) > 1e-9 else 2e-7
    ctrl = StageBController(K_ADOPTED, cp, vbat, predict=True)
    try:
        r = simulate(vbat, a, b, p=p, K=K_ADOPTED, control_p=cp, duration=DURATION, dt=dt, keep_trace=True, controller=ctrl)
    except ValueError:                       # 스텝 전 정상점부터 DAB 정격 밖(정격이 정적 링크전력보다 작음)
        return dict(case=case, Pr=Pr, tier=tier, set=name, vbat=vbat, p0=a, p1=b, path_peak=0., bridge_peak=0.,
                    dab_power_peak=float("nan"), vbus_min_post=float("nan"), vbus_max_post=float("nan"), vbus_max_all=float("nan"),
                    dev_max=float("nan"), recovery_s=None, series_peak=0., vlink_min=float("nan"), vlink_max=float("nan"),
                    ports_violated=["initial_steady_state"], failed=["initial_steady_state_outside_rating"], pass_=False)
    r.update(assess(r["t"], r["x"], T0, r["completed"], r["within_port_limits"], vref=c["VW"]))
    return dict(case=case, Pr=Pr, tier=tier, set=name, vbat=vbat, p0=a, p1=b, **judge_w(tier, r, c["VW"], c["upper"]))


def window_jobs(case, Pr, with_tol=True):
    c = CASES[case]; p, _ = plant(case, Pr)
    sets, tol = param_sets(p)
    js = []
    for v in c["V_win"]:
        for name, pp in sets.items():
            js += [(case, Pr, 1, name, v, a, b, pp) for a, b in T1_STEPS] + [(case, Pr, 2, name, v, a, b, pp) for a, b in T2_STEPS]
    if with_tol:
        for v in c["V_tol"]:
            for name, pp in tol.items():
                js += [(case, Pr, 1, name, v, a, b, pp) for a, b in T1_STEPS] + [(case, Pr, 2, name, v, a, b, pp) for a, b in T2_STEPS]
    return js


def summarize(rows):
    out = {}
    for key, sel in [("T1", lambda r: r["tier"] == 1), ("T2", lambda r: r["tier"] == 2)]:
        rall = [r for r in rows if sel(r)]
        rr = [r for r in rall if "initial_steady_state" not in r["ports_violated"]]     # 지표는 적분한 사례만
        if not rall:
            continue
        if not rr:
            out[key] = dict(total=len(rall), passed=0, initial_outside_rating=len(rall), max_current_A=0., max_dev_V=0.,
                            vbus_post_V=[0., 0.], max_series_V=0., max_dab_W=0., vlink_V=[0., 0.],
                            fails=[(r["set"], r["vbat"], r["p0"], r["p1"], r["failed"]) for r in rall][:12])
            continue
        out[key] = dict(total=len(rall), passed=sum(r["pass_"] for r in rall), initial_outside_rating=len(rall) - len(rr),
                        max_current_A=max(max(r["path_peak"], r["bridge_peak"]) for r in rr),
                        max_dev_V=max(r["dev_max"] for r in rr),
                        vbus_post_V=[min(r["vbus_min_post"] for r in rr), max(r["vbus_max_post"] for r in rr)],
                        max_series_V=max(r["series_peak"] for r in rr), max_dab_W=max(r["dab_power_peak"] for r in rr),
                        vlink_V=[min(r["vlink_min"] for r in rr), max(r["vlink_max"] for r in rr)],
                        fails=[(r["set"], r["vbat"], r["p0"], r["p1"], r["failed"]) for r in rall if not r["pass_"]][:12])
    # H2 판정 범위(docs/22에서 정정): Tier-1은 지연 +3.0 µs 포함, Tier-2는 지연 없는 집합만 판정하고 지연 사례는 정보
    scope = [r for r in rows if r["tier"] == 1 or r["set"] != "delay+3.0us"]
    out["H2_scope"] = dict(total=len(scope), passed=sum(r["pass_"] for r in scope))
    return out


def part_window():
    out = {}
    for case, c in CASES.items():
        js = window_jobs(case, c["Pr"])
        print(f"   {c['label']}: V_W {c['VW']:.0f} V, DAB {c['Pr'] / 1e3:.1f} kW, {len(js)}건")
        with Pool(workers()) as pool:
            rows = pool.map(run_window, js, chunksize=4)
        s = summarize(rows)
        print(f"     H2 판정 범위(Tier-2 지연 사례는 정보): {s['H2_scope']['passed']}/{s['H2_scope']['total']}")
        for k, v in s.items():
            if k == "H2_scope":
                continue
            print(f"     {k}: {v['passed']}/{v['total']}, 최대 전류 {v['max_current_A']:.2f} A, 편차 {v['max_dev_V']:.2f} V, "
                  f"버스 {v['vbus_post_V'][0]:.1f}–{v['vbus_post_V'][1]:.1f} V, 직렬 최대 {v['max_series_V']:.1f} V, "
                  f"DAB 최대 {v['max_dab_W'] / 1e3:.2f} kW, 링크 {v['vlink_V'][0]:.1f}–{v['vlink_V'][1]:.1f} V"
                  + (f", 실패 {v['fails'][:3]}" if v["fails"] else ""))
        verdict(f"{case} Tier-1·Tier-2 전부 통과(DAB {c['Pr'] / 1e3:.1f} kW, 공차 포함)", all(r["pass_"] for r in rows))
        out[case] = dict(design=dict(VW=c["VW"], Pr=c["Pr"], upper=c["upper"]), summary=s, rows=rows)
    save_json("E19", "window", out)
    return out


def part_rating():
    """DAB 정격 하한: 공칭·지연 집합만으로 정격을 바꿔 가며 판정."""
    out = {}
    for case, prs in RATING_SWEEP.items():
        out[case] = {}
        for Pr in prs:
            js = window_jobs(case, Pr, with_tol=False)
            with Pool(workers()) as pool:
                rows = pool.map(run_window, js, chunksize=4)
            s = summarize(rows)
            out[case][f"{Pr:.0f}"] = dict(passed=sum(r["pass_"] for r in rows), total=len(rows), summary=s)
            print(f"   {case} DAB {Pr / 1e3:.1f} kW: {out[case][f'{Pr:.0f}']['passed']}/{len(rows)}(H2 범위 {s['H2_scope']['passed']}/{s['H2_scope']['total']})"
                  + "".join(f", {k} 최대 DAB {v['max_dab_W'] / 1e3:.2f} kW·링크 {v['vlink_V'][0]:.1f}–{v['vlink_V'][1]:.1f} V" for k, v in s.items() if k != "H2_scope")
                  + (f", 실패 예 {[f for k, v in s.items() if k != 'H2_scope' for f in v['fails']][:2]}" if any(v.get("fails") for v in s.values()) else ""))
    save_json("E19", "rating", out)
    return out


# ----------------------------------------------------------------------------------------------
# (B) 모드 전환
# ----------------------------------------------------------------------------------------------
class RampW(StageBController):
    """채택 제어기 + 시간에 따라 바뀌는 기준전압. 창 조정 설계값(cp0)을 유지한 채 vref만 바꾼다."""
    def __init__(self, cp0, vbat, vref_fn):
        super().__init__(K_ADOPTED, cp0, vbat, predict=True)
        self.cp0, self.vref_fn, self.t = cp0, vref_fn, 0.

    def step(self, x):
        self.cp = replace(self.cp0, vref=float(self.vref_fn(self.t)))
        return super().step(x)


def enable_case(args):
    """켬: 바이패스(버스 = V_A) 상태에서 H-브리지 영벡터로 넘긴 뒤(직렬 ≈ 0) 기준을 V_A → V_W로 tr 동안 낮춘다."""
    case, tr, vbat, power = args
    c = CASES[case]; p, cp = plant(case)
    x0, va = zero_vector_state(vbat, power, p)
    vfn = (lambda t: c["VW"]) if tr == 0 else (lambda t: va + (c["VW"] - va) * min(t / tr, 1.))
    ctrl = RampW(cp, vbat, vfn); ctrl.reset(x0, np.array([0., 0.]))
    _, t, log = run_modes_cont(vbat, power, x0, ctrl, p=p, duration=.016)
    m = metrics(t, log, 0.)
    post = t >= tr
    out = np.flatnonzero(post & (np.abs(log[:, 2] - c["VW"]) > 4.))
    settle = float(t[out[-1]] - tr) if len(out) else 0.
    m.update(kind="enable", case=case, ramp_ms=tr * 1e3, vbat=vbat, power=power, VA=va, settle_after_ramp_ms=settle * 1e3)
    m["checks"] = dict(current_90A=max(m["path_peak"], m["bridge_peak"]) <= 90., series_90V=m["series_peak"] <= 90.,
                       link_band=bool(m["vlink_min"] >= 90. and m["vlink_max"] <= 110.), class_upper=m["vbus_max"] <= c["upper"],
                       settle_10ms=settle <= 10e-3, final=abs(m["vbus_end"] - c["VW"]) <= 4.)
    m["pass_"] = all(m["checks"].values())
    return m


def handover_case(args):
    """고 SOC 기동: Stage A 소프트스타트로 V_A가 오르다가 V_W에 이르면 Stage B가 영벡터에서 인계해 버스를 V_W로 유지하고,
    V_A는 기울기 rate로 V_bat/2까지 계속 오른다(E14 start_continue_case를 V_W로 일반화)."""
    case, rate, power = args
    c = CASES[case]; p, cp = plant(case)
    vbat = c["vbat_max"]
    x0, va0 = zero_vector_state(2 * c["VW"] + 2 * (p.R + p.Rh) * power / c["VW"], power, p)
    va_end = vbat / 2
    vfn = lambda t: min(va0 + rate * t, va_end) * 2
    ctrl = RampW(cp, vbat, lambda t: c["VW"]); ctrl.reset(x0, np.array([0., 0.]))
    T = (va_end - va0) / rate
    _, t, log = run_modes_cont(vbat, power, x0, ctrl, p=p, duration=T + 6e-3, vbat_fn=vfn)
    m = metrics(t, log, 0.)
    m.update(kind="handover", case=case, rate_V_per_ms=rate * 1e-3, vbat=vbat, power=power, ramp_ms=T * 1e3)
    m["checks"] = dict(current_90A=max(m["path_peak"], m["bridge_peak"]) <= 90., series_90V=m["series_peak"] <= 90.,
                       link_band=bool(m["vlink_min"] >= 90. and m["vlink_max"] <= 110.),
                       bus_pm8V=bool(c["VW"] - 8 <= m["vbus_min"] and m["vbus_max"] <= c["VW"] + 8), class_upper=m["vbus_max"] <= c["upper"],
                       final=abs(m["vbus_end"] - c["VW"]) <= 4.)
    m["pass_"] = all(m["checks"].values())
    return m


RAMP_OFF, HOLD_OFF, ZERO_OFF = 1e-3, 1e-3, .2e-3


def disable_case(args):
    """끔: V_bat/2 = V_W − h(직렬 +h V로 보태는 중)에서 기준을 V_W → V_A로 1 ms 램프, 1 ms 유지, 영벡터 0.2 ms 뒤 바이패스."""
    case, dv, power = args
    c = CASES[case]; p, cp = plant(case)
    vbat = 2 * (c["VW"] + dv)
    x0, u0 = equilibrium(vbat, power, p)
    va = float(va_est(vbat, power, p.R))
    t_ev = .5e-3
    ctrl = RampW(cp, vbat, lambda t: c["VW"] if t < t_ev else c["VW"] + (va - c["VW"]) * min((t - t_ev) / RAMP_OFF, 1.))
    t_zero = t_ev + RAMP_OFF + HOLD_OFF; t_byp = t_zero + ZERO_OFF
    sch = lambda t: "ctrl" if t < t_zero else ("zero" if t < t_byp else "bypass")
    _, t, log = run_modes(vbat, power, sch, x0, ctrl=ctrl, p=p, duration=8e-3, diode_fix=True)
    m = metrics(t, log, 0.)
    k_byp = int(np.searchsorted(t, t_byp)) - 1
    m.update(kind="disable", case=case, dv_V=dv, vbat=vbat, power=power, VA=va, series_at_bypass_V=float(abs(log[k_byp, 1])))
    m["checks"] = dict(current_90A=max(m["path_peak"], m["bridge_peak"]) <= 90., series_90V=m["series_peak"] <= 90.,
                       link_band=bool(m["vlink_min"] >= 90. and m["vlink_max"] <= 110.), class_upper=m["vbus_max"] <= c["upper"],
                       series_at_bypass_2V=m["series_at_bypass_V"] <= 2., bus_ge_260=m["vbus_min"] >= LOAD_MIN_V)
    m["pass_"] = all(m["checks"].values())
    return m


def part_transition():
    js_e = [(case, tr, 2 * (c["VW"] + H), P) for case, c in CASES.items() for tr in (0., .5e-3, 1e-3, 2e-3) for P in (0., 15000., 25000.)]
    js_h = [(case, r, P) for case in CASES for r in (60e3, 20e3, 6e3) for P in (0., 15000., 25000.)]
    js_d = [(case, dv, P) for case in CASES for dv in (-H, 0.) for P in (0., 15000., 25000.)]
    with Pool(workers()) as pool:
        re = pool.map(enable_case, js_e); rh = pool.map(handover_case, js_h); rd = pool.map(disable_case, js_d)
    out = {}
    for name, rows in (("enable", re), ("handover", rh), ("disable", rd)):
        for case in CASES:
            sel = [r for r in rows if r["case"] == case]
            s = dict(passed=sum(r["pass_"] for r in sel), total=len(sel),
                     max_current_A=max(max(r["path_peak"], r["bridge_peak"]) for r in sel),
                     vbus_V=[min(r["vbus_min"] for r in sel), max(r["vbus_max"] for r in sel)],
                     series_peak_V=max(r["series_peak"] for r in sel),
                     vlink_V=[min(r["vlink_min"] for r in sel), max(r["vlink_max"] for r in sel)],
                     fails=[(r.get("ramp_ms", r.get("rate_V_per_ms", r.get("dv_V"))), r["power"], [k for k, ok in r["checks"].items() if not ok])
                            for r in sel if not r["pass_"]])
            if name == "disable":
                s["series_at_bypass_V_max"] = max(r["series_at_bypass_V"] for r in sel)
            out.setdefault(name, {})[case] = s
            print(f"   {name:8s} {case}: {s['passed']}/{s['total']}, 최대 전류 {s['max_current_A']:.1f} A, 버스 {s['vbus_V'][0]:.1f}–{s['vbus_V'][1]:.1f} V, "
                  f"직렬 최대 {s['series_peak_V']:.1f} V, 링크 {s['vlink_V'][0]:.1f}–{s['vlink_V'][1]:.1f} V"
                  + (f", 바이패스 직전 직렬 최대 {s['series_at_bypass_V_max']:.2f} V" if name == "disable" else "")
                  + (f", 실패 {s['fails'][:3]}" if s["fails"] else ""))
    verdict("모드 전환(켬·인계·끔) 전부 통과", all(r["pass_"] for r in re + rh + rd))
    out["rows"] = dict(enable=re, handover=rh, disable=rd)
    save_json("E19", "transition", out)
    return out


# ----------------------------------------------------------------------------------------------
# (C) 고장 시 바이패스 강등
# ----------------------------------------------------------------------------------------------
FAULTS = {
    "DAB 고장 → 기준 램프 0.5 ms → 영벡터 → 바이패스": ("nodab", .5e-3),
    "DAB 고장 → 기준 램프 1 ms → 영벡터 → 바이패스": ("nodab", 1e-3),
    "H-브리지 전 소자 차단 → 50 µs 후 바이패스": ("off_bypass", None),
}


def fault_case(args):
    case, name, power = args
    kind, tr = FAULTS[name]
    c = CASES[case]; p, cp = plant(case)
    vbat = c["vbat_max"]
    x0, u0 = equilibrium(vbat, power, p)
    va = float(va_est(vbat, power, p.R))
    t_ev = .5e-3
    if kind == "nodab":
        ctrl = RampW(cp, vbat, lambda t: c["VW"] if t < t_ev else c["VW"] + (va - c["VW"]) * min((t - t_ev) / tr, 1.))
        t_zero = t_ev + tr + .2e-3; t_byp = t_zero + ZERO_OFF
        sch = lambda t: "ctrl" if t < t_ev else ("ctrl_nodab" if t < t_zero else ("zero" if t < t_byp else "bypass"))
    else:
        ctrl = RampW(cp, vbat, lambda t: c["VW"])
        t_byp = t_ev + 50e-6
        sch = lambda t: "ctrl" if t < t_ev else ("off" if t < t_byp else "bypass")
    _, t, log = run_modes(vbat, power, sch, x0, ctrl=ctrl, p=p, duration=6e-3, diode_fix=True)
    m = metrics(t, log, t_ev)
    k_byp = int(np.searchsorted(t, t_byp)) - 1
    m.update(case=case, fault=name, vbat=vbat, power=power, VA=va, series_at_bypass_V=float(abs(log[k_byp, 1])),
             bus_after_V=float(log[-1, 2]), above_class_after=bool(log[-1, 2] > c["upper"]))
    m["checks"] = dict(path_100A=m["path_peak"] <= 100., bridge_100A=m["bridge_peak"] <= 100., series_90V=m["series_peak"] <= 90.,
                       link_120V=m["vlink_max"] <= 120., bus_ge_260=m["vbus_min"] >= LOAD_MIN_V)
    m["pass_"] = all(m["checks"].values())
    return m


def part_fault():
    js = [(case, n, P) for case in CASES for n in FAULTS for P in (5000., 25000.)]
    with Pool(workers()) as pool:
        rows = pool.map(fault_case, js)
    out = {}
    for case, c in CASES.items():
        for n in FAULTS:
            sel = [r for r in rows if r["case"] == case and r["fault"] == n]
            s = dict(passed=sum(r["pass_"] for r in sel), total=len(sel), path_peak_A=max(r["path_peak"] for r in sel),
                     bridge_peak_A=max(r["bridge_peak"] for r in sel), series_peak_V=max(r["series_peak"] for r in sel),
                     vlink_max_V=max(r["vlink_max"] for r in sel), series_at_bypass_V=max(r["series_at_bypass_V"] for r in sel),
                     bus_after_V=max(r["bus_after_V"] for r in sel), above_class_after=any(r["above_class_after"] for r in sel),
                     fails=[(r["power"], [k for k, ok in r["checks"].items() if not ok]) for r in sel if not r["pass_"]])
            out.setdefault(case, {})[n] = s
            print(f"   {case} | {n}: {s['passed']}/{s['total']}, 경로 {s['path_peak_A']:.1f} A, 필터 {s['bridge_peak_A']:.1f} A, "
                  f"링크 최대 {s['vlink_max_V']:.1f} V, 바이패스 직전 직렬 {s['series_at_bypass_V']:.1f} V, 강등 후 버스 {s['bus_after_V']:.1f} V"
                  f"({'상한 초과 → 400 V 부하 분리 필요' if s['above_class_after'] else '상한 이내'})" + (f", 실패 {s['fails']}" if s["fails"] else ""))
    out["rows"] = rows
    save_json("E19", "fault", out)
    return out


# ----------------------------------------------------------------------------------------------
# 그림
# ----------------------------------------------------------------------------------------------
def part_figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    fig, ax = plt.subplots(1, 3, figsize=(15, 3.9))
    case = "W460_240s"; c = CASES[case]; p, cp = plant(case)
    # (a) Tier-2 1 → 25 kW, V_bat 1008 V
    ctrl = StageBController(K_ADOPTED, cp, 1008., predict=True)
    r = simulate(1008., 1000., 25000., p=p, K=K_ADOPTED, control_p=cp, duration=DURATION, dt=2e-7, keep_trace=True, controller=ctrl)
    ax[0].plot(r["t"] * 1e3, r["x"][:, 2], color=C["blue"], label="버스 v_bus")
    a2 = ax[0].twinx(); a2.grid(False)
    a2.plot(r["t"] * 1e3, r["x"][:, 0], color=C["orange"], lw=.8, label="경로전류 i_p")
    a2.plot(r["t"] * 1e3, r["x"][:, 4] * r["x"][:, 5] / 100., color=C["green"], lw=.8, label="DAB 전력/100 [W]")
    ax[0].axhspan(c["VW"] - 16, min(c["VW"] + 16, c["upper"]), color="y", alpha=.15)
    ax[0].set_xlim(0, 6); ax[0].set_ylim(440, 475); a2.set_ylim(-40, 100)
    ax[0].set_xlabel("시간 [ms]"); ax[0].set_ylabel("버스 [V]"); a2.set_ylabel("전류 [A] / 전력 [W/100]")
    h1, l1 = ax[0].get_legend_handles_labels(); h2, l2 = a2.get_legend_handles_labels()
    ax[0].legend(h1 + h2, l1 + l2, fontsize=7, loc="lower right")
    ax[0].set_title("(a) R2-W460 Tier-2 1→25 kW, V_bat 1008 V, DAB 4 kW")
    # (b) 켬(기준 램프 1 ms)과 끔(V_A로 램프 → 바이패스)
    x0, va = zero_vector_state(2 * (c["VW"] + H), 25000., p)
    ctrl = RampW(cp, 2 * (c["VW"] + H), lambda t: va + (c["VW"] - va) * min(t / 1e-3, 1.)); ctrl.reset(x0, np.array([0., 0.]))
    _, t, log = run_modes_cont(2 * (c["VW"] + H), 25000., x0, ctrl, p=p, duration=6e-3)
    ax[1].plot(t * 1e3, log[:, 2], color=C["blue"], label="켬: 버스")
    ax[1].plot(t * 1e3, log[:, 2] - log[:, 1], color=C["blue"], ls=":", label="켬: V_A(버스 − 직렬전압)")
    vbat = 2 * (c["VW"] - H); x0, _ = equilibrium(vbat, 25000., p); va2 = float(va_est(vbat, 25000., p.R))
    ctrl = RampW(cp, vbat, lambda t: c["VW"] if t < .5e-3 else c["VW"] + (va2 - c["VW"]) * min((t - .5e-3) / RAMP_OFF, 1.))
    t_zero = .5e-3 + RAMP_OFF + HOLD_OFF
    _, t, log = run_modes(vbat, 25000., lambda tt: "ctrl" if tt < t_zero else ("zero" if tt < t_zero + ZERO_OFF else "bypass"),
                          x0, ctrl=ctrl, p=p, duration=6e-3, keep=False, diode_fix=True)
    ax[1].plot(t * 1e3, log[:, 2], color=C["orange"], label="끔: 버스")
    ax[1].plot(t * 1e3, log[:, 2] - log[:, 1], color=C["orange"], ls=":", label="끔: V_A(버스 − 직렬전압)")
    ax[1].axvline((t_zero + ZERO_OFF) * 1e3, color=C["gray"], lw=.8, ls="--"); ax[1].text((t_zero + ZERO_OFF) * 1e3 + .05, 452, "바이패스", fontsize=7)
    ax[1].set_xlabel("시간 [ms]"); ax[1].set_ylabel("[V]"); ax[1].set_ylim(450, 470); ax[1].legend(fontsize=7, ncol=2, loc="upper right")
    ax[1].set_title("(b) 모드 전환(25 kW, 히스테리시스 ±5 V)")
    # (c) DAB 고장 → 1 ms 램프 → 바이패스, V_bat 1008 V, 25 kW
    vbat = c["vbat_max"]; x0, _ = equilibrium(vbat, 25000., p); va3 = float(va_est(vbat, 25000., p.R))
    ctrl = RampW(cp, vbat, lambda t: c["VW"] if t < .5e-3 else c["VW"] + (va3 - c["VW"]) * min((t - .5e-3) / 1e-3, 1.))
    t_zero = .5e-3 + 1e-3 + .2e-3
    _, t, log = run_modes(vbat, 25000., lambda tt: "ctrl" if tt < .5e-3 else ("ctrl_nodab" if tt < t_zero else ("zero" if tt < t_zero + ZERO_OFF else "bypass")),
                          x0, ctrl=ctrl, p=p, duration=5e-3, diode_fix=True)
    ax[2].plot(t * 1e3, log[:, 2], color=C["blue"], label="버스")
    ax[2].plot(t * 1e3, log[:, 4] * 4, color=C["green"], label="링크 × 4")
    a3 = ax[2].twinx(); a3.grid(False); a3.plot(t * 1e3, log[:, 0], color=C["orange"], lw=.8, label="경로전류")
    ax[2].axhline(c["upper"], color=C["red"], ls="--", lw=.8); ax[2].text(.1, c["upper"] + 2, "B_470 상한", fontsize=7, color=C["red"])
    ax[2].set_ylim(380, 520); a3.set_ylim(0, 120)
    ax[2].set_xlabel("시간 [ms]"); ax[2].set_ylabel("[V]"); a3.set_ylabel("경로전류 [A]")
    h1, l1 = ax[2].get_legend_handles_labels(); h2, l2 = a3.get_legend_handles_labels()
    ax[2].legend(h1 + h2, l1 + l2, fontsize=7, loc="lower right")
    ax[2].set_title("(c) DAB 고장 → 1 ms 램프 → 바이패스(1008 V, 25 kW)")
    fig.tight_layout(); fig.savefig(outdir("E19") / "E19_r2_window.png"); plt.close(fig)
    print("   그림 저장: results/E19/E19_r2_window.png")


PARTS = dict(window=part_window, rating=part_rating, transition=part_transition, fault=part_fault, figures=part_figures)

if __name__ == "__main__":
    sel = sys.argv[1:] or list(PARTS)
    for name in sel:
        t0 = time.time()
        print(f"[E19] {name}")
        PARTS[name]()
        print(f"   ({time.time() - t0:.0f} s)")
