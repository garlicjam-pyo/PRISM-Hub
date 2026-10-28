"""TB29 기준값 생성: V_A 클램프 설계 변경(E37 Q2: R_clamp 1.0 → 1.2 Ω, 켬 468·끔 463 V 그대로)을 TB28 회로(A25R)로 확인.

검증 코드를 쓴다(TB28과 같고 클램프 저항만 1.2 Ω).
  E26 run_event : V_A 노드 평균모델(R_A 9.0 mΩ, C_A 2.4 mF, 클램프 468/463 V·1.2 Ω·1 µs)
  E22 run_avg   : 조정형 Stage C 평균모델(E26 버스 궤적)
  model_stage_a : A25R 4모듈 스위칭 모델(사건 전 Stage A 기준)
사례(시험 전에 고정)
  A29_920V_pathloss  920 V, 충전 375 A, 400 V 부하 20 kW + Stage C 5 kW. 1.5 ms 배터리 경로 상실, 충전기 3 ms 유지 뒤 0(TB28 A와 같음)
  B29_640V_pathloss  640 V, 같은 부하, 충전기 3 ms 유지 뒤 0(E37 Q2에서 IGBT 온도가 가장 높았던 사건과 같은 팩·부하·유지 프로파일)
결과: TB29_<사례>_init.json, _ref.csv, _stageC.csv, _metrics.json(클램프 켬 횟수·켜진 시간 포함), _stageA.json, TB29_ref_summary.json
실행: python make_ref_TB29.py <검증 코드 python 폴더>
"""
import json
import math
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E22_stage_c_regulated as E          # noqa: E402
import E23_r2_integrated as R              # noqa: E402
import E24_stage_a_shedding as E24         # noqa: E402
import E26_charging_stop as C26            # noqa: E402
import E28_stage_a_modules as E28          # noqa: E402
import E35_a25r_verify as E35              # noqa: E402
import model_stage_a as A                  # noqa: E402
from E15_baseline_loss_rating import DEV, K   # noqa: E402

DT_C = 2.5e-9
RA_A25 = 9.0e-3                             # A25 모듈 출력저항(E32 design, E36과 같음)
T_EV = 1.5e-3
T_STOP_TB = 3e-3
Q400 = 20e3; PC = 5e3; I0 = 375.
CASES = {
    "A29_920V_pathloss": dict(vbat=920., Q=Q400, tI=[0, T_EV, T_EV + T_STOP_TB, T_EV + T_STOP_TB + 1e-9, 1., 2.],
                              II=[I0, I0, I0, 0., 0., 0.], mask=[0] * 8, fm=0, chg=[0., 1.], nmod_after=0, t_ev=T_EV,
                              t_end=T_EV + T_STOP_TB + 1e-3, kind="pathloss"),
    "B29_640V_pathloss": dict(vbat=640., Q=Q400, tI=[0, T_EV, T_EV + T_STOP_TB, T_EV + T_STOP_TB + 1e-9, 1., 2.],
                              II=[I0, I0, I0, 0., 0., 0.], mask=[0] * 8, fm=0, chg=[0., 1.], nmod_after=0, t_ev=T_EV,
                              t_end=T_EV + T_STOP_TB + 1e-3, kind="pathloss"),
}
R_CLAMP = 1.2                               # E37 Q2 선택(켬 468·끔 463 V 그대로)
W_HOLD = (2.6e-3, 2.9e-3)                   # D28 충전 유지 중 판정 창(램프 끝 2.2 ms + 10주기 뒤)


def gate_prm(dt, M, n0, If0, fm, tf):
    """prism_gate_stageA_zcpf.m 파라미터 23개(make_ref_TB27.py와 같음)."""
    td = A.BASE["tdead"]; t_on = 0.5 / A.FR0 * (1 - 2 * td * A.FR0)
    return [dt, A.mround(td / dt), A.mround(0.8 * t_on / dt), A.mround(1.12 * t_on / dt), A.mround(20e-9 / dt), 0.5,
            0, M["I_off"], M["I_on"], M["Ipk_on"], dt / M["tau"], A.mround(M["t_dwell"] / dt),
            M["Im_up"], M["Im_dn"], M["Ipk_m"], A.mround(M["t_dwell_m"] / dt), A.mround(M["t_lock"] / dt), n0, If0,
            A.mround(M["t_hold"] / dt), dt / M["tau_m"], fm, A.mround(tf / dt) if fm else 0]


def window(r, t1, t2, phases):
    """창 안 위상별 턴오프 전류/피크 최대, 첨두, 평균 출력전류(회로 run_TB29.zcs_window와 같은 정의)."""
    t = r["t"]; w = (t > t1) & (t <= t2)
    zz, pk, io = [], [], []
    for k in phases:
        i = r["i"][w, k].astype(float); s = r["st"][w, k].astype(int)
        off = np.where((s[:-1] > 0) & (s[1:] == 0))[0]
        p = float(np.abs(i).max()); pk.append(p)
        zz.append(float(np.abs(i[off]).max() / max(p, 1e-6)) if len(off) else 0.)
        io.append(float(np.mean(i * (s == 1) - i * (s == 2))))
    io_m = np.mean(io)
    return dict(zcs=zz, Ipk=pk, io=io, sharing=float(np.max(np.abs(np.array(io) - io_m)) / abs(io_m)) if io_m else None,
                vA_mean=float(r["vb"][w].mean()))


def model_run(cs, p_in, M):
    V = cs["vbat"]; P_bus = cs["Q"] + p_in
    tI = list(cs["tI"]); II = [-x for x in cs["II"]]           # V_A 노드 직접 전류(충전기 주입은 음수)
    tend = cs["t_ev"] if cs["kind"] == "pathloss" else cs["t_end"]
    chg = tuple(cs["chg"])
    n0 = 4 if chg[0] <= 0. else max(1, min(4, int(math.ceil(abs(II[0]) / M["Im_up"]))))
    bus = dict(E28.BUS, RA=E28.RA1 / n0, P=([0, 1], [P_bus, P_bus]))
    fault = [(cs["t_ev"], cs["fm"] - 1)] if cs["fm"] else None
    r = A.sim_array(N=8, Vbat=V, Iload=(tI, II), Cbus=E28.CA, mode="zcp", ncyc=int(round(tend / E28.T)), vC0=np.full(8, V / 2),
                    bus=bus, dead_fix=E28.DF, unarmed_stop=E28.GATE, mgr=dict(M, n0=n0), chg=chg, fault=fault)
    return r, n0, II[0]


def main():
    M = E35.configure()                                        # A25 설계, E32 문턱, E28.CA = 2.4 mF
    C26.BUS["CA"] = E28.CA; C26.RA_MOD = RA_A25
    C26.CL = dict(C26.CL, R=R_CLAMP)
    c, eq, g = R.design()
    n = c["n"]
    RL = K["mag_ind_cu"] * E.PO_MAX / (E.PO_MAX * 1.03 / (n * E.VO_NOM)) ** 2
    Ip_r = np.sqrt((np.pi * (E.PO_MAX / E.VO_NOM) / (2 * n)) ** 2 / 2 + c["im_pk"] ** 2 / 3)
    Rw = K["mag_tr_cu"] * E.PO_MAX / Ip_r ** 2
    p48 = R.p48_for_input(c, eq, PC)
    P_rated = E28.p_rated(None)
    out = {}
    for name, cs in CASES.items():
        # ---- E26 V_A 노드 평균모델 + 클램프 ------------------------------------------------------------------------
        t0 = cs["t_ev"] if cs["nmod_after"] != 4 else 10.
        ev = C26.run_event(cs["vbat"], cs["Q"], PC, arch="R2", clamp=True, nmod_after=cs["nmod_after"], tend=cs["t_end"],
                           t0=t0, ich_pwl=(cs["tI"], cs["II"]), rec_every=4, full_trace=True)
        tr = np.array(ev["trace"])                         # 1 µs: t vA vb ich iA icl
        w = 5; nn = (tr.shape[0] // w) * w
        tV = np.concatenate(([0.], tr[:nn, 0].reshape(-1, w)[:, -1]))
        VV = np.concatenate(([tr[0, 2]], tr[:nn, 2].reshape(-1, w).mean(axis=1)))
        Z = E.run_avg(c, eq, g, [0., 1.], [p48, p48], tV, VV, T_end=cs["t_end"], dec=20, start_eq=True)
        zz = Z[Z[:, 0] >= 1.0e-3]
        vo_min, vo_max = float(zz[:, 5].min()), float(zz[:, 5].max())
        vA0 = float(tr[0, 1]); vb0 = float(tr[0, 2])
        E_cl = float(np.sum(tr[:, 1] * tr[:, 5]) * 1e-6)
        on = tr[:, 5] > 0
        n_on = int(np.sum(~on[:-1] & on[1:]))
        m = dict(vA_max=ev["vA_max"], vb_max=ev["vb_max"], vA0=vA0, vb0=vb0, E_clamp_J=ev["E_clamp_J"], E_clamp_1us_J=E_cl,
                 t_clamp_on_ms=ev["t_clamp_on_ms"], P_clamp_pk_W=ev["P_clamp_pk_W"], n_on=n_on, R_clamp=R_CLAMP, t_hit_ms=ev["t_hit_ms"], vo_min=vo_min,
                 vo_max=vo_max, vo_end=float(Z[-1, 5]), p48=p48, ok_C1=ev["ok_C1"])
        # ---- A25R Stage A 스위칭 모델 ----------------------------------------------------------------------------
        p_in = PC                                         # Stage C 입력(정전력 등가)
        r, n0, If0 = model_run(cs, p_in, M)
        te = cs["t_ev"]
        sa = dict(pre=window(r, te - 0.2e-3, te - 2e-6, range(8) if cs["kind"] != "charge_slow" else range(2)), n0=n0)
        to = E24.turnoffs(r, 1.0e-3)
        sa["turnoffs"] = dict(n=len(to), bad=sum(1 for x in to if abs(x[2]) > max(0.05 * x[3], E28.I_ABS)),
                              worst=max(abs(x[2]) for x in to) if to else 0.)
        if cs["kind"] == "fault":
            fm = cs["fm"]; keep = [k for k in range(8) if k // 2 != fm - 1]
            sa["final"] = window(r, te + 0.5e-3, cs["t_end"], keep)
        if cs["kind"] == "charge_slow":
            sa["mid"] = window(r, W_HOLD[0], W_HOLD[1], range(8))
            t = r["t"]; ww = t >= 1.0e-3
            sa["phase_peak"] = float(np.abs(r["i"][ww]).max())
        na = r["nact"].astype(int); ch = np.where(np.diff(na) != 0)[0]
        sa["events"] = [(round(float(r["t"][k + 1]) * 1e3, 4), int(na[k + 1])) for k in ch]
        sa["n_end"] = int(na[-1]); sa["n_mcancel"] = int(r["n_mcancel"])
        il0 = (cs["Q"] + PC) / vb0
        Thalf = round(0.5 / A.FR0 / DT_C)
        init = dict(case=name, kind=cs["kind"], vbat=cs["vbat"], t_end=cs["t_end"], t_ev=te, t_stop=T_STOP_TB, tI=cs["tI"],
                    II=cs["II"], mask=cs["mask"], chg=cs["chg"], Q=cs["Q"], P=p48, PC=PC,
                    clamp=dict(von=C26.CL["on"], voff=C26.CL["off"], R=C26.CL["R"], delay=C26.CL["delay"]),
                    n=n, fr=c["fr"], Lr=c["Lr"], Cr=c["Cr"], Lm=c["Lm"], Rw=Rw, L=c["L"], RL=RL, CI=E.CI, CO=E.CO, fb=E.FS_CTRL,
                    td_b=50e-9, td_p=c["td_p"], td_s=c["td_s"], td_sb=c["td_sb"], P_in=c["P_in"], P_out=c["P_out"],
                    Ron_b=DEV["GaN650"]["Ron"] / c["nsw"], Coss_b=DEV["GaN650"]["Ctr"] * c["nsw"],
                    Ron_p=DEV["GaN650"]["Ron"] / c["np"], Coss_p=DEV["GaN650"]["Ctr"] * c["np"],
                    Ron_s=DEV["GaN150"]["Ron"] / c["ns"], Coss_s=DEV["GaN150"]["Ctr"] * c["ns"],
                    OCV=E.BAT["OCV"], x0=[float(Z[0, 2]), float(Z[0, 3]), float(Z[0, 5]), float(Z[0, 4])], d0=float(Z[0, 6]),
                    Ii0=(RL + g["Kpi"] * (1. - g["b"])) * float(Z[0, 2]),
                    Vref=E.VO_NOM, vA0=vA0, vb0=vb0, iw0=il0,
                    bus=dict(CA=E28.CA, RW=C26.BUS["Rw"], LW=C26.BUS["Lw"], CB=C26.BUS["Cb"], RD=C26.BUS["Rd"], CD=C26.BUS["Cd"],
                             vmin_q=C26.BUS["vmin"]),
                    ctl=[1 / E.FS_CTRL, g["Kpi"], g["Kii"], g["Kpv"], g["Kiv"], E.I_LIM, -E.PO_REV / E.VO_CV[0] * 1.1, 1., E.HYST, E.DMAX,
                         g["Kpb"], g["Kib"], E.IBAT_MAX, E.IO_MAX, E.T_OL, g["b"]],
                    band=[E.VO_NOM * (1 - E.VO_TOL), E.VO_NOM * (1 + E.VO_TOL)], v_lim=C26.V_LIM, pulse_rating_secondary=E.ID_PULSE_S,
                    # Stage A(A25R)
                    A=dict(Lr=A.BASE["Lr"], Cfly=A.BASE["Cfly"], Rds=A.BASE["Rds"], Vf=A.BASE["Vf"], ESR=A.BASE["ESR"], RL=A.BASE["RL"],
                           Rmisc=A.BASE["Rmisc"], Coss=float(A.qoss_pos(cs["vbat"] / 2) / (cs["vbat"] / 2)), fr0=A.FR0),
                    vC0=[cs["vbat"] / 2] * 8, n0=n0, If0=float(If0), mgr=M,
                    gate_prm=gate_prm(DT_C, M, n0, float(If0), cs["fm"], te if cs["fm"] else 0.),
                    gate_off=[int(round(k * Thalf / 8)) for k in range(8)], fault_module=cs["fm"], t_fault=te if cs["fm"] else 0.,
                    P_rated=P_rated, pk_lim=1.5 * P_rated, i_abs=E28.I_ABS, w_hold=list(W_HOLD))
        json.dump(init, open(f"TB29_{name}_init.json", "w"), indent=1, default=float)
        np.savetxt(f"TB29_{name}_ref.csv", tr, delimiter=",", fmt="%.9g", header="t,vA,vb,ich,iA,icl", comments="")
        np.savetxt(f"TB29_{name}_stageC.csv", Z, delimiter=",", fmt="%.9g",
                   header="t,vbus,iL,vI,ix,vo,d,mode,ibat,iin,pload,iref", comments="")
        json.dump(sa, open(f"TB29_{name}_stageA.json", "w"), indent=1, default=float)
        json.dump(m, open(f"TB29_{name}_metrics.json", "w"), indent=1, default=float)
        out[name] = dict(metrics=m, stageA=sa)
        print(name, "E26: V_A %.2f → 최고 %.2f, 버스 최고 %.2f, 클램프 %.0f J(%.2f ms), 48 V %.3f–%.3f | 모델 사건 전 V_A %.3f, 첨두 %.1f A, "
              "턴오프/피크 %.2f %%, 분담 %s, 모듈 %s, 끝 %d, 턴오프 위반 %d"
              % (vA0, m["vA_max"], m["vb_max"], m["E_clamp_J"], m["t_clamp_on_ms"], vo_min, vo_max, sa["pre"]["vA_mean"],
                 max(sa["pre"]["Ipk"]), 100 * max(sa["pre"]["zcs"]), sa["pre"]["sharing"], sa["events"], sa["n_end"],
                 sa["turnoffs"]["bad"]))
    json.dump(out, open("TB29_ref_summary.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
