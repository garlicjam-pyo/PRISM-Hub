"""TB26 실행 뒤 진단(판정을 바꾸지 않음): C5 손실 차의 원인 확인.

회로의 C5 손실은 마지막 10주기의 (배터리 전력 − V_A 쪽 출력 전력)이다. 이 값은 그 구간에서 Stage A 안에 저장된 에너지의 변화율
(C_fly·L_r)을 포함한다. A25는 C_fly가 6배(46.9 µF)라 C_fly 평균 전압이 1 V만 움직여도 위상당 약 47 W가 된다.
같은 사례의 모델(E33 설정)에서 마지막 10주기의 저장 에너지 변화율 dE/dt = Σ[½C(v_끝² − v_시작²) + ½L(i_끝² − i_시작²)]/Δt를 계산해
회로 손실 − 모델 손실과 비교한다. 또 창의 끝을 한 주기 안에서 20곳으로 옮겨 이 추정의 흩어짐을 본다(창이 실제 스위칭 주기와
정렬되지 않으면 C_fly 리플(±10 V)의 저장 에너지가 남는다).
실행: python diag_loss_TB26.py <검증 코드 python 폴더>  → TB26_loss_diag.json
"""
import json
import sys

import numpy as np

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "../../../../submission/verification_code/python")
import model_stage_a as A                  # noqa: E402
import E28_stage_a_modules as E28          # noqa: E402
import E30_module_fault as E30             # noqa: E402
import E33_stage_a_25k_dynamics as E33     # noqa: E402

CIRCUIT = {"FA25_800V_drive_15kW_m1": 88.80, "FF25_800V_charge_m1": 856.36, "MC25_800V_charge": 382.49}   # results/TB26_summary.txt


def store_rate(r, ncyc=10, shift=0.):
    t = r["t"]; T = r["T"]
    k2 = int(np.searchsorted(t, t[-1] - shift)); k2 = min(k2, len(t) - 1)
    k1 = int(np.searchsorted(t, t[k2] - ncyc * T))
    C = np.asarray(r["C"]); L = np.asarray(r["L"])
    v1, v2 = r["v"][k1].astype(float), r["v"][k2].astype(float)
    i1, i2 = r["i"][k1].astype(float), r["i"][k2].astype(float)
    dEc = 0.5 * C * (v2 ** 2 - v1 ** 2); dEl = 0.5 * L * (i2 ** 2 - i1 ** 2)
    Dt = t[k2] - t[k1]
    return dict(dEdt_W=float((dEc.sum() + dEl.sum()) / Dt), dEdt_C_W=(dEc / Dt).tolist(), dvC_V=(v2 - v1).tolist(), Dt_us=Dt * 1e6)


def main():
    E33.configure()
    out = {}
    for name, kind, src in (("FA25_800V_drive_15kW_m1", "fault", "FA_800V_drive_15kW_m1"), ("FF25_800V_charge_m1", "fault", "FF_800V_charge_m1"),
                            ("MC25_800V_charge", "mgr", "MC_800V_charge_prestart")):
        if kind == "fault":
            kw, n0 = E30.setup(src); r = A.sim_array(**kw)
        else:
            r = E28.run_case(src)
        met = json.load(open(f"TB26_{name}_metrics.json"))
        s = store_rate(r)
        sp = [store_rate(r, shift=f * r["T"])["dEdt_W"] for f in np.arange(0, 1, 0.05)]   # 창 끝을 한 주기 안에서 옮김
        s.update(dEdt_shift_min_W=float(min(sp)), dEdt_shift_max_W=float(max(sp)))
        s.update(model_loss_W=met["loss_ng_W"], circuit_W=CIRCUIT[name], diff_W=CIRCUIT[name] - met["loss_ng_W"],
                 model_plus_store_W=met["loss_ng_W"] + s["dEdt_W"])
        out[name] = s
        print("%-26s 회로 %.1f W, 모델 손실 %.1f W, 모델 저장 변화율 %.1f W → 모델 손실 + 저장 %.1f W (회로와 차 %.1f W), ΔvC %s V"
              % (name, CIRCUIT[name], met["loss_ng_W"], s["dEdt_W"], s["model_plus_store_W"], CIRCUIT[name] - s["model_plus_store_W"],
                 ["%.2f" % x for x in s["dvC_V"]]))
        print("    창 끝을 한 주기 안에서 20곳으로 옮기면 저장 변화율 %.0f … %.0f W(모델 손실 + 저장 %.0f … %.0f W)"
              % (s["dEdt_shift_min_W"], s["dEdt_shift_max_W"], met["loss_ng_W"] + s["dEdt_shift_min_W"], met["loss_ng_W"] + s["dEdt_shift_max_W"]))
    json.dump(out, open("TB26_loss_diag.json", "w"), indent=1)


if __name__ == "__main__":
    main()
