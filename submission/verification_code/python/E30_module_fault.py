"""[E30] Stage A 모듈 고장과 모듈 관리기의 연동(고장 모듈 제외) + 고장 운전의 위상 응력(부품 정격 표 입력).

■ 목적
  E26(docs/31)은 충전 중 모듈 1개 고장(P-b)을 "남은 모듈 하나가 375/3 A를 받는 정상상태"로만 계산했다(관리기 없음, 공칭).
  E28(docs/34)의 모듈 관리기는 동작 모듈을 모듈 번호 순으로 고르며, 고장 난 모듈을 후보에서 빼는 처리가 없었다
  (docs/34 남은 과제 2, docs/35 남은 과제 5: "부품 정격 표 단계에서 함께 다룬다").
  이 시험은
  (1) 모듈 고장 신호가 오면 그 모듈의 위상을 바로 멈추고 관리기 후보에서 영구히 빼는 처리(model_stage_a.mgr_fault)를 넣고,
  (2) 주행(모듈 1–2개 동작)과 충전(4개 → 3개) 중 고장에서 남은 모듈의 턴오프·위상 첨두·V_A·모듈 수를 판정하며(fault),
  (3) 공차 표본별 3모듈 충전의 위상 첨두·모듈 손실을 부품 정격 표(검증 과제 5) 입력으로 남기고,
  (4) 고장이 없는 경로가 E28과 같은지 확인한다(regress). 회로 확인은 TB24다.

■ 왜 필요한가
  - 주행 중 동작 모듈이 하나뿐인데 그 모듈이 고장 나면 V_A 노드(C_A 400 µF)는 부하전류로 곧 내려간다. 관리기는 동작 수를
    모듈 번호로 세므로, 고장 모듈을 빼지 않으면 같은(고장 난) 모듈을 계속 "동작"으로 센다.
  - 충전 중 고장이면 차량이 충전 전류를 3/4로 다시 요청할 때까지(통신·충전기 응답, 수십 ms 이상) 남은 3개 모듈이 375 A를
    받는다(E26 P-b). 이 동안의 위상 첨두가 Stage A 위상 소자·인덕터·플라잉 커패시터의 정격 조건이 된다.
  - 공차 표본에서는 정격점 첨두 자체가 공칭보다 10–12 % 크다(E28 rated). 3모듈 과부하에서도 같은지 봐야 한다.

■ 고장 처리(시험 전에 정함, 회로 게이트 ctrl/prism_gate_stageA_zcpf.m과 같은 순서)
  고장 신호(간격 번호 round(t_f/dt)) → 그 모듈 위상의 구간을 바로 0(네 스위치 끔, 남은 공진전류는 바디 다이오드로 소멸)
  → 관리기 건전 모듈 목록에서 뺌(다시 켜지 않음) → 동작 중이었으면 동작 수 −1 → 동작 모듈이 0이면 다음 건전 모듈을 바로
  두 위상으로 시작(추가 막는 시간 t_lock 시작) → 더 필요한 모듈은 E28의 추가 규칙(충전 요청이면 건전 모듈 전부, 아니면
  |If| > 동작 수 × 70 A 또는 위상 순시 > 66 A)이 정한다. 동작 모듈은 건전 모듈 가운데 번호가 작은 것부터다.
  고장의 원인(소자 단락·구동 고장 등)과 검출 지연은 넣지 않았다: 검출 순간 게이트를 끄는 것으로 둔다.
  멈춰 있던 모듈의 플라잉 커패시터는 docs/34의 균형 회로 목표값 V_bat/2 − 5 V에서 시작한다.

■ 사례(시험 전에 고정)  고장 시각 0.5 ms, 끝 1.5 ms(충전) · 1.5 ms(주행). 공칭 + 공차 표본 3개(E28과 같은 시드).
  주행(V_A 노드 뒤 R2 버스 정전력 부하, 충전기 없음)
    FA 800 V·15 kW(모듈 1개 동작), 모듈 1 고장 → 모듈 2가 대신
    FB 540 V·25 kW(모듈 2개 동작), 모듈 1 고장 → 모듈 2 혼자 약 93 A → 모듈 3 추가
    FC 1008 V·25 kW(모듈 1개), 모듈 1 고장 → 모듈 2
    FD 800 V·15 kW(모듈 1개), 멈춰 있던 모듈 3 고장 → 운전 변화 없음
  충전(V_A 노드에 −375 A, 버스 15 kW, 충전 요청 계속 → 4개 동작)
    FE 640 V, FF 800 V, FG 920 V: 모듈 1 고장 → 3개가 375 A
    FH 800 V: 모듈 4 고장(인터리빙 위치가 다른 경우)

■ 판정 기준(시험 전에 고정)
  (F1) 턴오프: 0.3 ms 이후 모든 턴오프(고장 모듈의 고장 순간 이후는 뺌) |i_off| ≤ max(5 % × 그 반주기 첨두, 1.0 A)(E28 T1)
  (F2) 위상 첨두(0.3 ms 이후, 고장 모듈은 고장 전까지만): 주행 ≤ P_rated(표본)(E28 T2),
       충전 ≤ 1.5 × P_rated(표본)(E26 C2를 표본별로)
  (F3) V_A: 고장 뒤 V_A가 고장 직전 20 µs 평균과 ±10 V 안, 배터리 ≤ 920 V면 ≤ 470 V(B_470)
  (F4) 모듈 수: 끝 동작 수 = 기대값(주행 max(1, ⌈|I|/70 A⌉), 충전 3), 고장 모듈 위상이 고장 뒤 다시 켜지지 않음,
       고장 뒤 동작 수 감소는 고장 자체 한 번뿐, 멈추기 취소 0
  (정보) 대체 모듈 첫 반주기까지 시간, V_A 최저·최고, 고장 모듈의 고장 순간 전류, 3모듈 충전 정상(마지막 10주기)의
         위상 첨두·평균전류 불균형·모듈 손실 → 부품 정격 표
  regress (G1) 고장 없음: E28 transient MA·MC(공칭)의 지표가 저장된 결과와 같다(관리기 일반화가 이전 경로를 바꾸지 않음)

■ 실행   python E30_module_fault.py fault regress figures   (2코어 약 25분)
■ 결과   results/E30/fault.json, regress.json, E30_module_fault.png
"""
import json
import sys
from multiprocessing import Pool

import numpy as np

import model_stage_a as A
import E24_stage_a_shedding as E24
import E28_stage_a_modules as E28
from common import save_json, verdict, outdir, workers

EID = "E30"
T = 1 / A.FR0
T_F = 0.5e-3
T0 = 0.3e-3
DV_A = 10.
V_B470 = 470.
PK_CHG = 1.5                                  # 충전 고장의 첨두 한도 배율(E26 C2)
DV_IDLE = -5.                                 # 멈춘 모듈의 플라잉 커패시터 = V_bat/2 − 5 V(docs/34 균형 회로 목표)

CASES = {
    "FA_800V_drive_15kW_m1": dict(V=800., kind="drive", P=15e3, fm=0, tend=1.5e-3),
    "FB_540V_drive_25kW_m1": dict(V=540., kind="drive", P=25e3, fm=0, tend=1.5e-3),
    "FC_1008V_drive_25kW_m1": dict(V=1008., kind="drive", P=25e3, fm=0, tend=1.5e-3),
    "FD_800V_drive_15kW_m3": dict(V=800., kind="drive", P=15e3, fm=2, tend=1.5e-3),
    "FE_640V_charge_m1": dict(V=640., kind="charge", P=15e3, fm=0, tend=1.5e-3),
    "FF_800V_charge_m1": dict(V=800., kind="charge", P=15e3, fm=0, tend=1.5e-3),
    "FG_920V_charge_m1": dict(V=920., kind="charge", P=15e3, fm=0, tend=1.5e-3),
    "FH_800V_charge_m4": dict(V=800., kind="charge", P=15e3, fm=3, tend=1.5e-3),
}
I_CH = 375.


def n_start(c):
    if c["kind"] == "charge":
        return 4
    return max(1, int(np.ceil(c["P"] / (c["V"] / 2) / E28.MGR["Im_up"])))


def setup(name):
    """sim_array 인자(고장 사례). TB24 기준값 생성도 이 함수를 쓴다."""
    c = CASES[name]
    n0 = n_start(c)
    vc0 = np.full(8, c["V"] / 2)
    for m in range(n0, 4):                                   # 멈춘 모듈의 플라잉 커패시터
        vc0[2 * m] = vc0[2 * m + 1] = c["V"] / 2 + DV_IDLE
    prof = (([0, 1], [-I_CH, -I_CH]) if c["kind"] == "charge" else 0.)
    bus = dict(E28.BUS, RA=E28.RA1 / n0, P=([0, 1], [c["P"], c["P"]]))
    chg = (0., 1.) if c["kind"] == "charge" else None
    return dict(N=8, Vbat=c["V"], Iload=prof, Cbus=E28.CA, mode="zcp", ncyc=int(c["tend"] / T), vC0=vc0, bus=bus,
                dead_fix=E28.DF, unarmed_stop=E28.GATE, mgr=dict(E28.MGR, n0=n0), chg=chg, fault=[(T_F, c["fm"])]), n0


def run(name, seed=None):
    kw, n0 = setup(name)
    tol, rs = E28._tol(seed)
    return A.sim_array(tol=tol, rs=rs, **kw), n0


def expected_end(c):
    if c["kind"] == "charge":
        return 3
    return max(1, int(np.ceil(c["P"] / (c["V"] / 2) / E28.MGR["Im_up"])))


def metrics(name, r, n0, seed=None):
    """판정(F1–F4)과 정보 지표. TB24 기준값도 이 함수로 만든다."""
    c = CASES[name]; fm = c["fm"]; fph = (2 * fm, 2 * fm + 1)
    t = r["t"]; dt = r["dt"]; kf = int(A.mround(T_F / dt))
    pr = E28.p_rated(seed)
    lim_pk = pr if c["kind"] == "drive" else PK_CHG * pr
    to = E24.turnoffs(r, T0)
    # 고장 모듈의 강제 턴오프는 마지막 도통 표본(간격 kf − 1)에 기록된다 → 그 표본부터 뺀다
    to_ok = [x for x in to if not (x[0] in fph and x[1] >= t[kf] - 1.5 * dt)]
    bad = [x for x in to_ok if abs(x[2]) > max(0.05 * x[3], E28.I_ABS)]
    w = t > T0
    I = np.abs(r["i"]).astype(float)
    pk_h = 0.
    for k in range(8):
        msk = w & (t < t[kf]) if k in fph else w
        if msk.any():
            pk_h = max(pk_h, float(I[msk, k].max()))
    pre = (t >= T_F - 20e-6) & (t < T_F)
    vpre = float(r["vb"][pre].mean())
    post = t >= T_F
    vmin, vmax = float(r["vb"][post].min()), float(r["vb"][post].max())
    na = r["nact"].astype(int)
    ch = np.where(np.diff(na) != 0)[0]
    ev = [(round(float(t[k + 1]) * 1e3, 4), int(na[k + 1])) for k in ch]
    dec_after = [k for k in ch if na[k + 1] < na[k] and k + 1 != kf]
    restart = bool(np.any(r["st"][kf + 1:, list(fph)] != 0))
    F = dict(F1=len(bad) == 0, F2=pk_h <= lim_pk,
             F3=(abs(vmin - vpre) <= DV_A and abs(vmax - vpre) <= DV_A and (c["V"] > 920. or vmax <= V_B470)),
             F4=(int(na[-1]) == expected_end(c) and not restart and len(dec_after) == 0 and r["n_mcancel"] == 0))
    # 대체 모듈: 고장 뒤 처음 켜진 위상(고장 전 꺼져 있던 위상)의 첫 반주기 시작까지
    t_rep = None
    off_before = [k for k in range(8) if k not in fph and not np.any(r["st"][kf - int(T / dt):kf, k] != 0)]
    for k in off_before:
        on = np.where(r["st"][kf:, k] != 0)[0]
        if len(on):
            tk = float(on[0] * dt)
            t_rep = tk if t_rep is None else min(t_rep, tk)
    # 마지막 10주기 정상: 위상 첨두·평균·모듈 손실(분석은 건전 위상만)
    ph, bus = A.analyze(r, ncyc_last=10)
    hp = [p for k, p in enumerate(ph) if k not in fph]
    run_ph = [(k, p) for k, p in enumerate(ph) if k not in fph and p["Ipk"] > 1.]
    iav = np.abs(np.array([p["Iavg"] for _, p in run_ph])) if run_ph else np.array([0.])
    worst = max(to_ok, key=lambda x: abs(x[2]) - max(0.05 * x[3], E28.I_ABS)) if to_ok else (None, 0., 0., 0.)
    return dict(case=name, V=c["V"], kind=c["kind"], seed=seed, limits=F, passed=all(F.values()), P_rated=pr, pk_limit=lim_pk,
                phase_peak=pk_h, n_turnoff=len(to_ok), n_bad=len(bad), ioff_max=max((abs(x[2]) for x in to_ok), default=0.),
                worst=dict(phase=worst[0], t_ms=worst[1] * 1e3, i_off=worst[2], pk=worst[3]),
                i_fault=[float(r["i"][kf - 1, k]) for k in fph], vA_pre=vpre, vA=[vmin, vmax], events=ev, n0=n0, n_end=int(na[-1]),
                restart=restart, n_mcancel=int(r["n_mcancel"]), t_rep_us=None if t_rep is None else t_rep * 1e6,
                steady=dict(pk=max((p["Ipk"] for p in hp), default=0.), Iavg=[float(p["Iavg"]) for p in hp],
                            share=float(iav.max() / iav.mean()) if iav.mean() > 0 else None,
                            loss_W=float(sum(p["Ploss"] for p in hp)), zcs=max((p["zcs"] for _, p in run_ph), default=0.)))


def _fault(args):
    name, seed = args
    r, n0 = run(name, seed)
    return metrics(name, r, n0, seed)


def fault():
    jobs = [(n, s) for n in CASES for s in E28.SEEDS]
    with Pool(workers()) as p:
        res = p.map(_fault, jobs)
    for x in res:
        print("  %-24s 공차 %-4s %s  모듈 수 %s, 대체 %s µs" % (
            x["case"], x["seed"], "통과" if x["passed"] else "불통과 " + str([k for k, v in x["limits"].items() if not v]),
            x["events"], "—" if x["t_rep_us"] is None else "%.2f" % x["t_rep_us"]))
        print("      턴오프 %d번 중 위반 %d, 최대 %.2f A, 위상 첨두 %.1f A(한도 %.1f A), V_A %.2f → %.2f–%.2f V, 고장 순간 %s A,"
              " 정상 첨두 %.1f A·분담 %.3f·손실 %.0f W" % (
                  x["n_turnoff"], x["n_bad"], x["ioff_max"], x["phase_peak"], x["pk_limit"], x["vA_pre"], x["vA"][0], x["vA"][1],
                  ["%.1f" % v for v in x["i_fault"]], x["steady"]["pk"], x["steady"]["share"] or 0, x["steady"]["loss_W"]))
    for kind in ("drive", "charge"):
        nom = [x for x in res if x["kind"] == kind and x["seed"] is None]
        tl = [x for x in res if x["kind"] == kind and x["seed"]]
        verdict("(fault) %s 공칭: F1–F4" % kind, all(x["passed"] for x in nom), "%d/%d" % (sum(x["passed"] for x in nom), len(nom)))
        verdict("(fault) %s 공차 표본 3개: F1–F4" % kind, all(x["passed"] for x in tl), "%d/%d" % (sum(x["passed"] for x in tl), len(tl)))
    chg = [x for x in res if x["kind"] == "charge"]
    req = dict(pk_max=max(x["phase_peak"] for x in chg), pk_steady_max=max(x["steady"]["pk"] for x in chg),
               share_max=max(x["steady"]["share"] for x in chg), loss_mod_max=max(x["steady"]["loss_W"] / 3 for x in chg))
    print("  3모듈 충전(부품 정격 표 입력): 위상 첨두 최대 %.1f A(정상 창 %.1f A), 분담 최대 %.3f, 모듈 손실 최대 %.0f W"
          % (req["pk_max"], req["pk_steady_max"], req["share_max"], req["loss_mod_max"]))
    save_json(EID, "fault", dict(cases=res, mgr=E28.MGR, t_f=T_F, dv_idle=DV_IDLE, parts_input=req))


# ---------------------------------------------------------------- regress
def _reg(name):
    return E28._transient((name, None))


def regress():
    old = {(c["case"], c["seed"]): c for c in json.loads((outdir("E28") / "transient.json").read_text(encoding="utf-8"))["cases"]}
    names = ["MA_540V_bus_5_25_5kW", "MC_800V_charge_prestart"]
    with Pool(workers()) as p:
        res = p.map(_reg, names)
    rows = []
    for m in res:
        o = old[(m["case"], None)]
        a = json.loads(json.dumps(m, default=float)); b = json.loads(json.dumps(o, default=float))
        keys = ("phase_peak", "phase_peak_ref", "ioff_max", "ioff_max_ref", "n_turnoff", "n_bad", "vA", "vA_ref", "events",
                "n_add", "n_rem", "n_mcancel", "passed")
        diff = {}
        for k in keys:
            x, y = a[k], b[k]
            if isinstance(x, list):
                same = json.dumps(x) == json.dumps(y) if not all(isinstance(v, (int, float)) for v in x) else \
                    max(abs(u - v) for u, v in zip(x, y)) <= 1e-9
            elif isinstance(x, float):
                same = abs(x - y) <= 1e-9
            else:
                same = x == y
            if not same:
                diff[k] = [x, y]
        rows.append(dict(case=m["case"], diff=diff))
        print("  %s: %s" % (m["case"], "차 없음" if not diff else diff))
    ok = all(not r["diff"] for r in rows)
    verdict("(regress G1) 고장 없음: E28 transient MA·MC 지표가 저장된 결과와 같음", ok)
    save_json(EID, "regress", dict(rows=rows, passed=ok))


# ---------------------------------------------------------------- figures
def figures():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from plotstyle import korean, COLOR
    korean()
    F = json.loads((outdir(EID) / "fault.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(2, 3, figsize=(15, 7.6))
    for col, name in enumerate(("FA_800V_drive_15kW_m1", "FF_800V_charge_m1")):
        r, n0 = run(name)
        t = r["t"] * 1e3; w = (t > 0.45) & (t < 0.62)
        a = ax[0, col]
        for k in range(8):
            if np.abs(r["i"][w, k]).max() > 0.5:
                a.plot(t[w], r["i"][w, k], lw=0.8, label="위상 %d(모듈 %d)" % (k + 1, k // 2 + 1))
        a.axvline(T_F * 1e3, color="k", ls=":", lw=0.8)
        a.set_title("(%s) %s: 위상 전류" % ("a" if col == 0 else "b", "800 V 주행 15 kW, 모듈 1 고장" if col == 0 else "800 V 충전 375 A, 모듈 1 고장"))
        a.set_xlabel("시간 [ms]"); a.set_ylabel("전류 [A]"); a.legend(fontsize=7, ncol=2)
        b = ax[1, col]
        b.plot(t, r["vb"], color=COLOR["blue"], lw=0.8, label="V_A")
        b2 = b.twinx(); b2.step(t, r["nact"], color=COLOR["red"], lw=1, where="post", label="동작 모듈 수"); b2.set_ylim(0, 4.5)
        b.axvline(T_F * 1e3, color="k", ls=":", lw=0.8)
        b.set_xlabel("시간 [ms]"); b.set_ylabel("V_A [V]"); b2.set_ylabel("동작 모듈 수")
        b.set_title("(%s) V_A와 동작 모듈 수" % ("c" if col == 0 else "d"))
    a = ax[0, 2]
    names = list(CASES)
    for j, s in enumerate(E28.SEEDS):
        xs = [x for x in F["cases"] if x["seed"] == s]
        xs = sorted(xs, key=lambda x: names.index(x["case"]))
        a.bar(np.arange(len(names)) + (j - 1.5) * 0.2, [x["phase_peak"] / x["P_rated"] for x in xs], 0.2,
              label="공칭" if s is None else "공차 %d" % s)
    a.axhline(1.0, color="k", ls="--", lw=0.8); a.axhline(PK_CHG, color="r", ls="--", lw=0.8)
    a.set_xticks(range(len(names))); a.set_xticklabels([n[:2] for n in names])
    a.set_ylabel("위상 첨두 / P_rated(표본)"); a.set_title("(e) 사례별 위상 첨두(주행 한도 1.0, 충전 한도 1.5)"); a.legend(fontsize=7)
    a = ax[1, 2]
    chg = [x for x in F["cases"] if x["kind"] == "charge"]
    for j, s in enumerate(E28.SEEDS):
        xs = sorted([x for x in chg if x["seed"] == s], key=lambda x: names.index(x["case"]))
        a.bar(np.arange(len(xs)) + (j - 1.5) * 0.2, [x["steady"]["pk"] for x in xs], 0.2, label="공칭" if s is None else "공차 %d" % s)
    a.set_xticks(range(4)); a.set_xticklabels([x["case"][:2] for x in sorted([x for x in chg if x["seed"] is None],
                                                                              key=lambda x: names.index(x["case"]))])
    a.set_ylabel("3모듈 충전 정상 위상 첨두 [A]"); a.set_title("(f) 3모듈 375 A 정상(마지막 10주기) 위상 첨두"); a.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    p = outdir(EID) / "E30_module_fault.png"
    fig.savefig(p, dpi=130); print("  → 저장:", p)


PARTS = dict(fault=fault, regress=regress, figures=figures)

if __name__ == "__main__":
    for a in (sys.argv[1:] or list(PARTS)):
        print("■ E30 %s" % a)
        PARTS[a]()
