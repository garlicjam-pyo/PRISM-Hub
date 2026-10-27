"""[E27] Stage A 영교차 추종 게이트의 방향 반전 처리: 무장하지 못한 반주기를 공칭 도통시간에 끈다.

■ 목적
  TB20 사례 D(800 V, 충전기 0 → 375 A, 3.75 A/µs)에서 턴오프 7,027번 가운데 1번이 1.010 A로 기준(1.0 A)을 넘었다
  (docs/31). 모듈 전류가 주행 방향 경부하(모듈당 약 9 A)에서 충전 방향으로 바뀌는 사이 한 반주기의 첨두가 2.44 A로
  영교차 검출기의 무장 문턱(5 × i_thr = 2.5 A)보다 작아, 검출 없이 최대 도통시간(공칭의 1.12배)에 꺼졌고 그때 전류는
  이미 반대 방향이었다. 이 시험은
  (1) 같은 기구를 스위칭 모델에서 재현하고(repro),
  (2) 무장하지 못한 반주기를 공칭 도통시간 t_on에서 끄는 게이트(unarmed_stop='nom')로 방향 반전을 여러 조건에서
      판정하며(repro, stress),
  (3) 이 변경이 기존 결과를 바꾸지 않는지 회귀한다(regress: E1 공차 표본, E24 정상·과도).
  회로 확인은 TB21(TB20 회로 + 같은 게이트 변경)이다.

■ 왜 필요한가
  무장 문턱은 잡음과 시작 과도에서 잘못 영교차로 보지 않으려는 장치다. 그 대가로 첨두가 문턱보다 작은 반주기는
  영교차를 검출할 수 없다. 이런 반주기는 정상 운전에서는 없고, 모듈 전류가 0을 지나는 순간(충전 시작·종료, 회생
  전환)에만 생긴다. 최대 도통시간은 공진주파수가 낮아진 위상(공차)이 영교차 전에 꺼지지 않도록 공칭보다 길게(1.12배)
  잡았기 때문에, 첨두가 작은 반주기를 거기까지 두면 영교차를 지나 반대 방향 전류가 자란 뒤에 끈다. 공칭 도통시간에서는
  첨두가 무장 문턱(2.5 A)보다 작은 반주기의 전류가 공진주파수 −10 %에서도 약 0.9 A 이하다(첨두 × sin(π·0.88)).

■ 게이트 변경(model_stage_a.sim_array unarmed_stop, 회로 ctrl/prism_gate_stageA_zcp_r.m)
  무장한 반주기: 그대로(영교차 검출 뒤 끔, 아니면 최대 도통시간).
  무장하지 못한 반주기: 공칭 도통시간 t_on = 1/(2 f_r0) − t_d에서 끈다(이전: 최대 도통시간 1.12·t_on).

■ 판정 기준(시험 전에 고정. repro의 첫 탐색 실행 뒤, stress·regress 실행 전에 정함)
  (R1) 재현(정보): 이전 게이트에서 방향 반전의 가장 큰 턴오프 전류가 무장하지 못한 반주기에서 나오는지
  (G1) 새 게이트: repro·stress의 모든 턴오프 |i_off| ≤ max(5 % × 그 반주기 첨두, 1.0 A)(E24·TB20의 T1·C5와 같음)
  (G2) 회귀: E1 공차 표본(정격 46.875 A 정·역방향 20개)의 턴오프 전류/피크가 이전과 같음(차 ≤ 1e-6),
       E24 정상 26점 판정이 같고 턴오프 비율 차 ≤ 0.1 %p, E24 과도 10사례 판정이 같고 위상 첨두 차 ≤ 0.5 A·V_A 차 ≤ 0.05 V
■ 실행   python E27_zcp_reversal.py repro stress regress figures   (2코어 약 15분)
■ 결과   results/E27/repro.json, stress.json, regress.json, E27_zcp_reversal.png
"""
import json
import sys
from multiprocessing import Pool

import numpy as np

import model_stage_a as A
import E24_stage_a_shedding as E24
from common import save_json, verdict, outdir, workers

EID = "E27"
T = 1 / A.FR0
DF = True
I_ABS = 1.0
BUS = dict(E24.BUS, RA=10.2e-3)            # R2 버스(E23·E24·TB20과 같음). RA는 초기값용
TOL = dict(C=0.05, L=0.10, R=0.10)         # E1 공차 표본과 같은 공차


def turnoffs_arm(r, t0):
    """턴오프 목록: (위상, 시각, 턴오프 전류, 반주기 첨두, 무장 여부)."""
    out = []
    for (k, t, i, pk) in E24.turnoffs(r, t0):
        o = int(round(t / r["dt"]))
        out.append((k, float(t), float(i), pk, int(r["arm"][o, k])))
    return out


def judge(to):
    bad = [x for x in to if abs(x[2]) > max(0.05 * x[3], I_ABS)]
    un = [x for x in to if x[4] == 0]
    worst = max(to, key=lambda x: abs(x[2]) - max(0.05 * x[3], I_ABS))
    return dict(n=len(to), n_bad=len(bad), n_unarmed=len(un), ioff_max=max(abs(x[2]) for x in to),
                ioff_unarmed_max=max((abs(x[2]) for x in un), default=0.), unarmed_pk_max=max((x[3] for x in un), default=0.),
                worst=dict(phase=worst[0], t_ms=worst[1] * 1e3, i_off=worst[2], pk=worst[3], armed=worst[4]),
                bad=[dict(phase=x[0], t_ms=x[1] * 1e3, i_off=x[2], pk=x[3], armed=x[4]) for x in bad[:5]])


# ---------------------------------------------------------------- repro: TB20 사례 D(4모듈 8위상)
D_OFFS = (0., 1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6)          # 충전기 램프 시작을 스위칭 주기 안에서 옮긴다


def _repro(args):
    g, off, tol = args
    t1 = 0.3e-3 + off * T
    prof = ([0, t1, t1 + 100e-6, 0.8e-3, 0.9e-3, 1], [0, 0, -375., -375., 0, 0])   # V_A 노드 주입(음수)
    r = A.sim_array(N=8, Vbat=800., Iload=prof, Cbus=400e-6, mode="zcp", ncyc=int(1.1e-3 / T),
                    tol=TOL if tol else None, rs=A.matlab_rng(3) if tol else None,
                    bus=dict(BUS, RA=10.2e-3 / 4, P=([0, 1], [15e3, 15e3])), dead_fix=DF, unarmed_stop=g)
    return dict(gate=g, off=off, tol=tol, **judge(turnoffs_arm(r, 0.25e-3)))


def repro():
    jobs = [(g, off, False) for g in ("max", "nom") for off in D_OFFS] + [(g, 0., True) for g in ("max", "nom")]
    with Pool(workers()) as p:
        rows = p.map(_repro, jobs)
    for x in rows:
        print("  %s 시작 +%.2fT 공차 %s: 턴오프 %d, 위반 %d, 무장 못 함 %d(첨두 ≤ %.2f A, 턴오프 ≤ %.2f A), 전체 최대 %.2f A"
              % (x["gate"], x["off"], "있음" if x["tol"] else "없음", x["n"], x["n_bad"], x["n_unarmed"],
                 x["unarmed_pk_max"], x["ioff_unarmed_max"], x["ioff_max"]))
    old = [x for x in rows if x["gate"] == "max"]; new = [x for x in rows if x["gate"] == "nom"]
    r1 = all(x["worst"]["armed"] == 0 for x in old)
    verdict("(R1) 이전 게이트: 방향 반전의 최대 턴오프 전류가 무장하지 못한 반주기에서 나옴(정보)", r1,
            "최대 %.2f A" % max(x["ioff_max"] for x in old))
    g1 = all(x["n_bad"] == 0 for x in new)
    verdict("(G1) 새 게이트: TB20 사례 D 조건의 모든 턴오프 ≤ max(5 %·첨두, 1 A)", g1,
            "무장 못 한 반주기 턴오프 최대 %.2f A, 전체 최대 %.2f A"
            % (max(x["ioff_unarmed_max"] for x in new), max(x["ioff_max"] for x in new)))
    save_json(EID, "repro", dict(rows=rows, R1=r1, G1=g1))


# ---------------------------------------------------------------- stress: 모듈 하나(2위상), 방향 반전 격자
ST_V = (540., 800., 1008.)
ST_SLOPE = (0.9375e6, 0.09375e6)            # 모듈당 충전 램프 요구(0.94 A/µs)와 그 1/10 [A/s]
ST_DIR = ("start", "stop")                  # 충전 시작(0 → −30 A 주입), 충전 종료(−30 → 0 A)
ST_TOL = (None, 1, 2, 3)                    # 공차 없음 + 공차 표본 3개(matlab_rng 시드)


def _stress(args):
    g, V, sl, d, seed = args
    P = 3.75e3 * V / 800.                   # 버스 전류가 배터리 전압과 상관없이 모듈당 약 9.4 A가 되도록
    t1 = 0.3e-3; t2 = t1 + 30. / sl
    a, b = (0., -30.) if d == "start" else (-30., 0.)
    prof = ([0, t1, t2, 1], [a, a, b, b])
    tend = t2 + 0.15e-3
    r = A.sim_array(N=2, Vbat=V, Iload=prof, Cbus=400e-6, mode="zcp", ncyc=int(tend / T),
                    tol=TOL if seed else None, rs=A.matlab_rng(seed) if seed else None,
                    bus=dict(BUS, P=([0, 1], [P, P])), dead_fix=DF, unarmed_stop=g)
    return dict(gate=g, V=V, slope=sl, dir=d, seed=seed, **judge(turnoffs_arm(r, 0.25e-3)))


def stress():
    jobs = [(g, V, sl, d, s) for g in ("max", "nom") for V in ST_V for sl in ST_SLOPE for d in ST_DIR for s in ST_TOL]
    with Pool(workers()) as p:
        rows = p.map(_stress, jobs)
    for g in ("max", "nom"):
        R = [x for x in rows if x["gate"] == g]
        print("  %s: %d사례, 위반 %d건(사례 %d), 무장 못 한 반주기 %d번, 그 턴오프 최대 %.2f A, 전체 턴오프 최대 %.2f A"
              % (g, len(R), sum(x["n_bad"] for x in R), sum(x["n_bad"] > 0 for x in R), sum(x["n_unarmed"] for x in R),
                 max(x["ioff_unarmed_max"] for x in R), max(x["ioff_max"] for x in R)))
    new = [x for x in rows if x["gate"] == "nom"]
    g1 = all(x["n_bad"] == 0 for x in new)
    verdict("(G1) 새 게이트: 방향 반전 격자(배터리 3 × 램프 2 × 방향 2 × 공차 4)의 모든 턴오프 ≤ max(5 %·첨두, 1 A)", g1,
            "%d/%d" % (sum(x["n_bad"] == 0 for x in new), len(new)))
    save_json(EID, "stress", dict(rows=rows, G1=g1))


# ---------------------------------------------------------------- regress: E1 공차 표본, E24 정상·과도
def _e1_samples(g):
    """E1 tolerance_samples()의 영교차 추종 정·역방향(정격 46.875 A, 공차 표본 20개)을 게이트 g로 다시 계산."""
    rs = A.matlab_rng(0); tol = dict(C=0.05, L=0.10, R=0.10); out = []
    for k in range(20):
        state = rs.get_state()                               # E1과 같은 표본 순서(표본마다 같은 난수로 세 번 계산)
        A.draw_tolerance(1, tol, rs)                         # E1의 고정 타이밍 계산이 쓰는 난수(계산은 생략)
        rs.set_state(state)
        b, _ = A.analyze(A.sim_array(N=1, Iload=46.875, mode="zcp", fratio=1.0, tol=tol, rs=rs, ncyc=50, unarmed_stop=g))
        rs.set_state(state)
        c, _ = A.analyze(A.sim_array(N=1, Iload=-46.875, mode="zcp", fratio=1.0, tol=tol, rs=rs, ncyc=50, unarmed_stop=g))
        out.append((b[0]["zcs"], c[0]["zcs"]))
    return out


def _e24_static(I):
    out = {}
    for V in E24.DESIGN_V:
        r = A.sim_array(N=2, Vbat=V, Iload=I, Cbus=E24.CA, mode="zcp", ncyc=int(0.6e-3 / T), shed=E24.SHED, dead_fix=DF,
                        unarmed_stop="nom")
        tl = r["t"][-1] - 10 * T
        to = E24.turnoffs(r, tl)
        zr = max(abs(x[2]) / x[3] for x in to); za = max(abs(x[2]) for x in to)
        out[V] = dict(I=I, V=V, zcs=zr, ioff_max=za, ok=(zr <= 0.05) if abs(I) >= E24.I_LOW else (za <= E24.I_ABS))
    return out


def _e24_case(name):
    c = E24.CASES[name]
    bus = dict(E24.BUS, P=c["bus"]) if "bus" in c else None
    run = lambda sh: A.sim_array(N=2, Vbat=c["V"], Iload=c["prof"], Cbus=E24.CA, mode="zcp", ncyc=int(c["tend"] / T),
                                 shed=E24.SHED if sh else None, bus=bus, dead_fix=DF, unarmed_stop="nom")
    return E24.case_metrics(name, run(True), run(False))


def _job(j):
    kind, arg = j
    if kind == "e1":
        return ("e1", arg, _e1_samples(arg))
    if kind == "st":
        return ("st", arg, _e24_static(arg))
    return ("tr", arg, _e24_case(arg))


def regress():
    S0 = json.loads((outdir("E24") / "static.json").read_text(encoding="utf-8"))["rows"]
    T0 = json.loads((outdir("E24") / "transient.json").read_text(encoding="utf-8"))["cases"]
    jobs = [("e1", "max"), ("e1", "nom")] + [("st", I) for I in E24.STATIC_I] + [("tr", n) for n in E24.CASES]
    with Pool(workers()) as p:
        res = p.map(_job, jobs)
    e1 = {a: v for k, a, v in res if k == "e1"}
    d_e1 = max(max(abs(a[0] - b[0]), abs(a[1] - b[1])) for a, b in zip(e1["max"], e1["nom"]))
    st = [x for k, a, v in res if k == "st" for x in v.values()]
    d_st = []
    for x in st:
        y = next(r for r in S0 if r["V"] == x["V"] and r["I"] == x["I"])
        d_st.append(dict(V=x["V"], I=x["I"], ok=x["ok"], ok0=y["ok"], dz=100 * (x["zcs"] - y["zcs"]), di=x["ioff_max"] - y["ioff_max"]))
    tr = [v for k, a, v in res if k == "tr"]
    d_tr = []
    for x in tr:
        y = next(r for r in T0 if r["case"] == x["case"])
        d_tr.append(dict(case=x["case"], passed=x["passed"], passed0=y["passed"], limits=x["limits"], limits0=y["limits"],
                         dpk=x["phase_peak"] - y["phase_peak"], dvA=max(abs(x["vA"][0] - y["vA"][0]), abs(x["vA"][1] - y["vA"][1])),
                         ioff_max=x["ioff_max"], ioff_max0=y["ioff_max"], n_bad=x["n_bad"], n_bad0=y["n_bad"],
                         ioff_noshed=x["ioff_max_noshed"], ioff_noshed0=y["ioff_max_noshed"]))
    print("  E1 공차 표본(정격 정·역방향 20개): 새 게이트 − 이전 게이트 턴오프/피크 차 최대 %.2e, 최대 비율 %.2f %%"
          % (d_e1, 100 * max(max(a) for a in e1["nom"])))
    print("  E24 정상: 판정 변화 %d, 턴오프 비율 차 최대 %.3f %%p, 턴오프 전류 차 최대 %.3f A"
          % (sum(x["ok"] != x["ok0"] for x in d_st), max(abs(x["dz"]) for x in d_st), max(abs(x["di"]) for x in d_st)))
    for x in d_tr:
        print("  E24 %-28s %s(이전 %s) 위상 첨두 차 %+.2f A, V_A 차 %.3f V, 턴오프 최대 %.2f A(이전 %.2f), 셰딩 없음 %.2f A(이전 %.2f)"
              % (x["case"], "통과" if x["passed"] else "불통과", "통과" if x["passed0"] else "불통과", x["dpk"], x["dvA"],
                 x["ioff_max"], x["ioff_max0"], x["ioff_noshed"], x["ioff_noshed0"]))
    g2 = (d_e1 <= 1e-6 and all(x["ok"] == x["ok0"] and abs(x["dz"]) <= 0.1 for x in d_st)
          and all(x["limits"] == x["limits0"] and abs(x["dpk"]) <= 0.5 and x["dvA"] <= 0.05 for x in d_tr))
    verdict("(G2) 회귀: E1 공차 표본 같음, E24 정상·과도 판정과 지표 같음", g2)
    save_json(EID, "regress", dict(e1_diff=d_e1, e1=e1, static=d_st, transient=d_tr, G2=g2))


# ---------------------------------------------------------------- figures
def _wave(g):
    t1 = 0.3e-3
    prof = ([0, t1, t1 + 100e-6, 0.8e-3, 0.9e-3, 1], [0, 0, -375., -375., 0, 0])
    return A.sim_array(N=8, Vbat=800., Iload=prof, Cbus=400e-6, mode="zcp", ncyc=int(0.45e-3 / T),
                       bus=dict(BUS, RA=10.2e-3 / 4, P=([0, 1], [15e3, 15e3])), dead_fix=DF, unarmed_stop=g)


def figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    R = json.loads((outdir(EID) / "repro.json").read_text(encoding="utf-8"))["rows"]
    S = json.loads((outdir(EID) / "stress.json").read_text(encoding="utf-8"))["rows"]
    with Pool(2) as p:
        wo, wn = p.map(_wave, ("max", "nom"))
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
    # (a) 무장하지 못한 반주기 하나: 이전·새 게이트
    to = turnoffs_arm(wo, 0.25e-3)
    un = [x for x in to if x[4] == 0]
    k, tk = (un[0][0], un[0][1]) if un else (0, 0.31e-3)
    for r, lab, col in ((wo, "이전: 최대 도통시간(1.12·t_on)에서 끔", C.get("red", "C3")), (wn, "새: 공칭 도통시간 t_on에서 끔", C.get("blue", "C0"))):
        m = (r["t"] > tk - 12e-6) & (r["t"] < tk + 8e-6)
        ax[0].plot(r["t"][m] * 1e6, r["i"][m, k], lw=1.1, label=lab, color=col)
    ax[0].axhline(2.5, ls=":", color="gray", lw=.8); ax[0].axhline(-2.5, ls=":", color="gray", lw=.8)
    ax[0].axhline(1.0, ls="--", color="k", lw=.6); ax[0].axhline(-1.0, ls="--", color="k", lw=.6)
    ax[0].set_ylim(-8, 8); ax[0].set_xlabel("시간 [µs]"); ax[0].set_ylabel("위상 %d 공진전류 [A]" % (k + 1))
    ax[0].set_title("(a) 방향 반전 근처(점선: 무장 문턱 ±2.5 A, 파선: ±1 A)"); ax[0].legend(fontsize=7.5); ax[0].grid(alpha=.3)
    # (b) 반주기 첨두 대 턴오프 전류(무장 못 한 반주기), 사례 D 조건 전부
    for g, col, lab in (("max", C.get("red", "C3"), "이전 게이트"), ("nom", C.get("blue", "C0"), "새 게이트")):
        xs = [x["unarmed_pk_max"] for x in R if x["gate"] == g]; ys = [x["ioff_unarmed_max"] for x in R if x["gate"] == g]
        ax[1].scatter(xs, ys, s=22, color=col, label=lab)
    ax[1].axhline(1.0, ls="--", color="k", lw=.7)
    ax[1].set_xlabel("무장 못 한 반주기의 첨두 최대 [A]"); ax[1].set_ylabel("그 턴오프 전류 최대 [A]")
    ax[1].set_title("(b) TB20 사례 D 조건(램프 시작 6가지 + 공차)"); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
    # (c) 방향 반전 격자: 사례별 턴오프 전류 최대
    idx = np.arange(len([x for x in S if x["gate"] == "max"]))
    for g, col, lab in (("max", C.get("red", "C3"), "이전 게이트"), ("nom", C.get("blue", "C0"), "새 게이트")):
        ax[2].plot(idx, [x["ioff_max"] for x in S if x["gate"] == g], "o", ms=3.5, color=col, label=lab)
    ax[2].axhline(1.0, ls="--", color="k", lw=.7)
    ax[2].set_xlabel("사례(배터리 3 × 램프 2 × 방향 2 × 공차 4)"); ax[2].set_ylabel("턴오프 전류 최대 [A]")
    ax[2].set_title("(c) 모듈 하나의 방향 반전 격자"); ax[2].legend(fontsize=8); ax[2].grid(alpha=.3)
    fig.tight_layout(); fig.savefig(outdir(EID) / "E27_zcp_reversal.png", dpi=150); plt.close(fig)
    print("  → 저장: results/E27/E27_zcp_reversal.png")


if __name__ == "__main__":
    parts = sys.argv[1:] or ["repro", "stress", "regress", "figures"]
    for name in parts:
        print("[E27] " + name)
        globals()[name]()
