"""[E21] DAB 고장 모드 변조의 회로 여유: 데드타임·출력용량·역방향 도통을 넣은 첨두 표로 1.5배 상한 지키기.

■ 목적
  E20의 EPS 지령표(이상 소자 해석)로 첨두를 1.5 × 정격점에 묶었지만, TB10 회로에서는 링크 붕괴 구간의 첨두가 해석의
  1.10–1.16배(79.4·75.3 A)였다. 이 시험은 (1) 초과의 원인을 스위칭 수준 정상상태 모의(dab_switching.py)로 재현해 확인하고,
  (2) 회로 블록이 쓰는 첨두 표를 같은 (D1, φ)의 스위칭 반영값으로 바꾼 강등 방식(P3s)이 평균모델에서 통과하는지 본다.
  회로 확인은 Simulink TB11이 같은 표로 한다.

■ 왜 필요한가
  상한을 해석으로만 정하면 회로에서 얼마나 넘을지 알 수 없다. 해석 상한을 경험적으로 낮추는 방법(E20 감도 1.3배)은 근거가 약하고
  붕괴가 시간 상한(10 ms)에 걸렸다. 원인을 모델로 재현하면 같은 모델로 표를 고칠 수 있고, 하드웨어의 데드타임이 바뀌어도 다시 계산할 수 있다.

■ 방법
  table   : 스위칭 표(R2-W460·W410). 확인 네 가지 — (a) 소자 효과를 끈 모의가 이상 해석과 같은지,
            (b) TB10 회로의 붕괴 주기 첨두를 같은 (v_bus, v_link)의 모의가 재현하는지, (c) 효과별 기여(데드타임·출력용량·V_f),
            (d) 회로 블록과 같은 탐색을 스위칭 표로 하고 실제 버스전압에서 모의한 첨두가 1.5배 안인지(버스 380–505 V × 링크 1–95 V)
  compare : E17 상태기계 P3s(= E20 P3 + 스위칭 표, 설계 상한 1.455배 = 1.5배 / 1.03) 기본 8사례와 감도.
            P3t(설계 상한 1.387배 = 1.5배 / (1.03 · 1.05), TB12 회로에서 잰 지령 전이 첨두 여유 5 %) 기본 8사례와 분리 3 ms
  figures : 허용 전류(이상 대 스위칭 1.455·1.387배), TB10 회로 첨두 재현, P3s·P3t 시간 궤적과 회로 TB10–TB13

■ 판정(시험 전에 고정)
  (a) 첨두·전류 오차 ≤ 0.5 %. (b) 정보(회로/모의 비의 최대·평균 기록). (d) 첨두 ≤ 1.5 × 정격점(설계 여유 3 %는 (b)의 최대 차에서 정함).
  compare: E17 고장 판정 + 스위칭 반영 DAB 첨두 ≤ 1.5 × 정격점(W460 68.7 A, W410 90.0 A).

■ 실행   python E21_dab_switching_margin.py table compare figures
■ 결과   results/E21/sw_table_n4.6.json·n4.1.json, table.json, compare.json, E21_*.png
■ 보고서 수치(docs/26)
  (a) 오차 ≤ 0.10 %. (b) TB10 붕괴 구간 회로/모의 최대 1.029·1.020, 평균 1.003·1.001(회로/해석 최대 1.131·1.098).
  (c) 버스 447 V·링크 52.8 V: 해석 67.6 → 데드타임 74.6 → + 출력용량 74.0 → + V_f 74.4 A. (d) 최대 1.466·1.462배.
  compare: P3s 기본 8/8(66.8·87.4 A), 감도 9/10(W410 감쇠기 없음 100.3 A). P3t 기본 8/8(63.7·83.4 A, 소프트 투입 ≤ 0.058 J), 분리 3 ms 2/2.
  회로: TB11(이 표) 정상 주기 첨두는 해결, 지령표 칸 전환 과도로 88.5·68.9 A 불통과 → TB12(게이트 생성기의 직류 편류 방지·변화율 상한)
        70.0·68.5 A 1/2 통과(전이 끝 정상 상한 위 4.9 %) → TB13(P3t, 전이 여유 5 %).
"""
import json
import math
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

from common import save_json, verdict, workers, outdir
import dab_modulation as DM
import dab_switching as SW
import E17_protection_integration as E17
import E19_r2_window_module as E19

EID = "E21"
PK_DESIGN = 1.455            # 설계 상한 = 1.5 × 정격점 / 1.03(회로와 스위칭 모의의 차 ≤ 2.8 %, (b))
PK_TR = round(1.5 / (1.03 * 1.05), 3)   # 1.387: 여기에 지령 전이 여유 5 %(TB12 회로: 전이 주기 첨두가 정상 상한 위 최대 4.9 %)
P3 = dict(hold="match", dmod="eps", soft_fail=True, curtail=True)
P3S = dict(P3, pk_table="sw", pk_fault=PK_DESIGN)
P3T = dict(P3, pk_table="sw", pk_fault=PK_TR)
VS = {"W460_240s": [930., 1008.], "W410_spec": [860., 920.]}
TBDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "simulink", "tb")


def rated(p, VW):
    return E17.dab_sps_peak(VW, 100., p.power_max / 100., p)


# ----------------------------------------------------------------------------------------------
def table():
    p, _ = E19.plant("W460_240s"); p4, _ = E19.plant("W410_spec")
    t0 = time.time(); DM.sw_table(p); DM.sw_table(p4)
    print("  스위칭 표 준비 %.0f s" % (time.time() - t0))
    wl = 2 * math.pi * p.fs * p.Ldab / p.turns ** 2
    # (a) 효과를 끈 모의 = 이상 해석
    pts, err = [], 0.
    for vb, vl, I in ((480., 55., -40.), (450., 20., -30.), (500., 89., -45.), (460., 100., 40.), (410., 5., -11.), (500., 70., -25.)):
        d, a, D1, phi = DM.eps_params(vb, vl, I, p)
        Ib = vb / p.turns / wl
        jn, pkn, _ = DM.wave_norm(vl / (vb / p.turns), (1 - D1) * np.pi, phi - D1 * np.pi)
        pk, il, _ = SW.steady(vb, vl, D1, phi, p, td=0., cp=1e-15, cs=1e-15, vf=0., R=1e-9)
        e = max(abs(pk / (float(pkn) * Ib) - 1), abs(il - float(jn) * Ib) / max(abs(float(jn) * Ib), 1.))
        err = max(err, e); pts.append(dict(vb=vb, vl=vl, I=I, pk_ideal=float(pkn) * Ib, pk_sim=pk, il_ideal=float(jn) * Ib, il_sim=il))
    verdict("(a) 소자 효과를 끈 스위칭 모의 = 이상 해석(첨두·전류 오차 ≤ 0.5 %)", err <= 0.005, "최대 %.3f %%" % (100 * err))
    # (b) TB10 회로 재현
    tab = DM.circuit_tables(); pk_t = 1.5 * rated(p, 460.)
    rep = {}
    for c in ("A_1008V_hbopen_25kW", "B_930V_hbopen_25kW"):
        f = os.path.join(TBDIR, "TB10_R2_FaultMod", "results", "TB10_%s_periods.csv" % c)
        if not os.path.exists(f):
            continue
        Z = np.loadtxt(f, delimiter=","); st = np.round(Z[:, 15])
        rows = []
        for q in range(100, len(Z)):
            if not (st[q - 100:q + 1] == 10).all() or Z[q, 4] < 6.:     # 붕괴 0.5 ms 뒤, 링크 ≥ 6 V(지령이 상한에 붙은 구간)
                continue
            if (q - 100) % 10:
                continue
            D1, phi, icmd, Ib = DM.circuit_map(Z[q - 1, 1], Z[q - 1, 4], -200., p, pk_t, tab)
            jn, pkn, _ = DM.wave_norm(Z[q - 1, 4] / (Z[q - 1, 1] / p.turns), (1 - D1) * np.pi, phi - D1 * np.pi)
            pk, il, _ = SW.steady(Z[q, 1], Z[q, 4], D1, phi, p)
            rows.append([Z[q, 0] * 1e3, Z[q, 1], Z[q, 4], D1, float(pkn) * Ib, pk, p.turns * Z[q, 13], icmd, il])
        R = np.array(rows)
        rep[c] = dict(n=len(R), circ_over_sim_max=float((R[:, 6] / R[:, 5]).max()), circ_over_sim_mean=float((R[:, 6] / R[:, 5]).mean()),
                      circ_over_ideal_max=float((R[:, 6] / R[:, 4]).max()), sim_over_ideal_max=float((R[:, 5] / R[:, 4]).max()),
                      rows=R.tolist())
        print("  (b) TB10 %s: %d주기, 회로/모의 최대 %.3f·평균 %.3f, 회로/해석 최대 %.3f, 모의/해석 최대 %.3f" % (
            c[:1], len(R), rep[c]["circ_over_sim_max"], rep[c]["circ_over_sim_mean"], rep[c]["circ_over_ideal_max"], rep[c]["sim_over_ideal_max"]))
    # (c) 효과별 기여
    contrib = []
    for vb, vl in ((447., 52.8), (460., 39.3), (476., 23.6), (431., 68.3)):
        D1, phi, icmd, Ib = DM.circuit_map(vb, vl, -200., p, pk_t, tab)
        row = dict(vb=vb, vl=vl, D1=D1, icmd=icmd)
        for name, kw in (("ideal", dict(td=0., cp=1e-15, cs=1e-15, vf=0.)), ("td", dict(cp=1e-15, cs=1e-15, vf=0.)),
                         ("td_coss", dict(vf=0.)), ("all", {})):
            pk, il, _ = SW.steady(vb, vl, D1, phi, p, **kw); row[name] = [pk, il]
        contrib.append(row)
        print("  (c) v_bus %.0f V, 링크 %.1f V: 이상 %.1f A → 데드타임 %.1f → + 출력용량 %.1f → + V_f %.1f A" % (
            vb, vl, row["ideal"][0], row["td"][0], row["td_coss"][0], row["all"][0]))
    # (d) 스위칭 표로 탐색한 지령의 실제 첨두(실제 버스전압에서 모의)
    chk = {}
    for case in VS:
        pc, _ = E19.plant(case); VW = E19.CASES[case]["VW"]; rk = rated(pc, VW)
        Tsw = DM.sw_table(pc)
        swtab = dict(d=tab["d"], phi=tab["phi"], pk=Tsw["pk_sw"], r0=tab["r0"], dr=tab["dr"], j0=tab["j0"], dj=tab["dj"])
        worst = 0.; wat = None; nn = 0
        for vb in np.arange(337., 506., 13.):
            for vl in np.arange(1., 96., 4.7):
                D1, phi, icmd, Ib = DM.circuit_map(vb, vl, -500., pc, PK_DESIGN * rk, swtab)
                pk, il, _ = SW.steady(vb, vl, D1, phi, pc)
                nn += 1
                if pk / rk > worst:
                    worst, wat = pk / rk, (float(vb), float(vl))
        chk[case] = dict(rated=rk, worst_ratio=worst, at=wat, n=nn)
        verdict("(d) %s: 스위칭 표 탐색 지령의 첨두 ≤ 1.5 × 정격점(%d점)" % (case[:4], nn), worst <= 1.5, "최대 %.3f배(v_bus %.0f V, 링크 %.1f V)" % (worst, *wat))
    save_json(EID, "table", dict(ideal_check=pts, ideal_check_err=err, tb10=rep, contrib=contrib, map_check=chk, pk_design=PK_DESIGN,
                                 device=dict(td=SW.TD, coss_p=SW.COSS_P, coss_s=SW.COSS_S, vf=SW.VF, rdab=SW.RDAB, vbs=list(SW.VB_SW))))


# ----------------------------------------------------------------------------------------------
def _job(a):
    name, j = a
    m = E17.r2_run(j)
    m["pol_name"] = name
    ev = dict((e[0], e[1]) for e in m["events"])
    m["collapse_ms"] = (ev["SOFT_BYP"] - ev["HB_COLLAPSE"]) if ("SOFT_BYP" in ev and "HB_COLLAPSE" in ev) else None
    m["checks"]["dab_peak_1p5x"] = m["dab_sec_peak"] <= m["dab_rated_sec_peak"] * E17.PK_FAULT * 1.005
    m["pass_"] = bool(all(m["checks"].values()))
    m.pop("trace", None)
    return m


def jobs():
    js = []
    for case, Vs in VS.items():
        for V in Vs:
            for P in (5000., 25000.):
                js.append(("P3s", dict(case=case, V=V, P=P, event="hb_open", policy="clamp_brk", **P3S)))
                js.append(("P3t", dict(case=case, V=V, P=P, event="hb_open", policy="clamp_brk", **P3T)))
    for case, Vs in VS.items():
        base = dict(case=case, V=Vs[-1], P=25000., event="hb_open", policy="clamp_brk", **P3S)
        js += [("P3s", dict(base, damper=False, tag="감쇠기 없음")), ("P3s", dict(base, vd=1.4, tag="V_D 1.4 V")),
               ("P3s", dict(base, vd=3.0, tag="V_D 3.0 V")), ("P3s", dict(base, t_shed=50e-3, tag="분리 50 ms")),
               ("P3s", dict(base, t_shed=3e-3, tag="분리 3 ms(회로 사례)")),
               ("P3t", dict(base, **dict(P3T, t_shed=3e-3), tag="분리 3 ms(회로 사례)"))]
    return js


def compare():
    js = jobs(); t0 = time.time()
    with Pool(workers()) as pool:
        rows = pool.map(_job, js, chunksize=1)
    print("  compare: %d건, %.0f s" % (len(rows), time.time() - t0))
    groups = {}
    for r in rows:
        k = "%s|%s%s" % (r["case"], r["pol_name"], ("|" + r["tag"]) if r.get("tag") else "")
        g = groups.setdefault(k, dict(n=0, passed=0, path=0., dab=0., dab_hold=0., bus_min=1e9, brk=0., soft=0., col=0., fails={},
                                      lim=r["dab_peak_limit"], rated=r["dab_rated_sec_peak"]))
        g["n"] += 1; g["passed"] += int(r["pass_"])
        g["path"] = max(g["path"], r["path_peak"]); g["dab"] = max(g["dab"], r["dab_sec_peak"])
        g["dab_hold"] = max(g["dab_hold"], r.get("dab_peak_hold") or 0.); g["bus_min"] = min(g["bus_min"], r["vbus_min"])
        g["brk"] = max(g["brk"], r["brk_energy_J"]); g["soft"] = max(g["soft"], r["soft_energy_J"] or 0.)
        g["col"] = max(g["col"], r.get("collapse_ms") or 0.)
        for c, ok in r["checks"].items():
            if not ok:
                g["fails"].setdefault(c, []).append((r["V"], r["P"]))
    for k, g in groups.items():
        print("  %-36s %2d/%2d, 경로 %5.1f A, DAB 첨두(스위칭) %5.1f A(설계 %.1f, 판정 %.1f, 유지 %.0f), 버스 최저 %.0f V, 제동 %.1f J, "
              "소프트 %.3f J, 붕괴 ≤ %.1f ms%s" % (k, g["passed"], g["n"], g["path"], g["dab"], g["lim"], 1.5 * g["rated"], g["dab_hold"],
                                              g["bus_min"], g["brk"], g["soft"], g["col"], ("  실패 " + str({c: len(v) for c, v in g["fails"].items()})) if g["fails"] else ""))
    for pol, k in (("P3s", PK_DESIGN), ("P3t", PK_TR)):
        base = [r for r in rows if not r.get("tag") and r["pol_name"] == pol]
        verdict("%s(스위칭 표, 설계 %.3f배) 기본 사례 전부 통과" % (pol, k), all(r["pass_"] for r in base), "%d/%d" % (sum(r["pass_"] for r in base), len(base)))
    save_json(EID, "compare", dict(groups=groups, rows=rows, settings=dict(PK_DESIGN=PK_DESIGN, PK_TR=PK_TR, P3S=P3S, P3T=P3T)))


# ----------------------------------------------------------------------------------------------
def figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    p, _ = E19.plant("W460_240s"); rk = rated(p, 460.)
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.4))
    # (a) 허용 링크전류(첨두 상한): 이상 표 1.5배 대 스위칭 표 1.455배
    vls = np.linspace(1, 95, 120)
    for vb, ls in ((440., "-"), (500., "--")):
        ax[0].plot(vls, [DM.eps_ilim(vb, v, p, 1.5 * rk) for v in vls], color=C["orange"], ls=ls, lw=1.3, label="이상 표, 1.5배(E20), 버스 %.0f V" % vb)
        ax[0].plot(vls, [DM.sw_ilim(vb, v, p, PK_DESIGN * rk) for v in vls], color=C["blue"], ls=ls, lw=1.5, label="스위칭 표, 1.455배(E21), 버스 %.0f V" % vb)
        ax[0].plot(vls, [DM.sw_ilim(vb, v, p, PK_TR * rk) for v in vls], color=C["green"], ls=ls, lw=1.2, label="스위칭 표 + 전이 여유, 1.387배, 버스 %.0f V" % vb)
    ax[0].set_xlabel("링크전압 [V]"); ax[0].set_ylabel("허용 링크 → 1차 전류 [A]"); ax[0].set_ylim(0, 70)
    ax[0].set_title("(a) 첨두 상한이 허용하는 DAB 전류", fontsize=9); ax[0].legend(fontsize=6.5)
    # (b) TB10 회로 재현
    T = json.load(open(os.path.join(outdir(EID), "table.json"), encoding="utf-8"))
    if "A_1008V_hbopen_25kW" in T["tb10"]:
        R = np.array(T["tb10"]["A_1008V_hbopen_25kW"]["rows"])
        ax[1].plot(R[:, 2], R[:, 4], "o", ms=3, color=C["orange"], label="이상 해석(E20 표)")
        ax[1].plot(R[:, 2], R[:, 5], "s", ms=3, color=C["blue"], label="스위칭 모의(데드타임·C_oss·V_f)")
        ax[1].plot(R[:, 2], R[:, 6], "x", ms=4, color="k", label="TB10 회로 n·max|i_L|")
        ax[1].axhline(1.5 * rk, color=C["red"], ls=":", lw=.9); ax[1].text(14, 1.5 * rk + .6, "1.5배", fontsize=7, color=C["red"])
        ax[1].invert_xaxis(); ax[1].set_xlabel("링크전압 [V](붕괴 진행 →)"); ax[1].set_ylabel("DAB 링크 쪽 첨두 [A]")
        ax[1].set_ylim(55, 82); ax[1].legend(fontsize=7, loc="lower left")
        ax[1].set_title("(b) TB10 사례 A 붕괴 구간: 회로 첨두를 스위칭 모의가 재현", fontsize=9)
    # (c) P3s 시간 궤적(분리 3 ms) + TB11 회로
    m = E17.r2_run(dict(case="W460_240s", V=1008., P=25000., event="hb_open", policy="clamp_brk", keep=True, t_shed=3e-3, **P3S))
    t = m["trace"]["t"] * 1e3; L = m["trace"]["log"]; ev = dict((e[0], e[1]) for e in m["events"])
    t_end = ev.get("DEGRADED", t[-1]) + E17.T_EV * 1e3
    ax[2].plot(t, L[:, 4], color=C["green"], lw=1., label="링크전압 [V](E17 P3s)")
    m3 = E17.r2_run(dict(case="W460_240s", V=1008., P=25000., event="hb_open", policy="clamp_brk", keep=True, t_shed=3e-3, **P3T))
    ax[2].plot(m3["trace"]["t"] * 1e3, m3["trace"]["log"][:, 4], color=C["green"], lw=1., ls="--", label="링크전압 [V](E17 P3t)")
    f11 = os.path.join(TBDIR, "TB11_R2_FaultMod_SW", "results", "TB11_A_1008V_hbopen_25kW_periods.csv")
    f10 = os.path.join(TBDIR, "TB10_R2_FaultMod", "results", "TB10_A_1008V_hbopen_25kW_periods.csv")
    f12 = os.path.join(TBDIR, "TB12_R2_FaultMod_TR", "results", "TB12_A_1008V_hbopen_25kW_periods.csv")
    f13 = os.path.join(TBDIR, "TB13_R2_FaultMod_TA", "results", "TB13_A_1008V_hbopen_25kW_periods.csv")
    for f, col, lab in ((f10, C["orange"], "TB10 회로(이상 표)"), (f11, C["gray"], "TB11 회로(스위칭 표)"),
                        (f12, C["blue"], "TB12 회로(+ 전이 변화율 상한)"), (f13, "k", "TB13 회로(+ 전이 여유)")):
        if os.path.exists(f):
            Z = np.loadtxt(f, delimiter=","); zs = np.round(Z[:, 15]); zpk = p.turns * Z[:, 13]
            zpk[~np.isin(zs, [9, 10, 11])] = np.nan
            ax[2].plot(Z[:, 0] * 1e3, zpk, color=col, lw=.8, label=lab + ": n·max|i_L|")
    ax[2].axhline(1.5 * rk, color=C["red"], ls=":", lw=.9); ax[2].text(.3, 1.5 * rk + 1, "1.5배", fontsize=7, color=C["red"])
    ax[2].set_xlim(0, 16); ax[2].set_ylim(0, 110); ax[2].set_xlabel("시간 [ms]"); ax[2].set_ylabel("[A] / [V]")
    ax[2].set_title("(c) 1008 V·25 kW H-브리지 개방(분리 3 ms): 강등 중 DAB 첨두", fontsize=9); ax[2].legend(fontsize=6.5, loc="upper right")
    fig.tight_layout(); fig.savefig(os.path.join(outdir(EID), "E21_dab_switching_margin.png"), dpi=150); plt.close(fig)
    print("  figures saved")


PARTS = dict(table=table, compare=compare, figures=figures)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        print("==== E21 %s ====" % w)
        PARTS[w]()
