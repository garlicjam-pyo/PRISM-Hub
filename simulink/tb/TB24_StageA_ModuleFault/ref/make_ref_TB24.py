"""TB24 기준값 생성: Stage A 4모듈(8위상) + 모듈 관리기·위상 셰딩 게이트 + 모듈 고장 처리 + R2 버스 + V_A 노드 충전기.

검증 코드 E30(model_stage_a.sim_array mgr·chg·fault, 버스 bus, 데드타임 소멸 처리 dead_fix, 게이트 E28.GATE = 'mag')의
고장 사례 가운데 FA·FB·FF·FH를 쓴다(공칭 부품값). 판정 지표는 E30.metrics(F1–F4)로 만든다.
결과: TB24_<사례>_init.json(회로 파라미터·초기조건·프로파일·관리기 파라미터·고장·첨두 기준), _ref.csv(약 1 µs: t, v_A, v_bus, i_w,
      Stage A 출력, 동작 모듈 수, 필터 전류), _metrics.json, TB24_ref_summary.json,
      gate_parity/<사례>/(게이트 대조용: 간격별 게이트 입력 전류·구간·동작 모듈 수·모듈 모드·충전 요청, 파라미터 23개, 시작 지연)
실행: python make_ref_TB24.py <검증 코드 python 폴더>
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E30_module_fault as E30        # noqa: E402
import E28_stage_a_modules as E28     # noqa: E402
import model_stage_a as A             # noqa: E402

CASES = ["FA_800V_drive_15kW_m1", "FB_540V_drive_25kW_m1", "FF_800V_charge_m1", "FH_800V_charge_m4"]
PARITY = ["FA_800V_drive_15kW_m1", "FF_800V_charge_m1"]


def pad6(tt, yy):
    tt = list(tt); yy = list(yy)
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


def gate_prm(dt, M, n0, If0, fm, tf):
    """회로 게이트 prism_gate_stageA_zcpf.m의 파라미터 23개(TB22 zcpm 21개 + 고장 모듈(1–4) + 고장 간격 번호)."""
    td = A.BASE["tdead"]; t_on = 0.5 / A.FR0 * (1 - 2 * td * A.FR0)
    return [dt, A.mround(td / dt), A.mround(0.8 * t_on / dt), A.mround(1.12 * t_on / dt), A.mround(20e-9 / dt), 0.5,
            0, M["I_off"], M["I_on"], M["Ipk_on"], dt / M["tau"], A.mround(M["t_dwell"] / dt),
            M["Im_up"], M["Im_dn"], M["Ipk_m"], A.mround(M["t_dwell_m"] / dt), A.mround(M["t_lock"] / dt), n0, If0,
            A.mround(M["t_hold"] / dt), dt / M["tau_m"], fm + 1, A.mround(tf / dt)]


out = {}
for name in CASES:
    c = E30.CASES[name]
    kw, n0 = E30.setup(name)
    r = A.sim_array(**kw)
    m = E30.metrics(name, r, n0)
    prof = kw["Iload"]
    tI, II = pad6(*prof) if isinstance(prof, (tuple, list)) else pad6([0, 1], [float(prof)] * 2)
    tP, PP = pad6(*kw["bus"]["P"])
    vA0, vb0, iw0 = init_state(c["V"], PP[0], II[0], E28.BUS, E28.RA1 / n0)
    chg = list(kw["chg"]) if kw["chg"] else [1.0, 1.0]           # 충전 요청이 없으면 빈 구간
    init = dict(case=name, vbat=c["V"], kind=c["kind"], t_end=c["tend"], tP=tP, PP=PP, tI=tI, II=II, chg=chg, bus=E28.BUS, CA=E28.CA,
                vA0=vA0, vb0=vb0, iw0=iw0, n0=n0, If0=float(II[0]), vC0=[float(v) for v in kw["vC0"]], mgr=E28.MGR,
                fault_module=c["fm"] + 1, t_fault=E30.T_F, P_rated=E28.p_rated(None), pk_limit=m["pk_limit"], i_abs=E28.I_ABS,
                t0=E30.T0, dv_A=E30.DV_A, v_b470=E30.V_B470, n_end=E30.expected_end(c))
    json.dump(init, open(f"TB24_{name}_init.json", "w"), indent=1)
    dec = int(round(1e-6 / r["dt"]))
    io = r["io"].sum(axis=1)
    nn = (len(r["t"]) // dec) * dec
    avg = lambda x: x[:nn].reshape(-1, dec).mean(axis=1)
    Z = np.column_stack([r["t"][:nn:dec], avg(r["vb"]), avg(r["vbus"]), avg(r["iw"]), avg(io), r["nact"][:nn:dec], avg(r["If"])])
    np.savetxt(f"TB24_{name}_ref.csv", Z, delimiter=",", fmt="%.9g", header="t,vA,vbus,iw,iAout,nact,If", comments="")
    json.dump(m, open(f"TB24_{name}_metrics.json", "w"), indent=1, default=float)
    out[name] = m
    print(name, "PASS" if m["passed"] else "FAIL", m["limits"], m["events"], "pk %.1f (lim %.1f), vA %.2f -> %.2f-%.2f, t_rep %s us"
          % (m["phase_peak"], m["pk_limit"], m["vA_pre"], m["vA"][0], m["vA"][1], m["t_rep_us"]))
    if name in PARITY:              # 게이트 대조(MATLAB): 같은 전류·충전 요청을 넣으면 같은 구간·모듈 상태가 나와야 한다
        d = os.path.join("gate_parity", name)
        os.makedirs(d, exist_ok=True)
        dt = r["dt"]
        np.savetxt(os.path.join(d, "prm.txt"), np.array(gate_prm(dt, E28.MGR, n0, float(II[0]), c["fm"], E30.T_F))[None, :], fmt="%.12g")
        np.savetxt(os.path.join(d, "off.txt"), A.mround(np.arange(8) * (340 / 2) / 8).astype(int)[None, :], fmt="%d")
        np.savetxt(os.path.join(d, "seq.csv"), np.column_stack([r["t"], r["ig"], r["st"], r["nact"], r["mm"], r["chg"]]),
                   delimiter=",", fmt="%.9g")
json.dump(out, open("TB24_ref_summary.json", "w"), indent=1, default=float)
