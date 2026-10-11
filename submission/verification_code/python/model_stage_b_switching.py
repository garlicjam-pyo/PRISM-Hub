"""[공통 모델] Stage B 스위칭 모델: DAB(SPS) + 4상한 H-브리지(유니폴라 PWM) + 표본화 제어기.

평균모델(model_stage_b.py)에서 확인한 전류·전압·지연 여유가 실제 스위칭 동작에서도 성립하는지 보기 위한
스위칭 수준 상미분방정식 모델이다(보고서 8.2절 "Stage B 스위칭 회로와 제어기 구현 검증"의 1단계).

[회로와 상태]  x = [i_p, v_s, v_bus, i_h, v_link, i_L]
  L    di_p/dt   = V_bat/2 − R·i_p + v_s − v_bus                 (평균모델과 같음, Stage A는 이상 2:1)
  C_s  dv_s/dt   = i_h − i_p
  C_b  dv_bus/dt = i_p − P/v_bus − s1·i_L − P_loss/v_bus         (s1·i_L: DAB 1차 브리지가 버스에서 끄는 전류)
  L_h  di_h/dt   = (sA − sB)·v_link − v_s − R_h·i_h              (H-브리지 레그 A·B의 실제 출력 상태)
  C_l  dv_link/dt= n·s2·i_L − (sA − sB)·i_h                       (DAB 2차 브리지가 링크로 보내는 전류 − H-브리지 소비)
  L_d  di_L/dt   = s1·v_bus − n·s2·v_link − R_d·i_L               (DAB 누설 인덕턴스 전류, 1차 환산)
  s1, s2: DAB 1·2차 브리지 출력(±1, 데드타임 중에는 아래 규칙), sA, sB: H-브리지 레그 노드 전압(0–1, 정규화).
  P_loss: DAB 손실. 직전 제어주기의 평균 링크전력 p̄에 평균모델과 같은 방향별 효율 η를 적용한 손실
     (1/η − 1)·max(p̄,0) + (1 − η)·max(−p̄,0) 에서 권선저항 R_d가 직접 소비한 손실을 뺀 값(0 이상)이다.
     → 정상상태의 DAB 총손실이 평균모델과 같아, 두 모델의 차이가 스위칭 동작에서만 나오게 했다.

[스위칭]
  H-브리지 : 유니폴라 PWM, 반송파 200 kHz(삼각파, 표본 시점에서 최댓값), 레그 데드타임 50 ns.
             데드타임 동안 노드 전압은 필터전류로 출력용량(기본 1 nF/스위치)을 충방전하며 움직이고, 남은
             전압은 데드타임 끝에서 하드 스위칭한다. 에지는 적분 간격 안의 정확한 위치로 처리한다.
  DAB      : 50 % 구형파 두 브리지, 200 kHz, 단일 위상천이(SPS). 링크전류 지령 → 위상
             φ = (π/2)(1 − √(1 − 4|I|/(π k))),  k = n·v_bus/(2π f L_d)  (|φ| ≤ π/3)
             위상 한계는 누설 인덕턴스가 공칭보다 10 % 작아도 링크 정격(80 A, 8 kW)을 넘지 않게 정한다.
             에지 배치: 반송파 최댓값·최솟값(반주기 중심 c_j)을 기준으로 1차 에지 c_j − δ/2, 2차 에지 c_j + δ/2
             (δ = φ·T/2π). 두 브리지가 H-브리지 반송파에 고정되어 위상 이력에 따라 표류하지 않는다.
             위상 갱신: 지령은 도착 후 첫 반주기 중심에서 반영한다. 쌍 j의 실제 위상차를 Δ_j = (A + δ_new)/2로
             두는데, A는 직전 쌍들의 실제 위상차로 계산한 전류 상태(A ← −A + 2Δ, 정상상태에서 A = δ)다. 두 브리지
             전압이 같을 때 쌍 j가 끝나면 전류가 새 위상의 정상상태 값에 놓여 직류 편류가 생기지 않는다(
             전이 반주기의 위상차를 이전·새 위상의 평균으로 두는 것과 같으며, 위상 부호와 무관하게 성립한다.
             관련 연구: K. Takagi, H. Fujita, "Dynamic Control and Performance of a Dual-Active-Bridge DC–DC
             Converter," IEEE Trans. Power Electron., 2018).
             이미 지난 에지는 고정하고 남은 에지만 옮기며, 남은 에지를 과거로 옮겨야 하는 경우(위상 부호 반전)는
             지금 스위칭하고 부족분은 A를 통해 다음 쌍에서 보정한다.
             데드타임 100 ns. 데드타임 동안 전류가 있으면 다이오드가 출력을 정하고, 전류가 0을 지나면 0에 고정
             (영전류 클램프)하며 열린 브리지는 상대 브리지 전압을 따른다(자기 직류전압으로 제한). DAB 소자
             출력용량은 넣지 않았다.
[제어기]   controller_adopted.StageBController와 같은 법칙(상태궤환 + 적분 + 내부 전류 법칙 + 링크 PI,
           채택 설계는 1주기 예측). 변조기에는 모델 기반 데드타임 보상을 둔다: 예측 i_h와 리플 반진폭으로
           리플 극값에서의 전이별 전압·시간 오차(출력용량 충방전 포함)를 계산해 변조율에서 뺀다
           (deadtime_error, 전이 중 전류 기울기는 무시). 표본 시점은 반송파 최댓값(5 µs 주기)이며 측정값은
           순시 표본이다(필터·양자화·잡음 없음). 지령은 표본 후 전달지연(기본 5 µs) 뒤에 PWM 비교 레지스터에
           즉시 반영되고, DAB 위상은 그 이후 첫 반주기 중심에서 반영된다.
[적분]     고정 간격 중점법 dt = 5 ns(주기당 1000단계). 스위치 상태는 간격 안의 에지·데드타임 경계로 나눈 평균.
[한계]     DAB 소자 출력용량·스위칭 손실·기생 인덕턴스·자화 인덕턴스·Stage A 리플·센서 잡음·보호 동작 미포함.
"""
import math

import numpy as np
from numba import njit

from model_stage_b import equilibrium

PI = math.pi
NREC = 21
# 주기 기록(rec) 열: 0 v_bus 평균, 1 i_p 평균, 2 i_h 평균, 3 v_link 평균, 4 링크전류 평균, 5 링크전력 평균,
#   6 i_h 최대, 7 i_h 최소, 8 |i_p| 최대, 9 v_bus 최소, 10 v_bus 최대, 11 v_link 최소, 12 v_link 최대,
#   13 |i_L| 최대, 14 변조율 지령(제어기 출력), 15 링크전류 지령, 16 적용 DAB 위상, 17 |v_s| 최대,
#   18 PWM 비교값(데드타임 보상 후), 19 i_L 주기 평균(직류 편류), 20 DAB 손실 전류원 전력


@njit(cache=True)
def _power(t, prof, P0, P1, step):
    if prof == 0:
        return P1 if t >= step else P0
    if t < step:
        return 12700. if prof <= 2 else 25000.
    s = (t - step) * 1e3
    if prof == 1 or prof == 3:
        sc = min(8500., s * 4000.)
    else:
        sc = min(8500., (math.floor(s) + 1.) * 4000.)
    if prof <= 2:
        return min(25000., 12700. + 3800. + sc + 60. * s * 3.)
    return max(-3200., 25000. - 3800. - sc - min(6000., 500. * s) - min(7000., 500. * s) - min(2900., 500. * s))


@njit(cache=True)
def _clip(v, lim):
    return min(lim, max(-lim, v))


@njit(cache=True)
def _controller(xs_meas, cst, cp, K, predict, vbat):
    """표본화 제어기 1회 계산. cst = [q, q_link, m_prev, ilink_prev]. 반환 (m, ilink, 브리지 전류지령, 예측 i_h)."""
    ip, vs, vb, ih, vl = xs_meas[0], xs_meas[1], xs_meas[2], xs_meas[3], xs_meas[4]
    L, Cs, R, Lh, Rh, Clink, Ts = cp[0], cp[1], cp[3], cp[4], cp[5], cp[6], cp[7]
    vref, vlink, mmax, refmax = cp[8], cp[9], cp[10], cp[11]
    link_max, power_max, link_bw, itau = cp[12], cp[13], cp[14], cp[15]
    Ldab, fs, turns, phmax = cp[16], cp[17], cp[18], cp[19]
    sip, svs, sih = ip, vs, ih
    if predict:                                      # 1주기 예측(공칭 모델, 중점법 5단계)
        m = cst[2]; h = Ts / 5.
        for _ in range(5):
            a1 = (vbat / 2 - R * sip + svs - vb) / L
            a2 = (sih - sip) / Cs
            a3 = (m * vl - svs - Rh * sih) / Lh
            mp, mv, mh = sip + .5 * h * a1, svs + .5 * h * a2, sih + .5 * h * a3
            b1 = (vbat / 2 - R * mp + mv - vb) / L
            b2 = (mh - mp) / Cs
            b3 = (m * vl - mv - Rh * mh) / Lh
            sip, svs, sih = sip + h * b1, svs + h * b2, sih + h * b3
    raw = -(K[0] * sip + K[1] * svs + K[2] * vb + K[3] * sih) - K[4] * cst[0]
    iref = _clip(raw, refmax)
    cst[0] += Ts * (vref - vb) + .1 * (iref - raw) / (-K[4])
    mraw = (svs + Rh * sih + Lh / itau * (iref - sih)) / vl
    m = _clip(mraw, mmax)
    w = 2 * PI * link_bw
    rawlink = m * sih + Clink * (2 * .7 * w * (vlink - vl) + w * w * cst[1])
    sps = max(vb, 0.) * turns * phmax * (1 - phmax / PI) / (2 * PI * fs * Ldab)
    lim = min(min(link_max, sps), power_max / max(vl, 1e-9))
    il = _clip(rawlink, lim)
    cst[1] += Ts * (vlink - vl) + .1 * (il - rawlink) / (Clink * w * w)
    cst[2] = m; cst[3] = il
    return m, il, iref, sih


@njit(cache=True)
def _err_rise(i, V, td, C):
    """레그 상승 전이(하측→상측) 한 번에 잃는 전압·시간 [V·s]. i: 그 순간 노드에서 나가는 전류."""
    if i >= 0.:
        return V * td                         # 노드가 하측에 머물다 데드타임 뒤 하드 스위칭
    ttr = 2 * C * V / (-i)
    return V * ttr / 2 if ttr <= td else V * td - (-i) * td * td / (4 * C)


@njit(cache=True)
def _err_fall(i, V, td, C):
    """레그 하강 전이(상측→하측) 한 번에 더해지는 전압·시간 [V·s]."""
    if i <= 0.:
        return V * td
    ttr = 2 * C * V / i
    return V * ttr / 2 if ttr <= td else V * td - i * td * td / (4 * C)


@njit(cache=True)
def deadtime_error(m, i, V, td, C, L, f):
    """유니폴라 PWM 한 주기의 브리지 평균 전압 오차 [V] (예측 전류 i, 리플 반진폭 r = V|m|(1−|m|)/(4Lf)).
    전이는 리플 극값에서 일어난다: 레그 A 상승·레그 B 하강은 전류 최소, 레그 A 하강·레그 B 상승은 최대(m > 0)."""
    if m < 0.:
        return -deadtime_error(-m, -i, V, td, C, L, f)
    r = V * m * (1 - m) / (4 * L * f)
    imin = i - r; imax = i + r
    d = -_err_rise(imin, V, td, C) + _err_fall(imax, V, td, C) + _err_rise(-imax, V, td, C) - _err_fall(-imin, V, td, C)
    return d * f


@njit(cache=True)
def _phase(il, vb, vl, cp, lmin):
    """DAB 링크전류 지령 → SPS 위상(공칭 n, L_d, f, 측정 v_bus). |φ| ≤ φ_max.
    lmin < 1이면 누설 인덕턴스가 공칭의 lmin배까지 작아져도 실제 링크전류가 정격(80 A, 8 kW/v_link)을
    넘지 않도록 위상을 추가로 제한한다(위상 앞먹임만으로 전류를 제한하는 구조의 공차 대책)."""
    Ldab, fs, turns, phmax = cp[16], cp[17], cp[18], cp[19]
    k = turns * max(vb, 1.) / (2 * PI * fs * Ldab)
    a = min(abs(il) / (PI * k / 4.), 1.)
    ph = PI / 2 * (1 - math.sqrt(1 - a))
    ph = min(ph, phmax)
    if lmin < 1.:
        kmax = k / lmin
        ilim = min(cp[12], cp[13] / max(vl, 1.))
        ph = min(ph, PI / 2 * (1 - math.sqrt(1 - min(ilim / (PI * kmax / 4.), 1.))))
    return ph if il >= 0 else -ph


@njit(cache=True)
def _deriv(x, sA, sB, s1, s2, P, pp, ploss):
    L, Cs, Cb, R, Lh, Rh, Clink, vbat, Ld, n, Rd = pp[0], pp[1], pp[2], pp[3], pp[4], pp[5], pp[6], pp[8], pp[9], pp[10], pp[11]
    ip, vs, vb, ih, vl, iL = x[0], x[1], x[2], x[3], x[4], x[5]
    sh = sA - sB
    ilink = n * s2 * iL
    iloss = ploss / vb
    d = np.empty(6)
    d[0] = (vbat / 2 - R * ip + vs - vb) / L
    d[1] = (ih - ip) / Cs
    d[2] = (ip - P / vb - s1 * iL - iloss) / Cb
    d[3] = (sh * vl - vs - Rh * ih) / Lh
    d[4] = (ilink - sh * ih) / Clink
    d[5] = (s1 * vb - n * s2 * vl - Rd * iL) / Ld
    return d


@njit(cache=True)
def _on_interval(m, c0, c1):
    """한 적분 간격 안에서 m > c(s)인 구간 [a, b] (s ∈ [0,1], 반송파는 간격 안에서 선형)."""
    if c1 < c0:
        thr = (c0 - m) / (c0 - c1)
        a = min(max(thr, 0.), 1.)
        return a, 1.
    thr = (m - c0) / (c1 - c0)
    return 0., min(max(thr, 0.), 1.)


@njit(cache=True)
def _overlap(a1, b1, a2, b2):
    return max(0., min(b1, b2) - max(a1, a2))


@njit(cache=True)
def _carrier(k, Np):
    """반송파(삼각파) 값: 주기 시작(표본 시점) +1, 반주기 −1."""
    frac = (k % Np) / Np
    return 4. * abs(frac - .5) - 1.


@njit(cache=True)
def _ramp_int(u0, sg, a, b):
    """∫_a^b clamp(u0 + sg·τ, 0, 1) dτ (τ: 전이 시작 후 경과 시간)."""
    if b <= a:
        return 0.
    if sg == 0.:
        return min(max(u0, 0.), 1.) * (b - a)
    # 클램프 경계 시각
    t0 = (0. - u0) / sg; t1 = (1. - u0) / sg
    lo, hi = (t0, t1) if sg > 0 else (t1, t0)   # lo 이전/ hi 이후는 클램프
    tot = 0.
    # [a, min(b, lo)] : 클램프 값
    e = min(b, lo)
    if e > a:
        tot += (0. if sg > 0 else 1.) * (e - a)
    # 선형 구간
    s0 = max(a, lo); s1 = min(b, hi)
    if s1 > s0:
        tot += u0 * (s1 - s0) + .5 * sg * (s1 * s1 - s0 * s0)
    s0 = max(a, hi)
    if b > s0:
        tot += (1. if sg > 0 else 0.) * (b - s0)
    return tot


@njit(cache=True)
def _leg_step(st, a, b, t0, dt, td, sg):
    """레그 노드 전압(정규화 0–1)의 한 간격 평균. 데드타임 동안 노드는 출력용량 충방전 기울기 sg로
    움직이고(다이오드 클램프 0–1), 데드타임이 끝나면 목표 레벨로 스위칭한다(남은 전압은 하드 스위칭).
    st = [전이 시작 시각 te, te에서의 노드 값, 목표 레벨, 현재 노드 레벨(전이 밖)]. a, b: 목표가 1인 구간."""
    d0 = 1. if (b > a and a == 0.) else 0.
    d1 = 1. if (b > a and b == 1.) else 0.
    t1 = t0 + dt
    edges = 0; se = 0.
    if d0 != d1:
        edges = 1; se = a if d1 == 1. else b
    if d0 != st[2]:                             # 간격 시작에서의 레벨 변화(지령 갱신): 지금 노드 값에서 새 전이 시작
        st[0] = t0; st[1] = st[3]; st[2] = d0
    tot = 0.
    seg_end = t0 + se * dt if edges == 1 else t1
    # 첫 구간: [t0, seg_end]
    tot += _seg(st, t0, seg_end, td, sg)
    if edges == 1:
        # 새 목표 에지: 그 순간의 노드 값에서 전이 시작
        st[1] = _node_at(st, seg_end, td, sg); st[0] = seg_end; st[2] = d1
        tot += _seg(st, seg_end, t1, td, sg)
    st[3] = _node_at(st, t1, td, sg)
    return tot / dt


@njit(cache=True)
def _node_at(st, t, td, sg):
    if t >= st[0] + td:
        return st[2]
    return min(max(st[1] + sg * (t - st[0]), 0.), 1.)


@njit(cache=True)
def _seg(st, ta, tb, td, sg):
    if tb <= ta:
        return 0.
    tend = st[0] + td                           # 데드타임 종료 시각
    tot = 0.
    if ta < tend:
        e = min(tb, tend)
        tot += _ramp_int(st[1], sg, ta - st[0], e - st[0])
        ta = e
    if tb > ta:
        tot += st[2] * (tb - ta)
    return tot


@njit(cache=True)
def _dab_avg(t0, t1, p_te, p_b, p_a, s_te, s_b, s_a, td, iL, vb, nvl):
    """DAB 두 브리지 출력(s1, s2)의 간격 평균.
    각 브리지: 에지 te 이전 s_before, [te, te+td) 데드타임, 이후 s_after. 간격을 에지·데드타임 경계로 나눠
    소구간마다 값을 정한다. 데드타임 동안 전류가 있으면 다이오드가 출력을 정하고(1차 −sign(i_L), 2차 +sign(i_L)),
    전류가 0(영전류 클램프 상태)이면 브리지가 열려 상대 브리지 전압을 따르되 자기 직류전압으로 제한된다
    (두 브리지가 모두 열리면 인덕터 전압 0). 소자 출력용량은 넣지 않았다."""
    pts = np.empty(6)
    pts[0] = t0; npt = 1
    for c in (p_te, p_te + td, s_te, s_te + td):
        if t0 < c < t1:
            pts[npt] = c; npt += 1
    pts[npt] = t1; npt += 1
    pts[:npt] = np.sort(pts[:npt])
    s1 = 0.; s2 = 0.
    for k in range(npt - 1):
        a = pts[k]; b = pts[k + 1]
        if b <= a:
            continue
        tm = .5 * (a + b)
        pd = p_te <= tm < p_te + td
        sd = s_te <= tm < s_te + td
        v1 = p_b if tm < p_te else p_a
        v2 = s_b if tm < s_te else s_a
        if iL > 0.:
            if pd:
                v1 = -1.
            if sd:
                v2 = 1.
        elif iL < 0.:
            if pd:
                v1 = 1.
            if sd:
                v2 = -1.
        else:
            if pd and sd:
                v1 = 0.; v2 = 0.
            elif pd:
                v1 = min(1., max(-1., v2 * nvl / vb))
            elif sd:
                v2 = min(1., max(-1., v1 * vb / nvl))
        s1 += v1 * (b - a); s2 += v2 * (b - a)
    return s1 / (t1 - t0), s2 / (t1 - t0)


@njit(cache=True)
def _loss(p, eta):
    """평균모델과 같은 방향별 효율 η의 DAB 손실 [W] (p: 링크 측 전력)."""
    return (1 / eta - 1) * max(p, 0.) + (1 - eta) * max(-p, 0.)


@njit(cache=True)
def run_core(x0, iL0, cst, uq, pp, cp, K, predict, prof, P0, P1, step, t_pre, duration, dt, lag, sw, cap):
    """스위칭 모델 적분. 반환: 주기별 기록, ZVS 집계, 완료 여부, 종료 스텝, 파형, 에너지 잔차."""
    Ts = cp[7]; Np = int(round(Ts / dt)); T = Ts; Nh = Np // 2
    td_h, td_d, dtc = sw[0], sw[1], sw[2]            # H-브리지·DAB 데드타임, 데드타임 보상(0 없음, 1 모델 기반, 2 선형)
    coss = sw[4]                                    # H-브리지 스위치 출력용량(노드 등가 2·C_oss)
    n_tot = int(round((t_pre + duration) / dt)); nper = n_tot // Np
    t_zvs = duration - 1e-3                          # ZVS 집계 구간(마지막 1 ms)
    rec = np.zeros((nper, NREC))
    # 파형 저장(선택): cap = [시작 시각, 끝 시각, 간격(스텝)]
    c_i0 = int(round((cap[0] + t_pre) / dt)); c_i1 = int(round((cap[1] + t_pre) / dt)); c_dec = max(int(cap[2]), 1)
    ncap = max((c_i1 - c_i0) // c_dec, 0)
    wave = np.zeros((ncap, 9))
    zvs = np.zeros(4)
    x = x0.copy(); x[5] = iL0
    vbat = pp[8]; n = pp[10]; eta = pp[7]; Rd = pp[11]
    m_reg = uq[0]                                    # PWM 비교값
    legA = np.array([-1., 1., 1., 1.]); legB = np.array([-1., 0., 0., 0.])
    qi = np.full(8, -1); qm = np.zeros(8); qp = np.zeros(8); qh = 0; qt = 0
    t_start = -t_pre
    # ---- DAB 에지 일정: 반주기 중심 c_j = t_start + j·T/2 (짝수 j = 반송파 최댓값 = 상승 쌍, 홀수 j = 하강 쌍).
    #      쌍 j의 1차 에지 c_j − δ/2, 2차 에지 c_j + δ/2 (δ = φ·T/2π, 부호 포함).
    ph_tgt = _phase(uq[1], x[2], x[4], cp, sw[6])    # 현재 위상 지령
    d0 = ph_tgt / (2 * PI) * T
    A = d0                                          # 직전 쌍까지의 전류 상태(시간 단위, 정상상태에서 δ)
    p_t = np.full(2, 1e30); s_t = np.full(2, 1e30)   # 쌍 짝/홀 슬롯의 예정 에지 시각(실행 후 비움)
    p_h = np.zeros(2); s_h = np.zeros(2)             # 쌍 짝/홀 슬롯의 실제 에지 시각
    p_te = t_start - 1.; s_te = t_start - 1.
    if d0 > 0:                                      # 1차가 앞선다: 쌍 0의 1차 에지는 이미 지남
        p_j = 1; p_h[0] = t_start - d0 / 2; p_state = 1.; p_before = 1.
        s_j = 0; s_state = -1.; s_before = -1.
    elif d0 < 0:
        s_j = 1; s_h[0] = t_start + d0 / 2; s_state = 1.; s_before = 1.
        p_j = 0; p_state = -1.; p_before = -1.
    else:
        p_j = 0; s_j = 0; p_state = -1.; p_before = -1.; s_state = -1.; s_before = -1.
    ph_rec = ph_tgt
    ploss = _loss(x0[4] * uq[1], eta)                # DAB 손실(직전 주기 평균 전력 기준, 주기마다 갱신)
    acc = np.zeros(8); mx_ih = -1e9; mn_ih = 1e9; mx_ip = 0.; mn_vb = 1e9; mx_vb = -1e9
    mn_vl = 1e9; mx_vl = -1e9; mx_iL = 0.; mx_vs = 0.
    alive = True; end_i = n_tot; eres = 0.
    for i in range(n_tot):
        t0 = t_start + i * dt; t1 = t0 + dt
        k_in = i % Np
        if k_in == 0:                                # 표본·제어 계산(반송파 최댓값)
            meas = x.copy()
            mcmd, icmd, iref, ihp = _controller(meas, cst, cp, K, predict, vbat)
            if dtc == 1.:                            # 모델 기반 데드타임 보상: 예측 전류와 리플로 오차를 계산해 상쇄
                vlm = max(meas[4], 1.)
                mcmd_pwm = mcmd - deadtime_error(mcmd, ihp, vlm, td_h, sw[3], cp[4], 1 / T) / vlm
            elif dtc == 2.:                          # (비교용) 전류지령 비례 보상: ±sw[5] A에서 포화
                mcmd_pwm = mcmd + 2 * td_h / T * min(max(iref / sw[5], -1.), 1.)
            else:
                mcmd_pwm = mcmd
            qi[qt % 8] = i + lag; qm[qt % 8] = mcmd_pwm; qp[qt % 8] = _phase(icmd, meas[2], meas[4], cp, sw[6]); qt += 1
            rec[i // Np, 14] = mcmd; rec[i // Np, 15] = icmd; rec[i // Np, 18] = mcmd_pwm
        while qh < qt and qi[qh % 8] <= i:          # 전달지연 뒤 지령 반영(PWM 비교값 즉시, DAB 위상은 다음 반주기 중심)
            m_reg = qm[qh % 8]; ph_tgt = qp[qh % 8]; qh += 1
        # ---- H-브리지(유니폴라 PWM, 정확한 에지 위치, 데드타임 중 출력용량 충방전)
        ih = x[3]
        c0 = _carrier(i, Np); c1 = _carrier(i + 1, Np)
        aA, bA = _on_interval(m_reg, c0, c1)
        aB, bB = _on_interval(-m_reg, c0, c1)
        # 노드 기울기(정규화/초): 레그 A에서 나가는 전류 i_h가 양이면 노드 A는 내려가고, 레그 B는 올라간다
        vl_ = max(x[4], 1.)
        sgA = -ih / (2 * coss * vl_); sgB = ih / (2 * coss * vl_)
        sA = _leg_step(legA, aA, bA, t0, dt, td_h, sgA)
        sB = _leg_step(legB, aB, bB, t0, dt, td_h, sgB)
        # ---- DAB 위상 갱신(반주기 중심마다). 쌍 j의 위상차 Δ_j = (A + δ_new)/2로 두면 쌍 j가 끝난 뒤 전류가
        #      새 위상의 정상상태 값에 바로 놓인다(전압 정합 시 직류 편류 없음). 이미 지난 에지는 고정하고,
        #      아직 남은 에지만 옮긴다. 남은 에지를 과거로 옮겨야 하면(위상 부호 반전) 지금 스위칭하고 그 부족분은
        #      A를 통해 다음 쌍에서 보정된다.
        if i % Nh == 0:
            j = i // Nh; cj = t0
            if j >= 1:
                jm = (j - 1) % 2
                A = -A + 2 * (s_h[jm] - p_h[jm])
            dtg = ph_tgt / (2 * PI) * T
            D = .5 * (A + dtg)
            jj = j % 2
            p_done = p_j > j; s_done = s_j > j
            if p_done and not s_done:
                s_t[jj] = max(cj, p_h[jj] + D)
            elif s_done and not p_done:
                p_t[jj] = max(cj, s_h[jj] - D)
            elif not p_done and not s_done:
                if D >= 0:
                    p_t[jj] = cj; s_t[jj] = cj + D
                else:
                    s_t[jj] = cj; p_t[jj] = cj - D
            tpj = p_h[jj] if p_done else p_t[jj]
            tsj = s_h[jj] if s_done else s_t[jj]
            D1 = .5 * (-A + 2 * (tsj - tpj) + dtg)
            cn = t_start + ((j + 1) * Nh) * dt
            p_t[1 - jj] = cn - D1 / 2; s_t[1 - jj] = cn + D1 / 2
            ph_rec = ph_tgt
        # ---- DAB 에지 실행
        if p_t[p_j % 2] < t1:
            te = max(p_t[p_j % 2], t0)
            p_before = p_state; p_state = 1. if p_j % 2 == 0 else -1.; p_te = te; p_h[p_j % 2] = te; p_t[p_j % 2] = 1e30; p_j += 1
            if te >= t_zvs:
                zvs[1] += 1
                if (p_state == -1 and x[5] > 0) or (p_state == 1 and x[5] < 0):
                    zvs[0] += 1
        if s_t[s_j % 2] < t1:
            te = max(s_t[s_j % 2], t0)
            s_before = s_state; s_state = 1. if s_j % 2 == 0 else -1.; s_te = te; s_h[s_j % 2] = te; s_t[s_j % 2] = 1e30; s_j += 1
            if te >= t_zvs:
                zvs[3] += 1
                if (s_state == -1 and x[5] < 0) or (s_state == 1 and x[5] > 0):
                    zvs[2] += 1
        iL_0 = x[5]
        s1, s2 = _dab_avg(t0, t1, p_te, p_before, p_state, s_te, s_before, s_state, td_d, iL_0,
                          max(x[2], 1.), n * max(x[4], 1.))
        # ---- 적분(중점법)
        P = _power(t0, prof, P0, P1, step)
        d1 = _deriv(x, sA, sB, s1, s2, P, pp, ploss)
        # 에너지 보존 검산: Σ(저장소자 · 상태 · 미분) = 입력 − 부하 − 저항손실 − DAB 손실항
        stored = (pp[0] * x[0] * d1[0] + pp[1] * x[1] * d1[1] + pp[2] * x[2] * d1[2] + pp[4] * x[3] * d1[3]
                  + pp[6] * x[4] * d1[4] + pp[9] * x[5] * d1[5])
        expect = (vbat / 2 * x[0] - pp[3] * x[0] ** 2 - P - pp[5] * x[3] ** 2 - Rd * x[5] ** 2 - ploss)
        eres = max(eres, abs(stored - expect))
        xm = x + .5 * dt * d1
        d2 = _deriv(xm, sA, sB, s1, s2, P, pp, ploss)
        x = x + dt * d2
        # ---- 영전류 클램프: 어느 브리지든 간격 끝에서 데드타임 중일 때 전류가 0을 지나면(다이오드 차단) 0에 고정하고,
        #      이미 0이면 열린 브리지가 상대 전압을 감당할 수 있는 동안 0을 유지한다.
        pd1 = p_te < t1 < p_te + td_d; sd1 = s_te < t1 < s_te + td_d
        if pd1 or sd1:
            if (iL_0 > 0. and x[5] <= 0.) or (iL_0 < 0. and x[5] >= 0.):
                x[5] = 0.
            elif iL_0 == 0.:
                vbx = max(x[2], 1.); nvl = n * max(x[4], 1.)
                if (pd1 and sd1) or (pd1 and nvl <= vbx) or (sd1 and vbx <= nvl):
                    x[5] = 0.
        # ---- 기록
        j = i // Np
        acc[0] += x[2]; acc[1] += x[0]; acc[2] += x[3]; acc[3] += x[4]
        il_now = n * s2 * x[5]; acc[4] += il_now; acc[5] += x[4] * il_now; acc[6] += x[5] * x[5]; acc[7] += x[5]
        mx_ih = max(mx_ih, x[3]); mn_ih = min(mn_ih, x[3]); mx_ip = max(mx_ip, abs(x[0]))
        mn_vb = min(mn_vb, x[2]); mx_vb = max(mx_vb, x[2]); mn_vl = min(mn_vl, x[4]); mx_vl = max(mx_vl, x[4])
        mx_iL = max(mx_iL, abs(x[5])); mx_vs = max(mx_vs, abs(x[1]))
        if c_i0 <= i < c_i1 and (i - c_i0) % c_dec == 0 and (i - c_i0) // c_dec < ncap:
            w_ = (i - c_i0) // c_dec
            wave[w_, 0] = t1; wave[w_, 1:7] = x; wave[w_, 7] = sA - sB; wave[w_, 8] = s1
        if k_in == Np - 1:
            rec[j, 0] = acc[0] / Np; rec[j, 1] = acc[1] / Np; rec[j, 2] = acc[2] / Np; rec[j, 3] = acc[3] / Np
            rec[j, 4] = acc[4] / Np; rec[j, 5] = acc[5] / Np
            rec[j, 6] = mx_ih; rec[j, 7] = mn_ih; rec[j, 8] = mx_ip; rec[j, 9] = mn_vb; rec[j, 10] = mx_vb
            rec[j, 11] = mn_vl; rec[j, 12] = mx_vl; rec[j, 13] = mx_iL; rec[j, 16] = ph_rec; rec[j, 17] = mx_vs
            rec[j, 19] = acc[7] / Np; rec[j, 20] = ploss
            ploss = max(_loss(acc[5] / Np, eta) - Rd * acc[6] / Np, 0.)
            acc[:] = 0.; mx_ih = -1e9; mn_ih = 1e9; mx_ip = 0.; mn_vb = 1e9; mx_vb = -1e9
            mn_vl = 1e9; mx_vl = -1e9; mx_iL = 0.; mx_vs = 0.
        if not (np.isfinite(x).all()) or x[2] < 50 or x[4] < 10:
            alive = False; end_i = i; break
    return rec, zvs, alive, end_i, wave, eres


SW_DEFAULT = dict(td_h=50e-9, td_dab=100e-9, R_dab=0.02, dt=5e-9, t_pre=2e-3, deadtime_comp="model",
                  coss_h=1e-9, coss_comp=1e-9, comp_band_A=20., dab_Lmin=0.9)


def iL_center(vbus, vlink, n, f, Ld, ph):
    """대칭 배치 SPS 정상상태에서 상승 쌍 중심(반송파 최댓값) 순간의 누설 전류(반파 대칭 해석해, 위상 부호 무관):
    i = −(V1 − V2)(T/2 − |δ|)/(2 L_d),  V1 = v_bus, V2 = n·v_link, δ = |φ|T/2π."""
    T = 1 / f; d = abs(ph) / (2 * PI) * T
    return -(vbus - n * vlink) * (T / 2 - d) / (2 * Ld)


def simulate_switching(vbat, P0, P1, p, cp, K, predict=True, profile=0, duration=.02, step=1e-3,
                       delay=None, sw=None, capture=None):
    """스위칭 모델 1개 시험. p: 플랜트 Parameters, cp: 제어기 공칭 Parameters, delay: 총 전달지연[s](기본 p.delay)."""
    sw = dict(SW_DEFAULT, **(sw or {}))
    dt = sw["dt"]; delay = p.delay if delay is None else delay
    x0, u0 = equilibrium(vbat, P0, p)
    ph0 = _phase(u0[1], x0[2], x0[4], _cp_vec(cp), sw["dab_Lmin"])
    iL0 = iL_center(x0[2], x0[4], p.turns, p.fs, p.Ldab, ph0)
    pp = np.array([p.L, p.Cs, p.Cb, p.R, p.Lh, p.Rh, p.Clink, p.eta, vbat, p.Ldab, p.turns, sw["R_dab"]])
    K = np.asarray(K, float)
    q0 = -(x0[0] + K[0] * x0[0] + K[1] * x0[1] + K[2] * x0[2] + K[3] * x0[3]) / K[4]
    cst = np.array([q0, 0., u0[0], u0[1]])
    cap = np.array(capture if capture is not None else [0., 0., 1.], float)
    rec, zvs, alive, end_i, wave, eres = run_core(x0.astype(float), float(iL0), cst, u0.astype(float), pp, _cp_vec(cp), K,
                                      bool(predict), int(profile), float(P0), float(P1), float(step),
                                      float(sw["t_pre"]), float(duration), float(dt), int(round(delay / dt)),
                                      np.array([sw["td_h"], sw["td_dab"], {"model": 1., "linear": 2.}.get(sw["deadtime_comp"], 0.),
                                                sw["coss_comp"], sw["coss_h"], sw["comp_band_A"], sw["dab_Lmin"]]), cap)
    if not alive:
        rec = rec[: end_i // int(round(cp.Ts / dt))]
    t_end = (np.arange(rec.shape[0]) + 1) * cp.Ts - sw["t_pre"]     # 주기 끝 시각(스텝 기준 시간축)
    return dict(t=t_end, rec=rec, zvs=zvs, completed=bool(alive), dt=dt, delay=delay, wave=wave, energy_residual_W=float(eres))


def _cp_vec(cp):
    return np.array([cp.L, cp.Cs, cp.Cb, cp.R, cp.Lh, cp.Rh, cp.Clink, cp.Ts, cp.vref, cp.vlink, cp.modulation_max,
                     cp.reference_max, cp.link_max, cp.power_max, cp.link_bw, cp.inner_tau, cp.Ldab, cp.fs, cp.turns,
                     cp.phase_max])
