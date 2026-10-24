"""[E20] R2 창 조정 모듈의 H-브리지 고장 강등 중 DAB 순환전류 제한: 전압비 정합 유지 + 1차 내부 위상천이(EPS) + 일시 감발.

■ 목적
  E17·TB09에서 H-브리지 고장 강등(다이오드 클램프 유지 → 400 V 부하 분리 → 링크 붕괴 → 소프트 투입)을 정했지만, 이 순서에서
  DAB 링크 쪽 순시 첨두가 정격점의 4.2배(회로 192 A, 정격점 45.8 A)였다. 원인은 단일 위상천이(SPS)에서 1차 전압(v_bus/n)과
  링크전압이 크게 어긋나는 것이다(유지 중 링크 40–67 V, 붕괴 끝 0 V). 이 시험은 순환전류를 정격 근처로 묶는 강등 방식을 정한다.
    (1) 변조: SPS와 EPS(1차 브리지 두 레그 사이 내부 위상차로 1차 전압에 영구간을 넣음)의 첨두를 같은 링크전류에서 비교하고,
        (r = v_link·n/v_bus, j = 정규화 링크전류)마다 첨두가 가장 작은 EPS 지령표를 만든다(dab_modulation.py).
    (2) 유지 방식: 버스를 V_W에 붙잡는 링크 기준(기존, 링크 40–67 V) 대신 DAB 전압비를 1로 두는 링크 기준
        n·v_link = v_bus(1008 V에서 링크 약 89 V, 버스 약 410 V)을 쓰고, DAB 정격을 넘는 링크전력은 제동 저항이 받는다.
    (3) 첨두 상한: 강등 상태(9–11)에서 DAB 지령 전류를 EPS로 첨두 ≤ 1.5 × 정격점 첨두가 되는 값까지 제한한다.
    (4) 일시 감발: V_A ≤ 부품 상한인 팩도 H-브리지 고장이면 400 V 부하 출력을 줄인 뒤 붕괴·투입하고, 강등 0.5 ms 뒤 되돌린다.
        감발이 없으면 붕괴 중 DAB가 전 부하 경로전류를 빼내야 해 첨두 상한과 함께 쓸 수 없다.
    (5) 소프트 투입 시간 상한(5 ms)에서 주 스위치를 강제로 닫지 않고 이중 고장(FAILSAFE)으로 넘긴다.

■ 왜 필요한가
  DAB 누설 인덕터와 2차 소자는 정격점 첨두(1차 약 10 A, 링크 쪽 45.8 A)에 맞춰 설계된다. 강등 중 4배 전류가 수십 ms 흐르면
  인덕터가 포화해 전류가 더 커질 수 있다. 하드웨어를 키우지 않고 변조·순서로 해결할 수 있는지 확인해야 한다.

■ 방법
  table   : EPS 지령표(r 0–1.4 × j −0.78–0.78, 격자 탐색 d 600 × α 1440). SPS(d = π)와 해석식 일치 확인,
            회로 지령 블록과 같은 보간을 상한에 붙여 쓴 첨두 확인(map_check)
  compare : E17 상태기계(r2_run)로 정책 비교. P0 = E17 추천(버스 유지, SPS), P1 = P0 + EPS(제한 없음, 첨두만),
            P3n = 정합 유지 + EPS 첨두 상한 + 시간 상한 FAILSAFE(감발 없음), P3 = P3n + 일시 감발(추천).
            R2-W460(930·1008 V)·R2-W410(860·920 V) × 5·25 kW, P3 감도(감쇠기 없음, V_D 1.4·3.0 V, 분리 50 ms, DAB 저링크 저하,
            상한 1.3배 = 회로 여유: TB10에서 회로 첨두가 해석 첨두의 1.10–1.16배)
  figures : 첨두-링크전압, 한 주기 인덕터 전류(SPS·EPS), 1008 V·25 kW 시간 궤적(P0·P3, 분리 3 ms, TB09·TB10 회로 첨두 겹침)

■ 판정(시험 전에 고정)
  E17 고장 판정(경로·필터 ≤ 100 A, 직렬·링크 ≤ 120 V, 바이패스 ≤ 329 A, 버스 ≥ 260 V, 강등 도달, 부하 연결 중 버스 ≤ 상한)
  + DAB 링크 쪽 순시 첨두(해석) ≤ 1.5 × 정격점 첨두(W460 68.7 A, W410 90.0 A).

■ 실행   python E20_dab_fault_modulation.py table compare figures
■ 결과   results/E20/eps_table.json, table.json, compare.json, E20_*.png
■ 보고서 수치(docs/25)
  504 V·링크 5 V·11 A: SPS 189 A → EPS 20 A. 정책: P0 0/8(197·202 A), P1 0/4, P3n 3/4, P3 8/8(68.8·90.0 A, 제동 ≤ 21.4 J).
  감도 15/16(W410 감쇠기 없음 100.2 A), 상한 1.3배 4/4. 회로 보간 첨두 ≤ 상한의 1.0007배.
  회로(TB10): 79.4·75.3 A — 해석의 1.10–1.16배(데드타임·소자 강하 등, 지령표에 없음).
"""
import math
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

from common import save_json, verdict, workers, outdir
import dab_modulation as DM
import E17_protection_integration as E17
import E19_r2_window_module as E19

EID = "E20"
POLICIES = {
    "P0": dict(),                                                        # E17 추천(버스를 V_W에, SPS)
    "P1": dict(dmod_metric="eps"),                                       # P0 궤적에서 EPS 첨두만(제한 없음)
    "P3n": dict(hold="match", dmod="eps", soft_fail=True),               # 정합 유지 + EPS 첨두 상한, 감발 없음
    "P3": dict(hold="match", dmod="eps", soft_fail=True, curtail=True),  # + 일시 감발(추천)
}
VS = {"W460_240s": [930., 1008.], "W410_spec": [860., 920.]}


# ----------------------------------------------------------------------------------------------
def table():
    T = DM.eps_table()
    p, _ = E19.plant("W460_240s")
    chk = []
    for r, phi in ((1.0, 0.4), (0.4, 0.9), (0.005, 0.3)):            # SPS(d = π)와 해석식
        j, pk, _ = DM.wave_norm(r, np.pi, phi)
        i0 = -(np.pi + r * (2 * phi - np.pi)) / 2; iph = ((2 * phi - np.pi) + r * np.pi) / 2
        chk.append(dict(r=r, phi=phi, j=float(j), j_formula=phi * (1 - phi / np.pi), pk=float(pk), pk_formula=max(abs(i0), abs(iph))))
    ok = all(abs(c["j"] - c["j_formula"]) < 1e-9 and abs(c["pk"] - c["pk_formula"]) < 1e-9 for c in chk)
    verdict("SPS 특수 경우(d = π)가 해석식과 같다", ok)
    rows = []
    for vb in (460., 504.):
        for vl in (0.5, 3.5, 10., 20., 40., 60., 89., 100.):
            for I in (-11., -30., -60.):
                rows.append(dict(vb=vb, vl=vl, I=I, sps=DM.peak_A(vb, vl, I, p, "sps"), eps=DM.peak_A(vb, vl, I, p, "eps")))
    for r_ in rows:
        if r_["vb"] == 504. and r_["I"] in (-11., -60.):
            print("   v_bus 504 V, 링크 %5.1f V, 링크전류 %5.0f A: SPS %6.1f A, EPS %6.1f A" % (r_["vl"], r_["I"], r_["sps"], r_["eps"]))
    lim = [dict(vb=vb, vl=vl, ilim=DM.eps_ilim(vb, vl, p, E17.PK_FAULT * 45.8281)) for vb in (380., 410., 460., 504.)
           for vl in (0.5, 5., 20., 50., 80., 89., 100.)]
    mc = map_check(p)
    verdict("회로 지령표(φ·D1 쌍선형 보간, D1 ≤ 0.95)를 상한에 붙여 써도 첨두 ≤ 상한 × 1.005", mc["ratio_max"] <= 1.005,
            "최대 %.4f배, 전류 오차 평균 %.1f %%" % (mc["ratio_max"], 100 * mc["i_err_mean"]))
    save_json(EID, "table", dict(check=chk, grid=dict(r=[T["r"][0], T["r"][-1], len(T["r"])], j=[T["j"][0], T["j"][-1], len(T["j"])]),
                                 points=rows, eps_current_limit_W460=lim, nd=T["nd"], na=T["na"], tol=T["tol"], circuit_map_check=mc))


def map_check(p, pkf=None):
    """회로 지령 블록(simulink/ctrl/prism_dab_eps_map.m)과 같은 계산을 여기서 흉내 낸다: j ≤ 0 표, j = 0 열은 j = −0.01 열,
    φ = α + D1·π, (d, φ) 쌍선형 보간, D1 ≤ 0.95. 지령을 상한에 붙인(−200 A) 상태에서 실제 파형의 첨두(wave_norm)가
    상한을 얼마나 넘는지 본다. 넘지 않으면 TB10 회로 첨두의 초과는 표 보간이 아니라 회로 효과(데드타임·소자 강하·주기 간 변화)다."""
    T = DM.eps_table(); pkf = E17.PK_FAULT if pkf is None else pkf
    J = np.asarray(T["j"]); keep = J <= 1e-9
    d = np.array(T["d"])[:, keep]; a = np.array(T["a"])[:, keep]; pk = np.array(T["pk"])[:, keep]
    d[:, -1] = d[:, -2]; a[:, -1] = a[:, -2]; pk[:, -1] = pk[:, -2]
    ph = np.vectorize(lambda aa, dd: math.remainder(aa + (1 - dd / np.pi) * np.pi, 2 * np.pi))(a, d)
    R = np.asarray(T["r"]); r0, dr = R[0], R[1] - R[0]; j0, dj = J[keep][0], J[1] - J[0]
    nr, nj = d.shape
    n, wl = p.turns, 2 * np.pi * p.fs * p.Ldab / p.turns ** 2
    pk_max = pkf * E17.dab_sps_peak(460., 100., p.power_max / 100., p)
    worst, errs = (0., None), []
    for vb in np.arange(380., 505., 7.3):
        for vl in np.arange(1., 95., 0.77):
            v1 = vb / n; Ib = v1 / wl
            r = min(max(vl / v1, r0), r0 + (nr - 1) * dr)
            ir = min(int((r - r0) / dr), nr - 2); fr = (r - r0) / dr - ir
            row = (1 - fr) * pk[ir] + fr * pk[ir + 1]
            jl = 0.
            for k in range(nj - 1, -1, -1):                         # j = 0 → −0.78, 상한 안의 최대 |j|
                if row[k] > pk_max / Ib:
                    break
                jl = -(j0 + k * dj)
            jn = max(-jl, j0)
            ij = min(int((jn - j0) / dj), nj - 2); fj = (jn - j0) / dj - ij
            bil = lambda z: ((1 - fr) * (1 - fj) * z[ir, ij] + (1 - fr) * fj * z[ir, ij + 1] + fr * (1 - fj) * z[ir + 1, ij] + fr * fj * z[ir + 1, ij + 1])
            D1 = min(max(1 - bil(d) / np.pi, 0.), 0.95)
            jj, pp, _ = DM.wave_norm(r, (1 - D1) * np.pi, bil(ph) - D1 * np.pi)
            ratio = float(pp) * Ib / pk_max
            if ratio > worst[0]:
                worst = (ratio, (float(vb), float(vl)))
            errs.append(abs(float(jj) - jn) / max(abs(jn), 1e-3) if jn < -0.02 else 0.)
    return dict(pk_max=pk_max, ratio_max=worst[0], worst_at_vb_vl=worst[1], i_err_mean=float(np.mean(errs)), n=len(errs))


# ----------------------------------------------------------------------------------------------
def _job(a):
    name, j = a
    kw = {k: v for k, v in j.items() if k != "dmod_metric"}
    p1 = j.get("dmod_metric") == "eps"
    m = E17.r2_run(dict(kw, keep=True) if p1 else kw)
    m["pol_name"] = name
    if p1:                                                              # P1: P0 궤적에서 EPS 첨두(제한 없음)를 다시 계산
        p, _ = E19.plant(j["case"]); tr = m["trace"]; L = tr["log"]; ev = dict((e[0], e[1]) for e in m["events"])
        t_h = ev.get("HB_HOLD"); t_d = ev.get("DEGRADED")
        tt = tr["t"] * 1e3
        w = (tt >= (t_h or 0.) + E17.T_EV * 1e3) & (tt <= (t_d or tt[-1]) + E17.T_EV * 1e3)
        m["dab_sec_peak"] = max(DM.peak_A(L[i, 2], L[i, 4], L[i, 5], p, "eps") for i in np.flatnonzero(w)[::5])
        m["dab_peak_hold"] = m["dab_peak_collapse"] = None
    ev = dict((e[0], e[1]) for e in m["events"])
    m["collapse_ms"] = (ev["SOFT_BYP"] - ev["HB_COLLAPSE"]) if ("SOFT_BYP" in ev and "HB_COLLAPSE" in ev) else None
    lim = m["dab_rated_sec_peak"] * E17.PK_FAULT                     # 판정은 언제나 1.5배(감도 pk_fault는 더 낮은 상한)
    m["checks"]["dab_peak_1p5x"] = m["dab_sec_peak"] <= lim * 1.005      # 표 보간 0.5 % 허용
    m["pass_"] = bool(all(m["checks"].values()))
    m.pop("trace", None)
    return m


def jobs():
    js = []
    for case, Vs in VS.items():
        for V in Vs:
            for P in (5000., 25000.):
                for name in ("P0", "P3"):
                    js.append((name, dict(case=case, V=V, P=P, event="hb_open", policy="clamp_brk", **POLICIES[name])))
                if P == 25000.:
                    for name in ("P1", "P3n"):
                        js.append((name, dict(case=case, V=V, P=P, event="hb_open", policy="clamp_brk", **POLICIES[name])))
    for case, Vs in VS.items():                                           # P3 감도(최대 전압·25 kW)
        V = Vs[-1]
        base = dict(case=case, V=V, P=25000., event="hb_open", policy="clamp_brk", **POLICIES["P3"])
        js += [("P3", dict(base, damper=False, tag="감쇠기 없음")), ("P3", dict(base, vd=1.4, tag="V_D 1.4 V")),
               ("P3", dict(base, vd=3.0, tag="V_D 3.0 V")), ("P3", dict(base, t_shed=50e-3, tag="분리 50 ms"))]
        for V2 in Vs:
            js.append(("P3", dict(base, V=V2, dab_lowv=10., tag="DAB 저링크 저하 10 V")))
            js.append(("P3", dict(base, V=V2, pk_fault=1.3, tag="상한 1.3배(회로 여유)")))   # TB10: 회로 첨두/해석 첨두 1.10–1.16
    return js


def compare():
    js = jobs()
    t0 = time.time()
    with Pool(workers()) as pool:
        rows = pool.map(_job, js, chunksize=1)
    print("  compare: %d건, %.0f s" % (len(rows), time.time() - t0))
    groups = {}
    for r in rows:
        k = "%s|%s%s" % (r["case"], r["pol_name"], ("|" + r["tag"]) if r.get("tag") else "")
        g = groups.setdefault(k, dict(n=0, passed=0, path=0., bridge=0., dab=0., dab_hold=0., dab_col=0., bus_min=1e9, bus_loaded=0.,
                                      brk=0., soft=0., col=0., fails={}, lim=r["dab_peak_limit"]))
        g["n"] += 1; g["passed"] += int(r["pass_"])
        g["path"] = max(g["path"], r["path_peak"]); g["bridge"] = max(g["bridge"], r["bridge_peak"])
        g["dab"] = max(g["dab"], r["dab_sec_peak"]); g["dab_hold"] = max(g["dab_hold"], r.get("dab_peak_hold") or 0.)
        g["dab_col"] = max(g["dab_col"], r.get("dab_peak_collapse") or 0.)
        g["bus_min"] = min(g["bus_min"], r["vbus_min"]); g["bus_loaded"] = max(g["bus_loaded"], r["vbus_max_loaded"] or 0.)
        g["brk"] = max(g["brk"], r["brk_energy_J"]); g["soft"] = max(g["soft"], r["soft_energy_J"])
        g["col"] = max(g["col"], r.get("collapse_ms") or 0.)
        for c, ok in r["checks"].items():
            if not ok:
                g["fails"].setdefault(c, []).append((r["V"], r["P"]))
    for k, g in groups.items():
        print("  %-42s %2d/%2d, 경로 %5.1f A, DAB 첨두 %5.1f A(상한 %.1f, 유지 %.0f·붕괴 %.0f), 버스 최저 %.0f V(연결 중 최고 %.0f V), "
              "제동 %.1f J, 소프트 %.3f J, 붕괴 ≤ %.1f ms%s" % (k, g["passed"], g["n"], g["path"], g["dab"], g["lim"], g["dab_hold"], g["dab_col"], g["bus_min"],
                                                g["bus_loaded"], g["brk"], g["soft"], g["col"], ("  실패 " + str({c: len(v) for c, v in g["fails"].items()})) if g["fails"] else ""))
    p3 = [r for r in rows if r["pol_name"] == "P3" and not r.get("tag")]
    verdict("P3(정합 유지 + EPS 첨두 상한 + 일시 감발) 기본 사례 전부 통과", all(r["pass_"] for r in p3), "%d/%d" % (sum(r["pass_"] for r in p3), len(p3)))
    save_json(EID, "compare", dict(groups=groups, rows=rows, settings=dict(PK_FAULT=E17.PK_FAULT, T_RESTORE=E17.T_RESTORE, policies=POLICIES)))


# ----------------------------------------------------------------------------------------------
def figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    case = "W460_240s"; p, _ = E19.plant(case)
    rated = E17.dab_sps_peak(460., 100., p.power_max / 100., p); lim = E17.PK_FAULT * rated
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.4))
    # (a) 첨두 - 링크전압
    vls = np.linspace(0., 100., 101)
    for I, ls in ((-11., "-"), (-40., "--")):
        ax[0].plot(vls, [DM.peak_A(504., v, I, p, "sps") for v in vls], color=C["orange"], ls=ls, lw=1.3, label="SPS, 링크전류 %.0f A" % I)
        ax[0].plot(vls, [DM.peak_A(504., v, I, p, "eps") for v in vls], color=C["blue"], ls=ls, lw=1.3, label="EPS(첨두 최소), %.0f A" % I)
    ax[0].axhline(rated, color=C["green"], ls=":", lw=.9); ax[0].text(1, rated + 3, "정격점 %.1f A" % rated, fontsize=7, color=C["green"])
    ax[0].axhline(lim, color=C["red"], ls=":", lw=.9); ax[0].text(1, lim + 3, "상한 1.5배 %.1f A" % lim, fontsize=7, color=C["red"])
    ax[0].set_xlabel("링크전압 v_link [V]"); ax[0].set_ylabel("DAB 링크 쪽 순시 첨두 [A]"); ax[0].set_ylim(0, 220)
    ax[0].set_title("(a) 버스 504 V(n = 4.6): 링크전압과 첨두", fontsize=9); ax[0].legend(fontsize=7, loc="upper right")
    # (b) 한 주기 인덕터 전류
    th = np.linspace(0, 2 * np.pi, 721)
    wl = 2 * np.pi * p.fs * p.Ldab / p.turns ** 2; v1 = 504. / p.turns; Ib = v1 / wl; vl = 5.; I = -11.
    def trace(d, a):
        s1 = np.where(np.mod(th, np.pi) < d, 1., 0.) * np.where(th < np.pi, 1., -1.)
        s2 = np.where(np.mod(th - a, 2 * np.pi) < np.pi, 1., -1.)
        v = v1 * s1 - vl * s2
        i = np.concatenate([[0.], np.cumsum((v[1:] + v[:-1]) / 2 * np.diff(th))]) / wl
        i = i - (i.max() + i.min()) / 2
        return i, s1, s2
    phi = DM.sps_phase(I / Ib)
    i_s, _, _ = trace(np.pi, np.mod(phi, 2 * np.pi))
    d, a, D1, _ = DM.eps_params(504., vl, I, p)
    i_e, s1e, _ = trace(d, a)
    ax[1].plot(np.degrees(th), i_s, color=C["orange"], lw=1.3, label="SPS(φ = %.2f rad)" % phi)
    ax[1].plot(np.degrees(th), i_e, color=C["blue"], lw=1.5, label="EPS(1차 펄스 %.0f°, D1 = %.2f)" % (np.degrees(d), D1))
    ax[1].plot(np.degrees(th), 15 * s1e, color=C["gray"], lw=.8, label="EPS 1차 전압(척도 15 A)")
    ax[1].set_xlabel("θ [°] (한 스위칭 주기 5 µs)"); ax[1].set_ylabel("링크 쪽 환산 인덕터 전류 [A]"); ax[1].set_xlim(0, 360)
    ax[1].set_title("(b) 링크 5 V에서 링크 → 버스 11 A: 같은 평균전류, 첨두 %.0f A → %.0f A" % (np.abs(i_s).max(), np.abs(i_e).max()), fontsize=9)
    ax[1].legend(fontsize=7, loc="lower right")
    # (c) 시간 궤적 P0 vs P3: 회로 사례와 같은 분리 3 ms로 계산하고 회로(TB09 = P0, TB10 = P3)의 n·max|i_L|을 겹친다
    tbroot = os.path.join(os.path.dirname(__file__), "..", "..", "..", "simulink", "tb")
    circ = {"P0": os.path.join(tbroot, "TB09_R2_Protection", "results", "TB09_A_1008V_hbopen_25kW_periods.csv"),
            "P3": os.path.join(tbroot, "TB10_R2_FaultMod", "results", "TB10_A_1008V_hbopen_25kW_periods.csv")}
    for name, col in (("P0", C["orange"]), ("P3", C["blue"])):
        m = E17.r2_run(dict(case=case, V=1008., P=25000., event="hb_open", policy="clamp_brk", keep=True, t_shed=3e-3,
                            **{k: v for k, v in POLICIES[name].items() if k != "dmod_metric"}))
        t = m["trace"]["t"] * 1e3; L = m["trace"]["log"]; ev = dict((e[0], e[1]) for e in m["events"])
        t_end = ev.get("DEGRADED", t[-1]) + E17.T_EV * 1e3
        mode = "eps" if name == "P3" else "sps"
        pk = np.array([DM.peak_A(L[i, 2], L[i, 4], L[i, 5], p, mode) if (t[i] >= E17.T_EV * 1e3 and t[i] <= t_end) else np.nan
                       for i in range(0, len(t), 5)])
        ax[2].plot(t[::5], pk, color=col, lw=1.2, label="%s 해석(E17 궤적)" % name)
        if os.path.exists(circ[name]):
            Z = np.loadtxt(circ[name], delimiter=","); zs = np.round(Z[:, 15])
            zpk = p.turns * Z[:, 13]; zpk[~np.isin(zs, [3, 4, 5, 9, 10, 11])] = np.nan
            ax[2].plot(Z[:, 0] * 1e3, zpk, color=col, lw=.8, alpha=.55, label="%s 회로(%s): n·max|i_L|" % (name, "TB09" if name == "P0" else "TB10"))
    ax[2].axhline(lim, color=C["red"], ls=":", lw=.9); ax[2].text(.3, lim + 3, "상한 1.5배", fontsize=7, color=C["red"])
    ax[2].axhline(2 * rated, color=C["gray"], ls=":", lw=.9); ax[2].text(.3, 2 * rated + 3, "회로 판정 2배", fontsize=7, color=C["gray"])
    ax[2].set_xlim(0, 16)
    ax[2].set_xlabel("시간 [ms]"); ax[2].set_ylabel("DAB 링크 쪽 순시 첨두 [A]"); ax[2].set_ylim(0, 210)
    ax[2].set_title("(c) 1008 V·25 kW H-브리지 개방(분리 3 ms): E17 추천(P0) 대 새 순서(P3)", fontsize=9); ax[2].legend(fontsize=7, loc="upper right")
    fig.tight_layout(); fig.savefig(os.path.join(outdir(EID), "E20_dab_fault_modulation.png"), dpi=150); plt.close(fig)
    print("  figures saved")


PARTS = dict(table=table, compare=compare, figures=figures)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        print("==== E20 %s ====" % w, flush=True)
        PARTS[w]()
