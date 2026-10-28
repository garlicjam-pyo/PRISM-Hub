"""[E35] Stage A 25 kHz 설계 수정안(A25R) 판정: E33과 같은 판정 기준으로 정상점·과도·모듈 고장을 다시 확인.

■ 목적
  E33(docs/38)에서 A25는 모듈 고장 처리는 통과했지만 과도 판정을 대부분 통과하지 못했다. 사용자 결정(2026-10-28)에 따라 A25를
  고친 설계(A25R)를 같은 기준으로 다시 판정한다. 무엇을 고칠지는 설계 단계(E35_a25r_design.py, results/E35/design_dev*.json)에서
  정했고, 이 파일의 판정 기준은 실행 전에 커밋한다.

■ A25R = A25 + 아래 변경(설계 단계 결과로 정함)
  V_A 노드 커패시터 C_A 400 µF → 2.4 mF(6배). 설계 단계(design_dev*.json)에서 고른 유일한 변경이다:
    - 충전 요청 중 셰딩 정지(D1), 인터리빙 맞춤 시작(D4), 둘의 조합, 관리기 시간 상수 150 kHz 값(TM1, 하나씩·다섯 모두)은
      느린 충전 3사례를 모두 통과하지 못했다.
    - C_A 6배는 느린 충전 3사례와 Tier-1 계단 2사례를 모두 통과했다. 공진을 6배 느리게 했으므로 V_A 노드의 시간 척도
      (C_A 대비 공진 한 주기의 전하)를 150 kHz 설계와 같게 되돌린 것이다.
  관리기 문턱·시간 상수는 E32(A25)와 같다. 셰딩·모듈 관리 규칙도 같다.

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
  clamp    : C_A가 바뀌므로 E26 충전 중 정지 사건 32개(클램프 있음)를 C_A 2.4 mF로 다시 계산하고 E34 P4·P5 기준으로 본다

■ 판정 기준(E28·E30·E33과 같음, 시험 전에 고정)
  static  S1 |I_m| ≥ 7.5 A 비율 ≤ 5 %, S2 < 7.5 A 턴오프 ≤ 1.0 A, S3 모듈·위상 수 = 규칙, S4 위상 첨두 ≤ P_rated(표본)
          (E33과 같이 시작 유지 + 5주기 뒤부터)
  transient T1 모든 턴오프 ≤ max(5 % × 반주기 첨두, 1.0 A), T2 위상 첨두 ≤ P_rated(표본), T3 V_A 최저·최고가 전부 켬과 1.0 V 안,
            T4 끝 모듈 수·추가·줄임 횟수·취소 0(판정 시작 0.9 ms)
  fault   F1–F4(E30)
  clamp   (E26 C1) V_A·버스 ≤ 470 V, (E34 P4) 사건 에너지 ≤ 15 kJ, (E34 P5) 클램프 전류 ≤ 450 A, V_A ≤ 960 V,
          사건 평균 IGBT 손실 × 0.104 K/W + 65 °C ≤ 150 °C
  E35 합격 = 요구 안 transient 6사례 × 2표본 모두 통과 + fault 16/16. static은 E33처럼 따로 보고한다(정격 충전점의 시작 과도는
  E28·E33에서도 불통과였던 항목).

■ 실행 결과(2026-10-28, 기준은 바꾸지 않았다)
  transient(요구 안): 공칭 6/6, 표본 1 6/6. 느린 충전 턴오프 위반 0(A25: 3–15번), 위상 첨두 ≤ 70.2·76.1 A.
  fault    : 16/16. 3모듈 충전 위상 첨두 최대 105.5 A(A25 119.6 A).
  → E35 합격(요구 안 transient 12/12 + fault 16/16).
  static   : 공칭 33/36(정격 충전점 S4: 시작 유지 뒤 첨두 76.7 A > 74.5 A, 마지막 10주기 74.3 A — E28·E33과 같은 시작 과도),
             표본 1 36/36.
  beyond(정보): 0/6·0/6. 20 kW 순간 계단 MA 첨두 87–88 A·MG 모듈 추가 1번(T4), 100 µs 충전 턴오프 위반 12–22번,
             사전 기동 없는 충전 MF 첨두 217–221 A(A25 169 A — C_A가 커 충전기 전류가 V_A를 늦게 올리므로 모듈 추가가 늦다).
  clamp    : C1·P4 통과, P5 불통과. 클램프 스위칭 5.8–8.7 kHz(A25 29–40 kHz), 사건당 IGBT 18–49 J, 보수 계산 T_vj 145–193 °C,
             전류 468 A > 450 A.

■ 실행   python E35_a25r_verify.py static transient beyond fault clamp   (2코어 약 3시간)
■ 결과   results/E35/static.json, transient.json, beyond.json, fault.json, clamp.json
"""
import sys
from multiprocessing import Pool

import E28_stage_a_modules as E28
import E33_stage_a_25k_dynamics as E33
from common import save_json, verdict, workers

EID = "E35"
STEP = E28.STEP
CA_R = 6 * 400e-6                                               # A25R: C_A 2.4 mF
DESIGN = dict(CA=CA_R)
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
    E28.CA = CA_R
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


def clamp():
    import E26_charging_stop as E26
    import E34_parts_rating as E34
    E26.BUS["CA"] = CA_R
    evs = [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]
    with Pool(workers()) as p:
        rows = p.map(E34._clamp, evs)
    g = E34.ds("FF450R12ME4P")["igbt"]
    for r in rows:
        print("  %-3s %4.0f V %2.0f+%1.0f kW %-4s t_comm %2.0f ms: V_A 최고 %.1f V, 저항 %6.0f J·%5.1f ms, 켬 %5d번(평균 %4.1f kHz), IGBT %.0f J → 평균 %.0f W → T_vj %.0f °C"
              % (r["arch"], r["Vbat"], r["P400"] / 1e3, r["PC"] / 1e3, r["prof"], r["t_comm"] * 1e3, r["vA_max"], r["E_clamp_J"], r["t_clamp_on_ms"],
                 r["n_on"], r["f_avg_kHz"], r["E_igbt_J"], r["P_igbt_avg_W"], r["Tvj_C"]))
    L = dict(C1=max(r["vA_max"] for r in rows) <= 470., P4=max(r["E_clamp_J"] for r in rows) <= 15000.,
             P5=(max(r["i_max"] for r in rows) <= 0.5 * g["I_CRM_A"] and max(r["vA_max"] for r in rows) <= 0.8 * g["V_CES_V"]
                 and max(r["Tvj_C"] for r in rows) <= g["T_vj_op_max_C"]))
    for k, v in L.items():
        verdict("(clamp, C_A %.1f mF) %s" % (CA_R * 1e3, k), v)
    save_json(EID, "clamp", dict(rows=rows, limits=L, CA=CA_R))


if __name__ == "__main__":
    for part in sys.argv[1:] or ["static", "transient", "beyond", "fault"]:
        print("E35", part, "...")
        globals()[part]()
