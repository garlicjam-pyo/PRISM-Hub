"""TB22 기준값 생성: Stage A 4모듈(8위상) + 모듈 관리기·위상 셰딩 게이트 + R2 버스(배선·C_b·감쇠기·정전력 부하) + V_A 노드 충전기.

검증 코드 E28(model_stage_a.sim_array mgr·chg, 버스 bus, 데드타임 소멸 처리 dead_fix, 방향 반전 처리 unarmed_stop='nom')의
과도 사례 가운데 MA·MB·MC·MF를 쓴다(공칭 부품값). 게이트는 E28.GATE('mag': 무장 전 부호 없는 영교차 검출). 사례마다 관리기 켬과 전부 켬(8위상, 셰딩 없음) 두 번 계산하고
E28.case_metrics로 판정 지표(T1–T4)를 만든다.
결과: TB22_<사례>_init.json(회로 파라미터·초기조건·프로파일·관리기 파라미터·첨두 기준), _ref.csv(약 1 µs: t, v_A, v_bus, i_w,
      Stage A 출력, 동작 모듈 수, 필터 전류, 전부 켬 v_A·v_bus), _metrics.json, TB22_ref_summary.json,
      gate_parity/(게이트 대조용: 사례 MC의 간격별 위상 전류·구간·동작 모듈 수·모듈 모드·충전 요청, 파라미터)
실행: python make_ref_TB22.py <검증 코드 python 폴더>
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E28_stage_a_modules as E      # noqa: E402
import model_stage_a as A            # noqa: E402

CASES = ["MA_540V_bus_5_25_5kW", "MB_800V_bus_ramp_2_36_2kW", "MC_800V_charge_prestart", "MF_800V_charge_no_prestart"]


def pad6(tt, yy):
    tt = list(tt); yy = list(yy)
    if len(tt) > 6:
        raise ValueError("profile longer than 6 points")
    while len(tt) < 6:
        tt.append(tt[-1]); yy.append(yy[-1])
    return tt, yy


def init_state(V, P0, IL0, bus, RA):
    """model_stage_a.sim_array(bus=...)와 같은 초기 평형 계산."""
    Vo0 = V / 2
    iw = P0 / (Vo0 - 0.0132 * P0 / Vo0)
    for _ in range(5):
        vA = Vo0 - RA * (iw + IL0); vbb = vA - bus["Rw"] * iw; iw = P0 / max(vbb, bus["vmin"])
    return vA, vbb, iw


def gate_prm(dt, M, n0, If0):
    td = A.BASE["tdead"]; t_on = 0.5 / A.FR0 * (1 - 2 * td * A.FR0)
    n_nom = A.mround(t_on / dt) if E.GATE == "nom" else 0          # 0 = 무장 전 부호 없는 검출(E28 'mag')
    return [dt, A.mround(td / dt), A.mround(0.8 * t_on / dt), A.mround(1.12 * t_on / dt), A.mround(20e-9 / dt), 0.5,
            n_nom, M["I_off"], M["I_on"], M["Ipk_on"], dt / M["tau"], A.mround(M["t_dwell"] / dt),
            M["Im_up"], M["Im_dn"], M["Ipk_m"], A.mround(M["t_dwell_m"] / dt), A.mround(M["t_lock"] / dt), n0, If0,
            A.mround(M["t_hold"] / dt), dt / M["tau_m"]]


out = {}
for name in CASES:
    c = E.CASES[name]
    r = E.run_case(name); b = E.run_case(name, ref=True)
    m = E.case_metrics(name, r, b)
    if isinstance(c["prof"], (tuple, list)):
        tI, II = pad6(*c["prof"])
    else:
        tI, II = pad6([0, 1], [float(c["prof"])] * 2)
    tP, PP = pad6(*c["bus"])
    n0 = int(r["nact"][0])
    vA0, vb0, iw0 = init_state(c["V"], PP[0], II[0], E.BUS, E.RA1 / n0)
    vA0r, vb0r, iw0r = init_state(c["V"], PP[0], II[0], E.BUS, E.RA1 / 4)
    chg = list(c.get("chg", (1.0, 1.0)))                       # 충전 요청이 없으면 빈 구간
    init = dict(case=name, vbat=c["V"], t_end=c["tend"], tP=tP, PP=PP, tI=tI, II=II, chg=chg, bus=E.BUS, CA=E.CA,
                vA0=vA0, vb0=vb0, iw0=iw0, vA0_ref=vA0r, vb0_ref=vb0r, iw0_ref=iw0r, n0=n0, If0=float(II[0]),
                mgr=E.MGR, P_rated=E.p_rated(None), i_abs=E.I_ABS, t0=0.3e-3, n_end=c["n_end"], add_max=c["add_max"],
                rem_max=c["rem_max"], dv_tol=1.0)
    json.dump(init, open(f"TB22_{name}_init.json", "w"), indent=1)
    dec = int(round(1e-6 / r["dt"]))
    io = r["io"].sum(axis=1)
    nn = (len(r["t"]) // dec) * dec
    avg = lambda x: x[:nn].reshape(-1, dec).mean(axis=1)
    Z = np.column_stack([r["t"][:nn:dec], avg(r["vb"]), avg(r["vbus"]), avg(r["iw"]), avg(io), r["nact"][:nn:dec], avg(r["If"]),
                         avg(b["vb"]), avg(b["vbus"])])
    np.savetxt(f"TB22_{name}_ref.csv", Z, delimiter=",", fmt="%.9g",
               header="t,vA,vbus,iw,iAout,nact,If,vA_allon,vbus_allon", comments="")
    json.dump(m, open(f"TB22_{name}_metrics.json", "w"), indent=1, default=float)
    out[name] = m
    print(name, "PASS" if m["passed"] else "FAIL", m["events"], "pk %.1f (all-on %.1f), vA %.2f-%.2f (all-on %.2f-%.2f)" % (
        m["phase_peak"], m["phase_peak_ref"], m["vA"][0], m["vA"][1], m["vA_ref"][0], m["vA_ref"][1]))
    if name == "MC_800V_charge_prestart":     # 게이트 대조(Octave): 같은 전류·충전 요청을 넣으면 같은 구간·모듈 상태가 나와야 한다
        os.makedirs("gate_parity", exist_ok=True)
        dt = r["dt"]
        np.savetxt("gate_parity/prm.txt", np.array(gate_prm(dt, E.MGR, n0, float(II[0])))[None, :], fmt="%.12g")
        np.savetxt("gate_parity/off.txt", A.mround(np.arange(8) * (340 / 2) / 8).astype(int)[None, :], fmt="%d")
        np.savetxt("gate_parity/seq.csv", np.column_stack([r["t"], r["ig"], r["st"], r["nact"], r["mm"], r["chg"]]),
                   delimiter=",", fmt="%.9g")
json.dump(out, open("TB22_ref_summary.json", "w"), indent=1, default=float)
