"""[E39] V_A 클램프 스위치 재판정: 최대 열저항과 가지 저항 불균형(재검토 2026-10-29 P1 대응).

■ 왜 필요한가
  재검토(2026-10-29)가 E38 Q1·Q2의 스위치 선정을 지적했다. E38(과 E37)의 스위치 판정 코드는 SiC 모듈의 R_thJC 전형값만 읽었다.
  CAB450M12XM3의 데이터 파일과 데이터시트(Rev. A)에는 전형 0.11 °C/W와 최대 0.13 °C/W가 함께 있다. 최대값을 쓰면 E38의 선정
  (사양 팩 가지 2개 × 1.6 Ω, W460 가지 2개 × 1.8 Ω)이 178.21·177.15 °C로 한도 175 °C를 넘는다(직접 재현, 판정 아님).
  또 E38은 두 가지 저항이 같은 모서리에 있는 경우만 판정했다. 한 가지는 작은 저항, 다른 가지는 큰 저항이면 작은 저항 가지의
  켜진 시간이 길어져 온도가 더 오른다(검토 표본 170.47 °C, 전형 열저항). 그 가지의 에너지(약 4.6 kJ)는 E38이 저항 자기 가열에
  가정한 3.5 kJ보다 크다(W460은 큰 저항 상태 가지도 3.81 kJ로 가정보다 크다).
  사용자 결정(2026-10-29): 기준을 먼저 정해 다시 판정한다.

■ 판정 기준(실행 전에 커밋. 바꾸면 그 이유와 함께 실행 경과에 적는다)
  공통(E38과 같음): 사건(사양 팩 E26 클램프 사건 32개, W460 E38 hv 사건 16개), 저항(Ohmite SP: 공차 ±10 %, 온도계수 +0.2 … −0.08 %/°C,
    노화 ±5 %, 주위 −40 … 85 °C, 자기 가열 ΔT = E/C_th, C_th 48.4 J/K 가정, 배선 3 mΩ), 스위치 강하 2.05 V, 손실(켬·끔 에너지·온저항·
    도통 전압은 표의 가장 큰 온도 값), 사건 평균 손실 × 정상 열저항, 케이스 100 °C(SiC) 또는 방열판 65 °C, 기준 (C1)(I)(E)(V).
  바뀌는 것
  (R1) 열저항: 데이터시트(저장 파일)에 최대값이 있으면 최대값을 쓴다. 값이 하나만 있으면(전형값이거나 열이 표시되지 않음)
       그 값 × 1.2를 쓴다. 1.2는 최대·전형을 모두 주는 유일한 후보 CAB450M12XM3의 비 0.13/0.11 = 1.18을 올린 값이다(가정).
       FF450R12ME4P R_thJH 0.104 → 0.1248, CAB450M12XM3 R_thJC 0.13(최대), CAB530M12BM3 R_thJC 0.065 → 0.078,
       FF2MR12KM1P R_thJH 0.104 → 0.1248, SKM500MB120SC R_thJC 0.08 → 0.096·R_thCH 0.025 → 0.030.
  (R2) 가지 저항 조합: n ≥ 2이면 세 조합을 모두 판정한다.
       max = 모든 가지 큰 저항(강하 2.05 V), min = 모든 가지 작은 저항(강하 0),
       mix = 가지 하나 작은 저항(강하 0) + 나머지 큰 저항(강하 2.05 V)(작은 저항 가지가 가장 오래 켜지는 조합).
       (C1)은 세 조합 모두, (I)(T)(E)는 세 조합의 모든 가지(종류별)의 최악으로 판정한다.
  (R3) 저항 자기 가열: 큰 저항 상태 가지는 E_가정 = 7 kJ ÷ n(E38과 같음), 작은 저항 상태 가지는 E_가정 = 7 kJ × f(f = mix 조합에서
       작은 저항 가지의 전류 몫, 모서리 저항으로 계산). 사건에서 나온 가지 에너지가 가정보다 크면 그 값(50 J 단위 올림)으로 모서리를
       다시 계산해 그 변형을 다시 실행한다(최대 2번). 마지막에도 넘으면 그 변형은 (S) 불통과. 단서: 지금 가정에서 이미 (C1)(E)를 못
       넘거나 통과 스위치가 없는 변형은 갱신하지 않는다(갱신은 큰 저항을 키우고 작은 저항을 줄여 C1·전류를 나쁘게 하는 쪽이라
       선정에 들어오지 않는다. 계산량 절약). 이런 변형의 (S)는 '갱신 안 함'으로 적고, 선정 대상에서 뺀다.
  (R4) 선정(사양 팩): ① 변형 = (C1)(E)(S)를 통과하고 스위치가 하나 이상 (I)(T)(V)를 통과하는 변형 가운데 가지 수가 적은 것 → 끔 463 V →
       큰 R_b. ② 스위치 = 그 변형에서 FF450R12ME4P가 통과하면 그것, 아니면 통과한 SiC 가운데 온도 여유(T_vj,max − T_vj)가 가장 큰 것
       (같으면 전류 여유가 큰 것).
       (W460, 켬 511·끔 506 V, C1 ≤ 530 V) ① 사양 팩에서 고른 스위치가 통과하는 변형 가운데 가지 수가 적은 것 → 큰 R_b(없으면
       어떤 스위치든 통과하는 변형에서 같은 순서) ② 사양 팩 스위치가 통과하면 그것, 아니면 (R4)②와 같다.
  정보(판정 아님): 과도 열(데이터시트에 Foster 계수 숫자가 있는 FF2MR12KM1P만: Z_thJH r_i·τ_i, 방열판 65 °C, 사건 파형의 순간 손실
       — 켬·끔 에너지는 그 순간에, 도통은 R_DS(on)·i² — 로 접합 온도 최고. 계수 그대로와 × 1.2), E38 선정의 E39 규칙 판정.

■ 계산 재사용
  max·min 조합(사양 팩)의 사건 기록은 E38 근거 파일(validation/2026-10-29-review-response/E38/clamp.json의 raw)을 다시 쓴다. 같은 E26
  모델·같은 모서리 저항이고(모서리 저항이 E38과 1e-9 Ω 안에서 같은지 확인한다), 부분 reg에서 두 사건을 새로 실행해 같은 값인지
  확인한다. 모서리가 다르면(R3 반복) 새로 실행한다. W460은 E38이 사건 기록을 남기지 않아 모두 새로 실행한다.

■ 실행   python E39_clamp_switch_rejudge.py reg spec hv tr table
■ 결과   results/E39/*.json
"""
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from common import load_json, save_json, verdict, workers
import E34_parts_rating as E34
import E38_review_response as E38

EID = "E39"
ROOT = Path(__file__).resolve().parents[3]
E38_CLAMP = ROOT / "validation" / "2026-10-29-review-response" / "E38" / "clamp.json"
F_RTH = 1.2                                   # 값이 하나만 있는 열저항의 배수(가정)
E_STEP = 50.                                  # 자기 가열 가정 갱신 단위 [J]
N_ITER = 2


# ======================================================================================================
# 저항 모서리(E38 kfac의 일반화: 가지 상태별 자기 가열 에너지)
# ======================================================================================================
def k_of(E_j, hot_only=False):
    dT = E_j / E38.C_TH; Th = E38.T_AMB[1] + dT
    kmax = (1 + E38.TOL) * (1 + E38.DRIFT) * (1 + E38.TCR_POS * (Th - E38.T_REF))
    kmin = (1 - E38.TOL) * (1 - E38.DRIFT) * min(1 + E38.TCR_POS * (E38.T_AMB[0] - E38.T_REF), 1 + E38.TCR_NEG * (Th - E38.T_REF))
    return kmax, kmin, dT


def corners39(n, Rb, E_hi=None, E_lo=None):
    """E_hi: 큰 저항 상태 가지의 자기 가열 에너지, E_lo: 작은 저항 상태 가지의 자기 가열 에너지."""
    E_hi = E38.E_EVT / n if E_hi is None else E_hi
    kmax, _, dT_hi = k_of(E_hi)
    if E_lo is None:
        if n == 1:
            E_lo = E38.E_EVT
        else:                                   # mix에서 작은 저항 가지의 몫(고정점, 모서리 저항으로)
            f = 0.5
            for _ in range(50):
                _, kmin, _ = k_of(E38.E_EVT * f)
                f = (1 / kmin) / (1 / kmin + (n - 1) / kmax)
            E_lo = E38.E_EVT * f
    _, kmin, dT_lo = k_of(E_lo)
    return dict(Rmax=Rb * kmax + E38.R_WIRE, Rmin=Rb * kmin, kmax=kmax, kmin=kmin, E_hi=E_hi, E_lo=E_lo, dT_hi=dT_hi, dT_lo=dT_lo)


def combos(n, c):
    """조합 → [(종류, R, 강하, 개수)]."""
    out = dict(max=[("hi", c["Rmax"], E38.V_DROP_MAX, n)], min=[("lo", c["Rmin"], 0., n)])
    if n >= 2:
        out["mix"] = [("lo", c["Rmin"], 0., 1), ("hi", c["Rmax"], E38.V_DROP_MAX, n - 1)]
    return out


# ======================================================================================================
# 스위치(R1 열저항 규칙)
# ======================================================================================================
def switches39():
    sw = E38.switches()
    import glob
    ds = {}
    for p in glob.glob(str(E34.DS_DIR / "E37_sic_*.json")):
        d = json.loads(open(p, encoding="utf-8").read()); ds[d["part"]] = d["mosfet"]
    g = E34.ds("FF450R12ME4P")["igbt"]
    rules = {}
    sw["FF450R12ME4P"]["therm"] = [(E34.T_H_IGBT, F_RTH * g["R_thJH_KperW"])]
    rules["FF450R12ME4P"] = "R_thJH %.3f(값 하나) × %.1f = %.4f K/W, 방열판 %.0f °C" % (g["R_thJH_KperW"], F_RTH, F_RTH * g["R_thJH_KperW"], E34.T_H_IGBT)
    for name, m in ds.items():
        th = []; txt = []
        if m.get("R_thJC_max_KperW"):
            th.append((E34.T_C_SEMI, m["R_thJC_max_KperW"])); txt.append("R_thJC 최대 %.3f" % m["R_thJC_max_KperW"])
        elif m.get("R_thJC_KperW"):
            th.append((E34.T_C_SEMI, F_RTH * m["R_thJC_KperW"])); txt.append("R_thJC %.3f × %.1f" % (m["R_thJC_KperW"], F_RTH))
        if m.get("R_thJH_KperW"):
            th.append((E34.T_H_IGBT, F_RTH * m["R_thJH_KperW"])); txt.append("R_thJH %.3f × %.1f" % (m["R_thJH_KperW"], F_RTH))
        elif m.get("R_thJC_KperW") and m.get("R_thCH_KperW"):
            rjc = m["R_thJC_max_KperW"] if m.get("R_thJC_max_KperW") else F_RTH * m["R_thJC_KperW"]
            th.append((E34.T_H_IGBT, rjc + F_RTH * m["R_thCH_KperW"])); txt.append("+ R_thCH %.3f × %.1f(방열판)" % (m["R_thCH_KperW"], F_RTH))
        sw[name]["therm"] = th
        sw[name]["foster"] = m.get("zth_foster")
        rules[name] = ", ".join(txt)
    return sw, rules


# ======================================================================================================
# 사건 실행(가지 종류별 기록)
# ======================================================================================================
def _branch_rows(tr, kw, br, n):
    t, vA, vb, icl = tr[:, 0], tr[:, 1], tr[:, 2], tr[:, 5]
    on_ = icl > 0
    k_on = np.flatnonzero(~on_[:-1] & on_[1:]) + 1
    k_off = np.flatnonzero(on_[:-1] & ~on_[1:]) + 1
    dt = float(t[1] - t[0])
    span = float(t[k_off[-1] - 1] - t[k_on[0]]) if len(k_on) and len(k_off) else float(on_.sum() * dt)
    rows = {}
    for kind, R, vd, m in br:
        i = np.where(on_, np.maximum(vA - vd, 0.) / R, 0.)
        rows[kind] = dict(kind=kind, R=R, vdrop=vd, count=m, **{k: kw[k] for k in ("Vbat", "P400", "PC", "arch", "prof", "t_comm")},
                          vA_max=float(vA.max()), vb_max=float(vb.max()), E_branch_J=float(np.sum(np.maximum(vA - vd, 0.) * i) * dt),
                          n_on=int(len(k_on)), span_s=span, i_max=float(i.max()),
                          S_on=float(np.sum(vA[k_on] * i[k_on])), S_off=float(np.sum(vA[k_off - 1] * i[k_off - 1])),
                          S_i=float(np.sum(i[on_]) * dt), S_i2=float(np.sum(i[on_] ** 2) * dt))
    return rows


def _ev39(args):
    br, on, off, kw = args
    import E26_charging_stop as E26
    E26.BUS["CA"] = E38.CA_R; E26.RA_MOD = E38.RA_A25
    E26.CL = dict(E26.CL, on=on, off=off, branches=[(R, vd, m) for _, R, vd, m in br])
    r = E26.run_event(**kw, rec_every=1, full_trace=True)
    tr = np.array(r.pop("trace"))
    rows = _branch_rows(tr, kw, br, sum(m for *_, m in br))
    for v in rows.values():
        v.update(vA_max=float(r["vA_max"]), vb_max=float(r["vb_max"]))
    return rows


def run_combos(jobs):
    """jobs: [(key, br, on, off, kw)] → {key: [rows dict per event]}"""
    with Pool(workers()) as p:
        res = p.map(_ev39, [j[1:] for j in jobs], chunksize=2)
    out = {}
    for j, r in zip(jobs, res):
        out.setdefault(j[0], []).append(r)
    return out


# ======================================================================================================
# 판정
# ======================================================================================================
def judge39(recs, sws, vlim):
    """recs: {조합: [ {종류: row} per event ]}"""
    allrows = [r for evs in recs.values() for e in evs for r in e.values()]
    c1 = max(max(r["vA_max"], r["vb_max"]) for r in allrows)
    c1_by = {k: max(max(r["vA_max"], r["vb_max"]) for e in evs for r in e.values()) for k, evs in recs.items()}
    E_b = max(r["E_branch_J"] for r in allrows)
    E_hi = max(r["E_branch_J"] for r in allrows if r["kind"] == "hi")
    E_lo = max(r["E_branch_J"] for r in allrows if r["kind"] == "lo")
    imax = max(r["i_max"] for r in allrows)
    vmax = max(r["vA_max"] for r in allrows)
    out = dict(C1_V=c1, C1_by=c1_by, C1=bool(c1 <= vlim), E_branch_max_J=E_b, E_hi_obs=E_hi, E_lo_obs=E_lo, E=bool(E_b <= E38.E_RES),
               i_branch_max=imax, vA_max=vmax, switches={})
    for sn, sw in sws.items():
        worst = None
        for cb, evs in recs.items():
            for kind in ("hi", "lo"):
                rows = [e[kind] for e in evs if kind in e]
                if not rows:
                    continue
                t = E38.thermal(rows, sw)
                if t.get("T") is not None and (worst is None or t["T"] > worst["T"]):
                    worst = dict(t, combo=cb, kind=kind)
        I_lim = None if sw.get("I_pulse") is None else E34.I_DER * sw["I_pulse"]
        ok_i = I_lim is not None and imax <= I_lim
        ok_v = vmax <= E34.V_DER * sw["V_rated"]
        ok_t = worst is not None and worst["T"] <= sw["T_max"]
        out["switches"][sn] = dict(ok=bool(ok_i and ok_v and ok_t), I=bool(ok_i), I_lim=I_lim, V=bool(ok_v), T=bool(ok_t),
                                   T_vj=None if worst is None else worst["T"], T_lim=sw["T_max"], worst=worst,
                                   T_margin=None if worst is None else sw["T_max"] - worst["T"],
                                   I_margin=None if I_lim is None else I_lim - imax)
    return out


def variant(n, Rb, on, off, events, vlim, sws, reuse=None, tag=""):
    """한 변형을 (R3) 반복과 함께 판정한다. reuse: E38 raw {max: rows, min: rows}(모서리가 같을 때만)."""
    c = corners39(n, Rb)
    hist = []
    for it in range(N_ITER + 1):
        cbs = combos(n, c)
        recs = {}
        jobs = []
        for cb, br in cbs.items():
            if reuse and it == 0 and cb in reuse:
                R_e38 = reuse[cb][0]["R"]; R_now = br[0][1]          # E38 raw의 R은 가지 하나의 저항(n 가지가 같은 값)
                if abs(R_e38 - R_now) < 1e-9 and abs(reuse[cb][0]["vdrop"] - br[0][2]) < 1e-12:
                    recs[cb] = [{br[0][0]: dict(r, kind=br[0][0])} for r in reuse[cb]]
                    continue
            for e in events:
                jobs.append((cb, br, on, off, e))
        if jobs:
            recs.update(run_combos(jobs))
        j = judge39(recs, sws, vlim)
        need_hi = j["E_hi_obs"] > c["E_hi"] + 1e-9
        need_lo = j["E_lo_obs"] > c["E_lo"] + 1e-9
        passing = j["C1"] and j["E"] and any(v["ok"] for v in j["switches"].values())
        if (need_hi or need_lo) and not passing:
            j["S"] = None                       # 불통과 변형은 갱신하지 않는다(R3 단서)
            hist.append(dict(it=it, E_hi_assumed=c["E_hi"], E_lo_assumed=c["E_lo"], E_hi_obs=j["E_hi_obs"], E_lo_obs=j["E_lo_obs"],
                             Rmax=c["Rmax"], Rmin=c["Rmin"], C1_V=j["C1_V"], note="불통과 변형, 갱신 안 함"))
            break
        hist.append(dict(it=it, E_hi_assumed=c["E_hi"], E_lo_assumed=c["E_lo"], E_hi_obs=j["E_hi_obs"], E_lo_obs=j["E_lo_obs"],
                         Rmax=c["Rmax"], Rmin=c["Rmin"], C1_V=j["C1_V"]))
        if not (need_hi or need_lo):
            j["S"] = True
            break
        if it == N_ITER:
            j["S"] = False
            break
        E_hi = math.ceil(j["E_hi_obs"] / E_STEP) * E_STEP if need_hi else c["E_hi"]
        E_lo = math.ceil(j["E_lo_obs"] / E_STEP) * E_STEP if need_lo else c["E_lo"]
        c = corners39(n, Rb, E_hi, E_lo)
        print("    %s n %d R_b %.1f: 자기 가열 가정 갱신 E_hi %.0f J, E_lo %.0f J → R %.4f–%.4f Ω" % (tag, n, Rb, E_hi, E_lo, c["Rmin"], c["Rmax"]))
    j.update(n=n, R_b=Rb, on=on, off=off, R_max=c["Rmax"], R_min=c["Rmin"], kmax=c["kmax"], kmin=c["kmin"], iter=hist,
             ok_variant=bool(j["C1"] and j["E"] and j["S"] is True and any(v["ok"] for v in j["switches"].values())))
    return j, recs


def pick_switch(j, order_first=None):
    ok = {sn: v for sn, v in j["switches"].items() if v["ok"]}
    if not ok:
        return None
    if order_first and order_first in ok:
        return order_first
    return max(ok, key=lambda sn: (ok[sn]["T_margin"], ok[sn]["I_margin"] or 0.))


def line(j):
    return ("n %d R_b %.1f Ω 끔 %.0f V: R %.3f–%.3f Ω, C1 %.2f V(%s) %s, 가지 %.0f A, 에너지 %.0f J(hi %.0f, lo %.0f) %s | %s"
            % (j["n"], j["R_b"], j["off"], j["R_min"], j["R_max"], j["C1_V"], ", ".join("%s %.2f" % kv for kv in j["C1_by"].items()),
               "통과" if j["C1"] else "불통과", j["i_branch_max"], j["E_branch_max_J"], j["E_hi_obs"], j["E_lo_obs"],
               "" if j["S"] else ("(S 불통과)" if j["S"] is False else "(S 갱신 안 함)"),
               ", ".join("%s %s(%s)" % (sn, "✓" if v["ok"] else "✗", "%.1f °C" % v["T_vj"] if v["T_vj"] else "-") for sn, v in j["switches"].items())))


# ======================================================================================================
# 부분
# ======================================================================================================
def reg():
    """재사용 근거: E38 raw의 두 사건을 새로 실행해 같은지, 가지 목록 한 개(개수 n)가 이전 식과 같은지."""
    import E26_charging_stop as E26
    raw = json.load(open(E38_CLAMP, encoding="utf-8"))["raw"]
    evs = [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]
    out = []
    for key, k_ev in (("2_1.6_463_max", 0), ("2_1.6_463_min", 5)):
        n, Rb, off, cn = key.split("_"); n = int(n); Rb = float(Rb); off = float(off)
        c = E38.corners(n, Rb)[cn]
        new = E38._ev((n, c["R"], c["vdrop"], 468., off, evs[k_ev]))
        old = raw[key][k_ev]
        d = max(abs(new[k] - old[k]) for k in ("vA_max", "vb_max", "E_branch_J", "S_on", "S_off", "S_i", "S_i2", "i_max", "span_s"))
        c39 = corners39(n, Rb); R39 = c39["Rmax"] if cn == "max" else c39["Rmin"]
        row39 = _ev39(([("x", R39, c["vdrop"], n)], 468., off, evs[k_ev]))["x"]
        d39 = max(abs(row39[k] - old[k]) for k in ("vA_max", "vb_max", "S_on", "S_off", "S_i", "S_i2", "i_max", "span_s"))
        dE = abs(row39["E_branch_J"] - old["E_branch_J"]) / max(old["E_branch_J"], 1.)
        out.append(dict(key=key, ev=k_ev, R_E38=c["R"], R_E39=R39, diff_E38_rerun=d, diff_E39_branches=d39, dE_rel=dE))
        print("  %s 사건 %d: E38 재실행 차 %.3g, E39 가지 목록 차 %.3g(에너지 상대 %.2g), 모서리 R E38 %.9f / E39 %.9f"
              % (key, k_ev, d, d39, dE, c["R"], R39))
    ok = all(o["diff_E38_rerun"] == 0. and abs(o["R_E38"] - o["R_E39"]) < 1e-9 and o["diff_E39_branches"] < 1e-9 for o in out)
    verdict("재사용 근거(E38 raw 재실행 차 0, 모서리 같음, 가지 목록 식 같음)", ok)
    save_json(EID, "reg", dict(rows=out, ok=ok))


def spec():
    import E26_charging_stop as E26
    evs = [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]
    raw = json.load(open(E38_CLAMP, encoding="utf-8"))["raw"]
    sws, rules = switches39()
    for sn, t in rules.items():
        print("  열저항 규칙 %s: %s" % (sn, t))
    table = []
    for n, rs in E38.GRID.items():
        for Rb in rs:
            for off in E38.OFFS:
                key = "%d_%.1f_%.0f" % (n, Rb, off)
                reuse = {"max": raw[key + "_max"], "min": raw[key + "_min"]}
                j, _ = variant(n, Rb, 468., off, evs, E38.V_LIM, sws, reuse=reuse, tag="spec")
                table.append(j)
                print("  " + line(j), flush=True)
    cands = [j for j in table if j["ok_variant"]]
    sel = None
    if cands:
        v = min(cands, key=lambda j: (j["n"], -j["off"], -j["R_b"]))
        sel = dict(n=v["n"], R_b=v["R_b"], off=v["off"], switch=pick_switch(v, "FF450R12ME4P"))
    e38 = next(j for j in table if j["n"] == 2 and j["R_b"] == 1.6 and j["off"] == 463.)
    verdict("(Q1′) 사양 팩 V_A 클램프 재선정(최대 열저항, 가지 저항 조합, 자기 가열 갱신)", sel is not None, str(sel))
    print("  정보: E38 선정(2 × 1.6 Ω·CAB450M12XM3)의 E39 판정: %s, %.2f °C(%s·%s)"
          % ("통과" if e38["switches"]["CAB450M12XM3"]["ok"] else "불통과", e38["switches"]["CAB450M12XM3"]["T_vj"],
             e38["switches"]["CAB450M12XM3"]["worst"]["combo"], e38["switches"]["CAB450M12XM3"]["worst"]["kind"]))
    save_json(EID, "spec", dict(rows=table, selected=sel, rules=rules, F_RTH=F_RTH,
                                e38_selection=dict(n=2, R_b=1.6, off=463., switch="CAB450M12XM3",
                                                   result=e38["switches"]["CAB450M12XM3"])))


def hv():
    import E26_charging_stop as E26
    P = E38._packs(); vchg = E38.CHG_VMAX - E38.R_CH * E38.I_CH
    vmx = {k: max(p["vmax"] / 2, min(p["vmax"] / 2 + E38.R_A4 * E38.I_CH, vchg)) for k, p in P.items()}
    hi = [k for k, v in vmx.items() if v > 463. - 2.]
    off_w = math.ceil(max(vmx[k] for k in hi) + 2.); on_w = off_w + 5.
    print("  고전압 팩 %s → 켬 %.0f·끔 %.0f V(E38과 같은 규칙)" % (hi, on_w, off_w))
    evs = [dict(Vbat=vb, P400=P400, PC=PC, arch="R2W", clamp=True, prof=prof, t_comm=tc, tend=E26.T_STOP + tc + 8e-3)
           for vb in (940.8, 2 * vchg) for (P400, PC) in ((0., 0.), (20e3, 5e3)) for prof in ("hold", "ramp") for tc in (0., 10e-3)]
    sws, rules = switches39()
    s1 = load_json(EID, "spec")["selected"]
    table = []
    for n in (2, 3):
        for Rb in (1.5, 1.6, 1.8, 2.0, 2.2, 2.7, 3.0):
            j, _ = variant(n, Rb, on_w, off_w, evs, E38.HV_LIM, sws, tag="W460")
            j["series_max_V"] = j["vA_max"] - E38.V_W
            table.append(j)
            print("  W460 " + line(j), flush=True)
    sw1 = s1["switch"] if s1 else None
    pool = [j for j in table if j["C1"] and j["E"] and j["S"] is True and sw1 and j["switches"][sw1]["ok"]]
    if not pool:
        pool = [j for j in table if j["ok_variant"]]
    sel = None
    if pool:
        v = min(pool, key=lambda j: (j["n"], -j["R_b"]))
        sel = dict(n=v["n"], R_b=v["R_b"], off=off_w, on=on_w, switch=pick_switch(v, sw1))
    e38 = next(j for j in table if j["n"] == 2 and j["R_b"] == 1.8)
    verdict("(Q2′) 고전압 팩(R2-W460) 클램프 재선정", sel is not None, str(sel))
    print("  정보: E38 선정(2 × 1.8 Ω·CAB450M12XM3)의 E39 판정: %s, %.2f °C"
          % ("통과" if e38["switches"]["CAB450M12XM3"]["ok"] else "불통과", e38["switches"]["CAB450M12XM3"]["T_vj"]))
    save_json(EID, "hv", dict(on=on_w, off=off_w, limit=E38.HV_LIM, hv_packs=hi, events=evs, rows=table, selected=sel,
                              same_hw_as_spec=bool(sel and s1 and sel["switch"] == s1["switch"]),
                              e38_selection=dict(n=2, R_b=1.8, switch="CAB450M12XM3", result=e38["switches"]["CAB450M12XM3"])))


def _foster_peak(args):
    """정보: 선정 변형의 한 사건에서 FF2MR12KM1P 작은 저항 가지(없으면 큰 저항)의 과도 접합 온도."""
    br, on, off, kw, sw, kind = args
    import E26_charging_stop as E26
    E26.BUS["CA"] = E38.CA_R; E26.RA_MOD = E38.RA_A25
    E26.CL = dict(E26.CL, on=on, off=off, branches=[(R, vd, m) for _, R, vd, m in br])
    r = E26.run_event(**kw, rec_every=1, full_trace=True)
    tr = np.array(r["trace"]); t, vA, icl = tr[:, 0], tr[:, 1], tr[:, 5]
    on_ = icl > 0; dt = float(t[1] - t[0])
    R, vd = next((R, vd) for k, R, vd, m in br if k == kind)
    i = np.where(on_, np.maximum(vA - vd, 0.) / R, 0.)
    p = sw["R_on"] * i ** 2
    k_on = np.flatnonzero(~on_[:-1] & on_[1:]) + 1; k_off = np.flatnonzero(on_[:-1] & ~on_[1:]) + 1
    p[k_on] += sw["E_on"] * vA[k_on] * i[k_on] / (sw["V_ref"] * sw["I_ref"]) / dt
    p[k_off - 1] += sw["E_off"] * vA[k_off - 1] * i[k_off - 1] / (sw["V_ref"] * sw["I_ref"]) / dt
    out = {}
    for scale in (1.0, F_RTH):
        x = np.zeros(len(sw["foster"])); pk = 0.
        a = np.array([math.exp(-dt / tau) for _, tau in sw["foster"]]); b = np.array([scale * ri for ri, _ in sw["foster"]]) * (1 - a)
        for q in range(len(p)):
            x = a * x + b * p[q]
            s = x.sum()
            if s > pk:
                pk = s
        out["%.1f" % scale] = E34.T_H_IGBT + pk
    return dict(kind=kind, **{k: kw[k] for k in ("Vbat", "P400", "PC", "arch", "prof", "t_comm")}, T=out,
                P_avg_span=float(p[on_].sum() * dt / max((t[k_off[-1] - 1] - t[k_on[0]]) if len(k_on) and len(k_off) else dt, dt)))


def tr():
    """정보(판정 아님): FF2MR12KM1P의 Foster Z_thJH로 선정 변형 사건의 과도 접합 온도."""
    import E26_charging_stop as E26
    sws, _ = switches39()
    sw = dict(sws["FF2MR12KM1P"])
    sw["foster"] = [tuple(x) for x in sw["foster"]]
    out = {}
    for part, evs_f in (("spec", lambda: [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]),
                        ("hv", lambda: load_json(EID, "hv")["events"])):
        d = load_json(EID, part); sel = d["selected"]
        if not sel:
            continue
        row = next(r for r in d["rows"] if r["n"] == sel["n"] and r["R_b"] == sel["R_b"] and r["off"] == sel["off"])
        c = dict(Rmax=row["R_max"], Rmin=row["R_min"])
        jobs = []
        for cb, br in combos(sel["n"], c).items():
            for kind in sorted({k for k, *_ in br}):
                for e in evs_f():
                    jobs.append((br, row["on"], row["off"], e, sw, kind))
        with Pool(workers()) as p:
            res = p.map(_foster_peak, jobs, chunksize=2)
        worst = max(res, key=lambda r: r["T"]["%.1f" % F_RTH])
        steady = row["switches"]["FF2MR12KM1P"]["T_vj"]
        out[part] = dict(variant=sel, T_peak=worst["T"], worst=worst, steady_T=steady, n=len(res))
        print("  %s: FF2MR12KM1P 과도 최고 %.1f °C(Foster 그대로) / %.1f °C(× %.1f), 정상 열저항 판정 %.1f °C"
              % (part, worst["T"]["1.0"], worst["T"]["%.1f" % F_RTH], F_RTH, steady))
    save_json(EID, "tr", out)


def table():
    out = {}
    for name in ("reg", "spec", "hv", "tr"):
        try:
            out[name] = load_json(EID, name)
        except FileNotFoundError:
            out[name] = None
    rows = []
    if out["spec"]:
        s = out["spec"]; sel = s["selected"]
        v = next(r for r in s["rows"] if sel and r["n"] == sel["n"] and r["R_b"] == sel["R_b"] and r["off"] == sel["off"])
        rows.append(dict(item="사양 팩", selected=sel, T_vj=v["switches"][sel["switch"]]["T_vj"], C1_V=v["C1_V"],
                         i_branch_max=v["i_branch_max"], E_branch_max_J=v["E_branch_max_J"],
                         switches={k: (x["ok"], x["T_vj"]) for k, x in v["switches"].items()}, e38=s["e38_selection"]["result"]["T_vj"]))
    if out["hv"]:
        h = out["hv"]; sel = h["selected"]
        v = next(r for r in h["rows"] if sel and r["n"] == sel["n"] and r["R_b"] == sel["R_b"])
        rows.append(dict(item="W460", selected=sel, T_vj=v["switches"][sel["switch"]]["T_vj"], C1_V=v["C1_V"],
                         i_branch_max=v["i_branch_max"], E_branch_max_J=v["E_branch_max_J"],
                         switches={k: (x["ok"], x["T_vj"]) for k, x in v["switches"].items()}, e38=h["e38_selection"]["result"]["T_vj"]))
    save_json(EID, "table", dict(rows=rows))
    for r in rows:
        print("  %s: %s" % (r["item"], r))


if __name__ == "__main__":
    for part in sys.argv[1:]:
        print("E39", part, "...", flush=True)
        globals()[part]()
