"""[E2-a] Stage B 평균모델의 정합성 검산 (에너지 보존, 평형점, 적분간격 수렴, 12개 동적 사례).

■ 목적
  E3–E9의 모든 Stage B 수치는 model_stage_b.py의 6상태 평균모델에서 나온다. 그 수치가 방정식·구현
  오류가 아니라 모델의 물리 거동임을 먼저 확인한다(보고서 5.3절).

■ 왜 필요한가
  평균모델은 하드웨어 측정으로 바로 확인할 수 없으므로, 모델 자체가 에너지를 만들거나 잃지 않는지,
  정상점이 실제로 평형인지, 수치 적분 오차가 판정을 바꾸지 않는지를 독립적으로 보여야 한다.
  또한 같은 사례를 MATLAB으로 따로 구현해 돌려(matlab/E2_two_stage_crosscheck.m) 구현 실수를 걸러낸다.

■ 방법
  1) 평형점 잔차: 6개 배터리 전압 × 4개 부하(−5, 0, 5, 25 kW) = 24점에서 rhs(x_eq) ≈ 0 인지 확인.
  2) 에너지 보존: 무작위 상태·입력 1,000개에서
     d/dt(저장에너지) = 입력전력 − 저항손실 − 부하 − DAB 손실 이 성립하는지(잔차 < 1e-7 W).
  3) 동적 사례 12개: 정격 스텝(5→25 kW, 5개 전압), 부하 감소, 회생, 영교차, 그리고 일부러 실패해야
     하는 2개(36 kW 과부하, 지령 포화 100 A로 여유를 없앤 경우). 실패 사례가 실패로 판정되는지도 본다.
     이 사례들은 운전점별로 극배치한 이득(design)을 쓰는 모델 검산용이며 제어기 평가가 아니다.
  4) 적분간격 수렴: 640 V 정격 사례를 0.2 µs와 0.1 µs로 적분해 버스전압 차이 < 0.05 V.
  5) MATLAB 입력 파일(two_stage_cases.json)을 내보낸다. 같은 이득·파라미터로 MATLAB이 독립 적분한다.

■ 판정 기준
  평형점 미분 최대 < 1e-5, 에너지 잔차 < 1e-7 W, 정상 사례 10개 통과, 실패 사례 2개 실패,
  적분간격 절반 시 버스전압 차 < 0.05 V (보고서: < 1 mV)

■ 실행   python E2a_model_consistency.py      (약 20초)
■ 결과   results/E2/two_stage_python.json, results/E2/two_stage_cases.json, results/E2/E2_two_stage.png
"""
from dataclasses import replace
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from model_stage_b import (Parameters, equilibrium, rhs, energy_residual, simulate,
                           primary_power, steady_feasible, continuous_power_limit)
from common import save_json, verdict, outdir


def main():
    print("[E2-a] Stage B 평균모델 정합성")
    p = Parameters()

    # 1) 평형점 잔차 (24점)
    steady = []; max_rhs = 0.
    for v in [640, 648, 788, 800, 907, 920]:
        for power in [-5000, 0, 5000, 25000]:
            x, u = equilibrium(v, power, p)
            max_rhs = max(max_rhs, float(np.max(np.abs(rhs(x, u, v, power, p)))))
            steady.append(dict(vbat=v, power=power, x=x, u=u,
                               dab_primary_power=primary_power(x[4] * x[5], p),
                               feasible=steady_feasible(v, power, p)))
    verdict("평형점 24개의 상태 미분 최대 < 1e-5", max_rhs < 1e-5, f"{max_rhs:.2e}")

    # 2) 에너지 보존 (무작위 1,000개 상태·입력)
    rng = np.random.default_rng(71); max_balance = 0.
    for _ in range(1000):
        x = np.array([rng.uniform(-100, 100), rng.uniform(-90, 90), rng.uniform(360, 420),
                      rng.uniform(-100, 100), rng.uniform(90, 110), rng.uniform(-80, 80)])
        u = np.array([rng.uniform(-.95, .95), rng.uniform(-80, 80)])
        v = rng.uniform(640, 920); power = rng.uniform(-5000, 30000)
        max_balance = max(max_balance, abs(energy_residual(x, rhs(x, u, v, power, p), v, power, p)))
    verdict("에너지 보존 잔차(임의 상태 1,000개) < 1e-7 W", max_balance < 1e-7, f"{max_balance:.2e} W")

    # 3) 동적 사례 12개 (마지막 2개는 실패해야 정상)
    specs = [(f"rated_{v}", v, 5000, 25000, p) for v in [640, 648, 788, 907, 920]]
    specs += [("unload_640", 640, 25000, 5000, p), ("unload_920", 920, 25000, 5000, p),
              ("regeneration_640", 640, 5000, -5000, p), ("regeneration_920", 920, -5000, 5000, p),
              ("zero_crossing_800", 800, 5000, -5000, p),
              ("overload_648", 648, 20000, 36000, p),                               # 정격 초과: 포트 한계 위반 예상
              ("no_control_reserve_640", 640, 5000, 25000, replace(p, reference_max=100))]   # 지령 여유 없음: 100 A 초과 예상
    cases = []; traces = {}
    for name, v, a, b, params in specs:
        r = simulate(v, a, b, params, keep_trace=True)
        traces[name] = (r.pop("t"), r.pop("x"), r.pop("u"))
        r["name"] = name; cases.append(r)
        print(f"   {name:24s} 강하 {r['droop']:7.3f} V, 경로 피크 {r['path_peak']:7.3f} A, "
              f"포트 한계 {'이내' if r['within_port_limits'] else '위반'}, 전압 품질 {'통과' if r['voltage_quality_pass'] else '실패'}")
    normal = [c for c in cases if c["name"].startswith(("rated", "unload", "regeneration", "zero_crossing"))]
    verdict("정상 사례 10개: 완료·포트 한계 이내·전압 품질 통과",
            all(c["completed"] and c["within_port_limits"] and c["voltage_quality_pass"] for c in normal))
    verdict("과부하 36 kW: 포트 한계 위반과 전압 품질 실패로 판정",
            not cases[-2]["within_port_limits"] and not cases[-2]["voltage_quality_pass"])
    verdict("지령 포화 100 A: 전압 품질은 통과하지만 포트 한계 위반으로 판정",
            not cases[-1]["within_port_limits"] and cases[-1]["voltage_quality_pass"])
    verdict("600 V: 정상점 불성립, 연속 한계 0 W", not steady_feasible(600, 0, p) and continuous_power_limit(600, p) == 0)

    # 4) 적분간격 수렴 (0.2 µs vs 0.1 µs, 같은 표본 시점 비교)
    refined = simulate(640, dt=1e-7, keep_trace=True)
    voltage_error = float(np.max(np.abs(refined["x"][1::2, 2] - traces["rated_640"][1][:, 2])))
    verdict("적분간격 0.2 → 0.1 µs 버스전압 최대 차 < 0.05 V", voltage_error < .05, f"{voltage_error*1e3:.3f} mV")

    result = dict(scope="유한 링크 평균모델 정합성 검산(하드웨어·스위칭 검증 아님)",
                  max_energy_residual_W=max_balance, max_equilibrium_derivative=max_rhs,
                  timestep_halving_max_bus_difference_V=voltage_error, steady=steady, cases=cases,
                  static_power_limit_W={str(v): continuous_power_limit(v, p) for v in [600, 620, 625, 640, 648, 788, 920]})
    save_json("E2", "two_stage_python", result)
    # MATLAB 독립 구현이 읽을 입력(같은 이득·파라미터)
    inputs = [dict(name=r["name"], vbat=r["vbat"], power0=r["power0"], power1=r["power1"],
                   dt=r["dt"], duration=r["duration"], K=r["K"], parameters=r["parameters"]) for r in cases]
    save_json("E2", "two_stage_cases", inputs)

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for name, label in [("rated_640", "640 V"), ("rated_920", "920 V"),
                        ("no_control_reserve_640", "640 V, 100 A reference (expected fail)")]:
        t, x, u = traces[name]; keep = slice(None, None, 25)
        for ax, data in zip(axes.flat, [x[:, 2], x[:, 0], x[:, 4], x[:, 5]]):
            ax.plot(t[keep] * 1e3, data[keep], label=label, lw=1)
    axes[0, 1].axhline(100, color="r", ls="--", lw=.8)
    for ax, label in zip(axes.flat, ["Bus voltage (V)", "Path current (A)", "Link voltage (V)", "DAB link current (A)"]):
        ax.set_ylabel(label); ax.grid(alpha=.3); ax.set_xlim(.8, 2.5)
    axes[0, 0].legend(fontsize=7); axes[1, 0].set_xlabel("Time (ms)"); axes[1, 1].set_xlabel("Time (ms)")
    fig.suptitle("E2-a: finite-link averaged model, 5 -> 25 kW at 1 ms")
    fig.tight_layout(); fig.savefig(outdir("E2") / "E2_two_stage.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    main()
