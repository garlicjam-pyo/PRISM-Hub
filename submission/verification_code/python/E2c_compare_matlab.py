"""[E2-c] Python·MATLAB 이중 구현 결과 대조.

■ 목적
  E2-a(12개 동적 사례)와 E2-b(80개 시험조건)를 MATLAB 독립 구현(matlab/E2_two_stage_crosscheck.m)이
  다시 계산한 결과와 비교한다. 두 구현은 같은 방정식을 따로 코딩한 것이며 이득·파라미터만 공유한다.

■ 판정 기준
  - 완료 여부, 포트 한계 위반(항목별), 전압 품질 항목별 판정, 최종 통과·실패가 모두 같을 것
  - 수치 지표(강하, 피크 전류 등) 최대 차이: 12개 사례 < 1e-6, 80개 조건 중 공칭 < 1e-6,
    공차·민감도·정격 초과 < 1e-3 (발산하는 실패 궤적은 부동소수점 오차가 커질 수 있어 완화.
    이 경우에도 판정은 같아야 한다)
  보고서 수치(MATLAB R2024b): 12개 사례 최대 차이 1.91×10⁻¹⁰, 80개 조건 판정 전부 일치.

■ 실행 순서
  1) python E2a_model_consistency.py ; python E2b_reference_matrix.py
  2) MATLAB(또는 GNU Octave)에서  cd matlab ; E2_two_stage_crosscheck
  3) python E2c_compare_matlab.py
■ 결과   results/E2/cross_language.json
"""
from common import load_json, save_json, verdict

METRICS = ["droop", "vbus_end", "vbus_max", "vlink_min", "vlink_max", "path_peak", "bridge_peak",
           "link_peak", "series_peak", "dab_power_peak", "modulation_peak", "end_time"]


def compare(py, mat, flags, extra_metrics=(), tol_fn=lambda row: 1e-6):
    errors = {}; mismatches = []
    for a, b in zip(py["cases"], mat["cases"]):
        assert a["name"] == b["name"], (a["name"], b["name"])
        for key in flags:
            if a[key] != b[key]:
                mismatches.append((a["name"], key))
        if "recovery_s" in extra_metrics:
            ra, rb = a["recovery_s"], b["recovery_s"]
            if (ra is None) != (rb is None) or (ra is not None and abs(ra - rb) > 1e-10):
                mismatches.append((a["name"], "recovery_s"))
        diff = max(abs(a[k] - b[k]) for k in METRICS + [m for m in extra_metrics if m != "recovery_s"])
        errors[a["name"]] = diff
        if diff >= tol_fn(a):
            mismatches.append((a["name"], f"metric {diff:.2e}"))
    return errors, mismatches


if __name__ == "__main__":
    print("[E2-c] Python·MATLAB 대조")
    out = {}
    py = load_json("E2", "two_stage_python"); mat = load_json("E2", "two_stage_matlab")
    e1, m1 = compare(py, mat, ["completed", "within_port_limits", "voltage_quality_pass", "violations"])
    verdict(f"12개 동적 사례 판정 일치, 지표 최대 차 {max(e1.values()):.2e}", not m1 and len(e1) == 12, str(m1) if m1 else "")
    out["two_stage"] = dict(cases=len(e1), max_absolute_metric_error=max(e1.values()), by_case=e1, mismatches=m1,
                            matlab_version=mat.get("matlab_version"))

    py = load_json("E2", "reference_matrix_python"); mat = load_json("E2", "reference_matrix_matlab")
    e2, m2 = compare(py, mat, ["completed", "within_port_limits", "voltage_quality_pass", "violations", "checks", "requirements_pass"],
                     extra_metrics=("tail_ripple_V", "recovery_s"),
                     tol_fn=lambda row: 1e-6 if row["group"] == "nominal" else 1e-3)
    nominal = [r["name"] for r in py["cases"] if r["group"] == "nominal"]
    verdict(f"80개 조건 판정 일치, 지표 최대 차 {max(e2.values()):.2e} (공칭 {max(e2[n] for n in nominal):.2e})",
            not m2 and len(e2) == 80, str(m2) if m2 else "")
    out["reference_matrix"] = dict(cases=len(e2), max_absolute_metric_error=max(e2.values()),
                                   max_nominal_error=max(e2[n] for n in nominal), by_case=e2, mismatches=m2)
    out["note"] = "같은 평균모델 방정식의 독립 구현 대조이며 하드웨어 검증이 아니다."
    save_json("E2", "cross_language", out)
