"""[E44] 제출 전 재검토(2026-11-06) 대응: 비교 소자 데이터시트 조건 정정의 연쇄 재계산(D), 클램프의 버스 수동소자 공차와
켬·끔 문턱 추종 오차(K), 플라잉 커패시터 후보값 확인(F), 기존 결과의 판정 범위 재분석(R).

■ 왜 필요한가(재검토 2026-11-06, 검토 커밋 7a36f30. 사용자 지시 2026-11-06: 재검토 내용을 참고해 수정)
  (D) E15의 1200 V SiC MOSFET C3M0016120K는 E_oss 127 µJ를 800 V 값으로 두었지만, 제조사 데이터시트(Rev. 5)에서 127 µJ는
      V_DS = 1000 V 값이다(전기 특성표 C_oss 묶음 조건 V_DS 1000 V, 그림 16 곡선; 800 V에서 약 85 µJ). E_on·E_off(2,552·788 µJ)는
      800 V·80 A 값이라 한 소자에 시험 전압이 다른 값이 섞였다. 비교에 쓰는 다른 소자(UJ4SC075006K4S, GS66516T, EPC2305,
      C4MS008075U2, 클램프 FF2MR12KM1P·CAB530M12BM3)의 값과 시험 조건도 데이터시트와 대조했고, 시험 전압이 틀린 값은 이것 하나였다
      (조건이 주석에 빠진 항목·곡선으로만 확인되는 가정값은 docs/49에 적는다). 정정한 값으로 이 값에 기대는 결과(H5 비교 E38 l1,
      공정 비교 E41, 가치 지도 E42, 일관된 스위칭 배율 E43 L)를 같은 규칙으로 다시 계산한다.
  (K) E43 (H)는 켬·끔 문턱에 같은 상대오차를 곱하고(공통 오차) 버스 수동소자를 공칭으로 두었다. 재검토 진단에서 (1) 사양 팩 문턱
      +0.10 %에 C_A·C_b·R_d·C_d 90 %·배선 L 110 %를 함께 주면 버스가 470.04 V(상한 470 V)였고, (2) 켬만 −0.5 %(끔 공칭, 히스테리시스
      2.66 V)이면 클램프 스위치가 157.6 °C(한도 150 °C)였다. 수동소자 공차와 문턱 간 추종 오차를 넣은 구현 요구를 정하고 결합 모서리로
      다시 판정한다.
  (F) 플라잉 커패시터 후보(CC7.5u1300 × 6 = 45.0 µF)는 해석값 46.875 µF보다 4 % 작고, 이 값과 제조 공차로 동특성을 다시 확인하지
      않았다(재검토는 대표 1사례만 실행).
  (R) 이미 있는 결과의 판정 범위: H4 승인 지연(손실 없음/손실 조건), H1 충전 링크전력(사양 안 정식/정보/632 V 경계), 팩별 150 kW
      충전 손실의 위상 수, 500 V 충전기 만충 직렬수(A25R 경로저항), TB28 관찰 범위, Stage A 첨두의 설계 세대(A25 → A25R).

■ 판정 기준(실행 전에 고정, 이 커밋. 결과를 본 뒤 바꾸지 않는다)
 (D) 소자 값 정정의 연쇄 재계산
  정정: DEV_FIX의 값만 바꾼다(전압 지수 1.5와 E_on + E_off의 기준점 합은 그대로). 판정 규칙은 원 시험과 같다: H5(E15 judge),
      E41 W1(3 % 동등범위, 같은 수준/견고)·W2·W3, E42 칸 판정(judge_cells, 3 %), E43 L(Stage A 출력용량 항 배율). E25 결론 문장 비교.
  순서: E38 l1(H5·E25·E18 가치 지도, Stage C 최종 설계) → E41 run → E42 run → E43 loss. 정정 없음(r0_)과 정정(fix_)을 각각 새 프로세스로
      계산한다(모듈 다시 읽기의 부작용을 피함). 결과는 results/E44/의 r0_*, fix_*.
  확인: (D-R0) 정정 없이 같은 순서로 계산한 값이 E38 l1·E41·E42·E43 저장값과 같음(모든 숫자의 상대 차 ≤ 1e-6, 실행 시간 항목 제외).
  보고 규칙: 판정(같은 수준/최선/유일 성립, H5 기각 여부, E25 문장)이 바뀌면 바뀐 대로, 명목 순서·동급 후보가 바뀌면 그대로 적는다.
 (K) 클램프 구현 요구(사양 팩: 가지 3 × 2.4 Ω, W460: 3 × 2.7 Ω, 스위치 FF2MR12KM1P, 최대 연속 켜짐 0.5 ms — E40 선정 그대로)
  문턱 모델: 켬 = on0·(1 + ε), 끔 = 켬 − H(히스테리시스 폭, 공칭 H0 = 5 V). ε = 공통 오차, H = 추종 오차를 담는 폭.
  수동소자 모서리: N(공칭), P−(C_A·C_b·C_d·R_d × 0.9, 배선 L × 1.1), P+(× 1.1, L × 0.9). 배선 저항은 공칭.
  자기 가열 가정: E43 (H) 최종값(results/E43/heat.json)에서 시작.
  (K1) 상한 공통 오차 X: H = H0·(1 + ε)(E43과 같은 공통 오차), 큰 저항 조합(max), 모든 사건, P−·P+에서 C1(V_A·버스 ≤ 상한)과
       E(가지 ≤ 15 kJ). 후보 ε: 사양 팩 0, +0.025, +0.05, +0.075, +0.10 %, W460 0, +0.25, +0.5, +0.75, +1.0 %.
       X = 0부터 차례로 통과한 최대 후보(앞 후보가 불통과면 거기서 멈춤). 0도 불통과면 음의 후보(사양 팩 −0.025, −0.05, −0.075,
       −0.10 %, W460 −0.25 … −1.0 %)를 차례로 보고 처음 통과한 값을 X로 한다(이때는 공칭 켬 문턱을 낮춰야 한다는 뜻이며 그대로 보고).
  (K2) 최소 히스테리시스 H_min: 수동소자 N, 작은 저항·섞임 조합(min, mix), 모든 사건, ε ∈ {−1.0 %, 0, X}에서 C1·E·스위치(I·V·T,
       E39 judge39 ok). 후보 H: 6.0, 4.5, 4.0, 3.5, 3.0 V(5.0 V는 E43). H_min = 5.0 V부터 작은 쪽으로 차례로 모든 ε에서 통과한 최소 후보.
       6.0 V도 통과해야 한다(통과하지 않으면 위쪽 한계도 보고).
  (K3) 확인: 모든 사건 × 세 조합 × 모서리 {ε: −1.0 %, X} × {H: H_min, 6.0 V} × {P−, P+}에서 C1·E·스위치·자기 가열 가정(S: 관측이 가정을
       넘으면 50 J 단위로 올려 최대 2번 다시 실행). 같은 모서리 {ε −1.0 %} × {H_min, 6.0} × {P−, P+}에서 E40 낮은 쪽 오동작 사건
       (강제 켬, 최대 연속 켜짐 있음): M1(0.5 ms 안에 끄고 다시 켜지지 않음), M2(에너지·전류·전압), M3(0.2 ms 이상 켜짐이면 접합 온도).
       모두 통과하면 요구 = "켬·끔 공통 오차 −1.0 … +X, 히스테리시스 폭 H_min–6.0 V, 버스 수동소자 ±10 %·배선 L ±10 % 안".
       불통과면 X를 한 단계 낮추거나 H_min을 한 단계 올려(불통과 항목이 C1·E이면 X, 스위치·오동작이면 H_min) K3을 다시 한다(최대 2번).
       그래도 불통과면 미해결로 보고한다.
 (F) 플라잉 커패시터: A25R(E35 configure)에서 (F-a) 설계값 45.0 µF(후보 공칭; 제어 주기·판정 시간도 이 값의 f_r), (F-b) 실제 42.75 µF
      (후보 −5 %)·제어 주기와 판정 시간은 45.0 µF 설계 그대로. L_r, 문턱(E32), P_rated(E32)는 그대로. E35의 요구 안 과도 6사례 × 2표본과
      모듈 고장 16사례를 E35와 같은 판정(T1–T4, F1–F4)으로 본다. 둘 다 모두 통과하면 P2 단서 '용량 −4 % 재검증 없음'을 거둔다.
      불통과면 불통과로 보고한다.
 (R) 재분석(새 판정 없음, 원 기준 그대로): H4 = E8 sals 결과의 손실 없음 최대·손실 조건 99 %·최대(기준 25·50 ms), H1 = E36 e16_static·
      concurrent에서 640–920 V 정식/정보/632 V 경계별 최대, 팩별 150 kW 위상 수(E38 l2), 500 V 충전기 만충 셀 직렬수
      (경로저항 = A25R 4모듈 9.0/4 mΩ + 배선 3 mΩ), TB28 관찰 시간·버스 감소·48 V 범위(CSV), Stage A 위상 첨두(E35 요구 안·고장·금지).

■ 실행 뒤 추가(2026-11-06, dev 결과를 본 뒤; 판정 없는 부속 재계산): bkv = 손익분기 상저항(E36_breakeven_grid와 같은 식·격자)을
  정정 소자값으로 다시 계산한다. 보고서의 "격자의 모든 모터 승압 조합보다 작아지는 상저항" 숫자를 바꾸기 위한 것이다.
■ 실행   python E44_review3_response.py scope dev clamp cfly    (2코어: dev 약 30분, clamp 약 3시간, cfly 약 1–2시간)
         clamp는 clamp:spec, clamp:W460으로 나눠 실행할 수 있다(결과는 같은 clamp.json에 모음).
■ 결과   results/E44/*.json
"""
import json
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np

from common import save_json, load_json, verdict, workers

EID = "E44"

# ======================================================================================================
# (D) 소자 값 정정
# ======================================================================================================
DEV_FIX = {
    "SiC1200": dict(Voss=1000.),       # C3M0016120K Rev. 5: E_oss 127 µJ는 V_DS 1000 V 값(C_oss 묶음 조건, 그림 16)
}
SKIP_KEYS = ("sec", "wall_s", "elapsed", "time_s")


def _redirect(mod, mapping, prefix):
    """mod 안의 load_json·save_json을 바꾼다. mapping: {(eid, name): (eid2, name2)}. prefix: E44에 저장할 때 붙일 이름 앞부분."""
    import common
    mod.load_json = lambda eid, name: common.load_json(*mapping.get((eid, name), (eid, name)))
    mod.save_json = lambda eid, name, obj: common.save_json(EID, prefix + name, obj)
    mod.EID = EID


def chain(tag):
    """새 프로세스에서 호출: tag 'r0_'(정정 없음) 또는 'fix_'(DEV_FIX). E38 l1 → E41 → E42 → E43 loss."""
    import common
    import E15_baseline_loss_rating as E15
    if tag == "fix_":
        for dev, kv in DEV_FIX.items():
            E15.DEV[dev].update(kv)
    print("  [%s] SiC1200 %s" % (tag, E15.DEV["SiC1200"]), flush=True)
    import E38_review_response as E38
    import E41_fair_aux_comparison as E41
    import E42_value_map_fair as E42
    import E43_review2_response as E43
    t0 = time.time()
    E38.EID = EID
    E38.save_json = lambda eid, name, obj: common.save_json(EID, tag + name, obj) if eid == EID else common.save_json(eid, name, obj)
    E38.load_json = lambda eid, name: common.load_json(EID, tag + name) if eid == EID else common.load_json(eid, name)
    E38.l1()
    print("  [%s] l1 %.0f s" % (tag, time.time() - t0), flush=True)
    m = {("E38", "l1_e25_comparison"): (EID, tag + "l1_e25_comparison"), ("E38", "l1_e15_comparison"): (EID, tag + "l1_e15_comparison"),
         ("E38", "l1_e18_A25R_value_map"): (EID, tag + "l1_e18_A25R_value_map"), ("E41", "fair"): (EID, tag + "e41_fair"),
         ("E42", "cases"): (EID, tag + "e42_cases"), ("E42", "cells"): (EID, tag + "e42_cells")}
    _redirect(E41, m, tag + "e41_"); E41.run()
    print("  [%s] E41 %.0f s" % (tag, time.time() - t0), flush=True)
    _redirect(E42, m, tag + "e42_"); E42.run()
    print("  [%s] E42 %.0f s" % (tag, time.time() - t0), flush=True)
    _redirect(E43, m, tag + "e43_"); E43.loss()
    print("  [%s] E43 L %.0f s" % (tag, time.time() - t0), flush=True)


def _diff_tree(a, b, path="", out=None, tol=1e-6):
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a:
            if k in b and k not in SKIP_KEYS:
                _diff_tree(a[k], b[k], path + "/" + str(k), out, tol)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            _diff_tree(x, y, path + "[%d]" % i, out, tol)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if abs(a - b) > tol * max(1., abs(a)):
            out.append((path, a, b))
    return out


def dev():
    for tag in ("r0_", "fix_"):
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "_chain", tag])
        if r.returncode != 0:
            raise SystemExit("chain %s 실패(%d)" % (tag, r.returncode))
    pairs = [(("E38", "l1_e15_comparison"), "r0_l1_e15_comparison"), (("E38", "l1_e25_comparison"), "r0_l1_e25_comparison"),
             (("E38", "l1_e18_A25R_value_map"), "r0_l1_e18_A25R_value_map"), (("E41", "fair"), "r0_e41_fair"),
             (("E42", "cases"), "r0_e42_cases"), (("E42", "cells"), "r0_e42_cells"), (("E43", "loss"), "r0_e43_loss")]
    r0 = {}
    for (eid, name), mine in pairs:
        d = _diff_tree(load_json(eid, name), load_json(EID, mine))
        r0["%s/%s" % (eid, name)] = dict(n_diff=len(d), first=[list(x) for x in d[:5]])
    ok0 = all(v["n_diff"] == 0 for v in r0.values())
    verdict("(D-R0) 정정 없이 저장값 재현", ok0, json.dumps({k: v["n_diff"] for k, v in r0.items()}, ensure_ascii=False))
    a41, b41 = load_json(EID, "r0_e41_fair"), load_json(EID, "fix_e41_fair")
    a42, b42 = load_json(EID, "r0_e42_cells")["cells"], load_json(EID, "fix_e42_cells")["cells"]
    a15, b15 = load_json(EID, "r0_l1_e15_comparison"), load_json(EID, "fix_l1_e15_comparison")
    a43, b43 = load_json(EID, "r0_e43_loss"), load_json(EID, "fix_e43_loss")
    s25a, s25b = load_json(EID, "r0_l1_e25_statements")["A25R"], load_json(EID, "fix_l1_e25_statements")["A25R"]
    keys = ("cls", "best_fair", "ties", "fair_margin_pct", "min_margin_pct")
    cells = {k: dict(old={x: a42[k].get(x) for x in keys}, new={x: b42[k].get(x) for x in keys}) for k in a42}
    cells43 = {k: dict(old=a43["e42"]["cells"][k].get("cls"), new=b43["e42"]["cells"][k].get("cls"),
                       old_min=a43["e42"]["cells"][k].get("min_margin_pct"), new_min=b43["e42"]["cells"][k].get("min_margin_pct"),
                       old_ties=a43["e42"]["cells"][k].get("ties"), new_ties=b43["e42"]["cells"][k].get("ties"),
                       old_best=a43["e42"]["cells"][k].get("best_fair"), new_best=b43["e42"]["cells"][k].get("best_fair"))
               for k in a43["e42"]["cells"]}
    aux = {s: [a15["results"][s]["drive_typ"]["avg_loss_W"], b15["results"][s]["drive_typ"]["avg_loss_W"]] for s in a15["results"]}
    F = "공정 기준(F1)"
    out = dict(DEV_FIX=DEV_FIX, R0=r0, R0_ok=ok0,
               H5=[a15["judge"]["H5_metric_pass"], b15["judge"]["H5_metric_pass"]],
               H5_band3=[a15["judge_band3"]["H5_metric_pass"], b15["judge_band3"]["H5_metric_pass"]], aux_l1_W=aux,
               e41=dict(fair=[{s: a41["cases"][F]["drive_typ"][s] for s in "456"}, {s: b41["cases"][F]["drive_typ"][s] for s in "456"}],
                        cases=[{c: {s: a41["cases"][c]["drive_typ"][s] for s in "456"} for c in a41["cases"]},
                               {c: {s: b41["cases"][c]["drive_typ"][s] for s in "456"} for c in b41["cases"]}],
                        W1=[a41["W1"], b41["W1"]], W2=[a41["W2"], b41["W2"]], W3=[a41["W3"], b41["W3"]],
                        charge=[a41["charge"], b41["charge"]]),
               e43=dict(W1=[a43["e41"]["W1"], b43["e41"]["W1"]], W2=[a43["e41"]["W2"], b43["e41"]["W2"]],
                        by_profile=[a43["e41"]["by_profile_pct"], b43["e41"]["by_profile_pct"]],
                        cases=[{t: a43["e41"]["cases"][t]["new"]["drive_typ"] for t in a43["e41"]["cases"]},
                               {t: b43["e41"]["cases"][t]["new"]["drive_typ"] for t in b43["e41"]["cases"]}], cells=cells43),
               e42_cells=cells, e25_statements=[s25a, s25b])
    save_json(EID, "dev", out)
    print("  보조 평균(E38 l1 형식) 이전 → 정정:", {s: "%.2f → %.2f" % tuple(v) for s, v in aux.items()})
    print("  E41 공정 기준 이전 %s → 정정 %s" % ({k: round(v, 3) for k, v in out["e41"]["fair"][0].items()},
                                       {k: round(v, 3) for k, v in out["e41"]["fair"][1].items()}))
    print("  E41 W1 %s %.2f %% → %s %.2f %%; E43 범위 %.1f … %.1f → %.1f … %.1f %%; W2 %.1f–%.1f → %.1f–%.1f W; W3 %.2f–%.2f → %.2f–%.2f배"
          % (a41["W1"]["rule"], a41["W1"]["fair_pct"], b41["W1"]["rule"], b41["W1"]["fair_pct"],
             a43["e41"]["W1"]["min_pct"], a43["e41"]["W1"]["max_pct"], b43["e41"]["W1"]["min_pct"], b43["e41"]["W1"]["max_pct"],
             a43["e41"]["W2"]["min_W"], a43["e41"]["W2"]["max_W"], b43["e41"]["W2"]["min_W"], b43["e41"]["W2"]["max_W"],
             a41["W3"]["min_ratio"], a41["W3"]["max_ratio"], b41["W3"]["min_ratio"], b41["W3"]["max_ratio"]))
    for k, v in cells.items():
        if v["old"] != v["new"]:
            print("  E42 칸 %-12s %s → %s" % (k, v["old"], v["new"]))
    for k, v in cells43.items():
        if (v["old"], v["old_best"], v["old_ties"]) != (v["new"], v["new_best"], v["new_ties"]):
            print("  E43 칸 %-12s %s(%s, %s) → %s(%s, %s), 최소 여유 %s → %s"
                  % (k, v["old"], v["old_best"], v["old_ties"], v["new"], v["new_best"], v["new_ties"], v["old_min"], v["new_min"]))
    verdict("(D) H5 판정 같음(엄격·3 %)", out["H5"][0] == out["H5"][1] and out["H5_band3"][0] == out["H5_band3"][1], str(out["H5"]))
    verdict("(D) E41 W1 같은 수준 유지", b41["W1"]["rule"] == a41["W1"]["rule"], b41["W1"]["rule"])
    verdict("(D) E42 칸 분류 같음", all(v["old"]["cls"] == v["new"]["cls"] for v in cells.values()), "")
    verdict("(D) E43 L 칸 분류 같음", all(v["old"] == v["new"] for v in cells43.values()), "")
    verdict("(D) E25 결론 문장 같음", s25a == s25b, "")


# ======================================================================================================
# (K) 클램프 구현 요구
# ======================================================================================================
PASSIVE = {"N": {}, "P-": dict(CA=0.9, Cb=0.9, Cd=0.9, Rd=0.9, Lw=1.1), "P+": dict(CA=1.1, Cb=1.1, Cd=1.1, Rd=1.1, Lw=0.9)}
H0 = 5.0
EPS_K1 = {"spec": ((0., 0.00025, 0.0005, 0.00075, 0.001), (-0.00025, -0.0005, -0.00075, -0.001)),
          "W460": ((0., 0.0025, 0.005, 0.0075, 0.01), (-0.0025, -0.005, -0.0075, -0.01))}
H_K2 = (6.0, 4.5, 4.0, 3.5, 3.0)
H_UP = (3.0, 3.5, 4.0, 4.5, 5.0)
EPS_LOW = -0.01


def _ev44(args):
    br, on, off, kw, extra, pas = args
    import E26_charging_stop as E26
    import E38_review_response as E38
    import E39_clamp_switch_rejudge as E39
    b = dict(E26.BUS_DEFAULT); b["CA"] = E38.CA_R
    for k, s in pas.items():
        b[k] = b[k] * s
    E26.BUS.clear(); E26.BUS.update(b)
    E26.RA_MOD = E38.RA_A25
    cl = dict(E26.CL_DEFAULT, on=on, off=off, branches=[(R, vd, m) for _, R, vd, m in br])
    cl.update(extra or {})
    E26.CL = cl
    r = E26.run_event(**kw, rec_every=1, full_trace=True)
    tr = np.array(r.pop("trace"))
    rows = E39._branch_rows(tr, kw, br, sum(m for *_, m in br))
    meta = dict(t_on_cont_max_ms=r["t_on_cont_max_ms"], n_forced_off=r["n_forced_off"], n_on_after_forced=r["n_on_after_forced"],
                clamp_on_end=r["clamp_on_end"], E_clamp_J=r["E_clamp_J"], t_clamp_on_ms=r["t_clamp_on_ms"],
                vA_min=float(tr[:, 1].min()), iA_min=float(tr[:, 4].min()), iA_max=float(tr[:, 4].max()))
    for v in rows.values():
        v.update(vA_max=float(r["vA_max"]), vb_max=float(r["vb_max"]), **meta)
    return rows


def _run44(jobs):
    """jobs: [(key, br, on, off, kw, extra, pas)] → {key: [ {종류: row} per event ]}"""
    with Pool(workers()) as p:
        res = p.map(_ev44, [j[1:] for j in jobs], chunksize=2)
    out = {}
    for j, r in zip(jobs, res):
        out.setdefault(j[0], []).append(r)
    return out


def _setup_part(part):
    import E39_clamp_switch_rejudge as E39
    import E40_typ_rule_rejudge as E40
    sws, _ = E40.switches40()
    vd = E40.vdrop40(sws)
    cfg, evf = (E40.SPEC, E40.spec_events) if part == "spec" else (E40.W460, E40.hv_events)
    sel, _row = E40._sel_row(part)
    swn = sel["switch"]
    last = load_json("E43", "heat")["parts"][part]["iter"][-1]
    Eh, El = last["E_hi_assumed"], last["E_lo_assumed"]
    c = E39.corners39(sel["n"], sel["R_b"], Eh, El)
    return dict(sws=sws, vd=vd, cfg=cfg, evf=evf, sel=sel, swn=swn, sw={swn: sws[swn]}, c=c, Eh=Eh, El=El)


def _point(P, eps, H, pas_name, combos):
    """한 점(ε, H, 수동소자, 조합 목록)의 모든 사건을 계산해 judge40 결과를 돌려준다. H=None이면 H0·(1 + ε)."""
    import E40_typ_rule_rejudge as E40
    Hv = H0 * (1 + eps) if H is None else H
    on = P["cfg"]["on"] * (1 + eps); off = on - Hv
    cbs = {k: v for k, v in E40.combos40(P["sel"]["n"], P["c"], P["vd"]).items() if k in combos}
    jobs = [(cb, br, on, off, e, dict(t_on_max=E40.T_ON_MAX), PASSIVE[pas_name]) for cb, br in cbs.items() for e in P["evf"]()]
    recs = _run44(jobs)
    rows = [r for evs_ in recs.values() for e in evs_ for r in e.values()]
    if {"hi", "lo"} <= {r["kind"] for r in rows}:
        j = E40.judge40(recs, P["sw"], P["cfg"]["lim"])
        s = j["switches"][P["swn"]]
    else:   # (실행 경과) 1차 실행에서 K1(max 조합만)에 작은 저항 가지가 없어 judge39가 멈춤 → C1·E를 judge39와 같은 식으로 직접 계산
        import E38_review_response as E38
        c1 = max(max(r["vA_max"], r["vb_max"]) for r in rows); Eb = max(r["E_branch_J"] for r in rows)
        hi = [r["E_branch_J"] for r in rows if r["kind"] == "hi"]; lo = [r["E_branch_J"] for r in rows if r["kind"] == "lo"]
        j = dict(C1_V=c1, C1=bool(c1 <= P["cfg"]["lim"]), E_branch_max_J=Eb, E=bool(Eb <= E38.E_RES), E_hi_obs=max(hi, default=0.),
                 E_lo_obs=max(lo, default=0.), i_branch_max=max(r["i_max"] for r in rows),
                 t_on_cont_max_ms=max(r["t_on_cont_max_ms"] for r in rows), n_forced_off_max=max(r["n_forced_off"] for r in rows))
        s = dict(ok=None, I=None, V=None, T=None, T_vj=None)
    return dict(eps=eps, H=Hv, on=on, off=off, pas=pas_name, combos=list(cbs), C1=j["C1"], C1_V=j["C1_V"],
                vA_max=max(r["vA_max"] for r in rows), vb_max=max(r["vb_max"] for r in rows), E=j["E"],
                E_branch_max_J=j["E_branch_max_J"], E_hi_obs=j["E_hi_obs"], E_lo_obs=j["E_lo_obs"], i_branch_max=j["i_branch_max"],
                sw_ok=s["ok"], I=s["I"], V=s["V"], T=s["T"], T_vj=s["T_vj"], t_on_cont_max_ms=j["t_on_cont_max_ms"],
                n_forced_off_max=j["n_forced_off_max"], Rmax=P["c"]["Rmax"], Rmin=P["c"]["Rmin"])


def _p(tag, r):
    sw = "—" if r["T_vj"] is None else "%.2f °C(%s)" % (r["T_vj"], "통과" if r["sw_ok"] else "불통과")
    print("   %s ε %+.3f %% H %.2f V %-2s %-11s: V_A %.3f·버스 %.3f V(C1 %s), 가지 %.0f J, %.1f A, 스위치 %s, 최대 켜짐 %.3f ms"
          % (tag, 100 * r["eps"], r["H"], r["pas"], "/".join(r["combos"]), r["vA_max"], r["vb_max"], "통과" if r["C1"] else "불통과",
             r["E_branch_max_J"], r["i_branch_max"], sw, r["t_on_cont_max_ms"]), flush=True)


def _spur(P, part, eps, H, pas_name):
    """E40 낮은 쪽 오동작 사건(강제 켬, 최대 연속 켜짐 있음). M1·M2·M3는 E40 (L)과 같다."""
    import E34_parts_rating as E34
    import E38_review_response as E38
    import E40_typ_rule_rejudge as E40
    on = P["cfg"]["on"] * (1 + eps); off = on - H
    extra = dict(force_on_at=E40.T_SPUR, t_on_max=E40.T_ON_MAX)
    cbs = E40.combos40(P["sel"]["n"], P["c"], P["vd"])
    jobs = [(cb, br, on, off, dict(e, tend=E40.T_SPUR + 38e-3), extra, PASSIVE[pas_name]) for cb, br in cbs.items() for e in E40._spur_events(part)]
    recs = _run44(jobs)
    sw = P["sw"][P["swn"]]
    I_lim = E34.I_DER * sw["I_pulse"]
    rows = []
    for cb, evs in recs.items():
        for e in evs:
            for kind, r in e.items():
                t_on = r["t_on_cont_max_ms"]
                th = E38.thermal([r], sw) if t_on >= 0.2 else None
                m1 = bool(t_on <= (E40.T_ON_MAX * 1e3 + 2e-3) and r["n_on_after_forced"] == 0 and not r["clamp_on_end"])
                m2 = bool(r["E_branch_J"] <= E38.E_RES and r["i_max"] <= I_lim and max(r["vA_max"], r["vb_max"]) <= P["cfg"]["lim"])
                m3 = None if th is None else bool(th["T"] <= sw["T_max"])
                rows.append(dict(combo=cb, kind=kind, Vbat=r["Vbat"], P400=r["P400"], t_on_ms=t_on, E_branch_J=r["E_branch_J"], i_max=r["i_max"],
                                 T=None if th is None else th["T"], M1=m1, M2=m2, M3=m3))
    return dict(eps=eps, H=H, pas=pas_name, M1=all(x["M1"] for x in rows), M2=all(x["M2"] for x in rows),
                M3=all(x["M3"] is not False for x in rows), t_on_max_ms=max(x["t_on_ms"] for x in rows),
                E_max_J=max(x["E_branch_J"] for x in rows), T_max=max([x["T"] for x in rows if x["T"] is not None], default=None), rows=rows)


def clamp(parts=("spec", "W460")):
    import E39_clamp_switch_rejudge as E39
    try:                                                                # 부분별로 따로 실행해도 한 파일에 모은다(실행 방법만, 판정 같음)
        out = load_json(EID, "clamp")["parts"]
    except Exception:
        out = {}
    for part in parts:
        P = _setup_part(part)
        t0 = time.time()
        print("  == %s: 가지 %d × %.1f Ω, %s, 가정 E_hi %.0f·E_lo %.0f J ==" % (part, P["sel"]["n"], P["sel"]["R_b"], P["swn"], P["Eh"], P["El"]), flush=True)
        # (K1)
        k1 = []
        X = None
        up, down = EPS_K1[part]
        for eps in up:
            rs = [_point(P, eps, None, pn, ("max",)) for pn in ("P-", "P+")]
            for r in rs:
                _p("K1", r)
            k1 += rs
            if all(r["C1"] and r["E"] for r in rs):
                X = eps
            else:
                break
        if X is None:
            for eps in down:
                rs = [_point(P, eps, None, pn, ("max",)) for pn in ("P-", "P+")]
                for r in rs:
                    _p("K1-", r)
                k1 += rs
                if all(r["C1"] and r["E"] for r in rs):
                    X = eps; break
        print("  K1 X = %s (%.0f s)" % (None if X is None else "%+.3f %%" % (100 * X), time.time() - t0), flush=True)
        if X is None:
            out[part] = dict(k1=k1, X=None, ok=False)
            save_json(EID, "clamp", dict(parts=out, passive=PASSIVE)); continue
        ladder_X = [e for e in sorted(set(up) | set(down)) if e <= X]          # 작은 쪽부터
        # (K2)
        k2 = []
        H_min = H0
        epss = sorted({EPS_LOW, 0., X})
        stop = False
        for H in H_K2:
            if stop and H < H0:
                break
            rs = [_point(P, eps, H, "N", ("min", "mix")) for eps in epss]
            for r in rs:
                _p("K2", r)
            k2 += rs
            okH = all(r["C1"] and r["E"] and r["sw_ok"] for r in rs)
            if H > H0:
                continue
            if okH:
                H_min = H
            else:
                stop = True
        upper_ok = all(r["C1"] and r["E"] and r["sw_ok"] for r in k2 if r["H"] == 6.0)
        print("  K2 H_min = %.1f V, 6.0 V %s (%.0f s)" % (H_min, "통과" if upper_ok else "불통과", time.time() - t0), flush=True)
        # (K3)
        k3_hist = []
        Xc, Hc = X, H_min
        ok = False
        for attempt in range(3):
            Eh, El = P["Eh"], P["El"]
            rows = None; S = False; it_hist = []
            for it in range(3):
                P["c"] = E39.corners39(P["sel"]["n"], P["sel"]["R_b"], Eh, El)
                rows = [_point(P, eps, H, pn, ("max", "min", "mix")) for eps in (EPS_LOW, Xc) for H in (Hc, 6.0) for pn in ("P-", "P+")]
                for r in rows:
                    _p("K3", r)
                Eho = max(r["E_hi_obs"] for r in rows); Elo = max(r["E_lo_obs"] for r in rows)
                it_hist.append(dict(it=it, E_hi_assumed=Eh, E_lo_assumed=El, E_hi_obs=Eho, E_lo_obs=Elo))
                if Eho <= Eh + 1e-9 and Elo <= El + 1e-9:
                    S = True; break
                if it == 2:
                    break
                Eh = math.ceil(Eho / E39.E_STEP) * E39.E_STEP if Eho > Eh else Eh
                El = math.ceil(Elo / E39.E_STEP) * E39.E_STEP if Elo > El else El
                print("   K3 자기 가열 가정 갱신 E_hi %.0f·E_lo %.0f J" % (Eh, El), flush=True)
            spur = [_spur(P, part, EPS_LOW, H, pn) for H in (Hc, 6.0) for pn in ("P-", "P+")]
            for s_ in spur:
                print("   K3-L ε −1 %% H %.1f V %s: M1 %s, M2 %s, M3 %s, 최대 켜짐 %.3f ms, 에너지 %.1f J, 온도 %s"
                      % (s_["H"], s_["pas"], s_["M1"], s_["M2"], s_["M3"], s_["t_on_max_ms"], s_["E_max_J"], s_["T_max"]), flush=True)
            c1 = all(r["C1"] and r["E"] for r in rows); swok = all(r["sw_ok"] for r in rows)
            spok = all(s_["M1"] and s_["M2"] and s_["M3"] for s_ in spur)
            k3_hist.append(dict(X=Xc, H_min=Hc, rows=rows, spur=spur, iter=it_hist, S=S, C1E=c1, sw=swok, spur_ok=spok))
            ok = bool(c1 and swok and spok and S)
            print("  K3 시도 %d: X %+.3f %%, H_min %.1f V → C1·E %s, 스위치 %s, 오동작 %s, 가정 %s (%.0f s)"
                  % (attempt + 1, 100 * Xc, Hc, c1, swok, spok, S, time.time() - t0), flush=True)
            if ok or attempt == 2:
                break
            if not c1:
                i = ladder_X.index(Xc)
                if i == 0:
                    break
                Xc = ladder_X[i - 1]
            elif not swok or not spok:
                nxt = [H for H in H_UP if H > Hc]
                if not nxt:
                    break
                Hc = nxt[0]
            else:
                break
        out[part] = dict(k1=k1, X=X, k2=k2, H_min=H_min, upper6_ok=upper_ok, k3=k3_hist, X_final=Xc, H_min_final=Hc, ok=ok,
                         lim=P["cfg"]["lim"], on0=P["cfg"]["on"], off0=P["cfg"]["off"], n=P["sel"]["n"], R_b=P["sel"]["R_b"], switch=P["swn"])
        verdict("(K) %s: 요구(공통 −1.0 … %+.3f %%, 히스테리시스 %.1f–6.0 V, 수동소자 ±10 %%) 결합 모서리 통과" % (part, 100 * Xc, Hc), ok, "")
        save_json(EID, "clamp", dict(parts=out, passive=PASSIVE))
    save_json(EID, "clamp", dict(parts=out, passive=PASSIVE))


# ======================================================================================================
# (F) 플라잉 커패시터 후보값
# ======================================================================================================
CFLY_DESIGN = 45.0e-6
CFLY_CASES = (("F-a_45.00uF", 45.0e-6), ("F-b_42.75uF", 42.75e-6))


def cfly():
    import model_stage_a as A
    import E35_a25r_verify as E35
    import E33_stage_a_25k_dynamics as E33
    base = A.DESIGNS["A25"]["Cfly"]
    orig_set = A.set_design
    res = {}
    for tag, C in CFLY_CASES:
        A.DESIGNS["A25"]["Cfly"] = CFLY_DESIGN                           # 제어 주기·판정 시간(FR0)은 설계값으로

        def set_design(name, _C=C):
            fr = orig_set(name)
            A.BASE["Cfly"] = _C                                         # 실제 부품값(공차 표본은 이 값 둘레)
            return fr
        A.set_design = set_design
        print("  == %s(해석 %.3f µF, 설계 %.2f µF) ==" % (tag, base * 1e6, CFLY_DESIGN * 1e6), flush=True)
        t0 = time.time()
        captured = {}
        E35.save_json = lambda eid, name, obj: captured.__setitem__(name, obj)
        E33.save_json = lambda eid, name, obj: captured.__setitem__(name, obj)
        try:
            E35.transient()
            E35.fault()
        finally:
            A.set_design = orig_set; A.DESIGNS["A25"]["Cfly"] = base
        tr = captured["transient"]["cases"]; fl = captured["fault"]["cases"]
        okT = all(x["passed"] for x in tr); okF = all(x["passed"] for x in fl)
        res[tag] = dict(C=C, C_design=CFLY_DESIGN, transient=tr, fault=fl, okT=okT, okF=okF, sec=time.time() - t0,
                        phase_peak_T=max(x["phase_peak"] for x in tr), phase_peak_F=max(x["phase_peak"] for x in fl),
                        vA_T=[min(x["vA"][0] for x in tr), max(x["vA"][1] for x in tr)])
        verdict("(F) %s: 요구 안 과도 %d/%d, 모듈 고장 %d/%d" % (tag, sum(x["passed"] for x in tr), len(tr), sum(x["passed"] for x in fl), len(fl)),
                okT and okF, "%.0f s, 첨두 과도 %.1f·고장 %.1f A" % (time.time() - t0, res[tag]["phase_peak_T"], res[tag]["phase_peak_F"]))
        save_json(EID, "cfly", res)


# ======================================================================================================
# (R) 재분석
# ======================================================================================================
def scope():
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    val = root / "validation"
    out = {}
    # H4
    s = json.loads((val / "2026-09-28-requirements" / "sals_contract.json").read_text(encoding="utf-8"))["summary"]["sals"]
    out["H4"] = dict(noloss=s["grant_latency_ms_noloss"], loss=s["grant_latency_ms_loss"], budget_exceed_ms=s["budget_exceed_ms_total"],
                     peak_kW=s["peak_kW"], unmet_total=s["d_unmet_fraction"]["total"], starts=s["compressor_starts"],
                     crit=dict(noloss_max_ms=25, loss_p99_ms=50),
                     ok=bool(s["grant_latency_ms_noloss"]["max"] <= 25 and s["grant_latency_ms_loss"]["p99"] <= 50 and s["budget_exceed_ms_total"] == 0))
    # H1
    st = json.loads((val / "2026-10-28-a25r-impact" / "E36" / "e16_static.json").read_text(encoding="utf-8"))
    co = json.loads((val / "2026-10-28-a25r-impact" / "E36" / "e16_concurrent.json").read_text(encoding="utf-8"))
    r = co["rows"]
    mx = lambda rows: max(x["dab_power_peak"] for x in rows) / 1e3
    ins = [x for x in r if 640 <= x["V"] <= 920]
    out["H1"] = dict(static_charge_all_kW=st["charge"]["link_kW_max"], static_charge_640_25kW=st["charge"]["link_at_640_25kW"],
                     static_drive_all_kW=st["drive"]["link_kW_max"], static_drive_640_25kW=st["drive"]["link_at_640_25kW"],
                     transient_spec_formal_kW=mx([x for x in ins if not (x["tier"] == 2 and x["delay"])]), transient_spec_all_kW=mx(ins),
                     transient_all_kW=mx(r), transient_632_kW=mx([x for x in r if x["V"] == 632]),
                     failed=[(x["name"], x["V"], x["info"], x["failed"]) for x in r if not x["pass_"]])
    # 팩별 150 kW
    l2 = json.loads((val / "2026-10-29-review-response" / "E38" / "l2.json").read_text(encoding="utf-8"))
    out["pack150"] = [dict(pack=x["pack"], P_kW=x["P_kW"], nph=x["nph"], iph=x["iph"], I_A=x["iph"] * x["nph"], loss_W=x["loss_W"])
                      for x in l2["rows"]]
    # 500 V 충전기
    R = 9.0e-3 / 4 + 3e-3
    vmax = 2 * (500. - R * 375.)
    out["charger500"] = dict(R_ohm=R, vbat_max=vmax, ns_max_4p2=int(vmax // 4.2), I_for_238s_A=(500. - 238 * 4.2 / 2) / R,
                             R_E18=0.00555, ns_max_E18=int(2 * (500. - 0.00555 * 375.) // 4.2))
    # TB28(열: 0 t, 1 V_A, 2 버스, 5 충전 전류, 10 48 V 출력)
    tb = root / "simulink" / "tb" / "TB28_A25R_Charging_Stop" / "results"
    tbo = {}
    for cn in ("A28_920V_pathloss", "B28_640V_pathloss_ramp", "C28_800V_module_fault"):
        Aa = np.loadtxt(tb / ("TB28_%s_avg1us.csv" % cn), delimiter=",")
        t, vA, vb, ich, vo = Aa[:, 0], Aa[:, 1], Aa[:, 2], Aa[:, 5], Aa[:, 10]
        post = t >= 1e-3
        d = dict(t_end_ms=float(t[-1] * 1e3), v48=[float(vo[post].min()), float(vo[post].max())], vA_end=float(vA[-1]), vbus_end=float(vb[-1]),
                 ich_end=float(ich[-1]))
        z = np.where((np.abs(ich) < 1) & (t > 1e-3))[0]
        if len(z):
            t0 = t[z[0]]; k = t >= t0
            d.update(t_ich0_ms=float(t0 * 1e3), obs_after_ms=float((t[-1] - t0) * 1e3), vbus=[float(vb[k][0]), float(vb[-1])], vA=[float(vA[k][0]), float(vA[-1])])
        tbo[cn] = d
    out["TB28"] = tbo
    # Stage A 첨두(A25R)
    e35 = val / "2026-10-28-stage-a-25k" / "E35"
    pk = {}
    for f in ("transient", "fault", "beyond"):
        rows = json.loads((e35 / ("%s.json" % f)).read_text(encoding="utf-8"))["cases"]
        pk[f] = max(x["phase_peak"] for x in rows)
    pk["per_device"] = {k: v / 2 * 1.1 for k, v in list(pk.items())}
    out["stageA_peak"] = pk
    save_json(EID, "scope", out)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=float)[:4000])


# ======================================================================================================
# (실행 뒤 추가, 판정 없음) 손익분기 상저항
# ======================================================================================================
def bkv():
    import E15_baseline_loss_rating as E15
    import E36_breakeven_grid as BG
    out = {}
    for tag in ("r0_", "fix_"):
        if tag == "fix_":
            for dev, kv in DEV_FIX.items():
                E15.DEV[dev].update(kv)
        e25 = load_json(EID, tag + "l1_e25_comparison")
        rows = {}
        for key, V in (("640V", 640.), ("800V", 800.), ("920V", 920.)):
            pA = e25["charge"][key]["stageA"]
            rA = BG.breakeven(V, pA)
            lo5, c5 = BG.grid_min(V, 0.005)
            rows[key] = dict(stageA_W=pA, Rph_grid_mOhm=rA, grid_min_at_5mOhm_W=lo5, combo_at_5mOhm=c5)
            print("  %s %s: Stage A %.1f W, 격자 손익분기 %.2f mΩ, 5 mΩ 격자 최소 %.1f W" % (tag, key, pA, rA, lo5), flush=True)
        out[tag] = rows
    save_json(EID, "bkv", out)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "_chain":
        chain(sys.argv[2]); sys.exit(0)
    parts = sys.argv[1:] or ["scope", "dev", "clamp", "cfly"]
    for p in parts:
        print("\n==== E44 %s ====" % p, flush=True)
        if p.startswith("clamp:"):                                      # 예: clamp:spec, clamp:W460 (2시간 실행 한도 때문에 나눠 실행)
            clamp((p.split(":", 1)[1],)); continue
        {"dev": dev, "clamp": clamp, "cfly": cfly, "scope": scope, "bkv": bkv}[p]()
