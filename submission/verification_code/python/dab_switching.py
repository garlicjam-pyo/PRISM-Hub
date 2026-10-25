"""DAB 스위칭 수준 정상상태 모의: 데드타임, 소자 출력용량, 역방향 도통 전압을 넣은 시간 영역 계산(E21, TB11 공용).

목적
  dab_modulation.py의 EPS 지령표는 이상 소자 파형(데드타임·출력용량·소자 강하 없음)이다. TB10 회로에서는 링크 붕괴 구간의
  DAB 링크 쪽 첨두가 해석 상한(1.5 × 정격점)의 1.10–1.16배였다. 이 모듈은 회로와 같은 소자 조건으로 한 운전점의 주기 정상상태를
  계산해 (1) 초과를 재현하는지, (2) 지령표 첨두를 회로 효과 반영값으로 바꾸면 상한을 지키는지 확인한다.

모델(TB10 회로의 DAB와 같은 구성)
  1차 풀브리지(버스 v_bus) – 누설 L_dab·R_dab(1차) – 이상 변압기 n:1 – 2차 풀브리지(링크 v_link).
  레그마다 목표가 바뀌면 켜진 소자를 바로 끄고 데드타임 t_d 뒤 새 소자를 켠다(ctrl/prism_gate_stageB_e.m과 같음).
  두 소자가 꺼진 동안 레그 중점 전압은 두 소자의 출력용량 2·C_oss를 그 레그로 들어오는 전류로 충방전하고,
  레일을 넘으면 역방향 도통(V_f)으로 묶인다. 켜진 소자는 중점을 레일에 붙인다(경 스위칭이면 즉시).
  EPS 게이트: 1차 레그 1은 가상 에지(0, π)에서, 레그 2는 D1·π 늦게 바뀐다. 2차 두 레그는 φ(등가 SPS 위상)에서 바뀐다.
  초기 전류는 이상 해석(dab_modulation.wave_norm)의 반주기 대칭 값으로 두고, 주기 평균 전류(직류 편류)를 빼며
  정상상태까지 반복한다(R_dab/L_dab 시정수가 수백 주기라 그냥 두면 수렴이 느림).
출력  링크 쪽 첨두 n·max|i_L|, 링크로 가는 평균전류(+ = 1차 → 링크), 1차 첨두.
"""
import math

import numpy as np

try:
    from numba import njit
except ImportError:                                           # numba가 없으면 순수 Python(느림)
    def njit(*a, **k):
        def deco(f):
            return f
        return deco if not (len(a) == 1 and callable(a[0])) else a[0]

TD = 100e-9          # DAB 데드타임(prism_hub_params B.td_d)
COSS_P = 335e-12     # 1차 소자 C_o(tr)(TB04B·TB08·TB10)
COSS_S = 1371e-12    # 2차 소자 C_oss(tr)
VF = 2.0             # 꺼진 GaN 역방향 도통(TB09·TB10 회로)
RDAB = 0.02          # 누설 인덕터 권선저항(1차 환산)


@njit(cache=True)
def _leg_target(theta, edge):
    """반주기 구형파: [edge, edge + π)에서 1(상측), 나머지 0. theta, edge는 [0, 2π)."""
    x = theta - edge
    while x < 0.:
        x += 2. * math.pi
    while x >= 2. * math.pi:
        x -= 2. * math.pi
    return 1 if x < math.pi else 0


@njit(cache=True)
def _sim(vb, vl, n, L, R, fs, D1, phi, i0, td, cp, cs, vf, ndt, nper, nfix):
    """한 운전점. 반환 (n·max|i_L|, 링크 평균전류, 1차 첨두, 마지막 주기 평균 i_L)."""
    T = 1. / fs
    dt = T / ndt
    w = 2. * math.pi * fs
    ndd = int(round(td / dt))
    e = [0., D1 * math.pi, phi % (2. * math.pi), phi % (2. * math.pi)]   # 레그 1·2(1차), 3·4(2차, 4는 3의 반대)
    rail = [vb, vb, vl, vl]
    ceq = [2. * cp, 2. * cp, 2. * cs, 2. * cs]
    # 초기: 각 레그의 목표 상태로 중점 전압
    tgt = np.zeros(4, np.int64); on = np.zeros(4, np.int64); kch = np.full(4, -10**9, np.int64); v = np.zeros(4)
    for j in range(4):
        s = _leg_target(0., e[j])
        if j == 1:
            s = 1 - _leg_target(0., e[j])                       # 레그 2는 레그 1의 반대가 기본(SPS에서 v1 = +V)
        if j == 3:
            s = 1 - _leg_target(0., e[2])
        tgt[j] = s; on[j] = s; v[j] = rail[j] * s
    i = i0
    pk = 0.; pk1 = 0.; acc_p = 0.; acc_i = 0.
    for p in range(nper):
        last = p == nper - 1
        pk_p = 0.; acc_p = 0.; acc_i = 0.
        for k in range(ndt):
            th = (k + 0.5) * dt * w
            for j in range(4):
                if j == 0:
                    s = _leg_target(th, e[0])
                elif j == 1:
                    s = 1 - _leg_target(th, e[1])
                elif j == 2:
                    s = _leg_target(th, e[2])
                else:
                    s = 1 - _leg_target(th, e[2])
                if s != tgt[j]:
                    tgt[j] = s; kch[j] = p * ndt + k; on[j] = -1         # 모두 끔(데드타임)
                if on[j] == -1 and p * ndt + k - kch[j] >= ndd:
                    on[j] = tgt[j]
            # 레그로 들어오는 전류: 1차 레그 1 −i, 레그 2 +i, 2차 레그 3 +n i, 레그 4 −n i
            iin = (-i, i, n * i, -n * i)
            for j in range(4):
                if on[j] == 1:
                    v[j] = rail[j]
                elif on[j] == 0:
                    v[j] = 0.
                else:
                    v[j] += iin[j] / ceq[j] * dt
                    if v[j] > rail[j] + vf:
                        v[j] = rail[j] + vf
                    elif v[j] < -vf:
                        v[j] = -vf
            v1 = v[0] - v[1]; v2 = v[2] - v[3]
            i += (v1 - n * v2 - R * i) / L * dt
            a = abs(i)
            if a > pk_p:
                pk_p = a
            acc_p += v2 * n * i
            acc_i += i
        if p >= nper - nfix - 1 and p < nper - 1:
            i -= acc_i / ndt                                      # 직류 편류 제거(정상상태 가속)
        pk = pk_p
    return n * pk, acc_p / ndt / max(vl, 1e-3), pk, acc_i / ndt


def steady(vb, vl, D1, phi, p, td=TD, cp=COSS_P, cs=COSS_S, vf=VF, R=RDAB, ndt=8000, nper=60, nfix=40):
    """한 운전점의 정상상태(링크 쪽 첨두 [A], 링크 평균전류 [A], 1차 첨두 [A])."""
    n, L, fs = p.turns, p.Ldab, p.fs
    wl = 2 * math.pi * fs * L / n ** 2
    v1 = vb / n
    r = vl / v1
    d = (1 - D1) * math.pi
    a = phi - D1 * math.pi
    # 초기 전류: 이상 파형(펄스 시작 기준)을 가상 에지(θ = 0)로 옮긴 값. 정상상태까지의 반복을 줄인다
    i0 = _ideal_i_at_edge(r, d, a, D1) * v1 / wl / n         # 1차 전류
    pkl, il, pk1, idc = _sim(vb, vl, n, L, R, fs, D1, phi, i0, td, cp, cs, vf, ndt, nper, nfix)
    return pkl, il, pk1


def _ideal_i_at_edge(r, d, a, D1):
    """이상 정규화 파형(펄스 시작 기준)에서 가상 에지(펄스 시작 − D1·π)의 정규화 전류(2차 환산)."""
    th = np.linspace(0, 2 * np.pi, 4001)
    a = a % (2 * np.pi)
    s1 = np.where(np.mod(th, 2 * np.pi) < d, 1., np.where((np.mod(th, 2 * np.pi) >= np.pi) & (np.mod(th, 2 * np.pi) < np.pi + d), -1., 0.))
    s2 = np.where(np.mod(th - a, 2 * np.pi) < np.pi, 1., -1.)
    di = s1 - r * s2
    i = np.concatenate([[0.], np.cumsum(0.5 * (di[1:] + di[:-1]) * np.diff(th))])
    i -= i.mean()
    k = int(round(((2 * np.pi - D1 * np.pi) % (2 * np.pi)) / (2 * np.pi) * 4000))
    return float(i[k])


VB_SW = (380., 440., 500.)   # 강등 상태 버스전압 범위(정합 유지 337–465 V, 붕괴 380–505 V)의 대표값. 첨두는 이 가운데 최댓값을 쓴다


def build_sw_table(p, vbs=VB_SW, verbose=True):
    """회로 지령표(dab_modulation.circuit_tables, j ≤ 0)의 칸마다 같은 (D1 ≤ 0.95, φ)로 스위칭 정상상태를 계산한다.
    반환 dict: pk_sw(정규화 첨두, vbs 가운데 최대), j_sw(정규화 평균 링크전류, vbs 평균), pk_vb·j_vb(버스전압별), 격자."""
    import time
    import dab_modulation as DM
    tab = DM.circuit_tables()
    d, ph = tab["d"], tab["phi"]
    nr, nj = d.shape
    R = tab["r0"] + tab["dr"] * np.arange(nr)
    J = tab["j0"] + tab["dj"] * np.arange(nj)
    n, wl = p.turns, 2 * math.pi * p.fs * p.Ldab / p.turns ** 2
    pk_vb = np.zeros((len(vbs), nr, nj)); j_vb = np.zeros((len(vbs), nr, nj))
    t0 = time.time()
    for a, vb in enumerate(vbs):
        v1 = vb / n; Ib = v1 / wl
        for i in range(nr):
            vl = R[i] * v1
            for k in range(nj):
                D1 = min(max(1 - d[i, k] / math.pi, 0.), 0.95)
                pkl, il, _ = steady(vb, vl, D1, float(ph[i, k]), p)
                pk_vb[a, i, k] = pkl / Ib; j_vb[a, i, k] = il / Ib
        if verbose:
            print("   sw table v_bus %.0f V done (%.0f s)" % (vb, time.time() - t0), flush=True)
    return dict(r0=tab["r0"], dr=tab["dr"], j0=tab["j0"], dj=tab["dj"], vbs=list(vbs), td=TD, coss_p=COSS_P, coss_s=COSS_S, vf=VF,
                pk_sw=pk_vb.max(axis=0).tolist(), j_sw=j_vb.mean(axis=0).tolist(), pk_ideal=tab["pk"].tolist(), j_ideal=np.tile(J, (nr, 1)).tolist(),
                pk_vb=pk_vb.tolist(), j_vb=j_vb.tolist())
