"""[E42] 가치 지도(E18)를 ①의 보조 강압기에 경부하 셰딩을 준 공정 기준으로 다시 계산한다(최종 보고서 독립 검토 대응).

■ 왜 필요한가
  최종 보고서의 기여 2와 결론 Q3는 "창 조정 모듈은 B_470의 224–240s와 B_420의 200s에서 보조 손실 최선"이라고 쓴다(E38 l1의
  가치 지도). 그런데 가치 지도의 ①(전전력 승압기 + 보조 강압기)은 ⑤(모터·인버터 승압)와 같은 보조 강압기(25 kW, 2위상 50 kHz)를
  경부하 셰딩 없이 두었다. E41은 ④ 대 ⑤ 비교에서 이 강압기에 이상적 셰딩을 주어 사양 팩 보조 손실이 115.9 → 102.1 W(13.8 W)
  줄어드는 것을 보였다. 같은 조건을 가치 지도에 주지 않았으므로, ①과의 차가 13.8 W보다 작은 칸(B_420 200s 9.0 W, B_470 224s
  13.1 W)은 판정이 바뀔 수 있다(독립 검토 지적, 2026-11-03). 사용자 결정(2026-11-03): 다시 계산하고 결과로 기여 2·Q3 문장을 고친다.

■ 기준 모델(E38 l1의 가치 지도와 같음)
  E15 손실 규칙, E38 Stage C 모델(조정형 = E22 선택안, 고정이득 = 5 kW 공진점 DCX), E38 정격 규칙, Stage A = A25R 확장 격자
  (E36 _ext_model, 셰딩 I_off 20 A), E18 팩 등급·성립 조건·프로파일 그대로.

■ 공정 기준과 경우(실행 전에 고정)
  (F1) 공정 기준: ①의 보조 강압기에 E41과 같은 이상적 셰딩(각 동작점에서 1위상(정격 12.5 kW 한 상)과 2위상 가운데 손실이 작은
       쪽, 1위상은 P ≤ 12.5 kW일 때만). 구현은 E41._hs_shed를 그대로 쓴다.
       ②의 전전력 조정기는 모델에서 1위상 4스위치 벅부스트라 위상 셰딩 대상이 없다(그대로). ③·R2-W의 Stage B와 ④·②·③·R2-W의
       Stage A는 설계된 운전 그대로다(Stage A는 설계 셰딩 I_off 20 A).
  (F2) 민감도(공정 기준 위에서, 모든 구조에 같이): E41의 손실 계수 항목 — 자성체 × 0.5·× 2, 스위칭 에너지 × 0.7·× 1.5, 제어 손실 0,
       GaN 전이시간 × 2, ① 보조 강압기 25 kHz. E41의 Stage A 항목(위상당 고정 손실 + 20·30 %, 수동소자 저항 × 2)은 확장 전압 격자의
       변형이 없어 넣지 않는다(한계로 적는다).
  성립 여부는 손실과 무관한 정적 조건이라 바뀌지 않아야 한다(아래 R0에서 확인).

■ 확인(실행 전에 고정. 통과하지 않으면 구현 오류로 보고 고친 뒤 다시 실행하며, 1차 결과를 남긴다)
  (R0) 셰딩을 끈 경우가 E38 l1 가치 지도(results/E38/l1_e18_A25R_value_map.json)와 모든 칸의 손실 차 ≤ 1e-6 W, 성립·최선 칸이 같다.
  (R1) 공정 기준 사양 팩 ① 보조 평균 = E41 공정 기준 ⑤(results/E41/fair.json) ± 0.05 W.
  (R2) 모든 경우에서 성립 집합이 E38과 같다.

■ 칸 판정과 문구 규칙(실행 전에 고정. 결과에 맞춰 바꾸지 않는다)
  각 팩 × 부품 등급 칸에서 성립 구조 가운데 공정 기준 최소 손실 구조를 b, 나머지 가운데 최소를 s라 하고 여유 m = (L_s − L_b)/L_s.
  (C1) "최선": 공정 기준과 (F2) 모든 경우에서 b가 최소이고 m > 3 %(E15 동등범위).
  (C2) "같은 수준": 공정 기준에서 b가 최소지만, 어느 경우에서 m ≤ 3 %이거나 다른 구조가 최소가 된다. 이때 3 % 안에 들거나
       최소가 된 구조를 함께 적고, b를 그 칸의 최선으로 주장하지 않는다.
  성립 구조가 하나뿐인 칸은 "유일 성립"으로 적는다.
  (W) 기여 2·Q3 문장: 창 조정 모듈(R2-W410·R2-W460)이 (C1)인 칸만 "보조 손실 최선"으로, (C2)인 칸은 "보조 손실이 같은 수준"으로,
      유일 성립 칸은 "유일하게 성립"으로 쓴다. 어느 칸에도 해당하지 않으면 창 조정 모듈의 보조 손실 이점을 주장하지 않는다.
      ④(R2 기본형) 칸도 같은 규칙으로 적는다.

■ 실행   python E42_value_map_fair.py run
■ 결과   results/E42/cases.json(경우별 가치 지도 손실), cells.json(칸 판정), E42_value_map_fair.png(공정 기준 그림)

■ 한계
  E15·E18과 같은 설계 단계 추정(대표 소자, 자성체 비율 규칙, 열·기생 성분 제외). 이상적 셰딩은 ①에 유리한 쪽이다. 자성체 손실을
  정격의 비율로 두므로 25 kHz 경우의 자성체 크기 증가는 손실에 들어가지 않는다(①에 유리한 끝값). Stage A 고정 손실 민감도는 넣지 않았다.
"""
import sys

import numpy as np

from common import load_json, save_json, verdict, outdir

EID = "E42"
BAND = 0.03
TOL_REG = 1e-6
CLASSES = ("B_420", "B_470")


def setup():
    import E15_baseline_loss_rating as E15
    import E18_industry_value_map as E18
    import E36_a25r_impact as E36
    import E38_review_response as E38
    sc, orig_sc, (regA, regF), fixF, _ = E38.stage_c_models()
    E15.stage_c = sc
    r0 = E15.ratings

    def ratings(SAm):                                   # E38 l1과 같은 정격 규칙(Stage C 최종 설계)
        r = r0(SAm)
        for k, v in r.items():
            if k == "extra":
                continue
            parts = dict(v["parts"])
            if "stageC_pre" in parts:
                parts["stageC"] = regA; parts["stageC_pre"] = regF
            else:
                parts["stageC"] = fixF
            tot = {m: sum(x[m] for x in parts.values()) for m in ("positions", "devices", "switch_kVA", "rated_kW", "magnetics")}
            r[k] = dict(parts=parts, total=tot)
        return r
    E15.ratings = ratings
    SAm = E36._ext_model("A25R")
    c15 = load_json("E38", "l1_e15_comparison")
    E18.stage_a_model = lambda: SAm
    E18.load_json = lambda eid, name: c15 if (eid, name) == ("E15", "comparison") else load_json(eid, name)
    return E15, E18


def run_cases():
    E15, E18 = setup()
    import E41_fair_aux_comparison as E41
    orig = E15.hs_converter
    K0 = dict(E15.K)
    captured = {}
    E18.save_json = lambda eid, name, obj: captured.__setitem__("out", obj)
    fig_for = {"tag": None}
    fig0 = E18.figure
    E18.figure = lambda out, path: (fig0(out, outdir(EID) / "E42_value_map_fair.png")
                                    if fig_for["tag"] == "공정 기준(F1)" else None)
    mag = lambda x: dict(mag_ind_cu=K0["mag_ind_cu"] * x, mag_ind_core=K0["mag_ind_core"] * x,
                         mag_tr_cu=K0["mag_tr_cu"] * x, mag_tr_core=K0["mag_tr_core"] * x)
    plan = [("E38 기준(셰딩 없음)", None, False, None), ("공정 기준(F1)", None, True, None),
            ("자성체 × 0.5", mag(0.5), True, None), ("자성체 × 2", mag(2.), True, None),
            ("스위칭 × 0.7", dict(esw=0.7), True, None), ("스위칭 × 1.5", dict(esw=1.5), True, None),
            ("제어 손실 0", dict(ctrl=0.), True, None), ("GaN 전이 × 2", dict(gan_t=2.), True, None),
            ("① 보조 강압기 25 kHz", None, True, 25e3)]
    cases = {}
    for tag, k, shed, f_aux in plan:
        E15.K.clear(); E15.K.update(K0)
        if k:
            E15.K.update(k)
        E15.hs_converter = E41._hs_shed(E15, orig, f_aux) if shed else orig
        fig_for["tag"] = tag
        try:
            print("\n######## %s ########" % tag, flush=True)
            E18.main()
        finally:
            E15.hs_converter = orig; E15.K.clear(); E15.K.update(K0)
        out = captured.pop("out")
        cases[tag] = {pk: dict(loss={s: v["loss"]["avg_W"] for s, v in r["structs"].items()},
                               same_as={s: v.get("same_as") for s, v in r["structs"].items()},
                               feas={c: sorted(r["best"][c]["feasible"]) for c in CLASSES},
                               best={c: r["best"][c]["best"] for c in CLASSES})
                      for pk, r in out["packs"].items()}
        if tag == "공정 기준(F1)":
            save_json(EID, "value_map_fair", out)
    return cases


def judge_cells(cases):
    fair = cases["공정 기준(F1)"]
    sens = [t for t in cases if t not in ("E38 기준(셰딩 없음)",)]
    e38 = cases["E38 기준(셰딩 없음)"]
    cells = {}
    for pk in fair:
        for c in CLASSES:
            feas = fair[pk]["feas"][c]
            if not feas:
                cells[f"{pk}/{c}"] = dict(cls="성립 없음"); continue
            L = fair[pk]["loss"]
            b = min(feas, key=lambda s: L[s])
            row = dict(feasible=feas, best_fair=b, best_E38=e38[pk]["best"][c],
                       loss_fair={s: L[s] for s in feas}, loss_E38={s: e38[pk]["loss"][s] for s in feas})
            if len(feas) == 1:
                row["cls"] = "유일 성립"; cells[f"{pk}/{c}"] = row; continue
            ties, margins, flips = set(), {}, set()
            for t in sens:
                Lt = cases[t][pk]["loss"]
                bt = min(feas, key=lambda s: Lt[s])
                if bt != b:
                    flips.add(bt)
                others = [s for s in feas if s != b]
                st = min(others, key=lambda s: Lt[s])
                m = (Lt[st] - Lt[b]) / Lt[st]
                margins[t] = m
                for s in others:
                    if (Lt[s] - Lt[b]) / Lt[s] <= BAND:
                        ties.add(s)
            robust = not flips and all(m > BAND for m in margins.values())
            row.update(margin_pct={t: 100 * m for t, m in margins.items()}, min_margin_pct=100 * min(margins.values()),
                       fair_margin_pct=100 * margins["공정 기준(F1)"], ties=sorted(ties | flips), flips=sorted(flips),
                       cls="최선" if robust else "같은 수준")
            cells[f"{pk}/{c}"] = row
    return cells


def run():
    cases = run_cases()
    e38 = load_json("E38", "l1_e18_A25R_value_map")
    base = cases["E38 기준(셰딩 없음)"]
    dmax = 0.; same = True
    for pk, r in e38["packs"].items():
        for s, v in r["structs"].items():
            dmax = max(dmax, abs(v["loss"]["avg_W"] - base[pk]["loss"][s]))
        for c in CLASSES:
            same &= (r["best"][c]["best"] == base[pk]["best"][c] and sorted(r["best"][c]["feasible"]) == base[pk]["feas"][c])
    R0 = dmax <= TOL_REG and same
    verdict("(R0) 셰딩 끔 = E38 l1 가치 지도", R0, "최대 손실 차 %.2e W, 성립·최선 칸 %s" % (dmax, "같음" if same else "다름"))
    f41 = load_json("E41", "fair")["cases"]["공정 기준(F1)"]["drive_typ"]["5"]
    f42 = cases["공정 기준(F1)"]["spec"]["loss"]["1"]
    R1 = abs(f41 - f42) <= 0.05
    verdict("(R1) 공정 기준 사양 팩 ① = E41 ⑤", R1, "E42 %.3f W, E41 %.3f W" % (f42, f41))
    R2 = all(cases[t][pk]["feas"] == base[pk]["feas"] for t in cases for pk in base)
    verdict("(R2) 모든 경우의 성립 집합이 E38과 같음", R2, "")
    cells = judge_cells(cases)
    print("\n== 칸 판정(공정 기준) ==")
    for k, v in cells.items():
        if v["cls"] == "성립 없음":
            print("  %-12s 성립 없음" % k); continue
        if v["cls"] == "유일 성립":
            print("  %-12s 유일 성립: %s(%.1f W)" % (k, v["best_fair"], v["loss_fair"][v["best_fair"]])); continue
        print("  %-12s %s: %s %.1f W(E38 최선 %s) | 공정 여유 %.1f %%, 최소 여유 %.1f %% | 같은 수준 후보 %s"
              % (k, v["cls"], v["best_fair"], v["loss_fair"][v["best_fair"]], v["best_E38"], v["fair_margin_pct"],
                 v["min_margin_pct"], v["ties"]))
    W = {}
    for k, v in cells.items():
        b = v.get("best_fair")
        if b in ("W410", "W460", "4") or (v.get("cls") == "같은 수준" and set(v.get("ties", [])) & {"W410", "W460", "4"}):
            W[k] = dict(best=b, cls=v["cls"], ties=v.get("ties", []))
    save_json(EID, "cases", cases)
    save_json(EID, "cells", dict(cells=cells, wording=W, R0=dict(ok=R0, dmax_W=dmax, same_cells=same),
                                 R1=dict(ok=R1, E42=f42, E41=f41), R2=R2, band=BAND))
    verdict("E42 실행(칸 판정·문구 규칙 적용)", R0 and R1 and R2, "")


if __name__ == "__main__":
    parts = sys.argv[1:] or ["run"]
    for p in parts:
        {"run": run}[p]()
