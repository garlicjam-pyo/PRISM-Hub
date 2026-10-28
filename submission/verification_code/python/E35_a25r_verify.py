"""[E35] Stage A 25 kHz 설계 수정안(A25R) 판정: E33과 같은 판정 기준으로 정상점·과도·모듈 고장을 다시 확인.

■ 목적
  E33(docs/38)에서 A25는 모듈 고장 처리는 통과했지만 과도 판정을 대부분 통과하지 못했다. 사용자 결정(2026-10-28)에 따라 A25를
  고친 설계(A25R)를 같은 기준으로 다시 판정한다. 무엇을 고칠지는 설계 단계(E35_a25r_design.py, results/E35/design_dev*.json)에서
  정했고, 이 파일의 판정 기준은 실행 전에 커밋한다.

■ A25R = A25 + 아래 변경(설계 단계 결과로 정함)
  __DESIGN__

■ 사례(실행 전에 고정)
  static   : E33과 같다(주행 540·800·1008 V × 3–220 A, 충전 640·800·920 V × −30–−375 A) × 공칭·표본 1
  transient(요구 안): 요구에 맞춘 사례 6개
     MA10 540 V 버스 5 → 15 → 5 kW 계단, MG10 1008 V 25 → 15 → 25 kW 계단 — docs/14 D3의 Tier-1 대표 시험(±10 kW 계단).
        임의의 1 ms 창 최대 부하 변화가 +7.98·−9.3 kW라는 계약에서 나온 값이다(E28의 20 kW 순간 계단은 이 계약 밖).
     MB 800 V 버스 램프 2 → 36 → 2 kW(E28과 같음)
     MC·MD·ME 충전 시작·종료: 사전 기동 600 µs·충전전류 램프 600 µs(E33 slow와 같은 시각; 공진 15주기 = 150 kHz 설계의 100 µs와
        같은 주기 수)
  transient(요구 밖, 정보): E28 원 사례 MA·MG(20 kW 순간 계단), MC·MD·ME(100 µs), MF(사전 기동 없음) — 판정 출력은 하되 E35
     합격 여부에 넣지 않는다.
  fault    : E30 FA–FH(E33과 같은 시각) × 공칭·표본 1

■ 판정 기준(E28·E30·E33과 같음, 시험 전에 고정)
  static  S1 |I_m| ≥ 7.5 A 비율 ≤ 5 %, S2 < 7.5 A 턴오프 ≤ 1.0 A, S3 모듈·위상 수 = 규칙, S4 위상 첨두 ≤ P_rated(표본)
          (E33과 같이 시작 유지 + 5주기 뒤부터)
  transient T1 모든 턴오프 ≤ max(5 % × 반주기 첨두, 1.0 A), T2 위상 첨두 ≤ P_rated(표본), T3 V_A 최저·최고가 전부 켬과 1.0 V 안,
            T4 끝 모듈 수·추가·줄임 횟수·취소 0(판정 시작 0.9 ms)
  fault   F1–F4(E30)
  E35 합격 = 요구 안 transient 6사례 × 2표본 모두 통과 + fault 16/16. static은 E33처럼 따로 보고한다(정격 충전점의 시작 과도는
  E28·E33에서도 불통과였던 항목).

■ 실행   python E35_a25r_verify.py static transient beyond fault   (2코어 약 3시간)
■ 결과   results/E35/static.json, transient.json, beyond.json, fault.json
"""
import sys
from multiprocessing import Pool

import E28_stage_a_modules as E28
import E33_stage_a_25k_dynamics as E33
from common import save_json, verdict, workers

EID = "E35"
STEP = E28.STEP
DESIGN = {}                                                     # A25R 관리기 변경(설계 단계에서 정함)
_configure33 = E33.configure


def tier1_cases():
    base = {"MA10_540V_bus_5_15_5kW": dict(V=540., prof=0., bus=STEP(5e3, 15e3, 0.5e-3, 1.5e-3), tend=2.9e-3, n_end=1, add_max=1, rem_max=1),
            "MG10_1008V_bus_25_15_25kW": dict(V=1008., prof=0., bus=STEP(25e3, 15e3, 0.5e-3, 1.5e-3), tend=2.9e-3, n_end=1,
                                              add_max=1, rem_max=1)}
    out = {}
    for k, c in base.items():
        cc = dict(c); cc["bus"] = (E33._sh(c["bus"][0]), list(c["bus"][1])); cc["tend"] = c["tend"] + E33.SHIFT
        out[k] = cc
    return out


IN_REQ = ("MA10_540V_bus_5_15_5kW", "MG10_1008V_bus_25_15_25kW", "MB_800V_bus_ramp_2_36_2kW",
          "MC_800V_charge_slow", "MD_640V_charge_slow", "ME_920V_charge_slow")
BEYOND = ("MA_540V_bus_5_25_5kW", "MG_1008V_bus_25_5_25kW", "MC_800V_charge_prestart", "MD_640V_charge_prestart",
          "ME_920V_charge_prestart", "MF_800V_charge_no_prestart")


def configure():
    M = _configure33()
    E28.MGR = dict(E28.MGR, **DESIGN)
    E28.CASES = dict(E28.CASES, **E33.slow_cases(), **tier1_cases())
    return E28.MGR


E33.configure = configure                                       # E33의 static·transient·fault가 이 설정을 쓰게 한다
E33.EID = EID


def _tr(args):
    name, seed = args
    configure()
    m = E28.case_metrics(name, E28.run_case(name, seed), E28.run_case(name, seed, ref=True), seed)
    m["seed"] = seed
    return m


def _transient(names, label, fname):
    configure()
    jobs = [(n, s) for n in names for s in E33.SEEDS]
    with Pool(workers(), initializer=configure) as p:
        res = p.map(_tr, jobs, chunksize=1)
    E33._report(res, label)
    save_json(EID, fname, dict(cases=res, mgr=E28.MGR, design=DESIGN))
    return res


def static():
    E33.static()


def transient():
    _transient(IN_REQ, "transient 요구 안", "transient")


def beyond():
    _transient(BEYOND, "transient 요구 밖(정보)", "beyond")


def fault():
    E33.fault()


if __name__ == "__main__":
    for part in sys.argv[1:] or ["static", "transient", "beyond", "fault"]:
        print("E35", part, "...")
        globals()[part]()
