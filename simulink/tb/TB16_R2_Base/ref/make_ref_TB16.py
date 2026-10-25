"""TB16 기준값 생성: R2 기본형 통합(Stage A 1모듈 + 400 V 버스·감쇠기·정전력 부하 + 조정형 Stage C)의 평균모델.

검증 코드 E23(E22 평균모델에 버스 회로를 같이 푸는 run_avg(bus=...))과 E1(Stage A 영교차 추종 2위상)을 쓴다.
사례(시험 전에 고정, E23 CASES와 같음, 2 ms 사건, 5 ms까지)
  A_540V_Cstep   배터리 540 V(V_A ≈ 270 V), 400 V 부하 10 kW, Stage C 0.1 → 5 kW 계단
  B_806V_Qstep   배터리 806 V(V_A ≈ 403 V), Stage C 3 kW, 400 V 부하 15 → 25 kW(10 µs)
  C_907V_Cregen  배터리 907 V(V_A ≈ 453 V), 400 V 부하 10 kW, Stage C 5 → −3 kW 계단
결과: TB16_<사례>_init.json(회로 파라미터·초기조건·제어 파라미터), _avg.csv(1 µs, 15열), _metrics.json(E23 판정 지표),
      _stageA.json(E1: 사건 전·끝 평균 출력전류에서 위상별 ZCS·V_A 평균), TB16_ref_summary.json
실행: python make_ref_TB16.py <검증 코드 python 폴더>
"""
import json
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E22_stage_c_regulated as E          # noqa: E402
import E23_r2_integrated as R              # noqa: E402
from E15_baseline_loss_rating import DEV, K   # noqa: E402

c, eq, g = R.design()
assert c["P_in"] > 0 and c["zvs_applied"], "E22 design zvs both dcx를 먼저 실행"
n = c["n"]
RL = K["mag_ind_cu"] * E.PO_MAX / (E.PO_MAX * 1.03 / (n * E.VO_NOM)) ** 2
Ip_r = np.sqrt((np.pi * (E.PO_MAX / E.VO_NOM) / (2 * n)) ** 2 / 2 + c["im_pk"] ** 2 / 3)
Rw = K["mag_tr_cu"] * E.PO_MAX / Ip_r ** 2                 # 변압기 권선(1차 환산), 1·2차에 절반씩
out = {}
for name, cs in R.CASES.items():
    Z = R.run_case(name, c, eq, g)
    m = R.evaluate(name, Z)
    m["stageA"] = dict(pre=R.stage_a_ref(cs["vbat"], m["iA_pre"]), final=R.stage_a_ref(cs["vbat"], m["iA_end"]))
    vo0 = float(Z[0, 5]); ix0 = float(Z[0, 4]); vI0 = float(Z[0, 3]); iL0 = float(Z[0, 2]); d0 = float(Z[0, 6])
    vb0 = float(Z[0, 1]); vA0 = float(Z[0, 12]); iw0 = (vA0 - vb0) / R.RW
    init = dict(case=name, vbat=cs["vbat"], n=n, fr=c["fr"], Lr=c["Lr"], Cr=c["Cr"], Lm=c["Lm"], Rw=Rw, L=c["L"], RL=RL, CI=E.CI,
                CO=E.CO, fb=E.FS_CTRL, td_b=50e-9, td_p=c["td_p"], td_s=c["td_s"], td_sb=c["td_sb"], P_in=c["P_in"], P_out=c["P_out"],
                Ron_b=DEV["GaN650"]["Ron"] / c["nsw"], Coss_b=DEV["GaN650"]["Ctr"] * c["nsw"],
                Ron_p=DEV["GaN650"]["Ron"] / c["np"], Coss_p=DEV["GaN650"]["Ctr"] * c["np"],
                Ron_s=DEV["GaN150"]["Ron"] / c["ns"], Coss_s=DEV["GaN150"]["Ctr"] * c["ns"],
                bat_on=0., OCV=E.BAT["OCV"], Rbat=E.BAT["R"],
                tQ=cs["tQ"], QQ=cs["QQ"], tP=cs["tP"], PP=cs["PP"], t_end=R.T_END, t_event=R.T0, band=list(cs["band"]),
                x0=[iL0, vI0, vo0, ix0], d0=d0, Vref=E.VO_NOM, vb0=vb0, vA0=vA0, iw0=iw0,
                bus=dict(RA=R.RA, CA=R.CA, RW=R.RW, LW=R.LW, CB=R.CB, RD=R.RD, CD=R.CD, vmin_q=R.VMIN_Q),
                ctl=[1 / E.FS_CTRL, g["Kpi"], g["Kii"], g["Kpv"], g["Kiv"], E.I_LIM, -E.PO_REV / E.VO_CV[0] * 1.1, 1., E.HYST, E.DMAX,
                     g["Kpb"], g["Kib"], E.IBAT_MAX, E.IO_MAX, E.T_OL, g["b"]],
                equiv=dict(Rx=eq["Rx"], Lx=eq["Lx"]), pulse_rating_secondary=E.ID_PULSE_S)
    json.dump(init, open(f"TB16_{name}_init.json", "w"), indent=1)
    np.savetxt(f"TB16_{name}_avg.csv", Z, delimiter=",", fmt="%.9g",
               header="t,vbus,iL,vI,ix,vo,d,mode,ibat,iin,pload,iref,vA,iA,p400", comments="")
    json.dump(m["stageA"], open(f"TB16_{name}_stageA.json", "w"), indent=1)
    mm = {k: v for k, v in m.items() if k not in ("stageA",)}
    json.dump(mm, open(f"TB16_{name}_metrics.json", "w"), indent=1)
    out[name] = mm
    print(name, "v_o %.2f–%.2f, bus %.2f–%.2f (pre %.2f end %.2f), iA %.1f → %.1f A, pass %s" % (
        m["vo_min"], m["vo_max"], m["bus_min"], m["bus_max"], m["bus_pre"], m["bus_end"], m["iA_pre"], m["iA_end"], m["passed"]))
json.dump(out, open("TB16_ref_summary.json", "w"), indent=1)
