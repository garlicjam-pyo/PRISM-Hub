"""[E2-b] 비교 설계 제어기의 80개 시험조건 (Python·MATLAB 이중 구현 대조용).

■ 목적
  고정 이득 제어기(비교 설계, controller_reference.py)를 80개 조건에서 돌려 판정 결과를 남기고,
  같은 조건을 MATLAB 독립 구현(matlab/E2_two_stage_crosscheck.m)이 다시 계산하게 한다.
  두 구현의 통과·실패 판정과 한계 위반 판정이 모두 일치하는지가 E2의 두 번째 검산이다(보고서 5.3절).

■ 왜 필요한가
  E5–E7의 판정은 전압 품질 6개 항목과 포트 한계 판정 로직에 의존한다. 제어 법칙·지연 버퍼·판정
  로직까지 포함한 전체 사슬을 다른 언어로 따로 구현해 같은 결과가 나오는지 확인해야 코드 오류가
  판정을 바꾸지 않았다고 말할 수 있다. 실패가 예상되는 조건(정격 초과, 지연 증가)을 일부러 넣어
  실패 판정도 같은지 본다.

■ 방법
  - 이득 GAIN은 788 V·5 kW에서 한 번 설계한 값이며 모든 조건에 고정(제어기는 공차를 모른다).
  - 조건 80개
      공칭 41개   : 1→25 kW(640–920 V, 10 V 간격 + 648·788·907 V, 32개), 5→25 kW, 25→1 kW(각 3개), 회생·영교차 3개
      정격 초과 3개: 5→29 kW (640·788·920 V) — 연속 정격 밖, 판정 기록용
      공차 28개   : L, Cs, Cb, Lh, Clink, R, Rh 중 하나를 ±10 % (640·920 V)
      민감도 8개  : 전달지연 10·15 µs, DAB 시정수 15 µs, 효율 0.94 (640·920 V)
  - 판정: 전압 품질 6개 항목(controller_reference.assess) + 포트 물리 한계.
  - 부가 검산: 판정 함수의 회복시간 정의 단위시험, 적분간격 절반 수렴, 한계 근처(L_h −10 %) 사례의 적분간격 민감도.

■ 판정 기준
  공칭 41개는 모두 통과해야 한다. 나머지는 결과를 기록하고 MATLAB과 판정이 같아야 한다.

■ 실행   python E2b_reference_matrix.py         (약 1분)
■ 결과   results/E2/reference_matrix_python.json, results/E2/reference_cases.json (MATLAB 입력)
"""
from dataclasses import replace, asdict
import numpy as np

from model_stage_b import design
from controller_reference import NOMINAL, GAIN, run, assess
from common import save_json, verdict


def specs():
    s = []
    for v in sorted(set(range(640, 921, 10)) | {648, 788, 907}):
        s.append((f"rated60_{v}", v, 1000, 25000, NOMINAL, "nominal"))          # 1→25 kW (400 V 기준 60 A 상당)
    for v in [640, 788, 920]:
        s += [(f"rated50_{v}", v, 5000, 25000, NOMINAL, "nominal"),
              (f"unload60_{v}", v, 25000, 1000, NOMINAL, "nominal"),
              (f"overload29_{v}", v, 5000, 29000, NOMINAL, "outside_continuous_rating")]
    s += [("regen_640", 640, 5000, -5000, NOMINAL, "nominal"),
          ("regen_920", 920, -5000, 5000, NOMINAL, "nominal"),
          ("zero_crossing_800", 800, 5000, -5000, NOMINAL, "nominal")]
    for field in ["L", "Cs", "Cb", "Lh", "Clink", "R", "Rh"]:                   # 단일 변수 공차
        for factor in [.9, 1.1]:
            p = replace(NOMINAL, **{field: getattr(NOMINAL, field) * factor})
            for v in [640, 920]:
                s.append((f"tolerance_{field}_{factor}_{v}", v, 1000, 25000, p, "tolerance"))
    for field, value in [("delay", 10e-6), ("delay", 15e-6), ("tau", 15e-6), ("eta", .94)]:
        for v in [640, 920]:
            s.append((f"sensitivity_{field}_{value}_{v}", v, 1000, 25000, replace(NOMINAL, **{field: value}), "sensitivity"))
    return s


def main():
    print("[E2-b] 비교 설계 제어기 80개 조건")
    # 고정 이득이 설계 함수의 결과와 같은지(이득이 임의로 바뀌지 않았는지)
    # (적분이득이 약 1.3e4로 크므로 상대오차로 비교한다. SciPy 버전에 따라 1e-11 수준 차이가 날 수 있다.)
    rel = np.max(np.abs((design(788, 5000, NOMINAL) - GAIN) / np.array(GAIN)))
    verdict("GAIN = design(788 V, 5 kW)", rel < 1e-9, f"상대오차 {rel:.1e}")
    # 회복시간 정의 단위시험: 벗어나지 않음 → 0, 벗어났다 재진입 → 재진입 시각, 끝까지 밖 → None
    t = np.array([.001, .0015, .002, .003]); x = np.zeros((4, 6)); x[:, 2] = 400
    ok = assess(t, x, .001, True, True)["recovery_s"] == 0
    x[1, 2] = 391; ok &= assess(t, x, .001, True, True)["recovery_s"] == .001
    x[-1, 2] = 395; ok &= assess(t, x, .001, True, True)["recovery_s"] is None
    verdict("회복시간 판정 함수 단위시험 3건", ok)

    rows = []; inputs = []; traces = {}
    for name, v, a, b, p, group in specs():
        r = run(v, a, b, p, keep_trace=True)
        traces[name] = (r.pop("t"), r.pop("x")); r.pop("u")
        r.update(name=name, group=group); rows.append(r)
        inputs.append(dict(name=name, vbat=v, power0=a, power1=b, dt=r["dt"], duration=r["duration"],
                           K=list(GAIN), parameters=asdict(p), control_parameters=asdict(NOMINAL),
                           expected_pass=r["requirements_pass"], group=group))
        rec = None if r["recovery_s"] is None else round(r["recovery_s"] * 1e6, 1)
        print(f"   {name:32s} {'통과' if r['requirements_pass'] else '실패'}  강하 {r['droop']:6.3f} V  "
              f"경로 {r['path_peak']:7.3f} A  회복 {rec} µs")
    summary = {g: dict(total=sum(r["group"] == g for r in rows),
                       passed=sum(r["group"] == g and r["requirements_pass"] for r in rows))
               for g in ["nominal", "outside_continuous_rating", "tolerance", "sensitivity"]}
    print("   요약:", summary)
    verdict("공칭 41개 조건 모두 통과", summary["nominal"]["passed"] == summary["nominal"]["total"] == 41)
    verdict("640 V 5→29 kW(정격 초과)는 실패로 판정", not next(r for r in rows if r["name"] == "overload29_640")["requirements_pass"])

    # 적분간격 절반 수렴(640 V, 1→25 kW)
    fine = run(640, dt=1e-7, keep_trace=True)
    convergence = float(np.max(np.abs(fine["x"][1::2, 2] - traces["rated60_640"][1][:, 2])))
    verdict("적분간격 0.2 → 0.1 µs 버스전압 최대 차 < 0.05 V", convergence < .05, f"{convergence*1e3:.3f} mV")
    # 100 A 한계 근처 사례(L_h −10 %)에서 적분간격이 판정을 바꾸지 않는지
    near = run(640, plant=replace(NOMINAL, Lh=NOMINAL.Lh * .9), dt=1e-7)
    coarse = next(r for r in rows if r["name"] == "tolerance_Lh_0.9_640")
    verdict("한계 근처 사례(L_h −10 %)의 적분간격 절반 시 판정 동일", near["requirements_pass"] == coarse["requirements_pass"],
            f"경로 피크 {coarse['path_peak']:.4f} → {near['path_peak']:.4f} A")

    data = dict(scope="비교 설계 고정 이득 1개, 유한 링크 평균모델, 평형점 시작, 20 ms",
                controller=dict(K=list(GAIN), parameters=asdict(NOMINAL), design_vbat=788, design_power=5000),
                summary=summary, timestep_halving_max_bus_difference_V=convergence,
                near_limit_refinement=dict(coarse_path_peak_A=coarse["path_peak"], fine_path_peak_A=near["path_peak"]),
                cases=rows)
    save_json("E2", "reference_matrix_python", data)
    save_json("E2", "reference_cases", inputs)


if __name__ == "__main__":
    main()
