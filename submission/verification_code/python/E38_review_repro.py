"""E38 보조: 외부 검토(2026-10-29) 지적의 재현(진단, 판정 아님).

docs/43 1.1절 표의 "재현" 열 수치를 다시 만든다. 지적이 맞는지 확인하는 계산이며, 설계 판정은 E38_review_response.py가 한다.
대화형으로 확인했던 값을 근거 파일로 남기기 위해 독립 검토(2026-10-29) 뒤에 만들었다.

  r2  지적 2: A25R(C_A 2.4 mF, R_A 9.0 mΩ) E26 클램프 사건 32개를 클램프 저항 1.20·1.25·1.26·1.32 Ω로 → V_A·버스 최고, 470 V 초과 사건 수
  r3  지적 3: E37 클램프 사건 기록(1.2 Ω·끔 463 V)을 E37 판정 함수에 넣되 FF450R12ME4P의 손실값을 150 °C 값으로 바꿈
              (스위칭 에너지만 / 스위칭 에너지 + V_CE)
  r4  지적 4: E26(R2W, 충전기 375 A, 400 V 20 kW + Stage C 5 kW)에서 고장 없는 2 ms(사건 시각 10 ms, 관찰 2 ms)의 클램프 소모 에너지,
              V_bat 936·960·1008 V, 클램프 1.2 Ω·468/463 V. 1008 V 충전은 500 V 충전기 범위 밖의 점이다(검토 원문도 그렇게 밝힘)
  r6  지적 6: E36 A25R 손실 격자(a25_grid.json, 주행 방향 2위상 모의)에서 800 V 8위상 손실(제어 손실 제외)을 위상당 1 A와
              187.5 A(위상당 23.4 A)에서, 375 A 충전 격자 값의 전류 제곱 환산과 비교

실행: python E38_review_repro.py [r2 r3 r4 r6]   결과: results/E38/review_repro.json
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "results" / "E38"
E36D = HERE.parent / "results" / "E36"        # (2026-10-29 정리) 제출 폴더 안 결과(이전에는 저장소 validation/의 사본을 읽었다)
E37D = HERE.parent / "results" / "E37"


def _a25r(E26):
    E26.BUS["CA"] = 2.4e-3
    E26.RA_MOD = 9.0e-3


def _r2_ev(args):
    R, e = args
    import E26_charging_stop as E26
    _a25r(E26)
    E26.CL = dict(E26.CL_DEFAULT, on=468., off=463., R=R)
    r = E26.run_event(**e)
    return dict(R=R, vA_max=r["vA_max"], vb_max=r["vb_max"])


def r2():
    import E26_charging_stop as E26
    evs = [e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after")]
    jobs = [(R, e) for R in (1.20, 1.25, 1.26, 1.32) for e in evs]
    with Pool(8) as p:
        res = p.map(_r2_ev, jobs)
    out = {}
    for R in (1.20, 1.25, 1.26, 1.32):
        rr = [x for x in res if x["R"] == R]
        out["%.2f" % R] = dict(n_events=len(rr), vA_max=max(x["vA_max"] for x in rr), vb_max=max(x["vb_max"] for x in rr),
                               n_over_470=sum(max(x["vA_max"], x["vb_max"]) > 470. for x in rr))
        print("  r2 R %.2f Ω: V_A 최고 %.2f V, 버스 최고 %.2f V, 470 V 초과 %d/%d" % (R, out["%.2f" % R]["vA_max"], out["%.2f" % R]["vb_max"],
                                                                         out["%.2f" % R]["n_over_470"], len(rr)))
    return out


def r3():
    import E37_parts_round2 as E37
    rows = json.load(open(E37D / "clamp_rows.json"))["rows"]
    rr = [r for r in rows if abs(r["R"] - 1.2) < 1e-9 and r["voff"] == 463.]
    g = E37.ds("FF450R12ME4P")["igbt"]
    base = E37.switch_models()["FF450R12ME4P"]
    out = {}
    for name, ch in (("125C_E37", {}),
                     ("150C_Esw", dict(E_on=g["E_on_mJ"]["150"] * 1e-3, E_off=g["E_off_mJ"]["150"] * 1e-3)),
                     ("150C_Esw_Vce", dict(E_on=g["E_on_mJ"]["150"] * 1e-3, E_off=g["E_off_mJ"]["150"] * 1e-3, k_cond=2.05 / 450.))):
        j = E37.judge_switch(rr, dict(base, **ch))
        out[name] = dict(T_vj=j["T_vj"], T_lim=j["T_lim"], ok=j["ok"])
        print("  r3 %s: T_vj %.2f °C (한도 %.0f °C)" % (name, j["T_vj"], j["T_lim"]))
    return out


def r4():
    import E26_charging_stop as E26
    _a25r(E26)
    E26.CL = dict(E26.CL_DEFAULT, on=468., off=463., R=1.2)
    out = {}
    for V in (936., 960., 1008.):
        r = E26.run_event(V, 20e3, 5e3, arch="R2W", clamp=True, t0=10e-3, tend=2e-3)
        out["%.0f" % V] = dict(vA0=r["vA0"], E_clamp_J_2ms=r["E_clamp_J"], t_clamp_on_ms=r["t_clamp_on_ms"],
                               charger_500V_reachable=bool(V / 2 + 9.0e-3 / 4 * 375. <= 500.))
        print("  r4 %.0f V: 초기 V_A %.2f V, 2 ms 클램프 에너지 %.1f J" % (V, r["vA0"], r["E_clamp_J"]))
    return out


def r6():
    d = json.load(open(E36D / "a25_grid.json"))
    fw = [r for r in d["spec"] if r["sign"] > 0]
    Vs = sorted({r["V"] for r in fw}); Is = sorted({r["iph"] for r in fw})
    P = np.array([[next(r["ploss_ph"] for r in fw if r["V"] == V and r["iph"] == i) for i in Is] for V in Vs])

    def p8(V, iph):
        return 8 * float(np.interp(V, Vs, [np.interp(iph, Is, P[k]) for k in range(len(Vs))]))
    ch = {r["V"]: r["ploss_ph"] for r in d["spec"] if r["sign"] < 0}
    cV = sorted(ch)
    p375 = 8 * float(np.interp(800., cV, [ch[v] for v in cV]))
    out = dict(p8_800V_1A_W=p8(800., 1.), p8_800V_187p5A_grid_W=p8(800., 187.5 / 8), p8_800V_375A_charge_W=p375,
               p8_800V_187p5A_square_W=p375 * 0.25, note="제어 손실(4 × 5 W) 제외. 1 A·187.5 A는 주행 방향 격자, 375 A는 충전 방향 격자")
    print("  r6 800 V 8위상: 1 A %.1f W, 187.5 A 격자 %.1f W, 375 A 충전 %.1f W → 제곱 환산 187.5 A %.1f W"
          % (out["p8_800V_1A_W"], out["p8_800V_187p5A_grid_W"], p375, out["p8_800V_187p5A_square_W"]))
    return out


if __name__ == "__main__":
    parts = sys.argv[1:] or ["r2", "r3", "r4", "r6"]
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "review_repro.json"
    res = json.load(open(f)) if f.exists() else {}
    for p in parts:
        print("[%s]" % p)
        res[p] = globals()[p]()
    json.dump(res, open(f, "w"), ensure_ascii=False, indent=1)
    print("저장:", f)
