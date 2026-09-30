"""[공통 시험 정의] Stage B 동특성 시험의 조건·판정 기준 (E4, E5–E7, E9가 공유).

■ 시험 등급 (보고서 3.4–3.5절, 표 2)
  Tier-1 : 부하 계약 안의 최악 변화. 계약 범위(−3.2–25 kW) 안의 ±10 kW 스텝 10종.
           판정 = 전압 품질 6개 항목(controller_reference.assess) + 포트 물리 한계
                  + 경로전류·브리지 필터 전류 ≤ 90 A
  Tier-2 : 계약 위반(부하 승인 계층 실패)을 가정한 1↔25 kW 스텝.
           판정 = 완료 + 포트 물리 한계 + 경로·필터 전류 ≤ 93.75 A(= 100 A 정격 − 스위칭 리플 반진폭 6.25 A)
                  + 스텝 후 버스 384–416 V + 20 ms 시점 400 ± 4 V
  공통 추가 판정(내부 진동 검사): 마지막 1 ms의 i_h 변동폭 ≤ 1 A, 변조율 변동폭 ≤ 0.01.
           평균모델의 정상상태는 일정해야 하는데, 지연이 크면 브리지 전류·변조율만 100 kHz로
           진동하고 버스 리플은 수 mV에 그칠 수 있어 전압 판정만으로는 불안정을 놓치기 때문이다.

■ 파라미터 집합
  모든 전압(632, 640, 660, 700, 788, 860, 920 V): 공칭, 추가 지연 +3.0 µs
  640·920 V: L, Cs, Cb, Lh, Clink, R, Rh 각각 ±10 %(단일 변수), DAB 시정수 15 µs, 효율 0.94
  → Tier-1 390건(지연 제외) + 70건(지연 +3.0 µs), Tier-2 78건(지연 제외) + 14건(지연) = 552건
  제어기는 항상 공칭 파라미터를 쓰며 플랜트 공차를 모른다.

■ 부하 계약 최악 시퀀스 (Tier-1 단일 스텝이 실제 계약을 대표하는지 확인)
  증가: 12.7 → 25 kW (V2L +3.8 kW 계단, Stage C −3.2 → +5.3 kW를 4 kW/ms, 컴프레서·D 부하 +0.06 kW/ms)
  감소: 25 → −3.2 kW (V2L −3.8 kW, Stage C +5.3 → −3.2 kW를 4 kW/ms, 컴프레서·D 부하 −0.5 kW/ms)
  각각 연속 램프와 1 ms 계단 형태.
"""
from dataclasses import replace
import numpy as np

from model_stage_b import simulate
from controller_reference import NOMINAL, assess
from controller_adopted import make, K_ADOPTED, CP

T1_LIMIT_A = 90.
T2_BAND = (384., 416.)
T2_LIMIT_A = 100. - 6.25
DELAY_BUDGET = 3.0e-6
T1_STEPS = [(0, 10000), (5000, 15000), (10000, 20000), (15000, 25000),
            (10000, 0), (15000, 5000), (20000, 10000), (25000, 15000),
            (-3200, 6800), (6800, -3200)]
T2_STEPS = [(1000, 25000), (25000, 1000)]
V_ALL = [632, 640, 660, 700, 788, 860, 920]
V_TOL = [640, 920]
FIELDS = ['L', 'Cs', 'Cb', 'Lh', 'Clink', 'R', 'Rh']
TAIL_IH_PP_A, TAIL_M_PP = 1.0, .01


def param_sets():
    """(모든 전압에 쓰는 집합, 640·920 V에만 쓰는 공차·민감도 집합)"""
    sets = {"nominal": NOMINAL, "delay+3.0us": replace(NOMINAL, delay=NOMINAL.delay + DELAY_BUDGET)}
    tol = {}
    for field in FIELDS:
        for f in [.9, 1.1]:
            tol[f"{field}x{f}"] = replace(NOMINAL, **{field: getattr(NOMINAL, field) * f})
    tol["tau15us"] = replace(NOMINAL, tau=15e-6)
    tol["eta0.94"] = replace(NOMINAL, eta=.94)
    return sets, tol


def grid_jobs():
    """Tier-1·Tier-2 격자 552건: (등급, 집합 이름, V_bat, 스텝 전 전력, 스텝 후 전력, 플랜트 파라미터)"""
    sets, tol = param_sets()
    js = []
    for v in V_ALL:
        for name, p in sets.items():
            js += [(1, name, float(v), a, b, p) for a, b in T1_STEPS]
            js += [(2, name, float(v), a, b, p) for a, b in T2_STEPS]
    for v in V_TOL:
        for name, p in tol.items():
            js += [(1, name, float(v), a, b, p) for a, b in T1_STEPS]
            js += [(2, name, float(v), a, b, p) for a, b in T2_STEPS]
    return js


def sim(vbat, a, b, p, dt=None, design="adopted", power_fn=None):
    """제어기 객체(채택 또는 비교 설계)로 20 ms 폐루프 시험을 한다. 1 ms에 a → b 스텝.
    적분간격은 기본 0.2 µs, 전달지연이 0.2 µs의 배수가 아니면 0.1 µs."""
    if dt is None:
        dt = 1e-7 if abs(p.delay / 2e-7 - round(p.delay / 2e-7)) > 1e-9 else 2e-7
    c = make(vbat, design)
    r = simulate(vbat, a, b, p=p, K=K_ADOPTED, control_p=CP, duration=.02, dt=dt, keep_trace=True,
                 controller=c, power_fn=power_fn)
    r.update(assess(r['t'], r['x'], .001, r['completed'], r['within_port_limits']))
    return r


def judge(tier, r):
    """Tier별 판정(모듈 설명 참고). 판정에 쓴 지표와 실패 항목을 함께 돌려준다."""
    post = r['x'][r['t'] >= .001, 2]
    tail = r['t'] >= r['t'][-1] - .001
    ih_pp = float(np.ptp(r['x'][tail, 3])); m_pp = float(np.ptp(r['u'][tail, 0]))
    internal_ok = bool(ih_pp <= TAIL_IH_PP_A and m_pp <= TAIL_M_PP)
    row = dict(path_peak=r['path_peak'], bridge_peak=r['bridge_peak'], link_peak=r['link_peak'],
               dab_power_peak=r['dab_power_peak'], droop=r['droop'], vbus_min_post=float(post.min()),
               vbus_max_post=float(post.max()), recovery_s=r['recovery_s'], tail_ripple_V=r['tail_ripple_V'],
               modulation_peak=r['modulation_peak'], series_peak=r['series_peak'], vlink_min=r['vlink_min'],
               tail_ih_pp_A=ih_pp, tail_m_pp=m_pp,
               failed=[k for k, c in r['checks'].items() if not c] + ([] if internal_ok else ['internal_tail_oscillation']),
               ports_violated=[k for k, v in r['violations'].items() if v])
    if tier == 1:
        row['pass_'] = bool(r['requirements_pass'] and internal_ok
                            and r['path_peak'] <= T1_LIMIT_A and r['bridge_peak'] <= T1_LIMIT_A)
    else:
        row['pass_'] = bool(r['completed'] and r['within_port_limits'] and post.min() >= T2_BAND[0]
                            and post.max() <= T2_BAND[1] and abs(r['x'][-1, 2] - 400) <= 4
                            and r['path_peak'] <= T2_LIMIT_A and r['bridge_peak'] <= T2_LIMIT_A and internal_ok)
        # Tier-2는 전압 6항목 대신 대역·최종값으로 판정하므로 실패 사유를 다시 적는다
        row['failed'] = [k for k, ok in [('completed', r['completed']), ('ports', r['within_port_limits']),
                                         ('bus_band_384_416V', T2_BAND[0] <= post.min() and post.max() <= T2_BAND[1]),
                                         ('final_voltage', abs(r['x'][-1, 2] - 400) <= 4),
                                         ('internal_tail_oscillation', internal_ok)] if not ok]
    limit = T1_LIMIT_A if tier == 1 else T2_LIMIT_A
    if max(r['path_peak'], r['bridge_peak']) > limit:
        row['failed'].append(f'current>{limit:g}A')
    return row


T0 = 1e-3


def seq_up(discrete):
    """부하 증가 최악 시퀀스 12.7 → 25 kW (discrete=True면 1 ms 계단)."""
    def f(t):
        if t < T0: return 12700.
        s = (t - T0) * 1e3                                   # 시작 후 경과 [ms]
        sc = min(8500., (np.floor(s) + 1) * 4000. if discrete else s * 4000.)   # Stage C −3.2 → +5.3 kW
        slow = 60. * s * 3                                   # 컴프레서 + D 부하 2개, 각 ≤ 0.06 kW/ms
        return min(25000., 12700. + 3800. + sc + slow)       # + V2L 3.8 kW 계단
    return f


def seq_down(discrete):
    """부하 감소 최악 시퀀스 25 → −3.2 kW."""
    def f(t):
        if t < T0: return 25000.
        s = (t - T0) * 1e3
        sc = min(8500., (np.floor(s) + 1) * 4000. if discrete else s * 4000.)
        comp = min(6000., 500. * s); ptc = min(7000., 500. * s); bh = min(2900., 500. * s)
        return max(-3200., 25000. - 3800. - sc - comp - ptc - bh)
    return f


SEQUENCES = {'up_ramp': seq_up(False), 'up_stair': seq_up(True),
             'down_ramp': seq_down(False), 'down_stair': seq_down(True)}
