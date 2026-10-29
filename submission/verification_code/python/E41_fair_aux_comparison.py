"""[E41] ④(R2 기본형) 대 ⑤(모터·인버터 승압 + 400 V급 보조부품)·⑥(800 V급 보조부품)의 공정 비교와 민감도(최종 검토 docs/45 A2 대응).

■ 왜 필요한가
  결론 2와 기여 1(docs/33 5절)은 "④의 보조 경로 손실이 ⑤보다 12 % 작다"(E38 l1: 101.5 대 115.9 W)를 쓴다. 최종 검토(docs/45 A2)가
  비교 조건의 차이를 찾았다. ④는 Stage A 위상 셰딩(위상당 전류 20 A 아래 1위상)으로 경부하 손실을 줄이는데, ⑤·①의 보조 강압기
  (25 kW, 2위상 50 kHz)는 늘 2위상으로 돌고 고정 철손(정격의 0.1 %, 25 W)이 붙는다. 주행 프로파일 시간의 60 %가 0.5–2.5 kW다.
  검토 진단(판정 아님): ⑤ 보조 강압기에도 셰딩을 주면 차가 0.5 %, 자성체 계수 × 0.5면 2.4 %, × 2면 24.4 %다. 충전 손실
  "전용 승압기의 약 1/3"도 승압기를 50 kHz 한 점으로 둔 값이다(25 kHz면 비 0.43).
  사용자 결정(2026-10-29): 같은 경부하 기법·승압기 주파수·계수 민감도로 다시 계산하고 결론 2·기여 1의 문구를 범위로 바꾼다.

■ 기준 모델(E38 l1과 같음)
  E15 손실 규칙, E38 Stage C 모델(조정형 = E22 선택안, 고정이득 = 5 kW 공진점 DCX), Stage A = A25R 표(E36 a25_grid, 셰딩 I_off 20 A),
  부하·배터리 분포 = E15 프로파일 세 가지(주행 대표·전 범위 균등·저 SOC). ⑤의 보조 경로는 ①과 같다(E25). ⑥ = E25 path6.

■ 공정 비교(실행 전에 고정)
  (F1) ⑤·①의 보조 강압기 위상 셰딩: 각 동작점에서 1위상(정격 12.5 kW 한 상, 철손도 그 상의 몫)과 2위상 가운데 손실이 작은 쪽을
       쓴다(1위상은 P ≤ 12.5 kW일 때만). 이상적 셰딩이라 ⑤에 유리한 쪽이다. ④는 설계된 셰딩(I_off 20 A) 그대로 둔다.
       정보: ④에도 같은 이상적 셰딩(1·2위상 중 작은 쪽, 위상당 전류 ≤ 50 A 격자 안)을 준 값.
  (F2) 민감도(모든 구조에 같이): 자성체 계수 × 0.5·× 2, 스위칭 에너지 × 0.7·× 1.5, 제어 손실 0, GaN 전이시간 × 2(E15 감도와 같은
       항목), Stage A 위상당 고정 손실 + 20 %·+ 30 %(④만, Stage A 출력용량·게이트 고정 손실 기준, E36 e25와 같은 식), Stage A 수동소자
       저항 × 2(④만, E36 a25_grid_Rpass_x2), ⑤·① 보조 강압기 25 kHz(같은 자성체 규칙).
  (F3) 충전 경로: ④ = E38 l2의 375 A 직접 계산(640·800·920 V), ① 전용 승압기 = E15 하드 스위칭 6상 부스트를 16·25·50 kHz로.
       ⑤·⑥의 모터 승압 충전 손실은 E38 l1의 E25 재계산(상저항 범위)을 그대로 인용한다.

■ 결론 문구 규칙(실행 전에 고정. 결과에 맞춰 바꾸지 않는다)
  (W1) 보조 경로 ④ 대 ⑤: 주행 대표 프로파일에서 (F1) 공정 기준과 (F2) 모든 민감도 경우에 ⑤ − ④가 ⑤의 3 %(E15 동등범위)보다 크면
       "④가 ⑤보다 a–b % 작다(공정 기준 c %)"로 쓴다. 공정 기준의 차가 3 % 이하이거나, 한 경우라도 ④ ≥ ⑤이면
       "④와 ⑤의 보조 경로 손실은 모델 계수 범위 안에서 같은 수준이다(공정 기준 c %, 범위 a … b %)"로 쓰고, 보조 손실을 ④의 이점으로
       주장하지 않는다.
  (W2) ④ 대 ⑥: 같은 방식으로 "④가 ⑥보다 a–b W 크다"(또는 같은 수준) — 범위로 쓴다.
  (W3) 충전 경로: "④의 375 A 충전 손실은 전용 승압기(16–50 kHz)의 x–y배"로 쓴다(한 주파수 값만 쓰지 않는다).
  세 프로파일의 값을 모두 보고한다(주행 대표가 기준).

■ 실행   python E41_fair_aux_comparison.py run table
■ 결과   results/E41/*.json
"""
import sys

import numpy as np

from common import load_json, save_json, verdict

EID = "E41"
BAND = 0.03
BOOST_F = (16e3, 25e3, 50e3)


def setup():
    import E15_baseline_loss_rating as E15
    import E38_review_response as E38
    import E36_a25r_impact as E36
    sc, *_ = E38.stage_c_models()
    E15.stage_c = sc
    return E15, E36._SA()


def _hs_shed(E15, orig, f_aux=None):
    """⑤·① 보조 강압기(벅, 25 kW, 2위상) 이상적 셰딩. f_aux: 주파수 바꿈(None이면 그대로)."""
    def hs(kind, Vin, Vout, P, dev, f, nph, Prated, Vnom, ripple=0.3):
        if kind == "buck" and Prated == 25000. and nph == 2:
            ff = f if f_aux is None else f_aux
            l2 = orig(kind, Vin, Vout, P, dev, ff, 2, Prated, Vnom, ripple)
            if P <= Prated / 2:
                l1 = orig(kind, Vin, Vout, P, dev, ff, 1, Prated / 2, Vnom, ripple)
                return min(l1, l2)
            return l2
        return orig(kind, Vin, Vout, P, dev, f, nph, Prated, Vnom, ripple)
    return hs


def _hs_freq(orig, f_aux):
    def hs(kind, Vin, Vout, P, dev, f, nph, Prated, Vnom, ripple=0.3):
        if kind == "buck" and Prated == 25000. and nph == 2:
            return orig(kind, Vin, Vout, P, dev, f_aux, nph, Prated, Vnom, ripple)
        return orig(kind, Vin, Vout, P, dev, f, nph, Prated, Vnom, ripple)
    return hs


class _SAideal:
    """정보: ④ Stage A에도 이상적 셰딩(1·2위상 중 손실이 작은 쪽, 위상당 전류가 격자 안일 때)."""
    def __init__(self, base):
        self.b = base

    def drive(self, V, I, nph=2):
        import E15_baseline_loss_rating as E15
        p2 = E15.StageA.drive(self.b, V, I, 2)
        if abs(I) <= E15.IGRID[-1]:
            p1 = E15.StageA.drive(self.b, V, I, 1)
            return p1 if p1[0] < p2[0] else p2
        return p2

    def charge(self, V):
        return self.b.charge(V)


def _avg(E15, fn, prof):
    pr = E15.PROFILES[prof]
    L = np.array([[fn(V, P) for P in E15.P400] for V in pr["V"]])
    return float(np.mean(L @ E15.W400)), L.mean(0).tolist()


def _all(E15, SA4, prof):
    import E25_motor_boost_comparison as E25
    a4 = _avg(E15, lambda V, P: E15.path_struct("4", SA4, V, P, E15.P48)["loss"], prof)
    a5 = _avg(E15, lambda V, P: E15.path_struct("1", SA4, V, P, E15.P48)["loss"], prof)
    a6 = _avg(E15, lambda V, P: E25.path6(SA4, V, P, E15.P48)["loss"], prof)
    return {"4": a4[0], "5": a5[0], "6": a6[0], "by_load": {"4": a4[1], "5": a5[1], "6": a6[1]}}


def _fixed_per_phase():
    import model_stage_a as A
    import E32_stage_a_25k as E32
    A.set_design(E32.DESIGN); fs = A.FR0
    return 4 * A.qoss_pos(400.) * 400. * fs + 4 * A.BASE["Qg_E"] * fs


def run():
    E15, SA = setup()
    import E32_stage_a_25k as E32
    import E36_a25r_impact as E36
    orig = E15.hs_converter
    K0 = dict(E15.K)
    cases = {}

    def case(tag, k=None, shed=True, SA4=None, f_aux=None):
        E15.K.clear(); E15.K.update(K0)
        if k:
            E15.K.update(k)
        E15.hs_converter = _hs_shed(E15, orig, f_aux) if shed else (_hs_freq(orig, f_aux) if f_aux else orig)
        try:
            cases[tag] = {pk: _all(E15, SA4 or SA, pk) for pk in E15.PROFILES}
        finally:
            E15.hs_converter = orig; E15.K.clear(); E15.K.update(K0)
        c = cases[tag]["drive_typ"]
        print("  %-34s ④ %6.1f  ⑤ %6.1f  ⑥ %6.1f W | ⑤−④ %5.1f W(%5.1f %%), ④−⑥ %5.1f W"
              % (tag, c["4"], c["5"], c["6"], c["5"] - c["4"], 100 * (c["5"] - c["4"]) / c["5"], c["4"] - c["6"]), flush=True)

    case("E38 기준(셰딩 없음)", shed=False)
    case("공정 기준(F1)")
    mag = lambda x: dict(mag_ind_cu=K0["mag_ind_cu"] * x, mag_ind_core=K0["mag_ind_core"] * x,
                         mag_tr_cu=K0["mag_tr_cu"] * x, mag_tr_core=K0["mag_tr_core"] * x)
    case("자성체 × 0.5", mag(0.5)); case("자성체 × 2", mag(2.))
    case("스위칭 × 0.7", dict(esw=0.7)); case("스위칭 × 1.5", dict(esw=1.5))
    case("제어 손실 0", dict(ctrl=0.)); case("GaN 전이 × 2", dict(gan_t=2.))
    fixed = _fixed_per_phase(); T = E36._T_spec()
    for fac in (0.2, 0.3):
        T2 = dict(T); T2["P"] = T["P"] + fac * fixed
        case("Stage A 고정 손실 + %d %%" % round(100 * fac), SA4=E32.StageAs(T2, E36.I_OFF))
    case("Stage A 수동소자 저항 × 2", SA4=E32.StageAs(E36._T_from(load_json("E36", "a25_grid_Rpass_x2")), E36.I_OFF))
    case("⑤ 보조 강압기 25 kHz", f_aux=25e3)
    info = {}
    E15.hs_converter = _hs_shed(E15, orig)
    try:
        info["④도 이상적 셰딩(정보)"] = {pk: _all(E15, _SAideal(SA), pk) for pk in E15.PROFILES}
    finally:
        E15.hs_converter = orig
    c = info["④도 이상적 셰딩(정보)"]["drive_typ"]
    print("  정보: ④에도 이상적 셰딩 ④ %.1f ⑤ %.1f ⑥ %.1f W" % (c["4"], c["5"], c["6"]))
    # (F3) 충전
    l2 = load_json("E38", "l2")["spec_points"]
    e25 = load_json("E38", "l1_e25_comparison")["charge"]
    ch = {}
    for V in (640., 800., 920.):
        b = {"%.0f" % (f / 1e3): E15.hs_converter("boost", V / 2, V, V / 2 * 375., "SiC1200", f, 6, 150000., 400.) for f in BOOST_F}
        sA = l2["%.0fV" % V]["loss_W"]
        ch["%.0fV" % V] = dict(stageA_W=sA, booster_W=b, ratio={k: sA / v for k, v in b.items()},
                               motor_base_W=e25["%.0fV" % V]["motor_base"], motor_min_Rph5_W=e25["%.0fV" % V]["motor_range"]["min_Rph5"])
        print("  충전 %.0f V: ④ %.0f W, 전용 승압기 %s W → 비 %s, 모터 승압 기준점 %.0f·하한 %.0f W"
              % (V, sA, {k: round(v) for k, v in b.items()}, {k: round(v, 2) for k, v in ch["%.0fV" % V]["ratio"].items()},
                 ch["%.0fV" % V]["motor_base_W"], ch["%.0fV" % V]["motor_min_Rph5_W"]))
    # 문구 규칙
    sens = [k for k in cases if k != "E38 기준(셰딩 없음)"]
    d = {k: (cases[k]["drive_typ"]["5"] - cases[k]["drive_typ"]["4"]) / cases[k]["drive_typ"]["5"] for k in sens}
    fair = d["공정 기준(F1)"]
    robust = fair > BAND and all(v > BAND for v in d.values())
    W1 = dict(rule="robust" if robust else "same_level", fair_pct=100 * fair, min_pct=100 * min(d.values()), max_pct=100 * max(d.values()),
              by_case_pct={k: 100 * v for k, v in d.items()})
    d6 = {k: cases[k]["drive_typ"]["4"] - cases[k]["drive_typ"]["6"] for k in sens}
    W2 = dict(fair_W=d6["공정 기준(F1)"], min_W=min(d6.values()), max_W=max(d6.values()), always_positive=all(v > 0 for v in d6.values()))
    rr = [r for v in ch.values() for r in v["ratio"].values()]
    W3 = dict(min_ratio=min(rr), max_ratio=max(rr))
    print("  (W1) ④ 대 ⑤: %s — 공정 기준 %.1f %%, 범위 %.1f … %.1f %%" % ("④가 작다(견고)" if robust else "같은 수준(이점으로 주장하지 않음)",
                                                                W1["fair_pct"], W1["min_pct"], W1["max_pct"]))
    print("  (W2) ④ − ⑥: 공정 기준 %.1f W, 범위 %.1f … %.1f W" % (W2["fair_W"], W2["min_W"], W2["max_W"]))
    print("  (W3) 충전: ④ / 전용 승압기 %.2f–%.2f배" % (W3["min_ratio"], W3["max_ratio"]))
    verdict("E41 실행(문구 규칙 적용)", True, W1["rule"])
    save_json(EID, "fair", dict(cases=cases, info=info, charge=ch, W1=W1, W2=W2, W3=W3, band=BAND, fixed_per_phase_W=fixed,
                                profiles={k: v["label"] for k, v in E15.PROFILES.items()}))


def table():
    d = load_json(EID, "fair")
    rows = []
    for k, v in d["cases"].items():
        rows.append(dict(case=k, **{pk: {s: v[pk][s] for s in ("4", "5", "6")} for pk in v}))
    save_json(EID, "table", dict(rows=rows, W1=d["W1"], W2=d["W2"], W3=d["W3"]))
    for r in rows:
        print("  %s" % r["case"], {pk: {s: round(x, 1) for s, x in r[pk].items()} for pk in ("drive_typ", "uniform", "low_soc")})


if __name__ == "__main__":
    for part in sys.argv[1:]:
        print("E41", part, "...", flush=True)
        globals()[part]()
