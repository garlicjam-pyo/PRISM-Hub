"""[E35 설계 단계] A25 수정안(A25R)의 설계 변경 후보를 개발 사례에서 고른다(판정 시험이 아님).

E33(docs/38)에서 A25는 과도 판정을 대부분 통과하지 못했다. 사용자 결정(2026-10-28): A25를 고쳐 다시 판정한다.
이 스크립트는 고칠 내용을 정하는 설계 단계다. 여기서 정한 규칙을 E35_a25r_verify.py의 판정 기준과 함께 커밋한 뒤 전체 사례를
판정한다(개발 사례와 판정 사례는 겹치지만, 판정 기준은 E28·E33과 같고 바꾸지 않는다).

후보
  D1 충전 요청 중 위상 셰딩 정지(cfg chg_noshed): E33 slow의 위반이 충전 시작 때 셰딩된 위상의 복귀와 전류 방향 반전이
     겹친 작은 반주기에서 났다.
  D2 충전 요구 600 µs(사전 기동·램프, 공진 15주기 = 150 kHz의 100 µs와 같은 주기 수): E33 slow 사례 그대로
  D3 V_A 노드 순간 부하 계단을 M0(Stage C + V2L, 9.1 kW)로 제한하는 요구(docs/35: D·M1은 계약 변화율 0.5 kW/ms):
     MA·MG의 20 kW 순간 계단 대신 9.1 kW 계단 사례(MA_M0·MG_M0)
사례: MC·MD·ME slow, MA, MA_M0, MG, MG_M0 × 기준(E33 A25) / D1, 공칭.

dev2(첫 결과 뒤 추가): D1만으로는 느린 충전 위반이 1번씩 남고 V_A가 전부 켬보다 1.7 V 벗어났다. E33 진단에서 관리기 시간 상수
  다섯 개를 모두 150 kHz 값으로 두면(TM1) 통과했으므로, 하나씩 150 kHz 값으로 되돌려 어느 것이 원인인지 본다(느린 충전 3사례).

dev2 결과: 하나만 되돌리면 어느 것도 통과하지 않았다(tau_m·t_lock·t_hold는 결과가 같고, tau·t_dwell은 위반이 남거나 첨두가 커짐).
  TM1의 통과는 셰딩이 충전 램프보다 먼저 끝난 시각 차이로 보인다.
dev3: D1에서 남은 것은 (a) 충전 램프 끝(2.2 ms)의 V_A가 전부 켬보다 1.7 V 높음, (b) 모듈 줄임 때 남는 모듈의 두 번째 위상 재시작
  반주기 1번(1.1–1.3 A). 충전 요청으로 모듈 3개가 같은 순간에 켜지면 위상들이 같은 자리에서 돌아 인터리빙이 깨진다(25 kHz에서
  V_A 리플이 커짐). 후보 D4: 막혔다 풀린 위상은 기준 위상(가장 낮은 번호의 동작 위상)의 마지막 구간 시작 + 인터리빙 차 자리에서만
  시작(cfg align_start). D4 단독, D1 + D4를 느린 충전 3사례와 Tier-1 계단 2사례(docs/14 D3, ±10 kW)에서 본다.

dev3 결과: Tier-1 계단(MA10·MG10)은 A25 그대로 통과. 느린 충전은 D4 단독·D1 + D4 모두 불통과(D1 + D4는 MC가 V_A 1.02 V로 T3만,
  ME는 첨두 91.5 A로 더 나빠짐).
dev4: E33 진단에서 MC 느린 충전을 통과한 두 변경(TM1: 관리기 시간 상수 다섯 개를 150 kHz 값, CA6: C_A 2.4 mF)을 MD·ME 느린 충전과
  Tier-1 계단 2사례에도 적용해 본다.

■ 실행   python E35_a25r_design.py [dev] [dev2] [dev3] [dev4]   (2코어 각 약 25·35·40·35분)
■ 결과   results/E35/design_dev.json, design_dev2.json, design_dev3.json, design_dev4.json
"""
from multiprocessing import Pool

import E28_stage_a_modules as E28
import E33_stage_a_25k_dynamics as E33
from common import save_json, workers

STEP = E28.STEP
M0 = 9.1e3


def dev_cases():
    """E28 사례 정의(이동 전 시각) + M0 계단 사례. E33.shifted_cases와 같은 0.6 ms 이동을 한다."""
    base = {
        "MA_M0_540V_bus_5_14_5kW": dict(V=540., prof=0., bus=STEP(5e3, 5e3 + M0, 0.5e-3, 1.5e-3), tend=2.9e-3, n_end=1, add_max=1, rem_max=1),
        "MG_M0_1008V_bus_25_16_25kW": dict(V=1008., prof=0., bus=STEP(25e3, 25e3 - M0, 0.5e-3, 1.5e-3), tend=2.9e-3, n_end=1,
                                           add_max=1, rem_max=1),
    }
    out = {}
    for k, c in base.items():
        cc = dict(c); cc["bus"] = (E33._sh(c["bus"][0]), list(c["bus"][1])); cc["tend"] = c["tend"] + E33.SHIFT
        out[k] = cc
    return out


R1_MGR = dict(E28.MGR)                                       # import 시점 = 150 kHz 관리기 값
TM_KEYS = ("tau", "t_dwell", "tau_m", "t_lock", "t_hold")


def _run(args):
    var, name = args
    E33.configure()
    E28.CASES = dict(E28.CASES, **E33.slow_cases(), **dev_cases(), **tier1())
    if var == "D1":
        E28.MGR = dict(E28.MGR, chg_noshed=True)
    elif var == "TM1":
        E28.MGR = dict(E28.MGR, **{k: R1_MGR[k] for k in TM_KEYS})
    elif var == "CA6":
        E28.CA = 6 * 400e-6
    elif var == "D4":
        E28.MGR = dict(E28.MGR, align_start=True)
    elif var == "D14":
        E28.MGR = dict(E28.MGR, chg_noshed=True, align_start=True)
    elif var.startswith("R1:"):
        E28.MGR = dict(E28.MGR, **{var[3:]: R1_MGR[var[3:]]})
    m = E28.case_metrics(name, E28.run_case(name), E28.run_case(name, ref=True), None)
    m.update(variant=var)
    return m


def report(rows):
    for x in rows:
        print("  %-10s %-28s %s 턴오프 위반 %d(전부 켬 %d) 최대 %.2f A, 첨두 %.1f A(전부 켬 %.1f, 한도 %.1f), V_A %.2f–%.2f(전부 켬 %.2f–%.2f), 모듈 %s"
              % (x["variant"], x["case"], "통과" if x["passed"] else "불통과 " + str([k for k, v in x["limits"].items() if not v]),
                 x["n_bad"], x["n_bad_ref"], x["ioff_max"], x["phase_peak"], x["phase_peak_ref"], x["P_rated"], x["vA"][0], x["vA"][1],
                 x["vA_ref"][0], x["vA_ref"][1], x["events"]))


def dev2():
    E33.configure()
    jobs = [("R1:" + k, n) for k in TM_KEYS for n in E33.slow_cases()]
    with Pool(workers()) as p:
        rows = p.map(_run, jobs, chunksize=1)
    report(rows)
    save_json("E35", "design_dev2", dict(rows=rows, R1=R1_MGR, note="설계 단계(판정 시험 아님): 시간 상수 하나씩 150 kHz 값"))


def tier1():
    """docs/14 D3 Tier-1 대표 시험(±10 kW 계단)을 MA·MG 조건에."""
    base = {"MA10_540V_bus_5_15_5kW": dict(V=540., prof=0., bus=STEP(5e3, 15e3, 0.5e-3, 1.5e-3), tend=2.9e-3, n_end=1, add_max=1, rem_max=1),
            "MG10_1008V_bus_25_15_25kW": dict(V=1008., prof=0., bus=STEP(25e3, 15e3, 0.5e-3, 1.5e-3), tend=2.9e-3, n_end=1,
                                              add_max=1, rem_max=1)}
    out = {}
    for k, c in base.items():
        cc = dict(c); cc["bus"] = (E33._sh(c["bus"][0]), list(c["bus"][1])); cc["tend"] = c["tend"] + E33.SHIFT
        out[k] = cc
    return out


def dev3():
    E33.configure()
    names = list(E33.slow_cases()) + list(tier1())
    jobs = [(v, n) for v in ("A25", "D4", "D14") for n in names if not (v == "A25" and n.startswith("M") and "slow" in n)]
    with Pool(workers()) as p:
        rows = p.map(_run, jobs, chunksize=1)
    report(rows)
    save_json("E35", "design_dev3", dict(rows=rows, note="설계 단계(판정 시험 아님): D4 인터리빙 맞춤 시작, D1 + D4"))


def dev4():
    E33.configure()
    names = ["MD_640V_charge_slow", "ME_920V_charge_slow"] + list(tier1())
    jobs = [(v, n) for v in ("TM1", "CA6") for n in names]
    with Pool(workers()) as p:
        rows = p.map(_run, jobs, chunksize=1)
    report(rows)
    save_json("E35", "design_dev4", dict(rows=rows, note="설계 단계(판정 시험 아님): TM1·CA6을 MD·ME 느린 충전과 Tier-1 계단에"))


def dev():
    E33.configure()
    names = list(E33.slow_cases()) + ["MA_540V_bus_5_25_5kW", "MG_1008V_bus_25_5_25kW"] + list(dev_cases())
    jobs = [(v, n) for v in ("A25", "D1") for n in names if not (v == "D1" and n.startswith(("MA", "MG")))]
    with Pool(workers()) as p:
        rows = p.map(_run, jobs, chunksize=1)
    for x in rows:
        print("  %-4s %-28s %s 턴오프 위반 %d(전부 켬 %d) 최대 %.2f A, 첨두 %.1f A(전부 켬 %.1f, 한도 %.1f), V_A %.2f–%.2f(전부 켬 %.2f–%.2f), 모듈 %s"
              % (x["variant"], x["case"], "통과" if x["passed"] else "불통과 " + str([k for k, v in x["limits"].items() if not v]),
                 x["n_bad"], x["n_bad_ref"], x["ioff_max"], x["phase_peak"], x["phase_peak_ref"], x["P_rated"], x["vA"][0], x["vA"][1],
                 x["vA_ref"][0], x["vA_ref"][1], x["events"]))
    save_json("E35", "design_dev", dict(rows=rows, note="설계 단계(판정 시험 아님)"))


if __name__ == "__main__":
    import sys
    for part in (sys.argv[1:] or ["dev"]):
        globals()[part]()
