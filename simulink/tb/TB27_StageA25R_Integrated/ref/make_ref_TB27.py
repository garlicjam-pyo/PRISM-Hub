"""TB27 기준값 생성: Stage A 25 kHz 설계 수정안 A25R(A25 + C_A 2.4 mF) 4모듈 + 모듈 관리기·셰딩·고장 처리 + R2 버스 + V_A 노드 충전기
(검증 코드 E35_a25r_verify.configure).

사례(E35와 같은 설정, 공칭 부품값):
  FF27_800V_charge_m1      : E30 FF(충전 375 A + 버스 15 kW 중 모듈 1 고장 → 3모듈)
  MC27_800V_charge_slow    : E33 slow MC(충전 시작·종료, 사전 기동 600 µs·충전전류 램프 600 µs)
  MA27_540V_bus_5_15_5kW   : E35 Tier-1 계단(540 V, 버스 5 → 15 → 5 kW, docs/14 D3)
  SC27_800V_charge_steady  : 정격 충전 정상상태(800 V, V_A 노드 −375 A + 버스 15 kW, 처음부터 충전 요청, 4 ms) — 손실 대조용
각 사례: TB27_<사례>_init.json(회로 파라미터·초기조건·프로파일·게이트 파라미터 23개(회로 간격 2.5 ns)·첨두 한도·판정 창),
_metrics.json(모델 판정 지표, 사건, 첨두, V_A, 손실), _ref.csv(약 1 µs 평균), gate_parity/<사례>/(모델 간격).
손실(SC27): 마지막 20주기(모델 analyze, 도통 + 다이오드 + 출력용량, 게이트 제외).
실행: python make_ref_TB27.py <검증 코드 python 폴더>
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
import E35_a25r_verify as E35              # noqa: E402

DT_C = 2.5e-9
N_LOSS = 20                                 # 손실 창 주기 수(SC27)


def pad6(tt, yy):
    tt = list(tt); yy = list(yy)
    while len(tt) < 6:
        tt.append(tt[-1]); yy.append(yy[-1])
    return tt, yy


def gate_prm(dt, M, n0, If0, fm, tf):
    td = A.BASE["tdead"]; t_on = 0.5 / A.FR0 * (1 - 2 * td * A.FR0)
    return [dt, A.mround(td / dt), A.mround(0.8 * t_on / dt), A.mround(1.12 * t_on / dt), A.mround(20e-9 / dt), 0.5,
            0, M["I_off"], M["I_on"], M["Ipk_on"], dt / M["tau"], A.mround(M["t_dwell"] / dt),
            M["Im_up"], M["Im_dn"], M["Ipk_m"], A.mround(M["t_dwell_m"] / dt), A.mround(M["t_lock"] / dt), n0, If0,
            A.mround(M["t_hold"] / dt), dt / M["tau_m"], fm, A.mround(tf / dt) if fm else 0]


def loss_ng(r, ncyc):
    ph, bus = A.analyze(r, ncyc_last=ncyc)
    return float(sum(p["Ploss"] - 4 * A.BASE["Qg_E"] * p["fs"] for p in ph if p["Ipk"] > 0.5))


def init_state(V, P0, IL0, bus, RA):
    Vo0 = V / 2
    iw = P0 / (Vo0 - 0.0132 * P0 / Vo0)
    for _ in range(5):
        vA = Vo0 - RA * (iw + IL0); vbb = vA - bus["Rw"] * iw; iw = P0 / max(vbb, bus["vmin"])
    return vA, vbb, iw


def steady_case():
    return {"SC_800V_charge_steady": dict(V=800., prof=([0, 1], [-375., -375.]), bus=([0, 1], [15e3, 15e3]), chg=(0., 1.0),
                                          tend=4.0e-3, n_end=4, add_max=0, rem_max=0)}


def main():
    M = E35.configure()
    E28.CASES = dict(E28.CASES, **steady_case())
    cases = [("FF27_800V_charge_m1", "fault", "FF_800V_charge_m1"), ("MC27_800V_charge_slow", "mgr", "MC_800V_charge_slow"),
             ("MA27_540V_bus_5_15_5kW", "mgr", "MA10_540V_bus_5_15_5kW"), ("SC27_800V_charge_steady", "steady", "SC_800V_charge_steady")]
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
            T = 1 / A.FR0
            t0 = (c["tend"] - 1.0e-3) if kind == "steady" else E28.T_JUDGE
            t = r["t"]; w = t > t0
            to = E24.turnoffs(r, t0)
            na = r["nact"].astype(int); ch = np.where(np.diff(na) != 0)[0]
            ev = [(round(float(t[k + 1]) * 1e3, 4), int(na[k + 1])) for k in ch]
            n0 = int(na[0])
            tP, PP = pad6(*c["bus"]); chg = list(c["chg"]) if c.get("chg") else [1.0, 1.0]
            tI, II = pad6(*c["prof"]) if not np.isscalar(c["prof"]) else pad6([0, 1], [float(c["prof"])] * 2)
            fm, tf = 0, 0.
            V = c["V"]; t_end = c["tend"]
            pk_limit = E28.p_rated(None); n_end = c["n_end"]; kind_s = "charge_steady" if kind == "steady" else \
                ("charge_startstop" if c.get("chg") else "bus_step")
            met = dict(events=ev, phase_peak=float(np.abs(r["i"][w]).max()), vA=[float(r["vb"][w].min()), float(r["vb"][w].max())],
                       ioff_max=max(abs(x[2]) for x in to), n_turnoff=len(to), n_end=int(na[-1]),
                       n_bad=sum(1 for x in to if abs(x[2]) > max(0.05 * x[3], E28.I_ABS)))
            vc0 = [c["V"] / 2] * 8
        met["loss_ng_W"] = loss_ng(r, N_LOSS if kind == "steady" else 10)
        met["loss_ncyc"] = N_LOSS if kind == "steady" else 10
        met["model"] = src
        RA = E28.RA1 / max(n0, 1)
        vA0, vb0, iw0 = init_state(V, PP[0], II[0], E28.BUS, RA)
        Thalf = round(0.5 / A.FR0 / DT_C)
        init = dict(case=name, src=src, vbat=V, kind=kind_s, t_end=t_end, t0=t0, tP=tP, PP=PP, tI=tI, II=II, chg=chg, bus=E28.BUS, CA=E28.CA,
                    vA0=vA0, vb0=vb0, iw0=iw0, n0=n0, If0=float(II[0]), vC0=vc0, mgr=M, loss_case=kind == "steady", n_loss=N_LOSS,
                    gate_prm=gate_prm(DT_C, M, n0, float(II[0]), fm, tf), gate_off=[int(round(k * Thalf / 8)) for k in range(8)],
                    fault_module=fm, t_fault=tf, P_rated=E28.p_rated(None), pk_limit=pk_limit, i_abs=E28.I_ABS, dv_A=E30.DV_A,
                    v_b470=E30.V_B470, n_end=n_end,
                    A=dict(Lr=A.BASE["Lr"], Cfly=A.BASE["Cfly"], Rds=A.BASE["Rds"], Vf=A.BASE["Vf"], ESR=A.BASE["ESR"], RL=A.BASE["RL"],
                           Rmisc=A.BASE["Rmisc"], Coss=float(A.qoss_pos(V / 2) / (V / 2)), fr0=A.FR0))
        json.dump(init, open(f"TB27_{name}_init.json", "w"), indent=1, default=float)
        json.dump(met, open(f"TB27_{name}_metrics.json", "w"), indent=1, default=float)
        dec = int(round(1e-6 / r["dt"]))
        io = r["io"].sum(axis=1); nn = (len(r["t"]) // dec) * dec
        avg = lambda x: x[:nn].reshape(-1, dec).mean(axis=1)
        Z = np.column_stack([r["t"][:nn:dec], avg(r["vb"]), avg(r["vbus"]), avg(r["iw"]), avg(io), r["nact"][:nn:dec], avg(r["If"])])
        np.savetxt(f"TB27_{name}_ref.csv", Z, delimiter=",", fmt="%.9g", header="t,vA,vbus,iw,iAout,nact,If", comments="")
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
    json.dump(summ, open("TB27_ref_summary.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
