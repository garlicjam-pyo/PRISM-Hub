"""TB14 기준값 생성: 조정형 Stage C(동기 벅 + CLLC 4.8:1 DCX, 48 V 배터리·정전력 부하)의 평균모델(검증 코드 E22 control과 같은
모델·제어기·게인)로 회로 사례와 같은 조건을 계산한다.

사례(시험 전에 고정, 모두 1.5 ms 동안 정상상태로 둔 뒤 사건)
  A_400V_ramp   입력 400 V, 배터리 없음, 0.1 → 5 kW 계약 부하 변화(4 kW/ms)
  B_270V_step   입력 270 V(최저), 배터리 없음, 0.1 → 5 kW 계단(견고성, 벅 전류 기울기 한계)
  C_504V_rev    입력 504 V(최고), 배터리 없음, 5 → −3 kW 계단(DCX 보내는 쪽이 2차로 바뀜)
  D_bus_step    3 kW, 배터리 없음, 버스 454 → 504 V 계단(10 µs, R2-W460 강등 진입과 같은 크기)
  E_400V_bat    입력 400 V, 48 V 배터리(OCV 47 V, 20 mΩ, 충전 제한 30 A), 0.1 → 5 kW 계단(과부하 시간 제한 2 ms 포함)
결과: TB14_<사례>_init.json(회로 파라미터·초기조건·제어 파라미터), _avg.csv(1 µs), _metrics.json, TB14_ref_summary.json
실행: python make_ref_TB14.py <검증 코드 python 폴더>
"""
import json
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E22_stage_c_regulated as E          # noqa: E402
from E15_baseline_loss_rating import DEV, K   # noqa: E402

T0 = 1.5e-3
CASES = {
    "A_400V_ramp": dict(Vb=[[0, 1], [400., 400.]], P=[[0, T0, T0 + 4.9e-3 / 4, 1], [100., 100., 5000., 5000.]], bat=False, t_end=4.5e-3),
    "B_270V_step": dict(Vb=[[0, 1], [270., 270.]], P=[[0, T0, T0 + 1e-9, 1], [100., 100., 5000., 5000.]], bat=False, t_end=4.5e-3),
    "C_504V_rev": dict(Vb=[[0, 1], [504., 504.]], P=[[0, T0, T0 + 1e-9, 1], [5000., 5000., -3000., -3000.]], bat=False, t_end=4.5e-3),
    "D_bus_step": dict(Vb=[[0, T0, T0 + 10e-6, 1], [454., 454., 504., 504.]], P=[[0, 1], [3000., 3000.]], bat=False, t_end=3.5e-3),
    "E_400V_bat": dict(Vb=[[0, 1], [400., 400.]], P=[[0, T0, T0 + 1e-9, 1], [100., 100., 5000., 5000.]], bat=True, t_end=5.0e-3),
}

c = E.selected(); eq = E.dcx_equiv(c); g = E.gains(c, eq)
n = c["n"]
RL = K["mag_ind_cu"] * E.PO_MAX / (E.PO_MAX * 1.03 / (n * E.VO_NOM)) ** 2
Ip_r = np.sqrt((np.pi * (E.PO_MAX / E.VO_NOM) / (2 * n)) ** 2 / 2 + c["im_pk"] ** 2 / 3)
Rw = K["mag_tr_cu"] * E.PO_MAX / Ip_r ** 2                 # 변압기 권선(1차 환산), 1·2차에 절반씩
out = {}
for name, cs in CASES.items():
    Z = E.run_avg(c, eq, g, cs["P"][0], cs["P"][1], cs["Vb"][0], cs["Vb"][1], battery=cs["bat"], T_end=cs["t_end"], dec=20)
    m = E.metrics(Z, T0 - 0.2e-3)
    m.update(ix_late=E.ix_late(Z, T0 + 2.5e-3, cs["t_end"]) if cs["t_end"] > T0 + 2.6e-3 else float("nan"))
    p0 = cs["P"][1][0]; vb0 = cs["Vb"][1][0]
    vo0 = float(Z[0, 5]); ix0 = float(Z[0, 4]); vI0 = float(Z[0, 3]); iL0 = float(Z[0, 2]); d0 = float(Z[0, 6])
    init = dict(case=name, n=n, fr=c["fr"], Lr=c["Lr"], Cr=c["Cr"], Lm=c["Lm"], Rw=Rw, L=c["L"], RL=RL, CI=E.CI, CO=E.CO,
                fb=E.FS_CTRL, td_b=50e-9, td_p=c["td_p"], td_s=c["td_s"], Lm0=c["Lm0"],
                Ron_b=DEV["GaN650"]["Ron"] / c["nsw"], Coss_b=DEV["GaN650"]["Ctr"] * c["nsw"],
                Ron_p=DEV["GaN650"]["Ron"] / c["np"], Coss_p=DEV["GaN650"]["Ctr"] * c["np"],
                Ron_s=DEV["GaN150"]["Ron"] / c["ns"], Coss_s=DEV["GaN150"]["Ctr"] * c["ns"],
                bat_on=1. if cs["bat"] else 0., OCV=E.BAT["OCV"], Rbat=E.BAT["R"],
                tV=cs["Vb"][0], VV=cs["Vb"][1], tP=cs["P"][0], PP=cs["P"][1], t_end=cs["t_end"], t_event=T0,
                x0=[iL0, vI0, vo0, ix0], d0=d0, Vref=E.VO_NOM,
                ctl=[1 / E.FS_CTRL, g["Kpi"], g["Kii"], g["Kpv"], g["Kiv"], E.I_LIM, -E.PO_REV / E.VO_CV[0] * 1.1, 1., E.HYST, E.DMAX,
                     g["Kpb"], g["Kib"], E.IBAT_MAX, E.IO_MAX, E.T_OL, g["b"]],
                equiv=dict(Rx=eq["Rx"], Lx=eq["Lx"]), pulse_rating_secondary=E.ID_PULSE_S)
    json.dump(init, open(f"TB14_{name}_init.json", "w"), indent=1)
    np.savetxt(f"TB14_{name}_avg.csv", Z, delimiter=",", fmt="%.9g",
               header="t,vbus,iL,vI,ix,vo,d,mode,ibat,iin,pload,iref", comments="")
    m = {k: (None if isinstance(v, float) and v != v else v) for k, v in m.items()}   # NaN → null(표준 JSON, MATLAB jsondecode)
    json.dump(m, open(f"TB14_{name}_metrics.json", "w"), indent=1)
    out[name] = m
    print(name, {k: round(v, 3) for k, v in m.items() if isinstance(v, float)})
json.dump(out, open("TB14_ref_summary.json", "w"), indent=1)
