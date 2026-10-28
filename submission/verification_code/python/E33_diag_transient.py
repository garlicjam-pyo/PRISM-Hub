"""[E33 진단] 실행 뒤 진단(판정을 바꾸지 않음): A25 과도 불통과의 원인 후보를 한 가지씩 바꿔 본다.

E33 transient·slow에서 A25는 E28 사례 대부분이 불통과였다(위상 첨두·턴오프·V_A). A25는 L_r·C_fly를 6배로 해 공진만 6배
느리게 했고, 관리기 시간 상수도 6배로 했다. 그러나 V_A 노드 커패시터 C_A(400 µF)와 버스는 그대로라, 공진 한 주기 동안 V_A가
받는 전하 교란이 상대적으로 6배 크다. 또 관리기가 6배 느리게 반응하므로 모듈 추가 전 노출 시간이 길다.
두 후보를 따로 바꿔 같은 판정 함수(E28.case_metrics)로 다시 계산한다.

  CA6 : C_A = 2.4 mF(6배), 관리기·사례 그대로
  TM1 : 관리기 시간 상수(tau, t_dwell, tau_m, t_lock, t_hold)를 150 kHz 값(E28)으로, C_A 그대로
사례: MA_540V_bus_5_25_5kW(부하 계단), MC_800V_charge_slow(충전 시작·종료, 느린 시각), 공칭.

■ 실행   python E33_diag_transient.py   (2코어 약 20분)
■ 결과   results/E33/diag_transient.json
"""
from multiprocessing import Pool

import E28_stage_a_modules as E28
import E33_stage_a_25k_dynamics as E33
from common import save_json, workers

R1_MGR = dict(E28.MGR)
VARIANTS = ("CA6", "TM1")
CASES = ("MA_540V_bus_5_25_5kW", "MC_800V_charge_slow")


def _run(args):
    var, name = args
    E33.configure()
    E28.CASES = dict(E28.CASES, **E33.slow_cases())
    if var == "CA6":
        E28.CA = 6 * 400e-6
    elif var == "TM1":
        M = dict(E28.MGR)
        for k in ("tau", "t_dwell", "tau_m", "t_lock", "t_hold"):
            M[k] = R1_MGR[k]
        E28.MGR = M
    m = E28.case_metrics(name, E28.run_case(name), E28.run_case(name, ref=True), None)
    m.update(variant=var, CA=E28.CA, mgr=E28.MGR)
    return m


def main():
    jobs = [(v, c) for v in VARIANTS for c in CASES]
    with Pool(workers()) as p:
        rows = p.map(_run, jobs, chunksize=1)
    for x in rows:
        print("  %-4s %-26s %s 턴오프 위반 %d(전부 켬 %d) 최대 %.2f A, 첨두 %.1f A(전부 켬 %.1f, 한도 %.1f), V_A %.2f–%.2f(전부 켬 %.2f–%.2f), 모듈 %s"
              % (x["variant"], x["case"], "통과" if x["passed"] else "불통과 " + str([k for k, v in x["limits"].items() if not v]),
                 x["n_bad"], x["n_bad_ref"], x["ioff_max"], x["phase_peak"], x["phase_peak_ref"], x["P_rated"], x["vA"][0], x["vA"][1],
                 x["vA_ref"][0], x["vA_ref"][1], x["events"]))
    save_json("E33", "diag_transient", dict(rows=rows, note="실행 뒤 진단. E33 판정을 바꾸지 않는다."))


if __name__ == "__main__":
    main()
