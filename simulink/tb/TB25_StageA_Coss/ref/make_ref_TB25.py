"""TB25 기준값 생성: Stage A 1위상 RSC + 스위치 출력용량(등가 선형 C_oss), 고정 타이밍 0.98·f_r, 800 V.

설계 세 가지(검증 코드 E31):
  O  원설계: L_r 144.1 nH, C_fly 7.8125 µF(f_r 150 kHz), R_ds 6 mΩ, C_oss = Q_oss,위치(400 V)/400 V(C4MS008075U2 2병렬)
  A  E31 선택 (가)(최소 변경안),  B  E31 선택 (나)(충전 우선안; A와 같으면 뺀다)
기준값:
  formula_W    4·C_oss·(V_bat/2)²·f_s (f_s = 1/T, T는 2.5 ns 격자에 맞춘 주기)
  exact_nl_C_W 노드 용량 정확해(E31.rsc_nodecap, 행렬 지수) 무부하 손실
  exact_ld_C_W 같은 정확해에서 출력전류 46.875 A가 되는 출력전압의 손실(바디 다이오드 없음: 노드 전압이 레일 안에 있으면 같다)
  e1_ld_0_W    E1 모델(sim_array 고정 타이밍, 출력용량 없음) 46.875 A 손실(도통 + 다이오드)
  model_fix_W  원 E1 모델의 고정 손실 항 4·(E_oss + Q_g·E)·f_s(비교용)
결과: TB25_cases.json(사례 12개 이하), TB25_ref_summary.json
실행: python make_ref_TB25.py <검증 코드 python 폴더>
"""
import json
import sys

import numpy as np
from scipy.optimize import brentq

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import E31_stage_a_coss as E31      # noqa: E402
import model_stage_a as SA          # noqa: E402
from common import load_json        # noqa: E402

DT = 2.5e-9
VBAT = 800.
IL = 375. / 8
NCYC, NEVAL = 50, 10


def design_params():
    devs = {n: E31.load_dev(n) for n in E31.DEVICES}
    origs, _ = E31.original_designs(devs)
    out = dict(O=dict(label="original 150 kHz, C4MS008075U2 x2 per position", Lr=E31.LR0, Cfly=E31.CF0, Rds=E31.RDS0,
                      Coss=origs[0]["Qpos"](400.) / 400.))
    res = load_json("E31", "coss")
    hw = {d["key"]: d for d in E31.hw_designs(devs)}
    seen = set()
    for k, lab in (("가", "A"), ("나", "B")):
        s = res["selection"].get(k)
        if not s:
            continue
        key, fr = s.split("@")
        row = [r for r in res["grid"] if r["key"] == key and abs(r["fr"] / 1e3 - float(fr.replace("kHz", ""))) < 0.5][0]
        if (key, row["fr"]) in seen:
            continue
        seen.add((key, row["fr"]))
        out[lab] = dict(label=f"E31 selection ({'ga' if k == '가' else 'na'}) {key} f_r {row['fr']/1e3:.0f} kHz", Lr=row["Lr"], Cfly=row["Cfly"],
                        Rds=row["Rpos"], Coss=hw[key]["Qpos"](400.) / 400.)
    return out


def e1_fixed_loss(Lr, Cf, Rds, T):
    keep = {k: SA.BASE[k] for k in ("Lr", "Cfly", "Rds")}; fr0 = SA.FR0
    try:
        SA.BASE.update(Lr=Lr, Cfly=Cf, Rds=Rds); SA.FR0 = 1 / (2 * np.pi * np.sqrt(Lr * Cf))
        r = SA.sim_array(N=1, Vbat=VBAT, Iload=IL, Cbus=400e-6, mode="fixed", fratio=1 / (T * SA.FR0), ncyc=60)
        p = E31.ph_parts(r)[0]
        return p["Pc"] + p["Pd"], p
    finally:
        SA.BASE.update(keep); SA.FR0 = fr0


def main():
    D = design_params()
    designs, cases, summ = {}, {}, {}
    for name, d in D.items():
        fr = 1 / (2 * np.pi * np.sqrt(d["Lr"] * d["Cfly"]))
        T = round(1 / (0.98 * fr) / DT) * DT
        fratio = 1 / (T * fr)
        formula = 4 * d["Coss"] * (VBAT / 2) ** 2 / T
        pnl, inl, _ = E31.rsc_nodecap(VBAT, VBAT / 2, d["Coss"], d["Lr"], d["Cfly"], d["Rds"], E31.RPASS, fratio=fratio, ncyc=60)
        f = lambda vo: E31.rsc_nodecap(VBAT, vo, d["Coss"], d["Lr"], d["Cfly"], d["Rds"], E31.RPASS, fratio=fratio, ncyc=60)[1] - IL
        vo = brentq(f, VBAT / 2 - 5., VBAT / 2)
        pld, ild, _ = E31.rsc_nodecap(VBAT, vo, d["Coss"], d["Lr"], d["Cfly"], d["Rds"], E31.RPASS, fratio=fratio, ncyc=60)
        e1, p1 = e1_fixed_loss(d["Lr"], d["Cfly"], d["Rds"], T)
        designs[name] = dict(label=d["label"], fr=fr, T=T, Lr=d["Lr"], Cfly=d["Cfly"], Rds=d["Rds"], Coss=d["Coss"],
                             formula_W=formula, exact_nl_C_W=pnl, exact_nl_Iout=inl, exact_ld_C_W=pld, exact_ld_vout=vo,
                             e1_ld_0_W=e1, e1_Ipk=p1["Ipk"], model_fix_W=4 * (SA.BASE["Eoss"] + SA.BASE["Qg_E"]) / T)
        for ld, Iload, v0 in (("nl", 0., VBAT / 2), ("ld", IL, vo)):
            for cc, C in (("0", 1e-15), ("C", d["Coss"])):
                cases[f"{name}_{ld}_{cc}"] = dict(Lr=d["Lr"], Cfly=d["Cfly"], Rds=d["Rds"], Coss=C, Iload=Iload, vout0=v0, vC0=VBAT / 2)
        print(f"{name}: f_r {fr/1e3:.2f} kHz, T {T*1e6:.4f} us, C_oss {d['Coss']*1e9:.3f} nF, formula {formula:.2f} W, "
              f"exact no-load {pnl:.2f} W, exact 46.9 A {pld:.2f} W (V_out {vo:.3f}), E1 no-C_oss {e1:.2f} W, old model fixed "
              f"{designs[name]['model_fix_W']:.2f} W")
    json.dump(dict(vbat=VBAT, ncyc=NCYC, neval=NEVAL, designs=designs, cases=cases), open("TB25_cases.json", "w"), indent=1)
    json.dump(designs, open("TB25_ref_summary.json", "w"), indent=1)


if __name__ == "__main__":
    main()
