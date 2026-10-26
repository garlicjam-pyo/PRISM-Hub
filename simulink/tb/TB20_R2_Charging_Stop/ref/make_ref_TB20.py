"""TB20 기준값 생성: 충전 중 R2 기본형(Stage A 4모듈 + 충전기 + 400 V 버스·감쇠기 + 조정형 Stage C + V_A 클램프).

검증 코드를 쓴다.
  E26 run_event : V_A 노드 평균모델(Stage A 정적 등가 V_bat/2 + 10.2 mΩ/모듈 수, 버스 회로, 정전력 부하, V_A 클램프 468/463 V·1 Ω·1 µs)
  E22 run_avg   : 조정형 Stage C 평균모델에 E26의 버스 궤적(5 µs 평균)을 이상 버스 전원으로 넣어 48 V 기준(E23 degrade와 같은 방식)
  model_stage_a : Stage A 영교차 추종 스위칭 ODE(dead_fix=True)로 모듈 하나의 위상 첨두·ZCS·V_A(사건 전, 모듈 고장 뒤)
사례(시험 전에 고정, 사건 1.5 ms)
  A_920V_pathloss       배터리 920 V, 충전 375 A, 400 V 부하 20 kW + Stage C 입력 5 kW. 1.5 ms에 배터리 경로 상실(8위상 게이트 차단).
                        클램프 + 비상 정지. 충전기는 3 ms 동안 375 A를 유지한 뒤 0(규격 최악 30 ms를 1/10로 줄임). 5.5 ms까지
  B_640V_pathloss_ramp  배터리 640 V, 같은 부하·사건. 충전기 375 → 5 A를 3 ms 선형 감소 뒤 0. 5.5 ms까지
  C_800V_module_fault   배터리 800 V, 같은 부하, 충전 375 A 유지. 1.5 ms에 모듈 4(위상 7·8) 게이트 차단. 3.5 ms까지
  D_800V_charger_ramp   배터리 800 V, 400 V 부하 10 kW + Stage C 5 kW. 충전기 0 → 375 A(1.5–1.6 ms, 3.75 A/µs = 요구 상한)
                        → 375 → 0 A(3.0–3.1 ms, 계획 정지). 4 ms까지
결과: TB20_<사례>_init.json(회로 파라미터·초기조건·시험 조건), _ref.csv(E26 1 µs: t vA vb ich iA icl),
      _stageC.csv(E22 1 µs), _metrics.json(E26·E22 지표), _stageA.json(E1 기준), TB20_ref_summary.json
실행: python make_ref_TB20.py <검증 코드 python 폴더>
"""
import json
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E22_stage_c_regulated as E          # noqa: E402
import E23_r2_integrated as R              # noqa: E402
import E26_charging_stop as C26            # noqa: E402
import model_stage_a as A                  # noqa: E402
from E15_baseline_loss_rating import DEV, K   # noqa: E402

T_EV = 1.5e-3
T_STOP_TB = 3e-3                            # 충전기 5 A까지(규격 30 ms를 회로 계산 시간 때문에 1/10로)
Q400 = 20e3; PC = 5e3; I0 = 375.
CASES = {
    "A_920V_pathloss": dict(vbat=920., Q=Q400, tI=[0, T_EV, T_EV + T_STOP_TB, T_EV + T_STOP_TB + 1e-9, 1., 2.],
                            II=[I0, I0, I0, 0., 0., 0.], mask=[0] * 8, nmod_after=0, t_end=T_EV + T_STOP_TB + 1e-3),
    "B_640V_pathloss_ramp": dict(vbat=640., Q=Q400, tI=[0, T_EV, T_EV + T_STOP_TB * (1 - 5 / I0), T_EV + T_STOP_TB * (1 - 5 / I0) + 1e-9, 1., 2.],
                                 II=[I0, I0, 5., 0., 0., 0.], mask=[0] * 8, nmod_after=0, t_end=T_EV + T_STOP_TB + 1e-3),
    "C_800V_module_fault": dict(vbat=800., Q=Q400, tI=[0, 1., 2., 3., 4., 5.], II=[I0] * 6, mask=[1, 1, 1, 1, 1, 1, 0, 0],
                                nmod_after=3, t_end=T_EV + 2e-3),
    "D_800V_charger_ramp": dict(vbat=800., Q=10e3, tI=[0, T_EV, T_EV + 100e-6, 3.0e-3, 3.1e-3, 1.], II=[0., 0., I0, I0, 0., 0.],
                                mask=[1] * 8, nmod_after=4, t_end=4e-3),
}


def stage_a_module(vbat, imod):
    """모듈 하나(2위상)가 충전 방향 전류 imod를 받는 정상상태(E26 overload와 같은 계산). imod < 0이면 주행 방향."""
    r = A.sim_array(N=2, Vbat=vbat, Iload=-imod, Cbus=400e-6, mode="zcp", ncyc=80, dead_fix=True)
    ph, bus = A.analyze(r, ncyc_last=10)
    return dict(imod=float(imod), vA_mean=bus["Vbus"], zcs=[float(p["zcs"]) for p in ph], Ipk=[float(p["Ipk"]) for p in ph])


c, eq, g = R.design()
n = c["n"]
RL = K["mag_ind_cu"] * E.PO_MAX / (E.PO_MAX * 1.03 / (n * E.VO_NOM)) ** 2
Ip_r = np.sqrt((np.pi * (E.PO_MAX / E.VO_NOM) / (2 * n)) ** 2 / 2 + c["im_pk"] ** 2 / 3)
Rw = K["mag_tr_cu"] * E.PO_MAX / Ip_r ** 2
p48 = R.p48_for_input(c, eq, PC)
out = {}
for name, cs in CASES.items():
    t0 = T_EV if cs["nmod_after"] != 4 else 10.
    ev = C26.run_event(cs["vbat"], cs["Q"], PC, arch="R2", clamp=True, nmod_after=cs["nmod_after"], tend=cs["t_end"],
                       t0=t0, ich_pwl=(cs["tI"], cs["II"]), rec_every=4, full_trace=True)
    tr = np.array(ev["trace"])                         # 1 µs: t vA vb ich iA icl
    # 버스 5 µs 평균 → Stage C 평균모델(이상 버스 전원)
    w = 5; nn = (tr.shape[0] // w) * w
    tV = np.concatenate(([0.], tr[:nn, 0].reshape(-1, w)[:, -1]))
    VV = np.concatenate(([tr[0, 2]], tr[:nn, 2].reshape(-1, w).mean(axis=1)))
    Z = E.run_avg(c, eq, g, [0., 1.], [p48, p48], tV, VV, T_end=cs["t_end"], dec=20, start_eq=True)
    zz = Z[Z[:, 0] >= 1.0e-3]
    vo_min, vo_max = float(zz[:, 5].min()), float(zz[:, 5].max())
    # Stage A 기준
    vA0 = float(tr[0, 1]); vb0 = float(tr[0, 2])
    imod_pre = float(np.interp(T_EV - 1e-6, tr[:, 0], tr[:, 4])) / 4
    sa = dict(pre=stage_a_module(cs["vbat"], imod_pre))        # imod < 0: 주행 방향(Stage A가 부하에 공급)
    if cs["nmod_after"] == 3:
        sa["final"] = stage_a_module(cs["vbat"], float(tr[-1, 4]) / 3)
    if cs["nmod_after"] == 4:
        sa["mid"] = stage_a_module(cs["vbat"], float(np.interp(2.9e-3, tr[:, 0], tr[:, 4])) / 4)
    E_cl = float(np.sum(tr[:, 1] * tr[:, 5]) * 1e-6)
    m = dict(vA_max=ev["vA_max"], vb_max=ev["vb_max"], vA0=vA0, vb0=vb0, E_clamp_J=ev["E_clamp_J"], E_clamp_1us_J=E_cl,
             t_clamp_on_ms=ev["t_clamp_on_ms"], P_clamp_pk_W=ev["P_clamp_pk_W"], vo_min=vo_min, vo_max=vo_max,
             vo_end=float(Z[-1, 5]), p48=p48, ok_C1=ev["ok_C1"])
    il0 = (cs["Q"] + PC) / vb0
    init = dict(case=name, vbat=cs["vbat"], t_end=cs["t_end"], t_ev=T_EV, t_stop=T_STOP_TB, tI=cs["tI"], II=cs["II"], mask=cs["mask"],
                Q=cs["Q"], P=p48, PC=PC, clamp=dict(von=C26.CL["on"], voff=C26.CL["off"], R=C26.CL["R"], delay=C26.CL["delay"]),
                n=n, fr=c["fr"], Lr=c["Lr"], Cr=c["Cr"], Lm=c["Lm"], Rw=Rw, L=c["L"], RL=RL, CI=E.CI, CO=E.CO, fb=E.FS_CTRL,
                td_b=50e-9, td_p=c["td_p"], td_s=c["td_s"], td_sb=c["td_sb"], P_in=c["P_in"], P_out=c["P_out"],
                Ron_b=DEV["GaN650"]["Ron"] / c["nsw"], Coss_b=DEV["GaN650"]["Ctr"] * c["nsw"],
                Ron_p=DEV["GaN650"]["Ron"] / c["np"], Coss_p=DEV["GaN650"]["Ctr"] * c["np"],
                Ron_s=DEV["GaN150"]["Ron"] / c["ns"], Coss_s=DEV["GaN150"]["Ctr"] * c["ns"],
                OCV=E.BAT["OCV"], x0=[float(Z[0, 2]), float(Z[0, 3]), float(Z[0, 5]), float(Z[0, 4])], d0=float(Z[0, 6]),
                Ii0=(RL + g["Kpi"] * (1. - g["b"])) * float(Z[0, 2]),     # 전류 PI 적분 시작값(평형, E22 start_eq·TB17과 같음)
                Vref=E.VO_NOM, vA0=vA0, vb0=vb0, iw0=il0,
                bus=dict(CA=C26.BUS["CA"], RW=C26.BUS["Rw"], LW=C26.BUS["Lw"], CB=C26.BUS["Cb"], RD=C26.BUS["Rd"], CD=C26.BUS["Cd"],
                         vmin_q=C26.BUS["vmin"]),
                ctl=[1 / E.FS_CTRL, g["Kpi"], g["Kii"], g["Kpv"], g["Kiv"], E.I_LIM, -E.PO_REV / E.VO_CV[0] * 1.1, 1., E.HYST, E.DMAX,
                     g["Kpb"], g["Kib"], E.IBAT_MAX, E.IO_MAX, E.T_OL, g["b"]],
                band=[E.VO_NOM * (1 - E.VO_TOL), E.VO_NOM * (1 + E.VO_TOL)], v_lim=C26.V_LIM, pk_lim=C26.PK_LIM,
                rated_pk=C26.RATED_PK, pulse_rating_secondary=E.ID_PULSE_S)
    json.dump(init, open(f"TB20_{name}_init.json", "w"), indent=1)
    np.savetxt(f"TB20_{name}_ref.csv", tr, delimiter=",", fmt="%.9g", header="t,vA,vb,ich,iA,icl", comments="")
    np.savetxt(f"TB20_{name}_stageC.csv", Z, delimiter=",", fmt="%.9g",
               header="t,vbus,iL,vI,ix,vo,d,mode,ibat,iin,pload,iref", comments="")
    json.dump(sa, open(f"TB20_{name}_stageA.json", "w"), indent=1)
    json.dump(m, open(f"TB20_{name}_metrics.json", "w"), indent=1)
    out[name] = dict(metrics=m, stageA=sa)
    print(name, "V_A %.2f → max %.2f, bus max %.2f, clamp %.0f J (%.2f ms on), 48 V %.3f–%.3f, Stage A pre Ipk %.1f ZCS %.2f %%%s" % (
        vA0, m["vA_max"], m["vb_max"], m["E_clamp_J"], m["t_clamp_on_ms"], vo_min, vo_max, max(sa["pre"]["Ipk"]),
        100 * max(sa["pre"]["zcs"]),
        "" if "final" not in sa else ", final(3 modules) Ipk %.1f ZCS %.2f %%" % (max(sa["final"]["Ipk"]), 100 * max(sa["final"]["zcs"]))))
json.dump(out, open("TB20_ref_summary.json", "w"), indent=1)
