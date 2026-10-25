"""TB18 기준값 생성: Stage A 모듈 1 + 경부하 위상 셰딩 게이트 + R2 버스(배선·C_b·감쇠기·정전력 부하) + V_A 노드 충전기 전류.

검증 코드 E24(model_stage_a.sim_array, 셰딩 shed_step, 버스 bus, 데드타임 소멸 처리 dead_fix)의 과도 사례 F–J를 쓴다.
사례마다 셰딩 켬·없음 두 번 계산하고, E24.case_metrics로 판정 지표(T1–T4)를 만든다.
결과: TB18_<사례>_init.json(회로 파라미터·초기조건·프로파일·셰딩 파라미터), _ref.csv(약 1 µs: t, v_A, v_bus, i_w, 모듈 출력,
      셰딩 모드, 필터 전류, 셰딩 없음 v_A·v_bus), _metrics.json, TB18_ref_summary.json,
      gate_parity/(게이트 대조용: 사례 F의 간격별 위상 전류·구간·모드, 파라미터)
실행: python make_ref_TB18.py <검증 코드 python 폴더>
"""
import json
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E24_stage_a_shedding as E      # noqa: E402
import model_stage_a as A             # noqa: E402

CASES = ["F_1008V_bus_25_5_25kW", "G_540V_bus_13p5_2p7_13p5kW", "H_1008V_bus5kW_charger_74A",
         "I_1008V_bus_ramp_20_1p5_20kW", "J_1008V_bus5kW_rev_m16A"]


def pad6(tt, yy):
    tt = list(tt); yy = list(yy)
    if len(tt) > 6:
        raise ValueError("profile longer than 6 points")
    while len(tt) < 6:
        tt.append(tt[-1]); yy.append(yy[-1])
    return tt, yy


def init_state(V, P0, IL0, bus):
    """model_stage_a.sim_array(bus=...)와 같은 초기 평형 계산."""
    Vo0 = V / 2
    iw = P0 / (Vo0 - 0.0132 * P0 / Vo0)
    for _ in range(5):
        vA = Vo0 - 10.2e-3 * (iw + IL0); vbb = vA - bus["Rw"] * iw; iw = P0 / max(vbb, bus["vmin"])
    return vA, vbb, iw


out = {}
for name in CASES:
    c = E.CASES[name]
    r = E.run_case(name, True); b = E.run_case(name, False)
    m = E.case_metrics(name, r, b)
    if isinstance(c["prof"], (tuple, list)):
        tI, II = pad6(*c["prof"])
    else:
        tI, II = pad6([0, 1], [float(c["prof"])] * 2)
    tP, PP = pad6(*c["bus"])
    vA0, vb0, iw0 = init_state(c["V"], PP[0], II[0], E.BUS)
    init = dict(case=name, vbat=c["V"], t_end=c["tend"], tP=tP, PP=PP, tI=tI, II=II, bus=E.BUS, vA0=vA0, vb0=vb0, iw0=iw0,
                CA=E.CA, shed=E.SHED, rated_pk=E.RATED_PK, i_abs=E.I_ABS, n_shed=c["n_shed"], n_ret=c["n_ret"], t0=0.3e-3)
    json.dump(init, open(f"TB18_{name}_init.json", "w"), indent=1)
    dec = int(round(1e-6 / r["dt"]))
    io = r["io"].sum(axis=1)
    nn = (len(r["t"]) // dec) * dec
    avg = lambda x: x[:nn].reshape(-1, dec).mean(axis=1)
    Z = np.column_stack([r["t"][:nn:dec], avg(r["vb"]), avg(r["vbus"]), avg(r["iw"]), avg(io), r["sm"][:nn:dec], avg(r["If"]),
                         avg(b["vb"]), avg(b["vbus"])])
    np.savetxt(f"TB18_{name}_ref.csv", Z, delimiter=",", fmt="%.9g",
               header="t,vA,vbus,iw,iAout,smode,If,vA_noshed,vbus_noshed", comments="")
    json.dump(m, open(f"TB18_{name}_metrics.json", "w"), indent=1, default=float)
    out[name] = m
    print(name, "PASS" if m["passed"] else "FAIL", m["events"], "pk %.1f (noshed %.1f), vA %.2f-%.2f" % (
        m["phase_peak"], m["phase_peak_noshed"], m["vA"][0], m["vA"][1]))
    if name == CASES[0]:                      # 게이트 대조(Octave): 같은 전류를 넣으면 같은 구간·모드가 나와야 한다
        import os
        os.makedirs("gate_parity", exist_ok=True)
        dt = r["dt"]; td = A.BASE["tdead"]; t_on = 0.5 / A.FR0 * (1 - 2 * td * A.FR0)
        prm = [dt, A.mround(td / dt), A.mround(0.8 * t_on / dt), A.mround(1.12 * t_on / dt), A.mround(20e-9 / dt), 0.5,
               E.SHED["I_off"], E.SHED["I_on"], E.SHED["Ipk_on"], dt / E.SHED["tau"], A.mround(E.SHED["t_dwell"] / dt), 1, 2]
        np.savetxt("gate_parity/prm.txt", np.array(prm)[None, :], fmt="%.12g")
        np.savetxt("gate_parity/off.txt", np.array([0, A.mround(340 / 4)] + [0] * 6)[None, :], fmt="%d")
        np.savetxt("gate_parity/seq.csv", np.column_stack([r["t"], r["ig"][:, 0], r["ig"][:, 1], r["st"][:, 0], r["st"][:, 1], r["sm"]]),
                   delimiter=",", fmt="%.9g")
json.dump(out, open("TB18_ref_summary.json", "w"), indent=1, default=float)
