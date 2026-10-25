"""TB17 기준값 생성: R2-W460 통합 회로(Stage A 모듈 1 + 창 조정 Stage B(H-브리지 개방 강등) + 조정형 Stage C).

검증 코드 E23 degrade(= E17 보호 상태기계, 강등 방식 E21 P3t, 고장 시각 1.5 ms → 그 버스 궤적을 E22 평균모델에 넣은 48 V)와
E1(Stage A 영교차 추종 2위상)을 쓴다. 회로·상태기계·지령표·게이트 생성기는 TB13과 같고 다른 것은 다음뿐이다.
  - V_A: 이상 V_bat/2 + 13.2 mΩ → Stage A 모듈 회로(출력저항 약 10.2 mΩ가 회로에서 생김) + C_A 400 µF + 배선 3 mΩ·1.5 µH
  - 400 V 부하 분리 뒤 남는 부하(E17 P_C 5 kW): 정전력 등가 → 조정형 Stage C 회로(입력 5 kW가 되는 48 V 부하 4.9 kW)
  - 고장 시각 0.5 → 1.5 ms(Stage A 회로 정착, 사건 전 판정 구간 1.3–1.5 ms)
사례(TB13과 같은 조건)
  A_1008V_hbopen  1008 V, 25 kW(400 V 부하 20 kW + Stage C 5 kW), H-브리지 개방 → 정합 유지 → 부하 분리 → 붕괴 → 소프트 바이패스 → 강등
  B_930V_hbopen    930 V, 같은 고장, 일시 감발 → 강등 0.5 ms 뒤 400 V 부하 되돌림
결과: TB17_<사례>_init.json, _avg.csv(E17, 1 µs), _stageC.csv(E22 평균모델, 1 µs), _metrics.json, _stageA.json,
      TB17_eps_table.json(TB13과 같음), TB17_ref_summary.json
실행: python make_ref_TB17.py <검증 코드 python 폴더>(먼저 E21 table, E22 design zvs both dcx)
"""
import json
import math
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E17_protection_integration as E17          # noqa: E402
import E19_r2_window_module as E19                # noqa: E402
import E22_stage_c_regulated as E                 # noqa: E402
import E23_r2_integrated as R                     # noqa: E402
import dab_modulation as DM                       # noqa: E402
from controller_adopted import K_ADOPTED          # noqa: E402
from model_stage_b import equilibrium             # noqa: E402
from E15_baseline_loss_rating import DEV, K as KL   # noqa: E402

CASE = "W460_240s"
EV = {"enable": 1, "disable": 2, "dab": 3, "hb_open": 4, "m_pos": 5, "m_neg": 6}
POL = {"now": 1, "collapse_now": 2, "clamp": 3, "clamp_brk": 4, "clamp_brk_hard": 5}
FTYPE = {"hb_open": 1, "dab": 2}
T_EV = R.T_EV_DEG

c = E19.CASES[CASE]; p, cp = E19.plant(CASE)
K = np.asarray(K_ADOPTED, float)
pk_rated = E17.dab_sps_peak(c["VW"], 100., p.power_max / 100., p)

# ---- 회로 지령표(TB13과 같은 계산) ---------------------------------------------------------------------------
T = DM.eps_table()
J = np.asarray(T["j"]); keep = J <= 1e-9
d = np.asarray(T["d"])[:, keep]; a = np.asarray(T["a"])[:, keep]; pk = np.asarray(T["pk"])[:, keep]
d[:, -1] = d[:, -2]; a[:, -1] = a[:, -2]; pk[:, -1] = pk[:, -2]
pk = np.asarray(DM.sw_table(p)["pk_sw"])
phi = np.vectorize(lambda aa, dd: math.remainder(aa + (1 - dd / np.pi) * np.pi, 2 * np.pi))(a, d)
tab = dict(r0=float(T["r"][0]), dr=float(T["r"][1] - T["r"][0]), j0=float(J[keep][0]), dj=float(J[1] - J[0]),
           d=d.tolist(), phi=phi.tolist(), pk=pk.tolist(), pk_max=R.PKD * pk_rated, rated_pk=pk_rated)
json.dump(tab, open("TB17_eps_table.json", "w"))

# ---- Stage C 설계(TB16과 같은 소자·권선 값) ----------------------------------------------------------------------
cC, eq, g = R.design()
n = cC["n"]
RL = KL["mag_ind_cu"] * E.PO_MAX / (E.PO_MAX * 1.03 / (n * E.VO_NOM)) ** 2
Ip_r = np.sqrt((np.pi * (E.PO_MAX / E.VO_NOM) / (2 * n)) ** 2 / 2 + cC["im_pk"] ** 2 / 3)
Rw = KL["mag_tr_cu"] * E.PO_MAX / Ip_r ** 2

out = {}
for name in R.DEG_CASES:
    job, m, tr, Z, p48 = R.degrade_case(name, cC, eq, g)
    V, P = job["V"], job["P"]
    xe, ue = equilibrium(V, P, p); x0 = np.array(xe, float); st0 = 3
    u0 = np.array([x0[1] / x0[4], 0.])
    q0 = float(-(x0[0] + K[:4] @ x0[:4]) / K[4])
    sup = [c["VW"], c["upper"], E17.H, p.R, p.Rh, p.Cs, p.Lh, p.inner_tau, p.Clink, job.get("vd", E17.VD),
           T_EV, EV[job["event"]], POL[job["policy"]], 0., 0., job.get("t_prep", E17.T_PREP), job.get("wait", E17.T_WAIT),
           E17.RAMP, E17.HOLD, E17.ZERO, job["t_shed"], E17.RATE_COL, E17.VL_SOFT, job.get("t_soft", E17.T_SOFT),
           E17.R_SOFT0, E17.R_BYP, E17.T_COL_MAX, E17.VL_SW[0], E17.VL_SW[1], E17.T_SW, E17.VB_SW, E17.T_VB,
           E17.KP_B, E17.KI_B, E17.QB_MAX, E17.W_L, E17.TAU_ST, 1e6, p.power_max, p.link_max, p.turns, p.phase_max,
           p.fs, p.Ldab, V, st0, p.Ts, E17.VS_GATE, E17.T_GATE, E17.T_GATE_MAX,
           E17.VL_STALL, E17.T_STALL, E17.DV_STALL, E17.DI_SOFT, E17.K_UP, E17.T_SOFT_MAX,
           1., 1., 1., E17.T_RESTORE]                                   # hold match, curtail, soft_fail(P3t, TB13과 같음)
    prot = [E17.T_HW, E17.I_HW, E17.VL_HW, E17.VS_HW, c["upper"], FTYPE[job["event"]], T_EV, E17.T_GDF]
    eps_prm = [1., p.turns, p.Ldab, p.fs, R.PKD * pk_rated, tab["r0"], tab["dr"], tab["j0"], tab["dj"]]
    # Stage C 시작점: 버스 460 V(창)에서 48 V 부하 p48의 평형(E22 평균모델 Z의 첫 행)
    vo0 = float(Z[0, 5]); ix0 = float(Z[0, 4]); vI0 = float(Z[0, 3]); iL0 = float(Z[0, 2]); d0 = float(Z[0, 6])
    pin0 = float(Z[0, 9] * Z[0, 1])
    init = dict(case=name, vbat=V, P0=P, P400=P - R.PC_IN, PC_IN=R.PC_IN, P48=p48, Pc=0., t_end=job["duration"], t_event=T_EV,
                x0=x0[:6].tolist(), vcd0=float(x0[2]), u0=u0.tolist(), q0=q0, st0=st0, VW=c["VW"], upper=c["upper"],
                dab_rated_W=p.power_max, turns=p.turns, Ldab=p.Ldab, eta=p.eta, R_bypass=E17.R_BYP, Vd=job.get("vd", E17.VD),
                Rbrk=E17.R_BRK, Rdmp=E17.R_DMP, Cdmp=E17.C_DMP, sup_prm=sup, prot_prm=prot, eps_prm=eps_prm,
                event=job["event"], policy=job["policy"], rated_pk=pk_rated, pk_max=R.PKD * pk_rated,
                # Stage A·배선(E23과 같음)
                RA=R.RA, CA=R.CA, RW=R.RW, LW=R.LW, vmin_q=R.VMIN_Q,
                # Stage C(TB16과 같음)
                n=n, fr=cC["fr"], Lr=cC["Lr"], Cr=cC["Cr"], Lm=cC["Lm"], Rw=Rw, L=cC["L"], RL=RL, CI=E.CI, CO=E.CO,
                fb=E.FS_CTRL, td_b=50e-9, td_p=cC["td_p"], td_s=cC["td_s"], td_sb=cC["td_sb"], P_in=cC["P_in"], P_out=cC["P_out"],
                Ron_b=DEV["GaN650"]["Ron"] / cC["nsw"], Coss_b=DEV["GaN650"]["Ctr"] * cC["nsw"],
                Ron_p=DEV["GaN650"]["Ron"] / cC["np"], Coss_p=DEV["GaN650"]["Ctr"] * cC["np"],
                Ron_s=DEV["GaN150"]["Ron"] / cC["ns"], Coss_s=DEV["GaN150"]["Ctr"] * cC["ns"],
                OCV=E.BAT["OCV"], xC0=[iL0, vI0, vo0, ix0], d0=d0, pinC0=pin0, Vref=E.VO_NOM,
                Ii0=(RL + g["Kpi"] * (1. - g["b"])) * iL0,      # 전류 PI 적분 시작값(평형, E22 run_avg start_eq와 같음)
                band=[E.VO_NOM * (1 - E.VO_TOL), E.VO_NOM * (1 + E.VO_TOL)],
                ctl=[1 / E.FS_CTRL, g["Kpi"], g["Kii"], g["Kpv"], g["Kiv"], E.I_LIM, -E.PO_REV / E.VO_CV[0] * 1.1, 1., E.HYST, E.DMAX,
                     g["Kpb"], g["Kib"], E.IBAT_MAX, E.IO_MAX, E.T_OL, g["b"]],
                pulse_rating_secondary=E.ID_PULSE_S)
    json.dump(init, open(f"TB17_{name}_init.json", "w"), indent=1)
    t, L = tr["t"], tr["log"]
    np.savetxt(f"TB17_{name}_avg.csv", np.column_stack([t, L[:, :6], L[:, 6], L[:, 7], L[:, 8], L[:, 9]]), delimiter=",",
               header="t_s,ip,vs,vbus,ih,vlink,idab,ibyp,loads400,bridge,Pbrk", comments="", fmt="%.9g")
    np.savetxt(f"TB17_{name}_stageC.csv", Z, delimiter=",", fmt="%.9g",
               header="t,vbus,iL,vI,ix,vo,d,mode,ibat,iin,pload,iref", comments="")
    # E23 degrade 지표(같은 계산)
    q = Z[:, 0] >= T_EV - 0.2e-3
    mc = E.metrics(Z, T_EV - 0.2e-3)
    pre = (t > T_EV - 0.2e-3) & (t <= T_EV); fin = t > t[-1] - 0.2e-3
    ip_pre, ip_end = float(L[pre, 0].mean()), float(L[fin, 0].mean())
    sa = dict(pre=R.stage_a_ref(V, ip_pre), final=R.stage_a_ref(V, ip_end), final_1ph=R.stage_a_ref(V, ip_end, N=1))
    json.dump(sa, open(f"TB17_{name}_stageA.json", "w"), indent=1)
    met = {k: v for k, v in m.items()}
    met.update(stageC=dict(vo_min=mc["vo_min"], vo_max=mc["vo_max"], vo_end=float(Z[-1, 5]), ix_avg100_max=mc["ix_avg100_max"],
                           ix_dev_peak=mc["ix_dev_peak"], pin_min=float((Z[q, 9] * Z[q, 1]).min()),
                           pin_max=float((Z[q, 9] * Z[q, 1]).max()), p48=p48))
    json.dump(met, open(f"TB17_{name}_metrics.json", "w"), indent=1, default=float)
    out[name] = dict(pass_=m["pass_"], events=m["events"], final_state=m["final_state"], vbus_min=m["vbus_min"], vbus_max=m["vbus_max"],
                     path_peak=m["path_peak"], dab_sec_peak=m.get("dab_sec_peak"), soft_energy_J=m.get("soft_energy_J"),
                     brk_energy_J=m["brk_energy_J"], stageC=met["stageC"], ip_pre=ip_pre, ip_end=ip_end,
                     stageA_zcs=dict(pre=sa["pre"]["zcs"], final=sa["final"]["zcs"], final_1ph=sa["final_1ph"]["zcs"]))
    print(name, "E17 %s, events %s" % ("PASS" if m["pass_"] else "FAIL", m["events"]))
    print("   Stage C P48 %.0f W (input at start %.0f W), v_o %.3f-%.3f V; Stage A %.1f -> %.1f A, E1 ZCS pre %s final %s (1ph %s)"
          % (p48, pin0, mc["vo_min"], mc["vo_max"], ip_pre, ip_end, np.round(100 * np.array(sa["pre"]["zcs"]), 2),
             np.round(100 * np.array(sa["final"]["zcs"]), 2), np.round(100 * np.array(sa["final_1ph"]["zcs"]), 2)))
json.dump(out, open("TB17_ref_summary.json", "w"), indent=1, default=float)
