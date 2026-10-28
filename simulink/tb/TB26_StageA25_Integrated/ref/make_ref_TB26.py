"""TB26 기준값 생성: Stage A 25 kHz 설계(A25) 4모듈 + 모듈 관리기·셰딩·고장 처리 + R2 버스 + V_A 노드 충전기(검증 코드 E33).

사례(E33과 같은 설정, 공칭 부품값):
  FA25_800V_drive_15kW_m1 : E30 FA(고장 1.1 ms, 모듈 1 → 모듈 2)
  FF25_800V_charge_m1     : E30 FF(충전 375 A 중 모듈 1 고장 → 3모듈)
  MC25_800V_charge        : E28 MC(충전 시작·종료, 고장 없음). E33 slow 결과가 원 시각(사전 기동 100 µs·램프 100 µs) 불통과이고
                            느린 시각(600 µs·600 µs) 통과면 느린 사례를 쓴다(E33의 요구 갱신 규칙과 같음).
각 사례: TB26_<사례>_init.json(회로 파라미터·초기조건·프로파일·게이트 파라미터 23개(회로 간격 2.5 ns)·첨두 한도), _metrics.json
(모델 판정 지표, 사건, 첨두, V_A, 마지막 10주기 Stage A 손실(게이트 제외)), _ref.csv(약 1 µs 평균), gate_parity/<사례>/(모델 간격).
실행: python make_ref_TB26.py <검증 코드 python 폴더>
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import model_stage_a as A                  # noqa: E402
import E24_stage_a_shedding as E24         # noqa: E402
import E28_stage_a_modules as E28          # noqa: E402
import E30_module_fault as E30             # noqa: E402
import E33_stage_a_25k_dynamics as E33     # noqa: E402
from common import load_json               # noqa: E402

DT_C = 2.5e-9                               # 회로 간격


def pad6(tt, yy):
    tt = list(tt); yy = list(yy)
    while len(tt) < 6:
        tt.append(tt[-1]); yy.append(yy[-1])
    return tt, yy


def gate_prm(dt, M, n0, If0, fm, tf):
    """prism_gate_stageA_zcpf.m 파라미터 23개(make_ref_TB24.gate_prm과 같은 규칙, A25 설계 묶음)."""
    td = A.BASE["tdead"]; t_on = 0.5 / A.FR0 * (1 - 2 * td * A.FR0)
    return [dt, A.mround(td / dt), A.mround(0.8 * t_on / dt), A.mround(1.12 * t_on / dt), A.mround(20e-9 / dt), 0.5,
            0, M["I_off"], M["I_on"], M["Ipk_on"], dt / M["tau"], A.mround(M["t_dwell"] / dt),
            M["Im_up"], M["Im_dn"], M["Ipk_m"], A.mround(M["t_dwell_m"] / dt), A.mround(M["t_lock"] / dt), n0, If0,
            A.mround(M["t_hold"] / dt), dt / M["tau_m"], fm, A.mround(tf / dt) if fm else 0]


def loss_ng(r):
    """마지막 10주기 Stage A 손실(도통 + 다이오드 + 출력용량, 게이트 제외) [W]."""
    ph, bus = A.analyze(r, ncyc_last=10)
    return float(sum(p["Ploss"] - 4 * A.BASE["Qg_E"] * p["fs"] for p in ph if p["Ipk"] > 0.5))


def init_state(V, P0, IL0, bus, RA):
    Vo0 = V / 2
    iw = P0 / (Vo0 - 0.0132 * P0 / Vo0)
    for _ in range(5):
        vA = Vo0 - RA * (iw + IL0); vbb = vA - bus["Rw"] * iw; iw = P0 / max(vbb, bus["vmin"])
    return vA, vbb, iw


def main():
    M = E33.configure()
    S = load_json("E33", "slow") if os.path.exists(os.path.join(os.path.dirname(E33.__file__), "..", "results", "E33", "slow.json")) else None
    mc = "MC_800V_charge_prestart"
    if S is not None and (not S["orig_ok"]) and S["slow_ok"]:
        mc = "MC_800V_charge_slow"
        E28.CASES = dict(E28.CASES, **E33.slow_cases())
    cases = [("FA25_800V_drive_15kW_m1", "fault", "FA_800V_drive_15kW_m1"), ("FF25_800V_charge_m1", "fault", "FF_800V_charge_m1"),
             ("MC25_800V_charge", "mgr", mc)]
    T = 1 / A.FR0
    summ = {}
    for name, kind, src in cases:
        if kind == "fault":
            kw, n0 = E30.setup(src)
            r = A.sim_array(**kw)
            m = E30.metrics(src, r, n0)
            c = E30.CASES[src]
            prof = kw["Iload"]; tP, PP = pad6(*kw["bus"]["P"])
            tI, II = pad6(*prof) if isinstance(prof, (tuple, list)) else pad6([0, 1], [float(prof)] * 2)
            chg = list(kw["chg"]) if kw["chg"] else [1.0, 1.0]
            vc0 = [float(v) for v in kw["vC0"]]
            fm, tf = c["fm"] + 1, E30.T_F
            V = c["V"]; t_end = c["tend"]; t0 = E30.T0
            pk_limit = m["pk_limit"]; n_end = E30.expected_end(c); kind_s = c["kind"]
            met = dict(passed=m["passed"], limits=m["limits"], events=m["events"], phase_peak=m["phase_peak"], vA_pre=m["vA_pre"],
                       vA=m["vA"], ioff_max=m["ioff_max"], n_turnoff=m["n_turnoff"], t_rep_us=m["t_rep_us"], n_end=m["n_end"])
        else:
            c = E28.CASES[src]
            r = E28.run_case(src)
            t = r["t"]; w = t > E28.T_JUDGE
            to = E24.turnoffs(r, E28.T_JUDGE)
            na = r["nact"].astype(int); ch = np.where(np.diff(na) != 0)[0]
            ev = [(round(float(t[k + 1]) * 1e3, 4), int(na[k + 1])) for k in ch]
            n0 = int(na[0])
            tP, PP = pad6(*c["bus"]); tI, II = pad6(*c["prof"]); chg = list(c["chg"])
            vc0 = [V2 for V2 in [c["V"] / 2] * 8]
            for mm in range(n0, 4):
                vc0[2 * mm] = vc0[2 * mm + 1] = c["V"] / 2 + E30.DV_IDLE
            fm, tf = 0, 0.
            V = c["V"]; t_end = c["tend"]; t0 = E28.T_JUDGE
            pk_limit = E28.p_rated(None); n_end = c["n_end"]; kind_s = "charge_startstop"
            met = dict(events=ev, phase_peak=float(np.abs(r["i"][w]).max()), vA=[float(r["vb"][w].min()), float(r["vb"][w].max())],
                       ioff_max=max(abs(x[2]) for x in to), n_turnoff=len(to), n_end=int(na[-1]),
                       n_bad=sum(1 for x in to if abs(x[2]) > max(0.05 * x[3], E28.I_ABS)))
            # E28 run_case는 vC0를 주지 않으므로(모든 위상 V/2) 회로도 같게 둔다
            vc0 = [c["V"] / 2] * 8
        met["loss_ng_W"] = loss_ng(r)
        met["model"] = src
        RA = E28.RA1 / max(n0, 1)
        vA0, vb0, iw0 = init_state(V, PP[0], II[0], E28.BUS, RA)
        Thalf = round(0.5 / A.FR0 / DT_C)
        init = dict(case=name, src=src, vbat=V, kind=kind_s, t_end=t_end, t0=t0, tP=tP, PP=PP, tI=tI, II=II, chg=chg, bus=E28.BUS, CA=E28.CA,
                    vA0=vA0, vb0=vb0, iw0=iw0, n0=n0, If0=float(II[0]), vC0=vc0, mgr=M,
                    gate_prm=gate_prm(DT_C, M, n0, float(II[0]), fm, tf), gate_off=[int(round(k * Thalf / 8)) for k in range(8)],
                    fault_module=fm, t_fault=tf, P_rated=E28.p_rated(None), pk_limit=pk_limit, i_abs=E28.I_ABS, dv_A=E30.DV_A,
                    v_b470=E30.V_B470, n_end=n_end,
                    A=dict(Lr=A.BASE["Lr"], Cfly=A.BASE["Cfly"], Rds=A.BASE["Rds"], Vf=A.BASE["Vf"], ESR=A.BASE["ESR"], RL=A.BASE["RL"],
                           Rmisc=A.BASE["Rmisc"], Coss=float(A.qoss_pos(V / 2) / (V / 2)), fr0=A.FR0))
        json.dump(init, open(f"TB26_{name}_init.json", "w"), indent=1, default=float)
        json.dump(met, open(f"TB26_{name}_metrics.json", "w"), indent=1, default=float)
        dec = int(round(1e-6 / r["dt"]))
        io = r["io"].sum(axis=1); nn = (len(r["t"]) // dec) * dec
        avg = lambda x: x[:nn].reshape(-1, dec).mean(axis=1)
        Z = np.column_stack([r["t"][:nn:dec], avg(r["vb"]), avg(r["vbus"]), avg(r["iw"]), avg(io), r["nact"][:nn:dec], avg(r["If"])])
        np.savetxt(f"TB26_{name}_ref.csv", Z, delimiter=",", fmt="%.9g", header="t,vA,vbus,iw,iAout,nact,If", comments="")
        d = os.path.join("gate_parity", name)
        os.makedirs(d, exist_ok=True)
        dt = r["dt"]
        np.savetxt(os.path.join(d, "prm.txt"), np.array(gate_prm(dt, M, n0, float(II[0]), fm, tf))[None, :], fmt="%.12g")
        Nst = A.BASE["Nstep"]
        np.savetxt(os.path.join(d, "off.txt"), A.mround(np.arange(8) * (Nst / 2) / 8).astype(int)[None, :], fmt="%d")
        np.savetxt(os.path.join(d, "seq.csv"), np.column_stack([r["t"], r["ig"], r["st"], r["nact"], r["mm"], r["chg"]]),
                   delimiter=",", fmt="%.9g")
        summ[name] = met
        print(name, "←", src, json.dumps({k: met[k] for k in ("events", "phase_peak", "vA", "ioff_max", "loss_ng_W")}, default=float))
    json.dump(summ, open("TB26_ref_summary.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
