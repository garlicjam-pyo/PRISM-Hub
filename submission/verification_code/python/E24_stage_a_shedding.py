"""[E24] Stage A 경부하 위상 셰딩: 모듈 출력전류가 작으면 두 위상 중 하나를 멈춰 영전류 스위칭(ZCS) 품질과 손실을 지킨다.

■ 목적
  R2 통합 회로(E23·TB17, docs/28)에서 영교차 추종 2위상은 모듈 출력 10 A 이하에서 턴오프 전류/피크가 5 %를 넘었다
  (E1: 10 A 5.46–5.50 %). 강등 뒤 1008 V에서 Stage C만 남으면 약 10 A다. 이 시험은
  (1) 위상 하나로 운전할 때의 ZCS·위상 첨두·손실로 셰딩 문턱과 복귀 방식을 정하고(design),
  (2) 셰딩을 켠 정상 운전점 격자에서 ZCS 기준을 확인하며(static),
  (3) 부하가 문턱을 지나는 과도에서 턴오프 전류, 위상 첨두, V_A, 모드 전환 횟수를 판정하고(transient),
  (4) 회로 모델 TB18의 기준값을 만든다.
  과도 사례 A–E는 부하 전류원을 V_A 노드(C_A 400 µF)에 바로 건다(버스의 완충이 없어 실제보다 엄격). A–E를 실행한 뒤
  R2 버스(배선 3 mΩ·1.5 µH, C_b 400 µF, 감쇠기 48.6 mΩ + 1.6 mF) 뒤의 정전력 부하와 모듈당 충전 램프(0.94 A/µs)로
  F–J를 더했다(같은 판정 기준, F–J는 TB18 회로 사례). 사례 E는 충전 램프 요구(전체 3.75 A/µs)를 모듈 하나에 걸어
  요구보다 4배 가팔랐다.
  모델: model_stage_a.sim_array(dead_fix=True). E1–E23의 데드타임 처리는 RK4가 부호 의존 다이오드 기울기를 평균해 데드타임
  전류가 0으로 가지 않고 남았다(멈춘 위상에서는 진동). F 1차 실행에서 이것이 복귀 위상의 강제 턴오프 고착(18 A)으로 나타났다.
  E24는 소멸 처리를 켜고, 위상 정격 첨두도 같은 모델로 다시 계산했다(76.4 A).

■ 왜 필요한가
  영교차 추종 게이트는 전류가 검출 문턱(0.5 A) 아래로 돌아온 뒤 검출 지연(20 ns) 만큼 늦게 끈다. 공진전류 첨두가
  작으면 이 문턱·지연이 반주기에서 차지하는 몫이 커져 비율이 오른다. 같은 출력전류를 위상 하나가 맡으면 첨두가
  약 두 배가 되어 비율이 절반 아래로 내려가고, 위상당 고정 손실(출력용량·게이트, 약 15.6 W/위상)도 준다.
  대신 위상 하나가 부하 계단을 받는 동안 첨두가 커지고, 멈췄던 위상은 플라잉 커패시터 전압이 그대로인 채 다시
  시작한다. 이 과도를 확인하지 않으면 셰딩이 위상 정격을 넘기거나 문턱 근처에서 반복 전환(채터링)할 수 있다.

■ 셰딩 논리(model_stage_a.shed_step, 회로 ctrl/prism_gate_stageA_zcps.m과 같음)
  모듈 출력전류 i_o = Σ(구간 1이면 +i, 구간 2이면 −i)를 1차 필터(τ)로 거른다.
  두 위상 → |i_o| < I_off가 t_dwell 동안 이어지면 멈출 위상이 지금 구간을 자연 턴오프로 끝낸 뒤(구간 0) 막는다.
  위상 하나 → |i_o| > I_on 또는 남는 위상의 순시 |i| > I_pk,on이면 바로 막음을 푼다(다음 데드타임 끝에서 시작).
  도통 중인 구간을 자르지 않으므로 멈추는 순간도 영전류다. 멈춘 위상은 다음 구간(충전·방전 교대)부터 시작한다.

■ 판정 기준(시험 전에 고정, design에서 문턱을 정한 뒤 static·transient 전에 정함)
  static  (S1) |I| ≥ 7.5 A: 위상별 턴오프 전류/피크 ≤ 5 %(마지막 10주기, E1·TB06과 같은 정의)
          (S2) |I| < 7.5 A: 턴오프 순간 전류 ≤ 1.0 A(검출 문턱 0.5 A의 두 배. 이 영역은 비율이 뜻이 없다)
  transient(전 구간, 0.3 ms 이후)
          (T1) 모든 턴오프: |i_off| ≤ max(5 % × 그 반주기 첨두, 1.0 A)
          (T2) 위상 첨두 ≤ 76.4 A(위상 정격 첨두 = E1 충전 정격점 788 V·46.875 A/위상의 위상 하나 첨두)
          (T3) V_A 최저·최고가 셰딩 없는 2위상 운전(같은 프로파일)과 0.5 V 안
          (T4) 모드 전환이 문턱 사건마다 한 번(셰딩·복귀가 예상 횟수, 채터링 없음)

  deadfix: 데드타임 전류 소멸 처리의 영향(TB16·TB17 회로의 Stage A 운전점에서 이전 처리와 회로 V_A 비교)
■ 실행   python E24_stage_a_shedding.py design static transient deadfix figures   (2코어 약 10분)
■ 결과   results/E24/design.json, static.json, transient.json, deadfix.json, E24_stage_a_shedding.png
"""
import json
import sys
from multiprocessing import Pool

import numpy as np

import model_stage_a as A
from common import save_json, verdict, outdir, workers

EID = "E24"
T = 1 / A.FR0
CA = 400e-6
DF = True                 # 데드타임 전류 소멸 처리(model_stage_a dead_fix). E24의 모든 계산에 쓴다
RATED_PK = 76.4           # 위상 정격 첨두 [A]: E1 충전 정격점(788 V, 46.875 A/위상)에서 위상 하나의 첨두(DF 모델, design에서 확인)
I_ABS = 1.0               # 비율 대신 보는 턴오프 전류 상한 [A]
I_LOW = 7.5               # 이 아래는 (S2)

# 셰딩 설계값(design에서 정함, 근거는 design() 출력과 docs/29)
SHED = dict(keep=0, sh=1, I_off=15., I_on=22., Ipk_on=36., tau=2e-6, t_dwell=100e-6, off_frac=-1.)

DESIGN_V = (540., 1008.)
DESIGN_I = (-7.5, -5., -3., 3., 5., 7.5, 10., 12., 15., 18., 20., 22., 25., 30., 40., 46.875, 60., 75.)
STATIC_I = (-10., -6., -3., 3., 5., 7.5, 10., 12., 14., 18., 25., 46.875, 75.)


def _steady(args):
    V, N, I = args
    r = A.sim_array(N=N, Vbat=V, Iload=I, Cbus=CA, mode="zcp", ncyc=60, dead_fix=DF)
    ph, bus = A.analyze(r, ncyc_last=10)
    return dict(V=V, N=N, I=I, zcs=max(p["zcs"] for p in ph), Ipk=max(p["Ipk"] for p in ph),
                loss=sum(p["Ploss"] for p in ph), ripple=bus["ripple"], Vbus=bus["Vbus"])


def design():
    """1위상·2위상 정상 운전의 ZCS·위상 첨두·손실(E1 손실 추정)."""
    jobs = [(V, N, I) for V in DESIGN_V for N in (1, 2) for I in DESIGN_I] + [(788., 1, 46.875)]
    with Pool(workers()) as p:
        rows = p.map(_steady, jobs)
    rated = rows.pop()                                     # 위상 정격 첨두: E1 충전 정격점(788 V, 46.875 A/위상) 위상 하나
    print("  위상 정격 첨두(788 V, 46.875 A, 위상 하나): %.1f A(코드 상수 %.1f A)" % (rated["Ipk"], RATED_PK))
    for V in DESIGN_V:
        print("  배터리 %.0f V: 출력전류 [A] / 2위상 ZCS·첨두·손실 / 1위상 ZCS·첨두·손실" % V)
        for I in DESIGN_I:
            a = next(r for r in rows if r["V"] == V and r["N"] == 2 and r["I"] == I)
            b = next(r for r in rows if r["V"] == V and r["N"] == 1 and r["I"] == I)
            print("   %7.2f  2위상 %5.2f %% %5.1f A %5.1f W | 1위상 %5.2f %% %5.1f A %5.1f W"
                  % (I, 100 * a["zcs"], a["Ipk"], a["loss"], 100 * b["zcs"], b["Ipk"], b["loss"]))
    fw = [r for r in rows if r["I"] > 0]
    z2 = {V: min(I for I in DESIGN_I if I > 0 and all(
        next(r for r in fw if r["V"] == V and r["N"] == 2 and r["I"] == J)["zcs"] <= 0.05 for J in DESIGN_I if J >= I)) for V in DESIGN_V}
    cross = {}
    for V in DESIGN_V:
        c = [I for I in DESIGN_I if I > 0 and next(r for r in fw if r["V"] == V and r["N"] == 1 and r["I"] == I)["loss"]
             >= next(r for r in fw if r["V"] == V and r["N"] == 2 and r["I"] == I)["loss"]]
        cross[V] = min(c) if c else None
    pk1_on = max(r["Ipk"] for r in fw if r["N"] == 1 and r["I"] <= SHED["I_on"] - 2)   # I_on 아래 정상 1위상 첨두
    print("  2위상 ZCS ≤ 5 %%가 그 위 전부에서 지켜지는 최소 전류: %s" % z2)
    print("  1위상 손실이 2위상 이상이 되는 최소 전류(격자): %s" % cross)
    print("  선택: I_off %.0f A(2위상 ZCS 여유: 15 A에서 3.8 %%), I_on %.0f A(히스테리시스 %.0f A), "
          "I_pk,on %.0f A(I_on − 2 A 아래 정상 1위상 첨두 최대 %.1f A 위), τ %.0f µs, 지속 %.0f µs, 복귀는 바로 시작"
          % (SHED["I_off"], SHED["I_on"], SHED["I_on"] - SHED["I_off"], SHED["Ipk_on"], pk1_on, SHED["tau"] * 1e6,
             SHED["t_dwell"] * 1e6))
    ok = pk1_on < SHED["Ipk_on"] and all(v <= SHED["I_off"] for v in z2.values()) and abs(rated["Ipk"] - RATED_PK) < 0.1
    verdict("(design) 문턱 일관성: 2위상은 I_off 위에서 ZCS ≤ 5 %, 정상 1위상 첨두 < I_pk,on", ok,
            "2위상 최소 %s A, 1위상 첨두 %.1f A" % (z2, pk1_on))
    save_json(EID, "design", dict(rows=rows, shed=SHED, min_I_2ph_zcs=z2, loss_cross=cross, pk1_below_on=pk1_on,
                                  rated_pk=RATED_PK, rated_point=rated, dead_fix=DF))


def turnoffs(r, t0=0.):
    """반주기별 턴오프: (위상, 시각, 턴오프 전류, 그 반주기 첨두). 턴오프 전류 = 마지막 도통 표본(E1과 같은 정의)."""
    out = []
    t = r["t"]
    for k in range(r["N"]):
        s = r["st"][:, k].astype(int); i = r["i"][:, k].astype(float)
        off = np.where((s[:-1] != 0) & (s[1:] == 0))[0]
        on = np.where((s[:-1] == 0) & (s[1:] != 0))[0] + 1
        for o in off:
            j = on[on <= o]
            if len(j) == 0 or t[o] < t0:
                continue
            out.append((k, t[o], i[o], float(np.abs(i[j[-1]:o + 1]).max())))
    return out


def _static(I):
    out = {}
    for V in DESIGN_V:
        r = A.sim_array(N=2, Vbat=V, Iload=I, Cbus=CA, mode="zcp", ncyc=int(0.6e-3 / T), shed=SHED, dead_fix=DF)
        tl = r["t"][-1] - 10 * T
        to = [x for x in turnoffs(r, tl)]
        zr = max(abs(x[2]) / x[3] for x in to)
        za = max(abs(x[2]) for x in to)
        nph = int(sum(1 for k in range(2) if np.any(r["st"][r["t"] > tl, k] != 0)))
        out[V] = dict(I=I, V=V, phases=nph, zcs=zr, ioff_max=za, mode_end=int(r["sm"][-1]),
                      ok=(zr <= 0.05) if abs(I) >= I_LOW else (za <= I_ABS))
    return out


def static():
    with Pool(workers()) as p:
        res = p.map(_static, STATIC_I)
    rows = [x for d in res for x in d.values()]
    for x in rows:
        print("  %4.0f V %7.2f A: 위상 %d, 턴오프/첨두 %.2f %%, 턴오프 최대 %.2f A, %s"
              % (x["V"], x["I"], x["phases"], 100 * x["zcs"], x["ioff_max"], "통과" if x["ok"] else "불통과"))
    verdict("(static) 셰딩 켬: |I| ≥ 7.5 A ZCS ≤ 5 %, |I| < 7.5 A 턴오프 ≤ 1 A", all(x["ok"] for x in rows),
            "%d/%d" % (sum(x["ok"] for x in rows), len(rows)))
    save_json(EID, "static", dict(rows=rows, shed=SHED))


# 과도 사례(시험 전에 고정). 전류원 부하를 V_A 노드(C_A 400 µF)에 바로 건다(버스 회로의 완충이 없어 실제보다 엄격).
CASES = {
    "A_1008V_54_10_54": dict(V=1008., prof=([0, .5e-3, .51e-3, 1.5e-3, 1.51e-3, 1], [54, 54, 10, 10, 54, 54]), tend=2.0e-3,
                             n_shed=1, n_ret=1),
    "B_540V_54_10_54": dict(V=540., prof=([0, .5e-3, .51e-3, 1.5e-3, 1.51e-3, 1], [54, 54, 10, 10, 54, 54]), tend=2.0e-3,
                            n_shed=1, n_ret=1),
    "C_1008V_ramp_40_3_40": dict(V=1008., prof=([0, .3e-3, 1.3e-3, 2.3e-3, 1], [40, 40, 3, 40, 40]), tend=2.5e-3,
                                 n_shed=1, n_ret=1),
    "D_1008V_rev_10_m6_10": dict(V=1008., prof=([0, .5e-3, .51e-3, 1.5e-3, 1.51e-3, 1], [10, 10, -6, -6, 10, 10]), tend=2.0e-3,
                                 n_shed=1, n_ret=0),
    "E_1008V_10_75_charger": dict(V=1008., prof=([0, 1.0e-3, 1.0e-3 + 65 / 3.75e6, 1], [10, 10, 75, 75]), tend=1.5e-3,
                                  n_shed=1, n_ret=1),
    # 사례 F–H(A–E 실행 뒤 추가, 판정 기준은 같음): R2 버스(E23과 같은 배선·C_b·감쇠기) 뒤의 정전력 부하와 V_A 노드의 충전기.
    # 사례 E는 충전전류 램프 요구(전체 3.75 A/µs, TB07)를 모듈 하나에 그대로 걸어 모듈당 요구(0.94 A/µs)보다 4배 가팔랐다.
    "F_1008V_bus_25_5_25kW": dict(V=1008., prof=0., bus=([0, .5e-3, .5e-3 + 1e-9, 1.5e-3, 1.5e-3 + 1e-9, 1], [25e3, 25e3, 5e3, 5e3, 25e3, 25e3]),
                                  tend=2.0e-3, n_shed=1, n_ret=1),
    "G_540V_bus_13p5_2p7_13p5kW": dict(V=540., prof=0., bus=([0, .5e-3, .5e-3 + 1e-9, 1.5e-3, 1.5e-3 + 1e-9, 1],
                                                            [13.5e3, 13.5e3, 2.7e3, 2.7e3, 13.5e3, 13.5e3]), tend=2.0e-3, n_shed=1, n_ret=1),
    "H_1008V_bus5kW_charger_74A": dict(V=1008., prof=([0, 1.0e-3, 1.0e-3 + 74.4 / 0.9375e6, 1], [0, 0, -74.4, -74.4]),
                                       bus=([0, 1], [5e3, 5e3]), tend=1.5e-3, n_shed=1, n_ret=1),
    # 사례 I·J: C·D를 R2 버스로(TB18 회로 사례와 같음)
    "I_1008V_bus_ramp_20_1p5_20kW": dict(V=1008., prof=0., bus=([0, .3e-3, 1.3e-3, 2.3e-3, 1], [20e3, 20e3, 1.5e3, 20e3, 20e3]),
                                         tend=2.5e-3, n_shed=1, n_ret=1),
    "J_1008V_bus5kW_rev_m16A": dict(V=1008., prof=([0, .5e-3, .51e-3, 1.5e-3, 1.51e-3, 1], [0, 0, -16, -16, 0, 0]),
                                    bus=([0, 1], [5e3, 5e3]), tend=2.0e-3, n_shed=1, n_ret=0),
}
BUS = dict(Rw=3e-3, Lw=1.5e-6, Cb=400e-6, Rd=48.6e-3, Cd=1.6e-3, vmin=200.)   # E23·TB16과 같은 R2 버스


def run_case(name, shed=True):
    c = CASES[name]
    bus = dict(BUS, P=c["bus"]) if "bus" in c else None
    return A.sim_array(N=2, Vbat=c["V"], Iload=c["prof"], Cbus=CA, mode="zcp", ncyc=int(c["tend"] / T),
                       shed=SHED if shed else None, bus=bus, dead_fix=DF)


def _transient(name):
    return case_metrics(name, run_case(name, True), run_case(name, False))


def case_metrics(name, r, b):
    """과도 사례 판정(T1–T4)과 지표. r = 셰딩 켬, b = 셰딩 없음(같은 프로파일). TB18 기준값도 이 함수로 만든다."""
    c = CASES[name]
    t = r["t"]; w = t > 0.3e-3
    to = turnoffs(r, 0.3e-3)
    bad = [x for x in to if abs(x[2]) > max(0.05 * x[3], I_ABS)]
    pk = float(np.abs(r["i"][w]).max()); pkb = float(np.abs(b["i"][w]).max())
    vmin, vmax = float(r["vb"][w].min()), float(r["vb"][w].max())
    bmin, bmax = float(b["vb"][w].min()), float(b["vb"][w].max())
    sm = r["sm"]; ch = np.where(np.diff(sm) != 0)[0]
    ev = [(round(float(t[k + 1]) * 1e3, 4), int(sm[k + 1])) for k in ch]
    n_shed = sum(1 for e in ev if e[1] == 1); n_ret = sum(1 for x, y in zip([2] + [e[1] for e in ev], [e[1] for e in ev]) if y == 2 and x in (1, 4))
    n3c = sum(1 for x, y in zip([2] + [e[1] for e in ev], [e[1] for e in ev]) if x == 3 and y == 2)   # 멈추기 취소
    tob = turnoffs(b, 0.3e-3)
    L = dict(T1=len(bad) == 0, T2=pk <= RATED_PK, T3=abs(vmin - bmin) <= 0.5 and abs(vmax - bmax) <= 0.5,
             T4=n_shed == c["n_shed"] and n_ret == c["n_ret"] and n3c == 0)
    # 정보: 셰딩 없는 2위상의 (T1) 위반 수, 반주기별 비율 최대(1 A 넘는 턴오프만)
    badb = [x for x in tob if abs(x[2]) > max(0.05 * x[3], I_ABS)]
    return dict(case=name, V=c["V"], limits=L, passed=all(L.values()), events=ev, n_turnoff=len(to), n_bad=len(bad),
                worst=max(to, key=lambda x: abs(x[2]) - max(0.05 * x[3], I_ABS))[1:] if to else None,
                ioff_max=max(abs(x[2]) for x in to), phase_peak=pk, phase_peak_noshed=pkb, vA=[vmin, vmax], vA_noshed=[bmin, bmax],
                n_bad_noshed=len(badb), ioff_max_noshed=max(abs(x[2]) for x in tob))


def transient():
    with Pool(workers()) as p:
        res = p.map(_transient, list(CASES))
    for x in res:
        print("  %-24s %s  전환 %s" % (x["case"], "통과" if x["passed"] else "불통과 " + str([k for k, v in x["limits"].items() if not v]),
                                     x["events"]))
        print("      턴오프 %d번 중 (T1) 위반 %d(셰딩 없음 %d), 턴오프 전류 최대 %.2f A(셰딩 없음 %.2f A), 위상 첨두 %.1f A(셰딩 없음 %.1f A), "
              "V_A %.2f–%.2f V(셰딩 없음 %.2f–%.2f V)"
              % (x["n_turnoff"], x["n_bad"], x["n_bad_noshed"], x["ioff_max"], x["ioff_max_noshed"], x["phase_peak"],
                 x["phase_peak_noshed"], x["vA"][0], x["vA"][1], x["vA_noshed"][0], x["vA_noshed"][1]))
    verdict("(transient) A–E(V_A 노드에 바로 건 전류원): 턴오프 전류, 위상 첨두 ≤ 정격 첨두, V_A, 채터링 없음",
            all(x["passed"] for x in res if x["case"] < "F"), "%d/%d" % (sum(x["passed"] for x in res if x["case"] < "F"),
                                                                      sum(1 for x in res if x["case"] < "F")))
    verdict("(transient) F–J(R2 버스 뒤 정전력 부하, 모듈당 충전 램프): 같은 기준", all(x["passed"] for x in res if x["case"] >= "F"),
            "%d/%d" % (sum(x["passed"] for x in res if x["case"] >= "F"), sum(1 for x in res if x["case"] >= "F")))
    save_json(EID, "transient", dict(cases=res, shed=SHED, rated_pk=RATED_PK))


def figures():
    from plotstyle import korean, COLOR as C
    plt = korean()
    D = json.loads((outdir(EID) / "design.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(2, 2, figsize=(13, 8.5))
    for V, ls in ((1008., "-"), (540., "--")):
        for N, col in ((2, C["blue"]), (1, C["red"])):
            rr = sorted([r for r in D["rows"] if r["V"] == V and r["N"] == N and r["I"] > 0], key=lambda r: r["I"])
            lab = "%d위상, %.0f V" % (N, V)
            ax[0, 0].plot([r["I"] for r in rr], [100 * r["zcs"] for r in rr], ls, color=col, marker="o", ms=3, label=lab)
            ax[0, 1].plot([r["I"] for r in rr], [r["loss"] for r in rr], ls, color=col, marker="o", ms=3, label=lab)
    ax[0, 0].axhline(5, color="k", ls=":"); ax[0, 0].axvspan(0, SHED["I_off"], color=C["red"], alpha=0.06)
    ax[0, 0].set_xscale("log"); ax[0, 0].set_xlabel("모듈 출력전류 [A]"); ax[0, 0].set_ylabel("턴오프 전류/첨두 [%]")
    ax[0, 0].set_title("(a) 영전류 스위칭 품질(붉은 띠: 셰딩 구간 < I_off)", fontsize=9); ax[0, 0].legend(fontsize=7)
    ax[0, 1].set_xlabel("모듈 출력전류 [A]"); ax[0, 1].set_ylabel("모듈 손실 추정 [W]"); ax[0, 1].set_title("(b) 손실(E1 추정)", fontsize=9)
    ax[0, 1].legend(fontsize=7)
    for name, a in (("A_1008V_54_10_54", ax[1, 0]), ("E_1008V_10_75_charger", ax[1, 1])):
        r = run_case(name, True); b = run_case(name, False)
        t = r["t"] * 1e3
        a.plot(t, r["i"][:, 0], color=C["blue"], lw=0.5, label="위상 1(셰딩)")
        a.plot(t, r["i"][:, 1], color=C["red"], lw=0.5, label="위상 2(셰딩)")
        a.plot(b["t"] * 1e3, np.abs(b["i"]).max(axis=1), color="0.6", lw=0.5, label="|i| 최대(셰딩 없음)")
        a.axhline(RATED_PK, color="k", ls=":"); a.axhline(-RATED_PK, color="k", ls=":")
        a2 = a.twinx(); a2.plot(t, r["sm"], color=C["green"], lw=1); a2.set_ylabel("셰딩 모드(2 둘, 3 멈추는 중, 1 하나)")
        a.set_xlabel("시간 [ms]"); a.set_ylabel("위상 공진전류 [A]"); a.legend(fontsize=7, loc="lower left")
        a.set_title("(%s) %s" % ("c" if a is ax[1, 0] else "d", name), fontsize=9)
    fig.tight_layout(); fig.savefig(outdir(EID) / "E24_stage_a_shedding.png", dpi=150); plt.close(fig)
    print("  figures saved")


# TB16·TB17 회로의 Stage A 운전점(배터리 전압, 모듈 출력전류)과 그 회로의 V_A 평균(10 µs 평균의 0.2 ms 평균)
DF_POINTS = [(540., 37.53, 269.611), (540., 56.26, 269.415), (806., 44.88, 402.533), (806., 69.82, 402.273),
             (907., 33.43, 453.153), (907., 15.60, 453.339), (1008., 49.95, 503.481), (930., 54.39, 464.434)]


def _df(args):
    V, I, fix = args
    r = A.sim_array(N=2, Vbat=V, Iload=I, Cbus=CA, mode="zcp", ncyc=80, dead_fix=fix)
    ph, bus = A.analyze(r, ncyc_last=10)
    return dict(V=V, I=I, fix=fix, vA=bus["Vbus"], zcs=max(p["zcs"] for p in ph))


def deadfix():
    """데드타임 전류 소멸 처리의 영향: TB16·TB17 회로의 Stage A 운전점에서 이전 처리(E1–E23)와 고친 처리의 V_A·ZCS."""
    jobs = [(V, I, f) for V, I, _ in DF_POINTS for f in (False, True)]
    with Pool(workers()) as p:
        rr = p.map(_df, jobs)
    rows = []
    for V, I, vc in DF_POINTS:
        a = next(r for r in rr if r["V"] == V and r["I"] == I and not r["fix"])
        b = next(r for r in rr if r["V"] == V and r["I"] == I and r["fix"])
        rows.append(dict(V=V, I=I, vA_circuit=vc, vA_old=a["vA"], vA_fix=b["vA"], zcs_old=a["zcs"], zcs_fix=b["zcs"]))
        print("  %4.0f V %6.2f A: V_A 회로 %.3f, 이전 %.3f(%+.3f), 고침 %.3f(%+.3f) / ZCS 이전 %.2f %%, 고침 %.2f %%"
              % (V, I, vc, a["vA"], vc - a["vA"], b["vA"], vc - b["vA"], 100 * a["zcs"], 100 * b["zcs"]))
    e0 = max(abs(r["vA_circuit"] - r["vA_old"]) for r in rows); e1 = max(abs(r["vA_circuit"] - r["vA_fix"]) for r in rows)
    verdict("(deadfix) 고친 처리가 회로 V_A에 더 가깝다", e1 < e0, "최대 차 이전 %.3f V, 고침 %.3f V" % (e0, e1))
    save_json(EID, "deadfix", dict(rows=rows, max_err_old=e0, max_err_fix=e1))


PARTS = dict(design=design, static=static, transient=transient, deadfix=deadfix, figures=figures)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        print("==== E24 %s ====" % w)
        PARTS[w]()
