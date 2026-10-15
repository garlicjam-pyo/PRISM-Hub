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
             데드타임 동안 노드 전압은 필터전류로 출력용량(기본 선형 1 nF/스위치, 선택으로 전압 의존
             C(v) = C0·(1 + v/V0)^(−m))을 충방전하며 움직이고, 남은 전압은 데드타임 끝에서 하드 스위칭한다.
             노드 값은 간격마다 그 시점 전류로 이어서 적분한다. 에지는 적분 간격 안의 정확한 위치로 처리한다.
  DAB      : 50 % 구형파 두 브리지, 200 kHz, 단일 위상천이(SPS). 링크전류 지령 → 위상
             φ = (π/2)(1 − √(1 − 4|I|/(π k))),  k = n·v_bus/(2π f L_d)  (|φ| ≤ π/3)
             링크전류 제어(채택): 앞먹임 위상은 누설 인덕턴스를 공차 하한(공칭 −10 %)으로 보고 계산해 실제 전류가
             지령을 넘지 않게 하고(정격 80 A·8 kW 보호), 링크 직류전류 측정값(주기 평균)과 그 주기에 적용된 위상의
             앞먹임 예측 전류의 비 ρ̂를 추정해 지령을 I/ρ̂로 보정한다(실제 인덕턴스가 크면 ρ̂ < 1 → 용량 회복).
             ρ̂는 예측 전류 40 A 이상(위상 약 19° 이상, 데드타임 영향이 작은 구간)이고 주기 안 위상 변화가 2° 미만일 때만
             이득 0.05/주기로 갱신하며 0.75–1.25로 제한한다. 미학습 상태는 ρ̂ = 1(보수 쪽).
             저전류 가산 보정(채택): 예측 전류 40 A 미만에서는 데드타임 때문에 전달 특성이 꺾인다(두 브리지 전압이 같을 때
             δ < 2t_d에서 증분 이득 2배, δ ≤ t_d에서 불감대). 이 구간에서 측정 전류와 ρ̂·예측 전류의 차 ε̂를 이득 0.2/주기로
             추종해 지령에서 빼고(|ε̂| ≤ 10 A), 40 A 이상에서는 ε̂를 같은 이득으로 0까지 줄인다. 측정 링크전류만 쓰므로
             실제 데드타임을 몰라도 된다. (비교용) dab_deadtime_comp: 데드타임 모델로 위상을 역보정하는 앞먹임 방식
             (_dab_dt_comp). 가정한 데드타임이 실제보다 길면 영전류 부근에서 과보상 계전기 동작이 생긴다(E12 dab_lowcurrent).
             (비교용) dab_estimator=False이면 공칭 L 앞먹임에 L −10 % 기준 위상 한계를 더한 이전 방식.
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
           채택 설계는 1주기 예측). 변조기에는 데드타임 보상을 둔다: 예측 i_h와 리플 반진폭으로 리플 극값에서의
           전이별 전압·시간 오차를 구해 변조율에서 뺀다. 채택은 교정표 방식(deadtime_error_tab: 전류별 전이 오차표,
           실제 장치에서는 측정한 데드타임 전압오차로 만들며 비선형 출력용량을 반영)이며, 계산한 오차의 κ만 보상한다.
           κ는 예측 전류 20 A 이하에서 0.6, 80 A에서 1로 선형 증가한다. 경부하에서는 남은 40 %가 전류와 반대 방향의
           전압오차(저항성)로 남아, 리플 극값 전류·출력용량의 불확도 때문에 보상이 실제 오차를 넘는 구간이 생겨도
           지속 진동이 생기지 않게 하고(E12 deadtime_robust), 전이가 모두 하드 스위칭인 대전류에서는 오차가 정확히
           알려져 있으므로 전부 보상해 저전압 정격 부하의 전류 여유를 지킨다. κ의 증가 기울기는 음저항으로 작용하므로
           완만하게 둔다(20→80 A).
           선형 출력용량 해석식(deadtime_error)은 비교용이다. 두 방식 모두 전이 중 전류 기울기는 무시한다.
           표본 시점은 반송파 최댓값(5 µs 주기)이며 측정값은 순시 표본이다. 지령은 표본 후 전달지연(기본 5 µs) 뒤에 PWM 비교 레지스터에 즉시 반영되고, DAB 위상은
           그 이후 첫 반주기 중심에서 반영된다.
[센서]     기본은 이상 센서. sensors 인자(6×4: i_p, v_s, v_bus, i_h, v_link, 링크전류 × [이득, 오프셋, 양자화 간격,
           잡음 표준편차])로 센서·ADC 오차를 넣는다. 잡음은 seed로 재현한다.
[적분]     고정 간격 중점법 dt = 5 ns(주기당 1000단계). 스위치 상태는 간격 안의 에지·데드타임 경계로 나눈 평균.
[양자화]   (선택, 기본 없음) gate_quantum·dab_quantum > 0이면 H-브리지 PWM 에지·DAB 에지를 그 시간 격자에 반올림한다
           (디지털 PWM·위상 분해능. 소자 회로 모델의 적분 간격 격자와 같은 효과를 적분 간격과 따로 줄 수 있다).
[한계]     DAB 소자 출력용량·스위칭 손실·기생 인덕턴스·자화 인덕턴스·Stage A 리플·센서 대역 제한·보호 동작 미포함.
"""
import math

import numpy as np
from numba import njit

from model_stage_b import equilibrium

PI = math.pi
NREC = 25
# 주기 기록(rec) 열: 0 v_bus 평균, 1 i_p 평균, 2 i_h 평균, 3 v_link 평균, 4 링크전류 평균, 5 링크전력 평균,
#   6 i_h 최대, 7 i_h 최소, 8 |i_p| 최대, 9 v_bus 최소, 10 v_bus 최대, 11 v_link 최소, 12 v_link 최대,
#   13 |i_L| 최대, 14 변조율 지령(제어기 출력), 15 링크전류 지령, 16 적용 DAB 위상, 17 |v_s| 최대,
#   18 PWM 비교값(데드타임 보상 후), 19 i_L 주기 평균(직류 편류), 20 DAB 손실 전류원 전력,
#   21 DAB 전류비 추정값 ρ̂(측정 링크전류 / 앞먹임 예측 전류), 22 저전류 가산 보정 ε̂ [A],
#   23 링크전류 센서 타당성 잔차(필터) [A], 24 링크전류 센서 고장 판정(0/1)


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
def deadtime_error_tab(m, i, V, L, f, ig, eg, Vtab):
    """deadtime_error의 표 방식. eg(ig) = 상승 전이 한 번에 잃는 전압·시간(전류 ig, 링크전압 Vtab에서 교정한 값).
    하강 전이는 대칭(E_fall(i) = E_rise(−i))이므로 한 주기 오차는 2·[E(−i_max) − E(i_min)]·f 이다."""
    if m < 0.:
        return -deadtime_error_tab(-m, -i, V, L, f, ig, eg, Vtab)
    r = V * m * (1 - m) / (4 * L * f)
    imin = i - r; imax = i + r
    d = 2. * (np.interp(-imax, ig, eg) - np.interp(imin, ig, eg)) * (V / Vtab)
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
def _phase_ff(il, vb, cp, lbasis):
    """링크전류 → SPS 위상 앞먹임(누설 인덕턴스를 공칭의 lbasis배로 가정, |φ| ≤ φ_max).
    lbasis = 0.9이면 인덕턴스가 공차 하한이라고 보고 위상을 정하므로, 실제 인덕턴스가 그보다 크면
    실제 전류는 지령보다 작다(정격 쪽으로 안전). 부족분은 전류비 추정(run_core)으로 보정한다."""
    Ldab, fs, turns, phmax = cp[16], cp[17], cp[18], cp[19]
    k = turns * max(vb, 1.) / (2 * PI * fs * Ldab * lbasis)
    a = min(abs(il) / (PI * k / 4.), 1.)
    ph = min(PI / 2 * (1 - math.sqrt(1 - a)), phmax)
    return ph if il >= 0 else -ph


@njit(cache=True)
def _ipred(ph, vb, cp, lbasis):
    """위상 ph에서 SPS 식이 주는 링크전류(인덕턴스 공칭의 lbasis배 가정)."""
    Ldab, fs, turns = cp[16], cp[17], cp[18]
    k = turns * max(vb, 1.) / (2 * PI * fs * Ldab * lbasis)
    return k * ph * (1 - abs(ph) / PI)


@njit(cache=True)
def _dab_dt_comp(dtg, tc):
    """DAB 위상 데드타임 보상(tc: 보상에 쓰는 데드타임, 0이면 없음). 두 브리지 전압이 같을 때(v_bus = n·v_link)
    앞선 브리지의 에지에서 전류가 데드타임 안에 0을 지나면 데드타임 끝까지 0에 묶여, 실제 전류는
    δ ≥ 2t_d에서 S·δ/2(S = 2v_bus/L_d, 데드타임 영향 없음), t_d < δ < 2t_d에서 S·(δ − t_d), δ ≤ t_d에서 0이 된다.
    따라서 원하는 유효 위상 시간 δ_eff(SPS 식)에 대해 δ_eff < 2t_d이면 δ = δ_eff/2 + t_d를 지령해 전달 특성을
    선형으로 되돌린다(경계 δ_eff = 2t_d에서 연속). 보상이 없으면 이 구간의 증분 이득이 2배, δ ≤ t_d는 불감대다."""
    if tc <= 0.:
        return dtg
    a = abs(dtg)
    if a < 2. * tc:
        a = .5 * a + tc
    return a if dtg >= 0. else -a


@njit(cache=True)
def _sense(v, s):
    """센서·ADC 모델: s = [이득, 오프셋, 양자화 간격(0이면 없음), 잡음 표준편차]."""
    y = s[0] * v + s[1]
    if s[3] > 0.:
        y += s[3] * np.random.standard_normal()
    if s[2] > 0.:
        y = s[2] * math.floor(y / s[2] + .5)
    return y


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
    """레그 노드 전압(정규화 0–1)의 한 간격 평균(선형 출력용량). 데드타임 동안 노드는 출력용량 충방전 기울기 sg로
    움직이고(다이오드 클램프 0–1), 데드타임이 끝나면 목표 레벨로 스위칭한다(남은 전압은 하드 스위칭).
    st = [전이 시작 시각 te, 기준 노드 값, 목표 레벨, 현재 노드 값, 기준 시각]. a, b: 목표가 1인 구간.
    기울기는 간격마다 그 시점의 전류로 정하고, 간격 시작의 노드 값에서 이어서 적분한다(간격 안 전류 일정)."""
    d0 = 1. if (b > a and a == 0.) else 0.
    d1 = 1. if (b > a and b == 1.) else 0.
    t1 = t0 + dt
    edges = 0; se = 0.
    if d0 != d1:
        edges = 1; se = a if d1 == 1. else b
    if d0 != st[2]:                             # 간격 시작에서의 레벨 변화(지령 갱신): 지금 노드 값에서 새 전이 시작
        st[0] = t0; st[2] = d0
    st[1] = st[3]; st[4] = t0                   # 간격 시작 노드 값을 기준으로 이번 간격의 기울기 적용
    tot = 0.
    seg_end = t0 + se * dt if edges == 1 else t1
    tot += _seg(st, t0, seg_end, td, sg)
    if edges == 1:
        # 새 목표 에지: 그 순간의 노드 값에서 전이 시작
        st[1] = _node_at(st, seg_end, td, sg); st[4] = seg_end; st[0] = seg_end; st[2] = d1
        tot += _seg(st, seg_end, t1, td, sg)
    st[3] = _node_at(st, t1, td, sg)
    return tot / dt


@njit(cache=True)
def _node_at(st, t, td, sg):
    if t >= st[0] + td:
        return st[2]
    return min(max(st[1] + sg * (t - st[4]), 0.), 1.)


@njit(cache=True)
def _seg(st, ta, tb, td, sg):
    if tb <= ta:
        return 0.
    tend = st[0] + td                           # 데드타임 종료 시각
    tot = 0.
    if ta < tend:
        e = min(tb, tend)
        tot += _ramp_int(st[1], sg, ta - st[4], e - st[4])
        ta = e
    if tb > ta:
        tot += st[2] * (tb - ta)
    return tot


@njit(cache=True)
def _cnode(u, vl, C0, V0, m):
    """레그 노드의 등가 용량(두 스위치 출력용량의 합). C(v) = C0·(1 + v/V0)^(−m)."""
    v1 = min(max(u, 0.), 1.) * vl
    return C0 * ((1. + v1 / V0) ** (-m) + (1. + (vl - v1) / V0) ** (-m))


@njit(cache=True)
def _seg_nl(st, ta, tb, td, iout, vl, C0, V0, m):
    """비선형 출력용량 레그 노드의 [ta, tb] 적분. st[3] = ta에서의 노드 값(정규화)을 tb 값으로 갱신한다.
    데드타임 동안 du/dt = −i_out/(v_link·C_node(u))(다이오드 클램프 0–1)를 0.5 ns 이하 간격의 중점법으로 적분한다."""
    tend = st[0] + td
    u = st[3]; tot = 0.; t = ta
    if t < tend and tb > t:
        e = min(tb, tend)
        nsub = max(1, int(math.ceil((e - t) / 0.5e-9)))
        h = (e - t) / nsub
        for _ in range(nsub):
            k1 = -iout / (vl * _cnode(u, vl, C0, V0, m))
            um = min(max(u + .5 * h * k1, 0.), 1.)
            k2 = -iout / (vl * _cnode(um, vl, C0, V0, m))
            un = min(max(u + h * k2, 0.), 1.)
            tot += .5 * (u + un) * h
            u = un
        t = e
    if tb > t:
        u = st[2]
        tot += u * (tb - t)
    st[3] = u
    return tot


@njit(cache=True)
def _leg_step_nl(st, a, b, t0, dt, td, iout, vl, C0, V0, m):
    """_leg_step의 비선형 출력용량판. st = [전이 시작 시각, (미사용), 목표 레벨, 현재 노드 값, (미사용)]."""
    d0 = 1. if (b > a and a == 0.) else 0.
    d1 = 1. if (b > a and b == 1.) else 0.
    t1 = t0 + dt
    edges = 0; se = 0.
    if d0 != d1:
        edges = 1; se = a if d1 == 1. else b
    if d0 != st[2]:
        st[0] = t0; st[2] = d0
    seg_end = t0 + se * dt if edges == 1 else t1
    tot = _seg_nl(st, t0, seg_end, td, iout, vl, C0, V0, m)
    if edges == 1:
        st[0] = seg_end; st[2] = d1
        tot += _seg_nl(st, seg_end, t1, td, iout, vl, C0, V0, m)
    return tot / dt


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
def run_core(x0, iL0, cst, uq, pp, cp, K, predict, prof, P0, P1, step, t_pre, duration, dt, lag, sw, cap, sens, seed, etab):
    """스위칭 모델 적분. 반환: 주기별 기록, ZVS 집계, 완료 여부, 종료 스텝, 파형, 에너지 잔차."""
    Ts = cp[7]; Np = int(round(Ts / dt)); T = Ts; Nh = Np // 2
    td_h, td_d, dtc = sw[0], sw[1], sw[2]            # H-브리지·DAB 데드타임, 데드타임 보상(0 없음, 1 모델 기반, 2 선형)
    coss = sw[4]                                    # H-브리지 스위치 출력용량(노드 등가 2·C_oss)
    lmin = sw[6]; est = sw[7] > 0.; est_g = sw[8]; est_min = sw[9]   # DAB 위상 기준 인덕턴스 비, 전류비 추정 사용·이득·최소 전류
    qe = sw[27]; qd = sw[28]                         # 게이트 시간 양자화 간격(H-브리지 PWM, DAB 에지). 0 = 없음(간격 안 정확한 에지)
    np.random.seed(seed)
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
    legA = np.array([-1., 1., 1., 1., -1.]); legB = np.array([-1., 0., 0., 0., -1.])
    qi = np.full(8, -1); qm = np.zeros(8); qp = np.zeros(8); qh = 0; qt = 0
    t_start = -t_pre
    # ---- DAB 에지 일정: 반주기 중심 c_j = t_start + j·T/2 (짝수 j = 반송파 최댓값 = 상승 쌍, 홀수 j = 하강 쌍).
    #      쌍 j의 1차 에지 c_j − δ/2, 2차 에지 c_j + δ/2 (δ = φ·T/2π, 부호 포함).
    rho = 1.                                        # 전류비 추정값(미학습 = 1: 인덕턴스가 공차 하한이라고 가정)
    eps = 0.                                        # 저전류 가산 보정값 ε̂ [A](측정 링크전류 − ρ̂·예측 전류)
    # 링크전류 센서 타당성 감시(sw[22] > 0이면 사용): 측정 DAB 링크전류를 링크 전하 수지(H-브리지 소비 m·i_h + C_l·Δv_link/T)와
    # 비교한 잔차를 1차 필터(sw[25])로 거르고, |잔차| > sw[23] + sw[24]·|기대값|이면 고장으로 판정(래치)해 ρ̂ = 1, ε̂ = 0으로
    # 되돌리고 갱신을 멈춘다(누설 인덕턴스 −10 % 기준 앞먹임만 남아 실제 전류 ≤ 지령). 판정 전이라도 빠른 필터(sw[26]) 잔차가
    # 문턱의 절반을 넘으면 ρ̂·ε̂ 갱신을 멈춰, 고장 센서 값이 판정 전에 추정값을 끌고 가지 못하게 한다.
    ih_prev = x[3]; vl_prev = x[4]; r_f = 0.; r_g = 0.; mon_fault = False
    if est:
        ph_tgt = _phase_ff(uq[1], x[2], cp, lmin)    # 현재 위상 지령
    else:
        ph_tgt = _phase(uq[1], x[2], x[4], cp, lmin)
    ip_c0 = _ipred(ph_tgt, x[2], cp, lmin); ip_c1 = ip_c0; ph_c0 = ph_tgt; ph_c1 = ph_tgt   # 주기 안 두 반주기 중심의 위상·예측 전류
    il_meas = uq[1]; il_pred = ip_c0; dph_prev = 0.; vb_m = x[2]
    d0 = _dab_dt_comp(ph_tgt / (2 * PI) * T, sw[18])
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
            for c in range(5):                       # 센서·ADC(기본은 이상 센서)
                meas[c] = _sense(x[c], sens[c])
            mcmd, icmd, iref, ihp = _controller(meas, cst, cp, K, predict, vbat)
            vb_m = meas[2]
            if est:
                # DAB 전류비 추정: 직전 주기의 측정 링크전류(주기 평균, 링크 직류전류 센서)와 그 주기에 적용된 위상의
                # 앞먹임 예측 전류를 비교한다. 위상이 데드타임 영향이 작은 큰 값이고 주기 안에서 위상이 거의 변하지 않을 때만 갱신.
                ilm = _sense(il_meas, sens[6] if (sens.shape[0] > 6 and t0 >= sw[21]) else sens[5])   # sens[6]: 고장 후 센서
                plaus = True                         # 감시 사용 시: 잔차가 고장 문턱의 절반 미만일 때만 ρ̂·ε̂ 갱신
                if sw[22] > 0. and i > 0:
                    iexp = m_reg * .5 * (ih_prev + meas[3]) + cp[6] * (meas[4] - vl_prev) / T
                    r_f += sw[25] * ((ilm - iexp) - r_f)            # 고장 판정용(느린 필터: 오경보 방지)
                    r_g += sw[26] * ((ilm - iexp) - r_g)            # 갱신 차단용(빠른 필터: 판정 전 추정값 오염 방지)
                    thr = sw[23] + sw[24] * abs(iexp)
                    if abs(r_f) > thr:
                        mon_fault = True
                    plaus = abs(r_g) < .5 * thr
                if mon_fault:
                    rho = 1.; eps = 0.
                elif plaus and abs(il_pred) >= est_min and ilm * il_pred > 0. and dph_prev < .035:
                    rho += est_g * (ilm / il_pred - rho)
                    rho = min(max(rho, .75), 1.25)
                # 저전류 가산 보정(sw[19] = 갱신 이득, 0이면 없음): 데드타임 영향이 있는 저전류 구간(|예측| < est_min)에서
                # 측정 전류와 ρ̂·예측 전류의 차를 1차 추종하고 지령에서 뺀다. 그 밖에서는 0으로 감쇠한다.
                if sw[19] > 0. and not mon_fault:
                    if plaus and abs(il_pred) < est_min and dph_prev < .035:
                        eps += sw[19] * ((ilm - rho * il_pred) - eps)
                    elif abs(il_pred) >= est_min:
                        eps -= sw[19] * eps
                    eps = min(max(eps, -sw[20]), sw[20])
                ph_new = _phase_ff((icmd - eps) / rho, meas[2], cp, lmin)
            else:
                ph_new = _phase(icmd, meas[2], meas[4], cp, lmin)
            if dtc == 1.:                            # 모델 기반 데드타임 보상: 예측 전류와 리플로 오차를 계산해 상쇄
                vlm = max(meas[4], 1.)
                mcmd_pwm = mcmd - sw[15] * deadtime_error(mcmd, ihp, vlm, td_h, sw[3], cp[4], 1 / T) / vlm
            elif dtc == 3.:                          # 교정표 기반 보상: 전류별 전이 오차표(비선형 출력용량 반영)
                vlm = max(meas[4], 1.)
                kap = sw[15] + (1. - sw[15]) * min(max((abs(ihp) - sw[16]) / max(sw[17] - sw[16], 1e-9), 0.), 1.)
                mcmd_pwm = mcmd - kap * deadtime_error_tab(mcmd, ihp, vlm, cp[4], 1 / T, etab[0], etab[1], sw[14]) / vlm
            elif dtc == 2.:                          # (비교용) 전류지령 비례 보상: ±sw[5] A에서 포화
                mcmd_pwm = mcmd + 2 * td_h / T * min(max(iref / sw[5], -1.), 1.)
            else:
                mcmd_pwm = mcmd
            qi[qt % 8] = i + lag; qm[qt % 8] = mcmd_pwm; qp[qt % 8] = ph_new; qt += 1
            rec[i // Np, 14] = mcmd; rec[i // Np, 15] = icmd; rec[i // Np, 18] = mcmd_pwm; rec[i // Np, 21] = rho
            rec[i // Np, 22] = eps; rec[i // Np, 23] = r_f; rec[i // Np, 24] = 1. if mon_fault else 0.
            ih_prev = meas[3]; vl_prev = meas[4]
        while qh < qt and qi[qh % 8] <= i:          # 전달지연 뒤 지령 반영(PWM 비교값 즉시, DAB 위상은 다음 반주기 중심)
            m_reg = qm[qh % 8]; ph_tgt = qp[qh % 8]; qh += 1
        # ---- H-브리지(유니폴라 PWM, 정확한 에지 위치, 데드타임 중 출력용량 충방전)
        ih = x[3]
        c0 = _carrier(i, Np); c1 = _carrier(i + 1, Np)
        aA, bA = _on_interval(m_reg, c0, c1)
        aB, bB = _on_interval(-m_reg, c0, c1)
        if qe > 0.:                                  # 게이트 시간 양자화(선택): PWM 에지를 qe 격자(dt의 정수분의 1)에 반올림
            nq = np.floor(dt / qe + .5)
            aA = np.floor(aA * nq + .5) / nq; bA = np.floor(bA * nq + .5) / nq
            aB = np.floor(aB * nq + .5) / nq; bB = np.floor(bB * nq + .5) / nq
        # 노드 기울기(정규화/초): 레그 A에서 나가는 전류 i_h가 양이면 노드 A는 내려가고, 레그 B는 올라간다
        vl_ = max(x[4], 1.)
        if sw[10] > 0.:                              # 비선형 출력용량(전압 의존 C_oss)
            sA = _leg_step_nl(legA, aA, bA, t0, dt, td_h, ih, vl_, sw[13], sw[12], sw[11])
            sB = _leg_step_nl(legB, aB, bB, t0, dt, td_h, -ih, vl_, sw[13], sw[12], sw[11])
        else:
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
            dtg = _dab_dt_comp(ph_tgt / (2 * PI) * T, sw[18])   # 유효 위상 → 적용 위상(데드타임 보상)
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
            if j % 2 == 0:
                ph_c0 = ph_tgt; ip_c0 = _ipred(ph_tgt, vb_m, cp, lmin)
            else:
                ph_c1 = ph_tgt; ip_c1 = _ipred(ph_tgt, vb_m, cp, lmin)
        # ---- DAB 에지 실행
        ptq = p_t[p_j % 2]
        if qd > 0. and ptq < 1e29:                   # DAB 에지 시간 양자화(선택): 가장 가까운 qd 격자 시각
            ptq = np.floor(ptq / qd + .5) * qd
        if ptq < t1:
            te = max(ptq, t0)
            p_before = p_state; p_state = 1. if p_j % 2 == 0 else -1.; p_te = te; p_h[p_j % 2] = te; p_t[p_j % 2] = 1e30; p_j += 1
            if te >= t_zvs:
                zvs[1] += 1
                if (p_state == -1 and x[5] > 0) or (p_state == 1 and x[5] < 0):
                    zvs[0] += 1
        stq = s_t[s_j % 2]
        if qd > 0. and stq < 1e29:
            stq = np.floor(stq / qd + .5) * qd
        if stq < t1:
            te = max(stq, t0)
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
            il_meas = acc[4] / Np; il_pred = .5 * (ip_c0 + ip_c1); dph_prev = abs(ph_c1 - ph_c0)
            ploss = max(_loss(acc[5] / Np, eta) - Rd * acc[6] / Np, 0.)
            acc[:] = 0.; mx_ih = -1e9; mn_ih = 1e9; mx_ip = 0.; mn_vb = 1e9; mx_vb = -1e9
            mn_vl = 1e9; mx_vl = -1e9; mx_iL = 0.; mx_vs = 0.
        if not (np.isfinite(x).all()) or x[2] < 50 or x[4] < 10:
            alive = False; end_i = i; break
    return rec, zvs, alive, end_i, wave, eres


SW_DEFAULT = dict(td_h=50e-9, td_dab=100e-9, R_dab=0.02, dt=5e-9, t_pre=2e-3, deadtime_comp="table",
                  coss_h=1e-9, coss_comp=1e-9, comp_band_A=20., dab_Lmin=0.9,
                  dab_estimator=True, dab_est_gain=0.05, dab_est_min_A=40.,
                  coss_nonlinear=False, coss_m=0.5, coss_V0=5.,
                  table_cq=None, table_nonlinear=None, table_m=None, table_V0=None, table_smooth_A=0., comp_scale=.6,
                  comp_full_from_A=20., comp_full_at_A=80., dab_deadtime_comp=0., dab_eps_gain=.2, dab_eps_max_A=10.,
                  link_sensor_fault_t=1e30, link_monitor=False, link_monitor_A=6., link_monitor_rel=.15, link_monitor_alpha=.05, link_gate_alpha=.3,
                  gate_quantum=0., dab_quantum=0.)

# 센서 채널 순서: i_p, v_s, v_bus, i_h, v_link, 링크전류(주기 평균). 각 행 = [이득, 오프셋, 양자화 간격, 잡음 표준편차]
SENSOR_IDEAL = np.array([[1., 0., 0., 0.]] * 6)


def coss_q(V, C0, m, V0):
    """C(v) = C0·(1 + v/V0)^(−m)의 전하 Q(V) = ∫0^V C dv."""
    return C0 * V0 / (1 - m) * ((1 + V / V0) ** (1 - m) - 1)


def coss_c0(cq, m, V0, V=100.):
    """전하 등가 용량 C_Q = Q(V)/V가 cq가 되는 C0(링크 공칭 100 V 기준)."""
    return cq * V / coss_q(V, 1., m, V0)


TABLE_V = 100.


_TABLE_CACHE = {}


def deadtime_table(td, cq, nonlinear, m, V0, V=TABLE_V, n=2000, smooth=0.):
    """교정표(아래 _deadtime_table_raw)를 만들고, smooth > 0이면 전류 ±smooth A 구간 평균으로 완만하게 한다.
    영전류 부근 전이 오차는 전류에 대해 급하게 변하므로, 예측 전이 전류의 오차(리플 크기·L_h 공차·예측 오차)가
    있으면 보상이 엉뚱한 전류에서 급변해 경부하 진동을 만든다. 구간 평균은 보상의 기울기를 제한한다."""
    key = (td, cq, bool(nonlinear), m, V0, V, n, smooth)
    if key not in _TABLE_CACHE:
        ig, eg = _deadtime_table_raw(td, cq, nonlinear, m, V0, V, n)
        if smooth > 0.:
            h = .01
            iu = np.arange(-100., 100. + h / 2, h)
            eu = np.interp(iu, ig, eg)
            w = int(round(smooth / h))
            cs = np.concatenate([[0.], np.cumsum(eu)])
            es = eu.copy()
            es[w:-w] = (cs[2 * w + 1:] - cs[:-2 * w - 1]) / (2 * w + 1)
            sel = np.arange(0, len(iu), 10)               # 0.1 A 간격으로 저장
            ig, eg = iu[sel], es[sel]
        _TABLE_CACHE[key] = np.vstack([ig, eg])
    return _TABLE_CACHE[key]


def _deadtime_table_raw(td, cq, nonlinear, m, V0, V=TABLE_V, n=2000):
    """데드타임 보상 교정표: 상승 전이 한 번에 잃는 전압·시간 E(i) [V·s] (i: 노드에서 나가는 전류, 전이 중 일정).
    노드를 0 V에서 시작해 dv/dt = −i/C_node(v)(0–V 클램프)로 데드타임 동안 적분하고 ∫(V − v)dt를 구한다.
    실제 장치에서는 전류를 바꿔 가며 측정한 데드타임 전압오차로 같은 표를 만든다."""
    ig = np.concatenate([-np.logspace(2, -2, 81), [0.], np.logspace(-2, 2, 81)])
    C0 = coss_c0(cq, m, V0) if nonlinear else cq
    mm = m if nonlinear else 0.
    cn = lambda v: C0 * ((1 + v / V0) ** (-mm) + (1 + (V - v) / V0) ** (-mm))
    v = np.zeros_like(ig); lost = np.zeros_like(ig); h = td / n
    for _ in range(n):
        vm = np.clip(v + .5 * h * (-ig / cn(v)), 0., V)
        vn = np.clip(v + h * (-ig / cn(vm)), 0., V)
        lost += (V - .5 * (v + vn)) * h
        v = vn
    return ig, lost


def iL_center(vbus, vlink, n, f, Ld, ph):
    """대칭 배치 SPS 정상상태에서 상승 쌍 중심(반송파 최댓값) 순간의 누설 전류(반파 대칭 해석해, 위상 부호 무관):
    i = −(V1 − V2)(T/2 − |δ|)/(2 L_d),  V1 = v_bus, V2 = n·v_link, δ = |φ|T/2π."""
    T = 1 / f; d = abs(ph) / (2 * PI) * T
    return -(vbus - n * vlink) * (T / 2 - d) / (2 * Ld)


def simulate_switching(vbat, P0, P1, p, cp, K, predict=True, profile=0, duration=.02, step=1e-3,
                       delay=None, sw=None, capture=None, sensors=None, seed=1):
    """스위칭 모델 1개 시험. p: 플랜트 Parameters, cp: 제어기 공칭 Parameters, delay: 총 전달지연[s](기본 p.delay),
    sensors: 6×4 센서 배열(SENSOR_IDEAL 형식, 기본 이상 센서), seed: 센서 잡음 난수 시드."""
    sw = dict(SW_DEFAULT, **(sw or {}))
    dt = sw["dt"]; delay = p.delay if delay is None else delay
    x0, u0 = equilibrium(vbat, P0, p)
    if sw["dab_estimator"]:
        ph0 = _phase_ff(u0[1], x0[2], _cp_vec(cp), sw["dab_Lmin"])
    else:
        ph0 = _phase(u0[1], x0[2], x0[4], _cp_vec(cp), sw["dab_Lmin"])
    iL0 = iL_center(x0[2], x0[4], p.turns, p.fs, p.Ldab, ph0)
    pp = np.array([p.L, p.Cs, p.Cb, p.R, p.Lh, p.Rh, p.Clink, p.eta, vbat, p.Ldab, p.turns, sw["R_dab"]])
    K = np.asarray(K, float)
    q0 = -(x0[0] + K[0] * x0[0] + K[1] * x0[1] + K[2] * x0[2] + K[3] * x0[3]) / K[4]
    cst = np.array([q0, 0., u0[0], u0[1]])
    cap = np.array(capture if capture is not None else [0., 0., 1.], float)
    # 교정표: 기본은 플랜트와 같은 출력용량 모델로 만든 표(이상적 교정). table_* 로 교정 오차를 줄 수 있다.
    tq = sw["coss_h"] if sw["table_cq"] is None else sw["table_cq"]
    tn = sw["coss_nonlinear"] if sw["table_nonlinear"] is None else sw["table_nonlinear"]
    tm = sw["coss_m"] if sw["table_m"] is None else sw["table_m"]
    tv = sw["coss_V0"] if sw["table_V0"] is None else sw["table_V0"]
    etab = (deadtime_table(sw["td_h"], tq, tn, tm, tv, smooth=sw["table_smooth_A"]) if sw["deadtime_comp"] == "table"
            else np.zeros((2, 2)))
    # (비교용) DAB 위상 데드타임 앞먹임 보상: 0이면 끔(기본), None이면 플랜트 데드타임과 같은 값, 수치를 주면 그 값으로 보상
    dab_tc = sw["td_dab"] if sw["dab_deadtime_comp"] is None else float(sw["dab_deadtime_comp"])
    rec, zvs, alive, end_i, wave, eres = run_core(x0.astype(float), float(iL0), cst, u0.astype(float), pp, _cp_vec(cp), K,
                                      bool(predict), int(profile), float(P0), float(P1), float(step),
                                      float(sw["t_pre"]), float(duration), float(dt), int(round(delay / dt)),
                                      np.array([sw["td_h"], sw["td_dab"], {"model": 1., "linear": 2., "table": 3.}.get(sw["deadtime_comp"], 0.),
                                                sw["coss_comp"], sw["coss_h"], sw["comp_band_A"], sw["dab_Lmin"],
                                                float(sw["dab_estimator"]), sw["dab_est_gain"], sw["dab_est_min_A"],
                                                float(sw["coss_nonlinear"]), sw["coss_m"], sw["coss_V0"],
                                                coss_c0(sw["coss_h"], sw["coss_m"], sw["coss_V0"]), TABLE_V, sw["comp_scale"], sw["comp_full_from_A"], sw["comp_full_at_A"],
                                                dab_tc, sw["dab_eps_gain"], sw["dab_eps_max_A"], float(sw["link_sensor_fault_t"]) - 0.,
                                                float(sw["link_monitor"]), sw["link_monitor_A"], sw["link_monitor_rel"], sw["link_monitor_alpha"],
                                                sw["link_gate_alpha"], sw["gate_quantum"], sw["dab_quantum"]]), cap,
                                      np.asarray(SENSOR_IDEAL if sensors is None else sensors, float), int(seed), etab)
    if not alive:
        rec = rec[: end_i // int(round(cp.Ts / dt))]
    t_end = (np.arange(rec.shape[0]) + 1) * cp.Ts - sw["t_pre"]     # 주기 끝 시각(스텝 기준 시간축)
    return dict(t=t_end, rec=rec, zvs=zvs, completed=bool(alive), dt=dt, delay=delay, wave=wave, energy_residual_W=float(eres))


def _cp_vec(cp):
    return np.array([cp.L, cp.Cs, cp.Cb, cp.R, cp.Lh, cp.Rh, cp.Clink, cp.Ts, cp.vref, cp.vlink, cp.modulation_max,
                     cp.reference_max, cp.link_max, cp.power_max, cp.link_bw, cp.inner_tau, cp.Ldab, cp.fs, cp.turns,
                     cp.phase_max])
