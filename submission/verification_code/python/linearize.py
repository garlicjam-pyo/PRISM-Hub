# -*- coding: utf-8 -*-
"""
[공통 도구] 표본화 선형화 — 추가 지연 여유와 불안정 모드 분석(E6, E9)
========================================================================
방법
  시뮬레이션(model_stage_b.simulate)과 똑같은 적분 방식으로 한 제어주기 T(5 µs) 동안의 폐루프 사상
      z_k → z_{k+1},   z = [플랜트 상태 6개, 제어기 내부 상태, 과거 지령 u_{k−1} … u_{k−N}]
  을 계산하고, 평형점에서 수치 야코비안 J를 구한다. J의 고유값 λ의 크기가 모두 1보다 작으면
  (스펙트럼 반경 ρ < 1) 그 운전점에서 국소적으로 안정하다.
  - 전달지연은 제어주기의 정수배가 아니어도 된다(적용 시점을 0.1 µs 적분 간격으로 정확히 반영).
  - 가장 큰 |λ|의 위상각으로 불안정 모드의 주파수를, 고유벡터로 모드의 구성을 알 수 있다.
  - 추가 지연 여유: 추가 지연을 0.1 µs씩 늘리며 처음으로 ρ ≥ 1이 되는 값을 찾는다(상향 탐색).
    안정성이 지연에 대해 단조가 아니므로(더 큰 지연에서 다시 안정해질 수 있음) 이분 탐색을 쓰지 않는다.
한계
  포화가 걸리지 않은 평형점 근방에서만 유효하다(대신호 거동은 비선형 시뮬레이션으로 확인).
"""
from dataclasses import replace
import numpy as np
from model_stage_b import equilibrium, rhs, current_limit

NHIST = 4    # 보관하는 과거 지령 수: 총 지연 < (NHIST−1)·T = 15 µs까지 표현


# ---------------------------------------------------------------- (1) 이득 K로 정의한 비교 설계 구조
def controller_step(x, q, qlink, K, cp):
    """model_stage_b.simulate()의 비교 설계 제어 법칙과 같은 산술."""
    raw = -K[:4] @ x[:4] - K[4] * q
    iref = np.clip(raw, -cp.reference_max, cp.reference_max)
    q = q + cp.Ts * (cp.vref - x[2]) + .1 * (iref - raw) / (-K[4])
    mraw = (x[1] + cp.Rh * x[3] + cp.Lh / cp.inner_tau * (iref - x[3])) / x[4]
    m = float(np.clip(mraw, -cp.modulation_max, cp.modulation_max))
    wlink = 2 * np.pi * cp.link_bw
    rawlink = m * x[3] + cp.Clink * (2 * .7 * wlink * (cp.vlink - x[4]) + wlink * wlink * qlink)
    limit = current_limit(x[2], x[4], cp)
    ilink = float(np.clip(rawlink, -limit, limit))
    qlink = qlink + cp.Ts * (cp.vlink - x[4]) + .1 * (ilink - rawlink) / (cp.Clink * wlink * wlink)
    return np.array([m, ilink]), q, qlink


def period_map(z, vbat, power, p, cp, K, dt=1e-7):
    """한 제어주기 사상. 시각 t의 입력은 '시각 t − 지연' 이전의 가장 최근 표본에서 계산한 지령이다."""
    x, q, qlink, hist = z[:6], z[6], z[7], z[8:].reshape(NHIST, 2)
    u, q, qlink = controller_step(x, q, qlink, K, cp)
    hist = np.vstack([u, hist[:-1]])                     # hist[0] = u_k, hist[1] = u_{k−1}, ...
    n = int(round(cp.Ts / dt))
    for j in range(n):
        idx = int(np.ceil((p.delay - j * dt) / cp.Ts - 1e-9))   # 몇 표본 전의 지령이 적용되는가
        applied = hist[min(max(idx, 0), NHIST - 1)]
        d1 = rhs(x, applied, vbat, power, p)
        x = x + dt * rhs(x + dt * .5 * d1, applied, vbat, power, p)   # simulate()와 같은 중점법
    return np.concatenate([x, [q, qlink], hist.ravel()])


def jacobian(vbat, power, p, cp, K, dt=1e-7):
    """평형점에서 중심차분 야코비안. 두 번째 반환값은 평형점 고정점 오차(정상이면 0)."""
    x, u = equilibrium(vbat, power, p)
    z0 = np.concatenate([x, [-(x[0] + K[:4] @ x[:4]) / K[4], 0.], np.tile(u, NHIST)])
    f0 = period_map(z0, vbat, power, p, cp, K, dt)
    scale = np.maximum(np.abs(z0), 1e-3) * 1e-6
    J = np.empty((len(z0), len(z0)))
    for i in range(len(z0)):
        e = np.zeros(len(z0)); e[i] = scale[i]
        J[:, i] = (period_map(z0 + e, vbat, power, p, cp, K, dt) - period_map(z0 - e, vbat, power, p, cp, K, dt)) / (2 * scale[i])
    return J, float(np.max(np.abs(f0 - z0)[:6] / np.maximum(np.abs(z0[:6]), 1)))


def rho(vbat, power, p, cp, K, dt=1e-7):
    """스펙트럼 반경 ρ = max|λ|."""
    return float(np.max(np.abs(np.linalg.eigvals(jacobian(vbat, power, p, cp, K, dt)[0]))))


def delay_margin(vbat, power, p, cp, K, hi=8e-6, step=1e-7, dt=1e-7):
    """이득 K 구조의 추가 지연 여유(상향 탐색). 공칭에서 이미 불안정하면 −1."""
    unstable = lambda extra: rho(vbat, power, replace(p, delay=p.delay + extra), cp, K, dt) >= 1
    if unstable(0.): return -1.
    for i in range(1, int(round(hi / step)) + 1):
        if unstable(i * step): return (i - 1) * step
    return hi


# ---------------------------------------------------------------- (2) 제어기 객체(채택 설계 포함)
def period_map_ctrl(z, vbat, power, p, ctrl, dt=1e-7):
    """controller_adopted.StageBController 객체를 쓰는 한 제어주기 사상."""
    nc = len(ctrl.state())
    x = z[:6]; ctrl.set_state(z[6:6 + nc]); hist = z[6 + nc:].reshape(NHIST, 2)
    u = ctrl.step(x)
    hist = np.vstack([u, hist[:-1]])
    for j in range(int(round(ctrl.cp.Ts / dt))):
        idx = int(np.ceil((p.delay - j * dt) / ctrl.cp.Ts - 1e-9))
        applied = hist[min(max(idx, 0), NHIST - 1)]
        d1 = rhs(x, applied, vbat, power, p)
        x = x + dt * rhs(x + dt * .5 * d1, applied, vbat, power, p)
    return np.concatenate([x, ctrl.state(), hist.ravel()])


def rho_ctrl(vbat, power, p, make_ctrl, dt=1e-7):
    """make_ctrl(vbat) → 제어기. 반환: (스펙트럼 반경, 지배 모드 주파수 [Hz])."""
    x, u = equilibrium(vbat, power, p)
    ctrl = make_ctrl(vbat); ctrl.reset(x, u)
    z0 = np.concatenate([x, ctrl.state(), np.tile(u, NHIST)])
    scale = np.maximum(np.abs(z0), 1e-3) * 1e-6
    J = np.empty((len(z0), len(z0)))
    for i in range(len(z0)):
        e = np.zeros(len(z0)); e[i] = scale[i]
        J[:, i] = (period_map_ctrl(z0 + e, vbat, power, p, ctrl, dt) - period_map_ctrl(z0 - e, vbat, power, p, ctrl, dt)) / (2 * scale[i])
    lam = np.linalg.eigvals(J); i = int(np.argmax(np.abs(lam)))
    return float(np.abs(lam[i])), float(abs(np.angle(lam[i])) / (2 * np.pi * ctrl.cp.Ts))


def delay_margin_ctrl(vbat, power, p, make_ctrl, hi=8e-6, dt=1e-7, step=1e-7):
    """제어기 객체의 추가 지연 여유(0.1 µs 상향 탐색). 공칭에서 불안정하면 −1."""
    unstable = lambda extra: rho_ctrl(vbat, power, replace(p, delay=p.delay + extra), make_ctrl, dt)[0] >= 1
    if unstable(0.): return -1.
    for i in range(1, int(round(hi / step)) + 1):
        if unstable(i * step): return (i - 1) * step
    return hi
