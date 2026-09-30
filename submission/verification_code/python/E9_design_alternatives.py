"""[E9] 제어기 설계 대안 비교: 채택 설계를 고르기까지 검토하고 기각한 방법들.

■ 목적
  비교 설계(보상 없음, 감쇠비 0.7)의 지연 여유 부족(1.4 µs < 예산 3.0 µs)을 해결하는 방법으로
  (1) 극배치 대역폭 낮춤·극 위치 변경, (2) 큰 전압 편차에서 전압항 포화를 검토했고, 이들이 왜 채택되지
  않았는지를 수치로 남긴다(보고서 4.5절). 또 비교 설계의 지연 한계 모드가 무엇인지 확인한다.

■ 왜 필요한가
  연산 지연 보상(예측)은 제어기 구현을 복잡하게 하므로, 더 단순한 대안으로 같은 목표를 달성할 수 없음을
  보여야 채택 근거가 선다. 또한 "기존 제어기가 통과한 사례에 숨은 내부 진동이 없었는지"를 선형화로
  확인해 비교 설계의 격자 결과가 유효함을 보인다.

■ 방법 (모두 평균모델, linearize.py·stage_b 시뮬레이션)
  1) 비교 설계 구조에서 극배치 대역폭(2.5–4.8 kHz)과 가장 빠른 극 위치(1.5ω, 2.5ω)를 바꿔 가며
     선형화 추가 지연 여유(640·920 V, 25 kW 중 최소, 0.1 µs 상향 탐색, 상한 8 µs)를 구한다.
  2) 대역폭을 낮춘 두 설계(3.0 kHz·1.5ω, 2.5 kHz·2.5ω)를 640 V 비선형 시뮬레이션으로 확인한다
     (Tier-1 15→25 kW, Tier-2 1→25 kW, 공칭과 L_h −10 %).
  3) 비교 설계 이득 + 예측에서 버스전압 비례이득을 α배로 줄였을 때의 최대 스펙트럼 반경(안정성).
  4) 비교 설계 이득 + 예측에서 전압 편차를 ±E V로 포화시켰을 때의 1→25 kW 경로전류와 25→1 kW 거동.
  5) 비교 설계의 지연 한계 모드(추가 지연 +1.5 µs, 640 V, 25 kW): 주파수와 고유벡터 구성.
  6) 비교 설계, 단일 변수 공차 16종에서 공칭 지연의 최대 스펙트럼 반경(숨은 진동이 없는지).

■ 판정(해석)
  1)·2) 대역폭을 낮추면 지연 여유는 늘지만 전압강하·경로전류가 기준을 넘고 L_h −10 %에서 버스가 붕괴
  3)·4) 비례이득이 약 0.35–0.5배 아래로 줄면 ρ > 1(불안정), 포화 폭 1.5 V에서 한계 순환
  5)    약 30 kHz 모드, 브리지 전류 i_h와 변조율 지령 m에 집중(내부 전류루프 모드)
  6)    ρ < 1 이면 비교 설계의 통과 사례에 숨은 진동이 없다.

■ 실행   python E9_design_alternatives.py      (약 5–10분)
■ 결과   results/E9/exploration.json
"""
import itertools
from dataclasses import replace

import numpy as np

from model_stage_b import simulate
from controller_reference import NOMINAL, GAIN, assess
from controller_adopted import StageBController, design_poles
from linearize import delay_margin, rho_ctrl, jacobian
from common import save_json


def run(v, a, b, p, K, cp, **opt):
    """640 V 등에서 20 ms 비선형 시험(전압 품질 판정 포함)."""
    c = StageBController(K, cp, v, **opt)
    r = simulate(v, a, b, p=p, K=K, control_p=cp, duration=.02, dt=2e-7, keep_trace=True, controller=c)
    r.update(assess(r['t'], r['x'], .001, r['completed'], r['within_port_limits']))
    return dict(path_peak=r['path_peak'], droop=r['droop'], completed=r['completed'], tail_ripple_V=r['tail_ripple_V'],
                requirements_pass=r['requirements_pass'], failed=[k for k, c in r['checks'].items() if not c])


def main():
    print("[E9] 제어기 설계 대안 비교")
    out = {}
    # 1) 대역폭·가장 빠른 극 위치 변경(보상 없음 구조)
    scan = []
    for bw, a3 in itertools.product([2.5e3, 3.0e3, 3.5e3, 4.0e3, 4.8e3], [1.5, 2.5]):
        cp = replace(NOMINAL, bus_bw=bw); K = design_poles(788, 5000, cp, a=(1., 1 / 3, a3))
        dm = min(delay_margin(v, 25000, NOMINAL, cp, K, hi=8e-6) for v in (640, 920))
        scan.append(dict(bus_bw=bw, fastest_pole=a3, delay_margin_us=round(dm * 1e6, 2)))
        cap = " 이상(탐색 상한)" if dm >= 8e-6 - 1e-12 else ""
        print(f"   1) 대역폭 {bw/1e3:.1f} kHz, 가장 빠른 극 {a3}ω: 추가 지연 여유 {dm*1e6:.1f} µs{cap}")
    out['bandwidth_scan'] = scan
    # 2) 대역폭을 낮춘 설계의 비선형 확인(640 V)
    low = []
    for bw, a3 in [(3.0e3, 1.5), (2.5e3, 2.5)]:
        cp = replace(NOMINAL, bus_bw=bw); K = design_poles(788, 5000, cp, a=(1., 1 / 3, a3))
        for name, p in [('nominal', NOMINAL), ('Lhx0.9', replace(NOMINAL, Lh=NOMINAL.Lh * .9))]:
            for a, b in [(15000, 25000), (1000, 25000)]:
                r = run(640., a, b, p, K, cp)
                low.append(dict(bus_bw=bw, fastest_pole=a3, plant=name, p0=a, p1=b, **r))
                print(f"   2) {bw/1e3:.1f} kHz·{a3}ω, {name}, {a/1e3:g}→{b/1e3:g} kW: 강하 {r['droop']:.1f} V, "
                      f"경로 {r['path_peak']:.1f} A, {'완료' if r['completed'] else '붕괴'}")
    out['low_bandwidth_nonlinear_640V'] = low
    # 3) 버스전압 비례이득 축소(비교 설계 이득 + 예측)
    K = np.array(GAIN); alpha = []
    for al in [1., .75, .5, .35, .25, 0.]:
        Ka = K.copy(); Ka[2] *= al
        r = max(rho_ctrl(v, P, NOMINAL, lambda vb: StageBController(Ka, NOMINAL, vb, predict=True))[0]
                for v in (640., 920.) for P in (1000., 25000.))
        alpha.append(dict(alpha=al, max_spectral_radius=r))
        print(f"   3) 비례이득 × {al}: 최대 스펙트럼 반경 {r:.4f} {'(불안정)' if r >= 1 else ''}")
    out['voltage_gain_scaling_with_prediction'] = alpha
    # 4) 전압 편차 포화(비교 설계 이득 + 예측)
    up = [dict(E=E, **run(640., 1000, 25000, NOMINAL, K, NOMINAL, predict=True, vdev_limit=E)) for E in (None, 3.0, 2.0)]
    dn = [dict(E=E, **run(640., 25000, 1000, NOMINAL, K, NOMINAL, predict=True, vdev_limit=E)) for E in (2.0, 1.5)]
    for r in up: print(f"   4) 포화 폭 E = {r['E']} V, 1→25 kW: 경로 {r['path_peak']:.2f} A")
    for r in dn: print(f"   4) 포화 폭 E = {r['E']} V, 25→1 kW: 마지막 1 ms 리플 {r['tail_ripple_V']:.2f} V, {'통과' if r['requirements_pass'] else '실패'}")
    out['hard_voltage_limit'] = dict(gain='비교 설계 이득 + 예측', load_step_1_to_25kW=up, unload_25_to_1kW=dn)
    # 5) 비교 설계의 지연 한계 모드(총 지연 6.5 µs = 모델 5 µs + 1.5 µs)
    J, _ = jacobian(640, 25000, replace(NOMINAL, delay=6.5e-6), NOMINAL, K)
    lam, V = np.linalg.eig(J); i = int(np.argmax(abs(lam))); v = V[:, i]
    names = ['i_p', 'v_s', 'v_bus', 'i_h', 'v_link', 'i_dab', 'q', 'q_link'] + \
            [f'{s}(k-{k})' for k in range(1, 5) for s in ('m', 'i_link')]
    scale = np.array([10, 10, 1, 10, 1, 10, 1e-3, 1e-3] + [.1, 10] * 4)       # 상태별 크기 정규화
    w = abs(v) / scale; w /= w.max()
    mode = dict(delay_s=6.5e-6, spectral_radius=float(abs(lam[i])), frequency_hz=float(abs(np.angle(lam[i])) / (2 * np.pi * 5e-6)),
                normalized_participation=dict(sorted(zip(names, map(float, w)), key=lambda t: -t[1])[:6]))
    print(f"   5) 비교 설계 지연 한계 모드: ρ = {mode['spectral_radius']:.4f}, {mode['frequency_hz']/1e3:.1f} kHz, "
          f"주 구성 {list(mode['normalized_participation'])[:3]}")
    out['delay_limited_mode_reference'] = mode
    # 6) 비교 설계, 단일 변수 공차 16종의 공칭 지연 안정성
    tol = [replace(NOMINAL, **{f: getattr(NOMINAL, f) * k}) for f in ['L', 'Cs', 'Cb', 'Lh', 'Clink', 'R', 'Rh'] for k in (.9, 1.1)]
    tol += [replace(NOMINAL, tau=15e-6), replace(NOMINAL, eta=.94)]
    rmax = max(rho_ctrl(v, P, p, lambda vb: StageBController(K, NOMINAL, vb))[0] for p in tol for v in (640., 920.) for P in (1000., 25000.))
    print(f"   6) 비교 설계, 공차 16종 최대 스펙트럼 반경 {rmax:.4f}")
    out['reference_tolerance_linear_check'] = dict(sets=len(tol), max_spectral_radius=rmax)
    save_json("E9", "exploration", out)


if __name__ == "__main__":
    main()
