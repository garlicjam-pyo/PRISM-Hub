"""[E45] 통합 수정안(2026-11-06, 기준 커밋 74e9437) 대응: 보존할 실패의 재확인(H2), 클램프 켬·끔 지연과 적분 간격,
가치 지도 후보 판정식 정정, 충전전력 정의, 180s 최저 버스, 비교기 강화, 작업자 상태 재현, P5·P8 사건 정보.

■ 왜 필요한가(사용자 지시 2026-11-06: 통합 수정안을 면밀히 검토해 오류가 없도록 수정)
  · H2 표의 '공차·지연 포함 전 시험 통과'는 원자료와 다르다(E7 복합 공차 Tier-2 평균모델 102/128).
  · E44 K는 클램프 켬·끔 지연을 1.0 µs로 고정했고 적분 간격 0.25 µs였다. 지연이 짧으면 켬 횟수가 늘어 열 선정 기준을 넘는
    반례(0.5 µs·폭 3.5 V 151.26 °C)가 보고되었다.
  · E42 judge_cells는 민감도 경우마다 명목 최저 구조 b와 후보를 비교해, b가 1위를 잃는 경우 실제 최저와 3 %를 넘게 차이 나는
    후보가 '같은 수준'에 들어갔다(200s/B470의 R2-W410).
  · Windows·macOS의 spawn 작업자는 부모가 바꾼 모듈 전역을 잃는다(E44 F, E35→E34, E36→E16). 코드는 common.Pool(fork 또는 같은
    프로세스 차례 실행)과 명시 인수(E16 Source.ra_mod, E34 _bus, model_stage_a.PLANT)로 고쳤다. 고친 코드가 저장 결과를 그대로
    내는지 확인한다.

■ 판정 기준(실행 전에 고정, 이 커밋. 결과를 본 뒤 바꾸지 않는다. 기존 E5–E44의 등록 판정과 원시 결과는 그대로 둔다)
 (h2) 재확인(새 판정 없음): E7 복합 공차 128 코너(Tier-1 +3.0 µs, Tier-2 +0 µs)와 E12 스위칭 같은 코너, E5 격자, E36 Tier-2 +3 µs
      정보 시험을 저장 자료에서 읽어 분모·최대값을 적는다. H2 원기준(docs/14: Tier-2 경로·필터 ≤ 93.75 A(평균모델), 공차 집합)을
      바꾸지 않는다. 평균모델 Tier-2 복합 공차가 128/128이 아니면 H2는 '부분 충족'으로 적는다.
 (vmap) 후속 재분류(새 규칙 V2, 원래 E42–E44 판정은 보존): 입력 = E44 fix_e42_cases + 스위칭 × 0.7·× 1.5를 fix_e43_loss e42.cases
      new로 바꾼 것. 규칙: 명목 최소 b가 모든 경우에서 그 경우의 차순위보다 3 %를 넘게 앞서면 '최선'(E42와 같음). 아니면
      '같은 수준' 후보 = 각 경우 t의 실제 최소 bt에 대해 (L_t(s) − L_t(bt))/L_t(s) ≤ 3 %인 s의 합집합(+ 1위가 된 구조). 성립 1개는
      '유일 성립'. 14칸 모두 다시 계산해 E43 L 칸과 비교한다.
 (power) 정의 계산(새 판정 없음): 충전기 명령 I = min(375 A, 150 kW/(V_bat/2))의 640·800·920 V 값, E38 l2의 375 A 고정 전력,
      팩별 P* = (V_bat/2)·I와 충전기 단자 P_ch = (V_bat/2 + R·I)·I(R = A25R 경로 5.25 mΩ), 각 정의로 150 kW에 필요한 전류와
      위상 수(위상당 ≤ 46.875 A, 2위상 단위).
 (s180) 확인(새 판정 없음): E44 fix_l1_e18_A25R 가치 지도의 180s·192s ④ 최저 버스와 Stage C 설계 입력 하한(E22 270 V).
 (dstrict) 비교기: common.strict_diff 자체 시험(키 삭제·문자열·NaN·길이·불리언·형·숫자 차를 모두 잡고 같은 값은 0)이 모두 맞아야
      한다. E44 D의 7쌍(E38 l1 3개·E41 fair·E42 cases·cells·E43 loss 대 r0_)을 엄격 비교해 차이 수를 적는다(차이가 있으면 그대로 보고).
 (delay) 클램프 켬·끔 지연과 적분 간격(E44 K의 최종 모서리: 사양 팩 ε +0.075 %·H 3.5 V·P−, W460 ε +1.0 %·H 4.0 V·P−, 큰·작은
      저항 섞임·작은 저항 조합 min·mix, 자기 가열 가정은 E43 값).
      1) 선별: 지연 1.0 µs·간격 0.25 µs로 모든 사건 × min·mix를 계산해 선정식 환산온도(E38 thermal) 상위 3개 (사건, 조합)을 고른다.
         재검토 반례 사건(사양 팩 640 V·R2·무부하·hold·t_comm 0·min)은 상위 3개에 없으면 더한다.
      2) 변형: (지연, H, 간격) = (1.0, H_min, 0.25), (1.0, H_min, 0.0625), (1.0, H_min, 0.03125), (0.5, H_min, 0.25),
         (0.5, H_min, 0.0625), (0.5, H_min, 0.03125), (0.5, H_min + 0.5, 0.0625). 켬 횟수, 평균 손실, 환산온도를 적는다.
      판정 D1: 지연 1.0 µs·간격 0.03125 µs에서 선택한 모든 사건의 환산온도 ≤ 150 °C이면 E44 K 요구는 '지연 1.0 µs 고정' 조건에서
         적분 간격에 대해 유지된다. 넘으면 그 팩의 요구는 '미해결(간격 수렴)'로 보고한다.
      판정 D2(보고): 지연 0.5 µs에서 150 °C를 넘는 사건이 있으면 '지연이 짧은 쪽의 반례'로 기록하고 요구 문구를 '시험 입력 지연
         1.0 µs 고정, 하드웨어 목표 ≤ 1 µs는 별도 검증'으로 한정한다(이 시험으로 지연 범위를 보장하지 않는다).
 (p5) 사건 정보(새 판정 없음): 위 선별 계산과 공칭(ε 0·H 5 V·N) 계산에서 선정식 환산온도와 평균 손실 최대(P = 켬·끔·도통 에너지 /
      첫 켬–마지막 끔 시간)를 팩별로 적는다.
 (brake) 사건 정보(새 판정 없음): E38 p6의 최대 제동 에너지 사건(W460_240s_930_MX_LA)을 같은 설정으로 다시 계산해 제동 펄스 수,
      첫 펄스–마지막 펄스 시간, 에너지를 적는다(저장 기록은 10 간격마다라 펄스 수는 이 해상도의 값).
 (repro) 작업자 상태 재현: PRISM_POOL=serial(같은 프로세스 차례 실행, spawn 플랫폼의 경로)로 다섯 대표 사례를 새로 계산한다:
      E44 F-a·F-b MA10_540V 과도(공칭 표본) 위상 첨두, F-b FG_920V_charge_m1 표본 1(첨두·턴오프 수·위반·V_A 범위), E35→E34 단일
      클램프 640 V R2 무부하 hold(가지 에너지·T_vj, C_A 2.4 mF), E36→E16 tau15us Tier-2 640 V 1→25 kW(링크 첨두, R_A 9.0 mΩ).
      판정 S1: 모든 값이 저장 결과와 상대 차 ≤ 1e-6, 정수는 같음.
 (fcheck) 고친 E44 cfly(model_stage_a.PLANT, common.Pool)를 다시 실행해 저장된 cfly.json의 과도 12 × 2·고장 16 × 2 = 56행과 엄격
      비교한다(실행 시간 제외). 판정 S2: 차이 0.

■ 실행   python E45_review4_response.py h2 vmap power s180 dstrict delay p5 brake repro fcheck   (2코어 약 1시간)
■ 결과   results/E45/*.json
"""
import json
import math
import os
import sys
import time

import numpy as np

from common import save_json, load_json, verdict, workers, Pool, strict_diff, strict_selftest, input_record

EID = "E45"
BAND = 0.03


def _root():
    from pathlib import Path
    return Path(__file__).resolve().parents[3]


# ======================================================================================================
# (h2)
# ======================================================================================================
def h2():
    val = _root() / "validation"
    out = {"source": "archived", "inputs": []}
    f7 = val / "2026-09-29-controller" / "corners.json"; f12 = val / "2026-10-11-matlab-switching" / "E12" / "corners.json"
    f5 = val / "2026-09-29-controller" / "grid.json"; fl = val / "2026-09-29-controller" / "corners_lh5.json"
    f36 = val / "2026-10-28-a25r-impact" / "E36" / "e16_concurrent.json"
    for f in (f7, f12, f5, fl, f36):
        out["inputs"].append(input_record(f, "archived"))
    c7 = json.loads(f7.read_text(encoding="utf-8"))["summary"]
    c12 = json.loads(f12.read_text(encoding="utf-8"))["summary"]
    lh = json.loads(fl.read_text(encoding="utf-8"))
    out["E7"] = {t: dict(total=c7[t]["total"], passed=c7[t]["passed"], max_path_A=c7[t]["worst"]["path_peak"],
                         delay_us=c7[t]["worst"]["added_delay_us"], step=[c7[t]["worst"]["p0"], c7[t]["worst"]["p1"]]) for t in ("T1", "T2")}
    out["E12"] = {t: dict(total=c12[t]["total"], passed=c12[t]["passed"], max_path_inst_A=c12[t]["worst"]["path_inst"]) for t in ("T1", "T2")}
    out["E7_lh5"] = dict(passed=lh["passed"], total=lh["total"], max_path_A=lh["max_path_A"])
    rows = json.loads(f5.read_text(encoding="utf-8"))["rows"]
    t1 = [r for r in rows if r.get("tier") == 1 and r["vbat"] >= 640]; t2 = [r for r in rows if r.get("tier") == 2 and r["vbat"] >= 640]
    out["E5_grid_640_920"] = dict(T1=[len(t1), sum(bool(r.get("pass_")) for r in t1)], T2=[len(t2), sum(bool(r.get("pass_")) for r in t2)],
                                  T1_max_A=max(r["path_peak"] for r in t1), T2_max_A=max(r["path_peak"] for r in t2))
    co = json.loads(f36.read_text(encoding="utf-8"))["summary"]
    out["E36_T2_delay"] = dict(n=co["concurrent|2|True"]["n"], passed=co["concurrent|2|True"]["passed"], failed=co["concurrent|2|True"]["failed"])
    out["H2"] = "부분 충족" if out["E7"]["T2"]["passed"] < out["E7"]["T2"]["total"] else "충족"
    save_json(EID, "h2", out)
    print(json.dumps({k: v for k, v in out.items() if k != "inputs"}, ensure_ascii=False, indent=1, default=float)[:2500])
    verdict("(h2) H2 판정 문구", True, out["H2"])


# ======================================================================================================
# (vmap)
# ======================================================================================================
def judge_cells_v2(cases, classes=("B_420", "B_470")):
    fair = cases["공정 기준(F1)"]
    sens = [t for t in cases if t not in ("E38 기준(셰딩 없음)",)]
    cells = {}
    for pk in fair:
        for c in classes:
            feas = fair[pk]["feas"][c]
            if not feas:
                cells[f"{pk}/{c}"] = dict(cls="성립 없음"); continue
            L = fair[pk]["loss"]
            b = min(feas, key=lambda s: L[s])
            row = dict(feasible=feas, best_fair=b, loss_fair={s: L[s] for s in feas})
            if len(feas) == 1:
                row["cls"] = "유일 성립"; cells[f"{pk}/{c}"] = row; continue
            ties, flips, margins, rel = set(), set(), {}, {}
            for t in sens:
                Lt = cases[t][pk]["loss"]
                bt = min(feas, key=lambda s: Lt[s])
                if bt != b:
                    flips.add(bt)
                others = [s for s in feas if s != b]
                st = min(others, key=lambda s: Lt[s])
                margins[t] = (Lt[st] - Lt[b]) / Lt[st]
                for s in feas:
                    if s == bt:
                        rel[s] = min(rel.get(s, 9.), 0.)      # (2026-11-06 E46) 그 경우의 최소이면 0을 기록(이전에는 건너뜀)
                        continue
                    r = (Lt[s] - Lt[bt]) / Lt[s]
                    rel[s] = min(rel.get(s, 9.), r)
                    if r <= BAND:
                        ties.add(s)
            robust = not flips and all(m > BAND for m in margins.values())
            row.update(margin_pct={t: 100 * m for t, m in margins.items()}, min_margin_pct=100 * min(margins.values()),
                       fair_margin_pct=100 * margins["공정 기준(F1)"], ties=sorted((ties | flips) - {b}), flips=sorted(flips),
                       min_rel_to_case_best_pct={s: 100 * v for s, v in rel.items()}, cls="최선" if robust else "같은 수준")
            cells[f"{pk}/{c}"] = row
    return cells


def vmap():
    cs = load_json("E44", "fix_e42_cases")
    e43 = load_json("E44", "fix_e43_loss")
    for t in ("스위칭 × 0.7", "스위칭 × 1.5"):
        cs[t] = e43["e42"]["cases"][t]["new"]
    v2 = judge_cells_v2(cs)
    old = e43["e42"]["cells"]
    changes = {}
    for k, r in v2.items():
        o = old.get(k, {})
        a = (o.get("cls"), o.get("best_fair"), sorted(o.get("ties", [])))
        b = (r.get("cls"), r.get("best_fair"), r.get("ties", []))
        if a != b:
            changes[k] = dict(old=a, new=b, min_rel_pct=r.get("min_rel_to_case_best_pct"))
            print("  %-12s %s → %s(실제 최저 대비 최소 상대 차 %s)" % (k, a, b, {s: round(v, 2) for s, v in (r.get("min_rel_to_case_best_pct") or {}).items()}))
    save_json(EID, "vmap", dict(rule="V2: 경우별 실제 최저 bt 기준 3 % 합집합", cells=v2, changes=changes, n_cells=len(v2)))
    verdict("(vmap) 14칸 재분류(분류·명목 최저 불변, 후보 목록 변화 %d칸)" % len(changes),
            all(changes[k]["old"][0] == changes[k]["new"][0] and changes[k]["old"][1] == changes[k]["new"][1] for k in changes), "")


# ======================================================================================================
# (power)
# ======================================================================================================
def power():
    R = 9.0e-3 / 4 + 3e-3
    IPH = 375. / 8
    cmd = {V: min(375., 150e3 / (V / 2)) for V in (640., 800., 920.)}
    out = dict(R_ohm=R, I_phase_max=IPH, charger_cmd={str(int(V)): dict(I_A=i, P_half_kW=i * V / 2 / 1e3) for V, i in cmd.items()},
               loss_compare_375A_kW={str(int(V)): 375. * V / 2 / 1e3 for V in (640., 800., 920.)})

    def phases(I):
        n = math.ceil(I / IPH - 1e-12)
        return n + (n % 2)
    packs = {"180s": 180, "192s": 192, "200s": 200, "216s": 216, "224s": 224, "240s": 240}
    rows = {}
    for pk, ns in packs.items():
        Vh = ns * 3.7 / 2
        I_star = 150e3 / Vh
        I_ch = (-Vh + math.sqrt(Vh * Vh + 4 * R * 150e3)) / (2 * R)
        rows[pk] = dict(V_half=Vh, P_star_375_kW=Vh * 375. / 1e3, P_ch_375_kW=(Vh + R * 375.) * 375. / 1e3,
                        I_for_Pstar150_A=I_star, n_ph_Pstar=phases(I_star), I_for_Pch150_A=I_ch, n_ph_Pch=phases(I_ch))
        print("  %s: V/2 %.1f V, 375 A에서 P* %.3f·P_ch %.3f kW; 150 kW에 P* %.3f A(%d위상), P_ch %.3f A(%d위상)"
              % (pk, Vh, rows[pk]["P_star_375_kW"], rows[pk]["P_ch_375_kW"], I_star, rows[pk]["n_ph_Pstar"], I_ch, rows[pk]["n_ph_Pch"]))
    out["packs"] = rows
    l2 = json.loads((_root() / "validation" / "2026-10-29-review-response" / "E38" / "l2.json").read_text(encoding="utf-8"))
    out["E38_l2"] = [dict(pack=x["pack"], P_kW=x["P_kW"], nph=x["nph"], I_A=x["iph"] * x["nph"]) for x in l2["rows"]]
    save_json(EID, "power", out)
    print("  충전기 명령:", {k: (round(v["I_A"], 1), round(v["P_half_kW"], 1)) for k, v in out["charger_cmd"].items()})


# ======================================================================================================
# (s180)
# ======================================================================================================
def s180():
    import E22_stage_c_regulated as E22
    vm = load_json("E44", "fix_l1_e18_A25R_value_map")
    out = dict(stageC_vin_min=E22.VBUS[0])
    for pk in ("180s", "192s"):
        for c in ("B_420", "B_470"):
            f = vm["packs"][pk]["structs"]["4"]["feas"][c]
            out[f"{pk}/{c}"] = dict(bus_V=f.get("bus_V"), ok=f.get("ok"))
    save_json(EID, "s180", out)
    print(json.dumps(out, ensure_ascii=False, default=float)[:800])


# ======================================================================================================
# (dstrict)
# ======================================================================================================
def dstrict():
    st = strict_selftest()
    pairs = [(("E38", "l1_e15_comparison"), "r0_l1_e15_comparison"), (("E38", "l1_e25_comparison"), "r0_l1_e25_comparison"),
             (("E38", "l1_e18_A25R_value_map"), "r0_l1_e18_A25R_value_map"), (("E41", "fair"), "r0_e41_fair"),
             (("E42", "cases"), "r0_e42_cases"), (("E42", "cells"), "r0_e42_cells"), (("E43", "loss"), "r0_e43_loss")]
    res = {}
    for (eid, name), mine in pairs:
        d = strict_diff(load_json(eid, name), load_json("E44", mine))
        res["%s/%s" % (eid, name)] = dict(n=len(d), first=[list(map(str, x)) for x in d[:5]])
    save_json(EID, "dstrict", dict(selftest=st, pairs=res))
    print("  자체 시험:", st); print("  7쌍:", {k: v["n"] for k, v in res.items()})
    verdict("(dstrict) 비교기 자체 시험", all(st.values()), "")
    verdict("(dstrict) E44 D 7쌍 엄격 비교 차이 0", all(v["n"] == 0 for v in res.values()), "")


# ======================================================================================================
# (delay)·(p5)
# ======================================================================================================
CORNER = {"spec": dict(eps=0.00075, H=3.5, pas="P-"), "W460": dict(eps=0.01, H=4.0, pas="P-")}
NOMINAL = dict(eps=0.0, H=5.0, pas="N")
VARIANTS = [(1.0e-6, 0.0, 0.25e-6), (1.0e-6, 0.0, 0.0625e-6), (1.0e-6, 0.0, 0.03125e-6), (0.5e-6, 0.0, 0.25e-6),
            (0.5e-6, 0.0, 0.0625e-6), (0.5e-6, 0.0, 0.03125e-6), (0.5e-6, 0.5, 0.0625e-6)]


def _ev45(args):
    dt, a44 = args
    import E26_charging_stop as E26
    import E44_review3_response as E44
    E26.DT = dt
    try:
        return E44._ev44(a44)
    finally:
        E26.DT = 0.25e-6


def _setup(part):
    import E44_review3_response as E44
    return E44._setup_part(part)


def _jobs(P, corner, combos, events, delay=1.0e-6, dt=0.25e-6, dH=0.0):
    import E40_typ_rule_rejudge as E40
    import E44_review3_response as E44
    on = P["cfg"]["on"] * (1 + corner["eps"]); off = on - (corner["H"] + dH)
    cbs = {k: v for k, v in E40.combos40(P["sel"]["n"], P["c"], P["vd"]).items() if k in combos}
    jobs = []
    for cb, br in cbs.items():
        for i, e in events:
            jobs.append(((cb, i), (dt, (br, on, off, e, dict(t_on_max=E40.T_ON_MAX, delay=delay), E44.PASSIVE[corner["pas"]]))))
    return jobs


def _therm(P, rows):
    import E38_review_response as E38
    sw = P["sw"][P["swn"]]
    th = E38.thermal(list(rows.values()), sw)
    n_on = max(r["n_on"] for r in rows.values())
    return dict(T=th.get("T"), P=th.get("P"), n_on=n_on, E_on=th.get("E_on"), E_off=th.get("E_off"), E_cond=th.get("E_cond"),
                vmax=max(max(r["vA_max"], r["vb_max"]) for r in rows.values()), E_branch=max(r["E_branch_J"] for r in rows.values()))


def _run(jobs):
    with Pool(workers()) as p:
        res = p.map(_ev45, [j[1] for j in jobs], chunksize=1)
    return {j[0]: r for j, r in zip(jobs, res)}


def delay():
    out = {}
    for part in ("spec", "W460"):
        P = _setup(part)
        evs = list(enumerate(P["evf"]()))
        t0 = time.time()
        scr = _run(_jobs(P, CORNER[part], ("min", "mix"), evs))
        th = {k: _therm(P, r) for k, r in scr.items()}
        top = sorted(th, key=lambda k: -th[k]["T"])[:3]
        if part == "spec":
            idx = next(i for i, e in evs if e["Vbat"] == 640. and e["arch"] == "R2" and e["P400"] == 0. and e["PC"] == 0.
                       and e["prof"] == "hold" and e["t_comm"] == 0.)
            if ("min", idx) not in top:
                top.append(("min", idx))
        print("  == %s 선별(%.0f s): 상위 %s" % (part, time.time() - t0, [(k, round(th[k]["T"], 2), th[k]["n_on"]) for k in top]), flush=True)
        var = {}
        for (cb, i) in top:
            e = dict(evs)[i]
            jobs = []
            for (d, dH, dt) in VARIANTS:
                jobs += [((d, dH, dt), j[1]) for j in _jobs(P, CORNER[part], (cb,), [(i, e)], d, dt, dH)]
            rr = _run(jobs)
            var["%s|%d" % (cb, i)] = dict(event=e, combo=cb, rows=[dict(delay_us=k[0] * 1e6, H=CORNER[part]["H"] + k[1], dt_us=k[2] * 1e6,
                                                                         **_therm(P, r)) for k, r in rr.items()])
            for x in var["%s|%d" % (cb, i)]["rows"]:
                print("   %s %s: 지연 %.2f µs H %.1f V 간격 %.5f µs → 켬 %d번, P %.1f W, %.2f °C, V %.3f V"
                      % (part, (cb, i, e["Vbat"], e["arch"], e["P400"], e["prof"], e["t_comm"]), x["delay_us"], x["H"], x["dt_us"],
                         x["n_on"], x["P"], x["T"], x["vmax"]), flush=True)
        d1 = all(x["T"] <= 150. for v in var.values() for x in v["rows"] if x["delay_us"] == 1.0 and abs(x["dt_us"] - 0.03125) < 1e-9)
        d2 = [dict(key=k, **x) for k, v in var.items() for x in v["rows"] if x["delay_us"] == 0.5 and x["T"] > 150.]
        out[part] = dict(corner=CORNER[part], screening={"%s|%d" % k: v for k, v in th.items()}, top=["%s|%d" % k for k in top],
                         variants=var, D1=d1, D2_counterexamples=d2)
        verdict("(delay D1) %s: 지연 1.0 µs·간격 0.03125 µs에서 선택 사건 ≤ 150 °C" % part, d1, "")
        verdict("(delay D2) %s: 지연 0.5 µs 반례 %d건" % (part, len(d2)), True, "")
        save_json(EID, "delay", out)


def p5():
    out = {}
    for part in ("spec", "W460"):
        P = _setup(part)
        evs = list(enumerate(P["evf"]()))
        res = {}
        for tag, corner in (("corner", CORNER[part]), ("nominal", NOMINAL)):
            th = {k: _therm(P, r) for k, r in _run(_jobs(P, corner, ("min", "mix"), evs)).items()}
            kT = max(th, key=lambda k: th[k]["T"]); kP = max(th, key=lambda k: th[k]["P"])
            res[tag] = dict(corner=corner, T_max=th[kT]["T"], T_event=dict(evs)[kT[1]], T_combo=kT[0], P_at_Tmax=th[kT]["P"],
                            P_max=th[kP]["P"], P_event=dict(evs)[kP[1]], P_combo=kP[0],
                            sw_share_at_Tmax=(th[kT]["E_on"] + th[kT]["E_off"]) / max(th[kT]["E_on"] + th[kT]["E_off"] + th[kT]["E_cond"], 1e-12))
            print("  %s %s: 환산온도 최대 %.2f °C(평균 손실 %.1f W, 스위칭 비중 %.0f %%), 평균 손실 최대 %.1f W"
                  % (part, tag, res[tag]["T_max"], res[tag]["P_at_Tmax"], 100 * res[tag]["sw_share_at_Tmax"], res[tag]["P_max"]), flush=True)
        out[part] = res
    save_json(EID, "p5", out)


# ======================================================================================================
# (brake)
# ======================================================================================================
def brake():
    import E17_protection_integration as E17
    import E29_sals_degradation as E29
    import E38_review_response as E38          # noqa: F401  (p6와 같은 모듈 설정)
    tag = "W460_240s_930_MX_LA"
    job = next(j for j in E29.seq_jobs() if j["_tag"] == tag)
    job = dict(job); job.pop("_tag"); job.pop("_extra"); job["sc_pause"] = True
    m = E17.r2_run(job)
    t = np.asarray(m["trace"]["t"]); pb = np.asarray(m["trace"]["log"])[:, 9]
    on = pb > 0
    k_on = np.flatnonzero(~on[:-1] & on[1:]) + 1
    k_off = np.flatnonzero(on[:-1] & ~on[1:]) + 1
    if on[0]:
        k_on = np.r_[0, k_on]
    span = float(t[k_off[-1]] - t[k_on[0]]) if len(k_on) and len(k_off) else 0.
    out = dict(tag=tag, brk_energy_J=m.get("brk_energy_J"), stored_J=51.87535912196788, n_pulses=int(len(k_on)), span_ms=1e3 * span,
               first_ms=float(1e3 * (t[k_on[0]] - E17.T_EV)) if len(k_on) else None, trace_step_s=float(t[1] - t[0]),
               P_peak_kW=float(pb.max() / 1e3))
    save_json(EID, "brake", out)
    print(json.dumps(out, ensure_ascii=False))


# ======================================================================================================
# (repro)
# ======================================================================================================
def _rel(a, b):
    return abs(a - b) / max(1., abs(a))


def repro():
    """(2026-11-06 E46 정정) 1차 실행은 PRISM_POOL=serial을 되돌리지 않아, 같은 프로세스에서 이어 실행한 fcheck도 같은 프로세스 차례
    실행이었다. 이제 끝에서 원래 값으로 되돌린다."""
    prev = os.environ.get("PRISM_POOL")
    os.environ["PRISM_POOL"] = "serial"
    try:
        _repro()
    finally:
        if prev is None:
            os.environ.pop("PRISM_POOL", None)
        else:
            os.environ["PRISM_POOL"] = prev


def _repro():
    import model_stage_a as A
    import E35_a25r_verify as E35
    import E33_stage_a_25k_dynamics as E33
    import E34_parts_rating as E34
    import E26_charging_stop as E26
    stored_f = load_json("E44", "cfly")
    checks = []
    base = A.DESIGNS["A25"]["Cfly"]
    for tag, C in (("F-a_45.00uF", 45.0e-6), ("F-b_42.75uF", 42.75e-6)):
        A.DESIGNS["A25"]["Cfly"] = 45.0e-6; A.PLANT.clear(); A.PLANT["Cfly"] = C
        try:
            m = E35._tr(("MA10_540V_bus_5_15_5kW", None))
            ref = next(x for x in stored_f[tag]["transient"] if x["case"] == "MA10_540V_bus_5_15_5kW" and x["seed"] is None)
            checks.append(dict(name="%s MA10 위상 첨두" % tag, new=m["phase_peak"], stored=ref["phase_peak"]))
            if tag.startswith("F-b"):
                f = E33._fault(("FG_920V_charge_m1", 1))
                ref = next(x for x in stored_f[tag]["fault"] if x["case"] == "FG_920V_charge_m1" and x["seed"] == 1)
                for k in ("phase_peak", "n_turnoff", "n_bad"):
                    checks.append(dict(name="%s FG_920V 표본 1 %s" % (tag, k), new=f[k], stored=ref[k]))
                checks.append(dict(name="%s FG_920V V_A 최소" % tag, new=f["vA"][0], stored=ref["vA"][0]))
                checks.append(dict(name="%s FG_920V V_A 최대" % tag, new=f["vA"][1], stored=ref["vA"][1]))
        finally:
            A.PLANT.clear(); A.DESIGNS["A25"]["Cfly"] = base
    # E35 → E34 단일 클램프
    ev = next(e for e in E26.EVENTS if e["clamp"] and not e.get("nmod_after") and e["Vbat"] == 640. and e["arch"] == "R2"
              and e["P400"] == 0. and e["PC"] == 0. and e["prof"] == "hold" and e["t_comm"] == 0.)
    E26.BUS.clear(); E26.BUS.update(E26.BUS_DEFAULT)                     # 부모 전역을 일부러 기본(0.4 mF)으로 둔다
    r = E34._clamp(dict(ev, _bus=dict(CA=E35.CA_R)))
    ref = next(x for x in load_json("E35", "clamp")["rows"] if x["arch"] == "R2" and x["Vbat"] == 640. and x["P400"] == 0. and x["PC"] == 0.
               and x["prof"] == "hold" and x["t_comm"] == 0.)
    checks.append(dict(name="E35→E34 가지 에너지", new=r["E_clamp_J"], stored=ref["E_clamp_J"]))
    checks.append(dict(name="E35→E34 T_vj", new=r["Tvj_C"], stored=ref["Tvj_C"]))
    # E36 → E16
    import E16_charging_integration as E16
    import E36_a25r_impact as E36
    E16.RA_MOD = E36.RA_A25
    js = [j for j in E16.concurrent_jobs() if j[1] == "tau15us" and j[2] == 2 and j[3] == 640. and j[7] == dict(P0=1000, P1=25000)]
    row = E16.run_case(js[0])
    E16.RA_MOD = 10.2e-3
    co = json.loads((_root() / "validation" / "2026-10-28-a25r-impact" / "E36" / "e16_concurrent.json").read_text(encoding="utf-8"))
    ref = next(x for x in co["rows"] if x["name"] == "tau15us" and x["tier"] == 2 and x["V"] == 640. and x["info"] == dict(P0=1000, P1=25000))
    checks.append(dict(name="E36→E16 tau15us 링크 첨두", new=row["dab_power_peak"], stored=ref["dab_power_peak"]))
    checks.append(dict(name="E36→E16 R_A", new=row["ra_mod"], stored=E36.RA_A25))
    for c in checks:
        c["rel"] = _rel(float(c["stored"]), float(c["new"]))
        print("  %-34s 새 %.6f / 저장 %.6f (상대 차 %.1e)" % (c["name"], float(c["new"]), float(c["stored"]), c["rel"]), flush=True)
    ok = all(c["rel"] <= 1e-6 for c in checks)
    save_json(EID, "repro", dict(pool="serial", checks=checks, S1=ok))
    verdict("(repro S1) 같은 프로세스 차례 실행에서 대표 사례가 저장 결과와 같음", ok, "%d개" % len(checks), gate=True)


# ======================================================================================================
# (fcheck)
# ======================================================================================================
def fcheck():
    import E44_review3_response as E44
    import common
    captured = {}
    E44.save_json = lambda eid, name, obj: captured.__setitem__(name, obj)
    E44.cfly()
    new = dict(captured["cfly"])
    new["_meta"] = dict(compute_pool=common.pool_mode(), workers=common.workers())     # (E46) 물리 계산의 실행 방식
    save_json(EID, "cfly_refactor", new)
    _fcheck_compare(first_run=True)


# (2026-11-06 E46, 두 번째 통합 검토 V02) S2 필수 조건. 엄격 비교만으로는 두 파일에서 같은 행을 지우거나(55행), 비교 대상이 아닌
# 설정(제어 주파수)을 바꿔도 통과했다. 사례 이름 56개 전부·각 사례의 설계/플랜트 주파수를 등록값과 따로 확인한다.
FCHECK_TAGS = ("F-a_45.00uF", "F-b_42.75uF")
FCHECK_N = dict(transient=12, fault=16)                  # 사례당 행 수(요구 안 과도 6사례 × 표본 2, 고장 8사례 × 표본 2)
FCHECK_F_HZ = {"F-a_45.00uF": (25515.627843745686, 25515.627843745686), "F-b_42.75uF": (25515.627843745686, 26178.481807544278)}


def fcheck_judge(old, new):
    """old·new(JSON에서 읽은 E44 cfly 형식)를 비교해 (ok, 상세)를 돌려준다. 파일 경로와 무관한 순수 함수(E46 gate가 오류 주입에 쓴다)."""
    diffs, problems, n_rows = {}, [], 0
    for tag in FCHECK_TAGS:
        if tag not in old or tag not in new:
            problems.append("사례 묶음 없음: %s" % tag); continue
        for part, n in FCHECK_N.items():
            o, w = old[tag].get(part, []), new[tag].get(part, [])
            keys_o = sorted((x.get("case"), str(x.get("seed"))) for x in o)
            keys_w = sorted((x.get("case"), str(x.get("seed"))) for x in w)
            if len(o) != n or len(w) != n:
                problems.append("%s/%s 행 수 %d·%d(필수 %d)" % (tag, part, len(o), len(w), n))
            if keys_o != keys_w:
                problems.append("%s/%s 사례·표본 이름 불일치" % (tag, part))
            n_rows += min(len(o), len(w))
            d = strict_diff(o, w)
            diffs["%s/%s" % (tag, part)] = dict(n=len(d), first=[list(map(str, x)) for x in d[:5]])
        fc, fp = FCHECK_F_HZ[tag]
        for k, ref in (("f_control_Hz", fc), ("f_plant_Hz", fp)):
            v = new[tag].get(k)
            if v is None or abs(float(v) - ref) > 1e-9 * ref:
                problems.append("%s %s = %s(등록 %.6f)" % (tag, k, v, ref))
    if n_rows != 56:
        problems.append("비교 행 %d(필수 56)" % n_rows)
    ok = not problems and all(v["n"] == 0 for v in diffs.values())
    return ok, dict(rows=n_rows, diffs=diffs, problems=problems)


def _fcheck_compare(first_run=False):
    """(2026-11-06 실행 경과) 1차 fcheck는 직렬화 전 객체(정수 키·튜플)를 JSON에서 읽은 저장 결과(문자열 키·리스트)와 비교해
    형 차이만으로 실패했다. 판정 기준(엄격 비교 차 0)은 그대로 두고, 저장 결과와 같은 경로(save_json → load_json)로 읽은 새 결과를 비교한다."""
    import common
    new = load_json(EID, "cfly_refactor"); old = load_json("E44", "cfly")
    ok, det = fcheck_judge(old, new)
    meta = new.get("_meta", {})
    save_json(EID, "fcheck", dict(rows=det["rows"], diffs=det["diffs"], problems=det["problems"], S2=ok,
                                  compute_pool=meta.get("compute_pool", "기록 없음(1차 실행은 repro가 PRISM_POOL=serial을 되돌리지 않아 같은 프로세스 차례 실행)"),
                                  judge_pool=common.pool_mode(), compared="save_json → load_json 경로(직렬화 뒤)",
                                  first_run_failed_on_serialization=not first_run,
                                  f_Hz={t: [new[t]["f_control_Hz"], new[t]["f_plant_Hz"]] for t in FCHECK_TAGS if t in new}))
    verdict("(fcheck S2) 고친 E44 cfly가 저장 결과 %d행과 같음(필수 56행·사례 이름·설계/플랜트 주파수 포함)" % det["rows"], ok,
            json.dumps(dict({k: v["n"] for k, v in det["diffs"].items()}, problems=det["problems"]), ensure_ascii=False), gate=True)


def fcheck_rejudge():
    """저장된 cfly_refactor.json으로 S2를 다시 판정한다(다시 계산하지 않음)."""
    _fcheck_compare(first_run=False)


PARTS = dict(h2=h2, vmap=vmap, power=power, s180=s180, dstrict=dstrict, delay=delay, p5=p5, brake=brake, repro=repro, fcheck=fcheck,
             fcheck_rejudge=fcheck_rejudge)

if __name__ == "__main__":
    want = sys.argv[1:] or list(PARTS)
    for w in want:
        if w not in PARTS:
            raise SystemExit("알 수 없는 부분: %s (가능: %s)" % (w, ", ".join(PARTS)))
    for w in want:
        print("\n==== E45 %s ====" % w, flush=True)
        PARTS[w]()
    import common as _c
    sys.exit(_c.exit_status())
