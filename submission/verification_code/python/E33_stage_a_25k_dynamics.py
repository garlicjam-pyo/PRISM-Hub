"""[E33] Stage A 25 kHz 설계(A25)의 동특성 재확인: 모듈 관리기 정상점·과도(E28)와 모듈 고장(E30)을 A25로 다시 판정.

■ 목적
  E32에서 A25 설계(위치당 C4MS008075U2 2병렬, f_r 25 kHz)의 셰딩·모듈 관리기 문턱과 시간 상수(150 kHz 값의 6배)를 정했다.
  E28·E30의 판정(부하 계단·램프, 충전 시작·종료, 모듈 고장)은 150 kHz 설계에서 했다. 공진이 6배 느려지면 새 모듈이
  분담을 받는 데 걸리는 시간, 시작 과도, V_A 노드의 응답이 바뀐다. 같은 판정 기준으로 다시 확인하고, 충전 전 사전 기동
  시간과 충전전류 램프 요구를 이 설계로 다시 정한다.

■ 모델  model_stage_a.set_design('A25')(E32와 같음), 관리기 = E32 thresholds의 MGR, 첨두 기준 P_rated = E32 rated(표본별).
  E28·E30 코드를 그대로 쓰고 설계·문턱·사례 시각만 바꾼다. 공차 표본은 공칭 + 표본 1(계산 시간 때문에 E28·E30의 3개에서 줄임).

■ 사례(실행 전에 고정)
  시각 이동: A25의 시작 유지 t_hold가 600 µs라, E28·E30 사례의 모든 사건 시각·판정 시작·끝 시각을 0.6 ms 늦춘다
  (사건이 시작 유지 안에 들지 않게). 이것 말고는 E28·E30과 같은 사례다.
  static  : E28 정상 운전점(주행 540·800·1008 V × 3–220 A, 충전 640·800·920 V × −30–−375 A) × 공칭·표본 1, 계산 2.0 ms,
            판정 창은 마지막 10주기(E28과 같음)
  transient: E28 MA·MB·MC·MD·ME·MF·MG(+0.6 ms) × 공칭·표본 1, 관리기 켬과 전부 켬(8위상, 셰딩 없음)
  slow    : 충전 사례 MC·MD·ME를 사전 기동 600 µs·충전전류 램프 600 µs(E28의 6배)로. 요구 갱신 규칙: 원 시각 사례(100 µs·100 µs)가
            불통과면 slow 사례 결과로 충전 전 사전 기동 시간·충전전류 램프 요구를 바꾼다(둘 다 불통과면 불통과로 보고)
  fault   : E30 FA–FH(고장 0.5 → 1.1 ms, 판정 시작 0.3 → 0.9 ms, 끝 1.5 → 2.1 ms) × 공칭·표본 1

■ 판정 기준(E28·E30과 같음, 시험 전에 고정)
  static  S1 |I_m| ≥ 7.5 A 비율 ≤ 5 %, S2 < 7.5 A 턴오프 ≤ 1.0 A, S3 모듈·위상 수 = 규칙, S4 위상 첨두 ≤ P_rated(표본)
          (S3·S4의 시작 제외 구간: E28은 0.1 ms(150 kHz 15주기)부터 보았다. A25는 시작 유지 t_hold(600 µs = 15주기) + 5주기
           뒤부터 본다. S3은 그 뒤 모듈 수가 바뀌지 않음, S4는 그 뒤 첨두)
  transient(판정 시작 0.9 ms = E28 0.3 ms + 이동 0.6 ms)
            T1 모든 턴오프 ≤ max(5 % × 반주기 첨두, 1.0 A), T2 위상 첨두 ≤ P_rated(표본), T3 V_A 최저·최고가 전부 켬과 1.0 V 안,
            T4 끝 모듈 수·추가·줄임 횟수·취소 0
  fault   F1–F4(E30)

■ 실행 결과(2026-10-28, 기준은 바꾸지 않았다)
  static   : 공칭 33/36, 표본 1 31/36. 불통과는 정격 충전점 S4(시작 유지 뒤 첨두 79.5–80.3 A > P_rated 74.5 A, 마지막 10주기
             첨두 75.0 A; 표본 1은 103.5·103.9 A > 102.8 A)와 표본 1의 130 A 주행 S3(모듈 3개, 규칙 2개: 시작 과도에서 순시 66 A를
             넘어 추가된 뒤 줄임 조건 ⌈130/60⌉ = 3에 걸려 남음).
  transient: 공칭 1/7, 표본 1 1/7(MB만 통과). 충전 사례 MC·MD·ME는 전부 켬(관리기 없음)도 턴오프 위반 21–43번 — 충전전류 램프
             100 µs가 25 kHz 공진 2.5주기다. MA(540 V 5 → 25 kW 계단)는 두 번째 모듈이 계단 뒤 84 µs(약 2주기)에 들어오는 동안
             위상 첨두 76.6 A > 74.5 A. MG는 V_A가 전부 켬보다 1.3 V 낮음(T3).
  slow     : 0/3·0/3. 턴오프 위반 2–15번(최대 1.7–4.4 A, 전부 켬은 0) — 충전 요구 갱신 규칙: 두 시각 모두 불통과.
  fault    : 주행·충전 × 공칭·표본 1 16/16 통과. 3모듈 충전 위상 첨두 최대 119.6 A(부품 정격 표 입력).
  실행 뒤 진단(E33_diag_transient.py, 판정 바꾸지 않음): MC_slow는 C_A 6배 또는 관리기 시간 상수 150 kHz 값이면 통과.
             MA는 둘 다 첨두 86–87 A로 불통과(단일 모듈이 25 kW를 받는 동안의 첨두).

■ 실행   python E33_stage_a_25k_dynamics.py static transient slow fault figures   (2코어 약 2시간)
■ 결과   results/E33/static.json, transient.json, slow.json, fault.json, E33_stage_a_25k_dynamics.png
"""
import json
import sys
from multiprocessing import Pool

import numpy as np

import model_stage_a as A
import E24_stage_a_shedding as E24
import E28_stage_a_modules as E28
import E30_module_fault as E30
from common import load_json, outdir, save_json, verdict, workers

EID = "E33"
DESIGN = "A25"
SHIFT = 0.6e-3
SEEDS = (None, 1)
T_STATIC = 2.0e-3


def configure():
    """A25 설계·E32 문턱·사건 시각 이동을 E28·E30 모듈 전역에 적용한다(작업 프로세스마다 호출)."""
    A.set_design(DESIGN)
    th = load_json("E32", "thresholds")
    M = dict(th["MGR"])
    E28.MGR = M; E28.T = 1 / A.FR0; E28.EID = "E32"          # p_rated는 E32 rated.json에서 읽는다
    E28.T_JUDGE = 0.3e-3 + SHIFT
    E30.T = 1 / A.FR0; E30.T_F = E30.T_F + SHIFT if E30.T_F < SHIFT else E30.T_F; E30.T0 = 0.3e-3 + SHIFT
    for c in E30.CASES.values():
        c["tend"] = 1.5e-3 + SHIFT
    E28.CASES = shifted_cases()
    return M


def _sh(tt):
    return [0] + [t + SHIFT for t in tt[1:-1]] + [1] if len(tt) > 2 else tt


def shifted_cases():
    base = {k: dict(v) for k, v in E28_CASES0.items()}
    out = {}
    for k, c in base.items():
        cc = dict(c)
        if not np.isscalar(c["prof"]):
            cc["prof"] = (_sh(c["prof"][0]), list(c["prof"][1]))
        cc["bus"] = (_sh(c["bus"][0]), list(c["bus"][1]))
        if "chg" in c:
            cc["chg"] = (c["chg"][0] + SHIFT, c["chg"][1] + SHIFT)
        cc["tend"] = c["tend"] + SHIFT
        out[k] = cc
    return out


E28_CASES0 = {k: dict(v) for k, v in E28.CASES.items()}       # import 시점(150 kHz 사례 정의)


def slow_cases():
    """충전 사례를 사전 기동 600 µs·램프 600 µs로(시각은 이미 0.6 ms 이동). 요청 1.0 ms, 램프 1.6–2.2 ms, 유지 3.0 ms,
    내림 3.0–3.6 ms, 요청 끝 3.65 ms, 끝 5.0 ms."""
    prof = ([0, 1.6e-3, 2.2e-3, 3.0e-3, 3.6e-3, 1], [0, 0, -375., -375., 0, 0])
    out = {}
    for k in ("MC_800V_charge_prestart", "MD_640V_charge_prestart", "ME_920V_charge_prestart"):
        c = dict(E28_CASES0[k])
        out[k.replace("prestart", "slow")] = dict(V=c["V"], prof=prof, bus=([0, 1], [15e3, 15e3]), chg=(1.0e-3, 3.65e-3), tend=5.0e-3,
                                                  n_end=1, add_max=1, rem_max=1)
    return out


def _init():
    configure()


# ---------------------------------------------------------------- static
def _static(args):
    V, I, chg, seed = args
    configure()
    T = E28.T
    tol, rs = E28._tol(seed)
    MGR = E28.MGR
    r = A.sim_array(N=8, Vbat=V, Iload=I, Cbus=E28.CA, mode="zcp", ncyc=int(T_STATIC / T), tol=tol, rs=rs, dead_fix=True,
                    unarmed_stop=E28.GATE, mgr=MGR, chg=(0., 1.) if chg else None)
    tl = r["t"][-1] - 10 * T
    w = r["t"] > tl
    n_exp, nph_exp = E28.expect_static(I, chg)
    to = E24.turnoffs(r, tl)
    mods, ok = [], True
    for m in range(4):
        act = [k for k in (2 * m, 2 * m + 1) if np.any(r["st"][w, k] != 0)]
        if not act:
            continue
        Im = float(r["io"][w][:, 2 * m:2 * m + 2].sum(axis=1).mean())
        tm = [x for x in to if x[0] in act]
        zr = max(abs(x[2]) / x[3] for x in tm); za = max(abs(x[2]) for x in tm)
        okm = (zr <= 0.05) if abs(Im) >= E28.I_LOW else (za <= E28.I_ABS)
        mods.append(dict(m=m, phases=len(act), I=Im, zcs=zr, ioff_max=za, ok=okm))
        ok &= okm
    na = r["nact"]
    hold_end = MGR["t_hold"] + 5 * T                              # 시작 유지 끝 뒤부터 모듈 수가 바뀌지 않아야 함
    steady = r["t"] > hold_end
    s3 = (int(na[-1]) == n_exp and np.all(na[steady] == na[-1]) and len(mods) == n_exp and all(x["phases"] == nph_exp for x in mods))
    pk = float(np.abs(r["i"][r["t"] > hold_end]).max())
    Im = [x["I"] for x in mods]
    share = max(np.abs(Im)) / np.mean(np.abs(Im)) if len(Im) > 1 else 1.0
    pk_st = float(np.abs(r["i"][w]).max())
    ph, bus = A.analyze(r, ncyc_last=10)
    L = dict(S12=bool(ok), S3=bool(s3), S4=pk <= E28.p_rated(seed))
    return dict(V=V, I=I, chg=chg, seed=seed, n_exp=n_exp, nph_exp=nph_exp, nact=int(na[-1]), mods=mods, phase_peak=pk, pk_steady=pk_st,
                share=share, loss=float(sum(p["Ploss"] for p in ph if p["Ipk"] > 0.5)), limits=L, passed=all(L.values()))


def static():
    configure()
    jobs = [(V, I, False, s) for V in E28.ST_DRIVE_V for I in E28.ST_DRIVE_I for s in SEEDS] + \
           [(V, I, True, s) for V in E28.ST_CHG_V for I in E28.ST_CHG_I for s in SEEDS]
    with Pool(workers(), initializer=_init) as p:
        rows = p.map(_static, jobs)
    for x in rows:
        if x["seed"] is None or not x["passed"]:
            print("  %4.0f V %7.1f A %s 공차 %s: 모듈 %d(기대 %d), 위상/모듈 %s, 비율 최대 %.2f %%, 턴오프 최대 %.2f A, 첨두 %.1f A, 손실 %.0f W, %s"
                  % (x["V"], x["I"], "충전" if x["chg"] else "주행", x["seed"], x["nact"], x["n_exp"], [m["phases"] for m in x["mods"]],
                     100 * max(m["zcs"] for m in x["mods"]), max(m["ioff_max"] for m in x["mods"]), x["phase_peak"], x["loss"],
                     "통과" if x["passed"] else "불통과 " + str([k for k, v in x["limits"].items() if not v])))
    for s in SEEDS:
        rr = [x for x in rows if x["seed"] == s]
        verdict("(static) 공차 %s: S1–S4" % s, all(x["passed"] for x in rr), "%d/%d" % (sum(x["passed"] for x in rr), len(rr)))
    save_json(EID, "static", dict(rows=rows, mgr=E28.MGR, t_sim=T_STATIC))


# ---------------------------------------------------------------- transient·slow
def _transient(args):
    name, seed, slow = args
    configure()
    if slow:
        E28.CASES = dict(E28.CASES, **slow_cases())
    m = E28.case_metrics(name, E28.run_case(name, seed), E28.run_case(name, seed, ref=True), seed)
    m["seed"] = seed
    return m


def _report(res, label):
    for x in res:
        print("  %-30s 공차 %-4s %s  모듈 %s, 턴오프 %d(위반 %d) 최대 %.2f A, 첨두 %.1f A(전부 켬 %.1f, P_rated %.1f), V_A %.2f–%.2f(전부 켬 %.2f–%.2f)"
              % (x["case"], x["seed"], "통과" if x["passed"] else "불통과 " + str([k for k, v in x["limits"].items() if not v]),
                 x["events"], x["n_turnoff"], x["n_bad"], x["ioff_max"], x["phase_peak"], x["phase_peak_ref"], x["P_rated"],
                 x["vA"][0], x["vA"][1], x["vA_ref"][0], x["vA_ref"][1]))
    for s in SEEDS:
        rr = [x for x in res if x["seed"] == s]
        verdict("(%s) 공차 %s: T1–T4" % (label, s), all(x["passed"] for x in rr), "%d/%d" % (sum(x["passed"] for x in rr), len(rr)))


def transient():
    configure()
    jobs = [(n, s, False) for n in E28.CASES for s in SEEDS]
    with Pool(workers(), initializer=_init) as p:
        res = p.map(_transient, jobs)
    _report(res, "transient")
    save_json(EID, "transient", dict(cases=res, mgr=E28.MGR, shift=SHIFT))


def slow():
    configure()
    jobs = [(n, s, True) for n in slow_cases() for s in SEEDS]
    with Pool(workers(), initializer=_init) as p:
        res = p.map(_transient, jobs)
    _report(res, "slow")
    tr = {(x["case"], x["seed"]): x for x in load_json(EID, "transient")["cases"]}
    orig_ok = all(tr[(k, s)]["passed"] for k in ("MC_800V_charge_prestart", "MD_640V_charge_prestart", "ME_920V_charge_prestart")
                  for s in SEEDS)
    slow_ok = all(x["passed"] for x in res)
    req = ("100 µs 사전 기동·100 µs 램프(E28과 같음)" if orig_ok else
           ("600 µs 사전 기동·600 µs 램프(요구 변경)" if slow_ok else "두 시각 모두 불통과"))
    print("  충전 요구 갱신: %s" % req)
    save_json(EID, "slow", dict(cases=res, orig_ok=orig_ok, slow_ok=slow_ok, requirement=req))


# ---------------------------------------------------------------- fault
def _fault(args):
    name, seed = args
    configure()
    r, n0 = E30.run(name, seed)
    return E30.metrics(name, r, n0, seed)


def fault():
    configure()
    jobs = [(n, s) for n in E30.CASES for s in SEEDS]
    with Pool(workers(), initializer=_init) as p:
        res = p.map(_fault, jobs)
    for x in res:
        print("  %-24s 공차 %-4s %s 모듈 %s, 대체 %s µs, 턴오프 %d(위반 %d) 최대 %.2f A, 첨두 %.1f A(한도 %.1f), V_A %.2f → %.2f–%.2f V, 정상 첨두 %.1f A·손실 %.0f W"
              % (x["case"], x["seed"], "통과" if x["passed"] else "불통과 " + str([k for k, v in x["limits"].items() if not v]),
                 x["events"], "—" if x["t_rep_us"] is None else "%.1f" % x["t_rep_us"], x["n_turnoff"], x["n_bad"], x["ioff_max"],
                 x["phase_peak"], x["pk_limit"], x["vA_pre"], x["vA"][0], x["vA"][1], x["steady"]["pk"], x["steady"]["loss_W"]))
    for kind in ("drive", "charge"):
        for s in SEEDS:
            rr = [x for x in res if x["kind"] == kind and x["seed"] == s]
            verdict("(fault) %s 공차 %s: F1–F4" % (kind, s), all(x["passed"] for x in rr), "%d/%d" % (sum(x["passed"] for x in rr), len(rr)))
    chg = [x for x in res if x["kind"] == "charge"]
    req = dict(pk_max=max(x["phase_peak"] for x in chg), pk_steady_max=max(x["steady"]["pk"] for x in chg),
               share_max=max(x["steady"]["share"] for x in chg), loss_mod_max=max(x["steady"]["loss_W"] / 3 for x in chg))
    print("  3모듈 충전(부품 정격 표 입력, A25): 위상 첨두 최대 %.1f A(정상 %.1f A), 분담 최대 %.3f, 모듈 손실 최대 %.0f W"
          % (req["pk_max"], req["pk_steady_max"], req["share_max"], req["loss_mod_max"]))
    save_json(EID, "fault", dict(cases=res, mgr=E28.MGR, t_f=E30.T_F, parts_input=req))


def figures():
    import matplotlib
    matplotlib.use("Agg")
    from plotstyle import korean, COLOR
    plt = korean()
    configure()
    fig, ax = plt.subplots(2, 2, figsize=(14, 7.5))
    for a, (name, slow_) in zip(ax[0], (("MC_800V_charge_prestart", False), ("MA_540V_bus_5_25_5kW", False))):
        r = E28.run_case(name)
        t = r["t"] * 1e3
        a.plot(t, r["i"][:, 0], lw=0.4, color=COLOR["blue"], label="위상 1")
        a.plot(t, r["i"][:, 2], lw=0.4, color=COLOR["orange"], label="위상 3")
        a2 = a.twinx(); a2.step(t, r["nact"], color=COLOR["red"], where="post"); a2.set_ylim(0, 4.5); a2.set_ylabel("동작 모듈 수")
        a.set_xlabel("시간 [ms]"); a.set_ylabel("위상 전류 [A]"); a.set_title("A25 %s" % name); a.legend(loc="upper left", fontsize=7)
    configure()
    r, n0 = E30.run("FF_800V_charge_m1")
    t = r["t"] * 1e3
    b = ax[1][0]
    b.plot(t, r["vb"], color=COLOR["blue"], lw=0.8); b.set_xlabel("시간 [ms]"); b.set_ylabel("V_A [V]")
    b2 = b.twinx(); b2.step(t, r["nact"], color=COLOR["red"], where="post"); b2.set_ylim(0, 4.5)
    b.set_title("A25 FF 800 V 충전 중 모듈 1 고장")
    c = ax[1][1]
    try:
        S = load_json(EID, "static")["rows"]
        dr = [x for x in S if not x["chg"] and x["seed"] is None]
        for V, col in zip(E28.ST_DRIVE_V, (COLOR["blue"], COLOR["green"], COLOR["red"])):
            rr = sorted([x for x in dr if x["V"] == V], key=lambda x: x["I"])
            c.plot([x["I"] for x in rr], [x["loss"] for x in rr], "-o", color=col, ms=3, label=f"{V:.0f} V")
        c.set_xlabel("V_A 노드 부하 [A]"); c.set_ylabel("Stage A 손실 [W]"); c.set_title("A25 관리기·셰딩 정상점 손실"); c.legend()
    except Exception:
        pass
    fig.tight_layout()
    p = outdir(EID) / "E33_stage_a_25k_dynamics.png"
    fig.savefig(p, dpi=130); print("  → 저장:", p)


if __name__ == "__main__":
    parts = sys.argv[1:] or ["static", "transient", "slow", "fault", "figures"]
    for part in parts:
        print(f"E33 {part} ...")
        globals()[part]()
