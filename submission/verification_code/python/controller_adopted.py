# -*- coding: utf-8 -*-
"""
[공통 모델] 채택 제어기: 연산 지연 보상(1주기 예측)을 적용한 Stage B 제어기
========================================================================
보고서 4.5절의 제어기. 비교 설계와 구조·설계점(788 V, 5 kW)은 같고 두 가지만 다르다.
  (1) 연산 지연 보상: 매 제어주기에 직전 지령 m(k−1)과 공칭 모델로 고속 상태 [i_p, v_s, i_h]를
      한 주기(5 µs) 앞으로 예측하고, 그 예측값으로 지령을 계산한다.
      - 근거: S. Bibian, H. Jin, IEEE TPEL 15(5), 2000 (디지털 제어 지연의 예측 보상)
      - v_bus, v_link는 측정값을 그대로 쓴다 → 부하전류 센서 불필요
      - 예측 적분: 중점법 1 µs × 5단계(주기당 약 150회 곱셈·덧셈)
  (2) 주 극점 감쇠비 0.7 → 0.95(재충전 전류 오버슈트 감소). 극 = {−ζω ± jω√(1−ζ²), −ω, −ω/3, −2.5ω},
      ω = 2π·4.8 kHz.

StageBController의 선택 기능
  predict    : 1주기 예측 사용 여부(False이면 비교 설계와 비트 단위로 같은 결과)
  vdev_limit : 버스전압 편차 포화 폭 E [V] — 기각한 대안(E9) 재현용. 채택 설계에서는 쓰지 않는다.
"""
from dataclasses import replace
import numpy as np
from scipy.signal import place_poles
from model_stage_b import equilibrium, primary_power, current_limit
from controller_reference import NOMINAL, GAIN

ZETA, POLES = .95, (1., 1 / 3, 2.5)        # 채택 설계의 극 배치 파라미터
CP = replace(NOMINAL, bus_bw=4800.)        # 제어기 공칭 파라미터


def design_poles(vbat, power, p, z=.7, a=(1., 1 / 3, 2.5)):
    """축약 4상태 모델 + 버스전압 적분(5상태)에 대한 극배치. z=0.7, a=(1,1/3,2.5)이면 비교 설계와 같다."""
    xe, _ = equilibrium(vbat, power, p)
    def reduced(x):
        ip, vs, vb, ih = x
        pin = primary_power((vs + p.Rh * ih) * ih, p)
        return np.array([(vbat / 2 - p.R * ip + vs - vb) / p.L, (ih - ip) / p.Cs,
                         (ip - (power + pin) / vb) / p.Cb, -ih / p.inner_tau])
    h = 1e-4
    J = np.column_stack([(reduced(xe[:4] + e) - reduced(xe[:4] - e)) / (2 * h) for e in np.eye(4) * h])
    A = np.zeros((5, 5)); A[:4, :4] = J; A[4, 2] = -1
    B = np.zeros((5, 1)); B[3, 0] = 1 / p.inner_tau
    w = 2 * np.pi * p.bus_bw
    poles = [-z * w + 1j * w * np.sqrt(1 - z * z), -z * w - 1j * w * np.sqrt(1 - z * z)] + [-ai * w for ai in a]
    return place_poles(A, B, poles).gain_matrix[0]


# 채택 설계 이득: 약 [−1.5814, 1.1113, 1.5398, 0.6419, −12687.0]
K_ADOPTED = design_poles(788, 5000, CP, z=ZETA, a=POLES)


class StageBController:
    """표본화(5 µs) Stage B 제어기. model_stage_b.simulate(controller=...)에 넘겨 쓴다."""
    def __init__(self, K, cp, vbat, predict=False, vdev_limit=None, n_sub=5):
        self.K, self.cp, self.vbat = np.asarray(K, float), cp, float(vbat)   # V_bat은 측정값으로 가정
        self.predict, self.vdev_limit, self.n_sub = predict, vdev_limit, n_sub
        self.wlink = 2 * np.pi * cp.link_bw

    def reset(self, x, u):
        """평형점에서 시작: 적분기를 지령 = i_p가 되도록 초기화."""
        self.q = -(x[0] + self.K[:4] @ x[:4]) / self.K[4]
        self.qlink = 0.
        self.u_prev = np.array(u, float)

    def state(self):
        """선형화(linearize.py)에서 쓰는 제어기 내부 상태 [q, q_link, m(k−1), i_link(k−1)]."""
        return np.concatenate([[self.q, self.qlink], self.u_prev])

    def set_state(self, s):
        self.q, self.qlink, self.u_prev = float(s[0]), float(s[1]), np.array(s[2:4], float)

    def _predict(self, x):
        """고속 상태 [i_p, v_s, i_h]를 직전 변조율 m(k−1)로 한 주기 앞까지 적분(공칭 모델, 중점법)."""
        cp = self.cp; ip, vs, vb, ih, vl = x[:5]; m = self.u_prev[0]
        h = cp.Ts / self.n_sub
        def f(s):
            ip, vs, ih = s
            return np.array([(self.vbat / 2 - cp.R * ip + vs - vb) / cp.L, (ih - ip) / cp.Cs,
                             (m * vl - vs - cp.Rh * ih) / cp.Lh])
        s = np.array([ip, vs, ih])
        for _ in range(self.n_sub):
            s = s + h * f(s + .5 * h * f(s))
        xp = np.array(x, float); xp[0], xp[1], xp[3] = s
        return xp

    def step(self, x):
        """한 제어주기의 지령 계산. 반환: [변조율 m, DAB 링크전류 지령]."""
        cp, K = self.cp, self.K
        xs = self._predict(x) if self.predict else x                 # (1) 연산 지연 보상
        vb_term = xs[2]
        if self.vdev_limit is not None:                              # (E9 전용) 전압항 포화
            vb_term = cp.vref - np.clip(cp.vref - xs[2], -self.vdev_limit, self.vdev_limit)
        raw = -(K[0] * xs[0] + K[1] * xs[1] + K[2] * vb_term + K[3] * xs[3]) - K[4] * self.q
        iref = np.clip(raw, -cp.reference_max, cp.reference_max)     # 브리지 전류지령 ±84 A
        self.q += cp.Ts * (cp.vref - x[2]) + .1 * (iref - raw) / (-K[4])   # 적분(측정 v_bus) + 역포화
        mraw = (xs[1] + cp.Rh * xs[3] + cp.Lh / cp.inner_tau * (iref - xs[3])) / xs[4]
        m = float(np.clip(mraw, -cp.modulation_max, cp.modulation_max))
        w = self.wlink
        rawlink = m * xs[3] + cp.Clink * (2 * .7 * w * (cp.vlink - x[4]) + w * w * self.qlink)
        limit = current_limit(x[2], x[4], cp)
        ilink = float(np.clip(rawlink, -limit, limit))
        self.qlink += cp.Ts * (cp.vlink - x[4]) + .1 * (ilink - rawlink) / (cp.Clink * w * w)
        self.u_prev = np.array([m, ilink])
        return self.u_prev.copy()


def make(vbat, design='adopted'):
    """시험용 제어기 생성. design='adopted'(채택 설계) 또는 'reference'(비교 설계)."""
    if design == 'reference':
        return StageBController(np.array(GAIN), NOMINAL, vbat)
    return StageBController(K_ADOPTED, CP, vbat, predict=True)
