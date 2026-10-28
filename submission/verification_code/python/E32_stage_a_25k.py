"""[E32] Stage A 25 kHz 설계(A25)의 정상상태: 손실·영전류 스위칭·정격 첨두와 셰딩·모듈 관리기 문턱 다시 정하기.

■ 목적
  E31(docs/37)에서 Stage A 출력용량 손실이 모델보다 한 자릿수 컸다. 수정안 (나)를 택했다(2026-10-28 결정):
  위치당 C4MS008075U2 2병렬, f_r 25 kHz(L_r 865 nH, C_fly 46.9 µF, √(L/C) 유지). 이 설계 묶음은 model_stage_a.DESIGNS['A25']다.
  E24·E28의 셰딩·모듈 관리기 문턱은 원 손실 모델(위상당 고정 손실 약 15.6 W)과 150 kHz 시간 상수로 정했다. 고정 손실이
  약 30 W/위상이 되고 공진이 6배 느려지므로, 같은 규칙으로 문턱을 다시 정하고 손실 비교(E25)를 이 설계로 다시 계산한다.
  동특성(부하 계단, 충전 시작, 모듈 고장)은 E33에서 이 문턱으로 다시 판정한다.

■ 모델
  model_stage_a.set_design('A25'): 출력용량 손실 = 4·Q_oss,위치(V_A)·V_A·f_s(E31 근사), 게이트 4·E_g·f_s(E_g = 2 × 278 nC × 22 V),
  바디 다이오드 4.5 V, 적분 간격 약 20 ns(주기당 2040단계), 데드타임 소멸 처리, 무장 전 부호 없는 영교차('mag', E28 게이트).

■ 시험(design → rated → 문턱 → loss)
  design : 모듈 하나(2위상)와 위상 하나 운전, 540·800·1008 V × 모듈 전류 3–93.75 A(위상 하나는 ≤ 50 A): 손실, 위상 첨두,
           턴오프 비율, V_A 강하, 스위칭 주파수. 모듈 수 N ↔ N+1 손실 교차(E28과 같은 방법).
  rated  : 공차 표본별 정격 충전점(V_A 노드 375 A 주입, 4모듈 8위상, 640·800·920 V) 위상 첨두 → P_rated(A25, 표본)
  문턱   : 아래 규칙(실행 전에 고정)
  loss   : E15 Stage A 격자(VGRID × IGRID 2위상 + 충전 6점)를 A25로 다시 계산해 E25 비교(④ 보조, 충전, ⑤·⑥·모터 승압)를
           셰딩 문턱(이전 15 A와 새 문턱)으로 계산

■ 판정 기준과 문턱 규칙(실행 전에 고정)
  (D0) 모델 일관성: 800 V 2위상 손실이 E31 (나) 예측(위상당 도통 + 출력용량 + 게이트)과 5 % 또는 1 W 안
       (위상 전류 3·10·30 A와 충전 46.875 A; E31은 150 kHz 도통 격자 + 공식, 여기서는 직접 모의 + analyze)
  (Z)  영전류 스위칭: 2위상·위상 하나 모두 모듈 전류 ≥ 7.5 A에서 턴오프 전류/피크 ≤ 5 %, < 7.5 A에서 턴오프 전류 ≤ 1.0 A
       (E24 S1·S2와 같음). 불통과 운전점은 그 운전 방식이 쓰이지 않도록 문턱을 정한다(아래 SH2).
  (SH1) I_on = 위상 하나가 2위상보다 손실이 작거나 같고(세 전압 모두), 위상 하나의 정상 첨두가 2위상의 모듈 추가 문턱
        Im_up 정상 첨두보다 크지 않은 가장 큰 격자 전류(≤ 50 A)
  (SH2) I_off = I_on − 7 A 이하인 가장 큰 격자 전류(E24 히스테리시스 7 A). 단 2위상 (Z)가 I_off − 3 A 이상 모든 격자점에서
        성립해야 하며, 아니면 성립하는 가장 작은 값으로 올린다(E24: 2위상 12 A 이상 성립 → 15 A)
  (SH3) Ipk_on = 위상 하나의 I_on 정상 첨두 × 1.1을 올림(1 A). Ipk_on < Ipk_m이어야 함
  (MG)  모듈 관리기 Im_up 70 A·Im_dn 60 A·Ipk_m 66 A를 E28 (D1)·(D2)로 다시 판정한다. (D1) 2위상 Im_up 정상 첨두 < Ipk_m <
        P_rated(A25 공칭), (D2) 줄임 문턱 N·Im_dn ≤ 손실 교차(N ↔ N+1). 불통과면 같은 규칙을 만족하는 10 A 단위 값으로 바꾼다
        (Im_up: (D1)을 만족하는 가장 큰 값, Im_dn = Im_up − 10 A, Ipk_m = ⌈(Im_up 첨두 + P_rated)/2⌉).
  (TM)  시간 상수: 스위칭 주기에 맞춰 정한 τ(2 µs), t_dwell(100 µs), τ_m(20 µs), t_lock(20 µs), t_hold(100 µs)는
        f_r0(R1)/f_r0(A25) = 6배. 부하 변화 판단용 t_dwell_m(1 ms)은 그대로.
  (L)   보고(합격 판정 없음): ④ 보조 손실과 충전 손실, ⑤·⑥·모터 승압 대비(E25 기준값), E31 (나) 예측과의 차

■ 실행   python E32_stage_a_25k.py design rated thresholds loss figures   (2코어 약 45분)
■ 결과   results/E32/design.json, rated.json, thresholds.json, loss.json, E32_stage_a_25k.png
"""
import json
import math
import sys
from multiprocessing import Pool

import numpy as np

import model_stage_a as A
import E15_baseline_loss_rating as E15
import E25_motor_boost_comparison as E25
import E28_stage_a_modules as E28
from common import load_json, outdir, save_json, verdict, workers

EID = "E32"
DESIGN = "A25"
FR_R1 = A.FR0                                   # 원설계 공진주파수(모듈 import 시점, R1)
CA = 400e-6
GATE = "mag"
DES_V = (540., 800., 1008.)
DES_I = (3., 5., 7.5, 10., 12.5, 15., 20., 25., 30., 35., 40., 45., 50., 60., 70., 80., 93.75)
I1_MAX = 50.
I_LOW, I_ABS = 7.5, 1.0
SEEDS = E28.SEEDS
TOL = E28.TOL
MGR_R1 = dict(E28.MGR)
TM_KEYS = ("tau", "t_dwell", "tau_m", "t_lock", "t_hold")


def _init():
    A.set_design(DESIGN)


def _steady(args):
    V, nph, I = args
    A.set_design(DESIGN)
    en = [True, nph == 2]
    r = A.sim_array(N=2, Vbat=V, Iload=I, Cbus=CA, mode="zcp", ncyc=60, dead_fix=True, unarmed_stop=GATE, en=en)
    ph, bus = A.analyze(r, ncyc_last=10)
    act = ph[:nph]
    return dict(V=V, nph=nph, I=I, loss=sum(p["Ploss"] for p in act), Ipk=max(p["Ipk"] for p in act),
                zcs=max(p["zcs"] for p in act), ioff=max(p["zcs"] * p["Ipk"] for p in act), fs=float(np.mean([p["fs"] for p in act])),
                dvA=float(V / 2 - bus["Vbus"]))


def design():
    A.set_design(DESIGN)
    jobs = [(V, n, I) for V in DES_V for n in (2, 1) for I in DES_I if not (n == 1 and I > I1_MAX)]
    with Pool(workers(), initializer=_init) as p:
        rows = p.map(_steady, jobs)
    out = dict(rows=rows, cross={})
    for V in DES_V:
        r2 = sorted([r for r in rows if r["V"] == V and r["nph"] == 2], key=lambda r: r["I"])
        r1 = {r["I"]: r for r in rows if r["V"] == V and r["nph"] == 1}
        print("  %4.0f V: 모듈 전류 [A] | 2위상 손실 W / 첨두 A / 턴오프 비율 | 위상 하나 손실 / 첨두 / 비율 | V_A 강하(2위상) V, f_s kHz" % V)
        for r in r2:
            o = r1.get(r["I"])
            print("     %6.2f | %6.1f %5.1f %5.2f %% | %s | %.3f, %.2f" % (
                r["I"], r["loss"], r["Ipk"], 100 * r["zcs"],
                "%6.1f %5.1f %5.2f %%" % (o["loss"], o["Ipk"], 100 * o["zcs"]) if o else "      –     –       – ", r["dvA"], r["fs"] / 1e3))
        Ig = np.array([r["I"] for r in r2]); Pg = np.array([r["loss"] for r in r2])
        P = lambda I: float(np.interp(I, Ig, Pg))
        cr = []
        for N in (1, 2, 3):
            II = np.linspace(N * 20., min(N * 93.75, 375.), 2000)
            d = np.array([N * P(I / N) - (N + 1) * P(I / (N + 1)) for I in II])
            j = np.where(np.diff(np.sign(d)) > 0)[0]
            cr.append(float(II[j[0]]) if len(j) else None)
        out["cross"][V] = cr
        print("    손실 교차(전체 전류): 1↔2 %s, 2↔3 %s, 3↔4 %s A" % tuple("%.0f" % c if c else "–" for c in cr))
    save_json(EID, "design", out)


def _rated(args):
    V, seed = args
    A.set_design(DESIGN)
    tol, rs = (TOL, A.matlab_rng(seed)) if seed else (None, None)
    r = A.sim_array(N=8, Vbat=V, Iload=-375., Cbus=CA, mode="zcp", ncyc=80, tol=tol, rs=rs, dead_fix=True, unarmed_stop=GATE)
    ph, bus = A.analyze(r, ncyc_last=20)
    return dict(V=V, seed=seed, Ipk=max(p["Ipk"] for p in ph), Iavg=[p["Iavg"] for p in ph], zcs=max(p["zcs"] for p in ph),
                loss=sum(p["Ploss"] for p in ph))


def rated():
    jobs = [(V, s) for s in SEEDS for V in E28.RATED_V]
    with Pool(workers(), initializer=_init) as p:
        rows = p.map(_rated, jobs)
    pr = {}
    for s in SEEDS:
        rr = [x for x in rows if x["seed"] == s]
        pr[str(s)] = max(x["Ipk"] for x in rr)
        ia = np.abs(np.array(rr[1]["Iavg"]))
        print("  공차 %-4s: 정격점 위상 첨두 %s → P_rated %.1f A, 분담 최대/평균 %.3f(800 V), 8위상 손실 %s W, 턴오프 비율 최대 %.2f %%"
              % (s, ["%.1f" % x["Ipk"] for x in rr], pr[str(s)], ia.max() / ia.mean(), ["%.0f" % x["loss"] for x in rr],
                 100 * max(x["zcs"] for x in rr)))
    save_json(EID, "rated", dict(rows=rows, P_rated=pr))


def zcs_ok(r):
    return (r["zcs"] <= 0.05) if abs(r["I"]) >= I_LOW else (r["ioff"] <= I_ABS)


def thresholds():
    D = load_json(EID, "design"); R = load_json(EID, "rated")
    rows = D["rows"]; prn = R["P_rated"]["None"]
    g = lambda V, n, I: [r for r in rows if r["V"] == V and r["nph"] == n and r["I"] == I][0]
    out = {}
    # (Z)
    zbad = [dict(V=r["V"], nph=r["nph"], I=r["I"], zcs=r["zcs"], ioff=r["ioff"]) for r in rows if not zcs_ok(r)]
    out["Z_fail_points"] = zbad
    verdict("(Z) 2위상·위상 하나 턴오프(≥ 7.5 A 비율 ≤ 5 %, 아래 ≤ 1.0 A)", len(zbad) == 0, "불통과 %d점 %s" % (len(zbad), zbad[:6]))
    # (MG) 먼저 Im_up 정상 첨두
    M = dict(MGR_R1)
    pk2 = lambda I: max(float(np.interp(I, [r["I"] for r in sorted([x for x in rows if x["V"] == V and x["nph"] == 2], key=lambda x: x["I"])],
                                        [r["Ipk"] for r in sorted([x for x in rows if x["V"] == V and x["nph"] == 2], key=lambda x: x["I"])]))
                        for V in DES_V)
    cr_min = [min(D["cross"][str(V)][N] if D["cross"][str(V)][N] is not None else 1e9 for V in DES_V) for N in range(3)]
    def mg_ok(Mx):
        d1 = pk2(Mx["Im_up"]) < Mx["Ipk_m"] < prn
        d2 = all(Mx["Im_dn"] * (N + 1) <= cr_min[N] for N in range(3))
        return d1, d2
    d1, d2 = mg_ok(M)
    mg_changed = False
    if not (d1 and d2):
        mg_changed = True
        for up in range(150, 20, -10):
            Mx = dict(M, Im_up=float(up), Im_dn=float(up - 10), Ipk_m=float(math.ceil((pk2(up) + prn) / 2)))
            if all(mg_ok(Mx)):
                M = Mx; break
        d1, d2 = mg_ok(M)
    out["MG"] = dict(Im_up=M["Im_up"], Im_dn=M["Im_dn"], Ipk_m=M["Ipk_m"], pk_at_up=pk2(M["Im_up"]), P_rated=prn, cross_min=cr_min,
                     D1=d1, D2=d2, changed=mg_changed)
    verdict("(MG) E28 (D1)·(D2) %s" % ("(E28 값 그대로)" if not mg_changed else "(규칙으로 바꿈)"), d1 and d2,
            "Im_up %.0f A 첨두 %.1f < Ipk_m %.0f < P_rated %.1f A, 줄임 %s ≤ 교차 %s A" % (
                M["Im_up"], pk2(M["Im_up"]), M["Ipk_m"], prn, [M["Im_dn"] * (N + 1) for N in range(3)], ["%.0f" % c for c in cr_min]))
    # (SH1)
    pk_up = pk2(M["Im_up"])
    cand = []
    for I in [x for x in DES_I if x <= I1_MAX]:
        ok = all(g(V, 1, I)["loss"] <= g(V, 2, I)["loss"] and g(V, 1, I)["Ipk"] <= pk_up for V in DES_V)
        if ok:
            cand.append(I)
    # 가장 큰 연속 구간의 위끝(작은 전류부터 끊김 없이 성립하는 범위)
    I_on = None
    for I in [x for x in DES_I if x <= I1_MAX]:
        if I in cand:
            I_on = I
        else:
            break
    # (SH2)
    two_ok = lambda I: all(zcs_ok(g(V, 2, x)) for V in DES_V for x in DES_I if x >= I - 3.)
    grid = [x for x in DES_I if x <= I_on - 7.]
    I_off = max(grid) if grid else None
    if I_off is not None and not two_ok(I_off):
        up = [x for x in DES_I if two_ok(x) and x < I_on]
        I_off = min(up) if up else None
    # (SH3)
    pk1_on = max(g(V, 1, I_on)["Ipk"] for V in DES_V)
    Ipk_on = float(math.ceil(1.1 * pk1_on))
    sh_ok = I_on is not None and I_off is not None and Ipk_on < M["Ipk_m"]
    k = FR_R1 / A.set_design(DESIGN)
    tm = {key: MGR_R1[key] * k for key in TM_KEYS}
    MGR = dict(M, I_off=float(I_off), I_on=float(I_on), Ipk_on=Ipk_on, **tm)
    out.update(SH=dict(I_on=I_on, I_off=I_off, Ipk_on=Ipk_on, pk1_on=pk1_on, cand=cand, pk_limit=pk_up, ok=sh_ok),
               TM=dict(k=k, **tm), MGR=MGR, MGR_R1=MGR_R1)
    verdict("(SH) 셰딩 문턱", sh_ok, "I_off %s A, I_on %s A, Ipk_on %.0f A(위상 하나 I_on 첨두 %.1f A, 한도 %.1f A), 손실·첨두 조건 성립 %s"
            % (I_off, I_on, Ipk_on, pk1_on, pk_up, cand))
    print("  (TM) 시간 상수 ×%.3f: %s, t_dwell_m %.1f ms 그대로" % (k, {kk: "%.0f µs" % (v * 1e6) for kk, v in tm.items()},
                                                               MGR["t_dwell_m"] * 1e3))
    save_json(EID, "thresholds", out)


# ---------------------------------------------------------------- loss: E15 격자와 E25 비교
def _e15_point(args):
    V, iph, sign = args
    A.set_design(DESIGN)
    r = A.sim_array(N=2, Vbat=V, Iload=sign * 2 * iph, Cbus=400e-6, mode="zcp", ncyc=60, dead_fix=True, unarmed_stop=GATE)
    ph, bus = A.analyze(r)
    return dict(V=V, iph=iph, sign=sign, ploss_ph=float(np.mean([p["Ploss"] for p in ph])),
                dvA=float(V / 2 - bus["Vbus"]), Ipk=float(np.mean([p["Ipk"] for p in ph])), zcs=float(np.max([p["zcs"] for p in ph])))


class StageAs(E15.StageA):
    def __init__(self, T, I_off):
        super().__init__(T); self.I_off = I_off

    def drive(self, V, I, nph=2):
        if self.I_off and abs(I) < self.I_off:
            nph = 1
        return super().drive(V, I, nph)


def loss():
    import os
    cache = outdir(EID) / "loss_grid_raw.json"
    if cache.exists() and os.environ.get("E32_RECOMPUTE") != "1":
        res = json.loads(cache.read_text(encoding="utf-8"))
    else:
        jobs = [(V, i, 1.) for V in E15.VGRID for i in E15.IGRID] + [(V, 375. / 8, -1.) for V in E15.VGRID]
        with Pool(workers(), initializer=_init) as p:
            res = p.map(_e15_point, jobs)
        save_json(EID, "loss_grid_raw", res)
    fw = [r for r in res if r["sign"] > 0]
    T = dict(P=np.array([r["ploss_ph"] for r in fw]).reshape(len(E15.VGRID), len(E15.IGRID)),
             D=np.array([r["dvA"] for r in fw]).reshape(len(E15.VGRID), len(E15.IGRID)),
             charge={r["V"]: r for r in res if r["sign"] < 0})
    th = load_json(EID, "thresholds"); c25 = load_json("E25", "comparison"); c31 = load_json("E31", "coss")
    out = dict(grid=dict(V=E15.VGRID, I=E15.IGRID, P_phase=T["P"], dvA=T["D"], charge={str(k): v for k, v in T["charge"].items()}))
    for lab, ioff in (("none", 0.), ("shed15", 15.), ("shed_new", th["SH"]["I_off"])):
        S = StageAs(T, ioff)
        aux4, by = E25.aux_avg(lambda V, P: E15.path_struct("4", S, V, P, E15.P48)["loss"])
        ch = {f"{V:.0f}V": E15.charge_loss("4", S, V) for V in (640., 800., 920.)}
        out[lab] = dict(I_off=ioff, aux4=aux4, by_load=by, charge=ch)
    ref = dict(aux5=c25["aux"]["5"]["avg_W"], aux6=c25["aux"]["6"]["avg_W"], aux1=c25["aux"]["1"]["avg_W"],
               motor_base={k: v["motor_base"] for k, v in c25["charge"].items()},
               motor_min_Rph5={k: v["motor_range"]["min_Rph5"] for k, v in c25["charge"].items()},
               booster={k: v["booster"] for k, v in c25["charge"].items()})
    e31 = [r for r in c31["grid"] if r["key"] == "C4MS008075U2x2" and abs(r["fr"] - 25e3) < 1][0]
    out["ref"] = ref
    out["E31_pred"] = dict(none=e31["none"]["aux4"], shed=e31["shed"]["aux4"], charge=e31["shed"]["charge"])
    # (D0) 800 V 위상당 손실: E31 예측(150 kHz 도통 격자 + 공식) 대비
    ct = c31["cond_tables"]["%.3fmOhm" % (A.BASE["Rds"] * 1e3)] if ("%.3fmOhm" % (A.BASE["Rds"] * 1e3)) in c31["cond_tables"] else None
    d0 = []
    if ct is not None:
        Ig = np.array(E15.IGRID)
        A.set_design(DESIGN)
        fix = lambda V: 4 * A.qoss_pos(V / 2) * (V / 2) + 4 * A.BASE["Qg_E"]
        i800 = list(E15.VGRID).index(820.) if 800. not in E15.VGRID else list(E15.VGRID).index(800.)
        Vrow = E15.VGRID[i800]
        for iph in (3., 10., 30.):
            j = list(E15.IGRID).index(iph)
            pred = (ct["Pc"][j] + ct["Pd"][j]) + fix(Vrow) * ct["fs"][j] * 25e3 / FR_R1
            got = float(T["P"][i800][j])
            d0.append(dict(V=Vrow, iph=iph, pred=pred, got=got, ok=abs(got - pred) <= max(0.05 * pred, 1.0)))
        chp = (ct["ch"]["Pc"] + ct["ch"]["Pd"]) + fix(800.) * ct["ch"]["fs"] * 25e3 / FR_R1
        Vs = sorted(T["charge"]); chg = float(np.interp(800., Vs, [T["charge"][v]["ploss_ph"] for v in Vs]))
        d0.append(dict(V=800., iph=46.875, pred=chp, got=chg, ok=abs(chg - chp) <= max(0.05 * chp, 1.0)))
    out["D0"] = d0
    verdict("(D0) A25 직접 모의 위상당 손실이 E31 (나) 예측과 5 % 또는 1 W 안", all(x["ok"] for x in d0) and len(d0) > 0,
            ", ".join("%.0f V %.1f A %.1f/%.1f W" % (x["V"], x["iph"], x["got"], x["pred"]) for x in d0))
    print("  (L) ④ 보조(주행 대표) / 800 V 충전: 셰딩 없음 %.1f W / %.0f W, I_off 15 A %.1f W, I_off %.0f A %.1f W "
          "(⑤ %.1f, ⑥ %.1f W; 모터 승압 기준점 %.0f W, 하한 %.0f W; E31 예측 셰딩 %.1f W·충전 %.0f W)"
          % (out["none"]["aux4"], out["none"]["charge"]["800V"], out["shed15"]["aux4"], th["SH"]["I_off"], out["shed_new"]["aux4"],
             ref["aux5"], ref["aux6"], ref["motor_base"]["800V"], ref["motor_min_Rph5"]["800V"], out["E31_pred"]["shed"],
             out["E31_pred"]["charge"]["800V"]))
    for V in ("640V", "800V", "920V"):
        print("     충전 %s: %.0f W(모터 기준점 %.0f, 하한 %.0f, 전용 승압기 %.0f W)" % (V, out["shed_new"]["charge"][V], ref["motor_base"][V],
                                                                       ref["motor_min_Rph5"][V], ref["booster"][V]))
    save_json(EID, "loss", out)


def figures():
    import matplotlib
    matplotlib.use("Agg")
    from plotstyle import korean, COLOR
    plt = korean()
    D = load_json(EID, "design"); th = load_json(EID, "thresholds"); L = load_json(EID, "loss")
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))
    a = ax[0]
    for V, c in zip(DES_V, (COLOR["blue"], COLOR["green"], COLOR["red"])):
        r2 = sorted([r for r in D["rows"] if r["V"] == V and r["nph"] == 2], key=lambda r: r["I"])
        r1 = sorted([r for r in D["rows"] if r["V"] == V and r["nph"] == 1], key=lambda r: r["I"])
        a.plot([r["I"] for r in r2], [r["loss"] for r in r2], "-o", color=c, ms=3, label=f"{V:.0f} V 2위상")
        a.plot([r["I"] for r in r1], [r["loss"] for r in r1], "--s", color=c, ms=3, label=f"{V:.0f} V 위상 하나")
    for x in (th["SH"]["I_off"], th["SH"]["I_on"]):
        a.axvline(x, color=COLOR["gray"], ls=":")
    a.set_xlabel("모듈 출력전류 [A]"); a.set_ylabel("모듈 손실 [W]"); a.set_title("(a) A25 모듈 손실(2위상·위상 하나)"); a.legend(fontsize=7)
    b = ax[1]
    for V, c in zip(DES_V, (COLOR["blue"], COLOR["green"], COLOR["red"])):
        for n, ls in ((2, "-o"), (1, "--s")):
            rr = sorted([r for r in D["rows"] if r["V"] == V and r["nph"] == n], key=lambda r: r["I"])
            b.plot([r["I"] for r in rr], [100 * r["zcs"] for r in rr], ls, color=c, ms=3)
    b.axhline(5, color=COLOR["red"], ls="--"); b.set_xlabel("모듈 출력전류 [A]"); b.set_ylabel("턴오프 전류/첨두 [%]")
    b.set_title("(b) 영전류 스위칭(실선 2위상, 점선 위상 하나)")
    c = ax[2]
    ref = L["ref"]
    labels = ["E25\n원모델", "A25\n셰딩 없음", "A25\nI_off 15 A", "A25\nI_off %.0f A" % th["SH"]["I_off"]]
    vals = [85.0, L["none"]["aux4"], L["shed15"]["aux4"], L["shed_new"]["aux4"]]
    c.bar(range(4), vals, color=COLOR["blue"])
    c.axhline(ref["aux5"], color=COLOR["orange"], ls="--", label="⑤ %.1f W" % ref["aux5"])
    c.axhline(ref["aux6"], color=COLOR["green"], ls="--", label="⑥ %.1f W" % ref["aux6"])
    c.set_xticks(range(4)); c.set_xticklabels(labels); c.set_ylabel("④ 보조 경로 손실, 주행 대표 [W]")
    c.set_title("(c) 보조 경로 손실(800 V 충전 %.0f W)" % L["shed_new"]["charge"]["800V"]); c.legend(loc="lower right")
    fig.tight_layout()
    p = outdir(EID) / "E32_stage_a_25k.png"
    fig.savefig(p, dpi=130); print("  → 저장:", p)


if __name__ == "__main__":
    parts = sys.argv[1:] or ["design", "rated", "thresholds", "loss", "figures"]
    for part in parts:
        print(f"E32 {part} ...")
        globals()[part]()
