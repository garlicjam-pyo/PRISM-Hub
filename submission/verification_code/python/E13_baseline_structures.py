"""[E13] 기준 구조 ③′·④ 평균모델과 1차 비교(보고서 이후 추가 검증).

■ 목적
  H5(기준 구조 대비 이점, 보고서 8.6절)의 비교 대상인 창 조정 변형 ③′와 비조정 구조 ④를 PRISM-Hub(③)와
  같은 경계·같은 평균모델 가정으로 구성하고, 정적 운전 범위·동특성·안정성·Stage B 부담을 같은 시험으로
  비교한다. 손실·반도체 수·정격 VA의 정량 비교(H5 1차 판정)는 이 모델 위에서 이어서 수행한다.

■ 왜 필요한가
  400±8 V 정밀 조정은 외부 요구가 아니라 고정이득 Stage C와 B_420 부품 선택에서 생기는 파생 요구다(docs/14 D1).
  따라서 Stage B의 가치는 "조정하지 않는 구조(④)"와 "상한만 제한하는 구조(③′)"보다 나은지로만 입증된다.
  비교가 공정하려면 세 구조가 같은 Stage A·경로 임피던스·버스 커패시터·부하 계약·시험 스텝을 써야 하고,
  ③ 쪽만 상세 검증된 상태에서는 그 비교가 성립하지 않는다.

■ 비교 구조와 모델 (공통: Stage A 이상 2:1 + 경로 R 13.2 mΩ·L 1.5 µH, 버스 C_b 400 µF, 정전력 부하)
  ③  PRISM-Hub: 버스 400 V 조정. Stage B 6상태 평균모델 + 채택 제어기(E5–E7 결과를 그대로 인용)
  ③′ 창 조정 변형: 버스 = min(V_A, 410 V). V_A > 410 V(배터리 약 820 V 초과)에서만 Stage B가 410 V로 조정하고,
      그 아래에서는 직렬 포트를 바이패스(스위치로 단락, Stage B 정지)해 버스 = V_A가 된다.
      - 조정 구간: ③과 같은 플랜트·제어기 구조·이득, 기준전압만 410 V
      - 바이패스 구간: ④와 같은 2상태 모델(직렬 포트 단락)
  ④  비조정 구조: Stage A 출력 V_A에 400 V 부하를 직접 연결. 2상태 모델(감쇠기를 두면 3상태)
        L di/dt = V_bat/2 − R·i − v_b,   C_b dv_b/dt = i − P/v_b − (v_b − v_d)/R_d,   C_d dv_d/dt = (v_b − v_d)/R_d
      48 V는 광입력 Stage C가 조정한다(여기서는 Stage C 입력 범위만 계산).

■ 구성
  static    정적 운전 범위: V_bat 632·640–920 V × P −3.2–25 kW(200 W 간격). 버스 범위, 직렬전압, Stage B 링크
            전력, 경로전류, 고정이득(400/48) 48 V 출력과 Stage C 필요 조정비, 부품 전압 등급(B_420/B_470),
            ③′ 모드 경계(배터리 전압 구간)
  window    ③′ 조정 구간(830·860·920 V)의 Tier-1·Tier-2 동특성: 공칭·지연 +3.0 µs(3개 전압),
            단일 변수 공차 16종(830·920 V) — 456건
  unreg     ④(및 ③′ 바이패스 구간)의 Tier-1·Tier-2 동특성: 7개 전압 × 공칭·L·C_b·R ±10 %·R ×0.5 — 672건
  damping   ④·③′ 바이패스의 경로전류 과도를 줄이는 버스 병렬 RC 감쇠기(C_d = n·C_b, n = 0.5–4) 설계와
            Tier-1·Tier-2 × 공차(감쇠기 R_d·C_d ±10 % 포함) 판정 — n별 1,008건
  stability ④·③′ 바이패스의 정전력 부하 소신호 안정성: 고유값·감쇠비 지도(공차 27조합 + R ×0.5),
            안정 한계 버스 커패시턴스
  figures   그림(정적 버스 범위, 대표 과도 비교)
  summary   세 구조 비교표(H5 1차 비교 입력)

■ 판정
  ③·③′ 조정 구간: E5와 같은 Tier 기준을 기준전압 V_ref(400 또는 410 V)로 적용. Tier-2 대역은
        [V_ref − 16, min(V_ref + 16, 420)] V(③′는 B_420 절대 상한 420 V를 넘을 수 없음)
  ④·③′ 바이패스: 조정 대상이 없으므로 서비스 창으로 판정 — 버스 ∈ [260 V(조사한 부하 하한 최댓값),
        470 V(B_470)], ③′ 바이패스 구간은 ≤ 420 V(B_420). 경로전류 Tier-1 ≤ 90 A·Tier-2 ≤ 93.75 A,
        마지막 1 ms 버스 변동 ≤ 0.1 V(감쇠 확인). 스텝 전 값 대비 과도 편차와 정착시간(±0.5 V)을 함께 기록
  모든 구조 공통: 버스 정적 범위로 Stage C 필요 조정비(최대/최소 입력)와 부품 전압 등급을 계산

■ 실행   python E13_baseline_structures.py                 (전체, 2코어 약 15분)
         python E13_baseline_structures.py static unreg damping stability summary
■ 결과   results/E13/*.json, results/E13/E13_*.png

■ 한계
  평균모델 비교다. Stage A의 출력 임피던스는 R·L로만 표현했고(세 구조 공통), 부하는 이상 정전력 부하다.
  ③′의 바이패스 스위치·모드 전환 과도, Stage C 조정형 설계, 손실·반도체 수·정격 VA 비교는 포함하지 않는다.
"""
import sys
import time
from dataclasses import replace
from multiprocessing import Pool

import numpy as np

from model_stage_b import equilibrium, steady_feasible, simulate
from controller_reference import NOMINAL, assess
from controller_adopted import StageBController, K_ADOPTED, CP
from stage_b_tests import (T1_STEPS, T2_STEPS, V_ALL, T1_LIMIT_A, T2_LIMIT_A, TAIL_IH_PP_A, TAIL_M_PP,
                           param_sets)
from E4_requirements import V_CAP, N_STAGE_C, ISO21498_B420, ISO21498_B470, ISO21780_48V, COMPONENTS
from common import save_json, load_json, verdict, workers, outdir, RESULTS

T0 = 1e-3                                   # 스텝 시각
DURATION = .02                              # 시험 길이 20 ms
LOAD_MIN_V = max(c["vmin"] for c in COMPONENTS if "DC/DC" not in c["name"])   # 400 V 부하 입력 하한의 최댓값(260 V)
V_GUAR = (640., 920.)                       # 보장 배터리 전압 범위
V_STATIC = [632.] + [float(v) for v in range(640, 921, 5)]
P_STATIC = np.arange(-3200., 25000.1, 200.)
P_TABLE = [-3200., 0., 5000., 15000., 25000.]
V_WIN_ALL = [830., 860., 920.]              # ③′ 조정 구간 시험 전압(V_A > 410 V가 모든 부하에서 성립)
V_WIN_TOL = [830., 920.]
UNREG_SETS = ["nominal", "Lx0.9", "Lx1.1", "Cbx0.9", "Cbx1.1", "Rx0.9", "Rx1.1", "Rx0.5"]
SETTLE_BAND_V = .5

CPW = replace(CP, vref=V_CAP)               # ③′ 제어기 공칭 파라미터(기준전압만 410 V)


# ----------------------------------------------------------------------------------------------
# 정적 운전점
# ----------------------------------------------------------------------------------------------
def va_exact(vbat, power, R=NOMINAL.R):
    """④·③′ 바이패스 정상점: V_A = V_bat/2 − R·P/V_A 의 큰 근(정전력 부하, 회생 P < 0 포함)."""
    e = np.asarray(vbat, float) / 2
    return (e + np.sqrt(e * e - 4 * R * np.asarray(power, float))) / 2


def point_regulated(vbat, power, vref):
    """③(vref 400)·③′ 조정 구간(vref 410)의 정상점. 평균모델 평형점과 같다."""
    p = replace(NOMINAL, vref=vref)
    x, u = equilibrium(vbat, power, p)
    return dict(bus_V=float(x[2]), path_A=float(x[0]), series_V=float(x[1]), modulation=float(u[0]),
                link_A=float(x[5]), link_W=float(x[4] * x[5]), feasible=bool(steady_feasible(vbat, power, p, control_reserve=False)),
                stage_b_active=True)


def point(structure, vbat, power):
    if structure == "3":
        return point_regulated(vbat, power, 400.)
    va = float(va_exact(vbat, power))
    if structure == "3w" and va > V_CAP:
        return point_regulated(vbat, power, V_CAP)
    return dict(bus_V=va, path_A=power / va, series_V=0., modulation=0., link_A=0., link_W=0., feasible=True,
                stage_b_active=False)


def voltage_class(vmax):
    return "B_420" if vmax <= ISO21498_B420 else ("B_470" if vmax <= ISO21498_B470 else "B_470 초과")


def part_static():
    print("   정적 운전점: V_bat 632·640–920 V(5 V 간격) × P −3.2–25 kW(200 W 간격)")
    names = {"3": "③ PRISM-Hub(400 V 조정)", "3w": "③′ 창 조정(≤ 410 V)", "4": "④ 비조정(버스 = V_A)"}
    out, table = {}, []
    for s, label in names.items():
        pts = [(v, P, point(s, v, P)) for v in V_STATIC for P in P_STATIC]
        g = [(v, P, d) for v, P, d in pts if V_GUAR[0] <= v <= V_GUAR[1]]
        bus = np.array([d["bus_V"] for _, _, d in g])
        vs = np.array([d["series_V"] for _, _, d in g]); lw = np.array([d["link_W"] for _, _, d in g])
        ip = np.array([d["path_A"] for _, _, d in g])
        act = [v for v, _, d in pts if d["stage_b_active"]]
        ratio = bus.max() / bus.min()
        v48 = bus / N_STAGE_C
        o = dict(label=label, bus_V=[bus.min(), bus.max()], series_V=[vs.min(), vs.max()],
                 link_W_max=float(np.abs(lw).max()), link_W_max_at=None, path_A_max=float(np.abs(ip).max()),
                 v48_fixed_gain_V=[v48.min(), v48.max()],
                 v48_fixed_gain_in_iso21780=bool(v48.min() >= ISO21780_48V[0] and v48.max() <= ISO21780_48V[1]),
                 stage_c_input_ratio=float(ratio), stage_c_regulation_pm_pct=float((ratio - 1) / (ratio + 1) * 100),
                 voltage_class_static=voltage_class(bus.max()),
                 all_points_feasible=bool(all(d["feasible"] for _, _, d in g)),
                 stage_b_active_vbat=[min(act), max(act)] if act else None)
        k = int(np.argmax(np.abs(lw))); o["link_W_max_at"] = dict(vbat=g[k][0], power=g[k][1])
        # 배터리 전압별 버스 범위(그림·표용)
        o["bus_by_vbat"] = [dict(vbat=v, bus_min=min(d["bus_V"] for vv, _, d in pts if vv == v),
                                 bus_max=max(d["bus_V"] for vv, _, d in pts if vv == v)) for v in V_STATIC]
        out[s] = o
        print(f"   {label}: 버스 {bus.min():.1f}–{bus.max():.1f} V, 직렬 {vs.min():+.2f}…{vs.max():+.2f} V, "
              f"링크 최대 {o['link_W_max'] / 1e3:.2f} kW @ {o['link_W_max_at']['vbat']:.0f} V, "
              f"고정이득 48 V {v48.min():.1f}–{v48.max():.1f} V, Stage C 조정비 {ratio:.3f}(±{o['stage_c_regulation_pm_pct']:.1f} %), "
              f"등급 {o['voltage_class_static']}")
    for v in [632., 640., 700., 788., 820., 830., 860., 920.]:
        for P in P_TABLE:
            table.append(dict(vbat=v, power=P, **{s: point(s, v, P) for s in names}))
    # ③′ 모드 경계: V_A(P) = 410 V가 되는 배터리 전압(부하에 따라 달라짐)
    from scipy.optimize import brentq
    vb_on = {str(P): brentq(lambda v: float(va_exact(v, P)) - V_CAP, 700., 920.) for P in [-3200., 0., 25000.]}
    print(f"   ③′ 모드 경계(V_A = 410 V): V_bat {min(vb_on.values()):.2f}–{max(vb_on.values()):.2f} V "
          f"(회생 −3.2 kW {vb_on['-3200.0']:.2f}, 무부하 {vb_on['0.0']:.2f}, 25 kW {vb_on['25000.0']:.2f} V)")
    verdict("③은 보장 범위 전 운전점에서 정상점이 포트 한계 안", out["3"]["all_points_feasible"])
    verdict("③′ 조정 구간 운전점이 포트 한계 안", out["3w"]["all_points_feasible"])
    return dict(structures=out, table=table, window_mode_boundary_vbat=vb_on, v_cap=V_CAP, load_min_V=LOAD_MIN_V,
                iso21498_V=dict(B_420=ISO21498_B420, B_470=ISO21498_B470), iso21780_48V_V=ISO21780_48V,
                stage_c_ratio_fixed=N_STAGE_C, vbat_range_for_summary=V_GUAR)


# ----------------------------------------------------------------------------------------------
# 조정 구조(③·③′) 판정 — E5와 같은 기준을 기준전압 vref로 일반화
# ----------------------------------------------------------------------------------------------
def judge_reg(tier, r, vref):
    t, x, u = r["t"], r["x"], r["u"]
    post = x[t >= T0, 2]
    tail = t >= t[-1] - 1e-3
    ih_pp = float(np.ptp(x[tail, 3])); m_pp = float(np.ptp(u[tail, 0]))
    internal_ok = bool(ih_pp <= TAIL_IH_PP_A and m_pp <= TAIL_M_PP)
    peak = max(r["path_peak"], r["bridge_peak"])
    vmax_all = float(x[:, 2].max())
    if tier == 1:
        checks = dict(r["checks"])
        checks["current_90A"] = peak <= T1_LIMIT_A
    else:
        lo, hi = vref - 16, min(vref + 16, ISO21498_B420)
        checks = dict(completed=r["completed"], ports=r["within_port_limits"],
                      bus_band=bool(lo <= post.min() and post.max() <= hi),
                      final_voltage=bool(abs(x[-1, 2] - vref) <= 4), current_93p75A=peak <= T2_LIMIT_A)
    checks["internal_tail_oscillation"] = internal_ok
    checks["b420_upper"] = vmax_all <= ISO21498_B420
    return dict(path_peak=r["path_peak"], bridge_peak=r["bridge_peak"], link_peak=r["link_peak"],
                dab_power_peak=r["dab_power_peak"], droop=r["droop"], vbus_min_post=float(post.min()),
                vbus_max_post=float(post.max()), vbus_max_all=vmax_all, dev_max=float(np.max(np.abs(post - vref))),
                recovery_s=r["recovery_s"], tail_ripple_V=r["tail_ripple_V"], modulation_peak=r["modulation_peak"],
                series_peak=r["series_peak"], series_min=float(x[:, 1].min()), series_max=float(x[:, 1].max()), vlink_min=r["vlink_min"],
                tail_ih_pp_A=ih_pp, tail_m_pp=m_pp, ports_violated=[k for k, v in r["violations"].items() if v],
                failed=[k for k, v in checks.items() if not v], pass_=bool(all(checks.values())))


def run_window(job):
    """③′ 조정 구간 1건: 채택 제어기(이득·예측 구조 동일), 기준전압 410 V."""
    tier, name, vbat, a, b, p = job
    p = replace(p, vref=V_CAP)
    dt = 1e-7 if abs(p.delay / 2e-7 - round(p.delay / 2e-7)) > 1e-9 else 2e-7
    c = StageBController(K_ADOPTED, CPW, vbat, predict=True)
    r = simulate(vbat, a, b, p=p, K=K_ADOPTED, control_p=CPW, duration=DURATION, dt=dt, keep_trace=True, controller=c)
    r.update(assess(r["t"], r["x"], T0, r["completed"], r["within_port_limits"], vref=V_CAP))
    return dict(tier=tier, set=name, vbat=vbat, p0=a, p1=b, **judge_reg(tier, r, V_CAP))


def window_jobs():
    sets, tol = param_sets()
    js = []
    for v in V_WIN_ALL:
        for name, p in sets.items():
            js += [(1, name, v, a, b, p) for a, b in T1_STEPS] + [(2, name, v, a, b, p) for a, b in T2_STEPS]
    for v in V_WIN_TOL:
        for name, p in tol.items():
            js += [(1, name, v, a, b, p) for a, b in T1_STEPS] + [(2, name, v, a, b, p) for a, b in T2_STEPS]
    return js


def summarize_reg(rows):
    s = {}
    for key, sel in [("T1", lambda r: r["tier"] == 1 and r["set"] != "delay+3.0us"),
                     ("T1_delay", lambda r: r["tier"] == 1 and r["set"] == "delay+3.0us"),
                     ("T2", lambda r: r["tier"] == 2 and r["set"] != "delay+3.0us"),
                     ("T2_delay", lambda r: r["tier"] == 2 and r["set"] == "delay+3.0us")]:
        rr = [r for r in rows if sel(r)]
        if not rr:
            continue
        w = max(rr, key=lambda r: max(r["path_peak"], r["bridge_peak"]))
        s[key] = dict(total=len(rr), passed=sum(r["pass_"] for r in rr),
                      max_current_A=max(max(r["path_peak"], r["bridge_peak"]) for r in rr),
                      worst=dict(vbat=w["vbat"], set=w["set"], p0=w["p0"], p1=w["p1"]),
                      max_dev_V=max(r["dev_max"] for r in rr) if "dev_max" in rr[0] else None,
                      vbus_post_V=[min(r["vbus_min_post"] for r in rr), max(r["vbus_max_post"] for r in rr)],
                      max_series_V=max(r["series_peak"] for r in rr),
                      series_pos_max_V=max(r.get("series_max", 0.) for r in rr) if "series_max" in rr[0] else None,
                      max_link_W=max(r["dab_power_peak"] for r in rr),
                      fails=[(r["set"], r["vbat"], r["p0"], r["p1"], r["failed"]) for r in rr if not r["pass_"]][:12])
    return s


def part_window():
    js = window_jobs()
    print(f"   ③′ 조정 구간(V_ref 410 V): {len(js)}건, 작업자 {workers()}")
    with Pool(workers()) as pool:
        rows = pool.map(run_window, js, chunksize=4)
    save_json("E13", "window_rows", dict(rows=rows))          # 요약 전 원자료(요약 단계 오류 시 재계산 방지)
    s = summarize_reg(rows)
    for k, v in s.items():
        print(f"   {k}: {v['passed']}/{v['total']}, 최대 전류 {v['max_current_A']:.2f} A, 버스 {v['vbus_post_V'][0]:.2f}–{v['vbus_post_V'][1]:.2f} V, "
              f"직렬 {-v['max_series_V']:.1f}…{v['series_pos_max_V']:+.1f} V, 링크 최대 {v['max_link_W'] / 1e3:.2f} kW" +
              (f", 실패 {v['fails'][:3]}" if v["fails"] else ""))
    verdict("③′ 조정 구간 Tier-1 전부 통과", all(r["pass_"] for r in rows if r["tier"] == 1))
    verdict("③′ 조정 구간 Tier-2 전부 통과(B_420 상한 포함)", all(r["pass_"] for r in rows if r["tier"] == 2))
    return dict(v_ref=V_CAP, voltages_all_sets=V_WIN_ALL, voltages_tolerance=V_WIN_TOL, summary=s, rows=rows)


# ----------------------------------------------------------------------------------------------
# 비조정 구조(④·③′ 바이패스): 2상태 모델을 사례 벡터로 한 번에 적분
# ----------------------------------------------------------------------------------------------
def unreg_params(name, damper=None):
    """비조정 2상태 모델 파라미터. damper = (n, R_d): 버스에 병렬 RC 감쇠기(C_d = n·C_b, 직렬 R_d)를 둔다."""
    base = dict(L=NOMINAL.L, R=NOMINAL.R, Cb=NOMINAL.Cb, Rd=1e9, Cd=1e-9)     # 감쇠기 없음(전류 ≈ 0)
    if damper is not None:
        base["Cd"], base["Rd"] = damper[0] * NOMINAL.Cb, damper[1]
    if name != "nominal":
        field, f = name.split("x")
        base[field] *= float(f)
    return base


def integrate_unreg(cases, dt=1e-7, trace=()):
    """cases: dict(vbat, p0, p1, L, R, Cb, Rd, Cd) 목록. 명시적 중점법, 0.1 µs. trace에 든 사례는 10 µs 간격 파형을 남긴다.
    상태: 경로전류 i_p, 버스전압 v_b, 감쇠기 커패시터 전압 v_d
      L di_p/dt = V_bat/2 − R·i_p − v_b,  C_b dv_b/dt = i_p − P/v_b − (v_b − v_d)/R_d,  C_d dv_d/dt = (v_b − v_d)/R_d"""
    vbat = np.array([c["vbat"] for c in cases]); p0 = np.array([c["p0"] for c in cases], float)
    p1 = np.array([c["p1"] for c in cases], float)
    L, R, Cb, Rd, Cd = (np.array([c[k] for c in cases], float) for k in ("L", "R", "Cb", "Rd", "Cd"))
    e = vbat / 2
    vb = va_exact(vbat, p0, R); ip = p0 / vb; vd = vb.copy()
    vb0 = vb.copy(); vfin = va_exact(vbat, p1, R)
    n = int(round(DURATION / dt)); ks = int(round(T0 / dt)); ktail = int(round((DURATION - 1e-3) / dt))
    vmin = np.full(len(cases), np.inf); vmax = np.full(len(cases), -np.inf)
    vmax_all = vb.copy(); ipk = np.abs(ip)
    tmin = np.full(len(cases), np.inf); tmax = np.full(len(cases), -np.inf)
    last_out = np.zeros(len(cases)); alive = np.ones(len(cases), bool)
    tr = {i: [] for i in trace}
    P = p0
    for k in range(n):
        if k == ks:
            P = p1
        idd = (vb - vd) / Rd
        ipm = ip + .5 * dt * (e - R * ip - vb) / L
        vbm = vb + .5 * dt * (ip - P / vb - idd) / Cb
        vdm = vd + .5 * dt * idd / Cd
        idm = (vbm - vdm) / Rd
        ip = ip + dt * (e - R * ipm - vbm) / L
        vb = vb + dt * (ipm - P / vbm - idm) / Cb
        vd = vd + dt * idm / Cd
        alive &= np.isfinite(vb) & (vb > 50)
        vb = np.where(alive, vb, 50.)
        ipk = np.maximum(ipk, np.abs(ip)); vmax_all = np.maximum(vmax_all, vb)
        if k >= ks:
            vmin = np.minimum(vmin, vb); vmax = np.maximum(vmax, vb)
            out = np.abs(vb - vfin) > SETTLE_BAND_V
            last_out = np.where(out, (k + 1) * dt - T0, last_out)
        if k >= ktail:
            tmin = np.minimum(tmin, vb); tmax = np.maximum(tmax, vb)
        if trace and k % 100 == 0:
            for i in trace:
                tr[i].append(((k + 1) * dt, vb[i], ip[i]))
    return [dict(vbus0=float(vb0[i]), vbus_final_eq=float(vfin[i]), vbus_end=float(vb[i]),
                 vbus_min_post=float(vmin[i]), vbus_max_post=float(vmax[i]), vbus_max_all=float(vmax_all[i]),
                 dev_from_pre_V=float(max(vb0[i] - vmin[i], vmax[i] - vb0[i])),
                 overshoot_from_final_V=float(max(vfin[i] - vmin[i], vmax[i] - vfin[i]) - abs(vfin[i] - vb0[i])),
                 settle_s=float(last_out[i]), path_peak=float(ipk[i]), tail_ripple_V=float(tmax[i] - tmin[i]),
                 completed=bool(alive[i])) for i in range(len(cases))], {i: np.array(v) for i, v in tr.items()}


def judge_unreg(tier, r, upper):
    lim = T1_LIMIT_A if tier == 1 else T2_LIMIT_A
    checks = dict(completed=r["completed"], path_rating=r["path_peak"] <= NOMINAL.path_max,
                  current=r["path_peak"] <= lim,
                  window=bool(r["vbus_min_post"] >= LOAD_MIN_V and r["vbus_max_all"] <= upper),
                  final_1ms_ripple=r["tail_ripple_V"] <= .1)
    return dict(failed=[k for k, v in checks.items() if not v], pass_=bool(all(checks.values())))


def unreg_cases(sets=UNREG_SETS, damper=None, voltages=V_ALL):
    cs = []
    for v in voltages:
        for name in sets:
            for tier, steps in ((1, T1_STEPS), (2, T2_STEPS)):
                for a, b in steps:
                    cs.append(dict(tier=tier, set=name, vbat=float(v), p0=float(a), p1=float(b), **unreg_params(name, damper)))
    return cs


def unreg_rows(cs, res):
    rows = []
    for c, r in zip(cs, res):
        # ③′는 V_A(P) ≤ 410 V인 전압에서 바이패스(④와 같은 동특성), 상한은 B_420
        bypass_3w = bool(va_exact(c["vbat"], -3200.) <= V_CAP)
        row = dict(c, **r)
        row["structure4"] = judge_unreg(c["tier"], r, ISO21498_B470)
        if bypass_3w:
            row["structure3w_bypass"] = judge_unreg(c["tier"], r, ISO21498_B420)
        rows.append(row)
    return rows


def unreg_summary(rows, sensitivity_sets=("Rx0.5",)):
    s = {}
    for key, tiers in (("T1", (1,)), ("T2", (2,))):
        for nm, sel in (("4", lambda r: True), ("3w_bypass", lambda r: "structure3w_bypass" in r)):
            rr = [r for r in rows if r["tier"] in tiers and sel(r) and r["set"] not in sensitivity_sets]
            jk = "structure4" if nm == "4" else "structure3w_bypass"
            w = max(rr, key=lambda r: r["dev_from_pre_V"])
            wi = max(rr, key=lambda r: r["path_peak"])
            s[f"{nm}_{key}"] = dict(total=len(rr), passed=sum(r[jk]["pass_"] for r in rr),
                                     max_current_A=wi["path_peak"],
                                     worst_current=dict(vbat=wi["vbat"], set=wi["set"], p0=wi["p0"], p1=wi["p1"]),
                                     vbus_post_V=[min(r["vbus_min_post"] for r in rr), max(r["vbus_max_all"] for r in rr)],
                                     max_dev_from_pre_V=w["dev_from_pre_V"],
                                     worst_dev=dict(vbat=w["vbat"], set=w["set"], p0=w["p0"], p1=w["p1"]),
                                     max_overshoot_from_final_V=max(r["overshoot_from_final_V"] for r in rr),
                                     max_settle_ms=max(r["settle_s"] for r in rr) * 1e3,
                                     max_tail_ripple_V=max(r["tail_ripple_V"] for r in rr),
                                     fail_kinds=sorted({f for r in rr for f in r[jk]["failed"]}),
                                     fails=[(r["set"], r["vbat"], r["p0"], r["p1"], r[jk]["failed"]) for r in rr if not r[jk]["pass_"]][:12])
    for sname in sensitivity_sets:
        rr = [r for r in rows if r["set"] == sname]
        if rr:
            s[f"4_{sname}"] = dict(total=len(rr), passed=sum(r["structure4"]["pass_"] for r in rr),
                                   max_current_A=max(r["path_peak"] for r in rr),
                                   max_dev_from_pre_V=max(r["dev_from_pre_V"] for r in rr),
                                   max_settle_ms=max(r["settle_s"] for r in rr) * 1e3,
                                   max_tail_ripple_V=max(r["tail_ripple_V"] for r in rr))
    return s


def print_unreg(s):
    for k, v in s.items():
        print(f"   {k}: {v['passed']}/{v['total']}, 최대 경로전류 {v['max_current_A']:.2f} A, 스텝 전 대비 최대 편차 {v['max_dev_from_pre_V']:.2f} V, "
              f"정착(±{SETTLE_BAND_V} V) 최대 {v['max_settle_ms']:.2f} ms" +
              (f", 버스 {v['vbus_post_V'][0]:.1f}–{v['vbus_post_V'][1]:.1f} V, 실패 유형 {v['fail_kinds']}" if "vbus_post_V" in v else ""))


def part_unreg():
    cs = unreg_cases()
    print(f"   ④ 비조정(및 ③′ 바이패스): {len(cs)}건 동시 적분(0.1 µs)")
    res, _ = integrate_unreg(cs)
    rows = unreg_rows(cs, res)
    s = unreg_summary(rows)
    print_unreg(s)
    verdict("④ Tier-1·Tier-2 서비스 창(260–470 V)·전류·감쇠 판정 통과",
            all(r["structure4"]["pass_"] for r in rows if r["set"] != "Rx0.5"))
    verdict("④ 버스전압은 서비스 창(260–470 V) 안(전류 판정 제외)",
            all("window" not in r["structure4"]["failed"] for r in rows))
    verdict("③′ 바이패스 구간이 B_420 상한(420 V) 안", all("window" not in r["structure3w_bypass"]["failed"] for r in rows
                                                       if "structure3w_bypass" in r))
    return dict(sets=UNREG_SETS, settle_band_V=SETTLE_BAND_V, load_min_V=LOAD_MIN_V, summary=s, rows=rows)


DAMP_N = [.5, 1., 2., 3., 4.]
DAMP_SETS = UNREG_SETS + ["Rdx0.9", "Rdx1.1", "Cdx0.9", "Cdx1.1"]


def part_damping():
    """④·③′ 바이패스의 경로전류 과도를 줄이는 버스 병렬 RC 감쇠기(C_d = n·C_b, 직렬 R_d) 설계.
    1) n별로 R_d를 쓸어 최악 사례(632 V, 1→25 kW, 공칭)의 경로전류 피크가 가장 작은 R_d를 고른다.
    2) 고른 (n, R_d)로 Tier-1·Tier-2 × 공차(L·C_b·R·R_d·C_d ±10 %) 격자를 판정한다."""
    r0 = np.sqrt(NOMINAL.L / NOMINAL.Cb)
    grid = r0 * np.logspace(-1, 1, 41)
    cs = [dict(vbat=632., p0=1000., p1=25000., **unreg_params("nominal", (n, rd))) for n in DAMP_N for rd in grid]
    res, _ = integrate_unreg(cs)
    designs = []
    for i, n in enumerate(DAMP_N):
        pk = [res[i * len(grid) + j]["path_peak"] for j in range(len(grid))]
        j = int(np.argmin(pk))
        designs.append(dict(n=n, Cd_uF=n * NOMINAL.Cb * 1e6, Rd_ohm=float(grid[j]), Rd_over_R0=float(grid[j] / r0),
                            worst_case_peak_A=float(pk[j]), sweep=[[float(g), float(p)] for g, p in zip(grid, pk)]))
        print(f"   n = {n}: C_d {n * NOMINAL.Cb * 1e6:.0f} µF, R_d {grid[j] * 1e3:.1f} mΩ(R₀의 {grid[j] / r0:.2f}배), "
              f"632 V 1→25 kW 경로전류 피크 {pk[j]:.1f} A")
    out = []
    for d in designs:
        cs = unreg_cases(DAMP_SETS, (d["n"], d["Rd_ohm"]))
        res, _ = integrate_unreg(cs)
        rows = unreg_rows(cs, res)
        s = unreg_summary(rows)
        ok = all(r["structure4"]["pass_"] for r in rows if r["set"] != "Rx0.5")
        print(f"   n = {d['n']}: ④ T1 {s['4_T1']['passed']}/{s['4_T1']['total']}, T2 {s['4_T2']['passed']}/{s['4_T2']['total']}, "
              f"최대 경로전류 T1 {s['4_T1']['max_current_A']:.1f} A·T2 {s['4_T2']['max_current_A']:.1f} A, "
              f"R ×0.5 {s['4_Rx0.5']['passed']}/{s['4_Rx0.5']['total']}({s['4_Rx0.5']['max_current_A']:.1f} A)")
        out.append(dict(design={k: v for k, v in d.items() if k != "sweep"}, all_pass=ok, summary=s,
                        fails=[(r["tier"], r["set"], r["vbat"], r["p0"], r["p1"], r["structure4"]["failed"]) for r in rows
                               if not r["structure4"]["pass_"]][:20]))
    passing = [o["design"]["n"] for o in out if o["all_pass"]]
    nmin = min(passing) if passing else None
    verdict("버스 RC 감쇠기로 ④의 Tier-1·Tier-2 전류 기준을 공차 포함 만족할 수 있다", nmin is not None,
            f"최소 C_d = {nmin} × C_b" if nmin is not None else "시험한 n 범위에서 없음")
    return dict(R0_ohm=r0, sets=DAMP_SETS, designs=designs, results=out, n_min_all_pass=nmin)


# ----------------------------------------------------------------------------------------------
# 정전력 부하 소신호 안정성(④·③′ 바이패스)
# ----------------------------------------------------------------------------------------------
def unreg_eig(vbat, power, L, R, Cb):
    """평형점 선형화: A = [[−R/L, −1/L], [1/C_b, P/(V²·C_b)]]. 정전력 부하는 음의 증분 컨덕턴스 −P/V²."""
    v = float(va_exact(vbat, power, R))
    A = np.array([[-R / L, -1 / L], [1 / Cb, power / (v * v * Cb)]])
    lam = np.linalg.eigvals(A)
    l = lam[np.argmax(lam.imag)]
    zeta = float(-l.real / abs(l))
    return dict(vbus=v, eig=[[float(x.real), float(x.imag)] for x in lam], zeta=zeta, f_hz=float(abs(l.imag) / (2 * np.pi)),
                cb_min_F=float(L * max(power, 0) / (R * v * v)))


def part_stability():
    combos = [(fl, fc, fr) for fl in (.9, 1., 1.1) for fc in (.9, 1., 1.1) for fr in (.9, 1., 1.1)]
    vs = [632.] + [float(v) for v in range(640, 921, 10)]
    Ps = np.unique(np.r_[np.arange(-3200., 25000., 400.), 25000.])
    out = {}
    for label, cset in (("tolerance27", combos), ("R_half", [(1., 1., .5)]), ("nominal", [(1., 1., 1.)])):
        worst = None; maxcb = None
        for fl, fc, fr in cset:
            for v in vs:
                for P in Ps:
                    d = unreg_eig(v, P, NOMINAL.L * fl, NOMINAL.R * fr, NOMINAL.Cb * fc)
                    if worst is None or d["zeta"] < worst["zeta"]:
                        worst = dict(d, vbat=v, power=float(P), L_scale=fl, Cb_scale=fc, R_scale=fr)
                    if maxcb is None or d["cb_min_F"] > maxcb["cb_min_F"]:
                        maxcb = dict(cb_min_F=d["cb_min_F"], vbat=v, power=float(P), L_scale=fl, R_scale=fr)
        out[label] = dict(min_zeta=worst, max_cb_min=maxcb)
        print(f"   {label}: 최소 감쇠비 {worst['zeta']:.4f} @ {worst['vbat']:.0f} V {worst['power'] / 1e3:.1f} kW "
              f"(L×{worst['L_scale']}, C_b×{worst['Cb_scale']}, R×{worst['R_scale']}), {worst['f_hz'] / 1e3:.2f} kHz; "
              f"안정 한계 C_b {maxcb['cb_min_F'] * 1e6:.1f} µF")
    # 공칭 감쇠비 지도(배터리 전압 × 부하)
    zmap = [dict(vbat=v, power=float(P), **{k: unreg_eig(v, P, NOMINAL.L, NOMINAL.R, NOMINAL.Cb)[k] for k in ("zeta", "f_hz")})
            for v in (640., 788., 920.) for P in (-3200., 0., 15000., 25000.)]
    # 무부하·정전력 부하 성분 분해: 2ζω₀ ≈ R/L − P/(V²·C_b)
    v = float(va_exact(640., 25000.))
    decomp = dict(R_over_L=NOMINAL.R / NOMINAL.L, cpl_term=25000. / (v * v * NOMINAL.Cb),
                  omega0=1 / np.sqrt(NOMINAL.L * NOMINAL.Cb), vbus=v)
    print(f"   640 V 25 kW 분해: R/L {decomp['R_over_L']:.0f} s⁻¹, 정전력 부하 항 {decomp['cpl_term']:.0f} s⁻¹, "
          f"ω₀ {decomp['omega0']:.0f} rad/s")
    verdict("④·③′ 바이패스: 공차 27조합 전 운전점에서 소신호 안정(감쇠비 > 0)", out["tolerance27"]["min_zeta"]["zeta"] > 0)
    return dict(results=out, zeta_map=zmap, decomposition_640V_25kW=decomp,
                note="경로 저항 R(13.2 mΩ, Stage A 출력저항 포함)이 감쇠의 거의 전부를 제공한다. 실제 Stage A 출력 임피던스와 부하 입력 필터의 상호작용은 포함하지 않는다.")


# ----------------------------------------------------------------------------------------------
# 그림
# ----------------------------------------------------------------------------------------------
def part_figures():
    from plotstyle import korean, COLOR as C
    from stage_b_tests import sim
    plt = korean()
    st = load_json("E13", "static")["structures"]
    dm = load_json("E13", "damping")
    dsel = next(o["design"] for o in dm["results"] if o["design"]["n"] == dm["n_min_all_pass"])
    fig, ax = plt.subplots(2, 2, figsize=(8.6, 6.0))
    ax = ax.ravel()
    for s, col in (("4", C["orange"]), ("3w", C["green"]), ("3", C["blue"])):
        b = st[s]["bus_by_vbat"]
        v = [x["vbat"] for x in b]
        ax[0].fill_between(v, [x["bus_min"] for x in b], [x["bus_max"] for x in b], color=col, alpha=.35, lw=0)
        ax[0].plot(v, [x["bus_max"] for x in b], color=col, lw=1, label=st[s]["label"])
    ax[0].axhline(ISO21498_B420, color=C["red"], ls=":", lw=.9); ax[0].axhline(ISO21498_B470, color=C["red"], ls="--", lw=.9)
    ax[0].text(645, 422, "B_420 상한", fontsize=7, color=C["red"]); ax[0].text(645, 472, "B_470 상한", fontsize=7, color=C["red"])
    ax[0].set_xlim(632, 920); ax[0].set_ylim(300, 485); ax[0].set_xlabel("배터리 전압 (V)"); ax[0].set_ylabel("보조버스 (V)")
    ax[0].set_title("(a) 정적 버스 범위(부하 −3.2–25 kW)"); ax[0].legend(loc="lower right", fontsize=6.5)
    # (b)(c) 640 V Tier-1 15→25 kW: ③ vs ④(= ③′ 바이패스), ④ + RC 감쇠기
    r3 = sim(640., 15000, 25000, NOMINAL)
    cs = [dict(vbat=640., p0=15000., p1=25000., **unreg_params("nominal")),
          dict(vbat=640., p0=15000., p1=25000., **unreg_params("nominal", (dsel["n"], dsel["Rd_ohm"]))),
          dict(vbat=920., p0=25000., p1=1000., **unreg_params("nominal"))]
    _, tr = integrate_unreg(cs, trace=(0, 1, 2))
    lab4d = f"④ + RC 감쇠기(C_d = {dsel['n']:g}·C_b)"
    ax[1].plot((r3["t"] - T0) * 1e3, r3["x"][:, 2] - 400, color=C["blue"], lw=1, label="③ (400 V 조정)")
    ax[1].plot((tr[0][:, 0] - T0) * 1e3, tr[0][:, 1] - tr[0][0, 1], color=C["orange"], lw=1, label="④·③′ 바이패스")
    ax[1].plot((tr[1][:, 0] - T0) * 1e3, tr[1][:, 1] - tr[1][0, 1], color=C["gray"], lw=1, ls="--", label=lab4d)
    ax[1].set_xlim(-.2, 2.5); ax[1].set_xlabel("스텝 후 시간 (ms)"); ax[1].set_ylabel("스텝 전 대비 버스 변화 (V)")
    ax[1].set_title("(b) 640 V, 15→25 kW(Tier-1): 버스전압"); ax[1].legend(fontsize=6.5, loc="lower right")
    ax[2].plot((r3["t"] - T0) * 1e3, r3["x"][:, 0], color=C["blue"], lw=1, label="③ 경로전류")
    ax[2].plot((tr[0][:, 0] - T0) * 1e3, tr[0][:, 2], color=C["orange"], lw=1, label="④ Stage A 출력전류")
    ax[2].plot((tr[1][:, 0] - T0) * 1e3, tr[1][:, 2], color=C["gray"], lw=1, ls="--", label=lab4d)
    ax[2].axhline(T1_LIMIT_A, color=C["red"], ls=":", lw=.9); ax[2].axhline(NOMINAL.path_max, color=C["red"], ls="--", lw=.9)
    ax[2].set_xlim(-.2, 2.5); ax[2].set_ylim(40, 110); ax[2].set_xlabel("스텝 후 시간 (ms)"); ax[2].set_ylabel("전류 (A)")
    ax[2].set_title("(c) 640 V, 15→25 kW(Tier-1): 경로전류"); ax[2].legend(fontsize=6.5, loc="lower right")
    # (d) 920 V Tier-2 25→1 kW: ③, ③′(410 V 조정), ④
    r3b = sim(920., 25000, 1000, NOMINAL)
    pw = replace(NOMINAL, vref=V_CAP)
    rw = simulate(920., 25000, 1000, p=pw, K=K_ADOPTED, control_p=CPW, duration=DURATION, dt=2e-7, keep_trace=True,
                  controller=StageBController(K_ADOPTED, CPW, 920., predict=True))
    ax[3].plot((r3b["t"] - T0) * 1e3, r3b["x"][:, 2], color=C["blue"], lw=1, label="③")
    ax[3].plot((rw["t"] - T0) * 1e3, rw["x"][:, 2], color=C["green"], lw=1, label="③′ (410 V 조정)")
    ax[3].plot((tr[2][:, 0] - T0) * 1e3, tr[2][:, 1], color=C["orange"], lw=1, label="④")
    ax[3].axhline(ISO21498_B420, color=C["red"], ls=":", lw=.9)
    ax[3].set_xlim(-.2, 2.5); ax[3].set_ylim(395, 470); ax[3].set_xlabel("스텝 후 시간 (ms)"); ax[3].set_ylabel("보조버스 (V)")
    ax[3].set_title("(d) 920 V, 25→1 kW(Tier-2): 버스전압"); ax[3].legend(fontsize=6.5, loc="center right")
    fig.tight_layout(); fig.savefig(outdir("E13") / "E13_baseline_comparison.png"); plt.close(fig)
    print("   → 그림: results/E13/E13_baseline_comparison.png")


# ----------------------------------------------------------------------------------------------
# 비교표
# ----------------------------------------------------------------------------------------------
def part_summary():
    st = load_json("E13", "static")["structures"]
    wn = load_json("E13", "window")["summary"]
    un = load_json("E13", "unreg")["summary"]
    dm = load_json("E13", "damping")
    sb = load_json("E13", "stability")["results"]
    g3 = load_json("E5", "grid_adopted")["rows"]
    s3 = {}
    for key, tier in (("T1", 1), ("T2", 2)):
        rr = [r for r in g3 if r["tier"] == tier and r["set"] != "delay+3.0us"]
        s3[key] = dict(total=len(rr), passed=sum(r["pass_"] for r in rr),
                       max_current_A=max(max(r["path_peak"], r["bridge_peak"]) for r in rr),
                       vbus_post_V=[min(r["vbus_min_post"] for r in rr), max(r["vbus_max_post"] for r in rr)],
                       max_dev_V=max(max(400 - r["vbus_min_post"], r["vbus_max_post"] - 400) for r in rr),
                       max_series_V=max(r["series_peak"] for r in rr), max_link_W=max(r["dab_power_peak"] for r in rr))
    dsel = next(o for o in dm["results"] if o["design"]["n"] == dm["n_min_all_pass"]) if dm["n_min_all_pass"] else None
    rows = []
    for s, lab in (("3", "③"), ("3w", "③′"), ("4", "④")):
        o = st[s]
        if s == "3":
            t1, t2 = s3["T1"], s3["T2"]
            dyn = dict(T1=f"{t1['passed']}/{t1['total']}", T2=f"{t2['passed']}/{t2['total']}", T1_dev_V=t1["max_dev_V"],
                       T2_bus_V=t2["vbus_post_V"], max_current_A=max(t1["max_current_A"], t2["max_current_A"]))
        elif s == "3w":
            a1, a2, b1, b2 = wn["T1"], wn["T2"], un["3w_bypass_T1"], un["3w_bypass_T2"]
            dyn = dict(T1_active=f"{a1['passed']}/{a1['total']}", T2_active=f"{a2['passed']}/{a2['total']}",
                       T1_bypass=f"{b1['passed']}/{b1['total']}", T2_bypass=f"{b2['passed']}/{b2['total']}",
                       T1_dev_V=max(a1["max_dev_V"], b1["max_dev_from_pre_V"]),
                       T2_bus_V=[min(a2["vbus_post_V"][0], b2["vbus_post_V"][0]), max(a2["vbus_post_V"][1], b2["vbus_post_V"][1])],
                       max_current_active_A=max(a1["max_current_A"], a2["max_current_A"]),
                       max_current_bypass_A=max(b1["max_current_A"], b2["max_current_A"]),
                       series_active_V=[-max(a1["max_series_V"], a2["max_series_V"]), max(a1["series_pos_max_V"], a2["series_pos_max_V"])],
                       link_active_peak_W=max(a1["max_link_W"], a2["max_link_W"]))
        else:
            b1, b2 = un["4_T1"], un["4_T2"]
            dyn = dict(T1=f"{b1['passed']}/{b1['total']}", T2=f"{b2['passed']}/{b2['total']}", T1_dev_V=b1["max_dev_from_pre_V"],
                       T2_bus_V=b2["vbus_post_V"], max_current_A=max(b1["max_current_A"], b2["max_current_A"]),
                       with_damper=None if dsel is None else dict(
                           n=dsel["design"]["n"], Cd_uF=dsel["design"]["Cd_uF"], Rd_ohm=dsel["design"]["Rd_ohm"],
                           T1=f"{dsel['summary']['4_T1']['passed']}/{dsel['summary']['4_T1']['total']}",
                           T2=f"{dsel['summary']['4_T2']['passed']}/{dsel['summary']['4_T2']['total']}",
                           max_current_A=max(dsel["summary"]["4_T1"]["max_current_A"], dsel["summary"]["4_T2"]["max_current_A"])),
                       min_zeta=sb["tolerance27"]["min_zeta"]["zeta"])
        rows.append(dict(structure=lab, label=o["label"], bus_static_V=o["bus_V"], voltage_class=o["voltage_class_static"],
                         v48_fixed_gain_V=o["v48_fixed_gain_V"], stage_c_ratio=o["stage_c_input_ratio"],
                         stage_c_regulation_pm_pct=o["stage_c_regulation_pm_pct"], series_static_V=o["series_V"],
                         link_static_max_W=o["link_W_max"], path_static_max_A=o["path_A_max"],
                         stage_b_active_vbat=o["stage_b_active_vbat"], dynamic=dyn))
    for r in rows:
        print(f"   {r['structure']}: 버스 {r['bus_static_V'][0]:.1f}–{r['bus_static_V'][1]:.1f} V({r['voltage_class']}), "
              f"Stage C 조정비 {r['stage_c_ratio']:.3f}, 직렬 {r['series_static_V'][0]:+.1f}…{r['series_static_V'][1]:+.1f} V, "
              f"링크 {r['link_static_max_W'] / 1e3:.2f} kW, 동특성 {r['dynamic']}")
    return dict(rows=rows, structure3_dynamic=s3,
                deferred_to_H5=["운전 프로파일 가중 손실(Stage B 스위칭·도통, ③′ 바이패스 스위치, ④ 감쇠기, Stage C 조정형)",
                                "정격 VA(H-브리지·DAB·Stage C·바이패스 스위치·감쇠 커패시터)와 반도체 수",
                                "③′ 모드 전환(바이패스 ↔ 조정) 과도와 히스테리시스, 바이패스 구간 능동 감쇠 대안",
                                "기준 구조 ①(전전력 승압기 + 별도 보조전원모듈)·②(고정비 + 별도 전전력 조정기)"])


PARTS = dict(static=part_static, window=part_window, unreg=part_unreg, damping=part_damping, stability=part_stability,
             figures=part_figures, summary=part_summary)

if __name__ == "__main__":
    todo = sys.argv[1:] or list(PARTS)
    print("[E13] 기준 구조 ③′·④ 평균모델과 1차 비교")
    for name in todo:
        t0 = time.time(); print(f"-- {name}", flush=True)
        res = PARTS[name]()
        if res is not None:
            save_json("E13", name, res)
        print(f"   ({time.time() - t0:.0f} s)", flush=True)
