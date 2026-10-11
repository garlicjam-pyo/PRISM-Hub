"""[E11] 채택 제어기의 MATLAB 독립 구현 교차검증 (Python 쪽: 사례 내보내기와 결과 대조).

■ 목적
  E5–E7의 채택 설계(연산 지연 보상 + 감쇠비 0.95) 결과는 Python 구현 하나에서만 나왔다. 같은 시험을
  MATLAB으로 따로 구현한 플랜트·제어기·판정 로직(matlab/prism_stage_b_batch.m)으로 다시 계산해
  통과·실패 판정과 지표가 일치하는지 확인한다(보고서 표 8.2 일정의 "제어기 MATLAB 교차검증").

■ 왜 필요한가
  예측 보상은 제어주기마다 공칭 모델을 5단계 적분하는 연산이 들어가 구현 실수가 판정을 바꿀 여지가
  비교 설계보다 크다. E2에서 비교 설계는 이중 구현으로 확인했지만, 보고서의 핵심 주장(H2 충족)은 채택
  설계에 기대고 있으므로 같은 수준의 독립 확인이 필요하다. 이득도 MATLAB에서 아커만 공식으로 따로
  계산해 극배치 단계의 오류까지 함께 걸러낸다.

■ 방법
  1) export : E5–E7과 같은 조건(시험 격자 552건 × 두 설계, 비선형 지연 경계 2 × 60건, 복합 공차 코너
              256건, L_h ±5 % 재시험 26건, 계약 시퀀스 48건)을 results/E11/cases_*.json으로 내보낸다.
              공유하는 것은 시험 조건(전압·부하·플랜트 파라미터·적분간격)과 사양(제어기 공칭 파라미터, 극배치
              사양인 감쇠비·극 비율·설계점, Tier 한계)이다. 이득·플랜트·제어기·판정 코드는 MATLAB이 따로 구현한다.
              따라서 이 대조는 구현 오류를 걸러내며, 사양이나 파라미터 값 자체의 오류는 걸러내지 못한다.
  2) MATLAB : matlab/E11_controller_crosscheck.m 이 사례를 벡터화(사례 방향) 적분하고 판정한다.
  3) compare: MATLAB 결과를 results/E5–E7의 Python 결과와 대조한다. 행 순서가 내보낸 사례와 같은지 사례
              키로 먼저 확인하고(MATLAB은 사례 순서대로 결과를 쓴다), 최종 판정과 세부 실패 항목을 함께 비교한다.

■ 판정 기준
  - 모든 사례에서 통과·실패 판정과 세부 실패 항목(전압 품질 6항목·포트·Tier-2 대역·내부 진동·전류 한계)이 같을 것
  - 수렴하는(통과 또는 완료된 안정) 사례의 지표 최대 상대오차 < 1e-6 (크기 1 미만 지표는 절대오차)
  - 발산하는 사례(비교 설계의 추가 지연 등)는 판정만 같으면 되며 지표 차를 기록한다
  - MATLAB에서 아커만 공식으로 계산한 이득과 Python 이득의 상대오차 < 1e-6

■ 실행   python E11_controller_crosscheck.py export
         (MATLAB/Octave)  cd matlab ; E11_controller_crosscheck
         python E11_controller_crosscheck.py compare
■ 결과   results/E11/cases_*.json, results/E11/matlab_*.json, results/E11/crosscheck.json
"""
import itertools
import sys
from dataclasses import asdict, replace

import numpy as np

import stage_b_tests as st
from controller_reference import NOMINAL, GAIN
from controller_adopted import K_ADOPTED, ZETA, POLES, CP
from common import save_json, load_json, verdict, RESULTS

PROFILE = {"step": 0, "up_ramp": 1, "up_stair": 2, "down_ramp": 3, "down_stair": 4}
METRICS = ["path_peak", "bridge_peak", "link_peak", "dab_power_peak", "droop", "vbus_min_post", "vbus_max_post",
           "tail_ripple_V", "modulation_peak", "series_peak", "vlink_min", "tail_ih_pp_A", "tail_m_pp"]


def dt_for(p):
    return 1e-7 if abs(p.delay / 2e-7 - round(p.delay / 2e-7)) > 1e-9 else 2e-7


def case(tier, vbat, p0, p1, p, dt=None, profile="step", key=None):
    return dict(key=key, tier=tier, vbat=float(vbat), power0=float(p0), power1=float(p1),
                profile=PROFILE[profile], dt=dt or dt_for(p), plant=asdict(p))


def export():
    groups = {}
    groups["grid"] = [case(t, v, a, b, p, key=[t, n, v, a, b]) for t, n, v, a, b, p in st.grid_jobs()]
    from E5_E7_controller import DELAY_EXTRAS, corner_p
    for d in ("adopted", "reference"):
        rows = []
        for v in (640, 920):
            for e in DELAY_EXTRAS[d]:
                for a, b in [(15000, 25000), (25000, 15000), (0, 10000)]:
                    p = replace(NOMINAL, delay=round((NOMINAL.delay + e * 1e-6) / 1e-7) * 1e-7)
                    rows.append(case(1, v, a, b, p, dt=1e-7, key=[v, e, a, b]))
        groups[f"delay_{d}"] = rows
    rows = []
    for s, t in [(s, t) for s in itertools.product([-1, 1], repeat=7) for t in (1, 2)]:
        extra = 3e-6 if t == 1 else 0.
        p = replace(corner_p(s, {f: .1 for f in st.FIELDS}), delay=NOMINAL.delay + extra)
        a, b = (15000, 25000) if t == 1 else (1000, 25000)
        rows.append(case(t, 640, a, b, p, key=[list(s), t]))
    groups["corners"] = rows
    prev = load_json("E7", "corners")
    fails = [tuple(r["signs"]) for r in prev["rows"] if r["tier"] == 2 and not r["pass_"]]
    groups["corners_lh5"] = [case(2, 640, 1000, 25000, corner_p(s, {f: (.05 if f == "Lh" else .1) for f in st.FIELDS}),
                                  key=list(s)) for s in fails]
    sets = {"nominal": NOMINAL, "Lhx0.9": replace(NOMINAL, Lh=NOMINAL.Lh * .9), "Lx1.1": replace(NOMINAL, L=NOMINAL.L * 1.1),
            "delay+3.0us": replace(NOMINAL, delay=NOMINAL.delay + 3e-6)}
    rows = []
    for v in (632., 640., 920.):
        for n, p in sets.items():
            for fn in st.SEQUENCES:
                p0 = st.SEQUENCES[fn](0.)
                rows.append(case(1, v, p0, p0, p, profile=fn, key=[v, n, fn]))
    groups["sequences"] = rows
    meta = dict(control=asdict(CP), reference=dict(K=list(GAIN), control=asdict(NOMINAL)),
                adopted=dict(K_python=K_ADOPTED.tolist(), zeta=ZETA, poles=POLES, design_point=[788., 5000.]),
                limits=dict(T1_A=st.T1_LIMIT_A, T2_A=st.T2_LIMIT_A, T2_band=st.T2_BAND,
                            tail_ih_pp_A=st.TAIL_IH_PP_A, tail_m_pp=st.TAIL_M_PP),
                duration=.02, step=.001)
    save_json("E11", "cases_meta", meta)
    for name, rows in groups.items():
        save_json("E11", f"cases_{name}", rows)
        print(f"   {name}: {len(rows)}건")


# (MATLAB 결과 이름, Python 결과 위치, 내보낸 사례 묶음)
PAIRS = [("grid_adopted", ("E5", "grid_adopted"), "grid"), ("grid_reference", ("E5", "grid_reference"), "grid"),
         ("delay_adopted", ("E6", "delay_adopted"), "delay_adopted"), ("delay_reference", ("E6", "delay_reference"), "delay_reference"),
         ("corners_adopted", ("E7", "corners"), "corners"), ("corners_lh5_adopted", ("E7", "corners_lh5"), "corners_lh5"),
         ("sequences_adopted", ("E7", "sequences_adopted"), "sequences")]
CHECK_NAMES = ["completed", "ports", "voltage_excursion", "final_voltage", "recovery_1ms", "final_1ms_ripple"]


def py_key(group, r):
    """Python 결과 행의 사례 키(내보낸 사례 키와 같은 형식)."""
    if group == "grid":
        return [r["tier"], r["set"], r["vbat"], r["p0"], r["p1"]]
    if group.startswith("delay"):
        return [r["vbat"], r["added_us"], r["p0"], r["p1"]]
    if group == "corners":
        return [list(r["signs"]), r["tier"]]
    if group == "corners_lh5":
        return list(r["signs"])
    return [r["vbat"], r["set"], r["sequence"]]


def same_key(a, b):
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same_key(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= 1e-9 * max(1., abs(float(a)))
    return a == b


def failed_matlab(tier, b):
    """MATLAB 행의 세부 판정을 Python 'failed' 목록과 같은 이름으로 바꾼다(stage_b_tests.judge와 같은 규칙)."""
    internal = b["tail_ih_pp_A"] <= st.TAIL_IH_PP_A and b["tail_m_pp"] <= st.TAIL_M_PP
    if tier == 1:
        f = [n for n, c in zip(CHECK_NAMES, b["checks"]) if not c]
        if not internal:
            f.append("internal_tail_oscillation")
        lim = st.T1_LIMIT_A
    else:
        band = st.T2_BAND[0] <= b["vbus_min_post"] and b["vbus_max_post"] <= st.T2_BAND[1]
        f = [n for n, ok in [("completed", b["checks"][0]), ("ports", b["ports_ok"]), ("bus_band_384_416V", band),
                             ("final_voltage", b["checks"][3]), ("internal_tail_oscillation", internal)] if not ok]
        lim = st.T2_LIMIT_A
    if max(b["path_peak"], b["bridge_peak"]) > lim:
        f.append(f"current>{lim:g}A")
    return f


def compare():
    print("[E11] Python·MATLAB 채택 제어기 대조")
    out = {}
    g = load_json("E11", "matlab_gain")
    rel = float(np.max(np.abs((np.array(g["K_adopted"]) - K_ADOPTED) / K_ADOPTED)))
    rel_ref = float(np.max(np.abs((np.array(g["K_reference"]) - np.array(GAIN)) / np.array(GAIN))))
    verdict("MATLAB 아커만 이득 = Python 극배치 이득(채택·비교 설계)", rel < 1e-6 and rel_ref < 1e-6,
            f"상대오차 {rel:.1e} / {rel_ref:.1e}")
    out["gain"] = dict(K_matlab=g["K_adopted"], K_python=K_ADOPTED.tolist(), rel_err=rel, rel_err_reference=rel_ref)
    allok = True
    for mname, (eid, pname), group in PAIRS:
        if not (RESULTS / "E11" / f"matlab_{mname}.json").exists():
            print(f"   {mname}: MATLAB 결과 없음(건너뜀)"); continue
        m = load_json("E11", f"matlab_{mname}")["rows"]; py = load_json(eid, pname)["rows"]
        cases = load_json("E11", f"cases_{group}")
        assert len(m) == len(py) == len(cases), (mname, len(m), len(py), len(cases))
        key_bad = [i for i, (c, a) in enumerate(zip(cases, py)) if not same_key(c["key"], py_key(group, a))]
        mism = []; sub_mism = []; dmax_conv = 0.; dmax_div = 0.
        for i, (a, b) in enumerate(zip(py, m)):
            if bool(a["pass_"]) != bool(b["pass_"]):
                mism.append(i)
            if sorted(a["failed"]) != sorted(failed_matlab(cases[i]["tier"], b)):
                sub_mism.append(i)
            rec_a, rec_b = a["recovery_s"], b["recovery_s"]
            d = max(abs(a[k] - b[k]) / max(1., abs(a[k])) for k in METRICS)   # 상대오차(1 미만 값은 절대오차)
            if (rec_a is None) != (rec_b is None):
                d = np.inf
            elif rec_a is not None:
                d = max(d, abs(rec_a - rec_b))
            converged = a["pass_"] or (a["tail_ih_pp_A"] <= st.TAIL_IH_PP_A and a["tail_m_pp"] <= st.TAIL_M_PP
                                       and a.get("completed", True))
            if converged: dmax_conv = max(dmax_conv, d)
            else: dmax_div = max(dmax_div, d)
        n_pass_py = sum(bool(r["pass_"]) for r in py); n_pass_m = sum(bool(r["pass_"]) for r in m)
        n_failed_items = sum(len(r["failed"]) for r in py)
        ok = not key_bad and not mism and not sub_mism and dmax_conv < 1e-6
        allok &= ok
        verdict(f"{mname}: {len(py)}건 사례 키·판정·세부 실패 항목 일치(통과 Python {n_pass_py} / MATLAB {n_pass_m}, "
                f"실패 항목 {n_failed_items}개), 수렴 사례 지표 최대 상대오차 {dmax_conv:.1e}"
                + (f", 발산 사례 {dmax_div:.1e}" if dmax_div else ""), ok,
                (f"키 불일치 {key_bad[:5]} " if key_bad else "") + (f"판정 불일치 {mism[:5]} " if mism else "")
                + (f"세부 항목 불일치 {sub_mism[:5]}" if sub_mism else ""))
        out[mname] = dict(cases=len(py), passed_python=n_pass_py, passed_matlab=n_pass_m, key_mismatch=key_bad,
                          verdict_mismatch=mism, failed_item_mismatch=sub_mism, failed_items_python=n_failed_items,
                          max_metric_diff_converged=dmax_conv, max_metric_diff_diverging=dmax_div)
    out["tool"] = load_json("E11", "matlab_gain").get("tool")
    out["all_agree"] = bool(allok)
    save_json("E11", "crosscheck", out)


if __name__ == "__main__":
    {"export": export, "compare": compare}[sys.argv[1] if len(sys.argv) > 1 else "export"]()
